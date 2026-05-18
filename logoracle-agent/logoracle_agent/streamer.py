"""logoracle_agent/streamer.py — HTTP streamer to LogOracle backend."""
import threading
from datetime import datetime

import httpx


_findings_ref = None


def _set_findings_ref(deq):
    """Register the TUI findings deque without importing main.py here."""
    global _findings_ref
    _findings_ref = deq


class Streamer:
    def __init__(self, base_url: str, mode: str = "tech", dev_id: str = ""):
        self.base_url        = base_url
        self.mode            = mode
        self.dev_id          = dev_id
        self.lines_sent      = 0
        self.analyses_done   = 0
        self.critical_count  = 0
        self.warning_count   = 0
        self.last_finding    = None
        self._lock           = threading.Lock()
        self._buffer: list[str] = []
        self._client         = httpx.Client(timeout=15.0)
        self._chat_callback  = None
        self._last_findings  = []

    def set_chat_callback(self, fn):
        """Register a callback that receives chatbot status and reply lines."""
        self._chat_callback = fn

    def ingest(self, lines: list[str], source: str = "agent"):
        """Receive new log lines, buffer them, flush to backend."""
        with self._lock:
            self._buffer.extend(lines)
            self.lines_sent += len(lines)

        # Send to /ingest/logs immediately
        try:
            self._client.post(
                f"{self.base_url}/ingest/logs",
                json={"lines": lines, "source": source},
            )
        except Exception:
            pass

        # Analyze every 20+ lines
        with self._lock:
            if len(self._buffer) < 20:
                return
            batch = self._buffer[:]
            self._buffer.clear()

        threading.Thread(target=self._analyze, args=(batch,), daemon=True).start()

    def _analyze(self, lines: list[str]):
        """POST to /analyze/log, update counters."""
        try:
            r = self._client.post(
                f"{self.base_url}/analyze/log",
                json={
                    "log_text":   "\n".join(lines),
                    "redact_pii": True,
                    "mode":       self.mode,
                },
            )
            if r.status_code == 200:
                data = r.json()
                findings = data.get("security_findings", [])
                with self._lock:
                    self.analyses_done += 1
                    self.critical_count += sum(1 for f in findings if f.get("severity") == "CRITICAL")
                    self.warning_count  += sum(1 for f in findings if f.get("severity") in ("WARNING", "HIGH"))
                    if findings:
                        self.last_finding = findings[0].get("message", "")[:60]
                        self._last_findings = findings

                if _findings_ref is not None:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    for finding in findings:
                        _findings_ref.appendleft(
                            {
                                "time": timestamp,
                                "severity": finding.get("severity", "INFO"),
                                "message": finding.get("message", "")[:80],
                            }
                        )

                criticals = [f for f in findings if f.get("severity") == "CRITICAL"]
                for finding in criticals[:1]:
                    threading.Thread(
                        target=self._ask_chatbot,
                        args=(finding, findings),
                        daemon=True,
                    ).start()
        except Exception:
            pass

    def _ask_chatbot(self, finding: dict, all_findings: list):
        """Ask the backend chatbot for a concise response to a CRITICAL finding."""
        if not self._chat_callback:
            return

        chat_findings = [
            {
                "agent": finding.get("agent", "security"),
                "severity": finding.get("severity", "CRITICAL"),
                "message": finding.get("message", ""),
                "confidence": finding.get("confidence", 0.9),
                "fix": finding.get("fix", ""),
                "cwe_id": finding.get("cwe_id"),
                "finding_id": finding.get("finding_id") or finding.get("id", ""),
            }
        ]
        payload = {
            "message": (
                f"CRITICAL finding detected: {finding.get('message', '')}. "
                "Explain what happened, why it's dangerous, and what to do immediately. "
                "Be concise - 3 sentences max."
            ),
            "session_id": "agent-auto",
            "persona": "security",
            "mode": self.mode,
            "session_context": {
                "findings": chat_findings,
                "last_log_lines": "",
                "code_diff": "",
            },
        }

        try:
            self._chat_callback(
                "system",
                f"🤖 Auto-querying chatbot for: {finding.get('message', '')[:50]}...",
            )
            response = self._client.post(
                f"{self.base_url}/chat/sync",
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            reply = data.get("reply", "").strip()
            if reply:
                self._chat_callback("chatbot", reply)
            else:
                self._chat_callback("error", "Chatbot returned empty reply")
        except Exception as exc:
            self._chat_callback("error", f"Chatbot unavailable: {str(exc)[:60]}")
