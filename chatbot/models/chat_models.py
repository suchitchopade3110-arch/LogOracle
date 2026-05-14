# chatbot/models/chat_models.py
from pydantic import BaseModel
from typing import Optional, List, Literal
from enum import Enum

class Persona(str, Enum):
    ARCHITECT = "architect"
    SECURITY  = "security"
    PERF      = "perf"
    MENTOR    = "mentor"
    DEFAULT   = "default"

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    persona: Optional[Persona] = None
    timestamp: Optional[str] = None

class Finding(BaseModel):
    agent: str
    severity: str
    message: str
    confidence: float
    fix: Optional[str] = None
    cwe_id: Optional[str] = None
    finding_id: Optional[str] = None

class DeveloperProfile(BaseModel):
    expertise_level: Optional[str] = "intermediate"   # beginner | intermediate | senior
    past_quiz_scores: List[float] = []
    badges: List[str] = []

class SessionContext(BaseModel):
    findings: List[Finding] = []
    last_log_lines: str = ""                # last 500 lines from monitored logs
    code_diff: str = ""                     # up to 8000 tokens of current file/diff
    chat_history: List[Message] = []        # last 20 turns (managed by session_history.py)
    developer_profile: DeveloperProfile = DeveloperProfile()

class ChatRequest(BaseModel):
    message: str
    session_context: SessionContext
    persona: Persona = Persona.DEFAULT
    mode: Literal["plain", "tech"] = "tech"
    dispute_finding_id: Optional[str] = None   # set if user clicking Dispute button

class ChatResponse(BaseModel):
    reply: str
    intent_detected: str                   # accept | dispute | clarify | plain_english
    dispute_result: Optional[dict] = None  # { verdict: retracted|confirmed, explanation }
    predictive_warning: Optional[str] = None
    xp_awarded: Optional[int] = None
