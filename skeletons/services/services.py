# services/self_heal.py
import asyncio
from typing import Dict

# Whitelist only — never exec arbitrary commands
COMMAND_WHITELIST: Dict[str, str] = {
    "restart_nginx":  "sudo systemctl restart nginx",
    "restart_redis":  "sudo systemctl restart redis",
    "block_ip":       "sudo ufw deny from {ip}",
    "clean_logs":     "sudo journalctl --vacuum-time=7d",
    "restart_sshd":   "sudo systemctl restart sshd",
}

# Pending commands awaiting approval (in-memory, stateless MVP)
_pending: Dict[str, dict] = {}

class SelfHealService:
    def stage(self, command_key: str, params: dict = {}) -> str:
        """Stage command for dry-run preview. Returns command_id."""
        import uuid
        if command_key not in COMMAND_WHITELIST:
            raise ValueError(f"Command not whitelisted: {command_key}")
        cmd = COMMAND_WHITELIST[command_key].format(**params)
        command_id = str(uuid.uuid4())[:8]
        _pending[command_id] = {"key": command_key, "cmd": cmd, "params": params}
        return command_id

    def preview(self, command_id: str) -> dict:
        """Return dry-run preview for frontend display."""
        if command_id not in _pending:
            raise KeyError(f"Unknown command_id: {command_id}")
        return {"command_id": command_id, "preview": _pending[command_id]["cmd"], "dry_run": True}

    async def execute(self, command_id: str) -> dict:
        """
        Execute whitelisted command after user approval.
        Demo env only — never production.
        """
        if command_id not in _pending:
            raise KeyError(f"Unknown command_id: {command_id}")
        cmd = _pending[command_id]["cmd"]
        # TODO: in real demo env, run via subprocess with timeout
        # proc = await asyncio.create_subprocess_shell(cmd, ...)
        del _pending[command_id]
        return {"executed": True, "command": cmd, "status": "success"}


# services/pdf_export.py
# WeasyPrint: server-side PDF from HTML template
from typing import Any

def generate_pdf(session_data: dict) -> bytes:
    """
    Build HTML from session findings + root cause chain.
    Convert to PDF via WeasyPrint.
    """
    try:
        from weasyprint import HTML
    except ImportError:
        raise RuntimeError("WeasyPrint not installed. pip install weasyprint.")

    html = _build_html(session_data)
    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes

def _build_html(data: dict) -> str:
    findings_html = "".join(
        f"<tr><td>{f.get('agent')}</td><td>{f.get('severity')}</td>"
        f"<td>{f.get('message')}</td><td>{f.get('confidence', '')}</td></tr>"
        for f in data.get("findings", [])
    )
    chain_html = "".join(
        f"<li>{c['cause']['message']} → {c['effect']['message']}</li>"
        for c in data.get("root_cause_chain", [])
    )
    return f"""
    <html><head><style>
        body {{ font-family: Arial; padding: 32px; }}
        h1 {{ color: #1F3864; }} h2 {{ color: #1F497D; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; font-size: 12px; }}
        th {{ background: #1F3864; color: white; }}
    </style></head><body>
    <h1>LogOracle Debug Session Report</h1>
    <h2>Findings</h2>
    <table><tr><th>Agent</th><th>Severity</th><th>Message</th><th>Confidence</th></tr>
    {findings_html}</table>
    <h2>Root Cause Chain</h2><ol>{chain_html}</ol>
    </body></html>
    """
