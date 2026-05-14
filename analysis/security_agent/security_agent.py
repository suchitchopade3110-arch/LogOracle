from collections import Counter
from typing import Any

BRUTE_FORCE_THRESHOLD = 5


def detect_brute_force(events: list[Any]) -> dict | None:
    failed = [
        event for event in events
        if "failed password" in event.raw.lower() or "ssh failed login" in (event.message or "").lower()
    ]
    if len(failed) < BRUTE_FORCE_THRESHOLD:
        return None

    ips = [
        event.metadata.get("source_ip")
        for event in failed
        if getattr(event, "metadata", None) and event.metadata.get("source_ip")
    ]
    attacker_ip = Counter(ips).most_common(1)[0][0] if ips else "<attacker_ip>"
    return {
        "message": f"SSH brute-force detected: {len(failed)} failed attempts from {attacker_ip}",
        "confidence": 0.94,
        "fix_linux": f"sudo ufw deny from {attacker_ip} && sudo systemctl restart sshd",
    }


def match_cves(log_text: str, platform: str) -> list[dict]:
    # TODO: replace with Shruthi's CVE signature matcher.
    return []
