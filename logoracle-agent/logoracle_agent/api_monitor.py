"""
logoracle_agent/api_monitor.py
Monitors outgoing HTTP calls by running a local proxy server.
Intercepts requests, records events, flushes to /analyze/api.

How it works:
  1. Starts a local HTTP proxy on port 8888
  2. App routes HTTP through it via HTTP_PROXY env var
  3. Proxy records every request/response (method, url, status, latency)
  4. Every 30s → POST /analyze/api with accumulated events
  5. Findings returned → streamed to backend → website shows alerts

Usage:
  logoracle-agent --watch /var/log/syslog --api

The agent prints:
  ✓ API proxy active on port 8888
  Set HTTP_PROXY=http://localhost:8888 in your app

Alternative (no proxy needed):
  App directly POSTs to /ingest/api_events
  Agent reads those events and analyzes
"""
import threading
import time
import json
import socket
import select
import httpx
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, urlunparse
from rich.console import Console

console = Console()

PROXY_PORT     = 8888
FLUSH_INTERVAL = 30.0   # analyze every 30s
MAX_EVENTS     = 500    # ring buffer size


class APIEvent:
    def __init__(self, method, url, status_code, latency_ms, error=None):
        self.method      = method
        self.url         = url
        self.status_code = status_code
        self.latency_ms  = latency_ms
        self.timestamp   = time.time()
        self.error       = error

    def to_dict(self) -> dict:
        return {
            "method":      self.method,
            "url":         self.url,
            "status_code": self.status_code,
            "latency_ms":  self.latency_ms,
            "timestamp":   self.timestamp,
            "error":       self.error,
        }


class EventBuffer:
    """Thread-safe ring buffer for API events."""
    def __init__(self, maxsize=MAX_EVENTS):
        self._events = deque(maxlen=maxsize)
        self._lock   = threading.Lock()

    def add(self, event: APIEvent):
        with self._lock:
            self._events.append(event)

    def drain(self) -> list[APIEvent]:
        with self._lock:
            events = list(self._events)
            self._events.clear()
            return events

    def __len__(self):
        with self._lock:
            return len(self._events)


# Global buffer shared across proxy handler instances
_buffer = EventBuffer()


class ProxyHandler(BaseHTTPRequestHandler):
    """
    Simple HTTP proxy that records request/response metrics.
    Supports HTTP (not HTTPS — use alternative ingest for HTTPS).
    """

    def log_message(self, format, *args):
        pass  # suppress default proxy logs

    def do_GET(self):    self._proxy("GET")
    def do_POST(self):   self._proxy("POST")
    def do_PUT(self):    self._proxy("PUT")
    def do_DELETE(self): self._proxy("DELETE")
    def do_PATCH(self):  self._proxy("PATCH")
    def do_HEAD(self):   self._proxy("HEAD")

    def do_CONNECT(self):
        """HTTPS tunnel — just pass through, record attempt."""
        host, _, port = self.path.partition(":")
        try:
            remote = socket.create_connection((host, int(port or 443)), timeout=10)
            self.send_response(200, "Connection established")
            self.end_headers()
            # Tunnel data
            self._tunnel(self.connection, remote)
        except Exception as e:
            self.send_error(502, str(e))

    def _tunnel(self, client, remote):
        """Bidirectional tunnel for HTTPS CONNECT."""
        try:
            while True:
                r, _, _ = select.select([client, remote], [], [], 5)
                if not r:
                    break
                for s in r:
                    data = s.recv(4096)
                    if not data:
                        return
                    (remote if s is client else client).sendall(data)
        except Exception as e:
            console.print(f"[dim]⚠ API flush failed: {e}[/dim]")
        finally:
            try: remote.close()
            except: pass

    def _proxy(self, method: str):
        """Forward request and record metrics."""
        start    = time.time()
        url      = self.path
        status   = 0
        error    = None

        try:
            # Read request body
            length  = int(self.headers.get("Content-Length", 0))
            body    = self.rfile.read(length) if length else b""

            # Forward headers (filter hop-by-hop)
            headers = {
                k: v for k, v in self.headers.items()
                if k.lower() not in (
                    "host", "proxy-connection", "proxy-authenticate",
                    "proxy-authorization", "te", "trailers",
                    "transfer-encoding", "upgrade"
                )
            }

            # Make request
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                resp = client.request(method, url, headers=headers, content=body)

            status = resp.status_code

            # Send response back to original caller
            self.send_response(status)
            for k, v in resp.headers.items():
                if k.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.content)

        except Exception as e:
            error  = str(e)
            status = 502
            self.send_error(502, error)

        finally:
            latency = round((time.time() - start) * 1000, 1)
            _buffer.add(APIEvent(method, url, status, latency, error))


class APIMonitor:
    """
    Runs proxy + periodic flush to /analyze/api.
    """
    def __init__(self, base_url: str, proxy_port: int = PROXY_PORT):
        self.base_url   = base_url
        self.proxy_port = proxy_port
        self._server    = None
        self._proxy_thread  = threading.Thread(target=self._run_proxy, daemon=True)
        self._flush_thread  = threading.Thread(target=self._run_flush, daemon=True)
        self._running   = False
        self._client    = httpx.Client(timeout=10.0)
        self.analyses   = 0
        self.findings   = 0
        self.last_finding = None

    def start(self):
        self._running = True
        self._proxy_thread.start()
        self._flush_thread.start()
        console.print(f"[green]✓ API proxy active on port {self.proxy_port}[/green]")
        console.print(f"[dim]  Set HTTP_PROXY=http://localhost:{self.proxy_port} in your app[/dim]")

    def stop(self):
        self._running = False
        if self._server:
            self._server.shutdown()

    def pending_count(self) -> int:
        return len(_buffer)

    def _run_proxy(self):
        try:
            self._server = HTTPServer(("localhost", self.proxy_port), ProxyHandler)
            self._server.serve_forever()
        except OSError as e:
            console.print(f"[red]✗ API proxy failed to start: {e}[/red]")
            console.print(f"[yellow]  Port {self.proxy_port} may be in use. Try --api-port 8889[/yellow]")

    def _run_flush(self):
        """Periodically drain buffer and send to /analyze/api."""
        while self._running:
            time.sleep(FLUSH_INTERVAL)
            self._flush()

    def _flush(self):
        events = _buffer.drain()
        if not events:
            return

        try:
            r = self._client.post(
                f"{self.base_url}/analyze/api",
                json={"events": [e.to_dict() for e in events]},
            )
            if r.status_code == 200:
                data     = r.json()
                findings = data.get("findings", [])
                self.analyses += 1
                self.findings += len(findings)

                for f in findings:
                    self.last_finding = f.get("message", "")[:60]
                    if f.get("severity") == "CRITICAL":
                        console.print(
                            f"\n[bold red]🌐 API AGENT CRITICAL[/bold red] "
                            f"{f['message']}"
                        )
        except Exception:
            pass

    def ingest_direct(self, events: list[dict]):
        """
        Alternative to proxy — app directly sends events here.
        Call from app SDK or middleware.
        """
        for e in events:
            _buffer.add(APIEvent(
                e.get("method", "GET"),
                e.get("url", ""),
                e.get("status_code", 0),
                e.get("latency_ms", 0),
                e.get("error"),
            ))
