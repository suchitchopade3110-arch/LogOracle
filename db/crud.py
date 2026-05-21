from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import AnalysisHistory, UserSession
from datetime import datetime
import uuid


async def save_analysis(
    db: AsyncSession,
    user: dict,
    log_text: str,
    result: dict,
    findings_count: int,
    severity: str = "INFO"
):
    entry = AnalysisHistory(
        id=str(uuid.uuid4()),
        user_id=user["id"],
        username=user.get("username", "unknown"),
        org=user.get("org", "default"),
        log_text=log_text[:500],  # truncate for storage
        findings_count=findings_count,
        severity=severity,
        result=result,
        created_at=datetime.utcnow()
    )
    db.add(entry)
    await db.commit()
    return entry


async def get_user_history(db: AsyncSession, user_id: str, limit: int = 20):
    result = await db.execute(
        select(AnalysisHistory)
        .where(AnalysisHistory.user_id == user_id)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def upsert_session(db: AsyncSession, user: dict):
    result = await db.execute(
        select(UserSession).where(UserSession.user_id == user["id"])
    )
    session = result.scalar_one_or_none()
    if session:
        session.last_seen = datetime.utcnow()
    else:
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=user["id"],
            username=user.get("username", "unknown"),
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        db.add(session)
    await db.commit()
    return session
