"""LLM-powered reasoning engine with prompt optimization.

This module provides sophisticated reasoning capabilities for the ReAct agent,
including context-aware prompt selection, robust JSON parsing, confidence tracking,
and continuous performance optimization.
"""
from __future__ import annotations

import json
import logging
import time
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from essay_agent.llm_client import get_chat_llm
from essay_agent.response_parser import safe_parse
from ..prompt_builder import PromptBuilder  
from ..prompt_optimizer import PromptOptimizer

# Import Phase 2 LLM-driven components
from essay_agent.prompts.tool_selection import comprehensive_tool_selector

logger = logging.getLogger(__name__)


@dataclass
class ReasoningResult:
    """Structured reasoning result with validation and metadata."""
    context_understanding: str
    reasoning: str
    chosen_tool: Optional[str]
    tool_args: Dict[str, Any]
    confidence: float
    response_type: str  # "tool_execution" or "conversation"
    anticipated_follow_up: str
    context_flags: List[str]
    reasoning_time: float
    prompt_version: str
    

class ReasoningError(Exception):
    """Raised when reasoning process fails."""
    pass


class ReasoningEngine:
    """LLM-powered reasoning engine with prompt optimization.
    
    This class handles the reasoning phase of the ReAct loop, using sophisticated
    prompt building and optimization to generate high-quality reasoning about
    what actions to take based on user input and context.
    """
    
    def __init__(self, prompt_builder: PromptBuilder, prompt_optimizer: PromptOptimizer):
        """Initialize the reasoning engine.
        
        Args:
            prompt_builder: Dynamic prompt construction system
            prompt_optimizer: Performance tracking and A/B testing system
        """
        self.prompt_builder = prompt_builder
        self.prompt_optimizer = prompt_optimizer
        self.llm = get_chat_llm()
        
        # Initialize Phase 2 LLM-driven components
        self.tool_selector = comprehensive_tool_selector
        
        # Performance tracking
        self.reasoning_count = 0
        self.total_reasoning_time = 0.0
        self.success_count = 0
        
        # Simple caching for performance
        self.prompt_cache = {}
        self.response_cache = {}
        self.cache_max_size = 50
        
    async def reason_about_action(
        self, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> ReasoningResult:
        """Generate reasoning about what action to take.
        
        This is the core reasoning method that analyzes user input and context
        to determine the appropriate tool to use or conversation to engage in.
        
        Args:
            user_input: The user's message or request
            context: Current context including memory, essay state, etc.
            
        Returns:
            ReasoningResult with action decision and confidence metrics
            
        Raises:
            ReasoningError: If reasoning process fails
        """
        start_time = time.time()
        self.reasoning_count += 1
        
        try:
            # Check for fast-path simple requests
            simple_response = self._try_simple_reasoning(user_input, context)
            if simple_response:
                return simple_response
            
            # Build optimized reasoning prompt with context optimization
            prompt_data = await self.prompt_builder.build_reasoning_prompt(
                user_input=user_input,
                context=self._optimize_context_size(context),
                prompt_type="action_reasoning"
            )
            
            # Check cache first
            cache_key = self._generate_cache_key(prompt_data["prompt"], user_input, context)
            if cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                logger.debug("Using cached reasoning response")
                reasoning_time = time.time() - start_time
                return self._create_cached_result(cached_response, reasoning_time, prompt_data.get("version", "default"))
            
            # Get LLM reasoning response
            llm_response = await self._call_llm_with_retry(prompt_data["prompt"])
            
            # Cache the response
            self._cache_response(cache_key, llm_response)
            
            # Parse and validate response
            reasoning_dict = self._parse_reasoning_response(llm_response)
            
            # PHASE 2 ENHANCEMENT: Use context-aware tool selection for validation/enhancement
            enhanced_reasoning = await self._enhance_with_context_aware_selection(
                reasoning_dict, user_input, context
            )
            
            # Create structured result
            reasoning_time = time.time() - start_time
            result = ReasoningResult(
                context_understanding=enhanced_reasoning.get("context_understanding", ""),
                reasoning=enhanced_reasoning.get("reasoning", ""),
                chosen_tool=enhanced_reasoning.get("chosen_tool"),
                tool_args=enhanced_reasoning.get("tool_args", {}),
                confidence=enhanced_reasoning.get("confidence", 0.5),
                response_type=enhanced_reasoning.get("response_type", "conversation"),
                anticipated_follow_up=enhanced_reasoning.get("anticipated_follow_up", ""),
                context_flags=enhanced_reasoning.get("context_flags", []),
                reasoning_time=reasoning_time,
                prompt_version=prompt_data.get("version", "default")
            )
            
            # Track performance
            self.success_count += 1
            self.total_reasoning_time += reasoning_time
            
            # Update prompt optimizer with results
            await self.prompt_optimizer.track_performance(
                prompt_version=prompt_data.get("version", "default"),
                success=True,
                response_time=reasoning_time,
                confidence=result.confidence,
                context_size=len(str(context))
            )
            
            logger.info(f"Reasoning completed in {reasoning_time:.2f}s with confidence {result.confidence:.2f}")
            return result
            
        except Exception as e:
            reasoning_time = time.time() - start_time
            self.total_reasoning_time += reasoning_time
            
            # Track failure in optimizer
            await self.prompt_optimizer.track_performance(
                prompt_version=prompt_data.get("version", "default") if 'prompt_data' in locals() else "unknown",
                success=False,
                response_time=reasoning_time,
                confidence=0.0,
                context_size=len(str(context))
            )
            
            logger.error(f"Reasoning failed after {reasoning_time:.2f}s: {e}")
            raise ReasoningError(f"Failed to generate reasoning: {e}") from e
    
    async def reason_about_response(
        self,
        user_input: str,
        reasoning: Dict[str, Any],
        action_result: Tuple[str, Any]
    ) -> str:
        """Generate natural language response based on action results.
        
        Args:
            user_input: Original user request
            reasoning: Previous reasoning from reason_about_action
            action_result: Result from action execution
            
        Returns:
            Natural language response string
        """
        try:
            # Build response generation prompt
            prompt_data = await self.prompt_builder.build_response_prompt(
                user_input=user_input,
                reasoning=reasoning,
                action_result=action_result
            )
            
            # Get response from LLM
            response = await self._call_llm_with_retry(prompt_data["prompt"])
            
            # Clean and validate response
            cleaned_response = self._clean_response(response)
            
            logger.debug(f"Generated response of {len(cleaned_response)} characters")
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback to basic response
            return self._generate_fallback_response(user_input, action_result)
    
    def _parse_reasoning_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse and validate LLM reasoning JSON response.
        
        Args:
            llm_response: Raw response from LLM
            
        Returns:
            Validated reasoning dictionary
            
        Raises:
            ReasoningError: If parsing fails
        """
        try:
            # Parse JSON response, handling markdown code blocks
            response_text = llm_response.strip()
            if response_text.startswith('```json'):
                # Extract JSON from markdown code blocks
                response_text = response_text[7:]  # Remove ```json
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove ```
            elif response_text.startswith('```'):
                # Handle generic code blocks
                response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
            
            parsed = json.loads(response_text.strip())
            
            if not isinstance(parsed, dict):
                raise ValueError("Response is not a dictionary")
            
            # Validate required fields
            required_fields = ["context_understanding", "reasoning", "response_type"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate response_type
            if parsed["response_type"] not in ["tool_execution", "conversation"]:
                parsed["response_type"] = "conversation"
            
            # Validate confidence
            if "confidence" in parsed:
                confidence = parsed["confidence"]
                if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                    parsed["confidence"] = 0.5
            else:
                parsed["confidence"] = 0.5
            
            # Ensure tool_args is a dict
            if "tool_args" not in parsed:
                parsed["tool_args"] = {}
            elif not isinstance(parsed["tool_args"], dict):
                parsed["tool_args"] = {}
            
            # Ensure context_flags is a list
            if "context_flags" not in parsed:
                parsed["context_flags"] = []
            elif not isinstance(parsed["context_flags"], list):
                parsed["context_flags"] = []
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse reasoning response: {e}")
            logger.debug(f"Raw response: {llm_response}")
            
            # Fallback: If LLM returned a conversational response instead of JSON,
            # create a valid reasoning structure for conversation mode
            if llm_response and llm_response.strip():
                logger.info("LLM returned conversational response instead of JSON - creating fallback structure")
                return {
                    "context_understanding": "Understanding user's essay writing needs",
                    "reasoning": "Providing conversational support for essay development",
                    "response_type": "conversation", 
                    "confidence": 0.7,
                    "tool_name": None,
                    "tool_args": {},
                    "context_flags": [],
                    "conversation_response": llm_response.strip()
                }
            
            raise ReasoningError(f"Invalid reasoning response format: {e}") from e
    
    async def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call LLM with retry logic and error handling.
        
        Args:
            prompt: The prompt to send to the LLM
            max_retries: Maximum number of retry attempts
            
        Returns:
            LLM response string
            
        Raises:
            ReasoningError: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self.llm.apredict(prompt)
                if response and response.strip():
                    return response.strip()
                else:
                    raise ValueError("Empty response from LLM")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = (2 ** attempt) * 1.0
                    await asyncio.sleep(wait_time)
                    
        raise ReasoningError(f"LLM call failed after {max_retries} attempts: {last_error}") from last_error
    
    def _clean_response(self, response: str) -> str:
        """Clean and validate natural language response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned response string
        """
        if not response:
            return "I'm here to help with your essay! What would you like to work on?"
        
        # Remove excessive whitespace
        cleaned = " ".join(response.split())
        
        # Ensure reasonable length
        if len(cleaned) > 2000:
            cleaned = cleaned[:1997] + "..."
        
        # Ensure it ends with proper punctuation
        if cleaned and not cleaned[-1] in ".!?":
            cleaned += "."
        
        return cleaned
    
    def _generate_fallback_response(self, user_input: str, action_result: Tuple[str, Any]) -> str:
        """Generate fallback response when normal response generation fails.
        
        Args:
            user_input: Original user input
            action_result: Action execution result
            
        Returns:
            Fallback response string
        """
        action_type, result = action_result
        
        if action_type == "tool_execution" and result:
            return "I've processed your request and generated some results. How can I help you further?"
        elif action_type == "error":
            return "I encountered an issue processing your request, but I'm here to help. Could you try rephrasing or let me know what specific assistance you need?"
        else:
            return "Thank you for your message! I'm here to help you with your essay writing. What would you like to work on?"
    
    def _try_simple_reasoning(self, user_input: str, context: Dict[str, Any]) -> Optional[ReasoningResult]:
        """Fast-path for simple requests that don't need full LLM reasoning.
        
        Args:
            user_input: User's message
            context: Current context
            
        Returns:
            ReasoningResult if simple case detected, None otherwise
        """
        user_lower = user_input.lower().strip()
        
        # Simple brainstorming requests
        if any(word in user_lower for word in ["brainstorm", "ideas", "think of"]) and len(user_input) < 100:
            return ReasoningResult(
                context_understanding="User wants brainstorming help",
                reasoning="Simple brainstorming request - using brainstorm tool",
                chosen_tool="brainstorm",
                tool_args={"user_input": user_input},
                confidence=0.9,
                response_type="tool_execution",
                anticipated_follow_up="User will want to explore ideas further",
                context_flags=["simple_request"],
                reasoning_time=0.1,
                prompt_version="fast_path"
            )
        
        # Simple help requests
        if user_lower in ["help", "help me", "what can you do", "what now"]:
            return ReasoningResult(
                context_understanding="User needs general guidance",
                reasoning="Simple help request - providing conversational guidance",
                chosen_tool=None,
                tool_args={},
                confidence=0.8,
                response_type="conversation",
                anticipated_follow_up="User will specify what they need help with",
                context_flags=["simple_request"],
                reasoning_time=0.1,
                prompt_version="fast_path"
            )
        
        return None
    
    def _optimize_context_size(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize context size for faster LLM processing.
        
        Args:
            context: Original context dictionary
            
        Returns:
            Optimized context with reduced size
        """
        optimized = context.copy()
        
        # Truncate conversation history to last 5 turns
        if "conversation_history" in optimized and isinstance(optimized["conversation_history"], list):
            optimized["conversation_history"] = optimized["conversation_history"][-5:]
        
        # Simplify user profile to essential info
        if "user_profile" in optimized and isinstance(optimized["user_profile"], dict):
            profile = optimized["user_profile"]
            essential_profile = {
                "name": profile.get("name", ""),
                "experience_level": profile.get("experience_level", "intermediate"),
                "core_values": profile.get("core_values", [])[:3],  # Keep only first 3
                "defining_moments": profile.get("defining_moments", [])[:2]  # Keep only first 2
            }
            optimized["user_profile"] = essential_profile
        
        # Remove large tool histories
        if "tool_history" in optimized:
            del optimized["tool_history"]
        
        return optimized
    
    def _generate_cache_key(self, prompt: str, user_input: str = "", context: Dict[str, Any] = None) -> str:
        """Generate cache key for prompt including user context.
        
        Args:
            prompt: LLM prompt text
            user_input: User's input for context differentiation  
            context: Context dictionary for additional differentiation
            
        Returns:
            Cache key string
        """
        import hashlib
        
        # BUGFIX: Include user input and context in cache key to prevent 
        # identical responses for different user inputs
        key_components = [
            prompt[:500],  # First 500 chars of prompt
            user_input[:200],  # First 200 chars of user input
        ]
        
        # Add context hash if available
        if context:
            # Create a stable hash of relevant context keys
            context_keys = ["user_profile", "conversation_history", "current_input"]
            context_parts = []
            for key in context_keys:
                if key in context and context[key]:
                    context_parts.append(f"{key}:{str(context[key])[:100]}")
            if context_parts:
                key_components.append(",".join(context_parts))
        
        # Create hash of combined components
        combined = "|".join(key_components)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _cache_response(self, cache_key: str, response: str) -> None:
        """Cache LLM response.
        
        Args:
            cache_key: Cache key
            response: LLM response to cache
        """
        if len(self.response_cache) >= self.cache_max_size:
            # Remove oldest entries
            keys_to_remove = list(self.response_cache.keys())[:10]
            for key in keys_to_remove:
                del self.response_cache[key]
        
        self.response_cache[cache_key] = response
    
    def _create_cached_result(self, cached_response: str, reasoning_time: float, prompt_version: str) -> ReasoningResult:
        """Create ReasoningResult from cached response.
        
        Args:
            cached_response: Previously cached LLM response
            reasoning_time: Time taken for this call
            prompt_version: Version of prompt used
            
        Returns:
            ReasoningResult with cached data
        """
        reasoning_dict = self._parse_reasoning_response(cached_response)
        
        return ReasoningResult(
            context_understanding=reasoning_dict.get("context_understanding", ""),
            reasoning=reasoning_dict.get("reasoning", ""),
            chosen_tool=reasoning_dict.get("chosen_tool"),
            tool_args=reasoning_dict.get("tool_args", {}),
            confidence=reasoning_dict.get("confidence", 0.5),
            response_type=reasoning_dict.get("response_type", "conversation"),
            anticipated_follow_up=reasoning_dict.get("anticipated_follow_up", ""),
            context_flags=reasoning_dict.get("context_flags", []) + ["cached"],
            reasoning_time=reasoning_time,
            prompt_version=prompt_version
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get reasoning engine performance metrics.
        
        Returns:
            Dictionary with performance statistics
        """
        avg_time = self.total_reasoning_time / max(self.reasoning_count, 1)
        success_rate = self.success_count / max(self.reasoning_count, 1)
        
        return {
            "total_reasoning_requests": self.reasoning_count,
            "successful_requests": self.success_count,
            "success_rate": success_rate,
            "average_reasoning_time": avg_time,
            "total_reasoning_time": self.total_reasoning_time,
            "cache_hit_ratio": len(self.response_cache) / max(self.reasoning_count, 1),
            "cache_size": len(self.response_cache)
        }
    
    # =========================================================================
    # Phase 2: Context-Aware Tool Selection Enhancement
    # =========================================================================
    
    async def _enhance_with_context_aware_selection(
        self,
        reasoning_dict: Dict[str, Any],
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance reasoning with context-aware tool selection.
        
        This method validates and potentially improves tool selection using the
        context-aware tool selector, solving Bug #2 (tool selection ignores user evolution).
        
        Args:
            reasoning_dict: Original reasoning from LLM
            user_input: User's input
            context: Current context
            
        Returns:
            Enhanced reasoning dictionary
        """
        try:
            enhanced_reasoning = dict(reasoning_dict)  # Copy original
            
            # Extract context for tool selection
            conversation_history = context.get('conversation_history', [])
            user_profile = context.get('user_profile', {})
            
            # Get available tools (simplified for now)
            available_tools = [
                'brainstorm', 'outline', 'draft', 'revise', 'polish',
                'suggest_stories', 'match_story', 'essay_scoring', 'word_count', 'clarify'
            ]
            
            # Get completed tools from conversation history
            completed_tools = self._extract_completed_tools(conversation_history)
            
            # Use comprehensive tool selector for validation/enhancement
            selected_tools = await self.tool_selector.select_tools_intelligent(
                user_input=user_input,
                conversation_history=conversation_history,
                user_profile=user_profile,
                available_tools=available_tools,
                max_tools=1  # Single tool for validation/enhancement
            )
            
            # Validate and potentially improve tool selection
            original_tool = reasoning_dict.get("chosen_tool")
            suggested_tool = selected_tools[0] if selected_tools else None
            
            # If the comprehensive selector suggests a different tool
            if (suggested_tool and 
                suggested_tool != original_tool and 
                suggested_tool in available_tools):
                
                logger.info(f"Comprehensive tool selector suggests '{suggested_tool}' instead of '{original_tool}'")
                
                # Update reasoning with better tool selection
                enhanced_reasoning.update({
                    "chosen_tool": suggested_tool,
                    "reasoning": f"{reasoning_dict.get('reasoning', '')} Enhanced with comprehensive tool analysis.",
                    "confidence": min(reasoning_dict.get("confidence", 0.5) + 0.1, 1.0),  # Slight confidence boost
                    "context_flags": reasoning_dict.get("context_flags", []) + ["comprehensive_tool_selection"]
                })
            
            # If no tool was originally selected but context suggests one
            elif not original_tool and suggested_tool:
                logger.info(f"Comprehensive tool selector suggests '{suggested_tool}' for conversation without tool")
                
                enhanced_reasoning.update({
                    "chosen_tool": suggested_tool,
                    "response_type": "tool_execution",
                    "reasoning": f"{reasoning_dict.get('reasoning', '')} Comprehensive analysis suggests tool usage.",
                    "confidence": 0.8,  # High confidence from comprehensive analysis
                    "context_flags": reasoning_dict.get("context_flags", []) + ["comprehensive_suggested_tool"]
                })
            
            return enhanced_reasoning
            
        except Exception as e:
            logger.warning(f"Context-aware tool selection enhancement failed: {e}")
            return reasoning_dict  # Return original reasoning on failure
    
    def _extract_completed_tools(self, conversation_history: List[Dict]) -> List[str]:
        """Extract completed tools from conversation history."""
        
        completed_tools = []
        
        for turn in conversation_history:
            tools_used = turn.get('tools_used', [])
            if isinstance(tools_used, list):
                completed_tools.extend(tools_used)
        
        return completed_tools 