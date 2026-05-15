"""
services/groq_client.py
Production-grade Groq client:
- Exponential backoff retry (3 attempts, 2s/4s/8s)
- 45s hard timeout via asyncio.wait_for()
- Cache fallback on failure
- Structured error logging
"""
import asyncio
import json
import time
import logging
from typing import List, Optional
import httpx
from core.config import settings
from services.groq_cache import get_cached, set_cached, get_demo_fallback

logger = logging.getLogger("logoracle.groq")

GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
MAX_RETRIES   = 3
RETRY_DELAYS  = [2.0, 4.0, 8.0]  # exponential backoff
HARD_TIMEOUT  = 45.0              # seconds


async def groq_complete(
    messages: List[dict],
    model:       Optional[str]  = None,
    max_tokens:  Optional[int]  = None,
    temperature: float          = 0.4,
    stream:      bool           = False,
    response_format: Optional[dict] = None,
) -> str:
    """
    Single Groq completion with retry + cache fallback.
    Returns response text string.
    """
    model      = model      or settings.groq_model
    max_tokens = max_tokens or settings.groq_max_tokens

    # Check cache first
    cached = get_cached(messages, model)
    if cached:
        logger.debug("Cache hit")
        return cached

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       model,
        "messages":    messages,
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "stream":      False,
    }
    if response_format:
        payload["response_format"] = response_format

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=HARD_TIMEOUT) as client:
                resp = await asyncio.wait_for(
                    client.post(GROQ_URL, headers=headers, json=payload),
                    timeout=HARD_TIMEOUT,
                )

                if resp.status_code == 429:
                    # Rate limited — wait longer
                    wait = RETRY_DELAYS[attempt] * 2
                    logger.warning(f"Groq 429 rate limit. Waiting {wait}s (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code in (500, 502, 503, 504):
                    wait = RETRY_DELAYS[attempt]
                    logger.warning(f"Groq {resp.status_code}. Retry in {wait}s (attempt {attempt+1})")
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]

                # Cache successful response
                set_cached(messages, model, text)
                return text

        except asyncio.TimeoutError:
            last_error = f"Timeout after {HARD_TIMEOUT}s"
            logger.error(f"Groq timeout (attempt {attempt+1})")
            await asyncio.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS)-1)])

        except Exception as e:
            last_error = str(e)
            logger.error(f"Groq error attempt {attempt+1}: {e}")
            await asyncio.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS)-1)])

    # All retries failed — try demo fallback
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    fallback = get_demo_fallback(user_msg)
    if fallback:
        logger.warning(f"Groq failed ({last_error}). Using demo fallback.")
        return fallback.get("reply", "Service temporarily unavailable. Please try again.")

    raise RuntimeError(f"Groq unavailable after {MAX_RETRIES} retries: {last_error}")


async def groq_json(
    messages: List[dict],
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.2,
) -> dict:
    """Groq JSON completion with retry/timeout and safe parse fallback."""
    raw = await groq_complete(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Groq returned non-JSON content for JSON request")
        return {"issues": []}


async def groq_stream(
    messages:    List[dict],
    model:       Optional[str]  = None,
    max_tokens:  Optional[int]  = None,
    temperature: float          = 0.4,
):
    """
    Async generator for streaming Groq responses.
    Yields token strings. Falls back to non-streaming on error.
    """
    model      = model      or settings.groq_model
    max_tokens = max_tokens or settings.groq_max_tokens

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       model,
        "messages":    messages,
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "stream":      True,
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=HARD_TIMEOUT) as client:
                async with client.stream("POST", GROQ_URL, headers=headers, json=payload) as resp:
                    if resp.status_code == 429:
                        await asyncio.sleep(RETRY_DELAYS[attempt] * 2)
                        continue
                    resp.raise_for_status()

                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            return
                        try:
                            token = json.loads(chunk)["choices"][0]["delta"].get("content", "")
                            if token:
                                yield token
                        except Exception:
                            continue
                    return  # success

        except (asyncio.TimeoutError, httpx.ReadTimeout):
            logger.error(f"Stream timeout attempt {attempt+1}")
            await asyncio.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS)-1)])
        except Exception as e:
            logger.error(f"Stream error attempt {attempt+1}: {e}")
            await asyncio.sleep(RETRY_DELAYS[min(attempt, len(RETRY_DELAYS)-1)])

    # Fallback — yield non-streamed response
    try:
        text = await groq_complete(messages, model, max_tokens, temperature)
        for word in text.split(" "):
            yield word + " "
            await asyncio.sleep(0.02)
    except Exception:
        yield "Service temporarily unavailable. Please try again."
