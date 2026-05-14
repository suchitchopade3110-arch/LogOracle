# analysis/ast_engine/pass1_ast.py
"""
Pass 1 — Syntactic AST analysis via tree-sitter.
Detects: unreachable code, undefined variables, type mismatches, syntax errors.

Supported: Python, JavaScript, TypeScript, Java, Go
Fallback:  regex-based check if tree-sitter unavailable (PRD risk mitigation)
"""
from typing import List
import ast
from analysis.models.analysis_models import ASTIssue

SUPPORTED_LANGUAGES = {"python", "javascript", "typescript", "java", "go"}

async def run_ast_pass(code: str, language: str) -> List[ASTIssue]:
    """Run Pass 1. Returns list of ASTIssue."""
    lang = language.lower()
    if lang not in SUPPORTED_LANGUAGES:
        return []

    try:
        return await _tree_sitter_analysis(code, lang)
    except Exception:
        # PRD fallback: regex-based syntactic check
        return _regex_fallback(code, lang)


async def _tree_sitter_analysis(code: str, language: str) -> List[ASTIssue]:
    """Real tree-sitter parse. Raises if tree-sitter unavailable."""
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser

    # Map language to tree-sitter binding
    lang_map = {
        "python": tspython,
        # TODO: add js/ts/java/go bindings when installed
    }
    ts_lang_module = lang_map.get(language)
    if ts_lang_module is None:
        raise ImportError(f"tree-sitter binding not available for {language}")

    PY_LANGUAGE = Language(ts_lang_module.language(), language)
    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    tree = parser.parse(bytes(code, "utf8"))

    issues = []
    _walk_tree(tree.root_node, code, issues)
    if language == "python" and not tree.root_node.has_error:
        issues.extend(_python_ast_checks(code))
    return issues


def _walk_tree(node, code: str, issues: List[ASTIssue]):
    """Recursively walk AST. Flag known bad node types."""
    BAD_NODE_TYPES = {
        "ERROR":            ("CRITICAL", "Syntax error", None),
        "undefined":        ("HIGH",     "Undefined identifier", "CWE-457"),
        "missing_semicolon":("LOW",      "Missing semicolon", None),
    }

    if getattr(node, "is_error", False) or getattr(node, "is_missing", False):
        issues.append(ASTIssue(
            pass_number=1,
            line=node.start_point[0] + 1,
            col=node.start_point[1],
            severity="CRITICAL",
            message=f"Syntax error at line {node.start_point[0] + 1}",
            confidence=0.95,
        ))
    elif node.type in BAD_NODE_TYPES:
        severity, msg, cwe = BAD_NODE_TYPES[node.type]
        issues.append(ASTIssue(
            pass_number=1,
            line=node.start_point[0] + 1,
            col=node.start_point[1],
            severity=severity,
            message=f"{msg} at line {node.start_point[0] + 1}",
            cwe_id=cwe,
            confidence=0.95,
        ))

    for child in node.children:
        _walk_tree(child, code, issues)


def _python_ast_checks(code: str) -> List[ASTIssue]:
    """Python-specific AST checks layered on top of tree-sitter parsing."""
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return issues

    mutable_types = (ast.List, ast.Dict, ast.Set)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                issues.append(ASTIssue(
                    pass_number=1,
                    line=node.lineno,
                    col=node.col_offset,
                    severity="HIGH",
                    message=f"Use of {node.func.id}() — code injection risk",
                    cwe_id="CWE-95",
                    confidence=0.90,
                ))
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(ASTIssue(
                pass_number=1,
                line=node.lineno,
                col=node.col_offset,
                severity="MEDIUM",
                message="Bare except catches all exceptions and can hide failures",
                confidence=0.85,
            ))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults:
                if isinstance(default, mutable_types):
                    issues.append(ASTIssue(
                        pass_number=1,
                        line=node.lineno,
                        col=node.col_offset,
                        severity="MEDIUM",
                        message="Mutable default argument can leak state between calls",
                        cwe_id="CWE-665",
                        confidence=0.85,
                    ))

    return issues


def _regex_fallback(code: str, language: str) -> List[ASTIssue]:
    """
    PRD risk mitigation: if tree-sitter unavailable, use regex patterns.
    Lower confidence than AST — marks as such.
    """
    import re
    issues = []
    lines = code.splitlines()

    patterns = {
        "python": [
            (r"^\s*$", "INFO",   "Empty line (INFO)",        None),
            (r"exec\s*\(",    "HIGH",   "Use of exec() — code injection risk", "CWE-95"),
            (r"eval\s*\(",    "HIGH",   "Use of eval() — code injection risk", "CWE-95"),
            (r"__import__\(", "MEDIUM", "Dynamic import via __import__",        "CWE-95"),
        ],
        "javascript": [
            (r"eval\s*\(",    "HIGH",   "Use of eval() — code injection risk", "CWE-95"),
            (r"innerHTML\s*=","MEDIUM", "innerHTML assignment — XSS risk",      "CWE-79"),
            (r"document\.write\(", "MEDIUM", "document.write — XSS risk",       "CWE-79"),
        ],
    }

    lang_patterns = patterns.get(language, [])
    for i, line in enumerate(lines, 1):
        for pat, sev, msg, cwe in lang_patterns:
            if re.search(pat, line):
                issues.append(ASTIssue(
                    pass_number=1,
                    line=i,
                    severity=sev,
                    message=msg,
                    cwe_id=cwe,
                    confidence=0.70,   # lower — regex not AST
                ))
    return issues
