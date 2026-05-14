"""
services/agent_stream.py
Real-time SSE agent status feed.
Polls current findings every 2s and streams agent health events.
"""
import asyncio
import json
import time
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

# In-memory agent state — updated by analyze/log and security agent calls
_agent_state: dict = {
    "log":           {"status": "idle", "findings": 0, "last_event": None},
    "security":      {"status": "idle", "findings": 0, "last_event": None},
    "performance":   {"status": "idle", "findings": 0, "last_event": None},
    "hallucination": {"status": "idle", "findings": 0, "last_event": None},
    "api":           {"status": "idle", "findings": 0, "last_event": None},
}

_findings_by_agent: dict[str, list] = {}
_health_badge: str = "green"  # green | orange | red


def update_agent_state(agent: str, status: str, findings: list, event_msg: str = None):
    """Called by analyze/log and analyze/code after results come in."""
    global _health_badge
    _agent_state[agent] = {
        "status": status,
        "findings": len(findings),
        "last_event": event_msg,
        "timestamp": time.time(),
    }
    _findings_by_agent[agent] = findings

    # Update health badge
    all_findings = [f for agent_findings in _findings_by_agent.values() for f in agent_findings]
    critical = sum(1 for f in all_findings if f.get("severity") == "CRITICAL")
    warnings  = sum(1 for f in all_findings if f.get("severity") == "WARNING")
    if critical > 0:
        _health_badge = "red"
    elif warnings > 0:
        _health_badge = "orange"
    else:
        _health_badge = "green"


def get_agent_snapshot() -> dict:
    all_findings = [f for agent_findings in _findings_by_agent.values() for f in agent_findings]
    critical = sum(1 for f in all_findings if f.get("severity") == "CRITICAL")
    warnings  = sum(1 for f in all_findings if f.get("severity") == "WARNING")
    return {
        "type":         "agent_status",
        "health_badge": _health_badge,
        "critical":     critical,
        "warnings":     warnings,
        "agents":       _agent_state,
        "timestamp":    time.time(),
    }


async def _stream_agent_events(interval: float = 2.0) -> AsyncGenerator[str, None]:
    """Yield SSE events every `interval` seconds."""
    # Send immediate snapshot on connect
    yield f"data: {json.dumps(get_agent_snapshot())}\n\n"

    while True:
        await asyncio.sleep(interval)
        snapshot = get_agent_snapshot()
        yield f"data: {json.dumps(snapshot)}\n\n"


@router.get("/stream/agents")
async def stream_agents():
    """
    SSE endpoint — frontend connects once, receives agent status every 2s.
    EventSource: new EventSource('/stream/agents')
    """
    return StreamingResponse(
        _stream_agent_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering":"no",
            "Access-Control-Allow-Origin": "*",
        },
    )
