"""Revision & Feedback Loops - Intelligent revision orchestration system.

This module implements specialized revision loop control with:
- Automatic quality assessment using EssayScoringTool
- Targeted feedback generation based on evaluation results
- Progress tracking through multiple revision attempts
- Fallback mechanisms for graceful degradation
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from essay_agent.workflows.base import WorkflowState, WorkflowNode
from essay_agent.workflows import register_workflow_node
from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.models import EssayPlan
from essay_agent.utils.logging import tool_trace


@dataclass
class RevisionProgress:
    """Tracks progress of a single revision attempt."""
    
    attempt_number: int
    previous_score: float
    current_score: float
    score_improvement: float
    focus_areas: List[str]
    changes_made: List[str]
    time_taken: float
    evaluation_result: Optional[Dict[str, Any]] = None
    
    @property
    def improvement_percentage(self) -> float:
        """Calculate improvement percentage."""
        if self.previous_score == 0:
            return 0.0
        return (self.score_improvement / self.previous_score) * 100
    
    @property
    def is_improvement(self) -> bool:
        """Check if this attempt resulted in improvement."""
        return self.score_improvement > 0
    
    @property
    def is_significant_improvement(self) -> bool:
        """Check if improvement is significant (>5% or >0.5 points)."""
        return self.score_improvement > 0.5 or self.improvement_percentage > 5.0


class RevisionTracker:
    """Tracks revision attempts and progress over time."""
    
    def __init__(self):
        self.attempts: List[RevisionProgress] = []
        self.start_time: float = time.time()
        self.total_time: float = 0.0
    
    def track_attempt(self, attempt: RevisionProgress) -> None:
        """Track individual revision attempt."""
        self.attempts.append(attempt)
        self.total_time = time.time() - self.start_time
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get summary of all revision attempts."""
        if not self.attempts:
            return {
                "total_attempts": 0,
                "total_improvement": 0.0,
                "average_time_per_attempt": 0.0,
                "final_score": 0.0,
                "initial_score": 0.0,
                "improvement_trend": "none"
            }
        
        initial_score = self.attempts[0].previous_score
        final_score = self.attempts[-1].current_score
        total_improvement = final_score - initial_score
        
        # Calculate improvement trend
        if len(self.attempts) >= 2:
            recent_improvements = [a.score_improvement for a in self.attempts[-2:]]
            if all(imp > 0 for imp in recent_improvements):
                trend = "improving"
            elif all(imp <= 0 for imp in recent_improvements):
                trend = "stagnating"
            else:
                trend = "mixed"
        else:
            trend = "insufficient_data"
        
        return {
            "total_attempts": len(self.attempts),
            "total_improvement": total_improvement,
            "average_time_per_attempt": self.total_time / len(self.attempts),
            "final_score": final_score,
            "initial_score": initial_score,
            "improvement_trend": trend,
            "total_time": self.total_time,
            "successful_attempts": len([a for a in self.attempts if a.is_improvement]),
            "significant_improvements": len([a for a in self.attempts if a.is_significant_improvement])
        }
    
    def get_latest_attempt(self) -> Optional[RevisionProgress]:
        """Get the most recent revision attempt."""
        return self.attempts[-1] if self.attempts else None
    
    def is_plateauing(self, threshold: float = 0.1, window: int = 2) -> bool:
        """Check if improvement has plateaued."""
        if len(self.attempts) < window:
            return False
        
        recent_improvements = [a.score_improvement for a in self.attempts[-window:]]
        return all(abs(imp) < threshold for imp in recent_improvements)


