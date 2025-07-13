"""essay_agent.agents.style_agent

Specialist LangGraph agent focused on essay style refinement. The pipeline
invokes a series of polishing tools to correct grammar, strengthen vocabulary,
ensure consistency, and achieve the target word count.

Pipeline
--------
1. fix_grammar          – correct grammar & spelling
2. enhance_vocabulary   – stronger, precise word choice
3. check_consistency    – verify tense/voice/style consistency
4. optimize_word_count  – trim or expand to target length

Input requirements (``AgentState.data``)
---------------------------------------
* essay_text (str)            – draft to polish
* target_word_count (int)     – desired length (optional, default 650)

All tool outputs are stored in ``state.data`` under their tool names.
Errors are accumulated in ``state.errors`` and abort the remaining steps.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from essay_agent.agents.base import BaseLangGraphAgent, AgentState
from essay_agent.tools import REGISTRY as TOOL_REGISTRY

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _get_latest_essay(data: Dict[str, Any]) -> str | None:  # noqa: D401
    """Return the most recent essay text available in *data*."""
    # Preference order: optimized -> consistency -> vocabulary -> grammar -> original
    for key in (
        "optimize_word_count",
        "check_consistency",
        "enhance_vocabulary",
        "fix_grammar",
    ):
        val = data.get(key)
        if isinstance(val, dict):
            # The schema defines these possible fields
            for field in ("optimized_essay", "corrected_essay", "enhanced_essay"):
                text = val.get(field) if isinstance(val, dict) else None  # type: ignore[arg-type]
                if text:
                    return str(text)
    return data.get("essay_text")


# ---------------------------------------------------------------------------
# StyleAgent implementation
# ---------------------------------------------------------------------------


class StyleAgent(BaseLangGraphAgent):  # noqa: D401
    """LangGraph specialist agent that polishes essay style and mechanics."""

    def _build_graph(self):  # noqa: D401
        nodes = [
            ("fix_grammar", self._node_fix_grammar),
            ("enhance_vocabulary", self._node_enhance_vocabulary),
            ("check_consistency", self._node_check_consistency),
            ("optimize_word_count", self._node_optimize_word_count),
        ]
        return self.build_linear_graph(nodes)

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _node_fix_grammar(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state
        data = state.data
        essay_text = data.get("essay_text")
        if not essay_text or not str(essay_text).strip():
            state.errors.append("StyleAgent: 'essay_text' is required")
            return state
        tool = TOOL_REGISTRY.get("fix_grammar")
        if tool is None:
            state.errors.append("Tool 'fix_grammar' not found in registry")
            return state
        try:
            result = await asyncio.to_thread(tool, essay_text=essay_text)
            data["fix_grammar"] = result
        except Exception as exc:  # noqa: BLE001
            state.setdefault("errors", []).append(str(exc))
        return state.__dict__

    async def _node_enhance_vocabulary(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state
        data = state.data
        essay_text = _get_latest_essay(data)
        if not essay_text:
            state.errors.append("StyleAgent: essay text unavailable for vocabulary enhancement")
            return state
        tool = TOOL_REGISTRY.get("enhance_vocabulary")
        if tool is None:
            state.errors.append("Tool 'enhance_vocabulary' not found in registry")
            return state
        try:
            result = await asyncio.to_thread(tool, essay_text=essay_text)
            data["enhance_vocabulary"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))
        return state.__dict__

    async def _node_check_consistency(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state
        data = state.data
        essay_text = _get_latest_essay(data)
        if not essay_text:
            state.errors.append("StyleAgent: essay text unavailable for consistency check")
            return state
        tool = TOOL_REGISTRY.get("check_consistency")
        if tool is None:
            state.errors.append("Tool 'check_consistency' not found in registry")
            return state
        try:
            result = await asyncio.to_thread(tool, essay_text=essay_text)
            data["check_consistency"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))
        return state.__dict__

    async def _node_optimize_word_count(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state
        data = state.data
        essay_text = _get_latest_essay(data)
        target = int(data.get("target_word_count", 650))
        if not essay_text:
            state.errors.append("StyleAgent: essay text unavailable for word count optimization")
            return state
        tool = TOOL_REGISTRY.get("optimize_word_count")
        if tool is None:
            state.errors.append("Tool 'optimize_word_count' not found in registry")
            return state
        try:
            result = await asyncio.to_thread(tool, essay_text=essay_text, target_words=target)
            data["optimize_word_count"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))
        return state.__dict__ 