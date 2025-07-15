"""Advanced Essay Workflow Engine with Branching Logic and Quality Gates.

This module implements an intelligent workflow engine that supports:
- Conditional workflow paths based on evaluation scores
- Quality gates that trigger revision loops when score < 8/10
- Automatic iteration through revise→polish→evaluate cycles
- Error recovery and fallback mechanisms
- Backward compatibility with existing linear workflow
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal, Optional
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from essay_agent.workflows.base import WorkflowState, WorkflowNode
from essay_agent.workflows import register_workflow_node
from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.planner import EssayPlan, Phase
from essay_agent.utils.logging import tool_trace


@dataclass
class AdvancedWorkflowState(WorkflowState):
    """Enhanced state for advanced workflow with revision tracking."""
    
    # All fields are now inherited from WorkflowState
    # revision_attempts, max_revision_attempts, quality_threshold, current_draft, essay_prompt
    # are already defined in WorkflowState
    
    def __post_init__(self):
        """Ensure proper initialization."""
        super().__post_init__()
        # Additional initialization if needed
        pass
    
    # All methods are now inherited from WorkflowState:
    # - get_evaluation_score()
    # - increment_revision_attempt()
    # - should_continue_revision()
    # - get_current_draft()
    # - get_essay_prompt()


class AdvancedEssayWorkflow:
    """Advanced workflow engine with branching, quality gates, and revision loops."""
    
    def __init__(self):
        self.max_revision_attempts = 3
        self.quality_threshold = 8.0
        self._workflow: Optional[StateGraph] = None
    
    def build_workflow(self) -> StateGraph:
        """Build the advanced workflow with conditional edges and loops."""
        workflow = StateGraph(AdvancedWorkflowState)
        
        # Add all workflow nodes
        workflow.add_node("brainstorm", self._brainstorm_node)
        workflow.add_node("outline", self._outline_node)
        workflow.add_node("draft", self._draft_node)
        workflow.add_node("evaluate", self._evaluate_node)
        workflow.add_node("revise", self._revise_node)
        workflow.add_node("polish", self._polish_node)
        workflow.add_node("qa_validation", self._qa_validation_node)
        workflow.add_node("qa_gate", self._qa_gate_node)
        workflow.add_node("finish", self._finish_node)
        
        # Set entry point
        workflow.set_entry_point("brainstorm")
        
        # Linear progression for initial phases
        workflow.add_edge("brainstorm", "outline")
        workflow.add_edge("outline", "draft")
        workflow.add_edge("draft", "evaluate")
        
        # Conditional edges based on quality gates
        workflow.add_conditional_edges(
            "evaluate",
            self._quality_gate_decision,
            {
                "finish": "qa_validation",
                "revise": "revise",
                "max_attempts": "finish"
            }
        )
        
        # Revision loop edges
        workflow.add_edge("revise", "polish")
        workflow.add_edge("polish", "evaluate")
        
        # QA validation flow
        workflow.add_edge("qa_validation", "qa_gate")
        workflow.add_conditional_edges(
            "qa_gate",
            self._qa_gate_decision,
            {
                "pass": "finish",
                "warning": "finish",
                "fail": "revise"
            }
        )
        
        # Finish node ends workflow
        workflow.add_edge("finish", END)
        
        return workflow.compile()
    
    def _quality_gate_decision(self, state: AdvancedWorkflowState) -> str:
        """Decide workflow path based on evaluation score and attempt count."""
        # Check if we've exceeded max attempts
        if state.revision_attempts >= self.max_revision_attempts:
            return "max_attempts"
        
        # Check if quality threshold is met
        if state.get_evaluation_score() >= self.quality_threshold:
            return "finish"
        
        # Continue revision loop
        return "revise"
    
    async def _brainstorm_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute brainstorming phase."""
        return await self._execute_tool("brainstorm", state)
    
    async def _outline_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute outline phase."""
        return await self._execute_tool("outline", state)
    
    async def _draft_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute draft phase."""
        return await self._execute_tool("draft", state)
    
    async def _evaluate_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute evaluation phase using EssayScoringTool."""
        state.add_node_execution("evaluate")
        
        # Get current draft and prompt
        essay_text = state.get_current_draft()
        essay_prompt = state.get_essay_prompt()
        
        if not essay_text:
            error_msg = "No essay text available for evaluation"
            return {
                "errors": [*state.errors, error_msg],
                "node_history": state.node_history,
                "quality_scores": {"overall": 0.0}
            }
        
        if not essay_prompt:
            # Try to extract from user input or context
            essay_prompt = state.data.get("user_input", "Write a personal essay")
        
        try:
            # Execute evaluation tool
            result = await TOOL_REGISTRY.acall(
                "essay_scoring",
                essay_text=essay_text,
                essay_prompt=essay_prompt
            )
            
            # Extract overall score
            overall_score = 0.0
            if isinstance(result, dict) and "overall_score" in result:
                overall_score = result["overall_score"]
            
            # Update state with evaluation results
            updated_quality_scores = {**state.quality_scores, "overall": overall_score}
            
            # Update tool outputs
            tool_outputs = state.data.get("tool_outputs", {})
            tool_outputs["evaluate"] = result
            
            return {
                "data": {
                    **state.data,
                    "tool_outputs": tool_outputs,
                },
                "quality_scores": updated_quality_scores,
                "node_history": state.node_history,
                "metadata": {
                    **state.metadata,
                    "last_evaluation": result,
                    "evaluation_score": overall_score,
                }
            }
            
        except Exception as e:
            error_msg = f"Evaluation failed: {str(e)}"
            return {
                "errors": [*state.errors, error_msg],
                "node_history": state.node_history,
                "quality_scores": {"overall": 0.0},
                "metadata": {
                    **state.metadata,
                    "evaluation_error": error_msg,
                }
            }
    
    async def _revise_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute revision phase."""
        # Increment revision attempt counter
        updated_revision_attempts = state.revision_attempts + 1
        
        # Execute revision tool
        result = await self._execute_tool("revise", state)
        
        # Add revision attempt tracking
        result["revision_attempts"] = updated_revision_attempts
        
        return result
    
    async def _polish_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute polish phase."""
        return await self._execute_tool("polish", state)
    
    async def _qa_validation_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute QA validation phase."""
        from essay_agent.workflows.qa_pipeline import QAValidationNode
        
        qa_node = QAValidationNode()
        return await qa_node.execute(state)
    
    async def _qa_gate_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute QA gate decision phase."""
        from essay_agent.workflows.qa_pipeline import QAGateNode
        
        qa_gate = QAGateNode()
        return await qa_gate.execute(state)
    
    def _qa_gate_decision(self, state: AdvancedWorkflowState) -> str:
        """Decide workflow path based on QA validation results."""
        # Get QA validation results
        tool_outputs = state.data.get("tool_outputs", {})
        qa_validation = tool_outputs.get("qa_validation", {})
        
        if not qa_validation:
            # No QA validation results - default to pass
            return "pass"
        
        # Check for critical issues
        critical_issues = qa_validation.get("critical_issues", [])
        if critical_issues:
            return "fail"
        
        # Get overall status
        overall_status = qa_validation.get("overall_status", "fail")
        
        # Route based on status
        if overall_status == "pass":
            return "pass"
        elif overall_status == "warning":
            return "warning"
        else:
            return "fail"
    
    async def _finish_node(self, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Finish workflow execution."""
        state.add_node_execution("finish")
        
        # Get QA validation results if available
        qa_results = state.data.get("tool_outputs", {}).get("qa_validation", {})
        
        return {
            "node_history": state.node_history,
            "metadata": {
                **state.metadata,
                "workflow_completed": True,
                "final_score": state.get_evaluation_score(),
                "total_revision_attempts": state.revision_attempts,
                "qa_validation_results": qa_results,
            }
        }
    
    async def _execute_tool(self, tool_name: str, state: AdvancedWorkflowState) -> Dict[str, Any]:
        """Execute a tool with error handling and retry logic."""
        state.add_node_execution(tool_name)
        
        # Get tool arguments from state
        args = state.data.get("args", {})
        
        if tool_name not in TOOL_REGISTRY:
            error_msg = f"Tool '{tool_name}' not found in registry"
            return {
                "errors": [*state.errors, error_msg],
                "node_history": state.node_history,
            }
        
        try:
            # Execute tool with retry logic
            retryer = AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=60),
                reraise=True,
            )
            
            async def tool_call():
                return await TOOL_REGISTRY.acall(tool_name, **args)
            
            start_time = asyncio.get_event_loop().time()
            tool_trace("start", tool_name, args=args)
            
            result = await retryer(tool_call)
            
            end_time = asyncio.get_event_loop().time()
            tool_trace("end", tool_name, elapsed=end_time - start_time)
            
            # Update tool outputs
            tool_outputs = state.data.get("tool_outputs", {})
            tool_outputs[tool_name] = result
            
            return {
                "data": {
                    **state.data,
                    "tool_outputs": tool_outputs,
                },
                "node_history": state.node_history,
                "metadata": {
                    **state.metadata,
                    f"{tool_name}_executed": True,
                    f"{tool_name}_result_type": type(result).__name__,
                }
            }
            
        except Exception as e:
            tool_trace("error", tool_name, error=str(e))
            error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
            
            # Store error result
            tool_outputs = state.data.get("tool_outputs", {})
            tool_outputs[tool_name] = {"error": str(e)}
            
            return {
                "errors": [*state.errors, error_msg],
                "data": {
                    **state.data,
                    "tool_outputs": tool_outputs,
                },
                "node_history": state.node_history,
                "metadata": {
                    **state.metadata,
                    f"{tool_name}_error": error_msg,
                }
            }


