"""Tool execution engine with error handling and recovery.

This module provides sophisticated tool execution capabilities for the ReAct agent,
including validation, timeout handling, error recovery, and performance tracking.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime

from essay_agent.agent.tools.tool_registry import EnhancedToolRegistry, ENHANCED_REGISTRY
from essay_agent.agent.memory.agent_memory import AgentMemory

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Structured action execution result with metadata."""
    action_type: str  # "tool_execution", "conversation", "error"
    success: bool
    result: Any
    execution_time: float
    error_message: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    tool_name: Optional[str] = None
    confidence: float = 1.0
    context_updates: Dict[str, Any] = None


class ActionExecutionError(Exception):
    """Raised when action execution fails."""
    pass


class ActionExecutor:
    """Tool execution engine with error handling and recovery.
    
    This class handles the action phase of the ReAct loop, executing chosen tools
    with comprehensive validation, error handling, and performance tracking.
    """
    
    def __init__(self, tool_registry: EnhancedToolRegistry, memory: AgentMemory):
        """Initialize the action executor.
        
        Args:
            tool_registry: Registry of available tools
            memory: Agent memory system for context and tracking
        """
        self.tool_registry = tool_registry
        self.memory = memory
        
        # Performance tracking
        self.execution_count = 0
        self.success_count = 0
        self.total_execution_time = 0.0
        self.tool_usage_stats = {}
        
        # Error recovery strategies
        self.recovery_strategies = {
            "timeout": self._handle_timeout_error,
            "validation": self._handle_validation_error,
            "execution": self._handle_execution_error,
            "network": self._handle_network_error,
            "llm": self._handle_llm_error
        }
    
    async def execute_action(self, reasoning: Dict[str, Any]) -> ActionResult:
        """Execute chosen action with comprehensive error handling.
        
        Args:
            reasoning: Reasoning result from ReasoningEngine
            
        Returns:
            ActionResult with execution details and results
        """
        start_time = time.time()
        self.execution_count += 1
        
        try:
            response_type = reasoning.get("response_type", "conversation")
            
            if response_type == "tool_execution":
                return await self._execute_tool_action(reasoning, start_time)
            else:
                return await self._execute_conversation_action(reasoning, start_time)
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            logger.error(f"Action execution failed after {execution_time:.2f}s: {e}")
            
            # Try to recover from the error
            recovery_result = self._handle_action_error(e, reasoning, execution_time)
            if recovery_result:
                return recovery_result
            
            # If recovery fails, return error result
            return ActionResult(
                action_type="error",
                success=False,
                result=None,
                execution_time=execution_time,
                error_message=str(e),
                recovery_suggestion="Please try rephrasing your request or specify what you'd like help with."
            )
    
    async def _execute_tool_action(self, reasoning: Dict[str, Any], start_time: float) -> ActionResult:
        """Execute a tool-based action.
        
        Args:
            reasoning: Reasoning result with tool selection
            start_time: When execution started
            
        Returns:
            ActionResult with tool execution results
        """
        tool_name = reasoning.get("chosen_tool")
        tool_args = reasoning.get("tool_args", {})
        
        if not tool_name:
            raise ActionExecutionError("No tool specified in reasoning")
        
        # Validate tool exists
        if not self.tool_registry.has_tool(tool_name):
            raise ActionExecutionError(f"Tool '{tool_name}' not found in registry")
        
        # Add missing required arguments for specific tools
        tool_args = self._add_missing_tool_args(tool_name, tool_args)
        
        # Execute the tool
        result = await self.execute_tool(tool_name, tool_args)
        
        execution_time = time.time() - start_time
        self.success_count += 1
        self.total_execution_time += execution_time
        
        # Update tool usage statistics
        if tool_name not in self.tool_usage_stats:
            self.tool_usage_stats[tool_name] = {
                "usage_count": 0,
                "success_count": 0,
                "total_time": 0.0,
                "avg_time": 0.0
            }
        
        stats = self.tool_usage_stats[tool_name]
        stats["usage_count"] += 1
        stats["success_count"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["usage_count"]
        
        # Store execution in memory
        await self.memory.store_tool_execution(
            tool_name=tool_name,
            args=tool_args,
            result=result,
            execution_time=execution_time,
            success=True
        )
        
        logger.info(f"Tool '{tool_name}' executed successfully in {execution_time:.2f}s")
        
        return ActionResult(
            action_type="tool_execution",
            success=True,
            result=result,
            execution_time=execution_time,
            tool_name=tool_name,
            confidence=reasoning.get("confidence", 1.0)
        )
    
    async def _execute_conversation_action(self, reasoning: Dict[str, Any], start_time: float) -> ActionResult:
        """Execute a conversation-based action.
        
        Args:
            reasoning: Reasoning result with conversation guidance
            start_time: When execution started
            
        Returns:
            ActionResult with conversation response
        """
        execution_time = time.time() - start_time
        self.success_count += 1
        self.total_execution_time += execution_time
        
        # Generate conversational response based on reasoning
        response = await self.handle_conversation(
            reasoning.get("reasoning", ""),
            reasoning.get("context", {})
        )
        
        logger.debug(f"Conversation response generated in {execution_time:.2f}s")
        
        return ActionResult(
            action_type="conversation",
            success=True,
            result=response,
            execution_time=execution_time,
            confidence=reasoning.get("confidence", 1.0)
        )
    
    async def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute specific tool with validation and timeout.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            
        Returns:
            Tool execution result
            
        Raises:
            ActionExecutionError: If tool execution fails
        """
        try:
            # Validate tool arguments
            self._validate_tool_args(tool_name, tool_args)
            
            # Get tool function
            tool_func = self.tool_registry.get_tool(tool_name)
            if not tool_func:
                raise ActionExecutionError(f"Tool '{tool_name}' not available")
            
            # Execute with timeout
            timeout = self._get_tool_timeout(tool_name)
            result = await asyncio.wait_for(
                self._execute_tool_with_args(tool_func, tool_args),
                timeout=timeout
            )
            
            # Validate result
            validated_result = self._validate_tool_result(tool_name, result)
            
            return validated_result
            
        except asyncio.TimeoutError:
            raise ActionExecutionError(f"Tool '{tool_name}' timed out after {timeout}s")
        except Exception as e:
            raise ActionExecutionError(f"Tool '{tool_name}' execution failed: {e}") from e
    
    async def handle_conversation(self, reasoning: str, context: Dict[str, Any]) -> str:
        """Handle conversational responses.
        
        Args:
            reasoning: Agent's reasoning about the conversation
            context: Current context including user state
            
        Returns:
            Natural language response
        """
        # Generate contextual conversational response
        if "stuck" in reasoning.lower() or "blocked" in reasoning.lower():
            return self._generate_encouragement_response(context)
        elif "question" in reasoning.lower() or "clarification" in reasoning.lower():
            return self._generate_clarification_response(context)
        elif "guidance" in reasoning.lower() or "help" in reasoning.lower():
            return self._generate_guidance_response(context)
        else:
            return self._generate_supportive_response(context)
    
    def _validate_tool_args(self, tool_name: str, tool_args: Dict[str, Any]) -> None:
        """Validate tool arguments before execution.
        
        Args:
            tool_name: Name of the tool
            tool_args: Arguments to validate
            
        Raises:
            ActionExecutionError: If validation fails
        """
        # Get tool description for validation
        tool_desc = self.tool_registry.get_tool_description(tool_name)
        if not tool_desc:
            return  # Skip validation if no description available
        
        # Check required arguments
        required_args = tool_desc.get("required_args", [])
        for arg in required_args:
            if arg not in tool_args:
                raise ActionExecutionError(f"Missing required argument '{arg}' for tool '{tool_name}'")
        
        # Validate argument types if specified
        arg_types = tool_desc.get("arg_types", {})
        for arg, expected_type in arg_types.items():
            if arg in tool_args:
                if not isinstance(tool_args[arg], expected_type):
                    raise ActionExecutionError(
                        f"Argument '{arg}' should be {expected_type.__name__}, got {type(tool_args[arg]).__name__}"
                    )
    
    def _get_tool_timeout(self, tool_name: str) -> float:
        """Get timeout for specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Timeout in seconds
        """
        # Default timeouts based on tool category
        timeouts = {
            "brainstorm": 30.0,
            "outline": 45.0,
            "draft": 60.0,
            "revise": 45.0,
            "polish": 30.0,
            "evaluate": 30.0,
            "research": 60.0
        }
        
        # Use specific timeout or default
        return timeouts.get(tool_name, 30.0)
    
    async def _execute_tool_with_args(self, tool_func, tool_args: Dict[str, Any]) -> Any:
        """Execute tool function with arguments.
        
        Args:
            tool_func: Tool function to execute
            tool_args: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**tool_args)
        else:
            return tool_func(**tool_args)
    
    def _validate_tool_result(self, tool_name: str, result: Any) -> Any:
        """Validate tool execution result.
        
        Args:
            tool_name: Name of the tool
            result: Result to validate
            
        Returns:
            Validated result
        """
        if result is None:
            logger.warning(f"Tool '{tool_name}' returned None result")
            return f"Tool '{tool_name}' completed but didn't return specific results."
        
        return result
    
    def _handle_action_error(
        self, 
        error: Exception, 
        reasoning: Dict[str, Any], 
        execution_time: float
    ) -> Optional[ActionResult]:
        """Handle action execution errors with recovery strategies.
        
        Args:
            error: The exception that occurred
            reasoning: Original reasoning
            execution_time: Time spent on failed execution
            
        Returns:
            ActionResult if recovery successful, None otherwise
        """
        error_type = self._classify_error(error)
        recovery_func = self.recovery_strategies.get(error_type)
        
        if recovery_func:
            try:
                return recovery_func(error, reasoning, execution_time)
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
        
        return None
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate recovery strategy.
        
        Args:
            error: The exception to classify
            
        Returns:
            Error category string
        """
        error_msg = str(error).lower()
        
        if "timeout" in error_msg:
            return "timeout"
        elif "validation" in error_msg or "argument" in error_msg:
            return "validation"
        elif "network" in error_msg or "connection" in error_msg:
            return "network"
        elif "llm" in error_msg or "openai" in error_msg:
            return "llm"
        else:
            return "execution"
    
    def _handle_timeout_error(self, error: Exception, reasoning: Dict, execution_time: float) -> ActionResult:
        """Handle timeout errors."""
        return ActionResult(
            action_type="error",
            success=False,
            result=None,
            execution_time=execution_time,
            error_message="Operation timed out",
            recovery_suggestion="Let's try a simpler approach or break this into smaller steps."
        )
    
    def _handle_validation_error(self, error: Exception, reasoning: Dict, execution_time: float) -> ActionResult:
        """Handle validation errors."""
        return ActionResult(
            action_type="error",
            success=False,
            result=None,
            execution_time=execution_time,
            error_message="Invalid input provided",
            recovery_suggestion="Could you provide more specific details about what you'd like help with?"
        )
    
    def _handle_execution_error(self, error: Exception, reasoning: Dict, execution_time: float) -> ActionResult:
        """Handle general execution errors."""
        return ActionResult(
            action_type="conversation",
            success=True,
            result="I encountered a technical issue, but I'm still here to help! What specific aspect of your essay would you like to work on?",
            execution_time=execution_time,
            confidence=0.8
        )
    
    def _handle_network_error(self, error: Exception, reasoning: Dict, execution_time: float) -> ActionResult:
        """Handle network-related errors."""
        return ActionResult(
            action_type="error",
            success=False,
            result=None,
            execution_time=execution_time,
            error_message="Network connectivity issue",
            recovery_suggestion="There seems to be a connectivity issue. Let's continue with what we can do offline."
        )
    
    def _handle_llm_error(self, error: Exception, reasoning: Dict, execution_time: float) -> ActionResult:
        """Handle LLM-related errors."""
        return ActionResult(
            action_type="conversation",
            success=True,
            result="I'm having some trouble with my language processing right now, but I can still help you brainstorm ideas or provide general guidance. What would you like to work on?",
            execution_time=execution_time,
            confidence=0.7
        )
    
    def _generate_encouragement_response(self, context: Dict[str, Any]) -> str:
        """Generate encouraging response for stuck users."""
        return "It's completely normal to feel stuck sometimes! Writing is a process, and every great essay starts with small steps. What's one small thing about your topic that interests you?"
    
    def _generate_clarification_response(self, context: Dict[str, Any]) -> str:
        """Generate clarification response."""
        return "I'd love to help clarify! Could you tell me more about what specifically you're working on or what's confusing you?"
    
    def _generate_guidance_response(self, context: Dict[str, Any]) -> str:
        """Generate guidance response."""
        return "I'm here to guide you through the essay writing process! We can work on brainstorming ideas, creating an outline, drafting sections, or polishing your writing. What feels like the right next step for you?"
    
    def _generate_supportive_response(self, context: Dict[str, Any]) -> str:
        """Generate general supportive response."""
        return "I'm here to support you with your essay! Whether you need help with ideas, structure, or writing, we can tackle this together. What would you like to focus on?"
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get action executor performance metrics.
        
        Returns:
            Dictionary with performance statistics
        """
        avg_time = self.total_execution_time / max(self.execution_count, 1)
        success_rate = self.success_count / max(self.execution_count, 1)
        
        return {
            "total_executions": self.execution_count,
            "successful_executions": self.success_count,
            "success_rate": success_rate,
            "average_execution_time": avg_time,
            "total_execution_time": self.total_execution_time,
            "tool_usage_stats": self.tool_usage_stats
        }
    
    def _add_missing_tool_args(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Add missing required arguments for specific tools.
        
        Args:
            tool_name: Name of the tool being executed
            tool_args: Current tool arguments
            
        Returns:
            Updated tool arguments with missing required args added
        """
        # Create a copy to avoid modifying the original
        updated_args = tool_args.copy()
        
        # Apply comprehensive parameter mapping
        updated_args = self._map_tool_parameters(tool_name, updated_args)
        
        # Add missing arguments for brainstorm tool
        if tool_name == "brainstorm":
            # Handle user_profile -> profile conversion (reasoning engine provides user_profile but tool expects profile)
            if "user_profile" in updated_args:
                user_profile_dict = updated_args.get("user_profile", {})
                if isinstance(user_profile_dict, dict):
                    # Convert user_profile dict to profile string
                    profile_parts = []
                    for key, value in user_profile_dict.items():
                        if value:
                            profile_parts.append(f"{key}: {value}")
                    if profile_parts:
                        updated_args["profile"] = "; ".join(profile_parts)
                    else:
                        updated_args["profile"] = "High school student passionate about learning and technology"
                else:
                    updated_args["profile"] = str(user_profile_dict)
                # Remove the user_profile key since we've converted it to profile
                del updated_args["user_profile"]
            
            # Add profile if still missing
            if "profile" not in updated_args:
                # Get user profile from memory if available
                try:
                    user_profile = self.memory.get_user_profile()
                    if user_profile and user_profile.get("name"):
                        # Create a simple profile description
                        profile_parts = []
                        if user_profile.get("name"):
                            profile_parts.append(f"Name: {user_profile['name']}")
                        if user_profile.get("core_values"):
                            values = [cv.get("value", "") for cv in user_profile.get("core_values", [])]
                            if values:
                                profile_parts.append(f"Values: {', '.join(values)}")
                        if user_profile.get("defining_moments"):
                            moments = [dm.get("title", "") for dm in user_profile.get("defining_moments", [])]
                            if moments:
                                profile_parts.append(f"Key experiences: {', '.join(moments)}")
                        
                        if profile_parts:
                            updated_args["profile"] = "; ".join(profile_parts)
                        else:
                            updated_args["profile"] = "High school student passionate about learning and technology"
                    else:
                        updated_args["profile"] = "High school student passionate about learning and technology"
                except Exception:
                    # Fallback profile if memory access fails
                    updated_args["profile"] = "High school student passionate about learning and technology"
            
            # Ensure essay_prompt is present
            if "essay_prompt" not in updated_args:
                updated_args["essay_prompt"] = "College application essay prompt"
        
        return updated_args
    
    def _map_tool_parameters(self, tool_name: str, generic_args: Dict[str, Any]) -> Dict[str, Any]:
        """Map generic reasoning parameters to tool-specific ones.
        
        Args:
            tool_name: Name of the tool to execute
            generic_args: Generic parameters from reasoning engine
            
        Returns:
            Mapped parameters specific to the tool
        """
        # Parameter mappings for specific tools
        param_mappings = {
            # Outline and structure tools
            'outline': {
                'user_input': 'story',
                'chosen_story': 'story',
                'essay_prompt': 'prompt',
                'target_word_count': 'word_count'
            },
            'outline_generator': {
                'user_input': 'story',
                'chosen_story': 'story',
                'essay_prompt': 'prompt',
                'target_word_count': 'word_count'
            },
            'structure_validator': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay'
            },
            'transition_suggestion': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay'
            },
            'length_optimizer': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay',
                'target_word_count': 'word_count'
            },
            
            # Brainstorming and story tools
            'brainstorm': {
                'user_input': 'topic',
                'essay_prompt': 'prompt'
            },
            'brainstorm_specific': {
                'user_input': 'topic',
                'chosen_story': 'topic',
                'topic': 'topic'
            },
            'suggest_stories': {
                'user_input': 'topic',
                'essay_prompt': 'prompt'
            },
            'match_story': {
                'user_input': 'story',
                'chosen_story': 'story',
                'user_story': 'story',
                'essay_prompt': 'essay_prompt',
                'prompt': 'essay_prompt'
            },
            'expand_story': {
                'user_input': 'story_seed',
                'story': 'story_seed',
                'chosen_story': 'story_seed'
            },
            'story_development': {
                'user_input': 'story',
                'chosen_story': 'story',
                'user_story': 'story'
            },
            'story_themes': {
                'user_input': 'story',
                'chosen_story': 'story',
                'user_story': 'story'
            },
            'validate_uniqueness': {
                'user_input': 'story',
                'chosen_story': 'story',
                'essay_prompt': 'prompt'
            },
            
            # Drafting and writing tools
            'draft': {
                'outline_dict': 'outline',
                'essay_prompt': 'prompt',
                'user_stories': 'stories',
                'voice': 'voice_profile'
            },
            'rewrite_paragraph': {
                'user_input': 'paragraph',
                'instruction': 'style_instruction',
                'voice': 'voice_profile',
                'style_instruction': 'style_instruction',
                'voice_profile': 'voice_profile'
            },
            'improve_opening': {
                'opening_text': 'opening_sentence',
                'user_input': 'opening_sentence',
                'context': 'essay_context',
                'voice': 'voice_profile'
            },
            'strengthen_voice': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay',
                'voice': 'voice_profile'
            },
            'expand_outline_section': {
                'section_text': 'section',
                'user_input': 'section',
                'context': 'essay_context',
                'voice': 'voice_profile'
            },
            'expand_paragraph': {
                'paragraph_text': 'paragraph',
                'user_input': 'paragraph',
                'context': 'essay_context',
                'voice': 'voice_profile'
            },
            
            # Polish and refinement tools
            'polish': {
                'draft_text': 'draft',
                'essay_text': 'draft',
                'user_input': 'draft',
                'target_word_count': 'word_count'
            },
            'revise': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay',
                'instruction': 'revision_instruction'
            },
            'fix_grammar': {
                'essay_text': 'text',
                'user_input': 'text',
                'draft': 'text'
            },
            'enhance_vocabulary': {
                'essay_text': 'text',
                'user_input': 'text',
                'draft': 'text'
            },
            'check_consistency': {
                'essay_text': 'text',
                'user_input': 'text',
                'draft': 'text'
            },
            'optimize_word_count': {
                'essay_text': 'text',
                'user_input': 'text',
                'draft': 'text',
                'target_word_count': 'target_count'
            },
            'final_polish': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay'
            },
            
            # Evaluation and analysis tools
            'essay_scoring': {
                'essay_text': 'essay_text',
                'user_input': 'essay_text',
                'draft': 'essay_text',
                'essay_prompt': 'essay_prompt',
                'prompt': 'essay_prompt'
            },
            'weakness_highlight': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay'
            },
            'cliche_detection': {
                'essay_text': 'text',
                'user_input': 'text',
                'draft': 'text'
            },
            'alignment_check': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay',
                'essay_prompt': 'prompt',
                'prompt': 'prompt'
            },
            'plagiarism_check': {
                'essay_text': 'text',
                'user_input': 'text',
                'draft': 'text'
            },
            'outline_alignment': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay',
                'outline_dict': 'outline'
            },
            'comprehensive_validation': {
                'essay_text': 'essay',
                'user_input': 'essay',
                'draft': 'essay',
                'essay_prompt': 'prompt'
            },
            
            # Prompt analysis tools
            'classify_prompt': {
                'essay_prompt': 'prompt',
                'prompt': 'prompt',
                'user_input': 'prompt'
            },
            'extract_requirements': {
                'essay_prompt': 'prompt',
                'prompt': 'prompt',
                'user_input': 'prompt'
            },
            'suggest_strategy': {
                'essay_prompt': 'prompt',
                'prompt': 'prompt',
                'user_input': 'prompt'
            },
            'detect_overlap': {
                'essay_prompt': 'prompt',
                'prompt': 'prompt',
                'user_input': 'prompt'
            },
            
            # Utility tools
            'word_count': {
                'essay_text': 'text',
                'user_input': 'text',
                'draft': 'text'
            },
            'clarify': {
                'user_input': 'input',
                'context': 'context'
            },
            'echo': {
                'user_input': 'message',
                'message': 'message'
            }
        }
        
        # Apply mappings if tool has specific parameter requirements
        if tool_name in param_mappings:
            mapped = {}
            for generic_key, tool_key in param_mappings[tool_name].items():
                if generic_key in generic_args:
                    mapped[tool_key] = generic_args[generic_key]
            
            # Merge mapped parameters with original, giving priority to mapped ones
            result = {**generic_args, **mapped}
        else:
            result = generic_args.copy()
        
        # Add fallback values for common missing parameters
        result = self._add_parameter_fallbacks(tool_name, result)
        
        return result
    
    def _add_parameter_fallbacks(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Add fallback values for commonly missing parameters.
        
        Args:
            tool_name: Name of the tool
            tool_args: Current tool arguments
            
        Returns:
            Tool arguments with fallback values added
        """
        result = tool_args.copy()
        
        # Common fallbacks for specific tools
        if tool_name in ['outline', 'outline_generator']:
            if 'story' not in result and 'user_input' in result:
                result['story'] = result['user_input']
            if 'prompt' not in result and 'essay_prompt' in result:
                result['prompt'] = result['essay_prompt']
            if 'prompt' not in result:
                result['prompt'] = "College application essay prompt"
            if 'word_count' not in result:
                result['word_count'] = 650
                
        elif tool_name == 'match_story':
            if 'story' not in result and 'user_input' in result:
                result['story'] = result['user_input']
            if 'story' not in result and 'chosen_story' in result:
                result['story'] = result['chosen_story']
            if 'story' not in result:
                result['story'] = "User's personal story"
            if 'essay_prompt' not in result and 'prompt' in result:
                result['essay_prompt'] = result['prompt']
            if 'essay_prompt' not in result:
                result['essay_prompt'] = "College application essay prompt"
                
        elif tool_name == 'brainstorm_specific':
            if 'topic' not in result and 'user_input' in result:
                result['topic'] = result['user_input']
            if 'topic' not in result:
                result['topic'] = "your experiences"
                
        elif tool_name in ['story_development', 'story_themes']:
            if 'story' not in result and 'user_input' in result:
                result['story'] = result['user_input']
            if 'story' not in result and 'chosen_story' in result:
                result['story'] = result['chosen_story']
            if 'story' not in result:
                result['story'] = "your personal story"
                
        elif tool_name in ['structure_validator', 'transition_suggestion', 'length_optimizer', 'weakness_highlight', 'alignment_check', 'outline_alignment', 'comprehensive_validation']:
            if 'essay' not in result and 'user_input' in result:
                result['essay'] = result['user_input']
            if 'essay' not in result and 'draft' in result:
                result['essay'] = result['draft']
            if 'essay' not in result and 'essay_text' in result:
                result['essay'] = result['essay_text']
            if 'essay' not in result:
                result['essay'] = "Sample essay content for analysis"
            if tool_name == 'length_optimizer' and 'word_count' not in result:
                result['word_count'] = 650
            if tool_name in ['alignment_check', 'comprehensive_validation'] and 'prompt' not in result:
                result['prompt'] = "College application essay prompt"
                
        elif tool_name in ['brainstorm', 'suggest_stories']:
            if 'topic' not in result and 'user_input' in result:
                result['topic'] = result['user_input']
            if 'topic' not in result:
                result['topic'] = "your experiences and interests"
            if 'prompt' not in result and 'essay_prompt' in result:
                result['prompt'] = result['essay_prompt']
            if 'prompt' not in result:
                result['prompt'] = "College application essay prompt"
                
        elif tool_name == 'expand_story':
            if 'story_seed' not in result and 'user_input' in result:
                result['story_seed'] = result['user_input']
            if 'story_seed' not in result and 'story' in result:
                result['story_seed'] = result['story']
            if 'story_seed' not in result:
                result['story_seed'] = "A meaningful experience from your life"
                
        elif tool_name == 'validate_uniqueness':
            if 'story' not in result and 'user_input' in result:
                result['story'] = result['user_input']
            if 'story' not in result:
                result['story'] = "Your personal story"
            if 'prompt' not in result and 'essay_prompt' in result:
                result['prompt'] = result['essay_prompt']
            if 'prompt' not in result:
                result['prompt'] = "College application essay prompt"
                
        elif tool_name == 'draft':
            if 'outline' not in result and 'outline_dict' in result:
                result['outline'] = result['outline_dict']
            if 'outline' not in result and 'user_input' in result:
                result['outline'] = result['user_input']
            if 'outline' not in result:
                result['outline'] = {"introduction": "Opening paragraph", "body": "Main content", "conclusion": "Closing thoughts"}
            if 'voice_profile' not in result and 'voice' in result:
                result['voice_profile'] = result['voice']
            if 'voice_profile' not in result:
                result['voice_profile'] = "Authentic, reflective high school student voice"
            if 'word_count' not in result:
                result['word_count'] = 650
                
        elif tool_name in ['polish', 'revise', 'strengthen_voice', 'final_polish']:
            if 'draft' not in result and 'user_input' in result:
                result['draft'] = result['user_input']
            if 'draft' not in result and 'essay_text' in result:
                result['draft'] = result['essay_text']
            if 'draft' not in result and 'essay' in result:
                result['draft'] = result['essay']
            if 'draft' not in result:
                result['draft'] = "Sample essay draft for polishing"
            if tool_name == 'polish' and 'word_count' not in result:
                result['word_count'] = 650
            if tool_name == 'revise' and 'revision_instruction' not in result:
                result['revision_instruction'] = "Improve clarity and flow"
            if tool_name in ['strengthen_voice', 'final_polish'] and 'voice_profile' not in result:
                result['voice_profile'] = "Authentic, reflective high school student voice"
                
        elif tool_name in ['fix_grammar', 'enhance_vocabulary', 'check_consistency', 'optimize_word_count', 'cliche_detection', 'plagiarism_check']:
            if 'text' not in result and 'user_input' in result:
                result['text'] = result['user_input']
            if 'text' not in result and 'essay_text' in result:
                result['text'] = result['essay_text']
            if 'text' not in result and 'draft' in result:
                result['text'] = result['draft']
            if 'text' not in result:
                result['text'] = "Sample text for processing"
            if tool_name == 'optimize_word_count' and 'target_count' not in result:
                result['target_count'] = 650
                
        elif tool_name == 'essay_scoring':
            if 'essay_text' not in result and 'user_input' in result:
                result['essay_text'] = result['user_input']
            if 'essay_text' not in result and 'draft' in result:
                result['essay_text'] = result['draft']
            if 'essay_text' not in result:
                result['essay_text'] = "Sample essay for scoring"
            if 'essay_prompt' not in result and 'prompt' in result:
                result['essay_prompt'] = result['prompt']
            if 'essay_prompt' not in result:
                result['essay_prompt'] = "College application essay prompt"
                
        elif tool_name in ['classify_prompt', 'extract_requirements', 'suggest_strategy', 'detect_overlap']:
            if 'prompt' not in result and 'user_input' in result:
                result['prompt'] = result['user_input']
            if 'prompt' not in result and 'essay_prompt' in result:
                result['prompt'] = result['essay_prompt']
            if 'prompt' not in result:
                result['prompt'] = "College application essay prompt"
                
        elif tool_name == 'word_count':
            if 'text' not in result and 'user_input' in result:
                result['text'] = result['user_input']
            if 'text' not in result and 'essay_text' in result:
                result['text'] = result['essay_text']
            if 'text' not in result and 'draft' in result:
                result['text'] = result['draft']
            if 'text' not in result:
                result['text'] = "Sample text for counting"
                
        elif tool_name == 'clarify':
            if 'input' not in result and 'user_input' in result:
                result['input'] = result['user_input']
            if 'input' not in result:
                result['input'] = "User needs clarification"
            if 'context' not in result:
                result['context'] = "Essay writing assistance"
                
        elif tool_name == 'echo':
            if 'message' not in result and 'user_input' in result:
                result['message'] = result['user_input']
            if 'message' not in result:
                result['message'] = "Hello"
                
        elif tool_name in ['expand_outline_section', 'expand_paragraph']:
            section_param = 'section' if tool_name == 'expand_outline_section' else 'paragraph'
            if section_param not in result and 'user_input' in result:
                result[section_param] = result['user_input']
            if section_param not in result:
                result[section_param] = f"Sample {section_param} for expansion"
            if 'essay_context' not in result and 'context' in result:
                result['essay_context'] = result['context']
            if 'essay_context' not in result:
                result['essay_context'] = "College application essay"
            if 'voice_profile' not in result and 'voice' in result:
                result['voice_profile'] = result['voice']
            if 'voice_profile' not in result:
                result['voice_profile'] = "Authentic, reflective high school student voice"
                
        elif tool_name == 'rewrite_paragraph':
            if 'paragraph' not in result and 'user_input' in result:
                result['paragraph'] = result['user_input']
            if 'style_instruction' not in result and 'instruction' in result:
                result['style_instruction'] = result['instruction']
            if 'style_instruction' not in result:
                result['style_instruction'] = "Make this paragraph more engaging and vivid"
            if 'voice_profile' not in result and 'voice' in result:
                result['voice_profile'] = result['voice']
            if 'voice_profile' not in result:
                result['voice_profile'] = "Authentic, reflective high school student voice"
                
        elif tool_name == 'improve_opening':
            if 'opening_sentence' not in result and 'user_input' in result:
                result['opening_sentence'] = result['user_input']
            if 'opening_sentence' not in result and 'opening_text' in result:
                result['opening_sentence'] = result['opening_text']
            if 'opening_sentence' not in result:
                result['opening_sentence'] = "Sample opening sentence for improvement"
            if 'essay_context' not in result and 'context' in result:
                result['essay_context'] = result['context']
            if 'essay_context' not in result:
                result['essay_context'] = "College application essay"
            if 'voice_profile' not in result and 'voice' in result:
                result['voice_profile'] = result['voice']
            if 'voice_profile' not in result:
                result['voice_profile'] = "Authentic, reflective high school student voice"
        
        return result 