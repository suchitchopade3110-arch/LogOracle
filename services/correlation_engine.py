"""
services/correlation_engine.py
Cross-agent causal chain builder.
Aligns findings by timestamp, builds directed causal graph, identifies root cause.
POST /analyze/correlate
"""
import re
import json
import time
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter()


class CorrelateRequest(BaseModel):
    findings: List[dict]          # from multiple agents
    log_text: str = ""            # raw log for timestamp extraction
    window_seconds: int = 300     # 5-min correlation window


class CausalNode:
    def __init__(self, finding: dict, ts: float):
        self.finding  = finding
        self.ts       = ts
        self.causes: List["CausalNode"] = []


# Known causal patterns — (trigger pattern, effect pattern, relationship)
CAUSAL_RULES = [
    # SSH brute-force → OOM → service crash
    (r"brute.?force|failed password",    r"out of memory|OOM|killed process",      "caused memory pressure via"),
    (r"out of memory|OOM|killed process", r"502|503|connection refused|nginx.*down", "caused service failure via"),
    (r"brute.?force|failed password",    r"sshd.*child|sshd.*process",              "spawned excessive processes via"),
    # Log4Shell → RCE
    (r"jndi:ldap|log4j|log4shell",       r"command.*executed|shell.*spawned|exec",  "enabled RCE via"),
    # Disk full → write failure
    (r"disk.*full|no space left",        r"write.*fail|cannot write|ENOSPC",        "caused write failure via"),
    # Redis leak → OOM
    (r"redis.*connect|connection.*pool", r"out of memory|memory.*spike",            "caused memory leak via"),
    # Retry storm → latency
    (r"retry|timeout.*upstream",        r"latency.*spike|response.*time|503",       "caused cascading failure via"),
]

# Severity weights for root cause scoring
SEV_WEIGHT = {"CRITICAL": 3, "HIGH": 2, "WARNING": 1, "INFO": 0}


def _extract_timestamp(finding: dict, log_text: str) -> float:
    """Best-effort timestamp extraction from finding or log context."""
    # Try explicit timestamp field
    ts = finding.get("timestamp")
    if ts:
        try:
            return float(ts)
        except (ValueError, TypeError):
            pass

    # Try to parse time from message
    msg = finding.get("message", "")
    patterns = [
        r"(\d{2}:\d{2}:\d{2})",
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
    ]
    for pat in patterns:
        m = re.search(pat, msg)
        if m:
            # Return relative offset — just use position in log for ordering
            return float(log_text.find(m.group(0))) / max(len(log_text), 1)

    # Fallback: use severity as ordering proxy
    return float(SEV_WEIGHT.get(finding.get("severity", "INFO"), 0))


def _find_causes(trigger: dict, effects: List[dict]) -> List[dict]:
    """Match trigger finding to effect findings using causal rules."""
    trigger_msg = (trigger.get("message", "") + " " + trigger.get("agent", "")).lower()
    causes = []
    for rule_trigger, rule_effect, relationship in CAUSAL_RULES:
        if re.search(rule_trigger, trigger_msg, re.IGNORECASE):
            for effect in effects:
                effect_msg = effect.get("message", "").lower()
                if re.search(rule_effect, effect_msg, re.IGNORECASE):
                    causes.append({
                        "from":         trigger.get("message", "")[:80],
                        "to":           effect.get("message", "")[:80],
                        "relationship": relationship,
                        "from_agent":   trigger.get("agent", "unknown"),
                        "to_agent":     effect.get("agent", "unknown"),
                    })
    return causes


def build_causal_chain(findings: List[dict], log_text: str = "") -> dict:
    """
    Main correlation logic.
    Returns: root_cause, chain (ordered events), edges (for ReactFlow), confidence.
    """
    if not findings:
        return {"root_cause": None, "chain": [], "edges": [], "confidence": 0.0}

    # Score each finding as potential root cause
    scored = []
    for f in findings:
        score = SEV_WEIGHT.get(f.get("severity", "INFO"), 0)
        ts    = _extract_timestamp(f, log_text)
        # Earlier + more severe = more likely root cause
        scored.append((score - ts * 0.01, f, ts))

    scored.sort(key=lambda x: -x[0])
    root_candidate = scored[0][1]

    # Build causal chain
    all_edges: List[dict] = []
    other_findings = [f for f in findings if f is not root_candidate]

    for finding in findings:
        edges = _find_causes(finding, other_findings)
        all_edges.extend(edges)

    # Build ordered chain (root → effects)
    chain = [{"agent": f.get("agent","?"), "severity": f.get("severity","?"),
               "message": f.get("message","")[:100], "timestamp": ts}
             for _, f, ts in sorted(scored, key=lambda x: x[2])]

    # ReactFlow nodes + edges
    nodes = [{"id": f"n{i}", "data": {"label": f"{f['agent'].upper()}: {f['message'][:60]}"},
               "position": {"x": 100, "y": i * 80},
               "style": {"background": "#FF3B5C" if f["severity"]=="CRITICAL" else
                          "#FF6B35" if f["severity"]=="WARNING" else "#4D9FFF"}}
             for i, f in enumerate(chain)]

    edges = [{"id": f"e{i}", "source": f"n{e['from'][:10]}", "target": f"n{e['to'][:10]}",
               "label": e["relationship"]}
             for i, e in enumerate(all_edges)]

    confidence = min(0.95, 0.6 + len(all_edges) * 0.1 + (scored[0][0] / 10))

    return {
        "root_cause": {
            "agent":      root_candidate.get("agent", "unknown"),
            "severity":   root_candidate.get("severity", "CRITICAL"),
            "message":    root_candidate.get("message", ""),
            "confidence": round(confidence, 2),
            "fix":        root_candidate.get("fix_linux") or root_candidate.get("fix", ""),
        },
        "chain":      chain,
        "causal_edges": all_edges,
        "nodes":      nodes,     # ReactFlow nodes
        "edges":      edges,     # ReactFlow edges
        "confidence": round(confidence, 2),
    }


@router.post("/analyze/correlate")
async def correlate(req: CorrelateRequest):
    """
    Multi-agent correlation endpoint.
    Pass findings from multiple /analyze/log calls + any code findings.
    Returns root cause chain ready for ReactFlow.
    """
    result = build_causal_chain(req.findings, req.log_text)
    return result
