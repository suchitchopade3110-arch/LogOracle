# chatbot/dispute_handler.py
"""
Dispute flow:
  User disputes a finding → re-evaluate with additional context
  → verdict: retracted | confirmed
  → if retracted: +60 XP awarded (per PRD)
"""
import httpx
import json
from chatbot.models.chat_models import Finding
from core.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

DISPUTE_PROMPT = """
A developer is disputing the following finding from LogOracle's analysis system.

ORIGINAL FINDING:
Agent: {agent}
Severity: {severity}
Message: {message}
Confidence: {confidence}
Suggested Fix: {fix}

DEVELOPER'S ARGUMENT:
{user_argument}

ADDITIONAL CONTEXT FROM SESSION:
{session_context}

Your job: Re-evaluate this finding fairly given the developer's argument and context.
Respond ONLY in JSON with this exact structure:
{{
  "verdict": "retracted" | "confirmed",
  "new_severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO",
  "new_confidence": 0.0-1.0,
  "explanation": "one paragraph explaining your verdict"
}}

Be honest. If the developer makes a valid point, retract. If the finding is correct, confirm.
Do not capitulate just because the developer is assertive — only retract on valid technical grounds.
"""

async def evaluate_dispute(
    finding: Finding,
    user_argument: str,
    session_context_summary: str
) -> dict:
    """
    Re-evaluate a disputed finding via GROQ.
    Returns: { verdict, new_severity, new_confidence, explanation, xp_awarded }
    """
    prompt = DISPUTE_PROMPT.format(
        agent=finding.agent,
        severity=finding.severity,
        message=finding.message,
        confidence=finding.confidence,
        fix=finding.fix or "none",
        user_argument=user_argument,
        session_context=session_context_summary[:1000],  # cap context size
    )

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.groq_model,
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,   # low temp → more consistent verdicts
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(GROQ_URL, headers=headers, json=payload)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]

    result = _parse_verdict(raw)

    # XP: +60 if retracted (per PRD spec)
    result["xp_awarded"] = 60 if result["verdict"] == "retracted" else 0
    return result


def _parse_verdict(raw: str) -> dict:
    """Parse GROQ JSON response. Fallback to confirmed on parse error."""
    try:
        clean = raw.strip().lstrip("```json").rstrip("```").strip()
        return json.loads(clean)
    except Exception:
        return {
            "verdict": "confirmed",
            "new_severity": "MEDIUM",
            "new_confidence": 0.5,
            "explanation": "Could not re-evaluate. Original finding stands."
        }
