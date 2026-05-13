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
    mode: str = "plain"
    distro: Optional[str] = None


class CorrelateRequest(BaseModel):
    logs: List[dict]


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
    all_findings = []
    for log in req.logs:
        findings = await orchestrator.run_all_agents(log["content"], session_id=log["name"])
        all_findings.extend(findings)
    chain = correlation.build_chain(all_findings)
    return {"root_cause_chain": correlation.to_dict(chain), "findings": [f.__dict__ for f in all_findings]}


@router.post("/code")
async def analyze_code(req: CodeRequest):
    return {"status": "stub", "issues": []}


@router.post("/intent")
async def analyze_intent(req: dict):
    return {"status": "stub", "gap_score": 0.0}

