"""
services/api_agent.py
API Agent — detects HTTP failures, retry storms, latency spikes.
POST /ingest/api_events  — receive API event data
POST /analyze/api        — analyze a batch of API events
"""
import re
import time
from collections import defaultdict
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# In-memory event buffer
_api_events: List[dict] = []

RETRY_STORM_THRESHOLD = 10   # same endpoint, same error, within window
LATENCY_SPIKE_MS      = 2000 # P95 latency threshold
ERROR_RATE_THRESHOLD  = 0.3  # 30% error rate


class APIEvent(BaseModel):
    method:      str        # GET, POST, etc.
    url:         str
    status_code: int
    latency_ms:  float
    timestamp:   float = 0.0
    error:       Optional[str] = None


class APIIngestRequest(BaseModel):
    events: List[APIEvent]


class APIAnalyzeRequest(BaseModel):
    events: List[APIEvent] = []
    window_seconds: int = 60


@router.post("/ingest/api_events")
async def ingest_api_events(req: APIIngestRequest):
    """Receive API events from client-side interceptor or manual input."""
    for e in req.events:
        if not e.timestamp:
            e.timestamp = time.time()
        _api_events.append(e.dict())
        if len(_api_events) > 1000:
            _api_events.pop(0)
    return {"ingested": len(req.events)}


def _analyze_events(events: List[dict]) -> List[dict]:
    findings = []

    if not events:
        return findings

    # Group by endpoint
    by_endpoint: dict = defaultdict(list)
    for e in events:
        # Normalize URL — strip query params and IDs
        url = re.sub(r"/\d+", "/{id}", e["url"])
        url = re.sub(r"\?.*$", "", url)
        by_endpoint[f"{e['method']} {url}"].append(e)

    for endpoint, evts in by_endpoint.items():
        errors   = [e for e in evts if e["status_code"] >= 400]
        latencies = [e["latency_ms"] for e in evts]

        # Retry storm detection
        if len(errors) >= RETRY_STORM_THRESHOLD:
            status_codes = set(e["status_code"] for e in errors)
            findings.append({
                "agent":      "api",
                "severity":   "CRITICAL",
                "message":    f"Retry storm: {len(errors)} failures on {endpoint} "
                              f"(status codes: {', '.join(str(s) for s in status_codes)})",
                "confidence": 0.91,
                "fix":        "Add exponential backoff with jitter. Set circuit breaker. Cache last known good response.",
                "finding_id": f"api_retry_{hash(endpoint) % 9999:04d}",
            })

        # High error rate
        error_rate = len(errors) / max(len(evts), 1)
        if error_rate >= ERROR_RATE_THRESHOLD and len(evts) >= 5:
            findings.append({
                "agent":      "api",
                "severity":   "WARNING",
                "message":    f"High error rate {error_rate:.0%} on {endpoint} ({len(errors)}/{len(evts)} requests failed)",
                "confidence": 0.85,
                "fix":        "Check upstream service health. Review error responses.",
                "finding_id": f"api_errrate_{hash(endpoint) % 9999:04d}",
            })

        # Latency spike
        if latencies:
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            if p95 >= LATENCY_SPIKE_MS:
                findings.append({
                    "agent":      "api",
                    "severity":   "WARNING",
                    "message":    f"Latency spike on {endpoint}: P95={p95:.0f}ms (threshold: {LATENCY_SPIKE_MS}ms)",
                    "confidence": 0.88,
                    "fix":        "Profile slow queries. Check DB connection pool. Add caching.",
                    "finding_id": f"api_latency_{hash(endpoint) % 9999:04d}",
                })

    return findings


@router.post("/analyze/api")
async def analyze_api(req: APIAnalyzeRequest):
    """Analyze a batch of API events for anomalies."""
    events = req.events if req.events else [APIEvent(**e) for e in _api_events[-500:]]
    findings = _analyze_events([e.dict() if hasattr(e, "dict") else e for e in events])
    return {
        "event_count": len(events),
        "findings":    findings,
        "finding_count": len(findings),
    }
