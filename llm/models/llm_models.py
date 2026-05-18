# llm/models/llm_models.py
from pydantic import BaseModel
from typing import Optional, List, Literal

class SemanticIssue(BaseModel):
    """Output of Pass 2 — LLM semantic analysis."""
    line: Optional[int] = None
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    message: str
    explanation: str                  # why this is a bug
    cwe_id: Optional[str] = None
    confidence: float                 # 0.0 – 1.0
    fix_hint: Optional[str] = None   # natural language hint, not patch

class AutoFix(BaseModel):
    """Output of auto-fix engine."""
    original_lines: str
    patch_diff: str                   # unified diff format
    explanation: str
    confidence: float
    cwe_id: Optional[str] = None
    auto_applied: bool = False        # True only if confidence >= 0.70 AND AST valid
    line_range: tuple = (0, 0)        # (start, end) — patch must stay within ± 5 lines

class IntentGapResult(BaseModel):
    """Output of intent vs implementation gap detection."""
    gap_score: float                  # cosine distance 0.0–1.0 (higher = bigger gap)
    flagged: bool                     # True if gap_score > 0.4
    severity: Literal["HIGH", "INFO"]
    explanation: str
    stated_intent: str                # extracted from PR title/description
    inferred_behaviour: str           # extracted from code diff AST nodes

class QuizQuestion(BaseModel):
    """MCQ question generated from a real bug."""
    question_id: str
    question: str
    options: List[str]                # exactly 4 options
    correct_index: int                # 0–3
    explanation: str                  # shown after answer
    difficulty: Literal["easy", "medium", "hard"]
    bug_type: str
    cwe_id: Optional[str] = None
    source_finding: Optional[str] = None   # finding_id that generated this question

class QuizAnswerResult(BaseModel):
    """Response after POST /quiz/answer."""
    correct: bool
    correct_index: int
    explanation: str
    xp_awarded: int
    time_bonus: bool                  # True if answered within 15s

class XPEvent(BaseModel):
    action: str
    xp_awarded: int
    total_xp: int
    badge_unlocked: Optional[str] = None
