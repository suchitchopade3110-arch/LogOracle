from dataclasses import dataclass
from typing import Dict, List

from agents.orchestrator import Finding


@dataclass
class CausalLink:
    cause: Finding
    effect: Finding
    confidence: float


class CorrelationEngine:
    WINDOW_SECONDS = 30

    def build_chain(self, findings: List[Finding]) -> List[CausalLink]:
        if not findings:
            return []

        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        sorted_findings = sorted(
            findings,
            key=lambda f: (severity_order.get(f.severity, 3), f.timestamp or "")
        )

        root = sorted_findings[0]
        rest = sorted_findings[1:]

        chain = []
        prev = root
        seen = set()
        for f in rest:
            key = f"{prev.agent}:{prev.message[:50]}->{f.agent}:{f.message[:50]}"
            if key not in seen:
                chain.append(CausalLink(cause=prev, effect=f, confidence=0.85))
                seen.add(key)
            prev = f

        return chain

    def to_dict(self, chain: List[CausalLink]) -> List[Dict]:
        return [
            {
                "cause": {"agent": l.cause.agent, "message": l.cause.message},
                "effect": {"agent": l.effect.agent, "message": l.effect.message},
                "confidence": l.confidence,
            }
            for l in chain
        ]
