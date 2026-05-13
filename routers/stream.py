from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from agents.orchestrator import Orchestrator
import asyncio
import json

router = APIRouter()
orchestrator = Orchestrator()


@router.get("/logs")
async def stream_logs():
    """SSE: real-time log tail. Agents analyze as lines arrive."""
    async def event_generator():
        while True:
            findings = orchestrator.state.findings
            data = json.dumps([f.__dict__ for f in findings[-5:]])
            yield f"data: {data}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/agents")
async def stream_agents():
    """SSE: live agent status + health badge + severity counts."""
    async def event_generator():
        while True:
            payload = {
                "health": orchestrator.state.health,
                "agent_status": orchestrator.state.agent_status,
                "counts": {
                    "critical": sum(1 for f in orchestrator.state.findings if f.severity == "CRITICAL"),
                    "warning": sum(1 for f in orchestrator.state.findings if f.severity == "WARNING"),
                    "info": sum(1 for f in orchestrator.state.findings if f.severity == "INFO"),
                },
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

