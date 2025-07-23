from __future__ import annotations

"""Test utilities shared across unit tests."""

def universal_context() -> dict:  # noqa: D401
    """Return a rich synthetic context covering common keys for ArgResolver tests."""
    return {
        "essay_prompt": "Tell me about a time you faced a challenge.",
        "prompt": "Tell me about a time you faced a challenge.",
        "profile": {},
        "user_profile": {},
        "selection": "Highlighted text here.",
        "outline": {},
        "story": "Placeholder story text.",
        "draft": "Placeholder draft text.",
        "college_context": {
            "essay_prompt": "Tell me about a time you faced a challenge.",
            "word_limit": 650,
        },
        "essay_state": {
            "story": "State story",
        },
        "preferences": {
            "tone": "neutral",
        },
    } 