class RevisionLoopController:
    """Orchestrates intelligent revision loops with quality gates and targeted feedback."""
    
    def __init__(self, max_attempts: int = 3, target_score: float = 8.0, min_improvement: float = 0.2):
        self.max_attempts = max_attempts
        self.target_score = target_score
        self.min_improvement = min_improvement
        self.tracker = RevisionTracker()
    
    async def should_continue_revision(self, state: WorkflowState) -> bool:
        """Determine if revision loop should continue based on quality and attempts."""
        # Check max attempts
        if state.revision_attempts >= self.max_attempts:
            return False
        
        # Check if target score is reached
        current_score = state.get_evaluation_score()
        if current_score >= self.target_score:
            return False
        
        # Check for plateauing
        if self.tracker.is_plateauing():
            return False
        
        return True
    
    def get_revision_focus(self, evaluation_result: Dict[str, Any]) -> str:
        """Generate targeted revision instructions based on evaluation results."""
        if not evaluation_result or "scores" not in evaluation_result:
            return "Focus on overall clarity and structure"
        
        # Identify weakest areas
        weak_areas = self._identify_weak_areas(evaluation_result)
        
        # Generate targeted revision prompt
        return self._generate_revision_prompt(weak_areas, evaluation_result)
    
    def _identify_weak_areas(self, evaluation_result: Dict[str, Any]) -> List[Tuple[str, int]]:
        """Identify lowest scoring dimensions for targeted improvement."""
        scores = evaluation_result.get("scores", {})
        if not scores:
            return []
        
        # Convert to list of (dimension, score) tuples and sort by score
        dimension_scores = [
            (dim, score) for dim, score in scores.items()
            if isinstance(score, (int, float))
        ]
        
        # Sort by score (ascending) and return lowest 2-3 dimensions
        dimension_scores.sort(key=lambda x: x[1])
        return dimension_scores[:3]
    
    def _generate_revision_prompt(self, weak_areas: List[Tuple[str, int]], evaluation_result: Dict[str, Any]) -> str:
        """Generate specific revision instructions based on weakest areas."""
        if not weak_areas:
            return "Focus on overall improvement and polish"
        
        # Map dimensions to specific instructions
        dimension_instructions = {
            "clarity": "Improve logical flow and paragraph transitions. Clarify main argument and supporting points.",
            "insight": "Deepen self-reflection and personal growth. Add more specific examples and meaningful insights.",
            "structure": "Strengthen narrative arc and pacing. Improve introduction hook and conclusion impact.",
            "voice": "Enhance authentic personal voice. Add more vivid details and specific examples.",
            "prompt_fit": "Better address the prompt requirements. Ensure all aspects of the question are covered."
        }
        
        # Build focused revision instructions
        instructions = []
        for dimension, score in weak_areas:
            if dimension in dimension_instructions:
                instructions.append(f"{dimension_instructions[dimension]} (Current: {score}/10)")
        
        # Add overall feedback if available
        feedback = evaluation_result.get("feedback", "")
        if feedback:
            instructions.append(f"Additional guidance: {feedback}")
        
        return " ".join(instructions)
    
    async def execute_revision_cycle(self, state: WorkflowState) -> Dict[str, Any]:
        """Execute a complete revision cycle with evaluation and feedback."""
        start_time = time.time()
        
        # Get current draft and essay prompt
        current_draft = state.get_current_draft()
        essay_prompt = state.get_essay_prompt()
        
        if not current_draft:
            return {
                "errors": [*state.errors, "No draft available for revision"],
                "revision_completed": False
            }
        
        try:
            # Step 1: Evaluate current draft
            evaluation_result = await self._evaluate_draft(current_draft, essay_prompt)
            if "error" in evaluation_result:
                return {
                    "errors": [*state.errors, f"Evaluation failed: {evaluation_result['error']}"],
                    "revision_completed": False
                }
            
            current_score = evaluation_result.get("overall_score", 0.0)
            
            # Step 2: Check if revision is needed
            if not await self.should_continue_revision(state):
                return {
                    "revision_completed": True,
                    "revision_needed": False,
                    "final_score": current_score,
                    "reason": "Target score reached or max attempts exceeded"
                }
            
            # Step 3: Generate targeted revision focus
            revision_focus = self.get_revision_focus(evaluation_result)
            
            # Step 4: Execute revision
            revision_result = await self._execute_revision(current_draft, revision_focus, state)
            if "error" in revision_result:
                return {
                    "errors": [*state.errors, f"Revision failed: {revision_result['error']}"],
                    "revision_completed": False
                }
            
            # Step 5: Evaluate revised draft
            revised_draft = revision_result.get("revised_draft", current_draft)
            new_evaluation = await self._evaluate_draft(revised_draft, essay_prompt)
            new_score = new_evaluation.get("overall_score", current_score)
            
            # Step 6: Track progress
            attempt_number = state.revision_attempts + 1
            progress = RevisionProgress(
                attempt_number=attempt_number,
                previous_score=current_score,
                current_score=new_score,
                score_improvement=new_score - current_score,
                focus_areas=revision_focus.split(". ")[0:2],  # Extract first 2 focus areas
                changes_made=revision_result.get("changes", []),
                time_taken=time.time() - start_time,
                evaluation_result=new_evaluation
            )
            
            self.tracker.track_attempt(progress)
            
            # Step 7: Update state
            updated_state = {
                "revision_attempts": attempt_number,
                "quality_scores": {"overall": new_score},
                "data": {
                    **state.data,
                    "tool_outputs": {
                        **state.data.get("tool_outputs", {}),
                        "revise": revision_result,
                        "evaluate": new_evaluation
                    }
                },
                "metadata": {
                    **state.metadata,
                    "revision_progress": progress,
                    "revision_focus": revision_focus,
                    "score_improvement": progress.score_improvement,
                    "revision_summary": self.tracker.get_progress_summary()
                }
            }
            
            return {
                **updated_state,
                "revision_completed": True,
                "revision_needed": True,
                "progress": progress,
                "should_continue": await self.should_continue_revision(state)
            }
            
        except Exception as e:
            return {
                "errors": [*state.errors, f"Revision cycle failed: {str(e)}"],
                "revision_completed": False
            }
    
    async def _evaluate_draft(self, draft: str, essay_prompt: str) -> Dict[str, Any]:
        """Evaluate draft using EssayScoringTool."""
        try:
            result = await TOOL_REGISTRY.acall(
                "essay_scoring",
                essay_text=draft,
                essay_prompt=essay_prompt
            )
            return result if isinstance(result, dict) else {"error": "Invalid evaluation result"}
        except Exception as e:
            return {"error": f"Evaluation failed: {str(e)}"}
    
    async def _execute_revision(self, draft: str, revision_focus: str, state: WorkflowState) -> Dict[str, Any]:
        """Execute revision using RevisionTool."""
        try:
            # Get word count from context
            word_count = state.data.get("context", {}).get("word_limit", 650)
            
            result = await TOOL_REGISTRY.acall(
                "revise",
                draft=draft,
                revision_focus=revision_focus,
                word_count=word_count
            )
            return result if isinstance(result, dict) else {"error": "Invalid revision result"}
        except Exception as e:
            return {"error": f"Revision failed: {str(e)}"}
    
    def get_controller_status(self) -> Dict[str, Any]:
        """Get current controller status and settings."""
        return {
            "max_attempts": self.max_attempts,
            "target_score": self.target_score,
            "min_improvement": self.min_improvement,
            "progress_summary": self.tracker.get_progress_summary(),
            "is_active": len(self.tracker.attempts) > 0,
            "latest_attempt": self.tracker.get_latest_attempt()
        }


