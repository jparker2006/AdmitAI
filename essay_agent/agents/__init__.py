"""essay_agent.agents

Base & registry for LangGraph-powered agents used throughout the Essay Agent
project.
"""
from __future__ import annotations

from typing import Any, Dict, Type, Callable

AGENT_REGISTRY: Dict[str, "BaseLangGraphAgent"] = {}


def register_agent(name: str) -> Callable[[Type["BaseLangGraphAgent"]], Type["BaseLangGraphAgent"]]:  # noqa: D401
    """Decorator to register a :class:`BaseLangGraphAgent` subclass by *name*."""

    def _decorator(cls: Type["BaseLangGraphAgent"]) -> Type["BaseLangGraphAgent"]:
        if name in AGENT_REGISTRY:  # pragma: no cover – duplicate guard
            raise ValueError(f"Agent '{name}' already registered")
        AGENT_REGISTRY[name] = cls  # type: ignore[assignment]
        return cls

    return _decorator

# Deferred import to avoid circulars --------------------------------------------------
from types import ModuleType as _ModuleType  # noqa: E402
import importlib as _importlib  # noqa: E402


def _lazy_import(name: str) -> _ModuleType:  # noqa: D401
    return _importlib.import_module(name)

# Public exports ----------------------------------------------------------------------
from .base import BaseLangGraphAgent, AgentMessage, AgentState  # noqa: E402, I001
from .research_agent import ResearchAgent  # noqa: E402
from .structure_agent import StructureAgent  # noqa: E402
from .style_agent import StyleAgent  # noqa: E402
from .supervisor import SupervisorAgent  # noqa: E402
from .communication import MessageEnvelope, EventQueue, push_message, pop_messages, resolve_conflicts  # noqa: E402

__all__ = [
    "BaseLangGraphAgent",
    "AgentMessage",
    "AgentState",
    "AGENT_REGISTRY",
    "register_agent",
]
__all__.extend([
    "ResearchAgent",
    "StructureAgent",
    "StyleAgent",
    "SupervisorAgent",
    "MessageEnvelope",
    "EventQueue",
    "push_message",
    "pop_messages",
    "resolve_conflicts",
]) 