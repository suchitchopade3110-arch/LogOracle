#!/usr/bin/env python3
"""
LogOracle Terminal Agent - Textual TUI Edition (Windows)
Usage:
  python logoracle_cli.py --watch <logfile>
  python logoracle_cli.py --ingest <logfile>
  python logoracle_cli.py --paste

Requires:
  pip install textual httpx
"""

import argparse
import asyncio
import os
import sys
import time
from collections import deque
from datetime import datetime
from typing import Any

import httpx
from rich.style import Style
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, DataTable, Footer, Header, Label, RichLog, Static

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional fallback
    def load_dotenv() -> bool:
        return False


load_dotenv()

BASE_URL = "http://localhost:8001"
API_KEY = os.getenv("LOGORACLE_API_KEY") or os.getenv("API_KEY") or ""
MAX_REQUEST_BYTES = 1_500_000
MAX_FINDINGS = 50
MAX_UI_LOG_LINES = 250
RECENT_CONTEXT_LINES = 500
LOG_QUEUE_SIZE = 1000
HEALTH_POLL_SECONDS = 5.0

_context_lines: deque[str] = deque(maxlen=RECENT_CONTEXT_LINES)
_findings: deque[dict[str, Any]] = deque(maxlen=MAX_FINDINGS)
_stats = {
    "lines_seen": 0,
    "analyses_done": 0,
    "criticals": 0,
    "warnings": 0,
    "backend_ok": False,
    "watch_path": "",
    "mode": "watch",
    "start_time": time.time(),
}

SEVERITY_STYLE = {
    "CRITICAL": Style(color="red", bold=True),
    "HIGH": Style(color="red"),
    "WARNING": Style(color="yellow", bold=True),
    "MEDIUM": Style(color="yellow"),
    "LOW": Style(color="green"),
    "INFO": Style(color="cyan"),
}

LOGO = (
    "                                                                          \n"
    "  _                          ___                  _                       \n"
    " | |    ___   __ _   ___    / _ \\  _ __ __ _  ___| | ___                  \n"
    " | |   / _ \\ / _` | |___|  | | | || '__/ _` |/ __| |/ _ \\                 \n"
    " | |__| (_) | (_| |  ___   | |_| || | | (_| | (__| |  __/                 \n"
    " |_____\\___/ \\__, | |___|   \\___/ |_|  \\__,_|\\___|_|\\___|                 \n"
    "             |___/                                                        \n"
    "                                                                          \n"
    "          AUTONOMOUS  DEBUG  INTELLIGENCE                                 \n"
    "          v1.0   *   HACKATHON 2026                                       \n"
)

def trim_text(text: str, limit: int = 300) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def build_headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def best_fix(finding: dict[str, Any]) -> str:
    for key in ("fix", "recommendation", "fix_linux", "fix_windows", "fix_linux_plain"):
        value = finding.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_findings(data: dict[str, Any]) -> list[dict[str, Any]]:
    findings = data.get("findings")
    if isinstance(findings, list):
        return [finding for finding in findings if isinstance(finding, dict)]

    findings = data.get("security_findings")
    if isinstance(findings, list):
        normalized = []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            item = dict(finding)
            item.setdefault("agent", "security")
            item.setdefault("fix", best_fix(item))
            normalized.append(item)
        return normalized

    return []


def chunk_lines(lines: list[str], max_bytes: int = MAX_REQUEST_BYTES) -> list[list[str]]:
    batches: list[list[str]] = []
    current_batch: list[str] = []
    current_bytes = 0

    for line in lines:
        line_bytes = len((line + "\n").encode("utf-8", errors="replace"))
        if current_batch and current_bytes + line_bytes > max_bytes:
            batches.append(current_batch)
            current_batch = [line]
            current_bytes = line_bytes
            continue
        current_batch.append(line)
        current_bytes += line_bytes

    if current_batch:
        batches.append(current_batch)

    return batches


