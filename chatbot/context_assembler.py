# chatbot/context_assembler.py
import json
from chatbot.models.chat_models import SessionContext, Persona
from chatbot.persona import get_persona_prompt, get_persona_label
from services.redis_sessions import SessionHistory

LOG_LINE_LIMIT   = 500    # last N log lines injected
CODE_TOKEN_LIMIT = 8000   # approximate — truncate diff if over

def assemble_system_prompt(
    context: SessionContext,
    persona: Persona,
    mode: str = "tech"
) -> str:
    """
    Build the full system prompt injected into every GROQ call.
    Structure:
      1. Persona instructions
      2. Current session findings (all agents)
      3. Last 500 log lines
      4. Code diff (up to 8000 tokens)
      5. Developer profile
      6. Mode instruction (plain/tech)
    """
    persona_block = get_persona_prompt(persona)

    findings_block = _format_findings(context.findings)
    log_block      = _format_logs(context.last_log_lines)
    code_block     = _format_code(context.code_diff)
    profile_block  = _format_profile(context.developer_profile)
    mode_block     = _format_mode(mode)

    return f"""
{persona_block}

--- SESSION FINDINGS ---
{findings_block}

--- RECENT LOG LINES (last {LOG_LINE_LIMIT} lines) ---
{log_block}

--- CURRENT CODE / DIFF ---
{code_block}

--- DEVELOPER PROFILE ---
{profile_block}

--- OUTPUT MODE ---
{mode_block}
""".strip()


def _format_findings(findings) -> str:
    if not findings:
        return "No findings yet."
    lines = []
    for f in findings:
        line = f"[{f.agent.upper()}] [{f.severity}] {f.message} (confidence: {f.confidence:.0%})"
        if f.fix:
            line += f"\n  Fix: {f.fix}"
        if f.cwe_id:
            line += f"  CWE: {f.cwe_id}"
        lines.append(line)
    return "\n".join(lines)


def _format_logs(log_lines: str) -> str:
    if not log_lines.strip():
        return "No log data in session."
    lines = log_lines.splitlines()
    # Take last LOG_LINE_LIMIT lines
    truncated = lines[-LOG_LINE_LIMIT:]
    if len(lines) > LOG_LINE_LIMIT:
        return f"[truncated to last {LOG_LINE_LIMIT} lines]\n" + "\n".join(truncated)
    return "\n".join(truncated)


def _format_code(code_diff: str) -> str:
    if not code_diff.strip():
        return "No code or diff in session."
    # Rough token estimate: 4 chars ≈ 1 token
    char_limit = CODE_TOKEN_LIMIT * 4
    if len(code_diff) > char_limit:
        return code_diff[:char_limit] + "\n[... truncated at 8000 token limit ...]"
    return code_diff


def _format_profile(profile) -> str:
    return (
        f"Expertise level: {profile.expertise_level}\n"
        f"Quiz accuracy: {_avg(profile.past_quiz_scores):.0%}\n"
        f"Badges earned: {', '.join(profile.badges) if profile.badges else 'none'}"
    )


def _format_mode(mode: str) -> str:
    if mode == "plain":
        return (
            "PLAIN ENGLISH MODE ACTIVE. "
            "Rewrite ALL technical terms in simple language. "
            "No jargon, no command syntax, no acronyms without explanation. "
            "Write as if explaining to a non-technical business owner."
        )
    return (
        "TECHNICAL MODE. "
        "Use precise technical language. Include process names, signal codes, "
        "kernel calls, CWE tags, and exact commands where relevant."
    )


def _avg(scores: list) -> float:
    return sum(scores) / len(scores) if scores else 0.0
