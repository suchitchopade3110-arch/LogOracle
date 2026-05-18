# agents/log_agent.py
# Shruthi fills parse logic. Suchit wires to orchestrator.
from agents.orchestrator import Finding, Severity, AgentName
from llm.groq_client import groq_analyze
from typing import List

class LogAgent:
    async def analyze(self, log_text: str) -> List[Finding]:
        # TODO: call Shruthi's parser → get structured events
        # Then call GROQ for plain-English + fix suggestion
        raw_events = self._parse(log_text)
        findings = []
        for event in raw_events:
            result = await groq_analyze(event, mode="log")
            findings.append(Finding(
                agent=AgentName.LOG,
                severity=result["severity"],
                message=result["message"],
                confidence=result["confidence"],
                fix=result.get("fix"),
                timestamp=event.get("timestamp"),
            ))
        return findings

    def _parse(self, log_text: str):
        # STUB — Shruthi replaces with real parser
        return [{"raw": log_text, "timestamp": None}]


# agents/api_agent.py
from agents.orchestrator import Finding, Severity, AgentName
from typing import List

class APIAgent:
    RETRY_STORM_THRESHOLD = 5      # same endpoint fail > 5x in window = storm

    async def analyze(self, log_text: str) -> List[Finding]:
        # TODO: parse HTTP request/response logs
        # Detect: 4xx/5xx spikes, retry storms, latency outliers
        findings = []
        # STUB
        return findings

    def detect_retry_storm(self, requests: list) -> bool:
        # Group by endpoint. Count failures in 60s window.
        # Return True if any endpoint exceeds threshold.
        pass  # TODO


# agents/security_agent.py
from agents.orchestrator import Finding, Severity, AgentName
from typing import List
import re

BRUTE_FORCE_PATTERN = re.compile(r"Failed password.*sshd", re.IGNORECASE)
BRUTE_FORCE_THRESHOLD = 10   # attempts in single log chunk

class SecurityAgent:
    async def analyze(self, log_text: str) -> List[Finding]:
        findings = []
        findings += self._check_brute_force(log_text)
        # TODO: CVE signature matching
        return findings

    def _check_brute_force(self, log_text: str) -> List[Finding]:
        matches = BRUTE_FORCE_PATTERN.findall(log_text)
        if len(matches) >= BRUTE_FORCE_THRESHOLD:
            return [Finding(
                agent=AgentName.SECURITY,
                severity=Severity.CRITICAL,
                message=f"SSH brute-force detected: {len(matches)} failed attempts",
                confidence=0.94,
                fix="sudo ufw deny from <attacker_ip> && sudo systemctl restart sshd",
            )]
        return []


# agents/correlation_engine.py
from agents.orchestrator import Finding
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class CausalLink:
    cause: Finding
    effect: Finding
    confidence: float

class CorrelationEngine:
    WINDOW_SECONDS = 30   # events within 30s window considered related

    def build_chain(self, findings: List[Finding]) -> List[CausalLink]:
        """
        Sort by timestamp. Build directed causal links.
        Rule-based MVP: Security CRITICAL → Log spike → Perf spike → API failure.
        """
        # TODO: implement timestamp alignment + graph traversal
        chain = []
        sorted_findings = sorted(
            [f for f in findings if f.timestamp],
            key=lambda f: f.timestamp
        )
        for i in range(len(sorted_findings) - 1):
            cause = sorted_findings[i]
            effect = sorted_findings[i + 1]
            chain.append(CausalLink(cause=cause, effect=effect, confidence=0.85))
        return chain

    def to_dict(self, chain: List[CausalLink]) -> List[Dict]:
        """Serialize for frontend visual tree."""
        return [
            {
                "cause": {"agent": l.cause.agent, "message": l.cause.message},
                "effect": {"agent": l.effect.agent, "message": l.effect.message},
                "confidence": l.confidence,
            }
            for l in chain
        ]
