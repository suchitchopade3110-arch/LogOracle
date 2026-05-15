import json
from core.config import settings
from llm.cache import load_cache, save_cache
from services.groq_client import groq_complete as hardened_groq_complete
from services.groq_client import groq_json as hardened_groq_json
from services.groq_client import groq_stream as hardened_groq_stream

async def groq_complete(
    messages: list[dict],
    max_tokens: int = 1000,
    temperature: float = 0.4,
) -> str:
    """Call GROQ chat completions and return the assistant text."""
    return await hardened_groq_complete(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

async def groq_stream(
    messages: list[dict],
    max_tokens: int = 1000,
    temperature: float = 0.4,
):
    async for token in hardened_groq_stream(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    ):
        yield token

async def groq_json(
    messages: list[dict],
    max_tokens: int = 1000,
    temperature: float = 0.2,
    cache_key: str | None = None,
) -> dict:
    if settings.cache_enabled and cache_key:
        cached = load_cache(cache_key)
        if cached:
            return cached

    result = await hardened_groq_json(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    if settings.cache_enabled and cache_key:
        save_cache(cache_key, result)
    return result

async def groq_analyze(event: dict, mode: str = "log") -> dict:
    """
    Call GROQ LLaMA 3.1. Return structured finding dict.
    Falls back to cache if cache_enabled=True and cache hit exists.
    """
    cache_key = f"{mode}:{hash(str(event))}"

    if settings.cache_enabled:
        cached = load_cache(cache_key)
        if cached:
            return cached

    prompt = _build_prompt(event, mode)
    raw = await hardened_groq_complete(
        messages=[{"role": "user", "content": prompt}],
    )

    result = _parse_response(raw)
    if settings.cache_enabled:
        save_cache(cache_key, result)
    return result

def _build_prompt(event: dict, mode: str) -> str:
    # Load from prompts/ dir
    import os
    prompt_file = os.path.join("llm", "prompts", f"{mode}_analysis.txt")
    with open(prompt_file) as f:
        template = f.read()
    return template.replace("{{EVENT}}", json.dumps(event))

def _parse_response(raw: str) -> dict:
    """Extract structured fields from LLM response. Fallback to defaults."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "severity": "INFO",
            "message": raw[:200],
            "confidence": 0.5,
            "fix": None,
        }


# llm/cache.py
import json
import os

CACHE_DIR = "llm/response_cache/"

def load_cache(key: str) -> dict | None:
    path = _path(key)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def save_cache(key: str, data: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_path(key), "w") as f:
        json.dump(data, f)

def _path(key: str) -> str:
    safe_key = str(abs(hash(key)))
    return os.path.join(CACHE_DIR, f"{safe_key}.json")
