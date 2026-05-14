# llm/quiz/generator.py
"""
Quiz MCQ Generation.
PRD spec:
  - 4-option MCQ from real bug found in session
  - 1 correct answer, 3 plausible distractors
  - Difficulty tag: easy | medium | hard
  - Second LLM validation pass (validator.py) before delivery
  - SM-2 spaced repetition delivery timing (scheduler separate)
"""
import uuid
from llm.groq_client import groq_json
from llm.cache import cache_key_for
from llm.models.llm_models import QuizQuestion

GENERATE_PROMPT = """
Generate a multiple-choice quiz question to help a developer learn from this bug.

BUG TYPE: {bug_type}
CWE: {cwe_id}
SEVERITY: {severity}
BUG DESCRIPTION: {message}
CODE SNIPPET:
```
{code_snippet}
```
FIX APPLIED:
```
{fix}
```

Rules:
- Question must test understanding of WHY this was a bug and HOW to prevent it
- 4 options: exactly 1 correct, 3 plausible distractors (not obviously wrong)
- Difficulty: easy (conceptual), medium (application), hard (edge case/nuance)
- Explanation must teach — not just say which is correct

Respond ONLY with valid JSON:
{{
  "question": "<the question text>",
  "options": ["<option A>", "<option B>", "<option C>", "<option D>"],
  "correct_index": <0-3>,
  "explanation": "<2-3 sentences explaining the correct answer and why others are wrong>",
  "difficulty": "easy" | "medium" | "hard"
}}
"""

async def generate_question(
    bug_type: str,
    message: str,
    code_snippet: str,
    fix: str,
    severity: str = "MEDIUM",
    cwe_id: str = "N/A",
    finding_id: str = None,
) -> QuizQuestion | None:
    """
    Generate MCQ from real bug. Returns None if validation fails after 2 attempts.
    """
    from llm.quiz.validator import validate_question

    key = cache_key_for("quiz", f"{bug_type}:{message}")

    for attempt in range(2):   # max 2 generation attempts (PRD spec)
        result = await groq_json(
            messages=[{"role": "user", "content": GENERATE_PROMPT.format(
                bug_type=bug_type,
                cwe_id=cwe_id,
                severity=severity,
                message=message,
                code_snippet=code_snippet[:1500],
                fix=fix[:500],
            )}],
            max_tokens=600,
            temperature=0.4 + (attempt * 0.1),   # slight variation on retry
            cache_key=key if attempt == 0 else None,
        )

        question = _parse_question(result, bug_type, cwe_id, finding_id)
        if question is None:
            continue

        # Second LLM validation pass (PRD spec)
        is_valid = await validate_question(question)
        if is_valid:
            return question
        # else: retry with fresh generation

    return None   # both attempts failed validation


def _parse_question(
    raw: dict,
    bug_type: str,
    cwe_id: str,
    finding_id: str,
) -> QuizQuestion | None:
    try:
        options = raw.get("options", [])
        if len(options) != 4:
            return None
        correct = int(raw.get("correct_index", -1))
        if correct not in range(4):
            return None

        return QuizQuestion(
            question_id=str(uuid.uuid4())[:8],
            question=raw["question"],
            options=options,
            correct_index=correct,
            explanation=raw.get("explanation", ""),
            difficulty=raw.get("difficulty", "medium"),
            bug_type=bug_type,
            cwe_id=cwe_id,
            source_finding=finding_id,
        )
    except Exception:
        return None


# llm/quiz/validator.py
"""
Second LLM validation pass for quiz questions.
PRD spec: reject rate < 20% in validation step.
Validates: clarity, correctness, non-ambiguity of options.
"""
from llm.groq_client import groq_json
from llm.models.llm_models import QuizQuestion

VALIDATE_PROMPT = """
You are reviewing a multiple-choice quiz question for quality.

QUESTION: {question}
OPTIONS:
A) {opt_a}
B) {opt_b}
C) {opt_c}
D) {opt_d}
CORRECT: option {correct_letter}
EXPLANATION: {explanation}

Evaluate:
1. Is the question clear and unambiguous?
2. Is the correct answer definitively correct?
3. Are the distractors plausible (not obviously wrong)?
4. Does the explanation actually teach something?

Respond ONLY with JSON:
{{
  "valid": true | false,
  "rejection_reason": "<null if valid, brief reason if invalid>"
}}
"""

OPTION_LETTERS = ["A", "B", "C", "D"]

async def validate_question(q: QuizQuestion) -> bool:
    """Returns True if question passes quality check, False if should be regenerated."""
    result = await groq_json(
        messages=[{"role": "user", "content": VALIDATE_PROMPT.format(
            question=q.question,
            opt_a=q.options[0],
            opt_b=q.options[1],
            opt_c=q.options[2],
            opt_d=q.options[3],
            correct_letter=OPTION_LETTERS[q.correct_index],
            explanation=q.explanation,
        )}],
        max_tokens=200,
        temperature=0.1,
    )
    return bool(result.get("valid", False))
