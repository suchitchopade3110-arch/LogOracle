# chatbot/dispute_handler.py
"""
Dispute flow:
  User disputes a finding -> re-evaluate with additional context
  -> verdict: retracted | confirmed
  -> if retracted: +60 XP awarded (per PRD)
"""
from chatbot.models.chat_models import Finding
from llm.groq_client import groq_json

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

    result = await groq_json(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.2,
    )

    if "verdict" not in result:
        result = _fallback_verdict()

    # XP: +60 if retracted (per PRD spec)
    result["xp_awarded"] = 60 if result["verdict"] == "retracted" else 0
    return result


def _fallback_verdict() -> dict:
    return {
        "verdict": "confirmed",
        "new_severity": "MEDIUM",
        "new_confidence": 0.5,
        "explanation": "Could not re-evaluate. Original finding stands.",
    }
