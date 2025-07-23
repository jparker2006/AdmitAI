from __future__ import annotations
"""Prompt length validation helper."""

def validate_prompt_len(prompt: str, max_words: int = 650) -> None:  # noqa: D401
    """Raise ValueError if *prompt* exceeds *max_words*.

    Args:
        prompt: Essay prompt string.
        max_words: Maximum allowed words (default 650).
    """
    words = prompt.strip().split()
    if len(words) > max_words:
        raise ValueError(f"Prompt exceeds {max_words}-word limit (got {len(words)} words)") 