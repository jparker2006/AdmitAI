"""Autonomous Essay Agent - Simple, Working ReAct Implementation

Replaces the broken EssayReActAgent with a reliable, tool-using agent.
This is Section 1.1 of the MVP implementation - a basic working agent that
successfully executes tools and integrates with the existing CLI system.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.memory.smart_memory import SmartMemory
from essay_agent.llm_client import get_chat_llm
from essay_agent.utils.logging import debug_print
from essay_agent.reasoning.bulletproof_reasoning import BulletproofReasoning, ReasoningResult
from essay_agent.tools.integration import build_params, execute_tool, format_tool_result
from essay_agent.intelligence.context_engine import ContextEngine
from essay_agent.tools.smart_orchestrator import SmartOrchestrator
from essay_agent.agents.response_enhancer import ResponseEnhancer

logger = logging.getLogger(__name__)


class ReasoningFallbackError(RuntimeError):
    """Raised when reasoning engine cannot decide and keyword fallback is disabled."""


class AutonomousEssayAgent:
    """Simple, reliable autonomous essay agent with working tool execution.
    
    This agent implements a basic ReAct pattern:
    1. Observe: Extract context from memory and user input
    2. Reason: Simple pattern matching for tool selection
    3. Act: Execute selected tool or default to conversation
    4. Respond: Generate natural language response
    
    Section 1.1 focuses on basic functionality with pattern-based reasoning.
    Future sections will add LLM-based reasoning and advanced features.
    """
    
    def __init__(self, user_id: str):
        """Initialize the autonomous agent.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.tools = TOOL_REGISTRY
        self.llm = get_chat_llm(temperature=float(
    os.getenv("ESSAY_AGENT_LLM_TEMPERATURE", "0.2")
))
        
        # Simple performance tracking
        self.session_start = datetime.now()
        self.interaction_count = 0
        
        # Evaluation tracking (required by evaluation system)
        self.last_execution_tools = []
        self.last_memory_access = []
        
        self.reasoner = BulletproofReasoning()
        self.ctx_engine = ContextEngine(user_id)
        self.memory = SmartMemory(self.user_id)

        # Section 3.1: intelligent orchestration
        self.orchestrator = SmartOrchestrator(
            user_id=self.user_id,
            memory=self.memory,
            context_engine=self.ctx_engine,
            reasoner=self.reasoner,
        )
        
        logger.info(f"AutonomousEssayAgent initialized for user {user_id}")
    
    async def handle_message(self, user_input: str) -> str:
        """Main entry point - handle user message with ReAct loop.
        
        Args:
            user_input: User's message or request
            
        Returns:
            Agent's response
        """
        start_time = datetime.now()
        self.interaction_count += 1
        
        try:
            # === IMMEDIATE MEMORY UPDATE ===
            # Save the user's input immediately so it's available for reasoning.
            self.memory.add_message("user", user_input)

            # ReAct Loop: Observe → Reason → Act → Respond
            context = await self._observe(user_input)
            reasoning = await self._reason(user_input, context)
            action_result = await self._act(reasoning, user_input)
            response = await self._respond(action_result, user_input)
            
            # === POST-RESPONSE MEMORY UPDATE ===
            # Save the agent's response to complete the conversation turn.
            self.memory.add_message("assistant", response)
            
            # learning hook
            self.memory.learn({
                "user_input": user_input,
                "agent_response": response,
                "tool_result": action_result if isinstance(action_result, dict) else {},
            })
            # Enhance tone before returning to user ---------------------------
            context_meta = {
                "college": self.memory.get("college", ""),
                "essay_prompt": self.memory.get("essay_prompt", ""),
            }
            polite_level = int(os.getenv("ESSAY_AGENT_POLITENESS_LEVEL", "1"))
            enhanced = ResponseEnhancer.enhance(response, context=context_meta, politeness_level=polite_level)
            return enhanced
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return "I apologize, but I encountered an error. Let me try to help you in a different way. What would you like to work on with your essay?"
    
    def _sync_snapshot(self, snap):
        # convert to dict & inject session info
        d = snap.model_dump()
        d["session_info"] = {
            "interaction_count": self.interaction_count,
            "session_duration": (datetime.now() - self.session_start).total_seconds(),
        }
        return d

    async def _observe(self, user_input: str) -> Dict[str, Any]:  # noqa: D401
        snap = await self.ctx_engine.snapshot(user_input)
        self.last_memory_access = ["semantic", "working"]
        synced = self._sync_snapshot(snap)
        # Persist latest context so that orchestrator can reuse it
        self._latest_context = synced
        if os.getenv("ESSAY_AGENT_DEBUG_MEMORY") == "1":
            import json as _json
            print("=========MEMORY=========")
            print(_json.dumps(synced, indent=2, default=str))
        return synced
    
    async def _reason(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Decide what action to take using BulletproofReasoning engine.

        Falls back to legacy keyword match when JSON reasoning fails.
        """
        # ------------------------------------------------------------------
        # Unified PlannerPrompt (U4-01)
        # ------------------------------------------------------------------
        from essay_agent.tools import REGISTRY as _registry  # local import to avoid cycles
        from essay_agent.planner_prompt import PlannerPrompt

        planner = PlannerPrompt(list(_registry.keys()))

        # Build context expected by planner prompt --------------------------
        planner_ctx = {
            "last_tool": self.last_execution_tools[-1] if self.last_execution_tools else "none",
            "recent_chat": self.memory.get_recent_chat(k=3),
            "profile": {
                "college": self.memory.get("college", ""),
                "essay_prompt": self.memory.get("essay_prompt", ""),
            },
            # Phase-5 additions --------------------------------------------------
            "tool_stats": "",  # populated later by orchestrator metrics
            "failure_count": getattr(self, "_planner_failures", 0),
        }

        prompt_str = planner.build_prompt(user_input, planner_ctx)

        # Optional observability ------------------------------------------------
        import os, json as _json
        if os.getenv("ESSAY_AGENT_SHOW_PROMPTS") == "1":
            print("\n---- PLANNER PROMPT ----")
            print(prompt_str)

        # Offline stub path -------------------------------------------------
        offline = os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1"
        if offline:
            plan_list = planner.parse_response("{}", offline=True)
        else:
            try:
                raw = await self.llm.apredict(prompt_str)
            except Exception as exc:  # pragma: no cover
                logger.error("Planner LLM call failed: %s", exc)
                raw = "{}"
            plan_list = planner.parse_response(raw, offline=offline)

        if os.getenv("ESSAY_AGENT_SHOW_PROMPTS") == "1":
            print("\n---- RAW PLAN ----")
            print(_json.dumps(plan_list, indent=2))

        return {"action": "tool_plan", "plan": plan_list}

    def _legacy_keyword_reasoning(self, user_input: str) -> Dict[str, Any]:
        """Keyword fallback disabled – always raise."""
        raise ReasoningFallbackError("Keyword reasoning disabled in Section 3+.")
    
    async def _act(self, reasoning: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Execute the chosen action (tool or conversation).
        
        Args:
            reasoning: Result from _reason() 
            
        Returns:
            Action result
        """
        if reasoning.get("action") == "tool_plan":
            plan_list = reasoning.get("plan", [])
            orchestration_result = await self.orchestrator.execute_plan(
                plan_list,
                user_input=user_input,
                context=self._latest_context or {},
            )
            # DEFENSIVE: Handle case where orchestration_result might not be a dict
            if not isinstance(orchestration_result, dict):
                logger.warning("orchestration_result is not a dict: %s", type(orchestration_result))
                return {"type": "conversation", "message": "I had trouble planning the right approach. Let me help you directly."}
            
            steps = orchestration_result.get("steps", [])
            if not steps:
                return {"type": "conversation", "message": "I'm not sure what tool to use next. Could you rephrase?"}
            self.last_execution_tools = [s["tool"] for s in steps]
            last_step = steps[-1]
            return {"type": "tool_result", "tool_name": last_step["tool"], "result": last_step["result"]}

        if reasoning.get("action") == "tool_execution":
            return await self._execute_orchestrated(reasoning, user_input)
        elif reasoning.get("action") == "tool_sequence":
            return await self._execute_sequence(reasoning, user_input)
        else:
            return await self._execute_conversation(reasoning)
    
    async def _execute_tool(self, reasoning: Dict[str, Any], user_input: str = "") -> Dict[str, Any]:
        """Execute a tool using unified EssayAgentState approach.
        
        Args:
            reasoning: Reasoning result with tool information
            
        Returns:
            Tool execution result
        """
        tool_name = reasoning.get("tool_name")
        
        if tool_name not in self.tools:
            logger.warning(f"Tool {tool_name} not found in registry")
            return {
                "type": "error",
                "message": f"I don't have access to the {tool_name} tool right now. Let me help you in another way."
            }
        
        try:
            # Use unified state approach for supported tools
            state_based_tools = ['smart_brainstorm', 'smart_outline', 'smart_polish', 'essay_chat']
            
            if tool_name in state_based_tools:
                result = await self._execute_with_unified_state(tool_name, user_input, reasoning)
            else:
                # Fallback to old parameter mapping for legacy tools
                tool_params = build_params(tool_name, user_id=self.user_id, user_input=user_input, context=reasoning.get("tool_args", {}))
                result = await execute_tool(tool_name, **tool_params)
            
            # Track tool usage for evaluation
            self.last_execution_tools = [tool_name]
            
            return {"type": "tool_result", "tool_name": tool_name, "result": result}
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return {
                "type": "error", 
                "message": f"I had trouble using the {tool_name} tool. Let me try to help you directly."
            }
    
    async def _execute_with_unified_state(self, tool_name: str, user_input: str, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool using unified EssayAgentState approach."""
        from essay_agent.state_manager import EssayStateManager
        from essay_agent.models.agent_state import EssayAgentState
        
        # Get or create state manager
        manager = EssayStateManager()
        
        # Try to load existing state, or create new one
        state = manager.load_state(self.user_id, "current")
        
        if not state:
            # Create initial state from current context
            essay_prompt = self.memory.get("essay_prompt", "")
            college = self.memory.get("college", "")
            
            # If no prompt in memory, try to extract from user input or reasoning
            if not essay_prompt:
                essay_prompt = reasoning.get("tool_args", {}).get("prompt", user_input)
            
            state = manager.create_new_essay(
                user_id=self.user_id,
                essay_prompt=essay_prompt,
                college=college,
                word_limit=650
            )
        
        # Update state with current context
        state.last_user_input = user_input
        if hasattr(self, '_latest_context') and self._latest_context:
            # Extract relevant context updates
            context = self._latest_context
            if context.get("selected_text"):
                state.selected_text = context["selected_text"]
            if context.get("current_focus"):
                state.current_focus = context["current_focus"]
        
        # Get the tool and execute with state
        tool = self.tools[tool_name]
        logger.info(f"Executing {tool_name} with unified state approach")
        
        try:
            result = tool._run(state)
            
            # Save updated state
            manager.save_state(state)
            
            # Add state summary to result for debugging
            result["state_summary"] = state.get_context_summary()
            result["unified_state_used"] = True
            
            return {"ok": result, "error": None}
            
        except Exception as e:
            logger.error(f"Unified state execution failed for {tool_name}: {e}")
            return {"ok": None, "error": str(e)}

    # ------------------------------------------------------------------
    # Section 3.1 – Orchestrated multi-tool execution
    # ------------------------------------------------------------------

    async def _execute_orchestrated(self, reasoning: Dict[str, Any], user_input: str = "") -> Dict[str, Any]:  # noqa: D401,E501
        """Delegate execution to SmartOrchestrator for multi-tool flows."""
        try:
            plan = await self.orchestrator.select_tools(reasoning, self._latest_context or {})
            orchestration_result = await self.orchestrator.execute_plan(
                plan,
                user_input=user_input,
                context=self._latest_context or {},
            )

            # DEFENSIVE: Handle case where orchestration_result might not be a dict
            if not isinstance(orchestration_result, dict):
                logger.warning("orchestration_result is not a dict in _execute_orchestrated: %s", type(orchestration_result))
                return {
                    "type": "error",
                    "message": "I had trouble with the tool orchestration. Let's discuss your essay directly."
                }

            steps = orchestration_result.get("steps", [])
            if not steps:
                return {
                    "type": "error",
                    "message": "I was unable to determine the right tool to help. Let’s discuss instead."
                }

            # Track tools for evaluation
            self.last_execution_tools = [step["tool"] for step in steps]

            last_step = steps[-1]
            return {
                "type": "tool_result",
                "tool_name": last_step["tool"],
                "result": last_step["result"],
            }

        except Exception as exc:  # noqa: BLE001
            logger.error("Smart orchestration failed: %s", exc)
            return {
                "type": "error",
                "message": "I encountered an error orchestrating tools. Let’s try a different approach together."
            }
    
    async def _execute_sequence(self, reasoning: Dict[str, Any], user_input: str = "") -> Dict[str, Any]:  # noqa: D401,E501
        """Execute a sequence of tools in order, returning last result."""
        results = []
        seq = reasoning.get("sequence") or []
        if not seq:
            return {
                "type": "error",
                "message": "Tool sequence was empty; let’s talk instead."
            }

        tool_args = reasoning.get("tool_args", {})

        for tool_name in seq:
            single_reasoning = {
                "tool_name": tool_name,
                "tool_args": tool_args,
            }
            exec_res = await self._execute_tool(single_reasoning, user_input)
            results.append(exec_res)

            # DEFENSIVE: Handle case where exec_res might be a string instead of dict
            if isinstance(exec_res, dict) and exec_res.get("type") == "error":
                # Stop chain on first error
                break
            elif not isinstance(exec_res, dict):
                # If exec_res is not a dict, treat as potential error and stop
                logger.warning("exec_res is not a dict in sequence: %s", type(exec_res))
                break

        self.last_execution_tools = seq

        return {
            "type": "tool_result_sequence",
            "results": results,
        }
    
    async def _execute_conversation(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversational response when no tool is needed.
        
        Args:
            reasoning: Reasoning result
            
        Returns:
            Conversation result
        """
        return {
            "type": "conversation",
            "message": "I'm here to help you with your essay. What specific aspect would you like to work on? I can help with brainstorming ideas, creating outlines, drafting, revising, or polishing your essay."
        }
    
    async def _respond(self, action_result: Dict[str, Any], user_input: str) -> str:
        """Generate natural language response from action result.
        
        Args:
            action_result: Result from _act()
            user_input: Original user input
            
        Returns:
            Natural language response
        """
        # DEFENSIVE: Handle case where action_result might be a string instead of dict
        if isinstance(action_result, str):
            logger.warning("action_result is unexpectedly a string: %s", action_result)
            return action_result
        
        if not isinstance(action_result, dict):
            logger.warning("action_result is not a dict: %s", type(action_result))
            return str(action_result)
        
        result_type = action_result.get("type")
        
        if result_type == "tool_result":
            tool_name = action_result.get("tool_name")
            result = action_result.get("result")
            
            # Use contextual composition instead of simple formatting
            return await self._compose_response(
                tool_name=tool_name,
                tool_result=result,
                user_input=user_input
            )
                
        elif result_type == "tool_result_sequence":
            # Use composition for sequence results (use last successful tool)
            last_ok = next((r for r in reversed(action_result["results"]) if r["type"] == "tool_result"), None)
            if last_ok:
                return await self._compose_response(
                    tool_name=last_ok["tool_name"],
                    tool_result=last_ok["result"],
                    user_input=user_input
                )
            return "I ran several tools but didn't get useful output. Let's discuss further."
        elif result_type == "conversation":
            return action_result.get("message", "How can I help you with your essay?")
            
        elif result_type == "error":
            return action_result.get("message", "I encountered an error, but I'm still here to help!")
            
        else:
            return "I'm here to help you with your essay writing. What would you like to work on?"
    
    async def _compose_response(self, tool_name: str, tool_result: Dict[str, Any], user_input: str) -> str:
        """Compose a natural, contextual response using tool results and full context.
        
        Args:
            tool_name: Name of the tool that was executed
            tool_result: Structured result from the tool
            user_input: Original user input
            
        Returns:
            Natural language response composed with full context
        """
        try:
            # Gather all available context
            from essay_agent.memory import load_user_profile
            user_profile = load_user_profile(self.user_id)
            essay_prompt = self.memory.get("essay_prompt", "")
            college = self.memory.get("college", "")
            recent_chat = self.memory.get_recent_chat(k=3)
            
            # Create comprehensive composition prompt
            composition_prompt = self._build_composition_prompt(
                tool_name=tool_name,
                tool_result=tool_result,
                user_input=user_input,
                user_profile=user_profile,
                essay_prompt=essay_prompt,
                college=college,
                recent_chat=recent_chat
            )
            
            # Generate contextual response using LLM
            response = await self.llm.apredict(composition_prompt)
            return response
            
        except Exception as e:
            logger.error(f"Response composition failed: {e}")
            # Fallback to simple formatting if composition fails
            from essay_agent.tools.integration import format_tool_result
            return format_tool_result(tool_name, tool_result)
    
    def _build_composition_prompt(
        self,
        tool_name: str,
        tool_result: Dict[str, Any],
        user_input: str,
        user_profile: Dict[str, Any],
        essay_prompt: str,
        college: str,
        recent_chat: list
    ) -> str:
        """Build a comprehensive prompt for response composition.
        
        Args:
            tool_name: Name of the executed tool
            tool_result: Structured tool output
            user_input: User's original request
            user_profile: User's profile and background
            essay_prompt: Current essay prompt
            college: Target college
            recent_chat: Recent conversation history
            
        Returns:
            Formatted prompt for LLM composition
        """
        # Extract user details safely
        user_info = user_profile.get("user_info", {})
        user_name = user_info.get("name", "the student")
        intended_major = user_info.get("intended_major", "")
        
        # Extract defining moments and activities
        defining_moments = user_profile.get("defining_moments", [])
        activities = user_profile.get("academic_profile", {}).get("activities", [])
        
        # Build context sections
        user_context = f"""
USER PROFILE:
- Name: {user_name}
- Intended Major: {intended_major}
- Target College: {college}
- Key Activities: {', '.join([act.get('name', '') for act in activities[:3]])}
- Notable Experiences: {len(defining_moments)} defining moments in profile
"""
        
        essay_context = f"""
ESSAY CONTEXT:
- College: {college}
- Prompt: "{essay_prompt}"
- Type: College application essay
"""
        
        tool_context = f"""
TOOL EXECUTION:
- Tool Used: {tool_name}
- User Request: "{user_input}"
- Tool Output: {tool_result}
"""
        
        conversation_context = ""
        if recent_chat:
            conversation_context = f"""
RECENT CONVERSATION:
{chr(10).join([f"- {msg}" for msg in recent_chat[-3:]])}
"""
        
        prompt = f"""You are an expert college essay coach having a personalized conversation with a student. 

{user_context}

{essay_context}

{tool_context}

{conversation_context}

TASK: Compose a natural, helpful response that:
1. Acknowledges the student's background and goals
2. References the specific essay prompt and college
3. Presents the tool results in a conversational, coach-like manner
4. Provides guidance and next steps
5. Feels personal and authentic, not robotic

The response should sound like an experienced counselor who knows this student well, not like a tool output formatter.

RESPONSE:"""
        
        return prompt
    
    def _update_memory(self, user_input: str, response: str) -> None:
        """Update memory with this interaction.
        
        Args:
            user_input: User's input
            response: Agent's response
        """
        try:
            # Record the chat turn in working memory
            # Keys expected by JSONConversationMemory are "human" and "ai"
            self.memory.add_chat_turn({"human": user_input}, {"ai": response})

            # Persist semantic/episodic tiers as well so preferences stick
            self.memory.save()

            logger.debug("Memory updated for user %s", self.user_id)
        except Exception as exc:
            logger.warning("Memory update failed: %s", exc)
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get session performance metrics for debugging.
        
        Returns:
            Dictionary with session metrics
        """
        total_time = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "interaction_count": self.interaction_count,
            "session_duration": total_time,
            "interactions_per_minute": (self.interaction_count / max(total_time / 60, 1)),
            "average_response_time": total_time / max(self.interaction_count, 1),
            "tools_used": list(set(self.last_execution_tools)) if self.last_execution_tools else [],
            "memory_accessed": list(set(self.last_memory_access)) if self.last_memory_access else []
        }


# For evaluation system compatibility
async def create_autonomous_agent(user_id: str) -> AutonomousEssayAgent:
    """Factory function for creating autonomous agents."""
    return AutonomousEssayAgent(user_id) 