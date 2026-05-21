from sqlalchemy import Column, String, DateTime, Text, Integer, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    username = Column(String, nullable=True)
    org = Column(String, nullable=True, default="default")
    log_text = Column(Text, nullable=False)
    findings_count = Column(Integer, default=0)
    severity = Column(String, default="INFO")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    username = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
