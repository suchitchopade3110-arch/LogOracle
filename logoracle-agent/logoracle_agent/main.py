"""
logoracle_agent/main.py
LogOracle local agent - Textual TUI edition.

Install: pip install logoracle-agent textual
Run:     logoracle-agent --url http://localhost:8001 --watch /var/log/auth.log --perf
"""
import os
import socket
import sys
import time
from collections import deque

import click
import httpx
import psutil
from rich.console import Console
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, RichLog, Static
from textual.containers import Vertical

from logoracle_agent.api_monitor import APIMonitor
from logoracle_agent.monitor import SystemMonitor
from logoracle_agent.relay import HealRelay
from logoracle_agent.streamer import Streamer, _set_findings_ref
from logoracle_agent.watcher import LogWatcher


_log_lines: deque[str] = deque(maxlen=200)
_chat_lines: deque[tuple[str, str]] = deque(maxlen=50)
_findings: deque[dict] = deque(maxlen=50)
_set_findings_ref(_findings)
_state: dict = {
    "lines_sent": 0,
    "analyses_done": 0,
    "critical_count": 0,
    "warning_count": 0,
    "last_finding": "-",
    "cpu": 0.0,
    "ram": 0.0,
    "disk": 0.0,
    "relay_active": False,
    "relay_dry_run": False,
    "commands_run": 0,
    "relay_failed": 0,
    "api_active": False,
    "api_port": 8888,
    "api_pending": 0,
    "api_analyses": 0,
    "api_findings": 0,
    "api_last": "",
    "agent_id": "",
    "backend_url": "",
    "watch_paths": [],
    "perf": False,
}

LOGO = """[bold cyan]
 ██╗      ██████╗  ██████╗  ██████╗ ██████╗  █████╗  ██████╗██╗     ███████╗
 ██║     ██╔═══██╗██╔════╝ ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║     ██╔════╝
 ██║     ██║   ██║██║  ███╗██║   ██║██████╔╝███████║██║     ██║     █████╗
 ██║     ██║   ██║██║   ██║██║   ██║██╔══██╗██╔══██║██║     ██║     ██╔══╝
 ███████╗╚██████╔╝╚██████╔╝╚██████╔╝██║  ██║██║  ██║╚██████╗███████╗███████╗
 ╚══════╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝
[/bold cyan][dim]  autonomous ai debugging · code intelligence · developer growth[/dim]"""


class TUIStreamer(Streamer):
    """Streamer that mirrors log lines and findings into the TUI state."""

    def ingest(self, lines: list[str], source: str = "agent"):
        for line in lines:
            _log_lines.append(line.rstrip())
        super().ingest(lines, source)

    def _analyze(self, lines: list[str]):
        super()._analyze(lines)


AGENT_CSS = """
Screen {
    layout: grid;
    grid-size: 2;
    grid-rows: auto 1fr 1fr;
    grid-columns: 1fr 2fr;
}

#logo-bar {
    column-span: 2;
    height: auto;
    padding: 0 1;
}

#left-col {
    layout: vertical;
    border: solid #1a3a4a;
    padding: 0 1;
}

#right-col {
    layout: vertical;
    border: solid #1a3a4a;
    padding: 0 1;
}

#findings-panel {
    column-span: 2;
    border: solid #3a1a1a;
    padding: 0 1;
}

.panel-title {
    color: cyan;
    text-style: bold;
    padding: 0 0 1 0;
}

RichLog {
    border: none;
    height: 100%;
    background: $surface;
}

Footer {
    background: #0a1a2a;
}

Header {
    background: #0a1a2a;
}
"""


class LogoBar(Static):
    def render(self):
        return Text.from_markup(LOGO)


class StatsPanel(Static):
    def render(self):
        s = _state
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("k", style="dim", width=18)
        table.add_column("v")
        table.add_row("backend", f"[cyan]{s['backend_url']}[/cyan]")
        table.add_row("agent id", f"[dim]{s['agent_id']}[/dim]")
        table.add_row("watching", f"[dim]{', '.join(s['watch_paths']) or '-'}[/dim]")
        table.add_row("-" * 16, "-" * 20)
        table.add_row("lines sent", str(s["lines_sent"]))
        table.add_row("analyses", str(s["analyses_done"]))
        table.add_row(
            "findings",
            f"[bold red]{s['critical_count']} CRITICAL[/bold red]  "
            f"[yellow]{s['warning_count']} WARNING[/yellow]",
        )
        table.add_row("last finding", f"[italic]{s['last_finding'][:50]}[/italic]")
        return table


