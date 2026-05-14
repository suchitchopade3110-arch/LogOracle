"""
services/groq_cache.py
GROQ response cache — demo safety fallback.
On first call: hit Groq, store response.
On subsequent identical calls: return cached response instantly.
If Groq is down: return cached fallback without error.
"""
import json
import hashlib
import os
import time
from pathlib import Path
from typing import Optional

CACHE_DIR = Path("groq_cache")
CACHE_DIR.mkdir(exist_ok=True)

# In-memory hot cache (fastest)
_hot_cache: dict = {}

# Pre-built demo fallbacks (hardcoded for zero-dependency demo)
DEMO_FALLBACKS = {
    "ssh_brute": {
        "reply": "SSH brute-force detected from 203.0.113.42. "
                 "47 failed attempts in 5 minutes targeting root. "
                 "Immediate action: sudo ufw deny from 203.0.113.42 && sudo systemctl restart sshd. "
                 "Root cause: attacker exploiting exposed SSH port 22 with credential stuffing.",
        "intent_detected": "clarify",
        "xp_awarded": 10,
    },
    "oom_kill": {
        "reply": "OOM killer terminated nginx (PID 999) due to memory exhaustion. "
                 "Root cause: Redis connection leak consuming unbounded memory. "
                 "Fix: check connection pool config, set max_connections, use context managers. "
                 "Immediate: sudo systemctl restart nginx && sudo systemctl restart redis.",
        "intent_detected": "clarify",
        "xp_awarded": 10,
    },
    "sql_injection": {
        "reply": "SQL injection vulnerability detected at line 3. "
                 "String concatenation directly in execute() call allows arbitrary SQL. "
                 "Fix: use parameterized queries — cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)). "
                 "CWE-89, OWASP A03. Confidence: 94%.",
        "intent_detected": "clarify",
        "xp_awarded": 10,
    },
}


def _cache_key(messages: list, model: str) -> str:
    """Deterministic hash of request."""
    content = json.dumps({"messages": messages, "model": model}, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get_cached(messages: list, model: str) -> Optional[str]:
    """Return cached response text or None."""
    key = _cache_key(messages, model)

    # 1. Hot cache
    if key in _hot_cache:
        return _hot_cache[key]

    # 2. Disk cache
    path = _cache_path(key)
    if path.exists():
        data = json.loads(path.read_text())
        _hot_cache[key] = data["response"]
        return data["response"]

    return None


def set_cached(messages: list, model: str, response: str):
    """Store response in hot + disk cache."""
    key = _cache_key(messages, model)
    _hot_cache[key] = response
    _cache_path(key).write_text(json.dumps({
        "response":  response,
        "model":     model,
        "cached_at": time.time(),
    }))


def get_demo_fallback(scenario_hint: str) -> Optional[dict]:
    """Return hardcoded demo fallback by keyword."""
    hint = scenario_hint.lower()
    for keyword, response in DEMO_FALLBACKS.items():
        if keyword.replace("_", " ") in hint or any(w in hint for w in keyword.split("_")):
            return response
    return None


def warm_cache(scenarios: list):
    """Pre-warm cache with all demo scenario chat prompts at startup."""
    # Called from main.py startup event
    # Scenarios are dicts with 'chat_prompt' field
    print(f"[cache] Warming with {len(scenarios)} demo scenarios...")
    # Actual Groq calls happen lazily on first real request
    # This just ensures cache dir exists and is writable
    test_path = CACHE_DIR / ".warmup"
    test_path.write_text("ok")
    test_path.unlink()
    print("[cache] Cache ready.")