@register_workflow_node("advanced_essay_workflow")
class AdvancedEssayWorkflowNode(WorkflowNode):
    """Workflow node wrapper for the advanced essay workflow."""
    
    def __init__(self):
        super().__init__()
        self.workflow_engine = AdvancedEssayWorkflow()
        self._compiled_workflow = None
    
    def get_name(self) -> str:
        """Return node name."""
        return "advanced_essay_workflow"
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute the advanced workflow."""
        # Convert EssayPlan to AdvancedWorkflowState
        workflow_state = self._convert_to_workflow_state(state)
        
        # Get or build compiled workflow
        if self._compiled_workflow is None:
            self._compiled_workflow = self.workflow_engine.build_workflow()
        
        # Execute workflow
        final_state = await self._compiled_workflow.ainvoke(workflow_state)
        
        # Return state updates
        return {
            "data": final_state.get("data", {}),
            "errors": final_state.get("errors", []),
            "metadata": final_state.get("metadata", {}),
        }
    
    def _convert_to_workflow_state(self, state: EssayPlan) -> AdvancedWorkflowState:
        """Convert EssayPlan to AdvancedWorkflowState."""
        return AdvancedWorkflowState(
            phase=state.phase,
            data=state.data,
            errors=state.errors or [],
            metadata=state.metadata or {},
            # Extract context information
            essay_prompt=state.data.get("context", {}).get("essay_prompt", ""),
        ) 