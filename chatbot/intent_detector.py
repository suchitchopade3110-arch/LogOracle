# chatbot/intent_detector.py
import re
from enum import Enum

class Intent(str, Enum):
    ACCEPT        = "accept"          # user approves finding/fix
    DISPUTE       = "dispute"         # user pushes back on finding
    CLARIFY       = "clarify"         # user asking why/how/what
    PLAIN_ENGLISH = "plain_english"   # user wants simpler explanation
    GENERAL       = "general"         # everything else

# Pattern sets — order matters, checked top to bottom
_PLAIN_PATTERNS = [
    r"\bexplain simply\b",
    r"\bplain english\b",
    r"\bsimple(r)?\b.*\bexplain\b",
    r"\bwhat does (that|this) mean\b",
    r"\bi don.t understand\b",
    r"\blayman\b",
]

_DISPUTE_PATTERNS = [
    r"\bthat.s (wrong|incorrect|not right)\b",
    r"\bi (don.t|disagree|dispute)\b",
    r"\bfalse positive\b",
    r"\bnot a (bug|vulnerability|issue)\b",
    r"\byou.re wrong\b",
    r"\bthis is fine\b",
    r"\bactually\b.{0,30}\b(work|correct|fine|ok)\b",
]

_CLARIFY_PATTERNS = [
    r"\bwhy\b",
    r"\bhow\b",
    r"\bwhat (is|are|does|caused)\b",
    r"\bcan you explain\b",
    r"\btell me more\b",
    r"\?\s*$",
]

_ACCEPT_PATTERNS = [
    r"\b(yes|ok|okay|sounds good|looks good|approve|accepted|go ahead|do it)\b",
    r"\bfix it\b",
    r"\bapply\b",
    r"\bmakes sense\b",
]


def detect_intent(message: str) -> Intent:
    """
    Rule-based intent detection on user message.
    Fast, no LLM call needed. Falls back to GENERAL.
    """
    msg = message.lower().strip()

    if _match_any(msg, _PLAIN_PATTERNS):
        return Intent.PLAIN_ENGLISH
    if _match_any(msg, _DISPUTE_PATTERNS):
        return Intent.DISPUTE
    if _match_any(msg, _CLARIFY_PATTERNS):
        return Intent.CLARIFY
    if _match_any(msg, _ACCEPT_PATTERNS):
        return Intent.ACCEPT

    return Intent.GENERAL


def _match_any(text: str, patterns: list) -> bool:
    return any(re.search(p, text) for p in patterns)
