# analysis/ast_engine/pass3_owasp.py

"""
Pass 3 — OWASP rule engine.
Runs AFTER Subhiksha's semantic Pass 2.
Detects: OWASP Top 10 security vulnerabilities.
Cross-platform: same rules apply regardless of OS.
"""
import re
from typing import List
from analysis.models.analysis_models import ASTIssue

OWASP_RULES = [
    # A1: Injection
    {"id": "A01-INJ-001", "cwe": "CWE-89",  "severity": "CRITICAL",
     "pattern": r"(execute|query|cursor\.execute)\s*\(\s*[\"'].*%.*[\"']\s*%",
     "message": "SQL Injection: string formatting in query. Use parameterized queries."},

    {"id": "A01-INJ-002", "cwe": "CWE-89",  "severity": "CRITICAL",
     "pattern": r"(execute|query)\s*\(\s*f[\"'].*\{",
     "message": "SQL Injection: f-string in query. Use parameterized queries."},

    {"id": "A01-CMD-001", "cwe": "CWE-78",  "severity": "CRITICAL",
     "pattern": r"subprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True",
     "message": "Command Injection: shell=True with user-controlled input."},


    # A1: Command injection via eval
    {"id": "A01-CMD-002", "cwe": "CWE-95", "severity": "HIGH",
     "pattern": r"\beval\s*\(",
     "message": "Use of eval() — code injection risk. Never eval user input."},

    # A2: Cryptographic failures
    {"id": "A02-CRY-001", "cwe": "CWE-259", "severity": "CRITICAL",
     "pattern": r"(password|secret|api_key|token)\s*=\s*[\"'][^\"']{4,}[\"']",
     "message": "Hardcoded secret detected. Move to environment variable."},

    {"id": "A02-CRY-002", "cwe": "CWE-326", "severity": "HIGH",
     "pattern": r"MD5|md5\(|hashlib\.md5",
     "message": "Weak hashing: MD5 is cryptographically broken. Use SHA-256 or bcrypt."},

    {"id": "A02-CRY-003", "cwe": "CWE-326", "severity": "HIGH",
     "pattern": r"hashlib\.sha1\b",
     "message": "Weak hashing: SHA-1 deprecated for security use. Use SHA-256."},

    # A3: XSS
    {"id": "A03-XSS-001", "cwe": "CWE-79",  "severity": "HIGH",
     "pattern": r"innerHTML\s*=|document\.write\(",
     "message": "XSS risk: innerHTML/document.write with dynamic content. Sanitize input."},

    # A5: Security misconfiguration
    {"id": "A05-MISC-001", "cwe": "CWE-330", "severity": "MEDIUM",
     "pattern": r"random\.random\(\)|random\.randint\(",
     "message": "Insecure randomness: use secrets module for security-sensitive values."},

    {"id": "A05-MISC-002", "cwe": "CWE-614", "severity": "MEDIUM",
     "pattern": r"verify\s*=\s*False",
     "message": "SSL verification disabled. Remove verify=False in production."},

    # A7: Auth failures
    {"id": "A07-AUTH-001", "cwe": "CWE-798", "severity": "CRITICAL",
     "pattern": r"(jwt\.decode|verify_token)\s*\([^)]*verify\s*=\s*False",
     "message": "JWT verification disabled. Never set verify=False."},

    # A9: Logging
    {"id": "A09-LOG-001", "cwe": "CWE-532", "severity": "MEDIUM",
     "pattern": r"logging\.(info|debug|warning|error)\s*\(.*password",
     "message": "Sensitive data logged: password appears in log statement."},

    # Windows-specific
    {"id": "WIN-REG-001", "cwe": "CWE-269", "severity": "HIGH",
     "pattern": r"winreg\.SetValue|RegSetValue|HKEY_LOCAL_MACHINE",
     "message": "Windows Registry write detected. Verify intent and permissions."},

    # macOS-specific
    {"id": "MAC-ENT-001", "cwe": "CWE-269", "severity": "MEDIUM",
     "pattern": r"NSTask|launchctl|xattr.*remove",
     "message": "macOS system call detected. Verify entitlements and sandbox compliance."},
]


async def run_owasp_pass(code: str, language: str) -> List[ASTIssue]:
    """Run Pass 3 OWASP rules against code. Returns list of ASTIssue."""
    issues = []
    lines  = code.splitlines()

    for rule in OWASP_RULES:
        pat = re.compile(rule["pattern"], re.IGNORECASE)
        for i, line in enumerate(lines, 1):
            if pat.search(line):
                issues.append(ASTIssue(
                    pass_number=3,
                    line=i,
                    severity=rule["severity"],
                    message=rule["message"],
                    cwe_id=rule["cwe"],
                    rule_id=rule["id"],
                    confidence=0.88,
                    auto_fixable=rule["severity"] in ("CRITICAL", "HIGH"),
                ))

    return issues
