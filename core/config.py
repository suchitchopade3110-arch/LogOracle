# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    groq_max_tokens: int = 1000
    cache_enabled: bool = True          # set False to force live GROQ calls
    cache_dir: str = "scenarios/"       # pre-built demo JSON fallback dir
    popup_cooldown_seconds: int = 300   # 5-min smart popup cooldown
    popup_confidence_threshold: float = 0.85

    class Config:
        env_file = ".env"

settings = Settings()
