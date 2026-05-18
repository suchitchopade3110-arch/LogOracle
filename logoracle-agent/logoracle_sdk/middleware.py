"""
logoracle_sdk/middleware.py
Optional SDK for apps to directly report API events to LogOracle.
No proxy needed — import and add to your app.

Python (requests/httpx):
    from logoracle_sdk.middleware import LogOracleMiddleware
    middleware = LogOracleMiddleware("http://localhost:8001")
    middleware.record(method="POST", url="/api/users",
                      status_code=503, latency_ms=3200)

FastAPI middleware:
    from logoracle_sdk.middleware import LogOracleFastAPIMiddleware
    app.add_middleware(LogOracleFastAPIMiddleware,
                       logoracle_url="http://localhost:8001")

Flask middleware:
    from logoracle_sdk.middleware import init_flask
    init_flask(app, logoracle_url="http://localhost:8001")
"""
import time
import threading
import httpx
from typing import Optional


class LogOracleMiddleware:
    """Standalone middleware — manually record API events."""

    def __init__(self, logoracle_url: str, flush_interval: float = 30.0):
        self.url    = logoracle_url
        self._buffer: list[dict] = []
        self._lock  = threading.Lock()
        self._client = httpx.Client(timeout=5.0)
        self._flush_interval = flush_interval
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def record(self, method: str, url: str, status_code: int,
               latency_ms: float, error: Optional[str] = None):
        with self._lock:
            self._buffer.append({
                "method":      method,
                "url":         url,
                "status_code": status_code,
                "latency_ms":  latency_ms,
                "timestamp":   time.time(),
                "error":       error,
            })

    def _run(self):
        while True:
            time.sleep(self._flush_interval)
            self._flush()

    def _flush(self):
        with self._lock:
            events = list(self._buffer)
            self._buffer.clear()
        if not events:
            return
        try:
            self._client.post(
                f"{self.url}/ingest/api_events",
                json={"events": events}
            )
        except Exception:
            pass


# ── FastAPI middleware ─────────────────────────────────────────────────────

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class LogOracleFastAPIMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, logoracle_url: str = "http://localhost:8001"):
            super().__init__(app)
            self._lo = LogOracleMiddleware(logoracle_url)

        async def dispatch(self, request: Request, call_next):
            start    = time.time()
            response = await call_next(request)
            latency  = round((time.time() - start) * 1000, 1)
            self._lo.record(
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                latency_ms=latency,
            )
            return response

except ImportError:
    pass  # starlette not installed


# ── Flask middleware ───────────────────────────────────────────────────────

def init_flask(app, logoracle_url: str = "http://localhost:8001"):
    """Add LogOracle API monitoring to a Flask app."""
    try:
        import flask
        lo = LogOracleMiddleware(logoracle_url)

        @app.before_request
        def before():
            flask.g._lo_start = time.time()

        @app.after_request
        def after(response):
            latency = round((time.time() - flask.g._lo_start) * 1000, 1)
            lo.record(
                method=flask.request.method,
                url=flask.request.url,
                status_code=response.status_code,
                latency_ms=latency,
            )
            return response

    except ImportError:
        pass

    return app
