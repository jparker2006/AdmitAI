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

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Any


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


class EssayPlanner:
    """Stateless planner (will reference memory in later iterations)."""

    def decide_next_action(self, user_input: str, context: Dict[str, Any]) -> Plan:
        """Placeholder decision engine.

        Args:
            user_input: Raw user message.
            context: Dict containing memory snapshot & conversation state.
        Returns:
            Plan: structured description of tasks for Executor.
        """
        # TODO: Replace with actual logic (LLM call / rules)
        return Plan(phase=Phase.BRAINSTORMING, tasks=["echo"], metadata={}) 