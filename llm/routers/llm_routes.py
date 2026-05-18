# llm/routers/llm_routes.py
"""
Subhiksha's endpoints — mounted by Suchit's main.py:
  app.include_router(llm_routes.router)

Endpoints:
  POST /analyze/semantic     — Pass 2 only (called by Suchit's /analyze/code pipeline)
  POST /analyze/intent       — intent vs implementation gap
  POST /analyze/fix          — auto-fix for a single issue
  POST /quiz/generate        — MCQ from bug record
  POST /quiz/answer          — submit answer + award XP
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from llm.passes.semantic_pass import run_semantic_pass
from llm.passes.intent_gap import detect_intent_gap
from llm.passes.auto_fix import generate_fix
from llm.quiz.generator_and_validator import generate_question, validate_question
from llm.models.llm_models import QuizAnswerResult

router = APIRouter()

# ── in-memory XP ledger (stateless MVP) ──────────────────────────────────
_xp_store: dict = {}   # { developer_id: int }
_questions: dict = {}  # { question_id: QuizQuestion }

XP_CORRECT      = 50
XP_CORRECT_FAST = 70   # correct + within 15s
XP_WRONG        = 10
TIME_BONUS_SEC  = 15


# ── Request models ─────────────────────────────────────────────────────────

class SemanticRequest(BaseModel):
    code: str
    language: str
    ast_issues: List[dict] = []

class IntentRequest(BaseModel):
    code_diff: str
    pr_title: str
    pr_description: str
    language: str = "python"

class FixRequest(BaseModel):
    code: str
    language: str
    issue: dict            # {line, severity, message, cwe_id}

class QuizGenerateRequest(BaseModel):
    bug_type: str
    message: str
    code_snippet: str
    fix: str
    severity: str = "MEDIUM"
    cwe_id: str = "N/A"
    finding_id: Optional[str] = None

class QuizAnswerRequest(BaseModel):
    question_id: str
    selected_option: int   # 0–3
    time_seconds: float
    developer_id: str = "default"


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/analyze/semantic")
async def analyze_semantic(req: SemanticRequest):
    """Pass 2: semantic/LLM bug detection. Called by Suchit's 3-pass pipeline."""
    issues = await run_semantic_pass(req.code, req.language, req.ast_issues)
    return {"issues": [i.model_dump() for i in issues], "pass": 2}


@router.post("/analyze/intent")
async def analyze_intent(req: IntentRequest):
    """Intent vs implementation gap detection."""
    result = await detect_intent_gap(
        code_diff=req.code_diff,
        pr_title=req.pr_title,
        pr_description=req.pr_description,
        language=req.language,
    )
    return result.model_dump()


@router.post("/analyze/fix")
async def analyze_fix(req: FixRequest):
    """Generate auto-fix for a single detected issue."""
    fix = await generate_fix(req.code, req.language, req.issue)
    return fix.model_dump()


@router.post("/quiz/generate")
async def quiz_generate(req: QuizGenerateRequest):
    """Generate MCQ from real bug. Returns question or 503 if validation fails."""
    question = await generate_question(
        bug_type=req.bug_type,
        message=req.message,
        code_snippet=req.code_snippet,
        fix=req.fix,
        severity=req.severity,
        cwe_id=req.cwe_id,
        finding_id=req.finding_id,
    )
    if question is None:
        return {"error": "Question generation failed validation after 2 attempts."}

    _questions[question.question_id] = question
    # Return question WITHOUT correct_index (don't leak answer to frontend)
    return {
        "question_id": question.question_id,
        "question": question.question,
        "options": question.options,
        "difficulty": question.difficulty,
        "bug_type": question.bug_type,
    }


@router.post("/quiz/answer")
async def quiz_answer(req: QuizAnswerRequest):
    """Submit answer, award XP, return result."""
    question = _questions.get(req.question_id)
    if not question:
        return {"error": f"Unknown question_id: {req.question_id}"}

    correct = req.selected_option == question.correct_index
    time_bonus = correct and req.time_seconds <= TIME_BONUS_SEC

    if correct:
        xp = XP_CORRECT_FAST if time_bonus else XP_CORRECT
    else:
        xp = XP_WRONG

    # Update XP store
    prev = _xp_store.get(req.developer_id, 0)
    _xp_store[req.developer_id] = prev + xp

    return QuizAnswerResult(
        correct=correct,
        correct_index=question.correct_index,
        explanation=question.explanation,
        xp_awarded=xp,
        time_bonus=time_bonus,
    ).model_dump()
