import re
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

DMESG_RE = re.compile(r"^\[\s*(?P<ts>\d+\.\d+)\]\s+(?P<message>.+)$")

async def parse(text: str) -> list[LogEvent]:
    events = []
    for line in text.splitlines():
        m = DMESG_RE.match(line.strip())
        msg = m.group("message") if m else line
        ts  = m.group("ts") if m else None
        events.append(LogEvent(raw=line, timestamp=ts, message=msg,
                               severity=tag_severity(line), format="dmesg", platform="linux"))
    return events
