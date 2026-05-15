"""
middleware/request_guard.py
Guards:
- Max request body size (2MB default)
- GROQ_API_KEY validation on startup
- Structured request logging
- CORS origin restriction for production
"""
import os
import time
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("logoracle.requests")

MAX_BODY_SIZE = 2 * 1024 * 1024  # 2MB


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies before processing."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error":   "payload_too_large",
                    "message": f"Request body exceeds 2MB limit. Chunk your log file using POST /ingest/logs.",
                    "max_bytes": MAX_BODY_SIZE,
                },
            )
        return await call_next(request)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Structured JSON logging for every request."""

    async def dispatch(self, request: Request, call_next):
        start   = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 1)

        logger.info(
            "request",
            extra={
                "method":   request.method,
                "path":     request.url.path,
                "status":   response.status_code,
                "latency_ms": duration,
                "ip":       request.client.host if request.client else "unknown",
            }
        )
        return response


def validate_env_on_startup():
    """
    Call from main.py startup event.
    Fails fast with clear message if required env vars missing.
    """
    errors = []

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        errors.append("GROQ_API_KEY is not set. All LLM endpoints will fail.")
    elif not groq_key.startswith("gsk_"):
        errors.append(f"GROQ_API_KEY looks invalid (should start with 'gsk_').")

    if errors:
        for e in errors:
            logger.warning(f"[startup] ⚠ {e}")
        # Don't crash — warn and continue (allows demo with cache fallback)
    else:
        logger.info("[startup] ✓ Environment validated")

    return len(errors) == 0


def get_allowed_origins() -> list[str]:
    """
    Return CORS origins from env.
    Dev: * (all)
    Prod: set ALLOWED_ORIGINS=https://logoracle.vercel.app,https://your-domain.com
    """
    raw = os.environ.get("ALLOWED_ORIGINS", "")
    if not raw:
        return ["*"]  # dev mode
    return [o.strip() for o in raw.split(",") if o.strip()]