def build_chat_context() -> dict[str, Any]:
    findings = []
    for finding in list(_findings):
        findings.append(
            {
                "agent": finding.get("agent", "security"),
                "severity": finding.get("severity", "INFO"),
                "message": finding.get("message", ""),
                "confidence": float(finding.get("confidence", 0.0) or 0.0),
                "fix": best_fix(finding) or None,
                "cwe_id": finding.get("cwe_id"),
            }
        )

    return {
        "findings": findings,
        "last_log_lines": "\n".join(list(_context_lines)[-RECENT_CONTEXT_LINES:]),
        "code_diff": "",
        "chat_history": [],
        "developer_profile": {
            "expertise_level": "intermediate",
            "past_quiz_scores": [],
            "badges": [],
        },
    }


def remember_raw_lines(lines: list[str]) -> None:
    for line in lines:
        _context_lines.append(line)


def enqueue_log(log_queue: asyncio.Queue, text: str) -> None:
    try:
        log_queue.put_nowait({"kind": "log", "text": text})
    except asyncio.QueueFull:
        pass


def enqueue_finding(log_queue: asyncio.Queue, finding: dict[str, Any]) -> None:
    try:
        log_queue.put_nowait({"kind": "finding", **finding})
    except asyncio.QueueFull:
        pass


async def wait_for_stop(stop_event: asyncio.Event, seconds: float) -> None:
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
    except (TimeoutError, asyncio.TimeoutError, Exception):
        pass


async def check_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5, headers=build_headers()) as client:
            response = await client.get(f"{BASE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False


async def ingest_lines(lines: list[str], source: str) -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=20, headers=build_headers()) as client:
            response = await client.post(
                f"{BASE_URL}/ingest/logs",
                json={"lines": lines, "source": source},
            )
            if response.status_code == 401:
                return False, "Backend requires X-API-Key for /ingest/logs."
            response.raise_for_status()
            return True, f"Ingested {len(lines)} lines into SSE stream."
    except Exception as exc:
        return False, trim_text(str(exc), 220)


async def analyze_log(log_text: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=60, headers=build_headers()) as client:
            response = await client.post(
                f"{BASE_URL}/analyze/log",
                json={"log_text": log_text, "mode": "plain"},
            )
            if response.status_code == 401:
                return {"error": "Backend requires X-API-Key for /analyze/log."}
            if response.status_code == 413:
                return {"error": "Payload too large for /analyze/log."}
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {"error": f"Cannot connect to {BASE_URL}. Is backend running?"}
    except Exception as exc:
        return {"error": trim_text(str(exc), 220)}


async def auto_chat(finding_msg: str) -> str:
    payload = {
        "message": f"Explain this CRITICAL finding and suggest a concrete fix: {finding_msg}",
        "persona": "security",
        "mode": "plain",
        "session_id": "cli-agent",
        "session_context": build_chat_context(),
    }

    try:
        async with httpx.AsyncClient(timeout=25, headers=build_headers()) as client:
            response = await client.post(f"{BASE_URL}/chat/sync", json=payload)
            if response.status_code == 401:
                return "Backend requires X-API-Key for /chat/sync."
            response.raise_for_status()
            data = response.json()
            return trim_text(
                data.get("reply") or data.get("response") or data.get("message") or "",
                300,
            )
    except Exception as exc:
        return f"Chatbot unavailable: {trim_text(str(exc), 220)}"


def severity_to_text(severity: str) -> Text:
    return Text(severity, style=SEVERITY_STYLE.get(severity.upper(), Style()))


def style_log_line(text: str) -> Text:
    upper = text.upper()
    if text.startswith("[CHATBOT]"):
        return Text(text, style="bold magenta")
    if text.startswith("[AUTO]"):
        return Text(text, style="bold cyan")
    if text.startswith("[OK]"):
        return Text(text, style="green")
    if "[CRITICAL]" in upper or " CRITICAL " in f" {upper} " or " ERROR" in f" {upper}" or " FAIL" in f" {upper}":
        return Text(text, style="bold red")
    if "[HIGH]" in upper:
        return Text(text, style="red")
    if "[WARNING]" in upper or "[WARN]" in upper or "[MEDIUM]" in upper:
        return Text(text, style="yellow")
    if "[LOW]" in upper:
        return Text(text, style="green")
    return Text(text, style="white")


