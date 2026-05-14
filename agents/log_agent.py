from analysis.log_parser.log_parser_core import parse_log
from analysis.security_agent.security_agent import detect_brute_force, match_cves
from agents.orchestrator import Finding, Severity, AgentName
from typing import List


class LogAgent:
    async def analyze(self, log_text: str) -> List[Finding]:
        parsed = await parse_log(log_text, redact=True)

        findings = []

        for event in parsed.events:
            if event.severity in ("CRITICAL", "WARNING"):
                findings.append(Finding(
                    agent=AgentName.LOG,
                    severity=Severity[event.severity],
                    message=event.message or event.raw[:200],
                    confidence=0.85,
                    timestamp=event.timestamp,
                ))

        brute = detect_brute_force(parsed.events)
        if brute:
            findings.append(Finding(
                agent=AgentName.SECURITY,
                severity=Severity.CRITICAL,
                message=brute["message"],
                confidence=brute["confidence"],
                fix=brute.get("fix_linux"),
            ))

        cves = match_cves(log_text, parsed.platform)
        for cve in cves:
            findings.append(Finding(
                agent=AgentName.SECURITY,
                severity=Severity.CRITICAL,
                message=cve["message"],
                confidence=cve["confidence"],
                fix=cve.get("fix"),
            ))

        seen_msgs = set()
        deduped = []
        for finding in findings:
            if finding.message not in seen_msgs:
                deduped.append(finding)
                seen_msgs.add(finding.message)
        return deduped
