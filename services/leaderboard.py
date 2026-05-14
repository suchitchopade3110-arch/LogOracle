"""
services/leaderboard.py
Team leaderboard — XP, badges, streaks.
GET  /leaderboard
POST /leaderboard/update
GET  /leaderboard/export/csv
"""
import csv
import io
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# In-memory leaderboard — resets on server restart (stateless MVP)
_leaderboard: dict = {}  # developer_id → entry

BADGE_THRESHOLDS = {
    "Bug Slayer":        lambda e: e["bugs_resolved"] >= 10,
    "Speed Fixer":       lambda e: e.get("fast_heals", 0) >= 1,
    "Quiz Master":       lambda e: e.get("quiz_streak", 0) >= 10,
    "Security Expert":   lambda e: e.get("security_score", 0) >= 85,
    "Code Legend":       lambda e: e["xp_total"] >= 1000,
    "Dispute Champion":  lambda e: e.get("disputes_won", 0) >= 5,
}


def _compute_badges(entry: dict) -> List[str]:
    return [name for name, check in BADGE_THRESHOLDS.items() if check(entry)]


def _default_entry(developer_id: str, name: str) -> dict:
    return {
        "developer_id":   developer_id,
        "name":           name,
        "xp_total":       0,
        "xp_this_week":   0,
        "bugs_resolved":  0,
        "disputes_won":   0,
        "quiz_streak":    0,
        "fast_heals":     0,
        "security_score": 0,
        "badges":         [],
        "streak_days":    0,
        "last_active":    time.time(),
        "opted_out":      False,
    }


class LeaderboardUpdateRequest(BaseModel):
    developer_id: str
    name: str = "Anonymous"
    xp_delta: int = 0
    action: str = ""   # correct_quiz | self_heal | dispute_won | bug_resolved
    opt_out: Optional[bool] = None


@router.post("/leaderboard/update")
async def update_leaderboard(req: LeaderboardUpdateRequest):
    """Called after XP events — quiz answer, self-heal approve, dispute retracted."""
    if req.developer_id not in _leaderboard:
        _leaderboard[req.developer_id] = _default_entry(req.developer_id, req.name)

    entry = _leaderboard[req.developer_id]
    entry["name"]         = req.name
    entry["xp_total"]     += req.xp_delta
    entry["xp_this_week"] += req.xp_delta
    entry["last_active"]   = time.time()

    if req.opt_out is not None:
        entry["opted_out"] = req.opt_out

    # Track action-specific counters
    if req.action == "bug_resolved":    entry["bugs_resolved"] += 1
    if req.action == "dispute_won":     entry["disputes_won"]  += 1
    if req.action == "self_heal":       entry["fast_heals"]    += 1
    if req.action == "correct_quiz":    entry["quiz_streak"]   += 1
    else:                               entry["quiz_streak"]    = 0  # reset streak on wrong

    # Recompute badges
    entry["badges"] = _compute_badges(entry)

    return {"xp_total": entry["xp_total"], "badges": entry["badges"]}


@router.get("/leaderboard")
async def get_leaderboard():
    """
    Return sorted leaderboard. Privacy: opted-out users shown as 'Anonymous'.
    Frontend polls this every 60s.
    """
    entries = []
    for entry in _leaderboard.values():
        display = dict(entry)
        if entry["opted_out"]:
            display["name"] = "Anonymous"
            display["developer_id"] = "***"
        entries.append(display)

    entries.sort(key=lambda e: -e["xp_total"])

    return {
        "leaderboard":  entries,
        "total_players": len(entries),
        "refreshed_at":  time.time(),
        "refresh_every": 60,
    }


@router.get("/leaderboard/export/csv")
async def export_leaderboard_csv():
    """CSV export for team review."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "rank", "name", "xp_total", "xp_this_week",
        "bugs_resolved", "disputes_won", "streak_days", "badges"
    ])
    writer.writeheader()

    sorted_entries = sorted(_leaderboard.values(), key=lambda e: -e["xp_total"])
    for i, entry in enumerate(sorted_entries, 1):
        if not entry["opted_out"]:
            writer.writerow({
                "rank":         i,
                "name":         entry["name"],
                "xp_total":     entry["xp_total"],
                "xp_this_week": entry["xp_this_week"],
                "bugs_resolved":entry["bugs_resolved"],
                "disputes_won": entry["disputes_won"],
                "streak_days":  entry["streak_days"],
                "badges":       "|".join(entry["badges"]),
            })

    return Response(
        content=output.getvalue().encode(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=logoracle-leaderboard.csv"}
    )
