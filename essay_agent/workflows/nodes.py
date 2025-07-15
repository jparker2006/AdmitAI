"""Concrete workflow node implementations.

This module provides concrete implementations of workflow nodes that can be
used to build complex essay writing workflows.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Callable

from essay_agent.planner import EssayPlan
from essay_agent.workflows.base import WorkflowNode, ConditionalNode, WorkflowState
from essay_agent.workflows import register_workflow_node


class ToolCallNode(WorkflowNode):
    """Node that executes existing tools from the registry."""
    
    def __init__(self, tool_name: str, args_extractor: Optional[Callable[[EssayPlan], Dict[str, Any]]] = None):
        super().__init__()
        self.tool_name = tool_name
        self.args_extractor = args_extractor or self._default_args_extractor
    
    def _default_args_extractor(self, state: EssayPlan) -> Dict[str, Any]:
        """Default arguments extractor from state."""
        return state.data.get("args", {})
    
    def get_name(self) -> str:
        """Return node name."""
        return self._name or f"tool_call_{self.tool_name}"
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute the specified tool."""
        workflow_state = self._ensure_workflow_state(state)
        workflow_state.add_node_execution(self.get_name())
        
        # Import registry dynamically to avoid circular imports
        from essay_agent.tools import REGISTRY as tool_registry
        
        if self.tool_name not in tool_registry:
            error_msg = f"Tool '{self.tool_name}' not found in registry"
            return {
                "errors": [*workflow_state.errors, error_msg],
                "node_history": workflow_state.node_history,
                "metadata": {
                    **workflow_state.metadata,
                    f"{self.get_name()}_error": error_msg,
                }
            }
        
        # Extract arguments for the tool
        tool_args = self.args_extractor(state)
        
        try:
            # Execute the tool
            tool_result = await tool_registry.acall(self.tool_name, **tool_args)
            
            # Update tool outputs in state
            tool_outputs = workflow_state.data.get("tool_outputs", {})
            tool_outputs[self.tool_name] = tool_result
            
            return {
                "data": {
                    **workflow_state.data,
                    "tool_outputs": tool_outputs,
                },
                "node_history": workflow_state.node_history,
                "metadata": {
                    **workflow_state.metadata,
                    f"{self.get_name()}_executed": True,
                    f"{self.get_name()}_result_type": type(tool_result).__name__,
                }
            }
            
        except Exception as e:
            error_msg = f"Tool '{self.tool_name}' execution failed: {str(e)}"
            return {
                "errors": [*workflow_state.errors, error_msg],
                "node_history": workflow_state.node_history,
                "metadata": {
                    **workflow_state.metadata,
                    f"{self.get_name()}_error": error_msg,
                }
            }


