"""ReAct memory data models.

This module contains Pydantic data models for storing and managing
ReAct pattern memory including reasoning chains, tool executions,
usage patterns, and error tracking.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from pydantic import BaseModel, Field


def generate_id() -> str:
    """Generate a unique ID for memory objects."""
    return str(uuid.uuid4())


class ReasoningStep(BaseModel):
    """Individual step in a reasoning chain."""
    step_number: int = Field(description="Order of this step in the reasoning chain")
    thought: str = Field(description="The reasoning or thought at this step")
    tool_considered: Optional[str] = Field(default=None, description="Tool considered for this step")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this reasoning step")
    context_used: List[str] = Field(default_factory=list, description="Context elements used in reasoning")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReasoningChain(BaseModel):
    """Complete reasoning chain from a ReAct episode."""
    id: str = Field(default_factory=generate_id, description="Unique identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When reasoning occurred")
    user_input: str = Field(description="Original user input that triggered reasoning")
    reasoning_steps: List[ReasoningStep] = Field(description="Individual reasoning steps")
    final_action: str = Field(description="Final action chosen after reasoning")
    result: Any = Field(description="Result of the action taken")
    success: bool = Field(description="Whether the reasoning led to successful outcome")
    execution_time: float = Field(description="Time taken for reasoning and execution (seconds)")
    context_tokens: int = Field(default=0, description="Number of tokens used in context")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ToolExecution(BaseModel):
    """Record of tool execution with context and results."""
    id: str = Field(default_factory=generate_id, description="Unique identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When execution occurred")
    tool_name: str = Field(description="Name of the tool executed")
    input_params: Dict[str, Any] = Field(description="Input parameters passed to tool")
    result: Any = Field(description="Result returned by tool")
    execution_time: float = Field(description="Time taken for execution (seconds)")
    success: bool = Field(description="Whether execution was successful")
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")
    reasoning_context: str = Field(description="Reasoning that led to this tool execution")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in tool choice")
    tokens_used: int = Field(default=0, description="Estimated tokens used by tool")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UsagePattern(BaseModel):
    """Detected pattern in tool usage or reasoning."""
    pattern_type: str = Field(description="Type of pattern (sequence, frequency, context, etc.)")
    tools: List[str] = Field(description="Tools involved in this pattern")
    frequency: int = Field(description="How often this pattern occurs")
    success_rate: float = Field(ge=0.0, le=1.0, description="Success rate of this pattern")
    avg_execution_time: float = Field(description="Average execution time for this pattern")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in pattern validity")
    context_indicators: List[str] = Field(default_factory=list, description="Context that triggers this pattern")
    last_seen: datetime = Field(default_factory=datetime.now, description="When pattern was last observed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorPattern(BaseModel):
    """Pattern of errors for prevention and learning."""
    error_type: str = Field(description="Type of error (tool_failure, reasoning_error, etc.)")
    tools_involved: List[str] = Field(description="Tools involved when error occurred")
    frequency: int = Field(description="How often this error pattern occurs")
    typical_context: str = Field(description="Common context when this error happens")
    error_messages: List[str] = Field(description="Common error messages for this pattern")
    suggested_fix: str = Field(description="Suggested approach to prevent this error")
    severity: str = Field(description="Error severity (low, medium, high)")
    last_occurrence: datetime = Field(default_factory=datetime.now, description="When error last occurred")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContextElement(BaseModel):
    """Individual element of context for reasoning."""
    source: str = Field(description="Source of context (conversation, semantic, tool_history, etc.)")
    content: Any = Field(description="The actual context content")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance to current query")
    tokens: int = Field(description="Estimated token count for this context")
    timestamp: datetime = Field(default_factory=datetime.now, description="When context was retrieved")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RetrievedContext(BaseModel):
    """Complete context retrieved for reasoning."""
    query: str = Field(description="Query used for context retrieval")
    elements: List[ContextElement] = Field(description="Individual context elements")
    total_tokens: int = Field(description="Total tokens across all elements")
    retrieval_time: float = Field(description="Time taken to retrieve context (seconds)")
    optimization_applied: bool = Field(default=False, description="Whether context was optimized for token limits")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Data classes for memory indexing (using dataclasses for performance)
@dataclass
class MemoryIndex:
    """Index entry for fast memory lookups."""
    id: str
    timestamp: datetime
    type: str  # reasoning_chain, tool_execution, usage_pattern, error_pattern
    keywords: List[str]
    hash_key: str = field(default="")
    
    def __post_init__(self):
        if not self.hash_key:
            # Generate hash from keywords for fast lookup
            import hashlib
            self.hash_key = hashlib.md5(
                " ".join(sorted(self.keywords)).encode()
            ).hexdigest()


@dataclass 
class PatternMatch:
    """Result of pattern matching operation."""
    pattern: Union[UsagePattern, ErrorPattern]
    confidence: float
    context_similarity: float
    tools_match: bool
    

class MemoryStats(BaseModel):
    """Statistics about agent memory usage."""
    total_reasoning_chains: int = 0
    total_tool_executions: int = 0
    total_usage_patterns: int = 0
    total_error_patterns: int = 0
    avg_reasoning_time: float = 0.0
    avg_tool_execution_time: float = 0.0
    success_rate: float = 0.0
    most_used_tools: List[str] = Field(default_factory=list)
    memory_size_mb: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 