class AgentStatusPanel(Static):
    def render(self):
        s = _state
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("agent", width=16)
        table.add_column("status")

        def row(name, active, note=""):
            icon = "[green]●[/green]" if active else "[dim]○[/dim]"
            label = f"[green]{note or 'active'}[/green]" if active else f"[dim]{note or 'inactive'}[/dim]"
            table.add_row(f"{icon} {name}", label)

        row("Log Agent", True)
        row("Security Agent", True, "via log analysis")
        row("Perf Agent", s["perf"])
        row("Heal Relay", s["relay_active"], "dry-run" if s["relay_dry_run"] else "active")
        row("API Agent", s["api_active"], f":{s['api_port']}" if s["api_active"] else "")

        if s["perf"]:
            table.add_row("-" * 14, "-" * 20)
            table.add_row(f"  CPU  {s['cpu']:.1f}%", _bar(s["cpu"], 100, 20))
            table.add_row(f"  RAM  {s['ram']:.1f}%", _bar(s["ram"], 100, 20))
            table.add_row(f"  Disk {s['disk']:.1f}%", _bar(s["disk"], 100, 20))

        if s["relay_active"]:
            table.add_row("-" * 14, "-" * 20)
            table.add_row("  cmds run", str(s["commands_run"]))
            table.add_row("  relay fail", str(s["relay_failed"]))

        if s["api_active"]:
            table.add_row("-" * 14, "-" * 20)
            table.add_row("  pending", str(s["api_pending"]))
            table.add_row("  analyses", str(s["api_analyses"]))
            table.add_row("  findings", str(s["api_findings"]))
        return table


class FindingsPanel(Static):
    def render(self):
        if not _findings:
            return Text("no findings yet - watching...", style="dim italic")

        table = Table(show_header=True, box=None, padding=(0, 1), expand=True)
        table.add_column("time", style="dim", width=10, no_wrap=True)
        table.add_column("severity", width=10, no_wrap=True)
        table.add_column("message")

        styles = {
            "CRITICAL": "bold red",
            "HIGH": "red",
            "MEDIUM": "yellow",
            "LOW": "cyan",
            "INFO": "dim",
        }
        for finding in list(_findings)[:15]:
            severity = finding["severity"]
            style = styles.get(severity, "white")
            table.add_row(finding["time"], f"[{style}]{severity}[/{style}]", finding["message"])
        return table


class LogTailPanel(RichLog):
    pass


def _bar(val: float, max_val: float, width: int = 20) -> str:
    filled = max(0, min(width, int((val / max_val) * width)))
    color = "red" if val > 85 else "yellow" if val > 60 else "green"
    bar = "█" * filled + "░" * (width - filled)
    return f"[{color}]{bar}[/{color}]"


class LogOracleApp(App):
    CSS = AGENT_CSS
    TITLE = "LogOracle Agent"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_log", "Clear log"),
        ("f", "clear_findings", "Clear findings"),
    ]

    def __init__(self, streamer, watchers, monitor, heal_relay, api_monitor, **kwargs):
        super().__init__(**kwargs)
        self._streamer = streamer
        self._watchers = watchers
        self._monitor = monitor
        self._heal_relay = heal_relay
        self._api_monitor = api_monitor

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield LogoBar(id="logo-bar")
        with Vertical(id="left-col"):
            yield Label("● stats", classes="panel-title")
            yield StatsPanel(id="stats")
            yield Label("● agents", classes="panel-title")
            yield AgentStatusPanel(id="agents")
        with Vertical(id="right-col"):
            yield Label("● live log tail", classes="panel-title")
            yield LogTailPanel(id="log-tail", highlight=True, markup=True, wrap=True)
        with Vertical(id="findings-panel"):
            yield Label("● findings", classes="panel-title")
            yield FindingsPanel(id="findings")
        yield Footer()

    def on_mount(self):
        self.set_interval(1.0, self._refresh_all)
        self.set_interval(0.5, self._drain_logs)

    def _refresh_all(self):
        if self._streamer:
            _state["lines_sent"] = self._streamer.lines_sent
            _state["analyses_done"] = self._streamer.analyses_done
            _state["critical_count"] = self._streamer.critical_count
            _state["warning_count"] = self._streamer.warning_count
            _state["last_finding"] = self._streamer.last_finding or "-"

        if _state["perf"]:
            try:
                _state["cpu"] = psutil.cpu_percent()
                _state["ram"] = psutil.virtual_memory().percent
                _state["disk"] = psutil.disk_usage("/").percent
            except Exception:
                pass

        if self._heal_relay:
            _state["relay_active"] = True
            _state["relay_dry_run"] = self._heal_relay.dry_run
            _state["commands_run"] = self._heal_relay.executed
            _state["relay_failed"] = self._heal_relay.failed

        if self._api_monitor:
            _state["api_active"] = True
            _state["api_pending"] = self._api_monitor.pending_count()
            _state["api_analyses"] = self._api_monitor.analyses
            _state["api_findings"] = self._api_monitor.findings

        self.query_one("#stats", StatsPanel).refresh()
        self.query_one("#agents", AgentStatusPanel).refresh()
        self.query_one("#findings", FindingsPanel).refresh()

    def _drain_logs(self):
        log_widget = self.query_one("#log-tail", LogTailPanel)
        while _log_lines:
            line = _log_lines.popleft()
            lowered = line.lower()
            if line.startswith("[CHATBOT]"):
                log_widget.write(f"[cyan]{line}[/cyan]")
            elif line.startswith("[AUTO]"):
                log_widget.write(f"[magenta]{line}[/magenta]")
            elif line.startswith("[CHAT ERR]"):
                log_widget.write(f"[red]{line}[/red]")
            elif any(word in lowered for word in ("error", "critical", "failed", "denied")):
                log_widget.write(f"[red]{line}[/red]")
            elif any(word in lowered for word in ("warn", "warning")):
                log_widget.write(f"[yellow]{line}[/yellow]")
            elif any(word in lowered for word in ("info", "success", "connected")):
                log_widget.write(f"[green]{line}[/green]")
            else:
                log_widget.write(f"[dim]{line}[/dim]")

    def action_quit(self):
        self._shutdown()
        self.exit()

    def action_clear_log(self):
        self.query_one("#log-tail", LogTailPanel).clear()

    def action_clear_findings(self):
        _findings.clear()
        self.query_one("#findings", FindingsPanel).refresh()

    def _shutdown(self):
        for watcher in self._watchers:
            try:
                watcher.stop()
            except Exception:
                pass
        if self._monitor:
            try:
                self._monitor.stop()
            except Exception:
                pass
        if self._heal_relay:
            try:
                self._heal_relay.stop()
            except Exception:
                pass
        if self._api_monitor:
            try:
                self._api_monitor.stop()
            except Exception:
                pass


