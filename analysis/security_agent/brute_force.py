# analysis/security_agent/brute_force.py
import re
from analysis.models.analysis_models import LogEvent
from analysis.security_agent.confidence_scorer import compute_confidence
from typing import List, Optional

SSH_FAIL_RE   = re.compile(r"Failed password|Invalid user|authentication failure", re.IGNORECASE)
RDP_FAIL_RE   = re.compile(r"EventID.*4625|Event ID[:\s]+4625|Logon Type.*3", re.IGNORECASE)
NTLM_FAIL_RE  = re.compile(r"EventID.*4776|NTLM.*fail|Kerberos.*fail", re.IGNORECASE)
MACOS_AUTH_RE = re.compile(r"com\.apple\.opendirectory.*authfailed|PAM.*authentication.*failure", re.IGNORECASE)

SSH_THRESHOLD   = 5
RDP_THRESHOLD   = 5
NTLM_THRESHOLD  = 5
MACOS_THRESHOLD = 5

IP_RE = re.compile(r"from\s+(\d{1,3}(?:\.\d{1,3}){3})")


def detect_brute_force(events: List[LogEvent]) -> Optional[dict]:
    log_text = "\n".join(e.raw for e in events)
    ssh_hits   = [e for e in events if SSH_FAIL_RE.search(e.raw)]
    rdp_hits   = [e for e in events if RDP_FAIL_RE.search(e.raw)]
    ntlm_hits  = [e for e in events if NTLM_FAIL_RE.search(e.raw)]
    macos_hits = [e for e in events if MACOS_AUTH_RE.search(e.raw)]

    if len(ssh_hits) >= SSH_THRESHOLD:
        ip = _extract_ip(ssh_hits)
        rules = ["SSH_FAIL_RE", "BRUTE_THRESHOLD_SSH", "IP_EXTRACTION"]
        if ip != "UNKNOWN_IP":
            rules.append("SOURCE_IP_IDENTIFIED")
        cf = compute_confidence(attack_type="SSH", hit_count=len(ssh_hits),
            threshold=SSH_THRESHOLD, log_text=log_text, rules_fired=rules,
            agents_agreed=2, total_agents=3, source_ip=ip)
        return _make_finding("SSH", len(ssh_hits), "linux/macos", ip,
            f"sudo ufw deny from {ip} && sudo systemctl restart sshd",
            "PowerShell: N/A (SSH brute-force is Linux/macOS)", cf)

    if len(rdp_hits) >= RDP_THRESHOLD:
        ip = _extract_ip(rdp_hits)
        rules = ["RDP_FAIL_RE", "BRUTE_THRESHOLD_RDP", "EVENT_ID_4625"]
        cf = compute_confidence(attack_type="RDP", hit_count=len(rdp_hits),
            threshold=RDP_THRESHOLD, log_text=log_text, rules_fired=rules,
            agents_agreed=2, total_agents=3, source_ip=ip)
        return _make_finding("RDP", len(rdp_hits), "windows", ip,
            f"netsh advfirewall firewall add rule name='Block {ip}' dir=in action=block remoteip={ip}",
            f"New-NetFirewallRule -DisplayName 'Block {ip}' -Direction Inbound -RemoteAddress {ip} -Action Block", cf)

    if len(ntlm_hits) >= NTLM_THRESHOLD:
        rules = ["NTLM_FAIL_RE", "BRUTE_THRESHOLD_NTLM"]
        cf = compute_confidence(attack_type="NTLM/SMB", hit_count=len(ntlm_hits),
            threshold=NTLM_THRESHOLD, log_text=log_text, rules_fired=rules,
            agents_agreed=2, total_agents=3)
        return _make_finding("NTLM/SMB", len(ntlm_hits), "windows", None,
            "Disable NTLMv1 in Group Policy.", None, cf)

    if len(macos_hits) >= MACOS_THRESHOLD:
        rules = ["MACOS_AUTH_RE", "BRUTE_THRESHOLD_MACOS"]
        cf = compute_confidence(attack_type="macOS Auth", hit_count=len(macos_hits),
            threshold=MACOS_THRESHOLD, log_text=log_text, rules_fired=rules,
            agents_agreed=2, total_agents=3)
        return _make_finding("macOS Auth", len(macos_hits), "macos", None,
            "sudo launchctl kickstart -k system/com.openssh.sshd", None, cf)

    return None


def _extract_ip(hits: List[LogEvent]) -> str:
    for e in hits:
        m = IP_RE.search(e.raw)
        if m:
            return m.group(1)
    return "UNKNOWN_IP"


def _make_finding(attack_type, count, platform, source_ip, linux_fix, windows_fix, confidence_factors):
    return {
        "agent":              "security",
        "severity":           "CRITICAL",
        "message":            f"{attack_type} brute-force detected: {count} failed attempts",
        "confidence":         confidence_factors.final_score,
        "confidence_pct":     confidence_factors.final_pct,
        "confidence_factors": confidence_factors.to_dict(),
        "platform":           platform,
        "source_ip":          source_ip,
        "fix_linux":          linux_fix,
        "fix_windows":        windows_fix,
        "popup":              True,
        "fix_linux_plain":    "Run this command in your terminal to block the attacker. Ask your system administrator if unsure.",
    }
