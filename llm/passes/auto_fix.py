# llm/passes/auto_fix.py
"""
Auto-Fix Engine.
For each detected issue, generate a candidate patch using constrained LLM prompt.

PRD constraints:
  - Patch must be syntactically valid (Shruthi's AST re-parse validates before delivery)
  - Patch must not modify lines outside flagged range ± 5 lines
  - Confidence < 0.70 → suggestion only, never auto-applied
  - Branch isolation: all applied patches on separate branch (Suchit handles git part)

Input:  code + language + issue (line, severity, message, cwe_id)
Output: AutoFix
"""
from llm.groq_client import groq_json
from llm.cache import cache_key_for
from llm.models.llm_models import AutoFix
from typing import Optional

CONTEXT_WINDOW = 50    # lines before and after flagged line
CONFIDENCE_THRESHOLD = 0.70

FIX_PROMPT = """
You are an expert software engineer generating a precise bug fix.

LANGUAGE: {language}
BUG TYPE: {cwe_id}
SEVERITY: {severity}
BUG DESCRIPTION: {message}
FLAGGED LINE: {line}

CODE CONTEXT (lines {start_line}–{end_line}):
```
{context_code}
```

Generate a minimal fix. Rules:
1. Only modify the flagged line ± 5 lines maximum
2. Do NOT change function signatures, imports, or logic outside the bug scope
3. The fix must be syntactically valid {language}
4. Preserve existing code style (indentation, naming conventions)

Respond ONLY with valid JSON:
{{
  "patch_diff": "<unified diff format showing the change>",
  "explanation": "<one paragraph: what you changed and why>",
  "confidence": <0.0-1.0>,
  "lines_modified": [<list of line numbers changed>]
}}
"""

async def generate_fix(
    code: str,
    language: str,
    issue: dict,
) -> AutoFix:
    """
    Generate auto-fix for a single issue.
    Returns AutoFix with confidence score.
    auto_applied=True only if confidence >= 0.70 (AST validation happens in Shruthi's module).
    """
    line = issue.get("line") or 1
    lines = code.splitlines()
    total = len(lines)

    # Extract ± CONTEXT_WINDOW lines around flagged line
    start = max(0, line - CONTEXT_WINDOW - 1)
    end   = min(total, line + CONTEXT_WINDOW)
    context_code = "\n".join(
        f"{start + i + 1:4d} | {l}"
        for i, l in enumerate(lines[start:end])
    )

    key = cache_key_for("fix", f"{language}:{issue.get('message','')}:{line}")

    result = await groq_json(
        messages=[{"role": "user", "content": FIX_PROMPT.format(
            language=language,
            cwe_id=issue.get("cwe_id", "N/A"),
            severity=issue.get("severity", "MEDIUM"),
            message=issue.get("message", ""),
            line=line,
            start_line=start + 1,
            end_line=end,
            context_code=context_code,
        )}],
        max_tokens=800,
        temperature=0.1,    # very low — fixes must be deterministic
        cache_key=key,
    )

    confidence = float(result.get("confidence", 0.0))

    return AutoFix(
        original_lines=context_code,
        patch_diff=result.get("patch_diff", ""),
        explanation=result.get("explanation", ""),
        confidence=confidence,
        cwe_id=issue.get("cwe_id"),
        auto_applied=confidence >= CONFIDENCE_THRESHOLD,
        line_range=(start + 1, end),
    )
