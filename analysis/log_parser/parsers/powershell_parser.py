import re
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")

async def parse(text: str) -> list[LogEvent]:
    events = []
    for line in text.splitlines():
        if not line.strip(): continue
        ts_m = TS_RE.search(line)
        events.append(LogEvent(raw=line, timestamp=ts_m.group(1) if ts_m else None,
                               source="PowerShell", message=line.strip(),
                               severity=tag_severity(line), format="powershell", platform="windows"))
    return events
