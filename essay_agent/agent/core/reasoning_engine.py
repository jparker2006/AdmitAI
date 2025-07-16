"""LLM-powered reasoning engine with prompt optimization.

This module provides sophisticated reasoning capabilities for the ReAct agent,
including context-aware prompt selection, robust JSON parsing, confidence tracking,
and continuous performance optimization.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from essay_agent.llm_client import get_chat_llm
from essay_agent.response_parser import safe_parse
from ..prompt_builder import PromptBuilder  
from ..prompt_optimizer import PromptOptimizer

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
        
        # Performance tracking
        self.reasoning_count = 0
        self.total_reasoning_time = 0.0
        self.success_count = 0
        
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
            # Build optimized reasoning prompt
            prompt_data = await self.prompt_builder.build_reasoning_prompt(
                user_input=user_input,
                context=context,
                prompt_type="action_reasoning"
            )
            
            # Get LLM reasoning response
            llm_response = await self._call_llm_with_retry(prompt_data["prompt"])
            
            # Parse and validate response
            reasoning_dict = self._parse_reasoning_response(llm_response)
            
            # Create structured result
            reasoning_time = time.time() - start_time
            result = ReasoningResult(
                context_understanding=reasoning_dict.get("context_understanding", ""),
                reasoning=reasoning_dict.get("reasoning", ""),
                chosen_tool=reasoning_dict.get("chosen_tool"),
                tool_args=reasoning_dict.get("tool_args", {}),
                confidence=reasoning_dict.get("confidence", 0.5),
                response_type=reasoning_dict.get("response_type", "conversation"),
                anticipated_follow_up=reasoning_dict.get("anticipated_follow_up", ""),
                context_flags=reasoning_dict.get("context_flags", []),
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
            "total_reasoning_time": self.total_reasoning_time
        } 