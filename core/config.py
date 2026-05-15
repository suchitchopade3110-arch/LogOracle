# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    groq_max_tokens: int = 1000
    cache_enabled: bool = True          # set False to force live GROQ calls
    cache_dir: str = "scenarios/"       # pre-built demo JSON fallback dir
    popup_cooldown_seconds: int = 300   # 5-min smart popup cooldown
    popup_confidence_threshold: float = 0.85
    api_key: str = ""
    allowed_origins: str = "*"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_pass: str = ""
    db_user: str = "logoracle"
    db_pass: str = ""
    db_name: str = "logoracle"
    db_host: str = "db"
    db_port: int = 5432
    vault_addr: str = "http://vault:8200"
    vault_token: str = ""
    vault_required: bool = False

    class Config:
        env_file = ".env"

settings = Settings()


def load_secret(path: str, key: str) -> Optional[str]:
    """Read a Vault KV-v2 secret, returning None when Vault is optional/unavailable."""
    if not settings.vault_token:
        return None
    try:
        import httpx
        resp = httpx.get(
            f"{settings.vault_addr}/v1/secret/data/{path}",
            headers={"X-Vault-Token": settings.vault_token},
            timeout=3.0,
        )
        if resp.status_code == 200:
            return resp.json()["data"]["data"].get(key)
    except Exception:
        pass
    return None


def get_secret(path: str, key: str, env_fallback: str) -> str:
    """Try Vault first, then env, and fail closed when VAULT_REQUIRED=true."""
    value = load_secret(path, key)
    if value:
        return value
    if settings.vault_required:
        raise RuntimeError(
            f"VAULT_REQUIRED=true but could not read {path}/{key} from Vault."
        )
    return env_fallback
