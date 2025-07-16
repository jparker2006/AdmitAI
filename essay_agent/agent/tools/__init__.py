"""Agent tools module with enhanced tool descriptions and analysis."""

from essay_agent.agent.tools.tool_descriptions import (
    ToolDescription,
    TOOL_DESCRIPTIONS,
    TOOL_CATEGORIES,
    get_tool_description,
    get_tools_by_category,
    format_tools_for_llm,
    get_all_tool_names,
    get_category_list
)

from essay_agent.agent.tools.tool_registry import (
    EnhancedToolRegistry,
    ENHANCED_REGISTRY
)

from essay_agent.agent.tools.tool_analyzer import (
    ToolAnalyzer,
    UserIntent,
    ToolRecommendation,
    ContextAnalysis,
    create_tool_analyzer
)

__all__ = [
    # Tool descriptions
    "ToolDescription",
    "TOOL_DESCRIPTIONS", 
    "TOOL_CATEGORIES",
    "get_tool_description",
    "get_tools_by_category",
    "format_tools_for_llm",
    "get_all_tool_names",
    "get_category_list",
    
    # Enhanced registry
    "EnhancedToolRegistry",
    "ENHANCED_REGISTRY",
    
    # Tool analyzer
    "ToolAnalyzer",
    "UserIntent",
    "ToolRecommendation", 
    "ContextAnalysis",
    "create_tool_analyzer"
] 