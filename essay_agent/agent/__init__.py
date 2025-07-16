"""ReAct Agent Package.

This package contains the core ReAct agent implementation for essay writing assistance.
It replaces the complex conversation management system with a clean, intelligent agent
that uses LLM reasoning for all decision-making.
"""

from .core import EssayReActAgent
from .memory import AgentMemory
from .tools import TOOL_DESCRIPTIONS

# Note: Legacy EssayAgent is in essay_agent.agent_legacy for backward compatibility

# TASK-004: Agent Prompt Templates - Export sophisticated prompt components
from .prompts import (
    ADVANCED_REASONING_PROMPT,
    ENHANCED_CONVERSATION_PROMPT,
    TOOL_SPECIFIC_PROMPTS,
    ERROR_RECOVERY_STRATEGIES,
    PERFORMANCE_OPTIMIZED_PROMPTS,
    format_context_for_reasoning,
    format_tool_descriptions,
    format_tool_result,
    select_reasoning_template,
    inject_memory_context,
    get_performance_context,
    # Legacy compatibility
    REASONING_PROMPT,
    RESPONSE_PROMPT,
    ERROR_RECOVERY_PROMPT,
    CONVERSATION_PROMPT
)

from .prompt_builder import (
    PromptBuilder,
    ContextInjector
)

from .prompt_optimizer import (
    PromptOptimizer,
    PromptVariantManager,
    PromptPerformanceMetrics,
    PromptVariant
)

__all__ = [
    # Core agent components
    "EssayReActAgent",
    "AgentMemory", 
    "TOOL_DESCRIPTIONS",

    
    # TASK-004: Advanced prompt templates and functions
    "ADVANCED_REASONING_PROMPT",
    "ENHANCED_CONVERSATION_PROMPT",
    "TOOL_SPECIFIC_PROMPTS",
    "ERROR_RECOVERY_STRATEGIES",
    "PERFORMANCE_OPTIMIZED_PROMPTS",
    "format_context_for_reasoning",
    "format_tool_descriptions",
    "format_tool_result",
    "select_reasoning_template",
    "inject_memory_context",
    "get_performance_context",
    
    # Legacy prompt compatibility
    "REASONING_PROMPT",
    "RESPONSE_PROMPT", 
    "ERROR_RECOVERY_PROMPT",
    "CONVERSATION_PROMPT",
    
    # Dynamic prompt building
    "PromptBuilder",
    "ContextInjector",
    
    # Performance optimization
    "PromptOptimizer",
    "PromptVariantManager",
    "PromptPerformanceMetrics",
    "PromptVariant"
]

__version__ = "2.0.0-alpha" 