"""
services/self_heal.py — updated whitelist with fail2ban as default blocker.

Changes:
- fail2ban banip added as PRIMARY block command
- fail2ban unban added
- fail2ban status check added
- UFW kept as fallback
- recidive jail commands added (permanent ban after 3 strikes)
- sshd config hardening commands added
"""
import re
import shlex
import subprocess
import time
from ipaddress import ip_address
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ── Whitelist ─────────────────────────────────────────────────────────────
COMMAND_WHITELIST = [

    # ── fail2ban (PRIMARY — preferred over raw iptables) ─────────────────
    (r"^sudo fail2ban-client set sshd banip (\d{1,3}\.){3}\d{1,3}$",
     "Ban attacker IP via fail2ban SSH jail"),

    (r"^sudo fail2ban-client set sshd unbanip (\d{1,3}\.){3}\d{1,3}$",
     "Unban IP from fail2ban SSH jail"),

    (r"^sudo fail2ban-client set recidive banip (\d{1,3}\.){3}\d{1,3}$",
     "Permanently ban repeat offender IP via fail2ban recidive jail"),

    (r"^sudo fail2ban-client status sshd$",
     "Check fail2ban SSH jail status"),

    (r"^sudo fail2ban-client reload$",
     "Reload fail2ban configuration"),

    (r"^sudo systemctl restart fail2ban$",
     "Restart fail2ban service"),

    # ── UFW (FALLBACK if fail2ban not installed) ──────────────────────────
    (r"^sudo ufw deny from (\d{1,3}\.){3}\d{1,3} to any port 22$",
     "Block attacker IP on SSH port via UFW"),

    (r"^sudo ufw deny from (\d{1,3}\.){3}\d{1,3}$",
     "Block attacker IP entirely via UFW"),

    (r"^sudo ufw reload$",
     "Reload UFW firewall rules"),

    (r"^sudo ufw delete deny from (\d{1,3}\.){3}\d{1,3}$",
     "Remove IP block from UFW"),

    # ── iptables (Alpine / RHEL / Arch fallback) ──────────────────────────
    (r"^sudo iptables -A INPUT -s (\d{1,3}\.){3}\d{1,3} -p tcp --dport 22 -j DROP$",
     "Block attacker IP via iptables"),

    (r"^sudo iptables -D INPUT -s (\d{1,3}\.){3}\d{1,3} -p tcp --dport 22 -j DROP$",
     "Remove iptables block for IP"),

    (r"^sudo iptables-save > /etc/iptables/rules\.v4$",
     "Persist iptables rules across reboots"),

    # ── firewall-cmd (RHEL/CentOS/Fedora) ────────────────────────────────
    (r"^sudo firewall-cmd --add-rich-rule='rule family=ipv4 source address=(\d{1,3}\.){3}\d{1,3} port port=22 protocol=tcp reject' --permanent$",
     "Block attacker IP via firewalld"),

    (r"^sudo firewall-cmd --reload$",
     "Reload firewalld rules"),

    # ── SSH hardening ─────────────────────────────────────────────────────
    (r"^sudo systemctl restart (sshd|ssh)$",
     "Restart SSH service"),

    (r"^sudo systemctl stop (sshd|ssh)$",
     "Stop SSH service (emergency)"),

    # ── Service management ────────────────────────────────────────────────
    (r"^sudo systemctl restart (nginx|apache2|redis|postgresql|mysql|mongodb)$",
     "Restart system service"),

    (r"^sudo systemctl stop (nginx|apache2|redis|postgresql|mysql|mongodb)$",
     "Stop system service"),

    # ── Log cleanup ───────────────────────────────────────────────────────
    (r"^sudo journalctl --vacuum-time=\d+d$",
     "Clean old journal logs"),

    (r"^sudo journalctl --vacuum-size=\d+(M|G)$",
     "Clean journal logs by size"),

    # ── pfctl (macOS) ─────────────────────────────────────────────────────
    (r"^echo 'block in quick from (\d{1,3}\.){3}\d{1,3} to any' \| sudo pfctl -f -$",
     "Block attacker IP via macOS pfctl"),

]

_pending: dict = {}


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


def _is_whitelisted(command: str) -> Optional[str]:
    for pattern, description in COMMAND_WHITELIST:
        if re.match(pattern, command.strip()):
            return description
    return None


def _generate_token(command: str) -> str:
    import hashlib
    return hashlib.md5(f"{command}{time.time()}".encode()).hexdigest()[:12]


def _is_valid_ip(ip: str) -> bool:
    try:
        ip_address(ip)
        return True
    except ValueError:
        return False


def _run_whitelisted(command: str, timeout: int = 10) -> subprocess.CompletedProcess:
    if any(token in command for token in ["|", ">", "'", "\""]):
        return subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
    return subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=timeout)


