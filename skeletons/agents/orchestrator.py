# agents/orchestrator.py
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
import asyncio

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING  = "WARNING"
    INFO     = "INFO"

class AgentName(str, Enum):
    LOG         = "log"
    API         = "api"
    SECURITY    = "security"
    CORRELATION = "correlation"
    HALLUCINATION = "hallucination"

@dataclass
class Finding:
    agent: AgentName
    severity: Severity
    message: str
    confidence: float          # 0.0 – 1.0
    fix: Optional[str] = None
    cwe_id: Optional[str] = None
    timestamp: Optional[str] = None

@dataclass
class OrchestratorState:
    health: str = "GREEN"      # GREEN | ORANGE | RED
    findings: List[Finding] = field(default_factory=list)
    agent_status: dict = field(default_factory=dict)  # agent → WATCHING|ANALYZING|ALERT

class Orchestrator:
    def __init__(self):
        self.state = OrchestratorState()

    def classify_severity(self, findings: List[Finding]) -> str:
        """Derive overall health badge from all active findings."""
        if any(f.severity == Severity.CRITICAL for f in findings):
            return "RED"
        if any(f.severity == Severity.WARNING for f in findings):
            return "ORANGE"
        return "GREEN"

    def should_popup(self, finding: Finding, last_popup_ts: float) -> bool:
        """Smart popup: CRITICAL + confidence > 85% + 5-min cooldown."""
        import time
        from core.config import settings
        if finding.severity != Severity.CRITICAL:
            return False
        if finding.confidence < settings.popup_confidence_threshold:
            return False
        if time.time() - last_popup_ts < settings.popup_cooldown_seconds:
            return False
        return True

    async def run_all_agents(self, log_text: str, session_id: str) -> List[Finding]:
        """
        Fire all agents concurrently. Collect findings.
        TODO: replace stubs with real agent calls.
        """
        results = await asyncio.gather(
            self._run_log_agent(log_text),
            self._run_security_agent(log_text),
            self._run_api_agent(log_text),
            return_exceptions=True
        )
        findings = []
        for r in results:
            if isinstance(r, list):
                findings.extend(r)
        self.state.health = self.classify_severity(findings)
        self.state.findings = findings
        return findings

    async def _run_log_agent(self, log_text: str) -> List[Finding]:
        from agents.log_agent import LogAgent
        return await LogAgent().analyze(log_text)

    async def _run_security_agent(self, log_text: str) -> List[Finding]:
        from agents.security_agent import SecurityAgent
        return await SecurityAgent().analyze(log_text)

    async def _run_api_agent(self, log_text: str) -> List[Finding]:
        from agents.api_agent import APIAgent
        return await APIAgent().analyze(log_text)
