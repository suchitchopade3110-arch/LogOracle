# routers/stream.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from agents.orchestrator import Orchestrator
import asyncio, json

router = APIRouter()
orchestrator = Orchestrator()

@router.get("/logs")
async def stream_logs():
    """SSE: real-time log tail. Agents analyze as lines arrive."""
    async def event_generator():
        # TODO: tail journald / syslog via subprocess
        # For now: yield agent findings as they come in
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
                    "warning":  sum(1 for f in orchestrator.state.findings if f.severity == "WARNING"),
                    "info":     sum(1 for f in orchestrator.state.findings if f.severity == "INFO"),
                }
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# routers/analyze.py
from fastapi import APIRouter
from pydantic import BaseModel
from agents.orchestrator import Orchestrator
from agents.correlation_engine import CorrelationEngine
from typing import List, Optional

router = APIRouter()
orchestrator = Orchestrator()
correlation = CorrelationEngine()

class LogRequest(BaseModel):
    log_text: str
    mode: str = "plain"       # plain | tech
    distro: Optional[str] = None

class CorrelateRequest(BaseModel):
    logs: List[dict]           # [{name, content}]

class CodeRequest(BaseModel):
    code: str
    language: str
    pr_context: Optional[dict] = None

@router.post("/log")
async def analyze_log(req: LogRequest):
    findings = await orchestrator.run_all_agents(req.log_text, session_id="default")
    chain = correlation.build_chain(findings)
    return {
        "findings": [f.__dict__ for f in findings],
        "root_cause_chain": correlation.to_dict(chain),
        "health": orchestrator.state.health,
    }

@router.post("/correlate")
async def analyze_correlate(req: CorrelateRequest):
    # Multi-file: run all agents on each, then correlate across
    all_findings = []
    for log in req.logs:
        findings = await orchestrator.run_all_agents(log["content"], session_id=log["name"])
        all_findings.extend(findings)
    chain = correlation.build_chain(all_findings)
    return {"root_cause_chain": correlation.to_dict(chain), "findings": [f.__dict__ for f in all_findings]}

@router.post("/code")
async def analyze_code(req: CodeRequest):
    # TODO: wire Shruthi's AST pass + Subhiksha's LLM pass + OWASP pass
    return {"status": "stub", "issues": []}

@router.post("/intent")
async def analyze_intent(req: dict):
    # TODO: Subhiksha's 2-stage LLM intent-gap pipeline
    return {"status": "stub", "gap_score": 0.0}


# routers/heal.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.self_heal import SelfHealService

router = APIRouter()
heal_service = SelfHealService()

class ApproveRequest(BaseModel):
    command_id: str
    confirmed: bool

@router.post("/approve")
async def approve_heal(req: ApproveRequest):
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="confirmed must be true")
    result = await heal_service.execute(req.command_id)
    return result
