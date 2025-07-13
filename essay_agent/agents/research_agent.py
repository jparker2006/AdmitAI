"""essay_agent.agents.research_agent

Specialist LangGraph agent that performs prompt-centric research and analysis.
It helps the user understand an essay prompt, extracts requirements, suggests a
response strategy, and (optionally) scores an existing draft.

Pipeline
--------
1. classify_prompt      – determine theme/category
2. extract_requirements – pull out word limits & key questions
3. suggest_strategy     – propose approach based on user profile
4. essay_scoring        – score current draft (only if essay_text provided)

Required inputs (``AgentState.data``)
-------------------------------------
* essay_prompt (str)
* profile (str, optional) – user profile for strategy suggestions
* essay_text (str, optional) – existing draft to score
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from essay_agent.agents.base import BaseLangGraphAgent, AgentState
from essay_agent.tools import REGISTRY as TOOL_REGISTRY


class ResearchAgent(BaseLangGraphAgent):  # noqa: D401
    """LangGraph specialist agent for prompt research & analysis."""

    def _build_graph(self):  # noqa: D401
        nodes = [
            ("classify_prompt", self._node_classify_prompt),
            ("extract_requirements", self._node_extract_requirements),
            ("suggest_strategy", self._node_suggest_strategy),
            ("essay_scoring", self._node_essay_scoring),  # may be skipped
        ]
        return self.build_linear_graph(nodes)

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _node_classify_prompt(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state.__dict__
        data = state.data
        prompt = data.get("essay_prompt")
        if not prompt or not str(prompt).strip():
            state.errors.append("ResearchAgent: 'essay_prompt' required")
            return state.__dict__
        tool = TOOL_REGISTRY.get("classify_prompt")
        if tool is None:
            state.errors.append("Tool 'classify_prompt' missing")
            return state.__dict__
        try:
            result = await asyncio.to_thread(tool, essay_prompt=prompt)
            data["classify_prompt"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))
        return state.__dict__

    async def _node_extract_requirements(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state.__dict__
        data = state.data
        prompt = data.get("essay_prompt")
        tool = TOOL_REGISTRY.get("extract_requirements")
        if tool is None:
            state.errors.append("Tool 'extract_requirements' missing")
            return state.__dict__
        try:
            result = await asyncio.to_thread(tool, essay_prompt=prompt)
            data["extract_requirements"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))
        return state.__dict__

    async def _node_suggest_strategy(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state.__dict__
        data = state.data
        prompt = data.get("essay_prompt")
        profile = data.get("profile", "")
        tool = TOOL_REGISTRY.get("suggest_strategy")
        if tool is None:
            state.errors.append("Tool 'suggest_strategy' missing")
            return state.__dict__
        try:
            result = await asyncio.to_thread(tool, essay_prompt=prompt, profile=profile)
            data["suggest_strategy"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))
        return state.__dict__

    async def _node_essay_scoring(self, state: "AgentState") -> "AgentState":  # noqa: D401
        # This node is optional – skip gracefully if no draft
        if state.errors:
            return state.__dict__
        data = state.data
        essay_text = data.get("essay_text")
        if not essay_text:
            return state.__dict__  # nothing to score
        prompt = data.get("essay_prompt")
        tool = TOOL_REGISTRY.get("essay_scoring")
        if tool is None:
            state.errors.append("Tool 'essay_scoring' missing")
            return state.__dict__
        try:
            result = await asyncio.to_thread(tool, essay_text=essay_text, essay_prompt=prompt)
            data["essay_scoring"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))
        return state.__dict__ 