class EvaluationNode(WorkflowNode):
    """Node that scores essay quality and provides feedback."""
    
    def __init__(self, evaluation_metrics: List[str] = None):
        super().__init__()
        self.evaluation_metrics = evaluation_metrics or ["overall", "keyword_similarity", "structure", "style"]
    
    def get_name(self) -> str:
        """Return node name."""
        return self._name or "evaluation"
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute essay evaluation."""
        workflow_state = self._ensure_workflow_state(state)
        workflow_state.add_node_execution(self.get_name())
        
        # Import evaluation tools dynamically
        from essay_agent.tools import REGISTRY as tool_registry
        
        quality_scores = {}
        evaluation_results = {}
        
        try:
            # Get current essay content
            tool_outputs = workflow_state.data.get("tool_outputs", {})
            essay_content = None
            
            # Try to get essay from various sources
            if "draft" in tool_outputs:
                essay_content = tool_outputs["draft"].get("essay", "")
            elif "polish" in tool_outputs:
                essay_content = tool_outputs["polish"].get("essay", "")
            elif "revise" in tool_outputs:
                essay_content = tool_outputs["revise"].get("essay", "")
            
            if not essay_content:
                return {
                    "errors": [*workflow_state.errors, "No essay content found for evaluation"],
                    "node_history": workflow_state.node_history,
                }
            
            # Run evaluation metrics
            for metric in self.evaluation_metrics:
                if metric == "overall":
                    # Use essay scoring tool if available
                    if "essay_scoring" in tool_registry:
                        result = await tool_registry.acall("essay_scoring", essay=essay_content)
                        quality_scores["overall"] = result.get("score", 0.0)
                        evaluation_results["overall"] = result
                    else:
                        # Basic word count evaluation as fallback
                        word_count = len(essay_content.split())
                        quality_scores["overall"] = min(word_count / 650, 1.0)  # Normalize to 650 words
                        evaluation_results["overall"] = {"score": quality_scores["overall"], "word_count": word_count}
                
                elif metric == "keyword_similarity":
                    # Calculate keyword similarity if outline exists
                    if "outline" in tool_outputs:
                        outline = tool_outputs["outline"].get("outline", "")
                        # Basic keyword matching (simplified)
                        outline_words = set(outline.lower().split())
                        essay_words = set(essay_content.lower().split())
                        if outline_words:
                            similarity = len(outline_words.intersection(essay_words)) / len(outline_words)
                            quality_scores["keyword_similarity"] = similarity
                            evaluation_results["keyword_similarity"] = {
                                "score": similarity,
                                "matched_words": len(outline_words.intersection(essay_words)),
                                "total_words": len(outline_words)
                            }
                
                elif metric == "structure":
                    # Use structure validator if available
                    if "structure_validator" in tool_registry:
                        result = await tool_registry.acall("structure_validator", essay=essay_content)
                        quality_scores["structure"] = result.get("score", 0.0)
                        evaluation_results["structure"] = result
                    else:
                        # Basic paragraph count evaluation
                        paragraphs = len([p for p in essay_content.split('\n\n') if p.strip()])
                        quality_scores["structure"] = min(paragraphs / 5, 1.0)  # Normalize to 5 paragraphs
                        evaluation_results["structure"] = {"score": quality_scores["structure"], "paragraphs": paragraphs}
                
                elif metric == "style":
                    # Use style analysis if available
                    if "strengthen_voice" in tool_registry:
                        result = await tool_registry.acall("strengthen_voice", essay=essay_content)
                        quality_scores["style"] = result.get("score", 0.7)  # Default decent score
                        evaluation_results["style"] = result
                    else:
                        # Basic sentence variety evaluation
                        sentences = essay_content.split('. ')
                        avg_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
                        quality_scores["style"] = min(avg_length / 15, 1.0)  # Normalize to 15 words per sentence
                        evaluation_results["style"] = {"score": quality_scores["style"], "avg_sentence_length": avg_length}
            
            # Update quality scores in state
            updated_scores = {**workflow_state.quality_scores, **quality_scores}
            
            return {
                "quality_scores": updated_scores,
                "node_history": workflow_state.node_history,
                "metadata": {
                    **workflow_state.metadata,
                    f"{self.get_name()}_results": evaluation_results,
                    f"{self.get_name()}_scores": quality_scores,
                }
            }
            
        except Exception as e:
            error_msg = f"Evaluation failed: {str(e)}"
            return {
                "errors": [*workflow_state.errors, error_msg],
                "node_history": workflow_state.node_history,
                "metadata": {
                    **workflow_state.metadata,
                    f"{self.get_name()}_error": error_msg,
                }
            }


class DecisionNode(ConditionalNode):
    """Node that makes routing decisions based on state."""
    
    def __init__(self, condition_func: Callable[[EssayPlan], bool], true_nodes: List[str], false_nodes: List[str]):
        super().__init__()
        self.condition_func = condition_func
        self.true_nodes = true_nodes
        self.false_nodes = false_nodes
    
    def get_name(self) -> str:
        """Return node name."""
        return self._name or "decision"
    
    def should_continue(self, state: EssayPlan) -> bool:
        """Evaluate the condition function."""
        return self.condition_func(state)
    
    def get_next_nodes(self, state: EssayPlan) -> List[str]:
        """Return next nodes based on condition."""
        if self.should_continue(state):
            return self.true_nodes
        return self.false_nodes


class BranchNode(WorkflowNode):
    """Node that splits workflow into parallel paths."""
    
    def __init__(self, branch_paths: Dict[str, List[str]], branch_selector: Callable[[EssayPlan], str]):
        super().__init__()
        self.branch_paths = branch_paths
        self.branch_selector = branch_selector
    
    def get_name(self) -> str:
        """Return node name."""
        return self._name or "branch"
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute branch logic."""
        workflow_state = self._ensure_workflow_state(state)
        workflow_state.add_node_execution(self.get_name())
        
        try:
            # Select branch based on current state
            selected_branch = self.branch_selector(state)
            
            if selected_branch not in self.branch_paths:
                error_msg = f"Branch '{selected_branch}' not found in branch paths"
                return {
                    "errors": [*workflow_state.errors, error_msg],
                    "node_history": workflow_state.node_history,
                    "metadata": {
                        **workflow_state.metadata,
                        f"{self.get_name()}_error": error_msg,
                    }
                }
            
            # Get the nodes for the selected branch
            branch_nodes = self.branch_paths[selected_branch]
            
            return {
                "node_history": workflow_state.node_history,
                "metadata": {
                    **workflow_state.metadata,
                    f"{self.get_name()}_selected_branch": selected_branch,
                    f"{self.get_name()}_branch_nodes": branch_nodes,
                }
            }
            
        except Exception as e:
            error_msg = f"Branch selection failed: {str(e)}"
            return {
                "errors": [*workflow_state.errors, error_msg],
                "node_history": workflow_state.node_history,
                "metadata": {
                    **workflow_state.metadata,
                    f"{self.get_name()}_error": error_msg,
                }
            }


