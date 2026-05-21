from fastapi import APIRouter, Depends
from auth.dependencies import get_current_user
from db.database import get_db
from db.crud import save_analysis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
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
async def analyze_log(req: LogRequest, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    print(f"[DEBUG USER] {user}")
    # Ensure user has id for DB (API key mode = anonymous user)
    if not user.get("id"):
        user["id"] = "anonymous"
        user["username"] = "anonymous"
    findings = await orchestrator.run_all_agents(req.log_text, session_id="default")
    chain = correlation.build_chain(findings)
    result = {
        "findings": [f.__dict__ for f in findings],
        "root_cause_chain": correlation.to_dict(chain),
        "health": orchestrator.state.health,
    }
    try:
        await save_analysis(
            db=db,
            user=user,
            log_text=req.log_text,
            result=result,
            findings_count=len(findings),
            severity=orchestrator.state.health or "INFO"
        )
    except Exception as e:
        import traceback
        print(f"[DB SAVE ERROR] {e}")
        traceback.print_exc()
    return result


@router.post("/correlate")
async def analyze_correlate(req: CorrelateRequest, user: dict = Depends(get_current_user)):
    all_findings = []
    for log in req.logs:
        findings = await orchestrator.run_all_agents(log["content"], session_id=log["name"])
        all_findings.extend(findings)
    chain = correlation.build_chain(all_findings)
    return {"root_cause_chain": correlation.to_dict(chain), "findings": [f.__dict__ for f in all_findings]}


@router.post("/code")
async def analyze_code(req: CodeRequest, user: dict = Depends(get_current_user)):
    from analysis.ast_engine.ast_engine import run_ast_pass, run_owasp_pass
    from llm.passes.semantic_pass import run_semantic_pass

    pass1 = await run_ast_pass(req.code, req.language)
    pass2 = await run_semantic_pass(req.code, req.language, [i.model_dump() for i in pass1])
    pass3 = await run_owasp_pass(req.code, req.language)

    all_issues = (
        [i.model_dump() for i in pass1] +
        [i.model_dump() for i in pass2] +
        [i.model_dump() for i in pass3]
    )

    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    all_issues.sort(key=lambda x: order.index(x.get("severity", "INFO")))

    return {
        "pass1_count": len(pass1),
        "pass2_count": len(pass2),
        "pass3_count": len(pass3),
        "issues": all_issues,
    }


@router.post("/intent")
async def analyze_intent(req: dict, user: dict = Depends(get_current_user)):
    from llm.passes.intent_gap import detect_intent_gap
    result = await detect_intent_gap(
        code_diff=req.get("code_diff", ""),
        pr_title=req.get("pr_title", ""),
        pr_description=req.get("pr_description", ""),
        language=req.get("language", "python"),
    )
    return result.model_dump()


@router.get("/history")
async def get_history(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from db.crud import get_user_history
    entries = await get_user_history(db, user_id=user["id"])
    return {
        "user": user["username"],
        "total": len(entries),
        "history": [
            {
                "id": e.id,
                "findings_count": e.findings_count,
                "severity": e.severity,
                "created_at": e.created_at.isoformat(),
                "log_preview": e.log_text[:100],
            }
            for e in entries
        ]
    }
