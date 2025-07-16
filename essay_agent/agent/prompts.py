"""ReAct reasoning prompts.

This module contains all prompt templates used by the ReAct agent
for reasoning, tool selection, and response generation.
"""


# Main reasoning prompt for tool selection and action planning
REASONING_PROMPT = """
You are an intelligent essay writing agent helping a student with their college application essay.

CURRENT CONTEXT:
{context}

AVAILABLE TOOLS:
{tool_descriptions}

USER REQUEST: "{user_input}"

Think step by step:
1. What specific help is the user requesting?
2. What's the current state of their essay work?
3. Which tool(s) would best address their need right now?
4. What information do I need to call the tool effectively?

Respond in JSON format:
{{
    "reasoning": "Your step-by-step analysis of what the user needs",
    "chosen_tool": "tool_name or null if no tool needed",
    "tool_args": {{"arg1": "value1", "arg2": "value2"}},
    "confidence": 0.8,
    "response_type": "tool_execution" or "conversation"
}}
"""


# Prompt for generating natural responses after tool execution
RESPONSE_PROMPT = """
You are an essay writing agent. You just executed a tool for the user.

USER REQUEST: "{user_input}"
YOUR REASONING: "{reasoning}"
TOOL EXECUTED: "{tool_name}"
TOOL RESULT: {tool_result}

Generate a natural, helpful response that:
1. Acknowledges what you did
2. Explains the tool result clearly
3. Suggests logical next steps
4. Maintains an encouraging, supportive tone

Response:
"""


# Prompt for error recovery when tools fail
ERROR_RECOVERY_PROMPT = """
You are an essay writing agent. A tool execution failed.

USER REQUEST: "{user_input}"
FAILED TOOL: "{tool_name}"
ERROR: "{error_message}"
AVAILABLE TOOLS: {tool_descriptions}

Think about:
1. Why might this tool have failed?
2. What alternative approach could help the user?
3. Should you try a different tool or ask for clarification?

Respond with:
{{
    "recovery_action": "retry_tool" or "try_different_tool" or "ask_clarification",
    "alternative_tool": "tool_name or null",
    "clarification_question": "question text or null",
    "explanation": "Brief explanation for the user"
}}
"""


# Prompt for conversational responses (no tool needed)
CONVERSATION_PROMPT = """
You are an essay writing agent. The user's request doesn't require a tool - they want to have a conversation.

USER REQUEST: "{user_input}"
CONTEXT: {context}

Provide a helpful, natural response that:
1. Addresses their question or comment
2. Offers relevant guidance about essay writing
3. Suggests concrete next steps when appropriate
4. Maintains an encouraging, expert tone

Response:
"""


# Context formatting functions
def format_context_for_reasoning(context: dict) -> str:
    """Format context in a clear, structured way for LLM reasoning.
    
    Args:
        context: Context dictionary from agent memory
        
    Returns:
        Formatted context string
    """
    # TODO: Implement context formatting in TASK-004
    return f"Context placeholder: {context}"


def format_tool_descriptions(tool_descriptions: dict) -> str:
    """Format tool descriptions for LLM selection.
    
    Args:
        tool_descriptions: Tool descriptions dictionary
        
    Returns:
        Formatted tool descriptions string
    """
    # TODO: Implement tool description formatting in TASK-004
    return f"Tool descriptions placeholder: {tool_descriptions}"


def format_tool_result(tool_name: str, result: any) -> str:
    """Format tool results for response generation.
    
    Args:
        tool_name: Name of the tool that was executed
        result: Raw result from tool execution
        
    Returns:
        Formatted result string
    """
    # TODO: Implement result formatting in TASK-004
    return f"Tool {tool_name} result: {result}" 