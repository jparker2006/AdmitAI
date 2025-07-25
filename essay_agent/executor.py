"""essay_agent.executor

LangGraph-powered executor that orchestrates a dynamic, planner-driven workflow.
Supports both legacy linear workflow and advanced workflow with branching, quality gates, and revision loops.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal, Optional

from langgraph.graph import StateGraph, END
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
# Legacy imports commented out - using unified state approach
# from .models import EssayPlanner, EssayPlan, Phase, _phase_from_tool
from time import time as _time
from essay_agent.utils.logging import tool_trace


class EssayExecutor:
    """
    Executes essay workflows using LangGraph StateGraph.
    
    Supports two modes:
    1. Legacy Mode: Original planner-driven loop for backward compatibility
    2. Advanced Mode: Branching workflow with quality gates and revision loops
    """

    def __init__(self, mode: Literal["legacy", "advanced"] = "legacy", 
                 monitoring_enabled: bool = False):
        self.mode = mode
        self.registry = TOOL_REGISTRY
        self._planner = EssayPlanner()
        self.monitoring_enabled = monitoring_enabled
        
        if mode == "legacy":
            self._graph = self._build_legacy_graph()
        elif mode == "advanced":
            self._graph = self._build_advanced_graph()
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'legacy' or 'advanced'")

    async def arun(self, user_input: str, context: dict | None = None) -> dict:
        """Asynchronously runs the workflow."""
        if context is None:
            context = {}
        
        # LangGraph expects a dictionary input, which it then maps to the state schema
        if self.mode == "legacy":
            initial_input = {
                "data": {"user_input": user_input, "context": context},
            }
        else:  # advanced mode
            initial_input = {
                "phase": Phase.BRAINSTORMING,
                "data": {
                    "user_input": user_input, 
                    "context": context,
                    "args": self._extract_args_from_context(context),
                },
                "errors": [],
                "metadata": {},
                "revision_attempts": 0,
                "max_revision_attempts": 3,
                "quality_threshold": context.get("quality_threshold", 8.0),
                "current_draft": "",
                "essay_prompt": context.get("essay_prompt", user_input),
            }
        
        final_state = await self._graph.ainvoke(initial_input)
        return final_state

    def _extract_args_from_context(self, context: dict) -> dict:
        """Extract tool arguments from context for advanced mode."""
        return {
            "user_id": context.get("user_id"),
            "word_limit": context.get("word_limit", 650),
            "conversation_history": context.get("conversation_history", []),
            "user_profile": context.get("user_profile", {}),
        }

    def _build_legacy_graph(self) -> StateGraph:
        """Constructs the legacy dynamic LangGraph workflow."""
        workflow = StateGraph(EssayPlan)

        workflow.add_node("planner", self._run_planner)
        workflow.add_node("executor", self._execute_tool)
        
        workflow.set_entry_point("planner")
        
        workflow.add_conditional_edges(
            "executor",
            self._decide_next_step,
            {"continue": "planner", "end": END}
        )
        workflow.add_edge("planner", "executor")

        return workflow.compile()

    def _build_advanced_graph(self) -> StateGraph:
        """Constructs the advanced workflow with branching logic and quality gates."""
        # Import here to avoid circular imports
        from essay_agent.workflows.essay_workflow import AdvancedWorkflowState, AdvancedEssayWorkflow
        
        workflow_engine = AdvancedEssayWorkflow()
        return workflow_engine.build_workflow()

    async def _run_planner(self, state: EssayPlan) -> dict:
        """Runs the planner to decide the next tool and arguments.
        Adds deterministic fallback based on current phase & executed tools to
        guarantee progress during offline tests when the LLM is unavailable or
        returns duplicate actions.
        """
        user_input = state.data.get("user_input", "")
        executed_tools = set(state.data.get("tool_outputs", {}).keys())

        # The 'context' for the planner is the whole state dict --------------
        context = {
            "user_id": state.data.get("context", {}).get("user_id"),
            "word_limit": state.data.get("context", {}).get("word_limit", 650),
            "tool_outputs": state.data.get("tool_outputs", {}),
            "conversation_history": state.data.get("context", {}).get("conversation_history", []),
            "user_profile": state.data.get("context", {}).get("user_profile", {}),
            "phase": state.phase,
        }

        # Deterministic mapping of phase to canonical tool -------------------
        phase_to_tool = {
            Phase.BRAINSTORMING: "brainstorm",
            Phase.OUTLINING: "outline",
            Phase.DRAFTING: "draft",
            Phase.REVISING: "revise",
            Phase.POLISHING: "polish",
        }

        try:
            plan = self._planner.decide_next_action(user_input, context)
        except Exception as e:
            # Deterministic fallback ---------------------------------------
            canonical_tool = phase_to_tool.get(state.phase)
            next_tool = canonical_tool or "finish_workflow"
            plan = EssayPlan(phase=_phase_from_tool(next_tool), data={"next_tool": next_tool, "args": {}})

        current_metadata = state.metadata or {}

        # ---------------------------------------------------------------------
        # Prepare the update dictionary – include new phase so conditional
        # logic can terminate once POLISHING is finished.
        # ---------------------------------------------------------------------
        # Merge existing data while preserving previously established args
        new_data = {**state.data, "next_tool": plan.data.get("next_tool")}
        if plan.data.get("args") is not None:
            new_data["args"] = plan.data["args"]
        update_dict = {
            "phase": plan.phase,
            "data": new_data,
            "metadata": {**current_metadata, "reasoning": plan.metadata.get("reasoning")},
        }
        return update_dict

    async def _execute_tool(self, state: EssayPlan) -> dict:
        """Executes the tool chosen by the planner with retry logic."""
        tool_name = state.data.get("next_tool")
        args = state.data.get("args", {})

        # Always reference the *current* tool registry in case the global
        # registry is monkey-patched during testing.
        from essay_agent.tools import REGISTRY as registry

        if not tool_name or tool_name == "finish_workflow":
            return {"next_tool": "finish_workflow", "args": {}}

        if tool_name not in registry:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        updated_data = dict(state.data)
        updated_errors = list(state.errors or [])
        
        print(f"Attempting to call tool: {tool_name} with args: {args}")
        
        try:
            # Skip execution if args are empty (indicates upstream failure)
            start_ts = _time()
            tool_trace("start", tool_name, args=args)

            if not args:
                print(f"Skipping {tool_name} due to upstream failure")
                result = {"ok": None, "error": f"Skipped {tool_name} due to upstream failure"}
            else:
                # Explicitly create a retrying session for the async tool call
                retryer = AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=2, max=60),
                    reraise=True,  # Reraise the last exception
                )

                # Define the async function to be called by tenacity
                async def tool_call():
                    # Ensure args is a dictionary
                    tool_args = args if isinstance(args, dict) else {}
                    # Registry may be a ToolRegistry instance or a plain dict when
                    # monkey-patched inside tests.  Handle both.
                    if hasattr(registry, "acall"):
                        result = await registry.acall(tool_name, **tool_args)  # type: ignore[attr-defined]
                    else:
                        tool_obj = registry[tool_name]
                        import inspect, asyncio as _asyncio
                        if inspect.iscoroutinefunction(tool_obj):
                            result = await tool_obj(**tool_args)  # type: ignore[misc]
                        else:
                            # Run sync function directly (fast) ------------------
                            result = tool_obj(**tool_args)  # type: ignore[call-arg]
                    return result

                result = await retryer(tool_call)

            tool_trace("end", tool_name, elapsed=_time() - start_ts)

            # Record monitoring metrics if enabled
            if self.monitoring_enabled:
                from essay_agent.utils.logging import performance_log
                execution_time = _time() - start_ts
                success = not (isinstance(result, dict) and result.get("error") is not None)
                
                performance_log(
                    "tool_execution",
                    "executor",
                    metrics={
                        "tool_name": tool_name,
                        "execution_time": execution_time,
                        "success": success,
                        "workflow_id": state.data.get("workflow_id", "unknown")
                    }
                )

            # -----------------------------------------------------------------
            # Check if tool result has an error field (ValidatedTool failure)
            # -----------------------------------------------------------------
            if isinstance(result, dict) and result.get("error") is not None:
                tool_trace("error", tool_name, error=result["error"])
                print(f"Tool {tool_name} failed with internal error: {result['error']}")
                error_message = f"Tool '{tool_name}' failed internally: {result['error']}"
                updated_errors.append(error_message)
                new_phase = state.phase  # Stay in current phase on error
            else:
                # Tool succeeded - advance to next phase
                phase_sequence = [
                    Phase.BRAINSTORMING,
                    Phase.OUTLINING,
                    Phase.DRAFTING,
                    Phase.REVISING,
                    Phase.POLISHING,
                ]
                try:
                    current_index = phase_sequence.index(state.phase)
                    new_phase = phase_sequence[min(current_index + 1, len(phase_sequence) - 1)]
                except ValueError:
                    new_phase = state.phase  # Unknown phase – keep as is
                    
                print(f"Tool {tool_name} executed successfully.")

            # -----------------------------------------------------------------
            # Persist results in two places for backward-compatibility:
            #   1) Flattened at the top-level of ``data`` (legacy tests)
            #   2) Nested under ``tool_outputs`` for modern consumers.
            # -----------------------------------------------------------------
            updated_data[tool_name] = result
            tool_outputs = updated_data.get("tool_outputs", {})
            tool_outputs[tool_name] = result
            updated_data["tool_outputs"] = tool_outputs
            
        except Exception as e:
            tool_trace("error", tool_name, error=str(e))
            print(f"Tool {tool_name} failed with error: {e}")
            error_message = f"Error executing tool '{tool_name}' after retries: {e}"
            updated_errors.append(error_message)
            new_phase = state.phase  # Stay in current phase on error
            
            # Store error result
            result = {"ok": None, "error": str(e)}
            updated_data[tool_name] = result
            tool_outputs = updated_data.get("tool_outputs", {})
            tool_outputs[tool_name] = result
            updated_data["tool_outputs"] = tool_outputs

        return {"data": updated_data, "errors": updated_errors, "phase": new_phase}

    def _decide_next_step(self, state: EssayPlan) -> Literal["continue", "end"]:
        """Determines if the workflow should continue or end."""
        # Terminate automatically if any unrecoverable errors were recorded ----
        if state.errors:
            return "end"

        # Terminate automatically once the POLISHING phase has completed ------
        if state.phase == Phase.POLISHING:
            # Ensure the final polishing tool has actually run ----------------
            if "polish" in (state.data.get("tool_outputs", {})):
                return "end"

        next_tool = state.data.get("next_tool")
        if next_tool == "finish_workflow":
            return "end"

        if state.errors:
            return "end"

        return "continue" 

    async def run_plan_async(self, plan: "EssayPlan") -> "EssayPlan":
        """Execute the plan asynchronously and return the updated EssayPlan.

        This helper is maintained for backward–compatibility with the existing
        test-suite that expects an `EssayPlan` instance to be returned.  Internally
        it merely forwards to the LangGraph workflow and converts the resulting
        state dictionary back into an `EssayPlan` dataclass.
        """
        if self.mode == "advanced":
            # For advanced mode, we need to handle state conversion
            return await self._run_advanced_plan_async(plan)
        
        # Build the initial state mapping expected by LangGraph
        initial_state: Dict[str, Any] = {
            "phase": plan.phase,
            "data": plan.data,
            "errors": plan.errors,
            "metadata": plan.metadata,
        }

        # Invoke the async graph – this will iterate until the planner signals the
        # end of the workflow or an unrecoverable error bubble up.
        final_state: Dict[str, Any] = await self._graph.ainvoke(initial_state)

        # Convert the graph's dict state back into the dataclass expected by callers
        return EssayPlan(
            phase=final_state.get("phase", plan.phase),
            data=final_state.get("data", {}),
            errors=final_state.get("errors", []),
            metadata=final_state.get("metadata", {}),
        )

    async def _run_advanced_plan_async(self, plan: "EssayPlan") -> "EssayPlan":
        """Execute plan using advanced workflow mode."""
        from essay_agent.workflows.essay_workflow import AdvancedWorkflowState
        
        # Convert EssayPlan to AdvancedWorkflowState
        initial_state = AdvancedWorkflowState(
            phase=plan.phase,
            data=plan.data,
            errors=plan.errors or [],
            metadata=plan.metadata or {},
            essay_prompt=plan.data.get("context", {}).get("essay_prompt", ""),
        )

        # Execute advanced workflow
        final_state = await self._graph.ainvoke(initial_state)

        # Convert back to EssayPlan
        return EssayPlan(
            phase=final_state.get("phase", plan.phase),
            data=final_state.get("data", {}),
            errors=final_state.get("errors", []),
            metadata=final_state.get("metadata", {}),
        )

    def run_plan(self, plan: "EssayPlan") -> Dict[str, Any]:
        """Synchronously execute *plan* returning only the tool outputs.

        Historic code – and therefore a sizable portion of the test-suite –
        utilises a blocking `run_plan` method that returns the *dictionary* of
        tool outputs (plus an ``errors`` key when applicable).  Instead of
        refactoring every test we provide this thin synchronous wrapper.
        """
        # Execute the async variant within its own event-loop
        updated_plan: "EssayPlan" = asyncio.run(self.run_plan_async(plan))

        # Collect tool outputs – they are stored under ``tool_outputs`` inside
        # the plan's ``data`` mapping.
        outputs: Dict[str, Any] = dict(updated_plan.data.get("tool_outputs", {}))

        # Propagate errors when present so existing assertions keep working.
        if updated_plan.errors:
            outputs["errors"] = updated_plan.errors

        return outputs

    def set_mode(self, mode: Literal["legacy", "advanced"]) -> None:
        """Switch between legacy and advanced workflow modes."""
        if mode not in ["legacy", "advanced"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'legacy' or 'advanced'")
        
        if mode != self.mode:
            self.mode = mode
            if mode == "legacy":
                self._graph = self._build_legacy_graph()
            else:  # advanced
                self._graph = self._build_advanced_graph()

    def get_mode(self) -> str:
        """Get current workflow mode."""
        return self.mode

    def get_workflow_capabilities(self) -> Dict[str, Any]:
        """Get information about current workflow capabilities."""
        if self.mode == "legacy":
            return {
                "mode": "legacy",
                "supports_branching": False,
                "supports_quality_gates": False,
                "supports_revision_loops": False,
                "max_revision_attempts": 0,
                "quality_threshold": None,
            }
        else:  # advanced
            return {
                "mode": "advanced",
                "supports_branching": True,
                "supports_quality_gates": True,
                "supports_revision_loops": True,
                "max_revision_attempts": 3,
                "quality_threshold": 8.0,
            } 