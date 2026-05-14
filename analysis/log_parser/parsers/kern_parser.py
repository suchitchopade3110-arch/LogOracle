import re
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

KERN_RE = re.compile(r"^(?P<ts>\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+\S+\s+kernel:\s*(?P<message>.+)$")

async def parse(text: str) -> list[LogEvent]:
    events = []
    for line in text.splitlines():
        m = KERN_RE.match(line.strip())
        events.append(LogEvent(
            raw=line, timestamp=m.group("ts") if m else None, source="kernel",
            message=m.group("message") if m else line,
            severity=tag_severity(line), format="kern", platform="linux",
        ))
    return events
