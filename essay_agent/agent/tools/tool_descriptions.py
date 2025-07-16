"""Rich tool descriptions for LLM reasoning.

This module contains comprehensive descriptions of all available tools
that enable the LLM to make intelligent decisions about which tools
to use based on user context and intent.
"""
from typing import Dict, Any


# Tool description schema for consistent LLM reasoning
TOOL_DESCRIPTION_SCHEMA = {
    "description": "Clear, detailed description of what this tool does",
    "when_to_use": "Specific situations where this tool is most helpful", 
    "requires": ["list", "of", "required", "inputs"],
    "output": "Description of what the tool returns",
    "examples": ["Example user request 1", "Example user request 2"]
}


# Comprehensive tool descriptions for agent reasoning
# TODO: Complete all tool descriptions in TASK-002
TOOL_DESCRIPTIONS: Dict[str, Dict[str, Any]] = {
    "brainstorm": {
        "description": "Generate personal stories and essay ideas based on user's profile and experiences",
        "when_to_use": "When user needs ideas, stories, or is stuck on what to write about",
        "requires": ["essay_prompt", "user_profile"],
        "output": "List of personal stories with details and relevance scores",
        "examples": [
            "I need help brainstorming essay ideas",
            "What stories could I write about?",
            "Help me think of ideas for a challenge essay"
        ]
    },
    
    # TODO: Add descriptions for all 30+ tools in TASK-002:
    # - Core tools: outline, draft, revise, polish
    # - Specialized tools: suggest_stories, expand_story, validate_uniqueness
    # - Writing tools: rewrite_paragraph, improve_opening, strengthen_voice
    # - Evaluation tools: essay_scoring, weakness_highlight, cliche_detection
    # - Structure tools: outline_generator, structure_validator, transition_suggestion
    # - Polish tools: fix_grammar, enhance_vocabulary, check_consistency
    # And more...
}


def get_tool_description(tool_name: str) -> Dict[str, Any]:
    """Get description for a specific tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool description dictionary
        
    Raises:
        KeyError: If tool not found
    """
    if tool_name not in TOOL_DESCRIPTIONS:
        raise KeyError(f"Tool '{tool_name}' not found in descriptions")
    return TOOL_DESCRIPTIONS[tool_name]


def format_tools_for_llm() -> str:
    """Format all tool descriptions for LLM reasoning.
    
    Returns:
        Formatted string of all tool descriptions
    """
    formatted = []
    for tool_name, desc in TOOL_DESCRIPTIONS.items():
        tool_text = f"""
**{tool_name}**
- Description: {desc['description']}
- When to use: {desc['when_to_use']}
- Requires: {', '.join(desc['requires'])}
- Output: {desc['output']}
"""
        formatted.append(tool_text)
    
    return "\n".join(formatted)


def get_tools_by_category() -> Dict[str, list]:
    """Group tools by category for better organization.
    
    Returns:
        Dictionary mapping categories to tool lists
    """
    # TODO: Implement tool categorization in TASK-002
    return {
        "core_workflow": ["brainstorm", "outline", "draft", "revise", "polish"],
        "brainstorming": ["suggest_stories", "expand_story", "validate_uniqueness"],
        "writing": ["rewrite_paragraph", "improve_opening", "strengthen_voice"],
        "evaluation": ["essay_scoring", "weakness_highlight", "cliche_detection"],
        "structure": ["outline_generator", "structure_validator", "transition_suggestion"],
        "polish": ["fix_grammar", "enhance_vocabulary", "check_consistency"]
    } 