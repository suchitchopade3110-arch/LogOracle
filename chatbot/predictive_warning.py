# chatbot/predictive_warning.py
"""
Before session closes (or after each new finding), check if current
error pattern matches historical patterns → inject proactive warning.

Threshold: cosine similarity > 0.65 (per PRD spec)
Uses: shared llm.embeddings.similarity helpers.
"""
from typing import Optional, List
from llm.embeddings.similarity import embed, cosine_similarity

SIMILARITY_THRESHOLD = 0.65

# Historical incident store (in-memory for MVP — seeded with demo scenarios)
# Format: { "description": str, "resolution": str, "embedding": np.ndarray | None }
KNOWN_INCIDENTS: List[dict] = [
    {
        "description": "Memory spike from Redis connection leak causing OOM kill",
        "resolution": "Check connection pool config. Set max_connections. Use connection context managers.",
        "embedding": None,   # populated on first call to _ensure_embeddings()
    },
    {
        "description": "SSH brute-force causing sshd child process explosion and nginx OOM kill",
        "resolution": "Block attacker IP via ufw. Restart nginx. Enable fail2ban.",
        "embedding": None,
    },
    {
        "description": "SQL injection vulnerability in user input not sanitized before query",
        "resolution": "Use parameterized queries. Never string-format SQL with user input.",
        "embedding": None,
    },
    {
        "description": "Disk full due to unrotated logs causing application write failures",
        "resolution": "Run journalctl --vacuum-time=7d. Set logrotate. Monitor disk via cron.",
        "embedding": None,
    },
    {
        "description": "API retry storm from upstream timeout causing cascading failures",
        "resolution": "Add exponential backoff with jitter. Set circuit breaker. Cache last known good response.",
        "embedding": None,
    },
]

def _ensure_embeddings():
    """Lazy-compute embeddings for known incidents on first call."""
    for incident in KNOWN_INCIDENTS:
        if incident["embedding"] is None:
            incident["embedding"] = embed(incident["description"])

def check_predictive_warning(current_finding_message: str) -> Optional[str]:
    """
    Compare current finding against known incident embeddings.
    Returns warning string if similarity > 0.65, else None.
    """
    try:
        _ensure_embeddings()
        current_embedding = embed(current_finding_message)

        best_match = None
        best_score = 0.0

        for incident in KNOWN_INCIDENTS:
            score = cosine_similarity(current_embedding, incident["embedding"])
            if score > best_score:
                best_score = score
                best_match = incident

        if best_score >= SIMILARITY_THRESHOLD and best_match:
            return (
                f"⚠ This pattern matches a past incident "
                f"(similarity: {best_score:.0%}): {best_match['description']}. "
                f"Suggested resolution: {best_match['resolution']}"
            )

        return None

    except Exception:
        # Never crash the chat flow over a predictive check
        return None
