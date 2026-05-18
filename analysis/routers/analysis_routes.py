"""
analysis/routers/analysis_routes.py
Mount in Suchit's main.py:
    from analysis.routers.analysis_routes import router as analysis_router
    app.include_router(analysis_router)

Endpoints:
    POST /analyze/log           — full log parse pipeline
    POST /analyze/code          — Pass 1 (AST) + Pass 3 (OWASP)
    POST /analyze/hallucination — registry validation
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from analysis.log_parser.log_parser_core import parse_log
from analysis.log_parser.pii_redactor import redact_pii
from analysis.platform.fix_commands import get_fix
from analysis.security_agent import detect_brute_force, match_cves, should_popup, format_popup_message
from analysis.hallucination_agent import check_imports, build_trust_layer
from analysis.ast_engine import run_ast_pass, run_owasp_pass
from analysis.models.analysis_models import ParsedLog
from services.session_utils import (
    chunk_log_text,
    chunk_summary,
    detect_pii_presence,
    translate_finding,
)

router = APIRouter()


class LogRequest(BaseModel):
    log_text: str
    mode: str = "plain"
    redact_pii: bool = True
    session_id: str = "default"

class CodeRequest(BaseModel):
    code: str
    language: str
    ast_issues_from_pass2: List[dict] = []

class HallucinationRequest(BaseModel):
    code: str
    language: str
    filename: Optional[str] = None


@router.post("/analyze/log")
async def analyze_log(req: LogRequest):
    pii_info = detect_pii_presence(req.log_text)
    chunks = chunk_log_text(req.log_text)
    chunk_info = chunk_summary(chunks)
    log_text_to_parse = req.log_text if len(chunks) == 1 else chunks[0]

    # Keep raw IPs available for security detection and fix-command templating.
    # Redaction is applied only to response event payloads below.
    parsed: ParsedLog = await parse_log(log_text_to_parse, redact=False)

    brute = detect_brute_force(parsed.events)
    cves  = match_cves(req.log_text, parsed.platform)

    security_findings = []
    if brute:
        security_findings.append(brute)
    security_findings.extend(cves)

    popups = []
    corroborated = len(security_findings) > 1
    for finding in security_findings:
        if should_popup(finding, corroborated):
            popups.append(format_popup_message(finding, parsed.platform))

    # Bug 4 fix: pass source_ip into template_vars
    fixes = []
    for finding in security_findings:
        fix_type = _finding_to_fix_type(finding)
        if fix_type:
            ip = finding.get("source_ip", "UNKNOWN_IP")
            fix = get_fix(fix_type, parsed.platform, parsed.distro,
                          template_vars={"ip": ip})
            if fix:
                fixes.append(fix.model_dump())

    from services.agent_stream import update_agent_state
    update_agent_state(
        "security",
        "active",
        security_findings,
        security_findings[0]["message"] if security_findings else None,
    )
    update_agent_state(
        "log",
        "active",
        [],
        f"Parsed {len(parsed.events)} events ({parsed.platform})",
    )

    return {
        "platform":          parsed.platform,
        "distro":            parsed.distro,
        "format_detected":    parsed.format_detected,
        "event_count":        len(parsed.events),
        "pii_redacted":       req.redact_pii,
        "pii_detected":       pii_info["pii_detected"],
        "pii_banner":         pii_info["banner_message"],
        "chunk_count":        chunk_info["chunk_count"],
        "chunked":            chunk_info["chunked"],
        "total_lines":        chunk_info["total_lines"],
        "mode":               req.mode,
        "events":             [_event_payload(e, req.redact_pii) for e in parsed.events[:100]],
        "security_findings":  [translate_finding(f, req.mode) for f in security_findings],
        "popups":             popups,
        "fixes":              fixes,
    }


@router.post("/analyze/code")
async def analyze_code(req: CodeRequest):
    pass1 = await run_ast_pass(req.code, req.language)
    pass3 = await run_owasp_pass(req.code, req.language)

    all_issues = [i.model_dump() for i in pass1 + pass3]
    all_issues.sort(key=lambda x: ["CRITICAL","HIGH","MEDIUM","LOW","INFO"].index(x["severity"]))

    return {
        "pass1_count": len(pass1),
        "pass3_count": len(pass3),
        "issues":      all_issues,
    }


@router.post("/analyze/hallucination")
async def analyze_hallucination(req: HallucinationRequest):
    items  = await check_imports(req.code, req.language)
    result = build_trust_layer(items, req.filename)
    return result.model_dump()


def _finding_to_fix_type(finding: dict) -> Optional[str]:
    msg = finding.get("message", "").lower()
    if "ssh" in msg or "brute" in msg:
        return "block_ip"
    if "rdp" in msg:
        return "mitigate_rdp_bruteforce"
    if "disk" in msg or ("log" in msg and "full" in msg):
        return "clean_logs"
    return None


def _event_payload(event, redact: bool) -> dict:
    payload = event.model_dump()
    if redact:
        payload["raw"] = redact_pii(payload.get("raw", ""))
        payload["message"] = redact_pii(payload.get("message", ""))
    return payload
