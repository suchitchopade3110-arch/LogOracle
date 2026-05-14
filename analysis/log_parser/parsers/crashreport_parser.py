import re
from analysis.models.analysis_models import LogEvent

async def parse(text: str) -> list[LogEvent]:
    fields = {
        "Incident Identifier": r"Incident Identifier:\s+(\S+)",
        "Process":             r"Process:\s+(.+)",
        "Exception Type":      r"Exception Type:\s+(.+)",
        "Exception Subtype":   r"Exception Subtype:\s+(.+)",
        "Crashed Thread":      r"Crashed Thread:\s+(.+)",
        "OS Version":          r"OS Version:\s+(.+)",
    }
    extracted = {}
    for key, pat in fields.items():
        m = re.search(pat, text)
        if m:
            extracted[key] = m.group(1).strip()
    summary = "; ".join(f"{k}: {v}" for k, v in extracted.items())
    return [LogEvent(
        raw=text[:500], timestamp=None,
        source=extracted.get("Process", "unknown"),
        message=summary or "macOS crash report — see raw for full details",
        severity="CRITICAL", format="crashreport", platform="macos",
    )]
