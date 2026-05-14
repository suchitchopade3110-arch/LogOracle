import re
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity  # FIX: was log_parser_core

SYSLOG_RE = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<source>\S+?)(?:\[\d+\])?\s*:\s*(?P<message>.+)$"
)

async def parse(text: str) -> list[LogEvent]:
    events = []
    for line in text.splitlines():
        m = SYSLOG_RE.match(line.strip())
        if m:
            events.append(LogEvent(
                raw=line,
                timestamp=f"{m.group('month')} {m.group('day')} {m.group('time')}",
                source=m.group("source"), message=m.group("message"),
                severity=tag_severity(line), format="syslog", platform="linux",
            ))
        elif line.strip():
            events.append(LogEvent(raw=line, message=line, format="syslog",
                                   platform="linux", severity=tag_severity(line)))
    return events