@click.command()
@click.option("--url", default="http://localhost:8001", show_default=True)
@click.option("--watch", multiple=True)
@click.option("--mode", default="tech", type=click.Choice(["tech", "plain"]), show_default=True)
@click.option("--dev-id", default="")
@click.option("--interval", default=2.0, show_default=True)
@click.option("--perf", is_flag=True, default=False)
@click.option("--api", is_flag=True, default=False)
@click.option("--api-port", default=8888, show_default=True)
@click.option("--relay", is_flag=True, default=False)
@click.option("--agent-id", default="")
@click.option("--dry-run", is_flag=True, default=False)
def cli(url, watch, mode, dev_id, interval, perf, api, api_port, relay, agent_id, dry_run):
    """LogOracle Local Agent - Textual TUI."""

    console = Console()
    try:
        response = httpx.get(f"{url}/health", timeout=5)
        if response.status_code != 200:
            console.print(f"[red]Backend returned {response.status_code}[/red]")
            sys.exit(1)
    except Exception as exc:
        console.print(f"[red]Cannot reach backend: {exc}[/red]")
        console.print("[yellow]Start: uvicorn main:app --host 0.0.0.0 --port 8001[/yellow]")
        sys.exit(1)

    if not agent_id:
        agent_id = f"{socket.gethostname()}_{int(time.time()) % 10000}"

    paths = list(watch)
    if not paths:
        candidates = ["/var/log/syslog", "/var/log/auth.log", "/var/log/kern.log"]
        paths = [path for path in candidates if os.path.exists(path)]

    _state["backend_url"] = url
    _state["agent_id"] = agent_id
    _state["watch_paths"] = paths
    _state["perf"] = perf
    _state["api_active"] = api
    _state["api_port"] = api_port
    _state["relay_active"] = relay

    streamer = TUIStreamer(url, mode, dev_id)

    def chat_callback(role: str, text: str):
        if role == "chatbot":
            _chat_lines.append(("chatbot", text))
            _log_lines.append(f"[CHATBOT] {text}")
        elif role == "system":
            _log_lines.append(f"[AUTO] {text}")
        elif role == "error":
            _log_lines.append(f"[CHAT ERR] {text}")

    streamer.set_chat_callback(chat_callback)

    if relay:
        try:
            httpx.post(
                f"{url}/heal/relay/register",
                json={
                    "agent_id": agent_id,
                    "hostname": socket.gethostname(),
                    "watch_paths": paths,
                },
                timeout=5,
            )
        except Exception:
            pass

    watchers = []
    for path in paths:
        if not os.path.exists(path):
            continue
        watcher = LogWatcher(path, streamer, interval)
        watcher.start()
        watchers.append(watcher)

    monitor = None
    if perf:
        monitor = SystemMonitor(streamer, poll_interval=5.0)
        monitor.start()

    heal_relay = None
    if relay:
        heal_relay = HealRelay(url, agent_id, dry_run=dry_run)
        heal_relay.start()

    api_monitor = None
    if api:
        api_monitor = APIMonitor(url, proxy_port=api_port)
        api_monitor.start()

    app = LogOracleApp(
        streamer=streamer,
        watchers=watchers,
        monitor=monitor,
        heal_relay=heal_relay,
        api_monitor=api_monitor,
    )
    app.run()
    console.print("\n[yellow]LogOracle agent stopped.[/yellow]")


if __name__ == "__main__":
    cli()
