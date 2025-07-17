"""Enhanced agent memory for ReAct pattern operations.

This module provides a comprehensive memory system for the ReAct agent,
supporting reasoning chain storage, tool execution tracking, context retrieval,
and pattern detection while integrating with existing memory infrastructure.
"""
from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime

# Import existing memory infrastructure
from essay_agent.memory.hierarchical import HierarchicalMemory
from essay_agent.memory.semantic_search import SemanticSearchIndex
from essay_agent.memory.conversation import JSONConversationMemory
from essay_agent.memory.context_manager import ContextWindowManager
from essay_agent.memory.user_profile_schema import UserProfile

# Import ReAct components
from .react_models import (
    ReasoningChain, ToolExecution, UsagePattern, ErrorPattern,
    ReasoningStep, RetrievedContext, MemoryStats
)
from .context_retrieval import ContextRetriever
from .memory_indexer import MemoryIndexer

logger = logging.getLogger(__name__)


class AgentMemory:
    """Enhanced memory system for ReAct agent operations.
    
    Provides comprehensive memory capabilities including:
    - ReAct reasoning chain storage and retrieval
    - Tool execution tracking and pattern analysis
    - Intelligent context retrieval for agent reasoning
    - Integration with existing memory infrastructure
    - Pattern detection for performance optimization
    """
    
    def __init__(self, user_id: str):
        """Initialize enhanced agent memory.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.memory_dir = Path("memory_store")
        self.memory_dir.mkdir(exist_ok=True)
        
        # Initialize memory components
        try:
            # Rich memory infrastructure
            self.hierarchical_memory = HierarchicalMemory(user_id)
            self.conversation_memory = JSONConversationMemory(user_id)
            self.context_manager = ContextWindowManager(user_id, essay_id="cli_session")
            
            # ReAct-specific components
            self.context_retriever = ContextRetriever(user_id)
            self.memory_indexer = MemoryIndexer(user_id)
            
            # In-memory caches for performance
            self.recent_reasoning_chains: List[ReasoningChain] = []
            self.recent_tool_executions: List[ToolExecution] = []
            self.pattern_cache: Dict[str, Any] = {}
            
            logger.info(f"Initialized AgentMemory for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error initializing AgentMemory: {e}")
            # Graceful degradation
            self.hierarchical_memory = None
            self.conversation_memory = None
            self.context_manager = None
            self.context_retriever = None
            self.memory_indexer = None
    
    # ================================================================
    # Core ReAct Memory Operations
    # ================================================================
    
    def store_reasoning_chain(self, reasoning: Optional[Dict[str, Any]] = None, 
                                user_input: str = "", reasoning_steps: List[Dict] = None,
                                final_action: str = "", success: bool = True, **kwargs) -> str:
        """Store a complete reasoning chain from ReAct episode.
        
        Args:
            reasoning: Dictionary containing reasoning information (legacy)
            user_input: User input that triggered the reasoning
            reasoning_steps: List of reasoning steps taken
            final_action: Final action chosen
            success: Whether the reasoning was successful
            **kwargs: Additional parameters
            
        Returns:
            ID of stored reasoning chain
        """
        try:
            # Handle both legacy and new parameter formats
            if reasoning is not None:
                # Legacy format: reasoning dict contains all data
                reasoning_data = reasoning
            else:
                # New format: individual parameters
                reasoning_data = {
                    "user_input": user_input,
                    "steps": reasoning_steps or [],
                    "final_action": final_action,
                    "success": success
                }
            
            # Create reasoning steps from reasoning data
            steps = []
            
            if "steps" in reasoning_data:
                for i, step_data in enumerate(reasoning_data["steps"]):
                    step = ReasoningStep(
                        step_number=i + 1,
                        thought=step_data.get("thought", ""),
                        tool_considered=step_data.get("tool_considered"),
                        confidence=step_data.get("confidence", 0.5),
                        context_used=step_data.get("context_used", [])
                    )
                    steps.append(step)
            
            # Create reasoning chain
            chain = ReasoningChain(
                user_input=reasoning_data.get("user_input", ""),
                reasoning_steps=steps,
                final_action=reasoning_data.get("final_action", ""),
                result=reasoning_data.get("result"),
                success=reasoning_data.get("success", True),
                execution_time=reasoning_data.get("execution_time", 0.0),
                context_tokens=reasoning_data.get("context_tokens", 0)
            )
            
            # Store in cache and index
            self.recent_reasoning_chains.append(chain)
            if len(self.recent_reasoning_chains) > 20:  # Keep recent 20
                self.recent_reasoning_chains = self.recent_reasoning_chains[-20:]
            
            # Index for pattern detection
            if self.memory_indexer:
                self.memory_indexer.index_reasoning_chain(chain)
            
            logger.debug(f"Stored reasoning chain {chain.id}")
            return chain.id
            
        except Exception as e:
            logger.error(f"Error storing reasoning chain: {e}")
            return ""
    
    def track_tool_execution(self, tool_name: str, result: Any, reasoning: str, 
                           execution_time: float = 0.0, success: bool = True,
                           error_message: Optional[str] = None,
                           confidence_score: float = 0.8,
                           input_params: Optional[Dict[str, Any]] = None) -> str:
        """Track tool execution with context and results.
        
        Args:
            tool_name: Name of the executed tool
            result: Result returned by the tool
            reasoning: Reasoning context that led to tool execution
            execution_time: Time taken for execution in seconds
            success: Whether execution was successful
            error_message: Error message if execution failed
            confidence_score: Confidence in tool choice (0-1)
            input_params: Parameters passed to the tool
            
        Returns:
            ID of tracked tool execution
        """
        try:
            # Estimate tokens used (simple heuristic)
            tokens_used = self._estimate_tokens_used(result)
            
            # Create tool execution record
            execution = ToolExecution(
                tool_name=tool_name,
                input_params=input_params or {},
                result=result,
                execution_time=execution_time,
                success=success,
                error_message=error_message,
                reasoning_context=reasoning,
                confidence_score=confidence_score,
                tokens_used=tokens_used
            )
            
            # Store in cache and index
            self.recent_tool_executions.append(execution)
            if len(self.recent_tool_executions) > 50:  # Keep recent 50
                self.recent_tool_executions = self.recent_tool_executions[-50:]
            
            # Index for pattern detection
            if self.memory_indexer:
                self.memory_indexer.index_tool_execution(execution)
            
            logger.debug(f"Tracked tool execution {execution.id} for {tool_name}")
            return execution.id
            
        except Exception as e:
            logger.error(f"Error tracking tool execution: {e}")
            return ""
    
    def get_relevant_context(self, query: str, max_tokens: int = 2000,
                           context_types: Optional[List[str]] = None) -> RetrievedContext:
        """Get relevant context for ReAct reasoning.
        
        Args:
            query: User query or reasoning prompt
            max_tokens: Maximum tokens to use for context
            context_types: Types of context to retrieve
            
        Returns:
            Retrieved context optimized for reasoning
        """
        try:
            if not self.context_retriever:
                # Fallback to simple context
                return self._get_simple_context(query, max_tokens)
            
            return self.context_retriever.retrieve_context(
                query=query,
                context_types=context_types,
                max_tokens=max_tokens
            )
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return self._get_simple_context(query, max_tokens)
    
    def retrieve_context(self, user_input: str = "", context_size: int = 2000, 
                        include_patterns: bool = True, include_recent_tools: bool = True, 
                        **kwargs) -> RetrievedContext:
        """Alias for get_relevant_context with ReAct agent compatibility.
        
        Maps ReAct agent parameters to AgentMemory interface:
        - user_input -> query  
        - context_size -> max_tokens
        - include_patterns, include_recent_tools -> context_types
        
        Args:
            user_input: User query or reasoning prompt (maps to query)
            context_size: Maximum tokens to use (maps to max_tokens)
            include_patterns: Whether to include pattern context
            include_recent_tools: Whether to include recent tool usage
            **kwargs: Additional parameters passed through
            
        Returns:
            Retrieved context optimized for reasoning
        """
        # Parameter mapping logic
        query = user_input or kwargs.get('query', '')
        max_tokens = context_size
        
        # Build context_types from boolean flags
        context_types = []
        if include_patterns:
            context_types.extend(['patterns', 'essay_structure'])
        if include_recent_tools:
            context_types.extend(['recent_tools', 'tool_usage'])
        
        result = self.get_relevant_context(
            query=query, 
            max_tokens=max_tokens,
            context_types=context_types or None
        )
        
        # Convert RetrievedContext to dictionary for ReAct agent compatibility
        if hasattr(result, 'model_dump'):
            return result.model_dump()
        else:
            return result
    
    def detect_patterns(self, lookback_days: int = 30) -> Dict[str, List[Any]]:
        """Detect usage and error patterns for optimization.
        
        Args:
            lookback_days: Days to look back for pattern detection
            
        Returns:
            Dictionary containing usage_patterns and error_patterns
        """
        patterns = {"usage_patterns": [], "error_patterns": []}
        
        try:
            if not self.memory_indexer:
                return patterns
            
            # Check cache first
            cache_key = f"patterns_{lookback_days}"
            if cache_key in self.pattern_cache:
                cache_data = self.pattern_cache[cache_key]
                cache_age = (datetime.now() - cache_data["timestamp"]).total_seconds()
                
                if cache_age < 3600:  # Use cache if less than 1 hour old
                    return cache_data["patterns"]
            
            # Detect patterns
            usage_patterns = self.memory_indexer.detect_usage_patterns(lookback_days)
            error_patterns = self.memory_indexer.detect_error_patterns(lookback_days)
            
            patterns = {
                "usage_patterns": usage_patterns,
                "error_patterns": error_patterns
            }
            
            # Cache results
            self.pattern_cache[cache_key] = {
                "patterns": patterns,
                "timestamp": datetime.now()
            }
            
            logger.info(f"Detected {len(usage_patterns)} usage patterns and "
                       f"{len(error_patterns)} error patterns")
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
        
        return patterns
    
    # ================================================================
    # Integration with Existing Memory
    # ================================================================
    
    def get_context(self) -> Dict[str, Any]:
        """Get comprehensive context for agent reasoning.
        
        Returns:
            Dictionary containing all context information needed for reasoning
        """
        try:
            context = {
                "user_profile": self.get_user_profile(),
                "essay_state": self.get_essay_state(),
                "conversation_history": self.get_recent_history(5),
                "recent_tools": self.get_recent_tool_usage(10),
                "usage_patterns": self.get_cached_usage_patterns(),
                "constraints": {}
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return {}
    
    def update_context(self, user_input: str, reasoning: str, action: str, result: Any) -> None:
        """Update context after agent action.
        
        Args:
            user_input: User's input that triggered the action
            reasoning: Agent's reasoning process
            action: Action taken by the agent
            result: Result of the action
        """
        try:
            # Store reasoning chain if this was a complete ReAct episode
            if reasoning and action:
                reasoning_data = {
                    "user_input": user_input,
                    "steps": [{"thought": reasoning, "tool_considered": action}],
                    "final_action": action,
                    "result": result,
                    "success": result is not None
                }
                self.store_reasoning_chain(reasoning_data)
            
            # Update conversation memory if available
            if self.conversation_memory:
                # Add user input
                self.conversation_memory.chat_memory.add_user_message(user_input)
                
                # Add agent response
                if isinstance(result, str):
                    self.conversation_memory.chat_memory.add_ai_message(result)
                else:
                    self.conversation_memory.chat_memory.add_ai_message(f"Executed {action}")
            
            logger.debug(f"Updated context for action: {action}")
            
        except Exception as e:
            logger.error(f"Error updating context: {e}")
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile data.
        
        Returns:
            User profile information
        """
        try:
            if not self.hierarchical_memory:
                return {}
            
            profile = self.hierarchical_memory.profile
            
            return {
                "name": getattr(profile, "name", ""),
                "core_values": [{"value": cv.value, "description": cv.description} 
                               for cv in getattr(profile, "core_values", [])],
                "defining_moments": [{"title": dm.title, "description": dm.description}
                                   for dm in getattr(profile, "defining_moments", [])],
                "academic_interests": getattr(profile, "academic_interests", []),
                "career_goals": getattr(profile, "career_goals", [])
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {}
    
    def get_essay_state(self) -> Dict[str, Any]:
        """Get current essay work state.
        
        Returns:
            Current essay state including prompt, stage, drafts
        """
        try:
            if not self.hierarchical_memory:
                return {"stage": "planning", "word_count": 0, "drafts": []}
            
            # Get latest essay record
            essay_history = getattr(self.hierarchical_memory.profile, "essay_history", [])
            
            if essay_history:
                latest_essay = essay_history[-1]
                return {
                    "prompt": getattr(latest_essay, "prompt", ""),
                    "stage": "drafting" if getattr(latest_essay, "versions", []) else "planning",
                    "word_count": len(getattr(latest_essay, "final_draft", "").split()) if hasattr(latest_essay, "final_draft") else 0,
                    "drafts": len(getattr(latest_essay, "versions", []))
                }
            
            return {"stage": "planning", "word_count": 0, "drafts": []}
            
        except Exception as e:
            logger.error(f"Error getting essay state: {e}")
            return {"stage": "planning", "word_count": 0, "drafts": []}
    
    def get_recent_history(self, turns: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation turns.
        
        Args:
            turns: Number of recent turns to retrieve
            
        Returns:
            List of recent conversation turns
        """
        try:
            if not self.conversation_memory:
                return []
            
            # Fix: JSONConversationMemory uses ._buffer_memory.chat_memory.messages
            # instead of .buffer.messages
            if hasattr(self.conversation_memory, '_buffer_memory'):
                # JSONConversationMemory interface
                messages = self.conversation_memory._buffer_memory.chat_memory.messages[-turns * 2:]
            elif hasattr(self.conversation_memory, 'buffer') and hasattr(self.conversation_memory.buffer, 'messages'):
                # Standard ConversationBufferMemory interface
                messages = self.conversation_memory.buffer.messages[-turns * 2:]
            else:
                # Fallback: try to get messages through memory variables
                memory_vars = self.conversation_memory.load_memory_variables({})
                chat_history = memory_vars.get('chat_history', [])
                if isinstance(chat_history, list):
                    messages = chat_history[-turns * 2:]
                else:
                    return []
            
            history = []
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    history.append({
                        "user": messages[i].content,
                        "agent": messages[i + 1].content,
                        "timestamp": datetime.now().isoformat()  # Approximate
                    })
            
            return history[-turns:]  # Return last N turns
            
        except Exception as e:
            logger.error(f"Error getting recent history: {e}")
            return []
    
    def get_recent_tool_usage(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent tool usage information.
        
        Args:
            count: Number of recent tool executions to return
            
        Returns:
            List of recent tool usage information
        """
        try:
            recent_tools = []
            
            for execution in self.recent_tool_executions[-count:]:
                recent_tools.append({
                    "tool_name": execution.tool_name,
                    "success": execution.success,
                    "execution_time": execution.execution_time,
                    "timestamp": execution.timestamp.isoformat()
                })
            
            return recent_tools
            
        except Exception as e:
            logger.error(f"Error getting recent tool usage: {e}")
            return []
    
    def get_cached_usage_patterns(self) -> List[Dict[str, Any]]:
        """Get cached usage patterns for quick access.
        
        Returns:
            List of usage pattern summaries
        """
        try:
            patterns_data = self.pattern_cache.get("patterns_30", {})
            usage_patterns = patterns_data.get("patterns", {}).get("usage_patterns", [])
            
            # Convert to simple dict format
            pattern_summaries = []
            for pattern in usage_patterns[:5]:  # Top 5 patterns
                pattern_summaries.append({
                    "type": pattern.pattern_type,
                    "tools": pattern.tools,
                    "frequency": pattern.frequency,
                    "success_rate": pattern.success_rate,
                    "confidence": pattern.confidence
                })
            
            return pattern_summaries
            
        except Exception as e:
            logger.error(f"Error getting cached usage patterns: {e}")
            return []
    
    # ================================================================
    # Memory Management & Statistics
    # ================================================================
    
    def get_memory_stats(self) -> MemoryStats:
        """Get comprehensive memory usage statistics.
        
        Returns:
            Memory statistics object
        """
        try:
            if self.memory_indexer:
                return self.memory_indexer.get_memory_stats()
            else:
                return MemoryStats()
                
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return MemoryStats()
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage and performance.
        
        Returns:
            Dictionary with optimization results
        """
        try:
            optimization_results = {
                "patterns_detected": 0,
                "cache_cleared": False,
                "memory_compacted": False,
                "recommendations": []
            }
            
            # Detect fresh patterns
            patterns = self.detect_patterns()
            optimization_results["patterns_detected"] = (
                len(patterns["usage_patterns"]) + len(patterns["error_patterns"])
            )
            
            # Clear old cache entries
            current_time = datetime.now()
            old_cache_keys = []
            
            for key, data in self.pattern_cache.items():
                if isinstance(data, dict) and "timestamp" in data:
                    age = (current_time - data["timestamp"]).total_seconds()
                    if age > 7200:  # Older than 2 hours
                        old_cache_keys.append(key)
            
            for key in old_cache_keys:
                del self.pattern_cache[key]
                optimization_results["cache_cleared"] = True
            
            # Generate recommendations based on patterns
            error_patterns = patterns["error_patterns"]
            if error_patterns:
                high_frequency_errors = [p for p in error_patterns if p.frequency > 3]
                if high_frequency_errors:
                    optimization_results["recommendations"].append(
                        f"Consider addressing {len(high_frequency_errors)} frequent error patterns"
                    )
            
            usage_patterns = patterns["usage_patterns"]
            low_success_patterns = [p for p in usage_patterns if p.success_rate < 0.7]
            if low_success_patterns:
                optimization_results["recommendations"].append(
                    f"Review {len(low_success_patterns)} tool patterns with low success rates"
                )
            
            # Save memory indexes
            if self.memory_indexer:
                self.memory_indexer.save_indexes()
                optimization_results["memory_compacted"] = True
            
            logger.info(f"Memory optimization completed: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")
            return {"error": str(e)}
    
    # ================================================================
    # Helper Methods
    # ================================================================
    
    def _get_simple_context(self, query: str, max_tokens: int) -> RetrievedContext:
        """Fallback simple context retrieval."""
        from .react_models import ContextElement, RetrievedContext
        
        elements = []
        
        # Add user profile context
        profile = self.get_user_profile()
        if profile:
            elements.append(ContextElement(
                source="user_profile",
                content=profile,
                relevance_score=0.8,
                tokens=min(200, max_tokens // 4)
            ))
        
        # Add recent conversation
        history = self.get_recent_history(3)
        if history:
            elements.append(ContextElement(
                source="conversation",
                content={"recent_turns": history},
                relevance_score=0.7,
                tokens=min(300, max_tokens // 3)
            ))
        
        # Add recent tools
        recent_tools = self.get_recent_tool_usage(5)
        if recent_tools:
            elements.append(ContextElement(
                source="tool_history",
                content={"recent_tools": recent_tools},
                relevance_score=0.6,
                tokens=min(200, max_tokens // 4)
            ))
        
        total_tokens = sum(e.tokens for e in elements)
        
        return RetrievedContext(
            query=query,
            elements=elements,
            total_tokens=total_tokens,
            retrieval_time=0.001,
            optimization_applied=False
        )
    
    def _estimate_tokens_used(self, result: Any) -> int:
        """Estimate tokens used by tool result."""
        try:
            if isinstance(result, str):
                # Rough estimate: 1 token per 4 characters
                return len(result) // 4
            elif isinstance(result, dict):
                # Estimate based on JSON string length
                import json
                return len(json.dumps(result)) // 4
            elif isinstance(result, list):
                # Estimate based on list length and average item size
                return len(result) * 10  # Rough estimate
            else:
                return 50  # Default estimate
                
        except Exception:
            return 50
    
    # ================================================================
    # ReAct Agent Integration Methods
    # ================================================================
    
    async def update_user_profile(self, updated_profile: Dict[str, Any]) -> None:
        """Update user profile with new information from context extraction.
        
        This method is called by the ReAct agent when new user context is extracted
        from conversations and needs to be persisted to the memory system.
        
        Args:
            updated_profile: Dictionary containing updated user profile information
        """
        try:
            if not self.hierarchical_memory:
                logger.warning("Cannot update profile: hierarchical memory not available")
                return
            
            # Get current profile
            current_profile = self.hierarchical_memory.profile
            
            # Update profile fields safely
            if 'user_info' in updated_profile:
                user_info = updated_profile['user_info']
                if hasattr(current_profile, 'user_info'):
                    # Update existing user_info fields
                    for key, value in user_info.items():
                        if hasattr(current_profile.user_info, key) and value:
                            setattr(current_profile.user_info, key, value)
            
            # Update core values if provided
            if 'core_values' in updated_profile:
                for cv_data in updated_profile['core_values']:
                    if isinstance(cv_data, dict) and 'value' in cv_data:
                        # Check if core value already exists
                        existing_values = [cv.value for cv in current_profile.core_values]
                        if cv_data['value'] not in existing_values:
                            from essay_agent.memory.user_profile_schema import CoreValue
                            new_cv = CoreValue(
                                value=cv_data['value'],
                                description=cv_data.get('description', ''),
                                manifestations=cv_data.get('manifestations', [])
                            )
                            current_profile.core_values.append(new_cv)
            
            # Update defining moments if provided
            if 'defining_moments' in updated_profile:
                for dm_data in updated_profile['defining_moments']:
                    if isinstance(dm_data, dict) and 'title' in dm_data:
                        # Check if defining moment already exists
                        existing_titles = [dm.title for dm in current_profile.defining_moments]
                        if dm_data['title'] not in existing_titles:
                            from essay_agent.memory.user_profile_schema import DefiningMoment
                            new_dm = DefiningMoment(
                                title=dm_data['title'],
                                description=dm_data.get('description', ''),
                                emotional_impact=dm_data.get('emotional_impact', ''),
                                lessons_learned=dm_data.get('lessons_learned', ''),
                                themes=dm_data.get('themes', [])
                            )
                            current_profile.defining_moments.append(new_dm)
            
            # Update writing voice if provided
            if 'writing_voice' in updated_profile and updated_profile['writing_voice']:
                voice_data = updated_profile['writing_voice']
                if hasattr(current_profile, 'writing_voice') and current_profile.writing_voice:
                    # Update existing writing voice
                    for key, value in voice_data.items():
                        if hasattr(current_profile.writing_voice, key) and value:
                            setattr(current_profile.writing_voice, key, value)
                else:
                    # Create new writing voice
                    from essay_agent.memory.user_profile_schema import WritingVoice
                    current_profile.writing_voice = WritingVoice(
                        tone=voice_data.get('tone', ''),
                        style=voice_data.get('style', ''),
                        sophistication_level=voice_data.get('sophistication_level', ''),
                        preferred_sentence_structures=voice_data.get('preferred_sentence_structures', []),
                        stylistic_traits=voice_data.get('stylistic_traits', [])
                    )
            
            # Save updated profile
            self.hierarchical_memory.save()
            
            logger.info(f"Updated user profile with new information")
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
    
    async def store_tool_execution(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        execution_time: float,
        success: bool = True
    ) -> None:
        """Store tool execution results for ReAct agent memory.
        
        Args:
            tool_name: Name of the executed tool
            args: Tool arguments used
            result: Tool execution result
            execution_time: Time taken for execution
            success: Whether execution was successful
        """
        try:
            # Create tool execution record
            execution_record = {
                "tool_name": tool_name,
                "args": args,
                "result": str(result)[:500],  # Truncate long results
                "execution_time": execution_time,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in recent tool executions
            self.recent_tool_executions.append(execution_record)
            
            # Keep only recent executions (limit to 50)
            if len(self.recent_tool_executions) > 50:
                self.recent_tool_executions = self.recent_tool_executions[-50:]
            
            logger.debug(f"Stored tool execution: {tool_name} (success={success})")
            
        except Exception as e:
            logger.error(f"Error storing tool execution: {e}")
    
    async def store_conversation_turn(
        self,
        user_input: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store conversation turn for ReAct agent memory.
        
        Args:
            user_input: User's input message
            agent_response: Agent's response
            metadata: Additional metadata about the turn
        """
        try:
            # Store via conversation memory if available
            if self.conversation_memory:
                self.conversation_memory.save_context(
                    inputs={"input": user_input},
                    outputs={"output": agent_response}
                )
            
            logger.debug(f"Stored conversation turn: {len(user_input)} chars input")
            
        except Exception as e:
            logger.error(f"Error storing conversation turn: {e}")
    
    # ================================================================
    # Context Manager Methods (for existing compatibility)
    # ================================================================
    
    def _save_context(self) -> None:
        """Save context to persistent storage."""
        try:
            # This is handled by individual memory components
            # Just trigger optimization to ensure everything is saved
            self.optimize_memory()
            
        except Exception as e:
            logger.error(f"Error saving context: {e}")
    
    def _load_context(self) -> None:
        """Load context from persistent storage."""
        try:
            # Context is loaded automatically by memory components
            # Just refresh pattern cache
            self.detect_patterns()
            
        except Exception as e:
            logger.error(f"Error loading context: {e}") 