"""
middleware/rate_limit.py
Rate limiting via slowapi.
Install: pip install slowapi

Mount in main.py:
    from middleware.rate_limit import limiter, rate_limit_handler
    from slowapi.errors import RateLimitExceeded
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

Then on each route:
    from middleware.rate_limit import limiter
    from fastapi import Request

    @router.post("/chat")
    @limiter.limit("20/minute")
    async def chat(request: Request, req: ChatRequest):
        ...
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

# Key by IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error":   "rate_limit_exceeded",
            "message": f"Too many requests. Limit: {exc.detail}. Try again shortly.",
            "retry_after": 60,
        },
        headers={"Retry-After": "60"},
    )


# Per-endpoint limits to apply as decorators
LIMITS = {
    "chat":           "20/minute",
    "analyze_log":    "30/minute",
    "analyze_code":   "30/minute",
    "analyze_hallu":  "30/minute",
    "quiz_generate":  "30/minute",
    "quiz_answer":    "60/minute",
    "heal_preview":   "20/minute",
    "heal_approve":   "10/minute",
    "export_pdf":     "10/minute",
    "demo_run":       "60/minute",
    "leaderboard":    "60/minute",
    "default":        "100/minute",
}

PATH_LIMITS = (
    ("/chat", 20),
    ("/analyze/log", 30),
    ("/analyze/code", 30),
    ("/analyze/hallucination", 30),
    ("/quiz/generate", 30),
    ("/quiz/answer", 60),
    ("/heal/preview", 20),
    ("/heal/approve", 10),
    ("/export/pdf", 10),
    ("/demo/run", 60),
    ("/leaderboard", 60),
)

EXEMPT_PREFIXES = (
    "/stream/",
    "/docs",
    "/redoc",
    "/openapi.json",
)

EXEMPT_PATHS = {"/", "/health"}

_buckets: dict[tuple[str, str], list[float]] = {}


def _path_limit(path: str) -> int:
    for prefix, limit in PATH_LIMITS:
        if path.startswith(prefix):
            return limit
    return 100


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple per-IP, per-path-prefix fixed-window limiter."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in EXEMPT_PATHS or any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
            return await call_next(request)

        limit = _path_limit(path)
        now = time.time()
        key = (request.client.host if request.client else "unknown", path)
        window = [ts for ts in _buckets.get(key, []) if now - ts < 60]

        if len(window) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Limit: {limit}/minute. Try again shortly.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        window.append(now)
        _buckets[key] = window
        return await call_next(request)
