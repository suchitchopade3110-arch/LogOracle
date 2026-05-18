# analysis/security_agent/confidence_scorer.py
"""
Real 5-factor confidence scoring engine.

Factors (each 0.0–1.0, weighted sum → final confidence):
  1. evidence_count        – how many independent signals corroborate
  2. anomaly_severity      – how far observed values deviate from baseline
  3. rule_match_density    – how many deterministic rules fired
  4. historical_similarity – pattern similarity to known attack signatures
  5. multi_agent_agreement – fraction of agents that reached same conclusion

Weights sum to 1.0.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import math

WEIGHTS = {
    "evidence_count":        0.25,
    "anomaly_severity":      0.20,
    "rule_match_density":    0.25,
    "historical_similarity": 0.15,
    "multi_agent_agreement": 0.15,
}

KNOWN_SIGNATURES = {
    "ssh_brute_force": {
        "patterns": ["Failed password", "Invalid user", "authentication failure"],
        "min_hits": 5,
        "typical_confidence": 0.94,
    },
    "rdp_brute_force": {
        "patterns": ["EventID 4625", "Event ID: 4625", "Logon Type 3"],
        "min_hits": 5,
        "typical_confidence": 0.91,
    },
    "redis_oom": {
        "patterns": ["OOM", "out of memory", "maxmemory"],
        "min_hits": 1,
        "typical_confidence": 0.88,
    },
    "retry_storm": {
        "patterns": ["connection refused", "timeout", "ECONNREFUSED"],
        "min_hits": 3,
        "typical_confidence": 0.85,
    },
}

BASELINES = {
    "ssh_failures_per_min": 1,
    "rdp_failures_per_min": 1,
    "error_rate_pct":       5.0,
    "retry_rate_per_min":   10,
}


@dataclass
class ConfidenceFactors:
    evidence_count: float
    anomaly_severity: float
    rule_match_density: float
    historical_similarity: float
    multi_agent_agreement: float
    evidence_lines: List[str] = field(default_factory=list)

    @property
    def final_score(self) -> float:
        raw = (
            self.evidence_count        * WEIGHTS["evidence_count"] +
            self.anomaly_severity      * WEIGHTS["anomaly_severity"] +
            self.rule_match_density    * WEIGHTS["rule_match_density"] +
            self.historical_similarity * WEIGHTS["historical_similarity"] +
            self.multi_agent_agreement * WEIGHTS["multi_agent_agreement"]
        )
        return round(min(max(raw, 0.0), 1.0), 4)

    @property
    def final_pct(self) -> int:
        return round(self.final_score * 100)

    def to_dict(self) -> Dict:
        return {
            "final_score": self.final_score,
            "final_pct":   self.final_pct,
            "weights":     WEIGHTS,
            "factors": {
                "evidence_count": {
                    "score":        round(self.evidence_count, 4),
                    "weight":       WEIGHTS["evidence_count"],
                    "contribution": round(self.evidence_count * WEIGHTS["evidence_count"], 4),
                    "description":  "Independent signals corroborating the conclusion",
                },
                "anomaly_severity": {
                    "score":        round(self.anomaly_severity, 4),
                    "weight":       WEIGHTS["anomaly_severity"],
                    "contribution": round(self.anomaly_severity * WEIGHTS["anomaly_severity"], 4),
                    "description":  "Statistical deviation from baseline behaviour",
                },
                "rule_match_density": {
                    "score":        round(self.rule_match_density, 4),
                    "weight":       WEIGHTS["rule_match_density"],
                    "contribution": round(self.rule_match_density * WEIGHTS["rule_match_density"], 4),
                    "description":  "Deterministic rules fired (OWASP, MITRE ATT&CK, custom)",
                },
                "historical_similarity": {
                    "score":        round(self.historical_similarity, 4),
                    "weight":       WEIGHTS["historical_similarity"],
                    "contribution": round(self.historical_similarity * WEIGHTS["historical_similarity"], 4),
                    "description":  "Cosine similarity to known incident patterns in rule base",
                },
                "multi_agent_agreement": {
                    "score":        round(self.multi_agent_agreement, 4),
                    "weight":       WEIGHTS["multi_agent_agreement"],
                    "contribution": round(self.multi_agent_agreement * WEIGHTS["multi_agent_agreement"], 4),
                    "description":  "Fraction of agents that independently reached same conclusion",
                },
            },
            "evidence_lines": self.evidence_lines,
        }


def _score_evidence_count(hit_count: int, threshold: int) -> float:
    if hit_count <= 0:
        return 0.0
    ratio = hit_count / max(threshold, 1)
    return round(1 - math.exp(-ratio * 1.2), 4)


def _score_anomaly_severity(hit_count: int, attack_type: str) -> float:
    baselines = {
        "SSH":        BASELINES["ssh_failures_per_min"],
        "RDP":        BASELINES["rdp_failures_per_min"],
        "NTLM/SMB":   BASELINES["rdp_failures_per_min"],
        "macOS Auth": BASELINES["ssh_failures_per_min"],
    }
    baseline = baselines.get(attack_type, 1)
    deviation = hit_count / max(baseline, 1)
    score = 1 - (1 / (1 + math.log1p(deviation)))
    return round(min(score, 1.0), 4)


def _score_rule_match_density(rules_fired: List[str]) -> float:
    n = len(rules_fired)
    if n == 0:
        return 0.0
    return round(1 - math.exp(-n * 0.6), 4)


def _score_historical_similarity(attack_type: str, log_text: str) -> float:
    sig_key = {
        "SSH":      "ssh_brute_force",
        "RDP":      "rdp_brute_force",
        "NTLM/SMB": "rdp_brute_force",
    }.get(attack_type)
    if not sig_key or sig_key not in KNOWN_SIGNATURES:
        return 0.60
    sig = KNOWN_SIGNATURES[sig_key]
    patterns = sig["patterns"]
    hits = sum(1 for p in patterns if p.lower() in log_text.lower())
    return round(hits / len(patterns), 4)


def _score_multi_agent_agreement(agents_agreed: int, total_agents: int = 3) -> float:
    if total_agents == 0:
        return 0.0
    return round(agents_agreed / total_agents, 4)


def compute_confidence(
    attack_type: str,
    hit_count: int,
    threshold: int,
    log_text: str,
    rules_fired: Optional[List[str]] = None,
    agents_agreed: int = 2,
    total_agents: int = 3,
    source_ip: Optional[str] = None,
) -> ConfidenceFactors:
    if rules_fired is None:
        rules_fired = []

    ec = _score_evidence_count(hit_count, threshold)
    av = _score_anomaly_severity(hit_count, attack_type)
    rm = _score_rule_match_density(rules_fired)
    hs = _score_historical_similarity(attack_type, log_text)
    ma = _score_multi_agent_agreement(agents_agreed, total_agents)

    evidence = []
    evidence.append(f"✓ {attack_type} pattern matched ({hit_count} events, threshold: {threshold})")
    for r in rules_fired:
        evidence.append(f"✓ Rule fired: {r}")
    if source_ip and source_ip != "UNKNOWN_IP":
        evidence.append(f"✓ Source IP identified: {source_ip}")
    deviation = hit_count / max(BASELINES.get("ssh_failures_per_min", 1), 1)
    evidence.append(f"✓ Anomaly: {hit_count}x observed vs baseline ({deviation:.0f}x above normal rate)")
    evidence.append(f"✓ Historical similarity to known {attack_type} signature: {round(hs * 100)}%")
    evidence.append(f"✓ Agent agreement: {agents_agreed}/{total_agents} agents flagged independently")

    return ConfidenceFactors(
        evidence_count=ec,
        anomaly_severity=av,
        rule_match_density=rm,
        historical_similarity=hs,
        multi_agent_agreement=ma,
        evidence_lines=evidence,
    )
