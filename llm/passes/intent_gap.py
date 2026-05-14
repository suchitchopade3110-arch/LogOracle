# llm/passes/intent_gap.py
"""
Intent vs Implementation Gap Detection.
PRD spec: 2-stage LLM pipeline.
  Stage 1: extract intent from PR title + description (natural language)
  Stage 2: infer functional behaviour from code diff AST nodes
  Compare: cosine distance between intent embedding and diff embedding
  Threshold: distance > 0.4 → flagged WARNING

Example:
  PR title: "Fix null check on user input"
  Diff also modifies payment processing path → flagged HIGH
"""
from llm.groq_client import groq_json
from llm.embeddings.similarity import embed, cosine_distance
from llm.models.llm_models import IntentGapResult

GAP_THRESHOLD = 0.4   # PRD spec

INTENT_EXTRACT_PROMPT = """
Extract the developer's stated intent from this PR description.
Return JSON only: {{"result": "<single plain-English sentence describing EXACTLY what change the developer intended to make>"}}.

PR Title: {title}
PR Description: {description}
"""

BEHAVIOUR_EXTRACT_PROMPT = """
Describe in one plain-English sentence what this code diff ACTUALLY does functionally.
Focus on: what functions/paths are modified, what logic changes, what side effects exist.
Return JSON only: {{"result": "<single plain-English sentence describing the actual functional behaviour>"}}.

Language: {language}
Code Diff:
```
{diff}
```
"""


async def detect_intent_gap(
    code_diff: str,
    pr_title: str,
    pr_description: str,
    language: str = "python",
) -> IntentGapResult:
    """
    Run 2-stage intent gap detection.
    Returns IntentGapResult with gap_score, flagged, severity, explanation.
    """
    # Stage 1: extract intent from PR description
    intent_result = await groq_json(
        messages=[{"role": "user", "content": INTENT_EXTRACT_PROMPT.format(
            title=pr_title,
            description=pr_description[:2000],
        )}],
        max_tokens=200,
        temperature=0.1,
    )
    stated_intent = _extract_text(intent_result, pr_title)

    # Stage 2: infer behaviour from code diff
    behaviour_result = await groq_json(
        messages=[{"role": "user", "content": BEHAVIOUR_EXTRACT_PROMPT.format(
            language=language,
            diff=code_diff[:4000],
        )}],
        max_tokens=200,
        temperature=0.1,
    )
    inferred_behaviour = _extract_text(behaviour_result, "Unknown behaviour")

    # Compute cosine distance between intent and behaviour embeddings
    intent_embed    = embed(stated_intent)
    behaviour_embed = embed(inferred_behaviour)
    gap_score = cosine_distance(intent_embed, behaviour_embed)

    flagged  = gap_score > GAP_THRESHOLD
    severity = "HIGH" if gap_score > 0.6 else "INFO"

    explanation = _build_explanation(
        stated_intent, inferred_behaviour, gap_score, flagged
    )

    return IntentGapResult(
        gap_score=round(gap_score, 3),
        flagged=flagged,
        severity=severity,
        explanation=explanation,
        stated_intent=stated_intent,
        inferred_behaviour=inferred_behaviour,
    )


def _extract_text(result: dict, fallback: str) -> str:
    """GROQ json_mode returns {"result": "..."} or raw text."""
    if isinstance(result, dict):
        for key in ("result", "intent", "behaviour", "description", "text"):
            if key in result:
                return str(result[key])
        # If dict but no known key — join all values
        vals = [str(v) for v in result.values() if isinstance(v, str)]
        return " ".join(vals) if vals else fallback
    return str(result) if result else fallback


def _build_explanation(intent: str, behaviour: str, score: float, flagged: bool) -> str:
    if not flagged:
        return f"Code diff aligns with stated intent (gap score: {score:.2f})."
    return (
        f"Stated intent: \"{intent}\"\n"
        f"Actual behaviour: \"{behaviour}\"\n"
        f"Gap score: {score:.2f} (threshold: {GAP_THRESHOLD}). "
        f"The diff appears to modify code outside the stated scope."
    )
