"""Context retrieval engine for ReAct reasoning.

This module provides intelligent context retrieval that combines multiple
memory sources (conversation, semantic, tool history) to provide relevant
context for ReAct agent reasoning within token budget constraints.
"""
from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

import tiktoken

# Import existing memory infrastructure
from essay_agent.memory.hierarchical import HierarchicalMemory
from essay_agent.memory.semantic_search import SemanticSearchIndex
from essay_agent.memory.conversation import JSONConversationMemory  
from essay_agent.memory.context_manager import ContextWindowManager
from essay_agent.memory.user_profile_schema import CoreValue, DefiningMoment

# Import ReAct models
from .react_models import (
    ContextElement, RetrievedContext, ToolExecution, ReasoningChain
)

logger = logging.getLogger(__name__)


class ContextRetriever:
    """Intelligent context retrieval for ReAct reasoning.
    
    Combines multiple memory sources to provide relevant context for agent
    reasoning while respecting token budget constraints.
    """
    
    def __init__(self, user_id: str):
        """Initialize context retriever.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.memory_dir = Path("memory_store")
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Initialize memory components
        try:
            self.hierarchical_memory = HierarchicalMemory(user_id)
            self.semantic_search = SemanticSearchIndex.load_or_build(
                user_id, self.hierarchical_memory.profile
            )
            self.conversation_memory = JSONConversationMemory(user_id)
            self.context_manager = ContextWindowManager(user_id, essay_id="cli_session")
        except Exception as e:
            logger.warning(f"Could not initialize full memory system: {e}")
            # Graceful degradation
            self.hierarchical_memory = None
            self.semantic_search = None
            self.conversation_memory = None
            self.context_manager = None
    
    def retrieve_context(self, 
                        query: str, 
                        context_types: Optional[List[str]] = None,
                        max_tokens: int = 2000) -> RetrievedContext:
        """Retrieve relevant context for reasoning.
        
        Args:
            query: User query or reasoning prompt
            context_types: Types of context to retrieve (conversation, semantic, tool_history, reasoning_history)
            max_tokens: Maximum tokens to use for context
            
        Returns:
            Retrieved context optimized for token budget
        """
        start_time = time.time()
        
        if context_types is None:
            context_types = ["conversation", "semantic", "tool_history", "reasoning_history"]
        
        elements = []
        
        # Retrieve from each requested source
        if "conversation" in context_types:
            elements.extend(self._get_conversation_context(query))
            
        if "semantic" in context_types:
            elements.extend(self._get_semantic_context(query))
            
        if "tool_history" in context_types:
            elements.extend(self._get_tool_history_context(query))
            
        if "reasoning_history" in context_types:
            elements.extend(self._get_reasoning_history_context(query))
        
        # Score and rank all elements
        scored_elements = self._score_relevance(elements, query)
        
        # Optimize for token budget
        optimized_elements, optimization_applied = self._optimize_context_window(
            scored_elements, max_tokens
        )
        
        retrieval_time = time.time() - start_time
        total_tokens = sum(element.tokens for element in optimized_elements)
        
        return RetrievedContext(
            query=query,
            elements=optimized_elements,
            total_tokens=total_tokens,
            retrieval_time=retrieval_time,
            optimization_applied=optimization_applied
        )
    
    def _get_conversation_context(self, query: str) -> List[ContextElement]:
        """Get relevant conversation context."""
        elements = []
        
        if not self.conversation_memory:
            return elements
        
        try:
            # Get recent conversation turns
            history = self.conversation_memory.buffer
            recent_messages = history.messages[-10:]  # Last 10 messages
            
            for i, message in enumerate(recent_messages):
                content = f"{message.type}: {message.content}"
                tokens = len(self.encoding.encode(content))
                
                # Simple relevance based on keyword overlap
                relevance = self._calculate_keyword_overlap(query, content)
                
                elements.append(ContextElement(
                    source="conversation",
                    content={"role": message.type, "content": message.content},
                    relevance_score=relevance,
                    tokens=tokens
                ))
                
        except Exception as e:
            logger.warning(f"Error retrieving conversation context: {e}")
        
        return elements
    
    def _get_semantic_context(self, query: str) -> List[ContextElement]:
        """Get relevant semantic context from user profile."""
        elements = []
        
        if not self.semantic_search or not self.hierarchical_memory:
            return elements
        
        try:
            # Search for relevant semantic items
            semantic_results = self.semantic_search.search(query, k=5)
            
            for item in semantic_results:
                if isinstance(item, CoreValue):
                    content = {
                        "type": "core_value",
                        "value": item.value,
                        "description": item.description,
                        "examples": item.examples
                    }
                    text = f"{item.value}: {item.description}"
                elif isinstance(item, DefiningMoment):
                    content = {
                        "type": "defining_moment", 
                        "title": item.title,
                        "description": item.description,
                        "impact": item.impact,
                        "skills_developed": item.skills_developed
                    }
                    text = f"{item.title}: {item.description}"
                else:
                    continue
                
                tokens = len(self.encoding.encode(text))
                relevance = self._calculate_semantic_relevance(query, text)
                
                elements.append(ContextElement(
                    source="semantic",
                    content=content,
                    relevance_score=relevance,
                    tokens=tokens
                ))
                
        except Exception as e:
            logger.warning(f"Error retrieving semantic context: {e}")
        
        return elements
    
    def _get_tool_history_context(self, query: str) -> List[ContextElement]:
        """Get relevant tool execution history."""
        elements = []
        
        try:
            # Load tool execution history from memory
            tool_history_file = self.memory_dir / f"{self.user_id}.tool_history.json"
            
            if tool_history_file.exists():
                import json
                with open(tool_history_file, 'r') as f:
                    tool_executions = json.load(f)
                
                # Get recent and relevant tool executions
                for execution_data in tool_executions[-20:]:  # Last 20 executions
                    tool_name = execution_data.get("tool_name", "")
                    reasoning = execution_data.get("reasoning_context", "")
                    success = execution_data.get("success", True)
                    
                    content = {
                        "type": "tool_execution",
                        "tool_name": tool_name,
                        "reasoning": reasoning,
                        "success": success,
                        "timestamp": execution_data.get("timestamp")
                    }
                    
                    text = f"Tool: {tool_name} - {reasoning}"
                    tokens = len(self.encoding.encode(text))
                    relevance = self._calculate_keyword_overlap(query, text)
                    
                    elements.append(ContextElement(
                        source="tool_history",
                        content=content,
                        relevance_score=relevance,
                        tokens=tokens
                    ))
                    
        except Exception as e:
            logger.warning(f"Error retrieving tool history context: {e}")
        
        return elements
    
    def _get_reasoning_history_context(self, query: str) -> List[ContextElement]:
        """Get relevant reasoning chain history."""
        elements = []
        
        try:
            # Load reasoning history from memory
            reasoning_history_file = self.memory_dir / f"{self.user_id}.reasoning_history.json"
            
            if reasoning_history_file.exists():
                import json
                with open(reasoning_history_file, 'r') as f:
                    reasoning_chains = json.load(f)
                
                # Get relevant reasoning chains
                for chain_data in reasoning_chains[-10:]:  # Last 10 chains
                    user_input = chain_data.get("user_input", "")
                    final_action = chain_data.get("final_action", "")
                    success = chain_data.get("success", True)
                    
                    content = {
                        "type": "reasoning_chain",
                        "user_input": user_input,
                        "final_action": final_action,
                        "success": success,
                        "reasoning_steps": chain_data.get("reasoning_steps", [])
                    }
                    
                    text = f"Similar request: {user_input} -> {final_action}"
                    tokens = len(self.encoding.encode(text))
                    relevance = self._calculate_keyword_overlap(query, text)
                    
                    elements.append(ContextElement(
                        source="reasoning_history",
                        content=content,
                        relevance_score=relevance,
                        tokens=tokens
                    ))
                    
        except Exception as e:
            logger.warning(f"Error retrieving reasoning history context: {e}")
        
        return elements
    
    def _score_relevance(self, elements: List[ContextElement], query: str) -> List[ContextElement]:
        """Score and sort elements by relevance to query."""
        # Sort by relevance score (descending)
        return sorted(elements, key=lambda x: x.relevance_score, reverse=True)
    
    def _optimize_context_window(self, 
                                 elements: List[ContextElement], 
                                 max_tokens: int) -> Tuple[List[ContextElement], bool]:
        """Optimize context to fit within token budget.
        
        Args:
            elements: Sorted context elements
            max_tokens: Maximum tokens allowed
            
        Returns:
            Tuple of (optimized_elements, optimization_was_applied)
        """
        if not elements:
            return [], False
        
        selected_elements = []
        total_tokens = 0
        optimization_applied = False
        
        # Greedily select highest relevance elements that fit budget
        for element in elements:
            if total_tokens + element.tokens <= max_tokens:
                selected_elements.append(element)
                total_tokens += element.tokens
            else:
                optimization_applied = True
                
                # If we have room for a truncated version, try to fit it
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 50:  # Minimum viable context
                    # Truncate the element content
                    truncated_element = self._truncate_element(element, remaining_tokens)
                    if truncated_element:
                        selected_elements.append(truncated_element)
                        total_tokens += truncated_element.tokens
                break
        
        return selected_elements, optimization_applied
    
    def _truncate_element(self, element: ContextElement, max_tokens: int) -> Optional[ContextElement]:
        """Truncate a context element to fit token budget."""
        try:
            content = element.content
            
            if isinstance(content, dict):
                # Try to preserve the most important parts
                if content.get("type") == "conversation":
                    # Truncate message content
                    message_content = content.get("content", "")
                    truncated = self._truncate_text(message_content, max_tokens - 20)  # Reserve for metadata
                    
                    if truncated:
                        new_content = content.copy()
                        new_content["content"] = truncated + "..."
                        
                        return ContextElement(
                            source=element.source,
                            content=new_content,
                            relevance_score=element.relevance_score * 0.8,  # Reduce score for truncation
                            tokens=max_tokens
                        )
                        
                elif content.get("type") in ["core_value", "defining_moment"]:
                    # Truncate description
                    description = content.get("description", "")
                    truncated = self._truncate_text(description, max_tokens - 30)
                    
                    if truncated:
                        new_content = content.copy()
                        new_content["description"] = truncated + "..."
                        
                        return ContextElement(
                            source=element.source,
                            content=new_content,
                            relevance_score=element.relevance_score * 0.8,
                            tokens=max_tokens
                        )
            
        except Exception as e:
            logger.warning(f"Error truncating element: {e}")
        
        return None
    
    def _truncate_text(self, text: str, max_tokens: int) -> Optional[str]:
        """Truncate text to fit token budget."""
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        if max_tokens < 10:  # Too small to be useful
            return None
        
        # Truncate tokens and decode back to text
        truncated_tokens = tokens[:max_tokens]
        try:
            return self.encoding.decode(truncated_tokens)
        except Exception:
            # If decoding fails, truncate more conservatively
            truncated_tokens = tokens[:max_tokens - 10]
            try:
                return self.encoding.decode(truncated_tokens)
            except Exception:
                return None
    
    def _calculate_keyword_overlap(self, query: str, text: str) -> float:
        """Calculate relevance based on keyword overlap."""
        try:
            query_words = set(query.lower().split())
            text_words = set(text.lower().split())
            
            if not query_words:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = query_words.intersection(text_words)
            union = query_words.union(text_words)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_semantic_relevance(self, query: str, text: str) -> float:
        """Calculate semantic relevance (enhanced keyword overlap for now)."""
        # Start with keyword overlap
        base_score = self._calculate_keyword_overlap(query, text)
        
        # Boost score for certain semantic indicators
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Boost for essay-related keywords
        essay_keywords = ["essay", "story", "experience", "challenge", "growth", "learning"]
        for keyword in essay_keywords:
            if keyword in query_lower and keyword in text_lower:
                base_score += 0.1
        
        # Boost for action/tool keywords  
        action_keywords = ["help", "write", "create", "improve", "brainstorm", "outline"]
        for keyword in action_keywords:
            if keyword in query_lower and any(word in text_lower for word in ["skill", "develop", "learn"]):
                base_score += 0.05
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def get_context_summary(self, context: RetrievedContext) -> str:
        """Generate a summary of retrieved context.
        
        Args:
            context: Retrieved context to summarize
            
        Returns:
            Human-readable summary of context
        """
        if not context.elements:
            return "No relevant context found."
        
        summary_parts = []
        
        # Group by source
        by_source = {}
        for element in context.elements:
            source = element.source
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(element)
        
        for source, elements in by_source.items():
            count = len(elements)
            avg_relevance = sum(e.relevance_score for e in elements) / count
            
            summary_parts.append(
                f"{source}: {count} items (avg relevance: {avg_relevance:.2f})"
            )
        
        summary = f"Context retrieved: {', '.join(summary_parts)}"
        summary += f"\nTotal tokens: {context.total_tokens}"
        summary += f"\nRetrieval time: {context.retrieval_time:.3f}s"
        
        if context.optimization_applied:
            summary += "\nContext was optimized to fit token budget"
        
        return summary 