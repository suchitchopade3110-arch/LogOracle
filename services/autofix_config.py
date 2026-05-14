"""
services/autofix_config.py
Exposes confidence gate as configurable endpoint.
GET  /analyze/fix/config      — get current gate settings
POST /analyze/fix/config      — update gate settings
Also patches /analyze/fix to accept confidence_threshold param.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Mutable config — can be changed via API during demo
_config = {
    "confidence_threshold": 0.70,   # minimum confidence to auto-apply fix
    "max_lines_context":    50,      # lines of context sent to LLM for fix
    "dry_run":              True,    # True = suggest only, never auto-apply
    "require_approval":     True,    # True = always show approve button
}


class FixConfigUpdate(BaseModel):
    confidence_threshold: Optional[float] = None
    max_lines_context:    Optional[int]   = None
    dry_run:              Optional[bool]  = None
    require_approval:     Optional[bool]  = None


@router.get("/analyze/fix/config")
async def get_fix_config():
    """Return current auto-fix gate configuration."""
    return {
        "config": _config,
        "description": {
            "confidence_threshold": "Minimum confidence (0-1) required to suggest auto-fix. Below = suggestion only.",
            "max_lines_context":    "Lines of code context sent to LLM when generating fix.",
            "dry_run":              "If true, fix is always shown as suggestion, never auto-applied.",
            "require_approval":     "If true, always show Approve button before applying fix.",
        }
    }


@router.post("/analyze/fix/config")
async def update_fix_config(req: FixConfigUpdate):
    """Update auto-fix gate settings. Useful for demo adjustments."""
    if req.confidence_threshold is not None:
        _config["confidence_threshold"] = max(0.0, min(1.0, req.confidence_threshold))
    if req.max_lines_context is not None:
        _config["max_lines_context"] = max(10, min(200, req.max_lines_context))
    if req.dry_run is not None:
        _config["dry_run"] = req.dry_run
    if req.require_approval is not None:
        _config["require_approval"] = req.require_approval
    return {"updated": _config}


def get_confidence_threshold() -> float:
    return _config["confidence_threshold"]


def is_dry_run() -> bool:
    return _config["dry_run"]
