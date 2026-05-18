import re
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

AUTH_RE = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"\S+\s+(?P<source>sshd|sudo|su|pam\S*?)(?:\[\d+\])?\s*:\s*(?P<message>.+)$"
)

async def parse(text: str) -> list[LogEvent]:
    events = []
    for line in text.splitlines():
        m = AUTH_RE.match(line.strip())
        events.append(LogEvent(
            raw=line,
            timestamp=f"{m.group('month')} {m.group('day')} {m.group('time')}" if m else None,
            source=m.group("source") if m else "auth",
            message=m.group("message") if m else line,
            severity=tag_severity(line), format="auth", platform="linux",
        ))
    return events
