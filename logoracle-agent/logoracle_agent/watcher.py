"""logoracle_agent/watcher.py — tails a single log file."""
import os
import threading
import time


class LogWatcher:
    def __init__(self, path: str, streamer, interval: float = 2.0):
        self.path     = path
        self.streamer = streamer
        self.interval = interval
        self._offset  = os.path.getsize(path) if os.path.exists(path) else 0
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._running = False
        self._buffer: list[str] = []

    def start(self):
        self._running = True
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                size = os.path.getsize(self.path)
                if size > self._offset:
                    with open(self.path, "r", errors="replace") as f:
                        f.seek(self._offset)
                        new_data = f.read()
                        self._offset = f.tell()
                    lines = [l for l in new_data.splitlines() if l.strip()]
                    if lines:
                        self.streamer.ingest(lines, source=f"file:{self.path}")
                elif size < self._offset:
                    # File rotated
                    self._offset = 0
            except Exception:
                pass
            time.sleep(self.interval)
