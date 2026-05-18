from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

async def parse(text: str) -> list[LogEvent]:
    events = []; fields = []
    for line in text.splitlines():
        if line.startswith("#Fields:"):
            fields = line.split()[1:]; continue
        if line.startswith("#") or not line.strip(): continue
        parts = line.split(); row = dict(zip(fields, parts)) if fields else {}
        status = row.get("sc-status", ""); method = row.get("cs-method", "GET"); uri = row.get("cs-uri-stem", "/")
        ts = f"{row.get('date','')} {row.get('time','')}".strip()
        msg = f"IIS {method} {uri} → {status}"
        events.append(LogEvent(raw=line, timestamp=ts or None, source="IIS", message=msg,
                               severity=tag_severity(msg + status), format="iis", platform="windows"))
    return events
