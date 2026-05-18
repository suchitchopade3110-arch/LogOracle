import json
import os
import hashlib

CACHE_DIR = "llm/response_cache/"


def cache_key_for(namespace: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


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
