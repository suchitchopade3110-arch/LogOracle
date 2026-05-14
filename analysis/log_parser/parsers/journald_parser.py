from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

async def parse(text: str) -> list[LogEvent]:
    events = []
    for entry in text.strip().split("\n\n"):
        fields = {}
        for line in entry.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                fields[k.strip()] = v.strip()
        msg = fields.get("MESSAGE", entry[:200])
        ts  = fields.get("_SOURCE_REALTIME_TIMESTAMP") or fields.get("__REALTIME_TIMESTAMP")
        src = fields.get("_COMM") or fields.get("SYSLOG_IDENTIFIER", "journald")
        events.append(LogEvent(raw=entry[:500], timestamp=ts, source=src, message=msg,
                               severity=tag_severity(msg), format="journald", platform="linux"))
    return events
