"""
services/redis_sessions.py
Redis-backed session history — survives server restarts.
Falls back to in-memory if Redis unavailable.

Install: pip install redis

Usage — drop-in replacement for session_history.py get_session():
    from services.redis_sessions import get_session, clear_session
"""
import json
import os
import time
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import redis
    _redis = redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        db=int(os.environ.get("REDIS_DB", 0)),
        decode_responses=True,
        socket_connect_timeout=2,
    )
    _redis.ping()
    REDIS_AVAILABLE = True
    print("[sessions] Redis connected ✓")
except Exception as e:
    REDIS_AVAILABLE = False
    print(f"[sessions] Redis unavailable ({e}) — using in-memory fallback")

# In-memory fallback
_memory_store: dict = {}

MAX_TURNS    = 20
SESSION_TTL  = 3600  # 1 hour


class Message:
    def __init__(self, role: str, content: str, persona: Optional[str] = None):
        self.role    = role
        self.content = content
        self.persona = persona
        self.ts      = time.time()

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content,
                "persona": self.persona, "ts": self.ts}

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        m = cls(d["role"], d["content"], d.get("persona"))
        m.ts = d.get("ts", time.time())
        return m


class SessionHistory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._key       = f"logoracle:session:{session_id}"

    def _load(self) -> List[Message]:
        if REDIS_AVAILABLE:
            try:
                raw = _redis.get(self._key)
                if raw:
                    return [Message.from_dict(d) for d in json.loads(raw)]
            except Exception:
                pass
        return _memory_store.get(self.session_id, [])

    def _save(self, messages: List[Message]):
        data = [m.to_dict() for m in messages[-MAX_TURNS:]]
        if REDIS_AVAILABLE:
            try:
                _redis.setex(self._key, SESSION_TTL, json.dumps(data))
                return
            except Exception:
                pass
        _memory_store[self.session_id] = messages[-MAX_TURNS:]

    def add(self, role: str, content: str, persona: Optional[str] = None):
        messages = self._load()
        messages.append(Message(role, content, persona))
        self._save(messages)

    def get(self) -> List[Message]:
        return self._load()

    def to_groq_messages(self) -> List[dict]:
        return [{"role": m.role, "content": m.content} for m in self._load()]

    def clear(self):
        if REDIS_AVAILABLE:
            try:
                _redis.delete(self._key)
            except Exception:
                pass
        _memory_store.pop(self.session_id, None)

    def __len__(self):
        return len(self._load())


def get_session(session_id: str = "default") -> SessionHistory:
    return SessionHistory(session_id)


def clear_session(session_id: str = "default"):
    SessionHistory(session_id).clear()


def get_redis_status() -> dict:
    return {
        "redis_available": REDIS_AVAILABLE,
        "backend":         "redis" if REDIS_AVAILABLE else "in-memory",
        "host":            os.environ.get("REDIS_HOST", "localhost"),
        "port":            int(os.environ.get("REDIS_PORT", 6379)),
    }
