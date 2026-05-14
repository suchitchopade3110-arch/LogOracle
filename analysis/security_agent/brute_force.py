import re
from analysis.models.analysis_models import LogEvent
from typing import List, Optional

SSH_FAIL_RE   = re.compile(r"Failed password|Invalid user|authentication failure", re.IGNORECASE)
RDP_FAIL_RE   = re.compile(r"EventID.*4625|Event ID[:\s]+4625|Logon Type.*3", re.IGNORECASE)
NTLM_FAIL_RE  = re.compile(r"EventID.*4776|NTLM.*fail|Kerberos.*fail", re.IGNORECASE)
MACOS_AUTH_RE = re.compile(r"com\.apple\.opendirectory.*authfailed|PAM.*authentication.*failure", re.IGNORECASE)

# Bug 3 fix: PRD spec = 5 attempts threshold (was 10)
SSH_THRESHOLD   = 5
RDP_THRESHOLD   = 5
NTLM_THRESHOLD  = 5
MACOS_THRESHOLD = 5

# Regex to extract source IP from SSH failure lines
IP_RE = re.compile(r"from\s+(\d{1,3}(?:\.\d{1,3}){3})")

def detect_brute_force(events: List[LogEvent]) -> Optional[dict]:
    ssh_hits   = [e for e in events if SSH_FAIL_RE.search(e.raw)]
    rdp_hits   = [e for e in events if RDP_FAIL_RE.search(e.raw)]
    ntlm_hits  = [e for e in events if NTLM_FAIL_RE.search(e.raw)]
    macos_hits = [e for e in events if MACOS_AUTH_RE.search(e.raw)]

    if len(ssh_hits) >= SSH_THRESHOLD:
        # Bug 4 fix: extract source_ip so router can pass to get_fix()
        ip = _extract_ip(ssh_hits)
        return _make_finding("SSH", len(ssh_hits), "linux/macos", ip,
                             f"sudo ufw deny from {ip} && sudo systemctl restart sshd",
                             "PowerShell: N/A (SSH brute-force is Linux/macOS)")

    if len(rdp_hits) >= RDP_THRESHOLD:
        ip = _extract_ip(rdp_hits)
        return _make_finding("RDP", len(rdp_hits), "windows", ip,
                             "sudo ufw deny from {ip}",
                             f"New-NetFirewallRule -DisplayName 'Block {ip}' -Direction Inbound -RemoteAddress {ip} -Action Block")

    if len(ntlm_hits) >= NTLM_THRESHOLD:
        return _make_finding("NTLM/SMB", len(ntlm_hits), "windows", None,
                             "Disable NTLMv1 in Group Policy.", None)

    if len(macos_hits) >= MACOS_THRESHOLD:
        return _make_finding("macOS Auth", len(macos_hits), "macos", None,
                             "sudo launchctl kickstart -k system/com.openssh.sshd", None)

    return None

def _extract_ip(hits: List[LogEvent]) -> str:
    for e in hits:
        m = IP_RE.search(e.raw)
        if m:
            return m.group(1)
    return "UNKNOWN_IP"

def _make_finding(attack_type, count, platform, source_ip, linux_fix, windows_fix):
    return {
        "agent":      "security",
        "severity":   "CRITICAL",
        "message":    f"{attack_type} brute-force detected: {count} failed attempts",
        "confidence": 0.94,
        "platform":   platform,
        "source_ip":  source_ip,   # Bug 4 fix: included for fix command substitution
        "fix_linux":  linux_fix,
        "fix_windows":windows_fix,
        "popup":      True,
    }
