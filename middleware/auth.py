"""
middleware/auth.py
API key authentication middleware.
Set in .env: API_KEY=logoracle_demo_key
Header: X-API-Key: logoracle_demo_key

Exempted routes: /health, /docs, /openapi.json, /redoc, /

Mount in main.py:
    from middleware.auth import APIKeyMiddleware
    app.add_middleware(APIKeyMiddleware)
"""
import os
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

load_dotenv()

# Routes that bypass auth
EXEMPT_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/export/pdf/preview",  # public preview
    "/badges/all",          # public badge list
    "/leaderboard",         # public leaderboard
    "/metrics/",            # Prometheus scraping
    "/metrics",             # Prometheus scraping
}

EXEMPT_PREFIXES = (
    "/stream/",   # SSE endpoints — browsers can't set custom headers on EventSource
    "/demo/",     # demo endpoints — public for judges
)


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str = ""):
        super().__init__(app)
        self.api_key = api_key or os.environ.get("API_KEY", "")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth if no key configured (dev mode)
        if not self.api_key:
            return await call_next(request)

        # Exempt paths
        if path in EXEMPT_PATHS:
            return await call_next(request)
        if any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
            return await call_next(request)

        # Check header
        provided = request.headers.get("X-API-Key", "")
        if provided != self.api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error":   "unauthorized",
                    "message": "Missing or invalid X-API-Key header.",
                    "hint":    "Set X-API-Key: <your_key> in request headers.",
                },
            )

        return await call_next(request)
