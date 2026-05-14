from typing import List
from llm.groq_client import groq_json
from llm.cache import cache_key_for


class SemanticIssue:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def model_dump(self):
        return self.__dict__


async def run_semantic_pass(code: str, language: str, ast_issues: List[dict] = []) -> List:
    key = cache_key_for("semantic", f"{language}:{code}")
    prompt = f"""
You are a senior engineer. Find semantic bugs in this {language} code.
CODE:
```
{code[:4000]}
```
Respond ONLY with JSON: {{"issues": [{{"line": 1, "severity": "HIGH", "message": "...", "explanation": "...", "cwe_id": null, "confidence": 0.9, "fix_hint": "..."}}]}}
If no issues: {{"issues": []}}
"""
    result = await groq_json(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.2,
        cache_key=key,
    )
    return [SemanticIssue(**i) for i in result.get("issues", []) if isinstance(i, dict)]
