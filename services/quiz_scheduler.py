"""
services/quiz_scheduler.py
SM-2 spaced repetition scheduler for quiz questions.
Streak tracking with daily check.
Badge unlock push via SSE-compatible event queue.
"""
import math
import time
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter()

# In-memory SM-2 cards keyed by (developer_id, question_id)
_sm2_cards: Dict[str, dict] = {}

# Badge event queue — frontend polls GET /badges/events
_badge_events: List[dict] = []

# Streak tracking keyed by developer_id
_streaks: Dict[str, dict] = {}

BADGE_DEFINITIONS = {
    "Bug Slayer":       {"desc": "Resolve 10 bugs",            "icon": "🛡️"},
    "Speed Fixer":      {"desc": "Self-heal approved < 5s",    "icon": "⚡"},
    "Quiz Master":      {"desc": "10 consecutive correct",     "icon": "🏆"},
    "Security Expert":  {"desc": "Security quiz ≥ 85%",        "icon": "🔒"},
    "30-Day Streak":    {"desc": "1 quiz/day for 30 days",     "icon": "🔥"},
    "Code Legend":      {"desc": "1,000 XP total",             "icon": "⭐"},
    "Dispute Champion": {"desc": "5 findings disputed + won",  "icon": "⚖️"},
    "Chain Breaker":    {"desc": "Resolve 4+ agent chain",     "icon": "⛓️"},
}


# ── SM-2 Algorithm ─────────────────────────────────────────────────────────

def _sm2_update(card: dict, quality: int) -> dict:
    """
    SM-2 update. quality: 0-5 (0=blackout, 5=perfect).
    Returns updated card with next review interval.
    """
    if quality < 3:
        card["repetitions"] = 0
        card["interval"]    = 1
    else:
        if card["repetitions"] == 0:
            card["interval"] = 1
        elif card["repetitions"] == 1:
            card["interval"] = 6
        else:
            card["interval"] = round(card["interval"] * card["easiness"])
        card["repetitions"] += 1

    card["easiness"] = max(
        1.3,
        card["easiness"] + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    )
    card["next_review"] = time.time() + card["interval"] * 86400  # seconds
    card["last_quality"] = quality
    return card


def _new_card(developer_id: str, question_id: str) -> dict:
    return {
        "developer_id": developer_id,
        "question_id":  question_id,
        "repetitions":  0,
        "interval":     1,
        "easiness":     2.5,
        "next_review":  time.time(),
        "last_quality": None,
    }


class SM2UpdateRequest(BaseModel):
    developer_id: str
    question_id:  str
    correct:      bool
    time_seconds: float


class StreakCheckRequest(BaseModel):
    developer_id: str
    name:         str = "Developer"


@router.post("/quiz/schedule")
async def schedule_question(req: SM2UpdateRequest):
    """
    Update SM-2 card after quiz answer.
    Returns next review time and interval.
    """
    card_key = f"{req.developer_id}:{req.question_id}"

    if card_key not in _sm2_cards:
        _sm2_cards[card_key] = _new_card(req.developer_id, req.question_id)

    # Convert correct/incorrect to SM-2 quality score
    if req.correct and req.time_seconds <= 15:
        quality = 5   # perfect + fast
    elif req.correct:
        quality = 4   # correct
    else:
        quality = 1   # incorrect

    card = _sm2_update(_sm2_cards[card_key], quality)

    return {
        "next_review_in_days": card["interval"],
        "next_review_at":      card["next_review"],
        "easiness":            round(card["easiness"], 2),
        "repetitions":         card["repetitions"],
    }


@router.get("/quiz/due/{developer_id}")
async def get_due_questions(developer_id: str):
    """Return question IDs due for review today."""
    now = time.time()
    due = [
        card["question_id"]
        for key, card in _sm2_cards.items()
        if key.startswith(f"{developer_id}:")
        and card["next_review"] <= now
    ]
    return {"due_count": len(due), "due_question_ids": due}


# ── Streak Tracking ────────────────────────────────────────────────────────

@router.post("/streak/check")
async def check_streak(req: StreakCheckRequest):
    """Call once per day when developer answers a quiz. Updates streak."""
    dev_id = req.developer_id
    today  = int(time.time() // 86400)  # day number

    if dev_id not in _streaks:
        _streaks[dev_id] = {"streak_days": 0, "last_day": None, "longest": 0}

    s = _streaks[dev_id]

    if s["last_day"] == today:
        # Already checked today
        pass
    elif s["last_day"] == today - 1:
        # Consecutive day
        s["streak_days"] += 1
        s["longest"] = max(s["longest"], s["streak_days"])
    else:
        # Streak broken
        s["streak_days"] = 1

    s["last_day"] = today
    badge_unlocked = None

    if s["streak_days"] >= 30:
        badge_unlocked = "30-Day Streak"
        _push_badge_event(dev_id, req.name, "30-Day Streak")

    return {
        "streak_days":    s["streak_days"],
        "longest_streak": s["longest"],
        "badge_unlocked": badge_unlocked,
    }


# ── Badge Events ───────────────────────────────────────────────────────────

def _push_badge_event(developer_id: str, name: str, badge: str):
    """Push badge unlock event to queue for frontend SSE pickup."""
    event = {
        "type":         "badge_unlocked",
        "developer_id": developer_id,
        "name":         name,
        "badge":        badge,
        "icon":         BADGE_DEFINITIONS.get(badge, {}).get("icon", "🏅"),
        "desc":         BADGE_DEFINITIONS.get(badge, {}).get("desc", ""),
        "timestamp":    time.time(),
    }
    _badge_events.append(event)
    if len(_badge_events) > 100:
        _badge_events.pop(0)


def push_badge(developer_id: str, name: str, badge: str):
    """External call — used by leaderboard and quiz answer routes."""
    _push_badge_event(developer_id, name, badge)


@router.get("/badges/events")
async def get_badge_events(since: float = 0):
    """Frontend polls this to get new badge unlock events."""
    new_events = [e for e in _badge_events if e["timestamp"] > since]
    return {
        "events":    new_events,
        "count":     len(new_events),
        "timestamp": time.time(),
    }


@router.get("/badges/all")
async def get_all_badges():
    """Return all badge definitions for frontend display."""
    return [
        {"name": name, **info}
        for name, info in BADGE_DEFINITIONS.items()
    ]
