from __future__ import annotations

"""Empathetic response post-processor for Essay Agent (Phase-2).

Usage:
    enhanced = ResponseEnhancer.enhance(raw_reply, context)

If ESSAY_AGENT_OFFLINE_TEST=1 the enhancer is a no-op so that unit tests
remain deterministic.
"""
from typing import Any, Dict
import os
import json

from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.prompts.response_enhancer import ENHANCER_PROMPT

_OFFLINE = os.getenv("ESSAY_AGENT_OFFLINE_TEST", "0") == "1"

class ResponseEnhancer:
    """Static helper to wrap agent replies in an empathetic tone."""

    @staticmethod
    def enhance(raw_text: str, context: Dict[str, Any] | None = None, politeness_level: int = 1) -> str:  # noqa: D401
        """Return an empathy-enhanced reply.

        Args:
            raw_text: Original reply string.
            context: Optional user / conversation context dict.
            politeness_level: 0 = terse, 1 = friendly, 2 = highly encouraging
        """
        if _OFFLINE or not raw_text.strip():
            return raw_text  # deterministic path in tests

        ctx = context or {}
        prompt = ENHANCER_PROMPT.format(
            raw_reply=raw_text,
            context=json_safe(ctx),
            politeness_level=politeness_level,
        )
        llm = get_chat_llm(temperature=0.2)
        improved = call_llm(llm, prompt).strip()
        # Guard: fall back if LLM returned empty string
        return improved or raw_text


def json_safe(data: Any) -> str:  # noqa: D401
    """Safe JSON repr limited to 300 chars to avoid blowing prompt budget."""
    try:
        txt = json.dumps(data)[:300]
    except Exception:
        txt = str(data)[:300]
    return txt

__all__ = ["ResponseEnhancer"] 