@register_workflow_node("revision_loop_controller")
class RevisionLoopNode(WorkflowNode):
    """Workflow node wrapper for the revision loop controller."""
    
    def __init__(self, max_attempts: int = 3, target_score: float = 8.0):
        super().__init__()
        self.controller = RevisionLoopController(max_attempts, target_score)
    
    def get_name(self) -> str:
        """Return node name."""
        return "revision_loop_controller"
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute the revision loop controller."""
        # Convert EssayPlan to WorkflowState
        workflow_state = self._ensure_workflow_state(state)
        
        # Execute revision cycle
        result = await self.controller.execute_revision_cycle(workflow_state)
        
        # Return state updates
        return {
            "data": result.get("data", {}),
            "errors": result.get("errors", []),
            "metadata": result.get("metadata", {}),
            "revision_completed": result.get("revision_completed", False),
            "controller_status": self.controller.get_controller_status()
        }


class RevisionQualityGate:
    """Quality gate that determines revision loop continuation."""
    
    def __init__(self, target_score: float = 8.0, max_attempts: int = 3):
        self.target_score = target_score
        self.max_attempts = max_attempts
    
    def should_continue(self, state: WorkflowState) -> bool:
        """Determine if revision should continue."""
        current_score = state.get_evaluation_score()
        attempts = getattr(state, 'revision_attempts', 0)
        
        # Continue if score is below target and under max attempts
        return current_score < self.target_score and attempts < self.max_attempts
    
    def get_decision_reason(self, state: WorkflowState) -> str:
        """Get human-readable reason for the decision."""
        current_score = state.get_evaluation_score()
        attempts = getattr(state, 'revision_attempts', 0)
        
        if current_score >= self.target_score:
            return f"Target score {self.target_score} reached (current: {current_score})"
        elif attempts >= self.max_attempts:
            return f"Maximum attempts {self.max_attempts} reached"
        else:
            return f"Continue revision (score: {current_score}/{self.target_score}, attempts: {attempts}/{self.max_attempts})"


# Factory functions for easy integration
def create_revision_controller(max_attempts: int = 3, target_score: float = 8.0) -> RevisionLoopController:
    """Create a revision loop controller with specified parameters."""
    return RevisionLoopController(max_attempts, target_score)


def create_quality_gate(target_score: float = 8.0, max_attempts: int = 3) -> RevisionQualityGate:
    """Create a revision quality gate with specified parameters."""
    return RevisionQualityGate(target_score, max_attempts)


async def execute_intelligent_revision_loop(state: WorkflowState, **kwargs) -> Dict[str, Any]:
    """Execute an intelligent revision loop with automatic quality assessment."""
    controller = create_revision_controller(**kwargs)
    return await controller.execute_revision_cycle(state) 