# chatbot/plain_english.py
"""
Plain English mode: restate any technical finding/message
in jargon-free language a non-developer can understand.
Triggered by: global mode toggle OR user asking 'explain simply'.
"""
from llm.groq_client import groq_complete

PLAIN_PROMPT = """
Rewrite the following technical finding in plain English for a non-technical business owner.

Rules:
- No jargon, acronyms, or command syntax
- Explain what went wrong, why it matters, and what to do — in that order
- Maximum 3 short sentences
- Write as if explaining to someone who has never seen a terminal
- Do NOT include any technical commands

TECHNICAL FINDING:
{finding}

Plain English version:
"""

async def restate_plain(technical_text: str) -> str:
    """
    Call GROQ to restate technical text in plain English.
    Returns plain-English string.
    """
    prompt = PLAIN_PROMPT.format(finding=technical_text[:2000])

    try:
        return (await groq_complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )).strip()
    except Exception:
        # Fallback: strip known technical patterns manually
        return _basic_simplify(technical_text)


def _basic_simplify(text: str) -> str:
    """Minimal fallback if GROQ call fails."""
    replacements = {
        "OOM killer": "memory manager",
        "nginx": "web server",
        "sshd": "login service",
        "kernel panic": "system crash",
        "CVE": "known security flaw",
        "brute-force": "repeated login attack",
        "SQL injection": "database attack",
        "segmentation fault": "program crash",
    }
    simplified = text
    for tech, plain in replacements.items():
        simplified = simplified.replace(tech, plain)
    return simplified
