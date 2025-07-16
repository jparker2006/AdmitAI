"""Memory indexing system for pattern detection and efficient retrieval.

This module provides pattern detection capabilities and efficient indexing
for ReAct memory operations including usage patterns, error analysis,
and performance optimization.
"""
from __future__ import annotations

import json
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Counter
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import asdict

from .react_models import (
    ReasoningChain, ToolExecution, UsagePattern, ErrorPattern,
    MemoryIndex, PatternMatch, MemoryStats
)

logger = logging.getLogger(__name__)


def safe_json_serialize(obj):
    """Safely serialize objects to JSON with datetime handling and Pydantic compatibility.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable representation of the object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'model_dump'):  # Pydantic v2
        return obj.model_dump()
    elif hasattr(obj, 'dict'):  # Pydantic v1 fallback
        return obj.dict()
    elif isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json_serialize(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Fallback to string representation for other types
        return str(obj)


class MemoryIndexer:
    """Pattern detection and efficient memory indexing.
    
    Provides intelligent analysis of memory patterns to improve agent
    performance through usage pattern detection, error analysis, and
    optimization recommendations.
    """
    
    def __init__(self, user_id: str):
        """Initialize memory indexer.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.memory_dir = Path("memory_store")
        self.memory_dir.mkdir(exist_ok=True)
        
        # Index files
        self.index_file = self.memory_dir / f"{user_id}.memory_index.json"
        self.patterns_file = self.memory_dir / f"{user_id}.patterns.json"
        self.stats_file = self.memory_dir / f"{user_id}.memory_stats.json"
        
        # In-memory indexes
        self.memory_index: Dict[str, MemoryIndex] = {}
        self.pattern_cache: Dict[str, List[UsagePattern]] = {}
        self.error_cache: Dict[str, List[ErrorPattern]] = {}
        self.tool_sequences: List[List[str]] = []
        
        # Load existing indexes
        self._load_indexes()
    
    def index_reasoning_chain(self, chain: ReasoningChain) -> None:
        """Index reasoning chain for pattern detection.
        
        Args:
            chain: Reasoning chain to index
        """
        try:
            # Extract keywords from reasoning chain
            keywords = self._extract_keywords_from_chain(chain)
            
            # Create index entry
            index_entry = MemoryIndex(
                id=chain.id,
                timestamp=chain.timestamp,
                type="reasoning_chain",
                keywords=keywords
            )
            
            self.memory_index[chain.id] = index_entry
            
            # Analyze for patterns
            self._analyze_reasoning_patterns(chain)
            
            # Save to persistent storage
            self._save_reasoning_chain(chain)
            
            logger.debug(f"Indexed reasoning chain {chain.id} with {len(keywords)} keywords")
            
        except Exception as e:
            logger.error(f"Error indexing reasoning chain: {e}")
    
    def index_tool_execution(self, execution: ToolExecution) -> None:
        """Index tool execution for usage patterns.
        
        Args:
            execution: Tool execution to index
        """
        try:
            # Extract keywords from tool execution
            keywords = self._extract_keywords_from_execution(execution)
            
            # Create index entry
            index_entry = MemoryIndex(
                id=execution.id,
                timestamp=execution.timestamp,
                type="tool_execution",
                keywords=keywords
            )
            
            self.memory_index[execution.id] = index_entry
            
            # Update tool sequences for pattern detection
            self._update_tool_sequences(execution)
            
            # Analyze for error patterns if execution failed
            if not execution.success:
                self._analyze_error_patterns(execution)
            
            # Save to persistent storage
            self._save_tool_execution(execution)
            
            logger.debug(f"Indexed tool execution {execution.id} for tool {execution.tool_name}")
            
        except Exception as e:
            logger.error(f"Error indexing tool execution: {e}")
    
    def detect_usage_patterns(self, lookback_days: int = 30) -> List[UsagePattern]:
        """Detect tool usage patterns for recommendations.
        
        Args:
            lookback_days: Days to look back for pattern detection
            
        Returns:
            List of detected usage patterns
        """
        try:
            patterns = []
            
            # Get recent tool executions
            recent_executions = self._get_recent_tool_executions(lookback_days)
            
            if len(recent_executions) < 3:  # Need minimum data for patterns
                return patterns
            
            # Detect sequence patterns
            patterns.extend(self._detect_sequence_patterns(recent_executions))
            
            # Detect frequency patterns
            patterns.extend(self._detect_frequency_patterns(recent_executions))
            
            # Detect context patterns
            patterns.extend(self._detect_context_patterns(recent_executions))
            
            # Filter and rank patterns
            patterns = self._filter_and_rank_patterns(patterns)
            
            # Cache patterns
            self.pattern_cache[f"usage_{lookback_days}"] = patterns
            
            logger.info(f"Detected {len(patterns)} usage patterns from {len(recent_executions)} executions")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting usage patterns: {e}")
            return []
    
    def detect_error_patterns(self, lookback_days: int = 30) -> List[ErrorPattern]:
        """Detect error patterns for prevention.
        
        Args:
            lookback_days: Days to look back for error analysis
            
        Returns:
            List of detected error patterns
        """
        try:
            error_patterns = []
            
            # Get recent failed executions
            failed_executions = self._get_failed_tool_executions(lookback_days)
            
            if len(failed_executions) < 2:  # Need minimum errors for patterns
                return error_patterns
            
            # Group errors by type and context
            error_groups = self._group_errors_by_similarity(failed_executions)
            
            # Analyze each group for patterns
            for error_type, executions in error_groups.items():
                if len(executions) >= 2:  # Pattern needs multiple occurrences
                    pattern = self._create_error_pattern(error_type, executions)
                    if pattern:
                        error_patterns.append(pattern)
            
            # Cache error patterns
            self.error_cache[f"errors_{lookback_days}"] = error_patterns
            
            logger.info(f"Detected {len(error_patterns)} error patterns from {len(failed_executions)} failures")
            
            return error_patterns
            
        except Exception as e:
            logger.error(f"Error detecting error patterns: {e}")
            return []
    
    def find_similar_patterns(self, 
                             query_context: str, 
                             pattern_type: str = "usage") -> List[PatternMatch]:
        """Find patterns similar to current context.
        
        Args:
            query_context: Current context to match against
            pattern_type: Type of patterns to search (usage, error)
            
        Returns:
            List of matching patterns with similarity scores
        """
        try:
            matches = []
            
            # Get relevant pattern cache
            if pattern_type == "usage":
                patterns = self.pattern_cache.get("usage_30", [])
            elif pattern_type == "error":
                patterns = self.error_cache.get("errors_30", [])
            else:
                return matches
            
            # Calculate similarity to each pattern
            for pattern in patterns:
                similarity = self._calculate_pattern_similarity(query_context, pattern)
                
                if similarity > 0.3:  # Minimum similarity threshold
                    match = PatternMatch(
                        pattern=pattern,
                        confidence=similarity,
                        context_similarity=similarity,
                        tools_match=self._check_tools_overlap(query_context, pattern)
                    )
                    matches.append(match)
            
            # Sort by confidence
            matches.sort(key=lambda x: x.confidence, reverse=True)
            
            return matches[:10]  # Return top 10 matches
            
        except Exception as e:
            logger.error(f"Error finding similar patterns: {e}")
            return []
    
    def get_memory_stats(self) -> MemoryStats:
        """Get comprehensive memory usage statistics.
        
        Returns:
            Memory statistics object
        """
        try:
            # Count different memory types
            reasoning_chains = self._count_items_by_type("reasoning_chain")
            tool_executions = self._count_items_by_type("tool_execution")
            usage_patterns = sum(len(patterns) for patterns in self.pattern_cache.values())
            error_patterns = sum(len(patterns) for patterns in self.error_cache.values())
            
            # Calculate averages
            avg_reasoning_time = self._calculate_avg_reasoning_time()
            avg_tool_time = self._calculate_avg_tool_execution_time()
            success_rate = self._calculate_success_rate()
            most_used_tools = self._get_most_used_tools()
            
            # Calculate memory size
            memory_size_mb = self._calculate_memory_size()
            
            stats = MemoryStats(
                total_reasoning_chains=reasoning_chains,
                total_tool_executions=tool_executions,
                total_usage_patterns=usage_patterns,
                total_error_patterns=error_patterns,
                avg_reasoning_time=avg_reasoning_time,
                avg_tool_execution_time=avg_tool_time,
                success_rate=success_rate,
                most_used_tools=most_used_tools,
                memory_size_mb=memory_size_mb,
                last_updated=datetime.now()
            )
            
            # Save stats
            self._save_stats(stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating memory stats: {e}")
            return MemoryStats()
    
    def _extract_keywords_from_chain(self, chain: ReasoningChain) -> List[str]:
        """Extract keywords from reasoning chain."""
        keywords = set()
        
        # Add keywords from user input
        keywords.update(self._extract_keywords_from_text(chain.user_input))
        
        # Add keywords from reasoning steps
        for step in chain.reasoning_steps:
            keywords.update(self._extract_keywords_from_text(step.thought))
            if step.tool_considered:
                keywords.add(step.tool_considered)
        
        # Add final action
        keywords.add(chain.final_action)
        
        # Add success/failure context
        keywords.add("success" if chain.success else "failure")
        
        return list(keywords)
    
    def _extract_keywords_from_execution(self, execution: ToolExecution) -> List[str]:
        """Extract keywords from tool execution."""
        keywords = set()
        
        # Add tool name
        keywords.add(execution.tool_name)
        
        # Add keywords from reasoning context
        keywords.update(self._extract_keywords_from_text(execution.reasoning_context))
        
        # Add success/failure context
        keywords.add("success" if execution.success else "failure")
        
        # Add error type if failed
        if execution.error_message:
            keywords.update(self._extract_keywords_from_text(execution.error_message))
        
        return list(keywords)
    
    def _extract_keywords_from_text(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        if not text:
            return set()
        
        # Simple keyword extraction (could be enhanced with NLP)
        words = text.lower().split()
        
        # Filter out common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "this", "that", "these", "those"
        }
        
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}
        
        return keywords
    
    def _analyze_reasoning_patterns(self, chain: ReasoningChain) -> None:
        """Analyze reasoning chain for patterns."""
        try:
            # Track reasoning step patterns
            if len(chain.reasoning_steps) > 1:
                step_sequence = [step.tool_considered for step in chain.reasoning_steps 
                               if step.tool_considered]
                if step_sequence:
                    self.tool_sequences.append(step_sequence)
            
            # TODO: Add more sophisticated reasoning analysis
            
        except Exception as e:
            logger.error(f"Error analyzing reasoning patterns: {e}")
    
    def _update_tool_sequences(self, execution: ToolExecution) -> None:
        """Update tool sequences for pattern detection."""
        try:
            # This is a simplified approach - in practice, we'd track
            # sequences within reasoning chains or conversation turns
            
            # For now, just track individual tool usage
            if not hasattr(self, '_recent_tools'):
                self._recent_tools = []
            
            self._recent_tools.append(execution.tool_name)
            
            # Keep only recent tools (last 20)
            if len(self._recent_tools) > 20:
                self._recent_tools = self._recent_tools[-20:]
                
        except Exception as e:
            logger.error(f"Error updating tool sequences: {e}")
    
    def _analyze_error_patterns(self, execution: ToolExecution) -> None:
        """Analyze failed execution for error patterns."""
        try:
            # Simple error categorization
            error_type = "unknown_error"
            
            if execution.error_message:
                error_msg = execution.error_message.lower()
                
                if "timeout" in error_msg:
                    error_type = "timeout_error"
                elif "validation" in error_msg:
                    error_type = "validation_error"
                elif "not found" in error_msg:
                    error_type = "not_found_error"
                elif "permission" in error_msg:
                    error_type = "permission_error"
                elif "network" in error_msg or "connection" in error_msg:
                    error_type = "network_error"
            
            # Store error context for pattern detection
            if not hasattr(self, '_error_contexts'):
                self._error_contexts = defaultdict(list)
            
            self._error_contexts[error_type].append({
                "tool": execution.tool_name,
                "context": execution.reasoning_context,
                "timestamp": execution.timestamp,
                "error_message": execution.error_message
            })
            
        except Exception as e:
            logger.error(f"Error analyzing error patterns: {e}")
    
    def _get_recent_tool_executions(self, days: int) -> List[ToolExecution]:
        """Get recent tool executions for pattern detection."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            executions = []
            
            # Load from persistent storage
            tool_history_file = self.memory_dir / f"{self.user_id}.tool_history.json"
            
            if tool_history_file.exists():
                with open(tool_history_file, 'r') as f:
                    tool_data = json.load(f)
                
                for data in tool_data:
                    timestamp = datetime.fromisoformat(data.get("timestamp", ""))
                    if timestamp >= cutoff_date:
                        execution = ToolExecution(**data)
                        executions.append(execution)
            
            return executions
            
        except Exception as e:
            logger.error(f"Error getting recent tool executions: {e}")
            return []
    
    def _get_failed_tool_executions(self, days: int) -> List[ToolExecution]:
        """Get recent failed tool executions."""
        recent_executions = self._get_recent_tool_executions(days)
        return [exec for exec in recent_executions if not exec.success]
    
    def _detect_sequence_patterns(self, executions: List[ToolExecution]) -> List[UsagePattern]:
        """Detect tool sequence patterns."""
        patterns = []
        
        try:
            # Group executions by time windows to find sequences
            time_windows = self._group_executions_by_time_window(executions, minutes=30)
            
            # Find common sequences
            sequences = []
            for window in time_windows:
                if len(window) > 1:
                    sequence = [exec.tool_name for exec in window]
                    sequences.append(sequence)
            
            # Count sequence patterns
            sequence_counts = Counter(tuple(seq) for seq in sequences if len(seq) > 1)
            
            # Create patterns for common sequences
            for sequence_tuple, count in sequence_counts.most_common(10):
                if count >= 2:  # Must occur at least twice
                    sequence_list = list(sequence_tuple)
                    
                    # Calculate metrics for this sequence
                    matching_windows = [w for w in time_windows 
                                      if [e.tool_name for e in w] == sequence_list]
                    
                    success_count = sum(1 for window in matching_windows 
                                      if all(e.success for e in window))
                    success_rate = success_count / len(matching_windows)
                    
                    avg_time = sum(sum(e.execution_time for e in window) 
                                 for window in matching_windows) / len(matching_windows)
                    
                    pattern = UsagePattern(
                        pattern_type="sequence",
                        tools=sequence_list,
                        frequency=count,
                        success_rate=success_rate,
                        avg_execution_time=avg_time,
                        confidence=min(count / 10.0, 1.0),  # Confidence based on frequency
                        context_indicators=self._extract_sequence_context(matching_windows)
                    )
                    patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error detecting sequence patterns: {e}")
        
        return patterns
    
    def _detect_frequency_patterns(self, executions: List[ToolExecution]) -> List[UsagePattern]:
        """Detect tool frequency patterns."""
        patterns = []
        
        try:
            # Count tool usage frequency
            tool_counts = Counter(exec.tool_name for exec in executions)
            
            # Calculate metrics for each frequently used tool
            for tool_name, count in tool_counts.most_common(10):
                if count >= 3:  # Must be used at least 3 times
                    tool_executions = [e for e in executions if e.tool_name == tool_name]
                    
                    success_count = sum(1 for e in tool_executions if e.success)
                    success_rate = success_count / len(tool_executions)
                    avg_time = sum(e.execution_time for e in tool_executions) / len(tool_executions)
                    
                    # Extract common context indicators
                    contexts = [e.reasoning_context for e in tool_executions]
                    context_keywords = self._extract_common_keywords(contexts)
                    
                    pattern = UsagePattern(
                        pattern_type="frequency",
                        tools=[tool_name],
                        frequency=count,
                        success_rate=success_rate,
                        avg_execution_time=avg_time,
                        confidence=min(count / 20.0, 1.0),
                        context_indicators=context_keywords
                    )
                    patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error detecting frequency patterns: {e}")
        
        return patterns
    
    def _detect_context_patterns(self, executions: List[ToolExecution]) -> List[UsagePattern]:
        """Detect context-based tool usage patterns."""
        patterns = []
        
        try:
            # Group executions by similar reasoning context
            context_groups = self._group_executions_by_context_similarity(executions)
            
            for context_keywords, group_executions in context_groups.items():
                if len(group_executions) >= 3:  # Need multiple examples
                    # Find most common tools in this context
                    tool_counts = Counter(e.tool_name for e in group_executions)
                    
                    for tool_name, count in tool_counts.most_common(3):
                        if count >= 2:
                            tool_executions = [e for e in group_executions 
                                             if e.tool_name == tool_name]
                            
                            success_count = sum(1 for e in tool_executions if e.success)
                            success_rate = success_count / len(tool_executions)
                            avg_time = sum(e.execution_time for e in tool_executions) / len(tool_executions)
                            
                            pattern = UsagePattern(
                                pattern_type="context",
                                tools=[tool_name],
                                frequency=count,
                                success_rate=success_rate,
                                avg_execution_time=avg_time,
                                confidence=min(success_rate * count / 5.0, 1.0),
                                context_indicators=list(context_keywords.split(","))
                            )
                            patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error detecting context patterns: {e}")
        
        return patterns
    
    def _group_executions_by_time_window(self, 
                                        executions: List[ToolExecution], 
                                        minutes: int = 30) -> List[List[ToolExecution]]:
        """Group executions by time windows."""
        if not executions:
            return []
        
        # Sort by timestamp
        sorted_executions = sorted(executions, key=lambda x: x.timestamp)
        
        windows = []
        current_window = [sorted_executions[0]]
        window_start = sorted_executions[0].timestamp
        
        for execution in sorted_executions[1:]:
            time_diff = (execution.timestamp - window_start).total_seconds() / 60
            
            if time_diff <= minutes:
                current_window.append(execution)
            else:
                windows.append(current_window)
                current_window = [execution]
                window_start = execution.timestamp
        
        if current_window:
            windows.append(current_window)
        
        return windows
    
    def _group_executions_by_context_similarity(self, 
                                               executions: List[ToolExecution]) -> Dict[str, List[ToolExecution]]:
        """Group executions by similar reasoning context."""
        groups = defaultdict(list)
        
        for execution in executions:
            # Extract key context words
            context_keywords = self._extract_keywords_from_text(execution.reasoning_context)
            # Create a signature from top keywords
            key_words = sorted(list(context_keywords))[:5]  # Top 5 keywords
            signature = ",".join(key_words)
            
            groups[signature].append(execution)
        
        # Filter groups with too few members
        return {k: v for k, v in groups.items() if len(v) >= 2}
    
    def _extract_sequence_context(self, windows: List[List[ToolExecution]]) -> List[str]:
        """Extract common context from sequence windows."""
        all_contexts = []
        for window in windows:
            for execution in window:
                all_contexts.append(execution.reasoning_context)
        
        return self._extract_common_keywords(all_contexts)
    
    def _extract_common_keywords(self, contexts: List[str]) -> List[str]:
        """Extract common keywords from multiple contexts."""
        if not contexts:
            return []
        
        # Get keywords from each context
        all_keywords = []
        for context in contexts:
            keywords = self._extract_keywords_from_text(context)
            all_keywords.extend(keywords)
        
        # Find most common keywords
        keyword_counts = Counter(all_keywords)
        
        # Return keywords that appear in at least 30% of contexts
        min_frequency = max(1, len(contexts) * 0.3)
        common_keywords = [word for word, count in keyword_counts.items() 
                          if count >= min_frequency]
        
        return common_keywords[:10]  # Top 10 common keywords
    
    def _filter_and_rank_patterns(self, patterns: List[UsagePattern]) -> List[UsagePattern]:
        """Filter and rank patterns by relevance."""
        # Filter out low-confidence patterns
        filtered = [p for p in patterns if p.confidence > 0.2]
        
        # Sort by a combination of confidence and frequency
        filtered.sort(key=lambda p: (p.confidence * 0.7 + (p.frequency / 20.0) * 0.3), reverse=True)
        
        return filtered[:20]  # Top 20 patterns
    
    def _group_errors_by_similarity(self, 
                                   failed_executions: List[ToolExecution]) -> Dict[str, List[ToolExecution]]:
        """Group errors by similarity."""
        groups = defaultdict(list)
        
        for execution in failed_executions:
            # Simple error categorization
            error_type = "unknown"
            
            if execution.error_message:
                error_msg = execution.error_message.lower()
                if "timeout" in error_msg:
                    error_type = "timeout"
                elif "validation" in error_msg:
                    error_type = "validation"
                elif "not found" in error_msg:
                    error_type = "not_found"
                elif "permission" in error_msg:
                    error_type = "permission"
                elif "network" in error_msg:
                    error_type = "network"
            
            groups[error_type].append(execution)
        
        return groups
    
    def _create_error_pattern(self, error_type: str, executions: List[ToolExecution]) -> Optional[ErrorPattern]:
        """Create error pattern from grouped executions."""
        try:
            if len(executions) < 2:
                return None
            
            tools_involved = list(set(e.tool_name for e in executions))
            error_messages = [e.error_message for e in executions if e.error_message]
            
            # Extract common context
            contexts = [e.reasoning_context for e in executions]
            common_context = " ".join(self._extract_common_keywords(contexts))
            
            # Determine severity based on frequency and impact
            frequency = len(executions)
            if frequency > 10:
                severity = "high"
            elif frequency > 5:
                severity = "medium"
            else:
                severity = "low"
            
            # Generate suggested fix based on error type
            suggested_fix = self._generate_error_fix_suggestion(error_type, tools_involved)
            
            pattern = ErrorPattern(
                error_type=error_type,
                tools_involved=tools_involved,
                frequency=frequency,
                typical_context=common_context,
                error_messages=error_messages[:5],  # Keep top 5 messages
                suggested_fix=suggested_fix,
                severity=severity,
                last_occurrence=max(e.timestamp for e in executions)
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error creating error pattern: {e}")
            return None
    
    def _generate_error_fix_suggestion(self, error_type: str, tools: List[str]) -> str:
        """Generate fix suggestion based on error type."""
        suggestions = {
            "timeout": "Consider increasing timeout limits or optimizing tool performance",
            "validation": "Check input parameters and ensure they meet tool requirements",
            "not_found": "Verify that required resources exist before tool execution",
            "permission": "Check user permissions and authentication settings",
            "network": "Implement retry logic for network-related operations",
            "unknown": "Add better error handling and logging to diagnose issues"
        }
        
        base_suggestion = suggestions.get(error_type, suggestions["unknown"])
        
        if len(tools) == 1:
            return f"{base_suggestion} for {tools[0]} tool"
        else:
            return f"{base_suggestion} for tools: {', '.join(tools)}"
    
    def _calculate_pattern_similarity(self, query_context: str, pattern: UsagePattern) -> float:
        """Calculate similarity between query context and pattern."""
        try:
            query_keywords = self._extract_keywords_from_text(query_context)
            pattern_keywords = set(pattern.context_indicators)
            
            if not query_keywords or not pattern_keywords:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = query_keywords.intersection(pattern_keywords)
            union = query_keywords.union(pattern_keywords)
            
            similarity = len(intersection) / len(union) if union else 0.0
            
            # Boost similarity for successful patterns
            if pattern.success_rate > 0.8:
                similarity *= 1.2
            
            return min(similarity, 1.0)
            
        except Exception:
            return 0.0
    
    def _check_tools_overlap(self, query_context: str, pattern: UsagePattern) -> bool:
        """Check if query context suggests tools in pattern."""
        query_lower = query_context.lower()
        
        for tool in pattern.tools:
            if tool.lower() in query_lower:
                return True
        
        return False
    
    # Statistics calculation methods
    def _count_items_by_type(self, item_type: str) -> int:
        """Count memory items by type."""
        return sum(1 for index in self.memory_index.values() if index.type == item_type)
    
    def _calculate_avg_reasoning_time(self) -> float:
        """Calculate average reasoning time."""
        try:
            reasoning_file = self.memory_dir / f"{self.user_id}.reasoning_history.json"
            if not reasoning_file.exists():
                return 0.0
            
            with open(reasoning_file, 'r') as f:
                chains = json.load(f)
            
            if not chains:
                return 0.0
            
            total_time = sum(chain.get("execution_time", 0) for chain in chains)
            return total_time / len(chains)
            
        except Exception:
            return 0.0
    
    def _calculate_avg_tool_execution_time(self) -> float:
        """Calculate average tool execution time."""
        try:
            tool_file = self.memory_dir / f"{self.user_id}.tool_history.json"
            if not tool_file.exists():
                return 0.0
            
            with open(tool_file, 'r') as f:
                executions = json.load(f)
            
            if not executions:
                return 0.0
            
            total_time = sum(exec.get("execution_time", 0) for exec in executions)
            return total_time / len(executions)
            
        except Exception:
            return 0.0
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        try:
            tool_file = self.memory_dir / f"{self.user_id}.tool_history.json"
            if not tool_file.exists():
                return 1.0
            
            with open(tool_file, 'r') as f:
                executions = json.load(f)
            
            if not executions:
                return 1.0
            
            successful = sum(1 for exec in executions if exec.get("success", True))
            return successful / len(executions)
            
        except Exception:
            return 1.0
    
    def _get_most_used_tools(self) -> List[str]:
        """Get list of most used tools."""
        try:
            tool_file = self.memory_dir / f"{self.user_id}.tool_history.json"
            if not tool_file.exists():
                return []
            
            with open(tool_file, 'r') as f:
                executions = json.load(f)
            
            tool_counts = Counter(exec.get("tool_name", "") for exec in executions)
            return [tool for tool, count in tool_counts.most_common(10)]
            
        except Exception:
            return []
    
    def _calculate_memory_size(self) -> float:
        """Calculate total memory size in MB."""
        try:
            total_size = 0
            
            for file_path in self.memory_dir.glob(f"{self.user_id}.*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception:
            return 0.0
    
    # Persistence methods
    def _save_reasoning_chain(self, chain: ReasoningChain) -> None:
        """Save reasoning chain to persistent storage."""
        try:
            reasoning_file = self.memory_dir / f"{self.user_id}.reasoning_history.json"
            
            # Load existing chains
            chains = []
            if reasoning_file.exists():
                try:
                    with open(reasoning_file, 'r') as f:
                        chains = json.load(f)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Could not parse existing reasoning history, starting fresh: {e}")
                    chains = []
            
            # Add new chain with safe serialization
            chains.append(safe_json_serialize(chain))
            
            # Keep only recent chains (last 100)
            if len(chains) > 100:
                chains = chains[-100:]
            
            # Save back
            with open(reasoning_file, 'w') as f:
                json.dump(chains, f, indent=2, default=safe_json_serialize)
                
        except Exception as e:
            logger.error(f"Error saving reasoning chain: {e}")
    
    def _save_tool_execution(self, execution: ToolExecution) -> None:
        """Save tool execution to persistent storage."""
        try:
            tool_file = self.memory_dir / f"{self.user_id}.tool_history.json"
            
            # Load existing executions
            executions = []
            if tool_file.exists():
                try:
                    with open(tool_file, 'r') as f:
                        executions = json.load(f)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Could not parse existing tool history, starting fresh: {e}")
                    executions = []
            
            # Add new execution with safe serialization
            executions.append(safe_json_serialize(execution))
            
            # Keep only recent executions (last 200)
            if len(executions) > 200:
                executions = executions[-200:]
            
            # Save back
            with open(tool_file, 'w') as f:
                json.dump(executions, f, indent=2, default=safe_json_serialize)
                
        except Exception as e:
            logger.error(f"Error saving tool execution: {e}")
    
    def _save_stats(self, stats: MemoryStats) -> None:
        """Save memory statistics."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory stats: {e}")
    
    def _load_indexes(self) -> None:
        """Load existing indexes from storage."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    index_data = json.load(f)
                
                for item_id, data in index_data.items():
                    index = MemoryIndex(
                        id=data["id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        type=data["type"],
                        keywords=data["keywords"],
                        hash_key=data.get("hash_key", "")
                    )
                    self.memory_index[item_id] = index
            
            logger.info(f"Loaded {len(self.memory_index)} memory indexes")
            
        except Exception as e:
            logger.error(f"Error loading indexes: {e}")
    
    def save_indexes(self) -> None:
        """Save indexes to persistent storage."""
        try:
            index_data = {}
            for item_id, index in self.memory_index.items():
                index_data[item_id] = {
                    "id": index.id,
                    "timestamp": index.timestamp.isoformat(),
                    "type": index.type,
                    "keywords": index.keywords,
                    "hash_key": index.hash_key
                }
            
            with open(self.index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
                
            logger.debug(f"Saved {len(self.memory_index)} memory indexes")
            
        except Exception as e:
            logger.error(f"Error saving indexes: {e}") 