# ---------------------------------------------------------------------------
# Register default node implementations
# ---------------------------------------------------------------------------

@register_workflow_node("quality_gate_default")
class DefaultQualityGateNode(ConditionalNode):
    """Default quality gate implementation."""
    
    def __init__(self, threshold: float = 0.7):
        super().__init__()
        self.threshold = threshold
    
    def should_continue(self, state: EssayPlan) -> bool:
        """Check if quality threshold is met."""
        workflow_state = self._ensure_workflow_state(state)
        score = workflow_state.get_evaluation_score()
        return score >= self.threshold
    
    def get_next_nodes(self, state: EssayPlan) -> List[str]:
        """Return next nodes based on quality check."""
        if self.should_continue(state):
            return ["finish"]
        return ["revise", "polish"]
    
    def get_name(self) -> str:
        """Return node name."""
        return self._name or f"quality_gate_{self.threshold}"


@register_workflow_node("word_count_decision")
class WordCountDecisionNode(DecisionNode):
    """Decision node based on word count."""
    
    def __init__(self, target_words: int = 650, tolerance: int = 50):
        self.target_words = target_words
        self.tolerance = tolerance
        
        def word_count_condition(state: EssayPlan) -> bool:
            tool_outputs = state.data.get("tool_outputs", {})
            essay_content = ""
            
            if "draft" in tool_outputs:
                essay_content = tool_outputs["draft"].get("essay", "")
            elif "polish" in tool_outputs:
                essay_content = tool_outputs["polish"].get("essay", "")
            
            if not essay_content:
                return False
            
            word_count = len(essay_content.split())
            return abs(word_count - target_words) <= tolerance
        
        super().__init__(
            condition_func=word_count_condition,
            true_nodes=["polish"],
            false_nodes=["revise"]
        )
    
    def get_name(self) -> str:
        """Return node name."""
        return self._name or f"word_count_decision_{self.target_words}" 