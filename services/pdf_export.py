"""
services/pdf_export.py
WeasyPrint PDF debug report generator.
POST /export/pdf
"""
import json
import time
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class PDFExportRequest(BaseModel):
    session_id: str = "session"
    findings: List[dict] = []
    fixes: List[dict] = []
    root_cause: Optional[dict] = None
    platform: str = "unknown"
    distro: Optional[str] = None
    log_snippet: str = ""
    code_issues: List[dict] = []


def generate_pdf(session_data: dict) -> bytes:
    """Compatibility helper for the older /export/pdf router."""
    root_cause = session_data.get("root_cause")
    if root_cause is None and session_data.get("root_cause_chain"):
        root_cause = session_data["root_cause_chain"][0]

    req = PDFExportRequest(
        session_id=session_data.get("session_id", "session"),
        findings=session_data.get("findings", []),
        fixes=session_data.get("fixes", []),
        root_cause=root_cause,
        platform=session_data.get("platform", "unknown"),
        distro=session_data.get("distro"),
        log_snippet=session_data.get("log_snippet", ""),
        code_issues=session_data.get("code_issues", []),
    )
    html = _build_html(req)
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except Exception:
        return html.encode()


def _severity_color(severity: str) -> str:
    return {"CRITICAL": "#FF3B5C", "HIGH": "#FF6B35",
            "WARNING": "#FF6B35", "MEDIUM": "#FACC15",
            "INFO": "#4D9FFF"}.get(severity, "#6B7594")


