"""essay_agent.agents.structure_agent

Specialist LangGraph agent focused on essay structure. The agent orchestrates a
fixed four-step pipeline of structure-related tools:

1. outline_generator – create four-part outline from story idea
2. structure_validator – score outline and provide feedback
3. transition_suggestion – craft smooth transitions between sections
4. length_optimizer – rebalance outline to hit target word count

Input requirements (provided via ``AgentState.data``)
----------------------------------------------------
* story (str) – short story idea / seed
* essay_prompt (str) – the prompt the essay must answer
* word_count (int, optional, default 650)

Outputs are appended to ``state.data`` under the key matching each tool name.
Errors are collected in ``state.errors`` and halt further execution.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from essay_agent.agents.base import BaseLangGraphAgent, AgentState
from essay_agent.tools import REGISTRY as TOOL_REGISTRY

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _missing(*keys: str, data: Dict[str, Any]) -> bool:  # noqa: D401
    """Return *True* if any *keys* are missing/empty in *data*."""
    for key in keys:
        val = data.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            return True
    return False


# ---------------------------------------------------------------------------
# StructureAgent implementation
# ---------------------------------------------------------------------------


class StructureAgent(BaseLangGraphAgent):  # noqa: D401, WPS110
    """LangGraph specialist agent that improves essay structure."""

    # ------------------------------------------------------------------
    # Graph building
    # ------------------------------------------------------------------

    def _build_graph(self):  # noqa: D401
        nodes = [
            ("outline_generator", self._node_outline_generator),
            ("structure_validator", self._node_structure_validator),
            ("transition_suggestion", self._node_transition_suggestion),
            ("length_optimizer", self._node_length_optimizer),
        ]
        return self.build_linear_graph(nodes)

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _node_outline_generator(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state

        data = state.data
        if _missing("story", "essay_prompt", data=data):
            state.errors.append(
                "StructureAgent: 'story' and 'essay_prompt' are required for outline generation",
            )
            return state

        story: str = data["story"]
        essay_prompt: str = data["essay_prompt"]
        word_count: int = int(data.get("word_count", 650))

        tool = TOOL_REGISTRY.get("outline_generator")
        if tool is None:
            state.errors.append("Tool 'outline_generator' not found in registry")
            return state

        try:
            result = await asyncio.to_thread(
                tool, story=story, essay_prompt=essay_prompt, word_count=word_count,
            )
            data["outline_generator"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))

        return state.__dict__

    async def _node_structure_validator(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state

        data = state.data
        outline = data.get("outline_generator")
        if outline is None:
            state.errors.append(
                "StructureAgent: outline missing – cannot validate structure",
            )
            return state

        tool = TOOL_REGISTRY.get("structure_validator")
        if tool is None:
            state.errors.append("Tool 'structure_validator' not found in registry")
            return state

        try:
            result = await asyncio.to_thread(tool, outline=outline)
            data["structure_validator"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))

        return state.__dict__

    async def _node_transition_suggestion(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state

        data = state.data
        outline = data.get("outline_generator")
        if outline is None:
            state.errors.append(
                "StructureAgent: outline missing – cannot suggest transitions",
            )
            return state

        tool = TOOL_REGISTRY.get("transition_suggestion")
        if tool is None:
            state.errors.append("Tool 'transition_suggestion' not found in registry")
            return state

        try:
            result = await asyncio.to_thread(tool, outline=outline)
            data["transition_suggestion"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))

        return state.__dict__

    async def _node_length_optimizer(self, state: "AgentState") -> "AgentState":  # noqa: D401
        if state.errors:
            return state

        data = state.data
        outline = data.get("outline_generator")
        if outline is None:
            state.errors.append(
                "StructureAgent: outline missing – cannot optimize length",
            )
            return state

        target_word_count = int(data.get("word_count", 650))

        tool = TOOL_REGISTRY.get("length_optimizer")
        if tool is None:
            state.errors.append("Tool 'length_optimizer' not found in registry")
            return state

        try:
            result = await asyncio.to_thread(
                tool, outline=outline, target_word_count=target_word_count,
            )
            data["length_optimizer"] = result
        except Exception as exc:  # noqa: BLE001
            state.errors.append(str(exc))

        return state.__dict__ 