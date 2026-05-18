# llm/groq_client.py
import httpx
import json
from core.config import settings
from llm.cache import load_cache, save_cache

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

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
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.groq_model,
        "max_tokens": settings.groq_max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(GROQ_URL, headers=headers, json=payload)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]

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
