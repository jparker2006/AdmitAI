"""
EssayPlanner - 100x Project Planner Skeleton

High-level responsibilities:
1. Interpret user input & memory state
2. Decide next action in the essay workflow
3. Return structured plan objects for the executor

TODO:
- Implement enum `Phase` for writing stages
- Add method `decide_next_action`
- Interface with memory (to be defined in memory module)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Any
import json, os
from essay_agent.prompts import SYSTEM_PROMPT, PLANNER_REACT_PROMPT
from essay_agent.tools import REGISTRY as TOOL_REGISTRY

# LangChain imports ---------------------------------------------------------
# Prefer langchain_openai (recommended) then community path, fallback to legacy
try:
    from langchain_openai import ChatOpenAI  # type: ignore
except ImportError:  # pragma: no cover – use community or legacy
    try:
        from langchain_community.chat_models import ChatOpenAI  # type: ignore
    except ImportError:  # pragma: no cover
        try:
            from langchain.chat_models import ChatOpenAI  # type: ignore
        except ImportError:
            ChatOpenAI = None  # type: ignore

# FakeListLLM remains the same for offline tests
try:
    from langchain.llms.fake import FakeListLLM  # type: ignore
except ImportError:
    FakeListLLM = None  # type: ignore


class Phase(Enum):
    """Writing phases for essay workflow."""

    BRAINSTORMING = auto()
    OUTLINING = auto()
    DRAFTING = auto()
    REVISING = auto()
    POLISHING = auto()


@dataclass
class Plan:
    """Container describing executor actions."""

    phase: Phase
    tasks: List[str]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# LangGraph-compatible plan structure
# ---------------------------------------------------------------------------


@dataclass
class EssayPlan:
    """State container that flows through the LangGraph executor."""

    phase: Phase = Phase.BRAINSTORMING
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Update return type for MVP while keeping backward compatibility ------------


class EssayPlanner:
    """Stateless planner (will reference memory in later iterations)."""

    def decide_next_action(self, user_input: str, context: Dict[str, Any]) -> EssayPlan:  # type: ignore[override]
        """Placeholder decision engine.

        Args:
            user_input: Raw user message.
            context: Dict containing memory snapshot & conversation state.
        Returns:
            EssayPlan: structured description of tasks for Executor.
        """

        # Lazy-init ReAct planner --------------------------------------------------
        if not hasattr(self, "_react"):
            self._react = EssayReActPlanner()

        return self._react.decide_next_action(user_input, context)


# ---------------------------------------------------------------------------
# ReAct planner implementation
# ---------------------------------------------------------------------------


class EssayReActPlanner:
    """LLM-driven planner that selects the next tool using a ReAct prompt."""

    def __init__(self, llm=None):
        if llm is None:
            if os.getenv("OPENAI_API_KEY") and ChatOpenAI is not None:
                llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            else:
                # Offline deterministic LLM for tests / no API key
                responses = [
                    '{"tool": "brainstorm", "args": {}}',
                ]
                llm = FakeListLLM(responses=responses) if FakeListLLM else None

        self.llm = llm

        # Build prompt content ------------------------------------------------
        self._tool_list_str = "\n".join(f"- {name}" for name in TOOL_REGISTRY.keys())

    # ------------------------------------------------------------------
    def decide_next_action(self, user_input: str, context: Dict[str, Any]) -> EssayPlan:  # noqa: D401
        # If llm is None fallback ------------------------------------------------
        if self.llm is None:
            return EssayPlan()

        prompt = PLANNER_REACT_PROMPT.format(
            system=SYSTEM_PROMPT, tools=self._tool_list_str, user=user_input
        )

        from essay_agent.llm_client import call_llm
        raw = call_llm(self.llm, prompt)

        try:
            json_str = raw.strip().splitlines()[-1]
            data = json.loads(json_str)
            tool_name = data.get("tool")
            args = data.get("args", {})
        except Exception:  # noqa: BLE001
            return EssayPlan(errors=["Planner JSON parse error"], metadata={"llm_raw": raw})

        if tool_name not in TOOL_REGISTRY:
            # Still return tool selection so executor or caller can handle
            return EssayPlan(
                phase=_phase_from_tool(tool_name),
                errors=[f"Unknown tool {tool_name}"],
                metadata={"llm_raw": raw},
                data={"next_tool": tool_name, "args": args},
            )

        phase = _phase_from_tool(tool_name)
        return EssayPlan(phase=phase, metadata={"llm_raw": raw}, data={"next_tool": tool_name, "args": args})


def _phase_from_tool(tool: str) -> Phase:
    mapping = {
        "brainstorm": Phase.BRAINSTORMING,
        "outline": Phase.OUTLINING,
        "draft": Phase.DRAFTING,
        "revise": Phase.REVISING,
        "polish": Phase.POLISHING,
    }
    return mapping.get(tool, Phase.BRAINSTORMING) 