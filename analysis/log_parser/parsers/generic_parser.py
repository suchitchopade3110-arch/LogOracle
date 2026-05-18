import re
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

TS_PATTERNS = [
    re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"),
    re.compile(r"(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})"),
    re.compile(r"(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})"),
]

async def parse(text: str) -> list[LogEvent]:
    events = []
    for line in text.splitlines():
        if not line.strip(): continue
        ts = None
        for pat in TS_PATTERNS:
            m = pat.search(line)
            if m: ts = m.group(1); break
        events.append(LogEvent(raw=line, timestamp=ts, message=line.strip(),
                               severity=tag_severity(line), format="generic", platform="unknown"))
    return events
