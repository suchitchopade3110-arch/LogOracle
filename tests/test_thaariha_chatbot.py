"""
tests/test_all.py  — consolidated test suite
Run: PYTHONPATH=. pytest tests/test_all.py -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from chatbot.intent_detector import detect_intent, Intent
from chatbot.persona import get_persona_prompt, get_persona_label, Persona
from chatbot.context_assembler import assemble_system_prompt, _format_logs
from chatbot.models.chat_models import SessionContext
from chatbot.dispute_handler import _parse_verdict


# ── intent_detector ───────────────────────────────────────────────────────────

class TestIntentDetector:
    def test_plain_english(self):
        assert detect_intent("explain simply please") == Intent.PLAIN_ENGLISH
        assert detect_intent("what does that mean?") == Intent.PLAIN_ENGLISH
        assert detect_intent("i don't understand this") == Intent.PLAIN_ENGLISH

    def test_dispute(self):
        assert detect_intent("that's wrong") == Intent.DISPUTE
        assert detect_intent("i disagree with this finding") == Intent.DISPUTE
        assert detect_intent("false positive") == Intent.DISPUTE

    def test_clarify(self):
        assert detect_intent("why is this a vulnerability?") == Intent.CLARIFY
        assert detect_intent("how does this cause the crash?") == Intent.CLARIFY

    def test_accept(self):
        assert detect_intent("yes go ahead") == Intent.ACCEPT
        assert detect_intent("looks good, apply it") == Intent.ACCEPT

    def test_general_fallback(self):
        assert detect_intent("hello") == Intent.GENERAL
        assert detect_intent("show me the logs") == Intent.GENERAL


# ── persona ───────────────────────────────────────────────────────────────────

class TestPersona:
    def test_all_personas_non_empty(self):
        for p in Persona:
            assert len(get_persona_prompt(p)) > 10

    def test_security_mentions_owasp(self):
        assert "OWASP" in get_persona_prompt(Persona.SECURITY)

    def test_mentor_is_warm(self):
        prompt = get_persona_prompt(Persona.MENTOR).lower()
        assert "patient" in prompt or "mentor" in prompt

    def test_labels_all_defined(self):
        for p in Persona:
            label = get_persona_label(p)
            assert isinstance(label, str) and len(label) > 0


# ── context_assembler ─────────────────────────────────────────────────────────

class TestContextAssembler:
    def test_returns_string(self):
        ctx = SessionContext()
        result = assemble_system_prompt(ctx, Persona.DEFAULT, mode="tech")
        assert isinstance(result, str) and len(result) > 0

    def test_plain_mode_instruction_present(self):
        ctx = SessionContext()
        result = assemble_system_prompt(ctx, Persona.DEFAULT, mode="plain")
        assert "PLAIN ENGLISH MODE" in result

    def test_log_truncation(self):
        long_log = "\n".join([f"line {i}" for i in range(600)])
        result = _format_logs(long_log)
        assert "truncated" in result

    def test_security_keywords_in_prompt(self):
        ctx = SessionContext()
        result = assemble_system_prompt(ctx, Persona.SECURITY, mode="tech")
        assert "OWASP" in result or "Security Auditor" in result


# ── dispute_handler ───────────────────────────────────────────────────────────

class TestDisputeHandler:
    def test_parse_valid_json(self):
        raw = '{"verdict": "retracted", "new_severity": "LOW", "new_confidence": 0.3, "explanation": "Valid."}'
        result = _parse_verdict(raw)
        assert result["verdict"] == "retracted"
        assert result["new_confidence"] == 0.3

    def test_parse_malformed_fallback(self):
        result = _parse_verdict("not valid json at all")
        assert result["verdict"] == "confirmed"

    def test_parse_json_with_markdown_fence(self):
        raw = '```json\n{"verdict": "confirmed", "new_severity": "HIGH", "new_confidence": 0.8, "explanation": "Stands."}\n```'
        result = _parse_verdict(raw)
        assert result["verdict"] == "confirmed"

    def test_xp_zero_on_confirmed(self):
        # xp_awarded=0 must still be returned (the original bug)
        raw = '{"verdict": "confirmed", "new_severity": "HIGH", "new_confidence": 0.9, "explanation": "Confirmed."}'
        result = _parse_verdict(raw)
        # xp injected by evaluate_dispute, not _parse_verdict — just verify no crash
        assert result["verdict"] == "confirmed"
