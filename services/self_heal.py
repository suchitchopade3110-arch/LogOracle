"""
services/self_heal.py
Self-heal dry-run + approve flow.
Command whitelist only — no arbitrary execution.
POST /heal/preview  — dry-run, returns what would run
POST /heal/approve  — executes approved command (sandboxed whitelist)
"""
import re
import subprocess
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ── Whitelist — ONLY these command patterns are executable ────────────────
COMMAND_WHITELIST = [
    # IP blocking
    (r"^sudo ufw deny from \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
     "Block attacker IP via UFW"),
    (r"^sudo ufw reload$",
     "Reload UFW firewall rules"),
    # Service restart
    (r"^sudo systemctl restart (sshd|nginx|redis|apache2|postgresql)$",
     "Restart system service"),
    (r"^sudo systemctl stop (sshd|nginx|redis|apache2|postgresql)$",
     "Stop system service"),
    # Log cleanup
    (r"^sudo journalctl --vacuum-time=\d+d$",
     "Clean old journal logs"),
    # fail2ban
    (r"^sudo fail2ban-client set sshd banip \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
     "Ban IP via fail2ban"),
]

# Pending approvals — keyed by token
_pending: dict = {}
_legacy_service = None


def _is_whitelisted(command: str) -> Optional[str]:
    """Return description if command matches whitelist, else None."""
    for pattern, description in COMMAND_WHITELIST:
        if re.match(pattern, command.strip()):
            return description
    return None


def _generate_token(command: str) -> str:
    import hashlib, time
    return hashlib.md5(f"{command}{time.time()}".encode()).hexdigest()[:12]


class HealPreviewRequest(BaseModel):
    command: str
    finding_message: str = ""
    severity: str = "CRITICAL"


class HealApproveRequest(BaseModel):
    token: str
    dry_run: bool = True   # True = just print, never execute for demo safety


class SelfHealService:
    """Compatibility wrapper for the older /heal/approve router."""

    def __init__(self):
        from services.services import SelfHealService as LegacySelfHealService
        self._legacy = LegacySelfHealService()

    def stage(self, command_key: str, params: dict = {}) -> str:
        return self._legacy.stage(command_key, params)

    def preview(self, command_id: str) -> dict:
        return self._legacy.preview(command_id)

    async def execute(self, command_id: str) -> dict:
        return await self._legacy.execute(command_id)


@router.post("/heal/preview")
async def heal_preview(req: HealPreviewRequest):
    """
    Validate command against whitelist. Return dry-run preview.
    Frontend shows this before asking user to approve.
    """
    description = _is_whitelisted(req.command)
    if not description:
        raise HTTPException(
            status_code=400,
            detail=f"Command not in whitelist. Only pre-approved remediation commands are allowed."
        )

    token = _generate_token(req.command)
    _pending[token] = {
        "command":     req.command,
        "description": description,
        "finding":     req.finding_message,
        "severity":    req.severity,
    }

    return {
        "token":       token,
        "command":     req.command,
        "description": description,
        "risk_level":  "LOW" if "reload" in req.command else "MEDIUM",
        "reversible":  "ufw" in req.command or "journalctl" in req.command,
        "warning":     "This will modify system firewall rules. Verify the IP is correct."
                       if "ufw" in req.command else None,
        "dry_run_output": f"[DRY RUN] Would execute: {req.command}",
        "xp_on_approve": 80,
    }


@router.post("/heal/approve")
async def heal_approve(req: HealApproveRequest):
    """
    Execute approved heal command.
    dry_run=True (default) for demo safety — logs but doesn't execute.
    """
    pending = _pending.pop(req.token, None)
    if not pending:
        raise HTTPException(status_code=404, detail="Token not found or already used.")

    command = pending["command"]

    if req.dry_run:
        # Demo mode — never actually run
        return {
            "executed":    False,
            "dry_run":     True,
            "command":     command,
            "description": pending["description"],
            "output":      f"[DEMO DRY RUN] Command validated and approved: {command}",
            "xp_awarded":  80,
            "message":     "Self-heal approved. In production this would execute on the target system.",
        }

    # Production mode — only whitelisted commands, subprocess with timeout
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True, text=True, timeout=10
        )
        return {
            "executed":    True,
            "dry_run":     False,
            "command":     command,
            "description": pending["description"],
            "output":      result.stdout or result.stderr,
            "returncode":  result.returncode,
            "xp_awarded":  80 if result.returncode == 0 else 0,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timed out after 10s.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heal/whitelist")
async def get_whitelist():
    """Return list of approved command patterns for frontend display."""
    return [{"pattern": p, "description": d} for p, d in COMMAND_WHITELIST]
