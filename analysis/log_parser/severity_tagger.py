import re
from typing import Literal

SeverityLevel = Literal["CRITICAL", "WARNING", "INFO"]

CRITICAL_PATTERNS = [
    r"kernel panic", r"OOM killer", r"out of memory", r"segfault",
    r"BSOD", r"BlueScreen", r"Critical.*Error", r"CRITICAL",
    r"brute.?force", r"ransomware",
    r"EventID.*4625.*\b(50|100|200)\b",
    r"panic\(cpu", r"Incident Identifier", r"CVE-\d{4}-\d+",
    r"privilege escalat", r"lateral movement",
]

WARNING_PATTERNS = [
    r"\bwarn(ing)?\b", r"\berror\b", r"failed", r"timeout",
    r"refused", r"denied",
    r"EventID.*(4648|4776|4771)",
    r"com\.apple.*fault",
    r"disk.*\b(9[0-9]|100)%",
    r"high (cpu|memory|load)",
]

def tag_severity(line: str) -> SeverityLevel:
    for pat in CRITICAL_PATTERNS:
        if re.search(pat, line, re.IGNORECASE):
            return "CRITICAL"
    lower = line.lower()
    for pat in WARNING_PATTERNS:
        if re.search(pat, lower):
            return "WARNING"
    return "INFO"
