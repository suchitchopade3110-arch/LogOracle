"""
LogOracle Terminal Agent - Textual TUI Edition (Windows)
Usage:
  python logoracle_cli.py --watch <logfile>
  python logoracle_cli.py --ingest <logfile>
  python logoracle_cli.py --paste

Requires: pip install textual httpx
"""

import argparse
import asyncio
import json
import sys
import time
import threading
from collections import deque
from datetime import datetime

import httpx
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Static, RichLog, DataTable, Label, Input
)
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive
from textual import work
from rich.text import Text
from rich.panel import Panel
from rich.console import Console
from rich.style import Style

# ── Global state ──────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8001"
_log_lines = deque(maxlen=200)
_findings = deque(maxlen=50)
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


# ── HTTP helpers ───────────────────────────────────────────────────────────────

async def check_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{BASE_URL}/health")
            return r.status_code == 200
    except Exception:
        return False


async def ingest_lines(lines: list, source: str = "cli-agent"):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(
                f"{BASE_URL}/ingest/logs",
                json={"lines": lines, "source": source}
            )
    except Exception:
        pass


async def analyze_log(log_text: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{BASE_URL}/analyze/log",
                json={"log_text": log_text, "mode": "plain"}
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"error": str(e)}


async def auto_chat(finding_msg: str) -> str:
    """Ask chatbot to explain a CRITICAL finding."""
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                f"{BASE_URL}/chat",
                json={
                    "message": f"Explain this security finding and suggest a fix: {finding_msg}",
                    "persona": "security",
                    "session_id": "cli-agent",
                }
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("response", data.get("message", ""))
    except Exception:
        pass
    return ""


# ── Textual Widgets ────────────────────────────────────────────────────────────

class LogoWidget(Static):
    def render(self):
        return Text(LOGO, style="bold cyan", no_wrap=True)


class StatsWidget(Static):
    """Live stats panel — updates every second."""

    def on_mount(self):
        self.set_interval(1.0, self.refresh)

    def render(self):
        up = int(time.time() - _stats["start_time"])
        h, rem = divmod(up, 3600)
        m, s = divmod(rem, 60)
        uptime = f"{h:02d}:{m:02d}:{s:02d}"
        backend_dot = "[green]●[/green]" if _stats["backend_ok"] else "[red]●[/red]"
        mode_str = _stats["mode"].upper()

        return (
            f"[bold cyan]── AGENT STATUS ──────────────────[/bold cyan]\n"
            f"  Backend    {backend_dot} {BASE_URL}\n"
            f"  Mode       [yellow]{mode_str}[/yellow]\n"
            f"  Watch      [dim]{_stats['watch_path'] or 'N/A'}[/dim]\n"
            f"  Uptime     [cyan]{uptime}[/cyan]\n\n"
            f"[bold cyan]── METRICS ───────────────────────[/bold cyan]\n"
            f"  Lines Seen   [white]{_stats['lines_seen']}[/white]\n"
            f"  Analyses     [white]{_stats['analyses_done']}[/white]\n"
            f"  Criticals    [red]{_stats['criticals']}[/red]\n"
            f"  Warnings     [yellow]{_stats['warnings']}[/yellow]\n"
        )


class FindingsWidget(DataTable):
    """Findings table — severity / time / message."""

    def on_mount(self):
        self.add_columns("Sev", "Time", "Agent", "Message")
        self.set_interval(1.0, self._refresh_rows)

    def _refresh_rows(self):
        count = self.row_count
        findings_list = list(_findings)
        if len(findings_list) > count:
            for f in findings_list[count:]:
                sev = f.get("severity", "INFO")
                ts = f.get("ts", "")
                agent = f.get("agent", "?")
                msg = f.get("message", f.get("description", ""))[:60]
                style = SEVERITY_STYLE.get(sev, Style())
                sev_text = Text(sev, style=style)
                self.add_row(sev_text, ts, agent, msg)
            self.move_cursor(row=self.row_count - 1)


# ── Main App ───────────────────────────────────────────────────────────────────

