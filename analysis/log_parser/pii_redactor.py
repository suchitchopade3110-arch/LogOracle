import re

PII_PATTERNS = [
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b",                          "[IP_REDACTED]"),
    (r"\b(?:[0-9a-fA-F]{1,4}:){3,7}[0-9a-fA-F]{1,4}\b",      "[IPV6_REDACTED]"),
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b","[EMAIL_REDACTED]"),
    (r"(?<=for user )\S+",                                      "[USER_REDACTED]"),
    (r"(?<=Invalid user )\S+",                                  "[USER_REDACTED]"),
    (r"\bS-\d-\d-\d{2,}-\d+-\d+-\d+\b",                       "[SID_REDACTED]"),
    (r"\\\\[A-Za-z0-9_\-]+\\",                                  "\\\\[HOST_REDACTED]\\"),
    (r"/Users/[A-Za-z0-9_\-]+",                                 "/Users/[USER_REDACTED]"),
    (r"/home/[A-Za-z0-9_\-]+",                                  "/home/[USER_REDACTED]"),
]

def redact_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, lambda _match, value=replacement: value, text)
    return text
