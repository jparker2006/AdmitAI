"""essay_agent.executor

LangGraph-powered executor that orchestrates the five fixed essay phases.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Callable, List

from langgraph.graph import StateGraph, END

# NOTE: use central registry
from essay_agent.tools import REGISTRY as TOOL_REGISTRY

from .planner import EssayPlan, Phase

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _next_phase(current: Phase) -> Phase:
    """Return the next enum member, or the same if at the end."""

    members: List[Phase] = list(Phase)
    idx = members.index(current)
    return members[idx + 1] if idx + 1 < len(members) else current


class EssayExecutor:  # pylint: disable=too-few-public-methods
    """Execute an :class:`EssayPlan` via a LangGraph `StateGraph`."""

    # Singleton compiled graph to avoid rebuild overhead
    _graph = None

    def __init__(self):
        self.registry = TOOL_REGISTRY
        if EssayExecutor._graph is None:
            EssayExecutor._graph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_plan_async(self, plan: EssayPlan) -> EssayPlan:  # noqa: D401
        """Sequential async execution (LangGraph placeholder)."""

        phase_to_tool = {
            Phase.BRAINSTORMING: "brainstorm",
            Phase.OUTLINING: "outline",
            Phase.DRAFTING: "draft",
            Phase.REVISING: "revise",
            Phase.POLISHING: "polish",
        }

        current_phase = plan.phase

        while True:
            tool_name = phase_to_tool.get(current_phase)
            if not tool_name:
                break  # Unknown phase

            tool = TOOL_REGISTRY.get(tool_name)
            if tool is None:
                plan.errors.append(f"Tool '{tool_name}' not found in registry")
                break

            try:
                result = await asyncio.to_thread(tool)
                plan.data[tool_name] = result
            except Exception as exc:  # noqa: BLE001
                plan.errors.append(str(exc))
                break

            if current_phase == Phase.POLISHING:
                break

            current_phase = _next_phase(current_phase)

        plan.phase = current_phase
        return plan

    def run_plan(self, plan: EssayPlan) -> Dict[str, Any]:  # noqa: D401
        """Sync wrapper around :meth:`run_plan_async`. Returns dict for convenience."""

        updated_plan = asyncio.run(self.run_plan_async(plan))
        # Flatten result for CLI/tests: merge data + errors (if any)
        result: Dict[str, Any] = dict(updated_plan.data)
        if updated_plan.errors:
            result["errors"] = updated_plan.errors
        return result

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):  # noqa: D401
        sg: StateGraph[EssayPlan] = StateGraph(EssayPlan)

        # Phase → (node_name, tool_name) mapping ----------------------------------
        phase_to_tool = {
            Phase.BRAINSTORMING: "brainstorm",
            Phase.OUTLINING: "outline",
            Phase.DRAFTING: "draft",
            Phase.REVISING: "revise",
            Phase.POLISHING: "polish",
        }

        # Dynamically create nodes for each phase ---------------------------------
        for phase, tool_name in phase_to_tool.items():
            node_name = tool_name  # Use tool name for clarity & edge mapping

            async def _node(state: dict, p: Phase = phase, t_name: str = tool_name) -> dict:  # noqa: D401
                # Short-circuit if an error already happened -----------------
                if state.get("errors"):
                    return state

                tool = TOOL_REGISTRY.get(t_name)
                if tool is None:
                    state.setdefault("errors", []).append(
                        f"Tool '{t_name}' not found in registry"
                    )
                    return state

                try:
                    # Call sync tools in background thread -------------------
                    result = await asyncio.to_thread(tool)
                    state.setdefault("data", {})[t_name] = result
                    state["phase"] = _next_phase(p)
                except Exception as exc:  # noqa: BLE001
                    state.setdefault("errors", []).append(str(exc))

                return state

            sg.add_node(node_name, _node)

        # Edges: fixed linear order ----------------------------------------------
        sg.set_entry_point("brainstorm")
        sg.add_edge("brainstorm", "outline")
        sg.add_edge("outline", "draft")
        sg.add_edge("draft", "revise")
        sg.add_edge("revise", "polish")
        sg.add_edge("polish", END)

        return sg.compile() 