class LogoWidget(Static):
    def render(self) -> Text:
        return Text(LOGO, style="bold cyan", no_wrap=True)


class StatsWidget(Static):
    def on_mount(self) -> None:
        self.set_interval(1.0, self.refresh)

    def render(self) -> Text:
        uptime_seconds = int(time.time() - _stats["start_time"])
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        backend_dot = "[green]●[/green]" if _stats["backend_ok"] else "[red]●[/red]"

        body = (
            "[bold cyan]── STATUS ─────────────────────────[/bold cyan]\n"
            f"  Backend    {backend_dot} {BASE_URL}\n"
            f"  Mode       [yellow]{_stats['mode'].upper()}[/yellow]\n"
            f"  Watch      [dim]{_stats['watch_path'] or 'N/A'}[/dim]\n"
            f"  Uptime     [cyan]{uptime}[/cyan]\n\n"
            "[bold cyan]── LIVE STATS ─────────────────────[/bold cyan]\n"
            f"  Lines      [white]{_stats['lines_seen']}[/white]\n"
            f"  Analyses   [white]{_stats['analyses_done']}[/white]\n"
            f"  Criticals  [red]{_stats['criticals']}[/red]\n"
            f"  Warnings   [yellow]{_stats['warnings']}[/yellow]\n"
        )
        return Text.from_markup(body)


class FindingsWidget(DataTable):
    def on_mount(self) -> None:
        self.add_columns("Sev", "Time", "Agent", "Message")
        self.cursor_type = "row"

    def sync_rows(self) -> None:
        self.clear(columns=False)
        for finding in list(_findings):
            severity = finding.get("severity", "INFO")
            timestamp = finding.get("ts", "")
            agent = finding.get("agent", "?")
            message = trim_text(finding.get("message", finding.get("description", "")), 80)
            self.add_row(severity_to_text(severity), timestamp, agent, message)
        if self.row_count:
            self.move_cursor(row=self.row_count - 1)


