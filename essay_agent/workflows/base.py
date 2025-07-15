"""Base workflow classes for advanced LangGraph patterns.

This module provides abstract base classes for workflow nodes that support
branching, conditional logic, loops, and quality gates.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from essay_agent.planner import EssayPlan


# ---------------------------------------------------------------------------
# Enhanced State Management
# ---------------------------------------------------------------------------

@dataclass
class WorkflowState(EssayPlan):
    """Enhanced state container for complex workflows."""
    
    iteration_count: int = 0
    max_iterations: int = 3
    node_history: Optional[List[str]] = field(default_factory=list)
    quality_scores: Dict[str, float] = field(default_factory=dict)
    revision_attempts: int = 0  # Add for compatibility
    max_revision_attempts: int = 3  # Add for compatibility
    quality_threshold: float = 8.0  # Add for compatibility
    current_draft: str = ""  # Add for compatibility
    essay_prompt: str = ""  # Add for compatibility
    
    def __post_init__(self):
        """Ensure node_history is always initialized."""
        if self.node_history is None:
            self.node_history = []
        # Call parent post_init if it exists
        if hasattr(super(), '__post_init__'):
            super().__post_init__()
    
    def get_evaluation_score(self) -> float:
        """Get latest evaluation score."""
        return self.quality_scores.get("overall", 0.0)
    
    def increment_iteration(self) -> None:
        """Track revision iterations."""
        self.iteration_count += 1
    
    def add_node_execution(self, node_name: str) -> None:
        """Track node execution history."""
        if self.node_history is None:
            self.node_history = []
        self.node_history.append(node_name)
    
    def has_exceeded_max_iterations(self) -> bool:
        """Check if maximum iterations reached."""
        return self.iteration_count >= self.max_iterations
    
    def get_last_n_nodes(self, n: int) -> List[str]:
        """Get last n executed nodes for loop detection."""
        if self.node_history is None:
            self.node_history = []
        return self.node_history[-n:] if len(self.node_history) >= n else self.node_history
    
    def increment_revision_attempt(self) -> None:
        """Track revision attempts."""
        self.revision_attempts += 1
        self.increment_iteration()
    
    def should_continue_revision(self) -> bool:
        """Check if revision loop should continue."""
        return (
            self.revision_attempts < self.max_revision_attempts and
            self.get_evaluation_score() < self.quality_threshold
        )
    
    def get_current_draft(self) -> str:
        """Get current essay draft from tool outputs."""
        if self.current_draft:
            return self.current_draft
        
        # Extract from tool outputs
        tool_outputs = self.data.get("tool_outputs", {})
        
        # Check polish output first, then draft
        if "polish" in tool_outputs:
            result = tool_outputs["polish"]
            if isinstance(result, dict) and "polished_essay" in result:
                return result["polished_essay"]
        
        if "draft" in tool_outputs:
            result = tool_outputs["draft"]
            if isinstance(result, dict) and "essay_text" in result:
                return result["essay_text"]
        
        return ""
    
    def get_essay_prompt(self) -> str:
        """Get essay prompt from context."""
        if self.essay_prompt:
            return self.essay_prompt
        
        return self.data.get("context", {}).get("essay_prompt", "")


# ---------------------------------------------------------------------------
# Abstract Base Classes
# ---------------------------------------------------------------------------

class WorkflowNode(ABC):
    """Abstract base class for all workflow nodes."""
    
    def __init__(self):
        self._name: Optional[str] = None
    
    @abstractmethod
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute the node's logic and return state updates.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary of state updates to merge into the current state
        """
        pass
    
    def get_name(self) -> str:
        """Get the node's name."""
        return self._name or self.__class__.__name__
    
    def set_name(self, name: str) -> None:
        """Set the node's name."""
        self._name = name


# ---------------------------------------------------------------------------
# Conditional Node Base Classes
# ---------------------------------------------------------------------------

class ConditionalNode(WorkflowNode):
    """Base class for nodes that make routing decisions."""
    
    def __init__(self, condition_fn: callable = None):
        super().__init__()
        self.condition_fn = condition_fn
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute the condition and return routing decision."""
        if self.condition_fn:
            result = await self.condition_fn(state)
            return {"routing_decision": result}
        else:
            # Backward compatibility - use should_continue method
            result = self.should_continue(state)
            next_nodes = self.get_next_nodes(state)
            return {
                "routing_decision": result,
                "next_nodes": next_nodes
            }
    
    def should_continue(self, state: EssayPlan) -> bool:
        """Determine if condition is met. Override in subclasses."""
        return True
    
    def get_next_nodes(self, state: EssayPlan) -> List[str]:
        """Return list of next node names. Override in subclasses."""
        return []
    
    def _ensure_workflow_state(self, state: EssayPlan) -> WorkflowState:
        """Convert EssayPlan to WorkflowState if needed."""
        return ensure_workflow_state_compatibility(state)


class QualityGateNode(ConditionalNode):
    """Node that evaluates quality and decides on routing."""
    
    def __init__(self, quality_threshold: float = 8.0):
        super().__init__(self._quality_check)
        self.quality_threshold = quality_threshold
    
    async def _quality_check(self, state: EssayPlan) -> str:
        """Check if essay meets quality threshold."""
        if hasattr(state, 'get_evaluation_score'):
            score = state.get_evaluation_score()
            return "pass" if score >= self.quality_threshold else "revise"
        return "revise"


# ---------------------------------------------------------------------------
# Loop Control Classes
# ---------------------------------------------------------------------------

class LoopControlNode(WorkflowNode):
    """Base class for nodes that control loop execution."""
    
    def __init__(self, max_iterations: int = 3):
        super().__init__()
        self.max_iterations = max_iterations
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Check loop conditions and update state."""
        if hasattr(state, 'has_exceeded_max_iterations'):
            should_continue = not state.has_exceeded_max_iterations()
        else:
            should_continue = True
        
        return {"should_continue": should_continue}


class RevisionLoopNode(LoopControlNode):
    """Node that controls revision loop execution."""
    
    def __init__(self, max_attempts: int = 3, quality_threshold: float = 8.0):
        super().__init__(max_attempts)
        self.quality_threshold = quality_threshold
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Check revision loop conditions."""
        if hasattr(state, 'should_continue_revision'):
            should_continue = state.should_continue_revision()
        else:
            should_continue = True
        
        return {"should_continue_revision": should_continue}


# ---------------------------------------------------------------------------
# Workflow Utilities
# ---------------------------------------------------------------------------

def create_workflow_state(
    phase: "Phase",
    data: Dict[str, Any],
    **kwargs
) -> WorkflowState:
    """Create a WorkflowState with proper initialization."""
    state = WorkflowState(
        phase=phase,
        data=data,
        **kwargs
    )
    
    # Ensure node_history is properly initialized
    if state.node_history is None:
        state.node_history = []
    
    return state


def ensure_workflow_state_compatibility(state: EssayPlan) -> WorkflowState:
    """Convert EssayPlan to WorkflowState if needed."""
    if isinstance(state, WorkflowState):
        # Ensure node_history is properly initialized
        if state.node_history is None:
            state.node_history = []
        return state
    
    # Convert EssayPlan to WorkflowState
    workflow_state = WorkflowState(
        phase=state.phase,
        data=state.data,
        errors=state.errors,
        metadata=state.metadata
    )
    
    # Ensure node_history is properly initialized
    if workflow_state.node_history is None:
        workflow_state.node_history = []
    
    return workflow_state 