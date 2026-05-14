"""
chatbot/routers/chat.py
POST /chat  →  SSE stream of tokens
Fixes:
  - session_id query param (multi-session support)
  - xp_awarded=0 transmitted correctly (is not None check)
  - CORS headers for browser EventSource
"""
import httpx
import json
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from chatbot.models.chat_models import ChatRequest, Persona
from chatbot.context_assembler import assemble_system_prompt
from chatbot.intent_detector import detect_intent, Intent
from chatbot.dispute_handler import evaluate_dispute
from chatbot.predictive_warning import check_predictive_warning
from chatbot.plain_english import restate_plain
from chatbot.session_history import get_session, clear_session
from core.config import settings

router = APIRouter()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Access-Control-Allow-Origin": "*",
}


@router.post("/chat")
async def chat(
    req: ChatRequest,
    session_id: str = Query(default="default"),
):
    session = get_session(session_id)
    intent = detect_intent(req.message)

    # ── PLAIN ENGLISH ────────────────────────────────────────────────────
    if intent == Intent.PLAIN_ENGLISH:
        plain = await restate_plain(req.message)
        session.add("user", req.message)
        session.add("assistant", plain)
        return _sse_single(plain, intent="plain_english", xp_awarded=10)

    # ── DISPUTE FLOW ─────────────────────────────────────────────────────
    if intent == Intent.DISPUTE or req.dispute_finding_id:
        target = _find_by_id(req.session_context.findings, req.dispute_finding_id)
        if target:
            result = await evaluate_dispute(
                finding=target,
                user_argument=req.message,
                session_context_summary=_summarize_context(req.session_context),
            )
            reply = _format_dispute_reply(result)
            session.add("user", req.message)
            session.add("assistant", reply)
            # FIX: use is not None so xp=0 is transmitted
            xp = result.get("xp_awarded")
            xp = xp if xp is not None else 0
            return _sse_single(reply, intent="dispute", dispute_result=result, xp_awarded=xp)

    # ── PREDICTIVE WARNING CHECK ──────────────────────────────────────────
    predictive_warning = None
    for finding in req.session_context.findings:
        w = check_predictive_warning(finding.message)
        if w:
            predictive_warning = w
            break

    # ── STANDARD PERSONA CHAT (SSE STREAM) ───────────────────────────────
    system_prompt = assemble_system_prompt(
        context=req.session_context,
        persona=req.persona,
        mode=req.mode,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        *session.to_groq_messages(),
        {"role": "user", "content": req.message},
    ]
    session.add("user", req.message, persona=req.persona)

    return StreamingResponse(
        _stream_groq(messages, session, req.persona, predictive_warning, intent),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.delete("/session/{session_id}")
async def reset_session(session_id: str = "default"):
    clear_session(session_id)
    return {"cleared": session_id}


async def _stream_groq(messages, session, persona, predictive_warning, intent):
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.groq_model,
        "max_tokens": settings.groq_max_tokens,
        "stream": True,
        "messages": messages,
        "temperature": 0.4,
    }

    full_reply = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", GROQ_URL, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            token = json.loads(chunk)["choices"][0]["delta"].get("content", "")
                            if token:
                                full_reply.append(token)
                                yield f"data: {json.dumps({'token': token, 'type': 'token'})}\n\n"
                        except Exception:
                            continue

        complete = "".join(full_reply)
        session.add("assistant", complete, persona=persona)

        if predictive_warning:
            yield f"data: {json.dumps({'warning': predictive_warning, 'type': 'predictive_warning'})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'intent': intent.value if hasattr(intent, 'value') else intent})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


def _sse_single(reply: str, intent: str, dispute_result=None, xp_awarded=None):
    async def gen():
        payload = {"type": "complete", "reply": reply, "intent": intent}
        if dispute_result:
            payload["dispute_result"] = dispute_result
        # FIX: is not None so 0 transmits
        if xp_awarded is not None:
            payload["xp_awarded"] = xp_awarded
        yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


def _find_by_id(findings, finding_id):
    if not finding_id:
        return findings[-1] if findings else None
    return next((f for f in findings if f.finding_id == finding_id), None)


def _summarize_context(ctx) -> str:
    s = f"Findings: {len(ctx.findings)}. "
    if ctx.findings:
        s += f"Most severe: {ctx.findings[0].severity} — {ctx.findings[0].message[:100]}. "
    if ctx.code_diff:
        s += f"Code diff present ({len(ctx.code_diff)} chars)."
    return s


def _format_dispute_reply(result: dict) -> str:
    verdict = result.get("verdict", "confirmed")
    explanation = result.get("explanation", "")
    xp = result.get("xp_awarded", 0)
    if verdict == "retracted":
        return f"✓ Finding retracted. {explanation}\n\n+{xp} XP awarded for valid dispute."
    return f"Finding confirmed. {explanation}"