class LogOracleApp(App[None]):
    CSS = """
    Screen {
        background: #0d1117;
    }
    Header {
        background: #161b22;
        color: cyan;
    }
    #chat-panel {
        height: 0;
        border: solid #238636;
    }
    #chat-panel.visible {
        height: 3;
    }
    #chat-input {
        background: #0d1117;
        color: white;
        border: none;
    }
    Footer {
        background: #161b22;
    }
    #left-panel {
        width: 76;
        border: solid #30363d;
        padding: 1;
    }
    #right-panel {
        width: 1fr;
    }
    #right-top {
        height: 3fr;
        border: solid #30363d;
    }
    #right-bottom {
        height: 2fr;
        border: solid #30363d;
        margin-top: 1;
    }
    #log-label, #findings-label {
        background: #161b22;
        padding: 0 1;
    }
    #log-label {
        color: cyan;
    }
    #findings-label {
        color: yellow;
    }
    LogoWidget {
        height: 11;
        width: 70;
        content-align: left top;
        color: cyan;
        padding: 0;
    }
    StatsWidget {
        color: white;
        height: auto;
    }
    RichLog {
        height: 1fr;
    }
    FindingsWidget {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit_app", "Quit"),
        ("c", "clear_log", "Clear Log"),
        ("f", "clear_findings", "Clear Findings"),
        ("t", "toggle_chat", "Chat"),
    ]

    def __init__(self, log_queue: asyncio.Queue, stop_event: asyncio.Event, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._log_queue = log_queue
        self._stop_event = stop_event

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="left-panel"):
                yield LogoWidget()
                yield StatsWidget()
            with Vertical(id="right-panel"):
                with Container(id="right-top"):
                    yield Label("  ▸ LIVE LOG TAIL", id="log-label")
                    yield RichLog(
                        id="log-view",
                        wrap=True,
                        highlight=False,
                        markup=False,
                        auto_scroll=True,
                        max_lines=MAX_UI_LOG_LINES,
                    )
                with Container(id="right-bottom"):
                    yield Label("  ▸ FINDINGS", id="findings-label")
                    yield FindingsWidget(id="findings-table")
        with Container(id="chat-panel"):
            yield Label("  ▸ CHAT  [t to hide]", id="chat-label")
            yield Input(placeholder="Ask LogOracle...", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "LogOracle Agent"
        self.sub_title = BASE_URL
        self.set_interval(0.2, self._drain_queue)

    def _drain_queue(self) -> None:
        log_view = self.query_one("#log-view", RichLog)
        findings_table = self.query_one("#findings-table", FindingsWidget)

        try:
            while True:
                item = self._log_queue.get_nowait()
                if item.get("kind") == "finding":
                    _findings.append(item)
                    findings_table.sync_rows()
                else:
                    log_view.write(style_log_line(item.get("text", "")))
        except asyncio.QueueEmpty:
            pass

    def action_quit_app(self) -> None:
        self._stop_event.set()
        self.exit()

    def action_clear_log(self) -> None:
        _context_lines.clear()
        self.query_one("#log-view", RichLog).clear()

    def action_clear_findings(self) -> None:
        _findings.clear()
        self.query_one("#findings-table", FindingsWidget).sync_rows()

    def action_toggle_chat(self) -> None:
        panel = self.query_one("#chat-panel")
        if "visible" in panel.classes:
            panel.remove_class("visible")
        else:
            panel.add_class("visible")
            self.query_one("#chat-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        msg = event.value.strip()
        if not msg:
            return
        event.input.value = ""
        panel = self.query_one("#chat-panel")
        panel.remove_class("visible")
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(Text(f"[YOU] {msg}", style="bold green"))
        self.refresh()
        import asyncio as _a
        _a.create_task(self._chat_request(msg))

    async def _chat_request(self, msg: str) -> None:
        import httpx as _h
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(Text("[CHATBOT] thinking...", style="dim magenta"))
        try:
            async with _h.AsyncClient(timeout=30) as c:
                r = await c.post(f"{BASE_URL}/chat/sync", json={"message": msg, "session_id": "cli-chat", "persona": "security", "mode": "plain", "session_context": {"findings": [], "last_log_lines": "", "code_diff": "", "chat_history": [], "developer_profile": {"expertise_level": "intermediate", "past_quiz_scores": [], "badges": []}}})
                data = r.json()
                reply = data.get("reply") or data.get("response") or data.get("message") or str(data)
                log_view.write(Text(f"[CHATBOT] {reply[:500]}", style="bold magenta"))
        except Exception as e:
            log_view.write(Text(f"[CHATBOT] Error: {e}", style="red"))


async def health_monitor(log_queue: asyncio.Queue, stop_event: asyncio.Event) -> None:
    previous_status: bool | None = None
    try:
        while not stop_event.is_set():
            current_status = await check_health()
            _stats["backend_ok"] = current_status
            if previous_status is not None and current_status != previous_status:
                if current_status:
                    enqueue_log(log_queue, "[AUTO] Backend connection restored.")
                else:
                    enqueue_log(log_queue, "[AUTO] Backend connection lost.")
            previous_status = current_status
            await wait_for_stop(stop_event, HEALTH_POLL_SECONDS)
    except asyncio.CancelledError:  # pragma: no cover - shutdown path
        pass


def emit_tail(lines: list[str], log_queue: asyncio.Queue) -> None:
    if len(lines) > MAX_UI_LOG_LINES:
        enqueue_log(
            log_queue,
            f"[AUTO] Loaded {len(lines)} lines. Showing last {MAX_UI_LOG_LINES} in the live tail.",
        )
        lines = lines[-MAX_UI_LOG_LINES:]

    for line in lines:
        enqueue_log(log_queue, line)


async def run_agent(
    mode: str,
    target: str,
    log_queue: asyncio.Queue,
    stop_event: asyncio.Event,
    pasted_lines: list[str] | None = None,
) -> None:
    _stats["mode"] = mode
    _stats["watch_path"] = target

    async def process_batch(lines: list[str], source: str) -> None:
        if not lines or stop_event.is_set():
            return

        batches = chunk_lines(lines)
        if len(batches) > 1:
            enqueue_log(
                log_queue,
                f"[AUTO] Split {len(lines)} lines into {len(batches)} chunks for backend size limits.",
            )

        for index, batch in enumerate(batches, 1):
            if stop_event.is_set():
                return

            chunk_suffix = f" (chunk {index}/{len(batches)})" if len(batches) > 1 else ""
            ok, ingest_message = await ingest_lines(batch, source=source)
            if ok:
                enqueue_log(log_queue, f"[OK] {ingest_message}")
            else:
                enqueue_log(log_queue, f"[AUTO] Ingest warning{chunk_suffix}: {ingest_message}")

            enqueue_log(log_queue, f"[AUTO] Analyzing {len(batch)} lines{chunk_suffix}...")
            data = await analyze_log("\n".join(batch))
            if "error" in data:
                enqueue_log(log_queue, f"[AUTO] Analysis error{chunk_suffix}: {data['error']}")
                continue

            _stats["analyses_done"] += 1

            pii_banner = data.get("pii_banner")
            if pii_banner:
                enqueue_log(log_queue, f"[AUTO] {trim_text(pii_banner, 180)}")

            findings = normalize_findings(data)
            if not findings:
                enqueue_log(log_queue, f"[OK] No issues found in batch{chunk_suffix}.")
                continue

            timestamp = datetime.now().strftime("%H:%M:%S")
            for finding in findings:
                severity = str(finding.get("severity", "INFO")).upper()
                message = finding.get("message", finding.get("description", "No message"))
                agent = finding.get("agent", "unknown")
                normalized = dict(finding)
                normalized["severity"] = severity
                normalized["agent"] = agent
                normalized["message"] = message
                normalized["fix"] = best_fix(normalized)
                normalized["ts"] = timestamp

                enqueue_log(log_queue, f"[{severity}] {message} ({agent})")
                enqueue_finding(log_queue, normalized)

                if severity == "CRITICAL":
                    _stats["criticals"] += 1
                    if normalized["fix"]:
                        enqueue_log(log_queue, f"[AUTO] Suggested fix: {trim_text(normalized['fix'], 220)}")
                    enqueue_log(log_queue, f"[AUTO] Querying chatbot for: {trim_text(message, 90)}")
                    reply = await auto_chat(message)
                    if reply:
                        enqueue_log(log_queue, f"[CHATBOT] {reply}")
                elif severity in {"HIGH", "WARNING", "MEDIUM"}:
                    _stats["warnings"] += 1

    try:
        _stats["backend_ok"] = await check_health()
        if _stats["backend_ok"]:
            enqueue_log(log_queue, f"[OK] Backend connected: {BASE_URL}")
        else:
            enqueue_log(log_queue, f"[AUTO] Cannot reach backend at {BASE_URL}. Start the backend on localhost:8001.")

        if mode == "watch":
            enqueue_log(log_queue, f"[OK] Watching: {target}")
            with open(target, "r", encoding="utf-8", errors="replace") as handle:
                handle.seek(0, 2)
                buffer: list[str] = []
                last_flush = time.time()

                while not stop_event.is_set():
                    line = handle.readline()
                    if line:
                        line = line.strip()
                        if line:
                            buffer.append(line)
                            remember_raw_lines([line])
                            _stats["lines_seen"] += 1
                            enqueue_log(log_queue, line)

                    if buffer and (time.time() - last_flush > 3 or len(buffer) >= 20):
                        await process_batch(buffer, source="file-watch")
                        buffer = []
                        last_flush = time.time()

                    await wait_for_stop(stop_event, 0.3)

        elif mode == "ingest":
            enqueue_log(log_queue, f"[OK] Ingesting: {target}")
            with open(target, "r", encoding="utf-8", errors="replace") as handle:
                lines = [line.strip() for line in handle if line.strip()]
            _stats["lines_seen"] += len(lines)
            remember_raw_lines(lines)
            emit_tail(lines, log_queue)
            await process_batch(lines, source="file-ingest")
            enqueue_log(log_queue, "[AUTO] Ingest complete. Press q to quit.")

        elif mode == "paste":
            lines = pasted_lines or []
            if not lines:
                enqueue_log(log_queue, "[AUTO] No pasted log lines were provided.")
            else:
                enqueue_log(log_queue, f"[OK] Received {len(lines)} pasted log lines.")
                _stats["lines_seen"] += len(lines)
                remember_raw_lines(lines)
                emit_tail(lines, log_queue)
                await process_batch(lines, source="paste")
            enqueue_log(log_queue, "[AUTO] Paste analysis complete. Press q to quit.")

    except FileNotFoundError:
        enqueue_log(log_queue, f"[AUTO] File not found: {target}")
    except asyncio.CancelledError:  # pragma: no cover - shutdown path
        pass
    except Exception as exc:
        enqueue_log(log_queue, f"[AUTO] Agent error: {trim_text(str(exc), 220)}")


def collect_paste_lines() -> list[str]:
    if not sys.stdin.isatty():
        return [line.strip() for line in sys.stdin if line.strip()]

    print("Paste log lines below. Enter a blank line twice to launch the TUI.\n")
    lines: list[str] = []
    blank_count = 0

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line == "":
            blank_count += 1
            if blank_count >= 2:
                break
            continue

        blank_count = 0
        line = line.strip()
        if line:
            lines.append(line)

    return lines


async def run_tui(mode: str, target: str, pasted_lines: list[str] | None = None) -> None:
    stop_event = asyncio.Event()
    log_queue: asyncio.Queue = asyncio.Queue(maxsize=LOG_QUEUE_SIZE)
    app = LogOracleApp(log_queue=log_queue, stop_event=stop_event)

    agent_task = asyncio.create_task(run_agent(mode, target, log_queue, stop_event, pasted_lines))
    health_task = asyncio.create_task(health_monitor(log_queue, stop_event))

    try:
        await app.run_async()
    finally:
        stop_event.set()
        for task in (agent_task, health_task):
            task.cancel()
        await asyncio.gather(agent_task, health_task, return_exceptions=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LogOracle Terminal Agent (Textual TUI)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python logoracle_cli.py --watch C:\\logs\\app.log
  python logoracle_cli.py --ingest C:\\logs\\error.log
  python logoracle_cli.py --paste
        """,
    )
    parser.add_argument("--watch", metavar="FILE", help="Tail-watch a log file live")
    parser.add_argument("--ingest", metavar="FILE", help="Analyze an entire log file once")
    parser.add_argument("--paste", action="store_true", help="Paste log lines manually")
    parser.add_argument("--url", default="http://localhost:8001", help="Backend URL")
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional X-API-Key override. Defaults to API_KEY or LOGORACLE_API_KEY env.",
    )
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.url.rstrip("/")

    global API_KEY
    if args.api_key is not None:
        API_KEY = args.api_key

    pasted_lines: list[str] | None = None
    if args.watch:
        mode, target = "watch", os.path.abspath(args.watch)
    elif args.ingest:
        mode, target = "ingest", os.path.abspath(args.ingest)
    elif args.paste:
        mode, target = "paste", ""
        pasted_lines = collect_paste_lines()
    else:
        parser.print_help()
        return

    try:
        asyncio.run(run_tui(mode, target, pasted_lines))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