def _build_html(req: PDFExportRequest) -> str:
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    findings_html = ""
    for f in req.findings:
        color = _severity_color(f.get("severity", "INFO"))
        findings_html += f"""
        <div class="finding">
          <div class="finding-header" style="border-left: 4px solid {color}; padding-left: 8px;">
            <span class="badge" style="background:{color};">{f.get('severity','?')}</span>
            <strong>{f.get('agent','?').upper()}</strong>
            <span class="confidence">{int(f.get('confidence',0)*100)}% confidence</span>
          </div>
          <p class="finding-msg">{f.get('message','')}</p>
          {f'<code class="fix">{f["fix_linux"]}</code>' if f.get("fix_linux") else ""}
          {f'<p class="cve">CVE: <a href="https://nvd.nist.gov/vuln/detail/{f["cve_id"]}">{f["cve_id"]}</a></p>' if f.get("cve_id") else ""}
        </div>"""

    code_html = ""
    for issue in req.code_issues:
        color = _severity_color(issue.get("severity", "INFO"))
        code_html += f"""
        <div class="code-issue">
          <span class="badge" style="background:{color};">{issue.get('severity','?')}</span>
          Line {issue.get('line','?')} — {issue.get('message','')}
          {f'<span class="cwe">{issue["cwe_id"]}</span>' if issue.get("cwe_id") else ""}
        </div>"""

    root_cause_html = ""
    if req.root_cause:
        rc = req.root_cause
        root_cause_html = f"""
        <div class="root-cause-box">
          <h3>Root Cause</h3>
          <p><strong>{rc.get('agent','?').upper()}</strong> — {rc.get('message','')}</p>
          <p>Confidence: {int(rc.get('confidence',0)*100)}%</p>
          {f'<code>{rc["fix"]}</code>' if rc.get("fix") else ""}
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'DejaVu Sans', sans-serif; font-size: 12px; color: #1a1a2e; background: #fff; }}
  .header {{ background: #0A0C10; color: #00E5FF; padding: 24px 32px; }}
  .header h1 {{ font-size: 28px; font-weight: 700; letter-spacing: -1px; }}
  .header .subtitle {{ color: #6B7594; font-size: 13px; margin-top: 4px; }}
  .meta {{ display: flex; gap: 32px; padding: 16px 32px; background: #F8F9FA; border-bottom: 1px solid #E0E0E0; }}
  .meta-item {{ display: flex; flex-direction: column; }}
  .meta-label {{ font-size: 10px; text-transform: uppercase; color: #6B7594; }}
  .meta-value {{ font-weight: 600; font-size: 13px; }}
  .section {{ padding: 20px 32px; border-bottom: 1px solid #E8E8E8; }}
  .section h2 {{ font-size: 16px; font-weight: 700; margin-bottom: 12px; color: #0A0C10; }}
  .finding {{ margin-bottom: 12px; padding: 10px; background: #FAFAFA; border-radius: 6px; border: 1px solid #E8E8E8; }}
  .finding-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
  .badge {{ color: white; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 3px; }}
  .confidence {{ margin-left: auto; color: #6B7594; font-size: 10px; }}
  .finding-msg {{ font-size: 12px; color: #333; line-height: 1.4; }}
  .fix {{ display: block; margin-top: 6px; background: #0A0C10; color: #00E5FF; padding: 6px 10px; border-radius: 4px; font-size: 11px; }}
  .cve {{ font-size: 10px; color: #FF3B5C; margin-top: 4px; }}
  .root-cause-box {{ background: #FFF0F3; border: 2px solid #FF3B5C; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
  .root-cause-box h3 {{ color: #FF3B5C; margin-bottom: 8px; }}
  .code-issue {{ display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #F0F0F0; font-size: 11px; }}
  .cwe {{ margin-left: auto; color: #6B7594; font-size: 10px; }}
  .footer {{ padding: 16px 32px; text-align: center; color: #6B7594; font-size: 10px; }}
  @page {{ margin: 0; }}
</style>
</head>
<body>
  <div class="header">
    <h1>LogOracle</h1>
    <div class="subtitle">Debug Session Report — {ts}</div>
  </div>

  <div class="meta">
    <div class="meta-item"><span class="meta-label">Platform</span><span class="meta-value">{req.platform}</span></div>
    <div class="meta-item"><span class="meta-label">Distro</span><span class="meta-value">{req.distro or 'unknown'}</span></div>
    <div class="meta-item"><span class="meta-label">Findings</span><span class="meta-value">{len(req.findings)}</span></div>
    <div class="meta-item"><span class="meta-label">Code Issues</span><span class="meta-value">{len(req.code_issues)}</span></div>
    <div class="meta-item"><span class="meta-label">Session</span><span class="meta-value">{req.session_id[:12]}</span></div>
  </div>

  {"<div class='section'>" + root_cause_html + "</div>" if root_cause_html else ""}

  {f'<div class="section"><h2>Security Findings ({len(req.findings)})</h2>{findings_html}</div>' if req.findings else ""}

  {f'<div class="section"><h2>Code Issues ({len(req.code_issues)})</h2>{code_html}</div>' if req.code_issues else ""}

  {f'<div class="section"><h2>Log Snippet</h2><pre style="font-size:10px;background:#F8F9FA;padding:12px;border-radius:4px;overflow:auto;">{req.log_snippet[:2000]}</pre></div>' if req.log_snippet else ""}

  <div class="footer">
    Generated by LogOracle · AI Antivirus for Code · {ts}
  </div>
</body>
</html>"""


@router.post("/export/pdf")
async def export_pdf(req: PDFExportRequest):
    """Generate PDF debug report. Returns PDF bytes."""
    html = _build_html(req)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=logoracle-report-{req.session_id[:8]}.pdf"}
        )
    except Exception as exc:
        # Fallback: return HTML if WeasyPrint is missing or native deps mismatch.
        return Response(
            content=html.encode(),
            media_type="text/html",
            headers={"X-PDF-Fallback": f"PDF generation unavailable: {exc}"}
        )


@router.get("/export/pdf/preview")
async def export_pdf_preview():
    """Return sample HTML preview of the PDF template."""
    sample = PDFExportRequest(
        session_id="demo_session",
        platform="linux", distro="ubuntu",
        findings=[{
            "agent": "security", "severity": "CRITICAL",
            "message": "SSH brute-force: 847 attempts from 203.0.113.42",
            "confidence": 0.94, "fix_linux": "sudo ufw deny from 203.0.113.42 && sudo ufw reload"
        }],
        root_cause={
            "agent": "security", "severity": "CRITICAL",
            "message": "SSH brute-force triggered OOM → nginx crash",
            "confidence": 0.94,
            "fix": "sudo ufw deny from 203.0.113.42 && sudo systemctl restart nginx"
        }
    )
    html = _build_html(sample)
    return Response(content=html.encode(), media_type="text/html")
