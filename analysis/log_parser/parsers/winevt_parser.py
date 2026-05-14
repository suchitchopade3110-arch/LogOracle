import re, xml.etree.ElementTree as ET
from analysis.models.analysis_models import LogEvent
from analysis.log_parser.severity_tagger import tag_severity

WIN_EVENT_DESCRIPTIONS = {
    "4624": "Successful logon", "4625": "Failed logon attempt",
    "4648": "Logon with explicit credentials", "4672": "Special privilege assigned",
    "4688": "New process created", "4720": "User account created",
    "4726": "User account deleted", "4740": "User account locked out",
    "4776": "NTLM authentication attempt", "7045": "New service installed",
    "1102": "Audit log cleared",
}

async def parse(text: str) -> list[LogEvent]:
    if "<Event xmlns" in text or "<EventID>" in text:
        return _parse_xml(text)
    return _parse_plaintext(text)

def _parse_xml(text: str) -> list[LogEvent]:
    events = []
    for raw in re.findall(r"<Event[^>]*>.*?</Event>", text, re.DOTALL):
        try:
            root = ET.fromstring(raw)
            ns = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
            event_id = root.findtext(".//e:EventID", namespaces=ns) or root.findtext(".//EventID", "?")
            tc = root.find(".//e:TimeCreated", namespaces=ns)
            ts = tc.get("SystemTime", "") if tc is not None else ""
            source = (root.find(".//e:Provider", namespaces=ns) or root).get("Name", "Windows")
            msg = root.findtext(".//e:Message", namespaces=ns) or WIN_EVENT_DESCRIPTIONS.get(event_id, f"Event ID {event_id}")
            events.append(LogEvent(raw=raw[:300], timestamp=ts, source=source, message=msg,
                                   severity=tag_severity(msg + f" EventID:{event_id}"),
                                   format="winevt", platform="windows", event_id=event_id))
        except Exception:
            continue
    return events

def _parse_plaintext(text: str) -> list[LogEvent]:
    events = []
    eid_re  = re.compile(r"Event ID[:\s]+(\d+)", re.IGNORECASE)
    date_re = re.compile(r"Date[:\s]+([\d/\-]+ [\d:]+)", re.IGNORECASE)
    src_re  = re.compile(r"Source[:\s]+(\S+)", re.IGNORECASE)
    for block in re.split(r"\n{2,}", text):
        eid_m = eid_re.search(block); date_m = date_re.search(block); src_m = src_re.search(block)
        eid = eid_m.group(1) if eid_m else None
        msg = WIN_EVENT_DESCRIPTIONS.get(eid, block[:200].strip())
        events.append(LogEvent(raw=block[:300], timestamp=date_m.group(1) if date_m else None,
                               source=src_m.group(1) if src_m else "Windows", message=msg,
                               severity=tag_severity(block + (f" EventID:{eid}" if eid else "")),
                               format="winevt", platform="windows", event_id=eid))
    return events
