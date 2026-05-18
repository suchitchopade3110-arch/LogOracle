"""logoracle_agent/monitor.py — system resource monitor."""
import threading
import time
import httpx

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SystemMonitor:
    def __init__(self, streamer, poll_interval: float = 5.0):
        self.streamer      = streamer
        self.poll_interval = poll_interval
        self._thread       = threading.Thread(target=self._run, daemon=True)
        self._running      = False
        self._client       = httpx.Client(timeout=10.0)

    def start(self):
        if not HAS_PSUTIL:
            return
        self._running = True
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                snap = {
                    "cpu_percent":  psutil.cpu_percent(interval=1),
                    "ram_percent":  psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage("/").percent,
                    "load_avg_1m":  psutil.getloadavg()[0],
                    "cpu_count":    psutil.cpu_count(),
                }
                # POST to /analyze/performance
                self._client.post(
                    f"{self.streamer.base_url}/analyze/performance",
                    json=snap,
                )
            except Exception:
                pass
            time.sleep(self.poll_interval)
