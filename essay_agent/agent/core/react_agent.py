"""Main ReAct agent implementation.

This module contains the core EssayReActAgent class that implements the
ReAct pattern (Reasoning, Acting, Observing) for essay writing assistance.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple
from datetime import datetime

# Import agent infrastructure components
from essay_agent.agent.memory.agent_memory import AgentMemory
from essay_agent.agent.prompt_builder import PromptBuilder
from essay_agent.agent.prompt_optimizer import PromptOptimizer
from essay_agent.agent.tools.tool_registry import ENHANCED_REGISTRY
from essay_agent.agent.tools.tool_descriptions import TOOL_DESCRIPTIONS
from essay_agent.llm_client import get_chat_llm, call_llm

# Import new ReAct components
from .reasoning_engine import ReasoningEngine, ReasoningResult, ReasoningError
from .action_executor import ActionExecutor, ActionResult, ActionExecutionError

# Import new LLM-driven components for Phase 2
from essay_agent.prompts.response_generation import response_generator
from essay_agent.prompts.tool_selection import comprehensive_tool_selector
from essay_agent.memory.user_context_extractor import context_extractor
from essay_agent.agent.school_context_injector import school_injector

logger = logging.getLogger(__name__)


class EssayReActAgent:
    """True ReAct agent for essay writing assistance.
    
    This agent implements the ReAct pattern:
    1. Observe: Get current context from memory
    2. Reason: Use LLM to decide what action to take
    3. Act: Execute chosen tools or engage in conversation
    4. Respond: Generate natural language response
    
    The agent integrates sophisticated memory, prompt optimization, tool execution,
    and error handling to provide intelligent essay writing assistance.
    """
    
    def __init__(self, user_id: str):
        """Initialize the ReAct agent with all components.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        
        # Initialize core components from completed tasks
        self.memory = AgentMemory(user_id)
        self.prompt_builder = PromptBuilder(self.memory, TOOL_DESCRIPTIONS)
        self.prompt_optimizer = PromptOptimizer(self.memory)
        self.reasoning_engine = ReasoningEngine(self.prompt_builder, self.prompt_optimizer)
        self.action_executor = ActionExecutor(ENHANCED_REGISTRY, self.memory)
        
        # Initialize new LLM-driven components for Phase 2
        self.response_generator = response_generator
        self.tool_selector = comprehensive_tool_selector
        self.context_extractor = context_extractor
        self.school_injector = school_injector
        
        # Performance tracking
        self.session_start = datetime.now()
        self.interaction_count = 0
        self.total_response_time = 0.0
        
        # Evaluation tracking attributes (required by conversation_runner)
        self.last_execution_tools = []
        self.last_memory_access = []
        
        # BUGFIX: Track actual memory access during current turn
        self.current_turn_memory_access = []
        
        # Phase 2: Response deduplication and context tracking
        self.recent_responses = []  # Track recent responses for deduplication
        self.conversation_context = {}  # Track extracted user context
        self.scenario_context = {}  # Track scenario information (school, etc.)
        
        logger.info(f"EssayReActAgent initialized for user {user_id}")
        
    async def handle_message(self, user_input: str) -> str:
        """Main ReAct loop: Observe → Reason → Act → Respond.
        
        This is the core method that implements the complete ReAct pattern,
        providing intelligent responses to user messages through context-aware
        reasoning and action execution.
        
        Args:
            user_input: User's message or request
            
        Returns:
            Natural language response from the agent
        """
        start_time = time.time()
        self.interaction_count += 1
        
        # BUGFIX: Reset memory access tracking for this turn
        self.current_turn_memory_access = []
        
        try:
            logger.info(f"Starting ReAct interaction #{self.interaction_count}: {user_input[:100]}...")
            
            # PHASE 2 ENHANCEMENT: Extract user context and detect school mentions
            await self._extract_and_update_context(user_input)
            
            # 1. OBSERVE: Get current context
            context = self._observe()
            logger.debug(f"Observed context with {len(context)} elements")
            
            # 2. REASON: Determine what action to take
            reasoning = await self._reason(user_input, context)
            logger.debug(f"Reasoning completed: {reasoning.response_type} with confidence {reasoning.confidence}")
            
            # 3. ACT: Execute the chosen action
            action_result = await self._act(reasoning)
            logger.debug(f"Action executed: {action_result.action_type} success={action_result.success}")
            
            # Update tracking attributes for evaluation
            self._update_tracking_attributes(action_result, reasoning)
            
            # 4. RESPOND: Generate natural language response
            response = await self._respond(user_input, reasoning, action_result)
            
            # Track performance and update memory
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            await self._update_interaction_memory(user_input, response, reasoning, action_result, response_time)
            
            logger.info(f"Interaction completed in {response_time:.2f}s")
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            logger.error(f"ReAct loop failed after {response_time:.2f}s: {e}")
            return self._generate_error_response(user_input, e)
        
    def _observe(self) -> Dict[str, Any]:
        """Get current context from memory.
        
        This method assembles comprehensive context for reasoning, including
        user profile, conversation history, essay state, and relevant memories.
        
        Returns:
            Dictionary containing user profile, essay state, conversation history, etc.
        """
        try:
            # BUGFIX: Track memory access during retrieval
            context = self._retrieve_context_with_tracking()
            
            # Add session information
            context["session_info"] = {
                "interaction_count": self.interaction_count,
                "session_duration": (datetime.now() - self.session_start).total_seconds(),
                "avg_response_time": self.total_response_time / max(self.interaction_count, 1)
            }
            
            # Add agent performance metrics
            context["agent_metrics"] = {
                "reasoning_stats": self.reasoning_engine.get_performance_metrics(),
                "execution_stats": self.action_executor.get_performance_metrics()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Context observation failed: {e}")
            # Return minimal context on failure
            return {
                "user_profile": {},
                "conversation_history": [],
                "essay_state": {},
                "session_info": {"interaction_count": self.interaction_count}
            }

    def _retrieve_context_with_tracking(self) -> Dict[str, Any]:
        """Retrieve context from memory while tracking actual access patterns.
        
        Returns:
            Context dictionary with memory access tracking
        """
        context = {}
        
        # Track user profile access
        try:
            if hasattr(self.memory, 'get_user_profile'):
                user_profile = self.memory.get_user_profile()
                if user_profile:
                    context["user_profile"] = user_profile
                    self._track_memory_access("user_profile", f"Retrieved profile for {self.user_id}")
                else:
                    context["user_profile"] = {}
            else:
                context["user_profile"] = {}
        except Exception as e:
            logger.warning(f"Failed to access user profile: {e}")
            context["user_profile"] = {}
        
        # Track conversation history access
        try:
            if hasattr(self.memory, 'get_recent_history'):
                history = self.memory.get_recent_history(turns=5)
                if history:
                    context["conversation_history"] = history
                    self._track_memory_access("conversation_history", f"Retrieved {len(history)} conversation turns")
                else:
                    context["conversation_history"] = []
            else:
                context["conversation_history"] = []
        except Exception as e:
            logger.warning(f"Failed to access conversation history: {e}")
            context["conversation_history"] = []
        
        # Track reasoning chains access
        try:
            if hasattr(self.memory, 'recent_reasoning_chains') and self.memory.recent_reasoning_chains:
                context["reasoning_chains"] = self.memory.recent_reasoning_chains[-3:]  # Last 3 chains
                self._track_memory_access("reasoning_chains", f"Retrieved {len(context['reasoning_chains'])} reasoning chains")
            else:
                context["reasoning_chains"] = []
        except Exception as e:
            logger.warning(f"Failed to access reasoning chains: {e}")
            context["reasoning_chains"] = []
        
        # Track tool execution history
        try:
            if hasattr(self.memory, 'recent_tool_executions') and self.memory.recent_tool_executions:
                context["tool_history"] = self.memory.recent_tool_executions[-5:]  # Last 5 executions
                self._track_memory_access("tool_history", f"Retrieved {len(context['tool_history'])} tool executions")
            else:
                context["tool_history"] = []
        except Exception as e:
            logger.warning(f"Failed to access tool history: {e}")
            context["tool_history"] = []
        
        # Get current essay state if available
        try:
            # Try to get essay state from context manager or memory
            if hasattr(self.memory, 'context_manager') and self.memory.context_manager:
                essay_state = self.memory.context_manager.get_current_state()
                if essay_state:
                    context["essay_state"] = essay_state
                    self._track_memory_access("essay_state", f"Retrieved current essay state")
                else:
                    context["essay_state"] = {}
            else:
                context["essay_state"] = {}
        except Exception as e:
            logger.warning(f"Failed to access essay state: {e}")
            context["essay_state"] = {}
        
        return context
    
    def _track_memory_access(self, access_type: str, description: str) -> None:
        """Track actual memory access with details.
        
        Args:
            access_type: Type of memory accessed (user_profile, conversation_history, etc.)
            description: Description of what was accessed
        """
        access_record = {
            "type": access_type,
            "timestamp": time.time(),
            "description": description
        }
        self.current_turn_memory_access.append(access_record)
        logger.debug(f"Memory access tracked: {access_type} - {description}")
        
    async def _reason(self, user_input: str, context: Dict[str, Any]) -> ReasoningResult:
        """Use LLM to reason about what action to take.
        
        This method leverages the ReasoningEngine to generate sophisticated
        reasoning about the appropriate response to the user's input.
        
        Args:
            user_input: User's request
            context: Current context from observation
            
        Returns:
            ReasoningResult with action decision and confidence metrics
        """
        try:
            # Add user input to context for reasoning
            enhanced_context = {**context, "current_input": user_input}
            
            # Use reasoning engine for sophisticated LLM reasoning
            reasoning = await self.reasoning_engine.reason_about_action(
                user_input=user_input,
                context=enhanced_context
            )
            
            return reasoning
            
        except ReasoningError as e:
            logger.error(f"Reasoning failed: {e}")
            # Fallback to simple reasoning
            return ReasoningResult(
                context_understanding=f"User said: {user_input}",
                reasoning="Unable to perform sophisticated reasoning, falling back to conversation",
                chosen_tool=None,
                tool_args={},
                confidence=0.3,
                response_type="conversation",
                anticipated_follow_up="Provide helpful guidance",
                context_flags=["reasoning_error"],
                reasoning_time=0.0,
                prompt_version="fallback"
            )
        
    async def _act(self, reasoning: ReasoningResult) -> ActionResult:
        """Execute the chosen action.
        
        This method uses the ActionExecutor to perform the action determined
        by the reasoning phase, with comprehensive error handling.
        
        Args:
            reasoning: Result from reasoning phase
            
        Returns:
            ActionResult with execution details and results
        """
        try:
            # Convert ReasoningResult to dict for ActionExecutor
            reasoning_dict = {
                "response_type": reasoning.response_type,
                "chosen_tool": reasoning.chosen_tool,
                "tool_args": reasoning.tool_args,
                "reasoning": reasoning.reasoning,
                "confidence": reasoning.confidence,
                "context": {}  # ActionExecutor will get context from memory
            }
            
            # Execute action using ActionExecutor
            action_result = await self.action_executor.execute_action(reasoning_dict)
            
            return action_result
            
        except ActionExecutionError as e:
            logger.error(f"Action execution failed: {e}")
            # Return error result
            return ActionResult(
                action_type="error",
                success=False,
                result=None,
                execution_time=0.0,
                error_message=str(e),
                recovery_suggestion="Let's try a different approach."
            )
        
    async def _respond(self, user_input: str, reasoning: ReasoningResult, action_result: ActionResult) -> str:
        """Generate natural response with LLM-driven enhancements.
        
        This method uses the intelligent response generation system to create
        contextual, unique responses that integrate user details and avoid duplication.
        
        Args:
            user_input: Original user request
            reasoning: Agent's reasoning
            action_result: Result from action phase
            
        Returns:
            Enhanced natural language response
        """
        try:
            if action_result.success:
                if action_result.action_type == "tool_execution":
                    # Use intelligent response generator with context and deduplication
                    response = await self.response_generator.generate_contextual_response(
                        user_input=user_input,
                        tool_result=action_result.result,
                        conversation_history=self.memory.get_recent_history(5),
                        user_profile=self.memory.get_user_profile(),
                        previous_responses=self.recent_responses,
                        school_context=self.scenario_context.get('school_context')
                    )
                    
                    # Add school-specific context if relevant
                    if school_name := self._extract_school_name(user_input):
                        response = await self.school_injector.inject_school_context(
                            response=response,
                            school_name=school_name,
                            user_interests=self._get_user_interests(),
                            user_context=self.conversation_context,
                            response_type=action_result.tool_name if hasattr(action_result, 'tool_name') else 'general'
                        )
                    
                    # Cache response for deduplication
                    self._cache_response(response)
                    
                    return response
                    
                elif action_result.action_type == "conversation":
                    # Enhanced conversational response
                    response = await self._generate_contextual_conversation(user_input, reasoning)
                    self._cache_response(response)
                    return response
                else:
                    return self._generate_default_response()
            else:
                return self._format_error_response(action_result, user_input)
                
        except Exception as e:
            logger.error(f"Enhanced response generation failed: {e}")
            return self._generate_fallback_response(user_input)
    
    async def _format_tool_response(self, action_result: ActionResult, reasoning: ReasoningResult) -> str:
        """Format response using intelligent LLM-based dynamic formatting.
        
        This method uses an LLM to transform any tool result into beautiful,
        context-aware, human-readable responses that adapt to the user's intent.
        
        Args:
            action_result: Successful tool execution result
            reasoning: Original reasoning with user context
            
        Returns:
            Beautifully formatted response string
        """
        # Handle empty results with fallback
        if not action_result.result:
            return f"✅ I've completed the {action_result.tool_name} operation. How would you like to proceed?"
        
        # Use LLM-based dynamic formatting
        try:
            return await self._format_with_llm(action_result, reasoning)
        except Exception as e:
            logger.warning(f"LLM formatting failed for {action_result.tool_name}: {e}")
            # Fallback to simple but safe formatting
            return self._format_fallback(action_result)

    # =========================================================================
    # LLM-Powered Dynamic Formatting System
    # =========================================================================
    
    async def _format_with_llm(self, action_result: ActionResult, reasoning: ReasoningResult) -> str:
        """Use LLM to intelligently format tool results into beautiful responses.
        
        This method leverages the LLM's natural language understanding to create
        contextually appropriate, engaging responses for any tool output.
        
        Args:
            action_result: Tool execution result to format
            reasoning: Context about user intent and reasoning
            
        Returns:
            Beautifully formatted response string
        """
        # Build context-aware formatting prompt
        formatting_prompt = self._build_formatting_prompt(action_result, reasoning)
        
        # Get LLM response with proper error handling
        try:
            # Get LLM instance and call with correct signature
            llm = get_chat_llm()
            response = call_llm(llm, formatting_prompt, temperature=0.7, max_tokens=1000)
            
            # Validate and clean response
            if response and len(response.strip()) > 20:
                return response.strip()
            else:
                logger.warning(f"LLM returned insufficient response for {action_result.tool_name}")
                return self._format_fallback(action_result)
                
        except Exception as e:
            logger.error(f"LLM call failed during formatting: {e}")
            return self._format_fallback(action_result)
    
    def _build_formatting_prompt(self, action_result: ActionResult, reasoning: ReasoningResult) -> str:
        """Build intelligent formatting prompt for the LLM.
        
        Args:
            action_result: Tool execution result
            reasoning: User context and reasoning
            
        Returns:
            Carefully crafted prompt for optimal formatting
        """
        # Extract tool information
        tool_name = action_result.tool_name
        tool_result = action_result.result
        user_context = reasoning.context_understanding
        user_reasoning = reasoning.reasoning
        
        # Handle nested structures (like brainstorm tool)
        result_json = self._prepare_result_for_prompt(tool_result)
        
        prompt = f"""You are an expert essay writing assistant. Transform this technical tool output into a beautiful, engaging response for the user.

CONTEXT:
- User Context: {user_context}
- Assistant Reasoning: {user_reasoning}
- Tool Executed: {tool_name}
- Tool Success: {action_result.success}

RAW TOOL OUTPUT:
{result_json}

FORMATTING REQUIREMENTS:
1. Use engaging markdown formatting (### headers, **bold**, bullet points)
2. Start with an appropriate emoji and compelling headline
3. Organize information with clear visual hierarchy
4. Explain results in context of what the user wanted
5. Highlight key insights and actionable information
6. End with specific, helpful next steps
7. Maintain an encouraging, professional tone
8. Make it scannable and easy to read

EXAMPLES OF GREAT FORMATTING:
- "✨ **I've brainstormed compelling story ideas for you:**"
- "🎯 **Story Analysis Complete:**"
- "📝 **Draft Complete:**"
- Use "---" as section dividers
- Include "**What's next?**" with concrete suggestions

Transform the tool output into a beautiful response that helps the user move forward with their essay:"""

        return prompt
    
    def _prepare_result_for_prompt(self, result: Any) -> str:
        """Prepare tool result for inclusion in LLM prompt.
        
        Args:
            result: Raw tool result
            
        Returns:
            Clean JSON string for prompt
        """
        try:
            # Handle nested structures gracefully
            if isinstance(result, dict):
                # Extract meaningful content from nested structures
                if 'ok' in result and isinstance(result['ok'], dict):
                    # For brainstorm tool format: {'ok': {...}, 'error': None}
                    content = result['ok']
                    error = result.get('error')
                    if error:
                        content['_error'] = error
                    return json.dumps(content, indent=2)
                else:
                    return json.dumps(result, indent=2)
            else:
                return json.dumps({"content": str(result)}, indent=2)
        except Exception:
            return f"{{\"content\": \"{str(result)}\"}}"
    
    def _format_fallback(self, action_result: ActionResult) -> str:
        """Provide safe fallback formatting when LLM formatting fails.
        
        Args:
            action_result: Tool execution result
            
        Returns:
            Simple but safe formatted response
        """
        tool_name = action_result.tool_name.replace('_', ' ').title()
        
        if isinstance(action_result.result, dict):
            # Try to extract meaningful content
            result = action_result.result
            
            # Handle brainstorm tool nested structure
            if 'ok' in result and isinstance(result['ok'], dict):
                stories = result['ok'].get('stories', [])
                if stories:
                    formatted = f"✅ **{tool_name} Complete - {len(stories)} ideas generated:**\n\n"
                    for i, story in enumerate(stories[:3], 1):  # Show first 3
                        title = story.get('title', f'Idea {i}')
                        description = story.get('description', '')[:100] + '...' if len(story.get('description', '')) > 100 else story.get('description', '')
                        formatted += f"**{i}. {title}**\n{description}\n\n"
                    formatted += "I can help you develop any of these ideas further!"
                    return formatted
            
            # Generic dict formatting
            if 'content' in result:
                return f"✅ **{tool_name} Complete:**\n\n{result['content']}\n\nHow would you like to proceed?"
        
        # Final fallback
        return f"✅ **{tool_name} Complete** - Results are ready! How would you like to proceed?"

    # =========================================================================
    # Legacy Manual Formatter Methods - REMOVED
    # =========================================================================
    # 
    # All manual tool-specific formatters have been replaced by the intelligent
    # LLM-based dynamic formatting system above. This reduces the codebase by
    # 600+ lines and provides better, more contextual formatting for any tool.
    # 
    # The LLM-based system automatically handles:
    # - Brainstorm results with beautiful story presentations
    # - Evaluation results with score visualizations  
    # - Draft results with organized content sections
    # - Any new tool without manual coding
    #
    # =========================================================================

    def _format_error_response(self, action_result: ActionResult, user_input: str) -> str:
        """Format response for failed actions.
        
        Args:
            action_result: Failed action result
            user_input: Original user input
            
        Returns:
            Helpful error response
        """
        if action_result.recovery_suggestion:
            return f"I encountered an issue, but don't worry! {action_result.recovery_suggestion}"
        else:
            return "I ran into a small hiccup, but I'm still here to help! Could you let me know what specific aspect of your essay you'd like to work on?"
    
    def _generate_default_response(self) -> str:
        """Generate default helpful response."""
        return "I'm here to help you with your essay! We can work on brainstorming ideas, creating an outline, drafting content, or polishing your writing. What feels like the right next step for you?"
    
    def _generate_error_response(self, user_input: str, error: Exception) -> str:
        """Generate response for system errors.
        
        Args:
            user_input: User's original input
            error: The exception that occurred
            
        Returns:
            Graceful error response
        """
        logger.error(f"System error in ReAct loop: {error}")
        return "I'm experiencing some technical difficulties, but I'm still here to help! Could you tell me what you'd like to work on with your essay, and I'll do my best to assist you."
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """Generate helpful essay-specific fallback response.
        
        Args:
            user_input: User's input
            
        Returns:
            Helpful essay-specific response
        """
        return self._generate_helpful_fallback(user_input, "system_fallback")
    
    async def _update_interaction_memory(
        self,
        user_input: str,
        response: str,
        reasoning: ReasoningResult,
        action_result: ActionResult,
        response_time: float
    ) -> None:
        """Update memory with interaction details.
        
        Args:
            user_input: User's input
            response: Agent's response
            reasoning: Reasoning result
            action_result: Action execution result
            response_time: Total response time
        """
        try:
            # Store conversation turn
            await self.memory.store_conversation_turn(
                user_input=user_input,
                agent_response=response,
                metadata={
                    "reasoning": reasoning,
                    "action_result": action_result,
                    "response_time": response_time,
                    "interaction_count": self.interaction_count
                }
            )
            
            # Store reasoning chain
            self.memory.store_reasoning_chain(
                user_input=user_input,
                reasoning_steps=[{
                    "step": "reason",
                    "content": reasoning.reasoning,
                    "confidence": reasoning.confidence,
                    "time": reasoning.reasoning_time
                }, {
                    "step": "act",
                    "content": action_result.action_type,
                    "success": action_result.success,
                    "time": action_result.execution_time
                }],
                final_action=action_result.action_type,
                success=action_result.success
            )
            
        except Exception as e:
            logger.warning(f"Failed to update interaction memory: {e}")
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get comprehensive session performance metrics.
        
        Returns:
            Dictionary with session statistics
        """
        session_duration = (datetime.now() - self.session_start).total_seconds()
        avg_response_time = self.total_response_time / max(self.interaction_count, 1)
        
        return {
            "session_duration": session_duration,
            "interaction_count": self.interaction_count,
            "total_response_time": self.total_response_time,
            "average_response_time": avg_response_time,
            "reasoning_metrics": self.reasoning_engine.get_performance_metrics(),
            "execution_metrics": self.action_executor.get_performance_metrics(),
            "interactions_per_minute": (self.interaction_count / session_duration) * 60 if session_duration > 0 else 0
        }
    
    def _update_tracking_attributes(self, action_result: ActionResult, reasoning: 'ReasoningResult') -> None:
        """Update tracking attributes for evaluation framework.
        
        Args:
            action_result: Result from action execution
            reasoning: Reasoning result that led to action
        """
        try:
            # Clear previous tracking
            self.last_execution_tools = []
            
            # Track tool execution
            if action_result.action_type == "tool_execution" and action_result.tool_name:
                self.last_execution_tools = [action_result.tool_name]
                logger.debug(f"Tracked tool execution: {action_result.tool_name}")
            
            # BUGFIX: Use actual memory access tracking instead of heuristics
            # Convert current turn memory access to the format expected by evaluation system
            self.last_memory_access = [access["type"] for access in self.current_turn_memory_access]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_accesses = []
            for access_type in self.last_memory_access:
                if access_type not in seen:
                    unique_accesses.append(access_type)
                    seen.add(access_type)
            self.last_memory_access = unique_accesses
                    
        except Exception as e:
            logger.warning(f"Failed to update tracking attributes: {e}")
            # Ensure attributes exist even if tracking fails
            if not hasattr(self, 'last_execution_tools'):
                self.last_execution_tools = []
            if not hasattr(self, 'last_memory_access'):
                self.last_memory_access = []
    
    def _generate_helpful_fallback(self, user_input: str, failed_action: str) -> str:
        """Generate helpful essay-specific response when tools fail.
        
        Args:
            user_input: User's original input
            failed_action: Description of what failed
            
        Returns:
            Helpful essay-specific guidance
        """
        user_input_lower = user_input.lower()
        
        # Check for specific essay assistance needs
        if any(word in user_input_lower for word in ['outline', 'structure', 'organize']):
            return self._help_with_outline_structure(user_input)
        elif any(word in user_input_lower for word in ['story', 'narrative', 'experience', 'moment']):
            return self._help_with_narrative_development(user_input)
        elif any(word in user_input_lower for word in ['detail', 'vivid', 'scene', 'description']):
            return self._help_with_vivid_details(user_input)
        elif any(word in user_input_lower for word in ['hook', 'opening', 'start', 'beginning']):
            return self._help_with_opening_hooks(user_input)
        elif any(word in user_input_lower for word in ['conclusion', 'ending', 'reflect', 'insights']):
            return self._help_with_reflection(user_input)
        elif any(word in user_input_lower for word in ['brainstorm', 'ideas', 'topics']):
            return self._help_with_brainstorming(user_input)
        elif any(word in user_input_lower for word in ['improve', 'better', 'stronger', 'revise']):
            return self._help_with_improvement(user_input)
        else:
            return self._general_essay_assistance(user_input)
    
    def _help_with_outline_structure(self, user_input: str) -> str:
        """Provide guidance on essay structure and outlining."""
        return """I'd love to help you with essay structure! Here's a proven approach for college essays:

**5-Part Structure:**
1. **Hook** - Start with an engaging moment or image
2. **Context** - Provide necessary background 
3. **Conflict/Challenge** - Describe the central tension
4. **Growth** - Show what you learned or how you changed
5. **Reflection** - Connect to your future goals or values

What specific part of your essay structure would you like to work on? Share your essay topic or prompt, and I can help you organize your ideas into this framework."""

    def _help_with_narrative_development(self, user_input: str) -> str:
        """Provide guidance on developing compelling narratives."""
        return """Great question about storytelling! Strong college essays focus on specific moments rather than broad overviews. Here's how to develop your narrative:

**Choose Your Moment:**
- Pick one specific day, conversation, or experience
- Focus on 15-30 minutes of real time
- Show don't tell through concrete details

**Story Elements:**
- What was the specific challenge or decision?
- What did you think, feel, and do in that moment?
- What changed in your perspective afterward?

What experience or story are you considering? I can help you narrow it down to the most compelling moment and develop the narrative structure."""

    def _help_with_vivid_details(self, user_input: str) -> str:
        """Provide guidance on adding vivid, sensory details."""
        return """Excellent focus on details! Vivid writing brings readers into your experience. Here's how to add compelling details:

**Sensory Details:**
- What did you see, hear, smell, feel, taste?
- Use specific rather than general descriptions
- Include dialogue when relevant

**Show Don't Tell:**
- Instead of "I was nervous" → "My hands shook as I reached for the microphone"
- Instead of "It was chaotic" → "Papers scattered across the floor while three phones rang simultaneously"

**Internal Experience:**
- What were you thinking in that exact moment?
- What physical sensations did you notice?

Do you have a specific scene or paragraph you'd like to make more vivid? Share it with me and I'll help you add compelling details."""

    def _help_with_opening_hooks(self, user_input: str) -> str:
        """Provide guidance on creating strong opening hooks."""
        return """Great focus on your opening! A strong hook draws readers in immediately. Here are proven techniques:

**Effective Hook Types:**
- **Action/Dialogue**: Start in the middle of a scene
- **Vivid Image**: Paint a specific, compelling picture
- **Unexpected Statement**: Challenge assumptions
- **Sensory Detail**: Engage the reader's senses

**What to Avoid:**
- Generic statements about life/society
- Dictionary definitions
- "Ever since I was little..."

**Examples:**
- "The silence lasted exactly twelve seconds."
- "My grandmother's laugh could shatter glass."
- "I've been fired from three volunteer jobs."

What's your essay topic? I can help you craft a hook that pulls readers into your specific story immediately."""

    def _help_with_reflection(self, user_input: str) -> str:
        """Provide guidance on powerful conclusions and reflection."""
        return """Perfect question about reflection! Strong conclusions don't just summarize—they show growth and future connection. Here's how:

**Reflection Elements:**
- What specific insight did you gain?
- How do you think differently now?
- What will you do differently in the future?
- How does this connect to your goals/values?

**Avoid These Pitfalls:**
- Generic life lessons ("I learned to never give up")
- Repetition of what you already said
- Grandiose claims about changing the world

**Strong Reflection Pattern:**
1. Specific insight you gained
2. How it shapes your current thinking
3. Connection to your future goals/approach

What was the main lesson or change from your experience? I can help you craft a reflection that feels authentic and forward-looking."""

    def _help_with_brainstorming(self, user_input: str) -> str:
        """Provide guidance on brainstorming essay topics and ideas."""
        return """I'd love to help you brainstorm! The best college essays come from specific, personal experiences. Let's find your story:

**Brainstorming Questions:**
- What's a moment when you surprised yourself?
- When did you change your mind about something important?
- What's a challenge that taught you something unexpected?
- When did you stand up for something you believe in?
- What's a mistake that led to growth?

**Essay Types to Consider:**
- **Identity**: What makes you uniquely you?
- **Challenge**: How did you overcome a difficulty?
- **Passion**: What genuinely excites you?
- **Community**: How do you contribute to others?

**Next Steps:**
1. Think of 3-5 specific moments from your life
2. For each, ask: "What did I learn?" and "How did I change?"
3. Pick the one where you can show the most growth

What type of essay prompt are you working on? Or what general life area interests you most (academics, family, activities, work, etc.)? I can help you dig deeper into specific stories."""

    def _help_with_improvement(self, user_input: str) -> str:
        """Provide guidance on improving and revising essays."""
        return """Excellent focus on improvement! Revision is where good essays become great. Here's a systematic approach:

**Improvement Areas:**
1. **Structure**: Does each paragraph have a clear purpose?
2. **Specificity**: Can you add more concrete details?
3. **Voice**: Does it sound authentically like you?
4. **Connection**: How well does it answer the prompt?
5. **Growth**: Do you show clear change/learning?

**Revision Questions:**
- What's the main point of each paragraph?
- Where can you "show don't tell"?
- What details make you unique?
- How do you demonstrate growth?

**Next Steps:**
If you have a draft, I'd love to help you identify specific areas for improvement. You can share:
- A paragraph you want to strengthen
- Your essay outline for structure feedback
- Your main story for development ideas

What aspect of your essay feels weakest right now? Structure, details, voice, or something else?"""

    def _general_essay_assistance(self, user_input: str) -> str:
        """Provide general essay writing assistance and guidance."""
        return """I'm here to help you with all aspects of college essay writing! I can assist you with:

**Essay Development:**
- Brainstorming compelling topics and stories
- Creating strong outlines and structure
- Developing vivid, specific details
- Crafting engaging hooks and conclusions

**Writing Process:**
- Choosing the best personal stories
- Showing growth and reflection
- Maintaining authentic voice
- Connecting experiences to prompts

**Revision & Polish:**
- Strengthening weak paragraphs
- Adding sensory details and dialogue
- Improving flow and transitions
- Ensuring prompt alignment

**How I Can Help:**
- Share your essay prompt and I'll help you brainstorm ideas
- Send me a paragraph and I'll help you make it more vivid
- Tell me your story and I'll help you structure it effectively
- Ask specific questions about any aspect of essay writing

What would you like to focus on first? Whether you're just starting or polishing a final draft, I'm here to help you create a compelling essay that showcases your unique story."""
    
    # =========================================================================
    # Phase 2: LLM-Driven Enhancement Methods
    # =========================================================================
    
    async def _extract_and_update_context(self, user_input: str) -> None:
        """Extract user context and update conversation state."""
        
        try:
            # Extract user context using the context extractor
            context_update = await self.context_extractor.extract_and_update_context(
                user_input=user_input,
                existing_profile=self.memory.get_user_profile(),
                conversation_history=self.memory.get_recent_history(3)
            )
            
            # Update conversation context
            self.conversation_context.update({
                'latest_experiences': context_update.new_experiences,
                'latest_interests': context_update.new_interests,
                'latest_background': context_update.new_background,
                'latest_goals': context_update.new_goals
            })
            
            # Update user profile in memory
            if context_update.updated_profile:
                await self.memory.update_user_profile(context_update.updated_profile)
            
            # Detect school mentions and update scenario context
            school_name = self.school_injector.extract_school_from_input(user_input)
            if school_name:
                school_context = self.school_injector.get_school_context(school_name)
                if school_context:
                    self.scenario_context['school_context'] = {
                        'name': school_context.name,
                        'values': school_context.values,
                        'programs': school_context.programs,
                        'culture': school_context.culture
                    }
            
            logger.debug(f"Context extracted: {context_update.integration_summary}")
            
        except Exception as e:
            logger.warning(f"Context extraction failed: {e}")
    
    def _extract_school_name(self, user_input: str) -> Optional[str]:
        """Extract school name from user input or scenario context."""
        
        # Check scenario context first
        if 'school_context' in self.scenario_context:
            return self.scenario_context['school_context']['name']
        
        # Extract from user input
        return self.school_injector.extract_school_from_input(user_input)
    
    def _get_user_interests(self) -> List[str]:
        """Get user interests from conversation context and profile."""
        
        interests = []
        
        # From conversation context
        if 'latest_interests' in self.conversation_context:
            interests.extend(self.conversation_context['latest_interests'])
        
        # From user profile
        user_profile = self.memory.get_user_profile()
        if user_profile and 'interests' in user_profile:
            profile_interests = user_profile['interests']
            if isinstance(profile_interests, list):
                interests.extend(profile_interests)
        
        return list(set(interests))  # Remove duplicates
    
    def _cache_response(self, response: str) -> None:
        """Cache response for deduplication checking."""
        
        self.recent_responses.append(response)
        
        # Keep only last 5 responses to prevent memory bloat
        if len(self.recent_responses) > 5:
            self.recent_responses = self.recent_responses[-3:]
    
    async def _generate_contextual_conversation(self, user_input: str, reasoning: ReasoningResult) -> str:
        """Generate enhanced conversational response with context integration."""
        
        try:
            # Use the response generator for conversation responses too
            conversation_result = f"Based on your request: {user_input}, here's my guidance..."
            
            response = await self.response_generator.generate_contextual_response(
                user_input=user_input,
                tool_result=conversation_result,
                conversation_history=self.memory.get_recent_history(3),
                user_profile=self.memory.get_user_profile(),
                previous_responses=self.recent_responses,
                school_context=self.scenario_context.get('school_context')
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Contextual conversation generation failed: {e}")
            return self._generate_helpful_fallback(user_input, "conversation_fallback") 