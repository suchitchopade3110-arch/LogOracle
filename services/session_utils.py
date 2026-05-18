"""
services/session_utils.py
Handles:
  - GET  /session/share          — generate shareable session URL token
  - POST /session/restore/{token} — restore session state from token
  - Plain/tech mode passed through to all log findings
  - PII detection flag for frontend banner
  - Log chunking for large files
"""
import hashlib
import json
import time
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

# In-memory session store (stateless MVP — tokens expire after 1h)
_session_store: dict = {}
SESSION_TTL = 3600  # 1 hour


class ShareSessionRequest(BaseModel):
    session_id:      str
    findings:        List[dict] = []
    fixes:           List[dict] = []
    root_cause:      Optional[dict] = None
    platform:        str = "unknown"
    distro:          Optional[str] = None
    log_snippet:     str = ""
    code_issues:     List[dict] = []


def _generate_share_token(session_id: str) -> str:
    return hashlib.md5(f"{session_id}{time.time()}".encode()).hexdigest()[:16]


@router.post("/session/share")
async def share_session(req: ShareSessionRequest):
    """Generate a shareable token for the current session state."""
    token = _generate_share_token(req.session_id)
    _session_store[token] = {
        "data":       req.dict(),
        "created_at": time.time(),
    }
    return {
        "token":      token,
        "share_url":  f"/session/restore/{token}",
        "expires_in": SESSION_TTL,
    }


@router.get("/session/restore/{token}")
async def restore_session(token: str):
    """Restore session state from share token."""
    entry = _session_store.get(token)
    if not entry:
        return {"error": "Token not found or expired."}
    if time.time() - entry["created_at"] > SESSION_TTL:
        del _session_store[token]
        return {"error": "Token expired."}
    return entry["data"]


# ── Plain/tech mode helpers ────────────────────────────────────────────────

TECHNICAL_TERMS = {
    "OOM killer":        "memory manager that kills processes when RAM is full",
    "sshd":              "SSH login service",
    "nginx":             "web server",
    "kernel panic":      "system crash",
    "CVE":               "known security vulnerability",
    "brute-force":       "repeated automated login attempts",
    "SQL injection":     "database attack via malicious input",
    "segmentation fault":"program crash due to memory error",
    "journald":          "system log manager",
    "systemd":           "system startup manager",
    "ufw":               "firewall tool",
    "syslog":            "system event log",
    "dmesg":             "kernel message log",
    "PID":               "process ID number",
    "NTLM":              "Windows login protocol",
    "CWE":               "weakness category ID",
    "OWASP":             "security standard",
}


def apply_plain_mode(text: str) -> str:
    """Replace technical terms with plain English equivalents."""
    for tech, plain in TECHNICAL_TERMS.items():
        text = text.replace(tech, f"{tech} ({plain})")
    return text


def translate_finding(finding: dict, mode: str) -> dict:
    """Apply plain/tech mode to a finding dict."""
    if mode != "plain":
        return finding
    result = dict(finding)
    if result.get("message"):
        result["message"] = apply_plain_mode(result["message"])
    if result.get("fix_linux"):
        result["fix_linux_plain"] = (
            "Run this command in your terminal to fix the issue. "
            "Ask your system administrator if unsure."
        )
    return result


# ── PII detection flag ─────────────────────────────────────────────────────

import re

PII_INDICATORS = [
    r"\bauth\.log\b",
    r"\bsecure\b",
    r"Failed password for",
    r"Accepted password for",
    r"Invalid user",
    r"\bS-\d-\d-",     # Windows SID
    r"/home/[a-zA-Z]", # Linux home path
    r"/Users/[a-zA-Z]",# macOS home path
]


def detect_pii_presence(log_text: str) -> dict:
    """Return PII detection result for frontend banner."""
    detected = []
    for pattern in PII_INDICATORS:
        if re.search(pattern, log_text, re.IGNORECASE):
            detected.append(pattern)
    return {
        "pii_detected":  len(detected) > 0,
        "pii_indicators": len(detected),
        "show_banner":   len(detected) > 0,
        "banner_message": (
            "This log contains potentially sensitive data (usernames, IPs, paths). "
            "PII has been automatically redacted before AI processing."
            if detected else None
        ),
    }


# ── Log chunking ───────────────────────────────────────────────────────────

def chunk_log_text(log_text: str, max_lines: int = 500) -> List[str]:
    """Split large log into analysis-sized chunks."""
    lines  = log_text.strip().splitlines()
    chunks = []
    for i in range(0, len(lines), max_lines):
        chunks.append("\n".join(lines[i:i + max_lines]))
    return chunks or [log_text]


def chunk_summary(chunks: List[str]) -> dict:
    return {
        "chunk_count": len(chunks),
        "total_lines": sum(len(c.splitlines()) for c in chunks),
        "chunked":     len(chunks) > 1,
    }
