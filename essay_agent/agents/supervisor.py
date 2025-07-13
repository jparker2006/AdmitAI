"""essay_agent.agents.supervisor

LangGraph SupervisorAgent – coordinates Research, Structure, and Style
specialist agents. It delegates work sequentially with conditional early exit
on error, merging each sub-agent's results back into the shared state.
"""
from __future__ import annotations

import asyncio
import traceback
from typing import Any, Dict

from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph  # type: ignore

from essay_agent.agents.base import BaseLangGraphAgent, AgentState
from essay_agent.agents.research_agent import ResearchAgent
from essay_agent.agents.structure_agent import StructureAgent
from essay_agent.agents.style_agent import StyleAgent


class SupervisorAgent(BaseLangGraphAgent):  # noqa: D401
    """High-level agent that orchestrates specialist agents in order."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self):
        # Instantiate sub-agents once -----------------------------------------
        self.research = ResearchAgent()
        self.structure = StructureAgent()
        self.style = StyleAgent()
        super().__init__(name="SupervisorAgent")

    # ------------------------------------------------------------------
    # Graph definition
    # ------------------------------------------------------------------

    def _build_graph(self) -> CompiledGraph:  # noqa: D401
        sg: StateGraph[AgentState] = StateGraph(AgentState)

        # Add nodes -----------------------------------------------------------
        sg.add_node("research", self._node_research)
        sg.add_node("structure", self._node_structure)
        sg.add_node("style", self._node_style)

        # Entry ----------------------------------------------------------------
        sg.set_entry_point("research")

        # Conditional edges: if errors present, end early ---------------------
        def _cond(state: dict | AgentState):  # type: ignore[type-arg]  # noqa: D401
            errors = state.errors if isinstance(state, AgentState) else state.get("errors")
            return "end" if errors else "continue"

        sg.add_conditional_edges(
            "research",
            _cond,
            {
                "continue": "structure",
                "end": END,
            },
        )
        sg.add_conditional_edges(
            "structure",
            _cond,
            {
                "continue": "style",
                "end": END,
            },
        )
        sg.add_edge("style", END)

        return sg.compile()

    # ------------------------------------------------------------------
    # Node helpers
    # ------------------------------------------------------------------

    async def _run_subagent(self, sub_agent: BaseLangGraphAgent, state: dict | AgentState) -> dict:  # noqa: D401
        """Helper: run *sub_agent* and merge its output into *state*."""

        # Convert to dict for safe mutation ---------------------------------
        if isinstance(state, AgentState):
            working_state: Dict[str, Any] = state.__dict__.copy()
        else:
            working_state = state  # type: ignore[assignment]

        try:
            agent_state = AgentState(**working_state)
            result: AgentState = await sub_agent.ainvoke(agent_state)  # type: ignore[assignment]

            working_state.setdefault("data", {}).update(result.data)
            working_state.setdefault("errors", []).extend(result.errors)
        except Exception as exc:  # noqa: BLE001
            trace = "".join(traceback.format_tb(exc.__traceback__))
            working_state.setdefault("errors", []).append(
                f"{exc.__class__.__name__}: {exc}. Trace:\n{trace}",
            )
        return working_state

    async def _node_research(self, state):  # noqa: D401
        if (state.errors if isinstance(state, AgentState) else state.get("errors")):
            return state
        return await self._run_subagent(self.research, state)

    async def _node_structure(self, state):  # noqa: D401
        if (state.errors if isinstance(state, AgentState) else state.get("errors")):
            return state
        return await self._run_subagent(self.structure, state)

    async def _node_style(self, state):  # noqa: D401
        if (state.errors if isinstance(state, AgentState) else state.get("errors")):
            return state
        return await self._run_subagent(self.style, state) 