import re
from typing import List

CVE_SIGNATURES = [
    {"id": "CVE-2021-4034",  "platforms": ["linux"],                    "pattern": r"pkexec.*polkit",                    "desc": "Polkit privilege escalation (PwnKit)"},
    {"id": "CVE-2022-0847",  "platforms": ["linux"],                    "pattern": r"dirty pipe|PIPE_BUF_FLAG_CAN_MERGE", "desc": "Dirty Pipe — Linux kernel LPE"},
    {"id": "CVE-2021-44228", "platforms": ["linux","windows","macos"],   "pattern": r"jndi:ldap|log4j",                   "desc": "Log4Shell — Log4j JNDI injection RCE"},
    {"id": "CVE-2021-41773", "platforms": ["linux","macos"],             "pattern": r"path traversal.*apache|\.\./",      "desc": "Apache 2.4.49 path traversal"},
    {"id": "CVE-2021-34527", "platforms": ["windows"],                   "pattern": r"PrintNightmare|spoolsv",            "desc": "PrintNightmare — Print Spooler RCE"},
    {"id": "CVE-2020-1472",  "platforms": ["windows"],                   "pattern": r"ZeroLogon|NetrServerAuthenticate",  "desc": "Zerologon — Netlogon privilege escalation"},
    {"id": "CVE-2017-0144",  "platforms": ["windows"],                   "pattern": r"EternalBlue|MS17-010|SMBv1",        "desc": "EternalBlue — SMBv1 RCE (WannaCry vector)"},
    {"id": "CVE-2021-30807", "platforms": ["macos"],                     "pattern": r"IOMobileFrameBuffer|iomfb",         "desc": "macOS IOMobileFrameBuffer memory corruption"},
    {"id": "CVE-2023-32434", "platforms": ["macos"],                     "pattern": r"XNU.*integer overflow|kernel.*XNU", "desc": "Apple XNU kernel integer overflow"},
    {"id": "CVE-2021-26084", "platforms": ["linux","windows"],           "pattern": r"Confluence.*OGNL|confluence.*injection","desc": "Confluence OGNL injection RCE"},
    {"id": "CVE-2022-22965", "platforms": ["linux","windows"],           "pattern": r"Spring.*shell|SpringShell",         "desc": "Spring4Shell — Spring Framework RCE"},
]

def match_cves(log_text: str, platform: str) -> List[dict]:
    matches = []
    for sig in CVE_SIGNATURES:
        if platform not in sig["platforms"]:
            continue
        if re.search(sig["pattern"], log_text, re.IGNORECASE):
            matches.append({
                "agent":      "security",
                "severity":   "CRITICAL",
                "message":    f"CVE match: {sig['id']} — {sig['desc']}",
                "confidence": 0.88,
                "cve_id":     sig["id"],
                "fix":        f"https://nvd.nist.gov/vuln/detail/{sig['id']}",
                "popup":      True,
            })
    return matches
