# chatbot/session_history.py
from chatbot.models.chat_models import Message
from typing import List
from datetime import datetime

MAX_TURNS = 20   # PRD spec: last 20 AI-generated comments and user replies

class SessionHistory:
    def __init__(self):
        self._history: List[Message] = []

    def add(self, role: str, content: str, persona=None):
        msg = Message(
            role=role,
            content=content,
            persona=persona,
            timestamp=datetime.utcnow().isoformat()
        )
        self._history.append(msg)
        # Keep only last MAX_TURNS turns
        if len(self._history) > MAX_TURNS:
            self._history = self._history[-MAX_TURNS:]

    def get(self) -> List[Message]:
        return list(self._history)

    def to_groq_messages(self) -> List[dict]:
        """Format for GROQ API messages array."""
        return [{"role": m.role, "content": m.content} for m in self._history]

    def clear(self):
        self._history = []

    def __len__(self):
        return len(self._history)


# In-memory store keyed by session_id (stateless MVP — resets on server restart)
_sessions: dict[str, SessionHistory] = {}

def get_session(session_id: str = "default") -> SessionHistory:
    if session_id not in _sessions:
        _sessions[session_id] = SessionHistory()
    return _sessions[session_id]

def clear_session(session_id: str = "default"):
    if session_id in _sessions:
        _sessions[session_id].clear()
