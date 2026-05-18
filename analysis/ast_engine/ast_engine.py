from dataclasses import dataclass
import ast


@dataclass
class CodeIssue:
    line: int
    severity: str
    message: str
    explanation: str
    cwe_id: str | None = None
    confidence: float = 0.8
    fix_hint: str | None = None

    def model_dump(self):
        return self.__dict__


async def run_ast_pass(code: str, language: str) -> list[CodeIssue]:
    if language.lower() != "python":
        return []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [CodeIssue(
            line=exc.lineno or 1,
            severity="HIGH",
            message="Python syntax error",
            explanation=exc.msg,
            confidence=0.95,
            fix_hint="Fix the syntax error before semantic analysis.",
        )]

    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
            issues.append(CodeIssue(
                line=node.lineno,
                severity="HIGH",
                message=f"Use of {node.func.id}() on dynamic input is dangerous",
                explanation=f"{node.func.id}() can execute arbitrary code if user-controlled data reaches it.",
                cwe_id="CWE-95",
                confidence=0.9,
                fix_hint="Replace dynamic execution with explicit parsing or a safe dispatch table.",
            ))
    return issues


async def run_owasp_pass(code: str, language: str) -> list[CodeIssue]:
    lowered = code.lower()
    issues = []
    if "password" in lowered and any(token in lowered for token in ["=", ":"]):
        issues.append(CodeIssue(
            line=_line_for(code, "password"),
            severity="MEDIUM",
            message="Possible hardcoded password or secret",
            explanation="Hardcoded credentials can leak through source control and logs.",
            cwe_id="CWE-798",
            confidence=0.75,
            fix_hint="Move secrets to environment variables or a secrets manager.",
        ))
    if "subprocess" in lowered and "shell=true" in lowered.replace(" ", ""):
        issues.append(CodeIssue(
            line=_line_for(code, "shell=True"),
            severity="HIGH",
            message="subprocess called with shell=True",
            explanation="Shell execution can allow command injection when arguments include user input.",
            cwe_id="CWE-78",
            confidence=0.85,
            fix_hint="Pass arguments as a list and keep shell=False.",
        ))
    return issues


def _line_for(code: str, needle: str) -> int:
    needle_lower = needle.lower()
    for index, line in enumerate(code.splitlines(), start=1):
        if needle_lower in line.lower():
            return index
    return 1