class LogOracleApp(App):
    CSS = """
    Screen {
        background: #0d1117;
    }
    LogoWidget {
        height: 11;
        width: 70;
        content-align: left top;
        color: cyan;
        padding: 0;
    }
    #left-panel {
        width: 76;
        border: solid #30363d;
        padding: 1;
    }
    #right-top {
        height: 55%;
        border: solid #30363d;
    }
    #right-bottom {
        height: 45%;
        border: solid #30363d;
    }
    #log-label {
        background: #161b22;
        color: cyan;
        padding: 0 1;
    }
    #findings-label {
        background: #161b22;
        color: yellow;
        padding: 0 1;
    }
    StatsWidget {
        color: white;
    }
    FindingsWidget {
        height: 1fr;
    }
    RichLog {
        height: 1fr;
    }
    Header {
        background: #161b22;
        color: cyan;
    }
    Footer {
        background: #161b22;
    }
    #chat-panel {
        height: 3;
        border: solid #238636;
        display: none;
        padding: 0 1;
    }
    #chat-panel.visible {
        display: block;
    }
    #chat-label {
        background: #0d1117;
        color: green;
        padding: 0 1;
    }
    #chat-input {
        background: #0d1117;
        color: white;
        border: none;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_log", "Clear Log"),
        ("f", "clear_findings", "Clear Findings"),
        ("t", "toggle_chat", "Chat"),
    ]

    def __init__(self, log_queue: asyncio.Queue, **kwargs):
        super().__init__(**kwargs)
        self._log_queue = log_queue
        self._chat_visible = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="left-panel"):
                yield LogoWidget()
                yield StatsWidget()
            with Vertical():
                with Container(id="right-top"):
                    yield Label("  ▸ LIVE LOG TAIL", id="log-label")
                    yield RichLog(id="log-view", highlight=True, markup=True, wrap=True)
                with Container(id="right-bottom"):
                    yield Label("  ▸ FINDINGS", id="findings-label")
                    yield FindingsWidget(id="findings-table")
        with Container(id="chat-panel"):
            yield Label("  ▸ CHAT  [press Enter to send, t to hide]", id="chat-label")
            yield Input(placeholder="Ask LogOracle anything...", id="chat-input")
        yield Footer()

    def on_mount(self):
        self.title = "LogOracle Agent"
        self.sub_title = BASE_URL
        self.set_interval(0.2, self._drain_queue)

    def _drain_queue(self):
        log_view = self.query_one("#log-view", RichLog)
        try:
            while True:
                item = self._log_queue.get_nowait()
                kind = item.get("kind", "log")
                text = item.get("text", "")

                if kind == "log":
                    if any(w in text.upper() for w in ["CRITICAL", "ERROR", "FAIL"]):
                        log_view.write(Text(text, style="red"))
                    elif any(w in text.upper() for w in ["WARN", "WARNING"]):
                        log_view.write(Text(text, style="yellow"))
                    elif text.startswith("[CHATBOT]"):
                        log_view.write(Text(text, style="bold magenta"))
                    elif text.startswith("[AUTO]"):
                        log_view.write(Text(text, style="bold cyan"))
                    elif text.startswith("[YOU]"):
                        log_view.write(Text(text, style="bold green"))
                    elif text.startswith("[✓]") or "SUCCESS" in text.upper():
                        log_view.write(Text(text, style="green"))
                    else:
                        log_view.write(Text(text, style="white"))
                elif kind == "finding":
                    _findings.append(item)
        except asyncio.QueueEmpty:
            pass

    def action_clear_log(self):
        self.query_one("#log-view", RichLog).clear()

    def action_clear_findings(self):
        _findings.clear()
        self.query_one("#findings-table", FindingsWidget).clear()

    def action_toggle_chat(self):
        panel = self.query_one("#chat-panel")
        self._chat_visible = not self._chat_visible
        if self._chat_visible:
            panel.add_class("visible")
            self.query_one("#chat-input", Input).focus()
        else:
            panel.remove_class("visible")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        msg = event.value.strip()
        if not msg:
            return
        event.input.value = ""
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(Text(f"[YOU] {msg}", style="bold green"))
        asyncio.create_task(self._chat_request(msg))

    async def _chat_request(self, msg: str):
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(Text("[CHATBOT] thinking...", style="dim magenta"))
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(
                    f"{BASE_URL}/chat/sync",
                    json={
                        "message": msg,
                        "session_id": "cli-chat",
                        "persona": "security",
                        "mode": "plain",
                        "session_context": {
                            "findings": [],
                            "last_log_lines": "",
                            "code_diff": "",
                            "chat_history": [],
                            "developer_profile": {
                                "expertise_level": "intermediate",
                                "past_quiz_scores": [],
                                "badges": [],
                            },
                        },
                    }
                )
                data = r.json()
                reply = data.get("reply") or data.get("response") or data.get("message") or str(data)
                log_view.write(Text(f"[CHATBOT] {reply[:500]}", style="bold magenta"))
        except Exception as e:
            log_view.write(Text(f"[CHATBOT] Error: {e}", style="red"))


# ── Agent Logic ────────────────────────────────────────────────────────────────

async def run_agent(mode: str, target: str, log_queue: asyncio.Queue):
    def push_log(text: str):
        try:
            log_queue.put_nowait({"kind": "log", "text": text})
        except asyncio.QueueFull:
            pass

    def push_finding(f: dict):
        try:
            log_queue.put_nowait({**f, "kind": "finding"})
        except asyncio.QueueFull:
            pass

    _stats["backend_ok"] = await check_health()
    if not _stats["backend_ok"]:
        push_log(f"[✗] Cannot reach backend at {BASE_URL}. Start uvicorn first.")
    else:
        push_log(f"[✓] Backend connected: {BASE_URL}")

    _stats["mode"] = mode

    async def process_batch(lines: list):
        if not lines:
            return
        await ingest_lines(lines, source=f"cli-{mode}")
        push_log(f"[AUTO] Analyzing {len(lines)} lines...")
        log_text = "\n".join(lines)
        data = await analyze_log(log_text)

        if "error" in data:
            push_log(f"[✗] Analysis error: {data['error']}")
            return

        findings = data.get("findings", [])
        _stats["analyses_done"] += 1

        if not findings:
            push_log("[✓] No issues found in batch.")
            return

        ts = datetime.now().strftime("%H:%M:%S")
        for f in findings:
            sev = f.get("severity", "INFO")
            msg = f.get("message", f.get("description", ""))
            agent = f.get("agent", "unknown")
            push_log(f"[{sev}] {msg}  ({agent})")
            push_finding({**f, "ts": ts})
            if sev in ("CRITICAL", "HIGH"):
                _stats["criticals"] += 1
                push_log(f"[AUTO] Querying chatbot for: {msg[:60]}...")
                reply = await auto_chat(msg)
                if reply:
                    push_log(f"[CHATBOT] {reply[:300]}")
            elif sev == "MEDIUM":
                _stats["warnings"] += 1

    if mode == "watch":
        _stats["watch_path"] = target
        push_log(f"[✓] Watching: {target}")
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                f.seek(0, 2)
                buffer = []
                last_flush = time.time()
                while True:
                    line = f.readline()
                    if line:
                        line = line.strip()
                        if line:
                            buffer.append(line)
                            _stats["lines_seen"] += 1
                            push_log(line)
                    if buffer and (time.time() - last_flush > 3 or len(buffer) >= 20):
                        await process_batch(buffer)
                        buffer = []
                        last_flush = time.time()
                    await asyncio.sleep(0.3)
        except FileNotFoundError:
            push_log(f"[✗] File not found: {target}")

    elif mode == "ingest":
        _stats["watch_path"] = target
        push_log(f"[✓] Ingesting: {target}")
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = [l.strip() for l in f if l.strip()]
            _stats["lines_seen"] += len(lines)
            for line in lines:
                push_log(line)
            await process_batch(lines)
        except FileNotFoundError:
            push_log(f"[✗] File not found: {target}")

    elif mode == "paste":
        push_log("[✓] Paste mode — reading stdin...")
        lines = []
        for line in sys.stdin:
            line = line.strip()
            if line:
                lines.append(line)
                _stats["lines_seen"] += 1
                push_log(line)
        await process_batch(lines)


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    global BASE_URL

    parser = argparse.ArgumentParser(
        description="LogOracle Terminal Agent (Textual TUI)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python logoracle_cli.py --watch C:\\logs\\app.log
  python logoracle_cli.py --ingest C:\\logs\\error.log
  python logoracle_cli.py --paste
        """
    )
    parser.add_argument("--watch", metavar="FILE", help="Tail-watch a log file live")
    parser.add_argument("--ingest", metavar="FILE", help="Analyze entire file once")
    parser.add_argument("--paste", action="store_true", help="Paste log lines via stdin")
    parser.add_argument("--url", default="http://localhost:8001", help="Backend URL")
    args = parser.parse_args()

    BASE_URL = args.url.rstrip("/")

    if args.watch:
        mode, target = "watch", args.watch
    elif args.ingest:
        mode, target = "ingest", args.ingest
    elif args.paste:
        mode, target = "paste", ""
    else:
        parser.print_help()
        sys.exit(0)

    log_queue: asyncio.Queue = asyncio.Queue(maxsize=500)
    app = LogOracleApp(log_queue=log_queue)

    async def _run():
        await asyncio.gather(
            app.run_async(),
            run_agent(mode, target, log_queue),
        )

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
