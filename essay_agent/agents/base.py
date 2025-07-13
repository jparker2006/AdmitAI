"""essay_agent.agents.base

Abstract LangGraph agent base-class plus message & state models.  All specialist
agents (structure, style, research, etc.) will inherit from this class.
"""
from __future__ import annotations

import asyncio
import traceback
from abc import ABC, abstractmethod, ABCMeta
from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable, Type, Awaitable, Optional

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph  # type: ignore

# -----------------------------------------------------------------------------
# Message & State models
# -----------------------------------------------------------------------------

class AgentMessage(BaseModel):
    """Standard envelope for messages passed between agents/nodes."""

    sender: str
    receiver: str
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class AgentState:  # noqa: D401
    """Generic state container carried through a LangGraph StateGraph."""

    phase: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    last_message: Optional[AgentMessage] = None


# -----------------------------------------------------------------------------
# Core abstract agent
# -----------------------------------------------------------------------------

class BaseLangGraphAgent(ABC):  # noqa: D401, WPS110
    """Base class that wraps an internal LangGraph StateGraph."""

    name: str
    state_cls: Type[AgentState] = AgentState

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, *, name: str | None = None):
        self.name = name or self.__class__.__name__
        self._graph: CompiledGraph = self._build_graph()

    # ------------------------------------------------------------------
    # Abstracts & helpers for subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_graph(self) -> CompiledGraph:  # noqa: D401
        """Return a compiled LangGraph graph for this agent."""

    # Helper: build linear graph from mapping -----------------------------------
    @classmethod
    def build_linear_graph(
        cls,
        nodes: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] | List[
            tuple[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]]
        ],
    ) -> CompiledGraph:  # noqa: D401
        """Utility to create *phase1 → phase2 → … → END* graph quickly."""

        sg: StateGraph[AgentState] = StateGraph(cls.state_cls)

        # Normalize input -------------------------------------------------------
        if isinstance(nodes, dict):
            items = list(nodes.items())
        else:
            items = list(nodes)

        # Add nodes -------------------------------------------------------------
        for name, fn in items:
            sg.add_node(name, fn)

        # Wire linear edges -----------------------------------------------------
        first_name = items[0][0]
        sg.set_entry_point(first_name)
        for idx in range(len(items) - 1):
            sg.add_edge(items[idx][0], items[idx + 1][0])
        sg.add_edge(items[-1][0], END)

        return sg.compile()

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------

    async def ainvoke(self, initial_state: AgentState | None = None) -> AgentState:  # noqa: D401
        """Run the compiled graph asynchronously and return the final state."""

        state_dict: Dict[str, Any] = (
            initial_state.__dict__ if initial_state is not None else {}
        )
        try:
            result_dict: Dict[str, Any] = await self._graph.ainvoke(state_dict)
        except Exception as exc:  # noqa: BLE001
            # Capture uncaught error into state --------------------------------
            trace = "".join(traceback.format_tb(exc.__traceback__))
            err_msg = f"{exc.__class__.__name__}: {exc}. Trace:\n{trace}"
            state_dict.setdefault("errors", []).append(err_msg)
            return self.state_cls(**state_dict)

        return self.state_cls(**result_dict)

    def invoke(self, initial_state: AgentState | None = None) -> AgentState:  # noqa: D401
        """Synchronous wrapper around :py:meth:`ainvoke`."""

        return asyncio.run(self.ainvoke(initial_state))


# -----------------------------------------------------------------------------
# Register in global registry upon subclass creation (metaclass hack) ----------
# -----------------------------------------------------------------------------

from essay_agent.agents import AGENT_REGISTRY  # noqa: E402  circular OK at end


class _AgentMeta(ABCMeta):  # noqa: D401
    def __new__(mcls, name, bases, namespace, **kwargs):  # noqa: D401
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        # Skip abstract base class itself --------------------------------------
        if name != "BaseLangGraphAgent" and not name.startswith("_"):
            AGENT_REGISTRY[name] = cls  # type: ignore[assignment]
        return cls


# Re-bind BaseLangGraphAgent to meta so subclasses auto-register --------------
BaseLangGraphAgent = _AgentMeta(  # type: ignore[misc]
    "BaseLangGraphAgent",
    BaseLangGraphAgent.__bases__,
    dict(BaseLangGraphAgent.__dict__),
) 