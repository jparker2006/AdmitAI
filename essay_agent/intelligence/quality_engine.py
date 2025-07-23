"""essay_agent.intelligence.quality_engine

Real-time draft quality scorer used by SmartOrchestrator (Section 3.3).
Falls back to a lightweight heuristic when the full `essay_scoring` tool or
LLM is unavailable (e.g. during CI).
"""
from __future__ import annotations

import os
import statistics
import string
from typing import Optional

from essay_agent.tools import REGISTRY as TOOL_REGISTRY


_MIN_WORDS = 40  # too small → low score


def _simple_readability(words: list[str]) -> float:  # 0-10
    if not words:
        return 0.0
    avg_len = statistics.mean(len(w) for w in words)
    vocab_ratio = len(set(words)) / len(words)
    score = 5 + (1.5 - abs(1.5 - avg_len))  # preference for ~5-7 char words
    score += vocab_ratio * 5  # richer vocab gets more points
    score -= max(0, (_MIN_WORDS - len(words)) / _MIN_WORDS * 5)
    return max(0.0, min(10.0, score))


class QualityEngine:
    """Provides `score_draft(text) -> float` in the 0-10 range."""

    def __init__(self, *, offline: bool | None = None):
        # Decide whether to call essay_scoring tool
        if offline is None:
            offline = os.getenv("ESSAY_AGENT_OFFLINE_TEST", "0") == "1"
        self._use_tool = not offline and "essay_scoring" in TOOL_REGISTRY
        self._tool = TOOL_REGISTRY.get("essay_scoring") if self._use_tool else None

    def score_draft(self, text: str, *, user_id: str = "_qi") -> float:  # noqa: D401
        if not text:
            return 0.0
        # Prefer dedicated essay_scoring tool --------------------------------
        if self._tool is not None:
            try:
                res = self._tool(draft=text, user_id=user_id, profile={})
                score = res.get("ok", {}).get("overall_score")
                if isinstance(score, (int, float)):
                    return float(score)
            except Exception:  # noqa: BLE001
                # Fall back to heuristic
                pass
        # Heuristic ---------------------------------------------------------
        words = [w.strip(string.punctuation).lower() for w in text.split() if w]
        return _simple_readability(words) 

    # ------------------------------------------------------------------
    # Async convenience wrapper – avoids blocking event loop
    # ------------------------------------------------------------------

    async def async_score_draft(self, text: str, *, user_id: str = "_qi") -> float:  # noqa: D401
        """Async wrapper around `score_draft` using thread offload.

        Allows callers (e.g., SmartOrchestrator) to remain fully async.
        """
        import asyncio

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.score_draft(text, user_id=user_id)) 