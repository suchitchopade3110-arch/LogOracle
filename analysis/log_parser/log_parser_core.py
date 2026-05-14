from dataclasses import dataclass, field
from typing import Any
import re

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
SYSLOG_TS_RE = re.compile(r"^([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})")


@dataclass
class ParsedEvent:
    raw: str
    severity: str = "INFO"
    message: str | None = None
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedLog:
    events: list[ParsedEvent]
    platform: str = "linux"


async def parse_log(log_text: str, redact: bool = True) -> ParsedLog:
    events = []
    for line in [line.strip() for line in log_text.splitlines() if line.strip()]:
        timestamp = _extract_timestamp(line)
        source_ip = _extract_source_ip(line)
        severity, message = _classify(line, source_ip)
        raw = IP_RE.sub("<redacted_ip>", line) if redact else line
        events.append(ParsedEvent(
            raw=raw,
            severity=severity,
            message=message,
            timestamp=timestamp,
            metadata={"source_ip": source_ip} if source_ip else {},
        ))
    return ParsedLog(events=events)


def _extract_timestamp(line: str) -> str | None:
    match = SYSLOG_TS_RE.match(line)
    return match.group(1) if match else None


def _extract_source_ip(line: str) -> str | None:
    match = re.search(r"\bfrom\s+((?:\d{1,3}\.){3}\d{1,3})\b", line)
    if match:
        return match.group(1)
    match = IP_RE.search(line)
    return match.group(0) if match else None


def _classify(line: str, source_ip: str | None) -> tuple[str, str]:
    lowered = line.lower()
    if "failed password" in lowered and "sshd" in lowered:
        ip_text = f" from {source_ip}" if source_ip else ""
        return "WARNING", f"SSH failed login attempt{ip_text}"
    if "oom killer" in lowered or "out of memory" in lowered:
        return "CRITICAL", "Out-of-memory condition detected"
    if " 503" in lowered or "status=503" in lowered:
        return "CRITICAL", "HTTP 503 service failure detected"
    if "error" in lowered or "failed" in lowered:
        return "WARNING", line[:200]
    return "INFO", line[:200]
