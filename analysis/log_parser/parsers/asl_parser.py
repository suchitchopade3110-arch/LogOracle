import re
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

ASL_RE = re.compile(r"\[(?P<ts>[^\]]+)\] \[(?P<level>[^\]]+)\] (?P<sender>[^:]+): (?P<message>.+)")

async def parse(text: str) -> list[LogEvent]:
    events = []
    for line in text.splitlines():
        m = ASL_RE.match(line.strip())
        events.append(LogEvent(raw=line, timestamp=m.group("ts") if m else None,
                               source=m.group("sender").strip() if m else "asl",
                               message=m.group("message") if m else line,
                               severity=tag_severity(line), format="asl", platform="macos"))
    return events