def _check_fail2ban_installed() -> bool:
    """Check if fail2ban is available on this system."""
    try:
        result = subprocess.run(
            ["which", "fail2ban-client"],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return False


def build_block_commands(ip: str, platform: str, distro: str) -> list[dict]:
    """
    Build ordered list of block commands for a given IP.
    Priority: fail2ban → UFW → iptables → firewall-cmd → pfctl
    Returns list so frontend can show all options.
    """
    commands = []
    fail2ban = _check_fail2ban_installed()

    if not _is_valid_ip(ip):
        return []

    if platform == "linux":
        if fail2ban:
            commands.append({
                "command":     f"sudo fail2ban-client set sshd banip {ip}",
                "description": "Ban via fail2ban (recommended — auto-unbans, tracks recidivists)",
                "method":      "fail2ban",
                "recommended": True,
                "reversible":  True,
                "auto_unban":  True,
            })
            commands.append({
                "command":     f"sudo fail2ban-client set recidive banip {ip}",
                "description": "Permanent ban via fail2ban recidive jail (repeat offenders)",
                "method":      "fail2ban-permanent",
                "recommended": False,
                "reversible":  True,
                "auto_unban":  False,
            })

        if distro in ("ubuntu", "debian", ""):
            commands.append({
                "command":     f"sudo ufw deny from {ip} to any port 22",
                "description": "Block SSH port via UFW",
                "method":      "ufw",
                "recommended": not fail2ban,
                "reversible":  True,
                "auto_unban":  False,
            })

        if distro in ("rhel", "centos", "fedora", "almalinux", "rocky"):
            commands.append({
                "command":     f"sudo firewall-cmd --add-rich-rule='rule family=ipv4 source address={ip} port port=22 protocol=tcp reject' --permanent",
                "description": "Block via firewalld (RHEL/CentOS)",
                "method":      "firewalld",
                "recommended": not fail2ban,
                "reversible":  True,
                "auto_unban":  False,
            })

        # iptables always available as last resort
        commands.append({
            "command":     f"sudo iptables -A INPUT -s {ip} -p tcp --dport 22 -j DROP",
            "description": "Block via iptables (works on all Linux)",
            "method":      "iptables",
            "recommended": False,
            "reversible":  True,
            "auto_unban":  False,
        })

    elif platform == "macos":
        commands.append({
            "command":     f"echo 'block in quick from {ip} to any' | sudo pfctl -f -",
            "description": "Block via macOS pfctl",
            "method":      "pfctl",
            "recommended": True,
            "reversible":  True,
            "auto_unban":  False,
        })

    return commands


# ── API endpoints ─────────────────────────────────────────────────────────

class HealPreviewRequest(BaseModel):
    command:         str
    finding_message: str = ""
    severity:        str = "CRITICAL"


class HealApproveRequest(BaseModel):
    token:    str
    dry_run:  bool = True
    agent_id: Optional[str] = None


class BlockIPRequest(BaseModel):
    ip:       str
    platform: str = "linux"
    distro:   str = "ubuntu"


@router.post("/heal/preview")
async def heal_preview(req: HealPreviewRequest):
    description = _is_whitelisted(req.command)
    if not description:
        raise HTTPException(
            status_code=400,
            detail="Command not in whitelist. Only pre-approved remediation commands allowed."
        )

    token = _generate_token(req.command)
    _pending[token] = {
        "command":     req.command,
        "description": description,
        "finding":     req.finding_message,
        "severity":    req.severity,
    }

    return {
        "token":           token,
        "command":         req.command,
        "description":     description,
        "risk_level":      "LOW" if "reload" in req.command else "MEDIUM",
        "reversible":      any(k in req.command for k in ["ufw", "fail2ban", "iptables -D"]),
        "auto_unban":      "fail2ban" in req.command,
        "warning":         "This will block the IP at firewall level." if any(
            k in req.command for k in ["ufw", "iptables", "fail2ban", "pfctl", "firewall-cmd"]
        ) else None,
        "dry_run_output":  f"[DRY RUN] Would execute: {req.command}",
        "xp_on_approve":   80,
    }


@router.post("/heal/block-options")
async def get_block_options(req: BlockIPRequest):
    """
    Given an IP + platform/distro, return all available blocking methods.
    Frontend shows these as options before user approves.
    """
    if not _is_valid_ip(req.ip):
        raise HTTPException(status_code=400, detail="Invalid IP address.")

    commands = build_block_commands(req.ip, req.platform, req.distro)
    return {
        "ip":       req.ip,
        "platform": req.platform,
        "distro":   req.distro,
        "options":  commands,
        "fail2ban_available": _check_fail2ban_installed(),
    }


@router.post("/heal/approve")
async def heal_approve(req: HealApproveRequest):
    pending = _pending.pop(req.token, None)
    if not pending:
        raise HTTPException(status_code=404, detail="Token not found or already used.")

    command     = pending["command"]
    description = pending["description"]

    # Route to relay if agent_id provided
    if req.agent_id:
        from services.heal_relay import queue_command_for_agent
        queue_command_for_agent(
            agent_id=req.agent_id,
            token=req.token,
            command=command,
            description=description,
            finding_message=pending.get("finding", ""),
        )
        return {
            "executed":    False,
            "relay":       True,
            "agent_id":    req.agent_id,
            "token":       req.token,
            "command":     command,
            "description": description,
            "status_url":  f"/heal/relay/status/{req.token}",
            "message":     f"Queued for agent '{req.agent_id}'. Poll status_url for result.",
            "xp_awarded":  0,
        }

    # Dry run (demo mode)
    if req.dry_run:
        return {
            "executed":    False,
            "dry_run":     True,
            "command":     command,
            "description": description,
            "output":      f"[DEMO] Would execute: {command}",
            "xp_awarded":  80,
        }

    # Local execution
    try:
        result = _run_whitelisted(command, timeout=10)
        return {
            "executed":    True,
            "command":     command,
            "output":      result.stdout or result.stderr,
            "returncode":  result.returncode,
            "xp_awarded":  80 if result.returncode == 0 else 0,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heal/whitelist")
async def get_whitelist():
    return [{"pattern": p, "description": d} for p, d in COMMAND_WHITELIST]
