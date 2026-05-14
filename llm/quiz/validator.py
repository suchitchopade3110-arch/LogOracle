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
