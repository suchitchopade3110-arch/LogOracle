import re
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

UNIFIED_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+[+-]\d{4})\s+"
    r"0x\S+\s+(?P<type>\S+)\s+\S+\s+(?P<pid>\d+)\s+\S+\s+(?P<process>[^:]+):\s+(?P<message>.+)$"
)

async def parse(text: str) -> list[LogEvent]:
    events = []
    for line in text.splitlines():
        m = UNIFIED_RE.match(line.strip())
        events.append(LogEvent(raw=line, timestamp=m.group("ts") if m else None,
                               source=m.group("process").strip() if m else "macos",
                               message=m.group("message") if m else line,
                               severity=tag_severity(line), format="unified_log", platform="macos"))
    return events
