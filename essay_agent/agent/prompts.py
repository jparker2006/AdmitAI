"""ReAct reasoning prompts.

This module contains all prompt templates used by the ReAct agent
for reasoning, tool selection, and response generation with sophisticated
context awareness and dynamic prompt generation capabilities.
"""
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime


# ============================================================================
# ADVANCED REACT REASONING TEMPLATES
# ============================================================================

# Enhanced main reasoning prompt with sophisticated context awareness
ADVANCED_REASONING_PROMPT = """
You are an intelligent essay writing agent with deep expertise in college application essays.
Your goal is to help students craft authentic, compelling essays that showcase their unique voice and experiences.

CONVERSATION CONTEXT:
{conversation_context}

MEMORY CONTEXT:
{memory_context}

CURRENT USER STATE:
{user_state}

AVAILABLE TOOLS:
{tool_descriptions}

RECENT PERFORMANCE PATTERNS:
{performance_context}

USER REQUEST: "{user_input}"

===== REASONING FRAMEWORK =====
Apply sophisticated reasoning using these steps:

1. CONTEXT ANALYSIS:
   - What is the user's current position in their essay journey?
   - What relevant memories and patterns inform this moment?
   - What emotional or cognitive state might they be in?

2. INTENT RECOGNITION:
   - What specific help is the user requesting (explicit and implicit)?
   - What underlying needs might they not be expressing?
   - How does this connect to their broader essay goals?

3. TOOL EVALUATION:
   - Which tools could address their immediate need?
   - What are the success patterns for similar contexts?
   - What are the risks and benefits of each tool option?

4. STRATEGIC PLANNING:
   - What is the optimal sequence of actions?
   - How can we build momentum and confidence?
   - What follow-up actions should we anticipate?

Respond in JSON format:
{{
    "context_understanding": "Your analysis of the user's current situation and needs",
    "reasoning": "Your step-by-step thought process and strategic considerations", 
    "chosen_tool": "tool_name or null if conversation is more appropriate",
    "tool_args": {{"arg1": "value1", "arg2": "value2"}},
    "confidence": 0.8,
    "response_type": "tool_execution" or "conversation",
    "anticipated_follow_up": "What you expect might happen next",
    "context_flags": ["any_important_context_indicators"]
}}
"""

# Context-aware conversation prompt for non-tool interactions
ENHANCED_CONVERSATION_PROMPT = """
You are an expert essay writing coach having a natural conversation with a student.

CONVERSATION CONTEXT:
{conversation_context}

MEMORY CONTEXT:
{memory_context}

USER PROFILE:
{user_profile}

USER REQUEST: "{user_input}"

Provide a response that:
1. Acknowledges their specific situation and history
2. Offers concrete, actionable guidance
3. Builds confidence and motivation
4. Suggests natural next steps when appropriate
5. Maintains your role as a supportive expert

Consider:
- Their past struggles and successes
- Their writing style and voice patterns
- Their current emotional state
- The broader context of their essay journey

Response:
"""

# Tool-specific reasoning prompts for different categories
TOOL_SPECIFIC_PROMPTS = {
    "brainstorm": """
BRAINSTORMING CONTEXT: The user needs story ideas that authentically address their essay prompt.

Consider:
- Their past experiences and values from memory
- Prompt requirements and themes
- Authentic voice and growth potential
- Avoiding overused essay topics

Generate stories that feel genuinely theirs, not generic college essay tropes.
""",
    
    "outline": """
OUTLINING CONTEXT: The user has a story and needs structural guidance.

Consider:
- Optimal story arc for college essays (hook → context → conflict → growth → reflection)
- Word count constraints and pacing
- Emotional trajectory and impact
- Clear narrative progression

Create an outline that maximizes storytelling impact within constraints.
""",
    
    "draft": """
DRAFTING CONTEXT: The user needs to transform their outline into compelling prose.

Consider:
- Their authentic voice and writing style
- Show-don't-tell principles
- Specific details and scenes
- Emotional resonance and insight

Write in their voice, not a generic "college essay" voice.
""",
    
    "revise": """
REVISION CONTEXT: The user wants to improve an existing draft.

Consider:
- Specific weaknesses in the current draft
- Opportunities for deeper insight
- Voice consistency and authenticity
- Overall narrative flow and impact

Focus on strategic improvements, not just surface polishing.
""",
    
    "polish": """
POLISHING CONTEXT: The user needs final refinements for submission.

Consider:
- Grammar, style, and technical precision
- Word count optimization
- Final impact and memorability
- Readiness for submission

Preserve their voice while ensuring technical excellence.
"""
}

# Error recovery strategies with context awareness
ERROR_RECOVERY_STRATEGIES = {
    "tool_failure": """
A tool execution failed. You need to help the user continue their progress despite this setback.

FAILED TOOL: "{tool_name}"
ERROR: "{error_message}"
USER CONTEXT: {context}

Recovery options:
1. RETRY: Try the same tool with adjusted parameters
2. ALTERNATIVE: Suggest a different tool that could help
3. MANUAL: Guide them through a manual approach
4. CLARIFY: Ask for more information to improve success

Choose the recovery strategy most likely to maintain their momentum and confidence.
""",
    
    "unclear_intent": """
The user's request is ambiguous or unclear. Help them clarify what they need.

USER INPUT: "{user_input}"
CONTEXT: {context}

Guide them to be more specific about:
- What stage they're at in their essay process
- What specific help they need right now
- What they've already tried or considered

Ask one focused clarifying question that moves them forward.
""",
    
    "context_missing": """
Important context is missing that would help provide better assistance.

MISSING CONTEXT: {missing_context}
CURRENT CONTEXT: {available_context}

Gently gather the missing information while providing immediate value:
- Acknowledge what you can help with now
- Explain why additional context would be valuable
- Ask for the specific information needed
"""
}

# Performance-optimized prompt variations for A/B testing
PERFORMANCE_OPTIMIZED_PROMPTS = {
    "high_confidence_reasoning": """
[Optimized for high-confidence decisions]
You are an expert essay writing agent with proven success patterns.

Based on extensive experience with similar contexts, apply your expertise decisively:
{context}

USER REQUEST: "{user_input}"

Make a confident, strategic decision based on successful patterns.
""",
    
    "exploratory_reasoning": """
[Optimized for creative exploration]
You are an innovative essay writing agent focused on discovering unique possibilities.

Explore creative approaches and novel solutions:
{context}

USER REQUEST: "{user_input}"

Consider unconventional but effective approaches to help them stand out.
""",
    
    "support_focused": """
[Optimized for emotional support and confidence building]
You are a supportive essay writing mentor focused on building student confidence.

Prioritize encouragement and achievable next steps:
{context}

USER REQUEST: "{user_input}"

Help them feel capable and motivated while making concrete progress.
"""
}


# ============================================================================
# DYNAMIC CONTEXT FORMATTING FUNCTIONS
# ============================================================================

def format_context_for_reasoning(context: Dict[str, Any]) -> str:
    """Format context in a clear, structured way for LLM reasoning.
    
    Args:
        context: Context dictionary from agent memory
        
    Returns:
        Formatted context string optimized for LLM comprehension
    """
    if not context:
        return "No context available."
    
    formatted_parts = []
    
    # Conversation history
    if context.get('conversation_history'):
        history = context['conversation_history'][-3:]  # Last 3 exchanges
        formatted_parts.append("RECENT CONVERSATION:")
        for i, exchange in enumerate(history, 1):
            formatted_parts.append(f"  {i}. User: {exchange.get('user', 'N/A')}")
            formatted_parts.append(f"     Agent: {exchange.get('agent', 'N/A')}")
    
    # Current essay state
    if context.get('essay_state'):
        state = context['essay_state']
        formatted_parts.append(f"\nESSAY STATE:")
        formatted_parts.append(f"  Phase: {state.get('phase', 'Unknown')}")
        formatted_parts.append(f"  Progress: {state.get('progress', 'Unknown')}")
        if state.get('current_draft'):
            word_count = len(state['current_draft'].split())
            formatted_parts.append(f"  Draft: {word_count} words")
    
    # User profile insights
    if context.get('user_profile'):
        profile = context['user_profile']
        formatted_parts.append(f"\nUSER PROFILE:")
        formatted_parts.append(f"  Writing style: {profile.get('writing_style', 'Unknown')}")
        formatted_parts.append(f"  Experience level: {profile.get('experience_level', 'Unknown')}")
        if profile.get('values'):
            formatted_parts.append(f"  Core values: {', '.join(profile['values'][:3])}")
    
    # Memory insights
    if context.get('relevant_memories'):
        memories = context['relevant_memories'][:2]  # Top 2 most relevant
        formatted_parts.append(f"\nRELEVANT MEMORIES:")
        for memory in memories:
            formatted_parts.append(f"  - {memory.get('summary', 'Memory available')}")
    
    return '\n'.join(formatted_parts) if formatted_parts else "Context available but formatting failed."


def format_tool_descriptions(tool_descriptions: Dict[str, Any]) -> str:
    """Format tool descriptions for optimal LLM selection.
    
    Args:
        tool_descriptions: Tool descriptions dictionary from registry
        
    Returns:
        Formatted tool descriptions string for reasoning
    """
    if not tool_descriptions:
        return "No tools available."
    
    formatted_tools = []
    
    # Group tools by category for better organization
    categories = {}
    for tool_name, desc in tool_descriptions.items():
        category = getattr(desc, 'category', 'other')
        if category not in categories:
            categories[category] = []
        categories[category].append((tool_name, desc))
    
    # Format each category
    for category, tools in categories.items():
        formatted_tools.append(f"\n{category.upper().replace('_', ' ')} TOOLS:")
        
        for tool_name, desc in tools:
            # Core info
            formatted_tools.append(f"  • {tool_name}: {getattr(desc, 'description', 'No description')}")
            
            # When to use
            when_to_use = getattr(desc, 'when_to_use', None)
            if when_to_use:
                formatted_tools.append(f"    → Use when: {when_to_use}")
            
            # Requirements
            requirements = getattr(desc, 'input_requirements', [])
            if requirements:
                formatted_tools.append(f"    → Needs: {', '.join(requirements)}")
            
            # Confidence threshold
            confidence = getattr(desc, 'confidence_threshold', 0.7)
            formatted_tools.append(f"    → Confidence needed: {confidence}")
    
    return '\n'.join(formatted_tools)


def format_tool_result(tool_name: str, result: Any, context: Optional[Dict] = None) -> str:
    """Format tool results for response generation.
    
    Args:
        tool_name: Name of the tool that was executed
        result: Raw result from tool execution
        context: Optional context for formatting decisions
        
    Returns:
        Formatted result string optimized for user presentation
    """
    if result is None:
        return f"Tool '{tool_name}' completed but returned no result."
    
    # Handle different result types based on tool
    if tool_name == "brainstorm":
        if isinstance(result, dict) and 'stories' in result:
            stories = result['stories']
            formatted = f"Generated {len(stories)} story ideas:\n"
            for i, story in enumerate(stories, 1):
                formatted += f"  {i}. {story.get('title', 'Untitled')}\n"
                formatted += f"     {story.get('description', 'No description')[:100]}...\n"
                formatted += f"     Prompt fit: {story.get('prompt_fit', 'Unknown')}\n"
            return formatted
    
    elif tool_name == "outline":
        if isinstance(result, dict) and 'outline' in result:
            outline = result['outline']
            formatted = "Created essay outline:\n"
            sections = ['hook', 'context', 'conflict', 'growth', 'reflection']
            for section in sections:
                if section in outline:
                    formatted += f"  {section.title()}: {outline[section][:80]}...\n"
            if 'estimated_word_count' in result:
                formatted += f"  Estimated length: {result['estimated_word_count']} words"
            return formatted
    
    elif tool_name in ["draft", "revise", "polish"]:
        if isinstance(result, dict) and 'content' in result:
            content = result['content']
            word_count = len(content.split())
            formatted = f"Generated {tool_name} ({word_count} words):\n"
            formatted += f"  Preview: {content[:150]}...\n"
            if 'improvements' in result:
                formatted += f"  Key improvements: {', '.join(result['improvements'][:3])}"
            return formatted
    
    # Generic formatting for other tools
    if isinstance(result, dict):
        if 'summary' in result:
            return f"Tool '{tool_name}' result: {result['summary']}"
        elif 'message' in result:
            return f"Tool '{tool_name}' says: {result['message']}"
        else:
            # Format key-value pairs
            formatted = f"Tool '{tool_name}' results:\n"
            for key, value in list(result.items())[:3]:  # Limit to first 3 items
                formatted += f"  {key}: {str(value)[:50]}...\n"
            return formatted
    
    elif isinstance(result, (list, tuple)):
        formatted = f"Tool '{tool_name}' returned {len(result)} items:\n"
        for i, item in enumerate(result[:3], 1):  # Show first 3 items
            formatted += f"  {i}. {str(item)[:50]}...\n"
        return formatted
    
    else:
        # Simple string or other type
        result_str = str(result)
        if len(result_str) > 200:
            return f"Tool '{tool_name}' result: {result_str[:200]}..."
        return f"Tool '{tool_name}' result: {result_str}"


def select_reasoning_template(task_type: str, context: Dict[str, Any]) -> str:
    """Select optimal reasoning template based on task type and context.
    
    Args:
        task_type: Type of task (e.g., 'tool_selection', 'conversation', 'error_recovery')
        context: Context dictionary for decision making
        
    Returns:
        Selected prompt template
    """
    # Analyze context for prompt optimization
    user_experience = context.get('user_profile', {}).get('experience_level', 'intermediate')
    conversation_length = len(context.get('conversation_history', []))
    has_errors = context.get('recent_errors', False)
    
    # CRITICAL FIX: During reasoning phase, ALWAYS use JSON-expecting prompts
    # The ENHANCED_CONVERSATION_PROMPT should only be used for final response generation,
    # never for reasoning about what action to take
    
    # Select based on context patterns
    if task_type == 'tool_selection':
        if has_errors or user_experience == 'beginner':
            return PERFORMANCE_OPTIMIZED_PROMPTS['support_focused']
        elif conversation_length > 10:  # Long conversation, be decisive
            return PERFORMANCE_OPTIMIZED_PROMPTS['high_confidence_reasoning'] 
        else:
            return ADVANCED_REASONING_PROMPT
    
    elif task_type == 'conversation':
        # CRITICAL FIX: Even for "conversation" task type during reasoning,
        # we still need JSON format to decide if we should use tools or respond conversationally
        return ADVANCED_REASONING_PROMPT
    
    elif task_type == 'error_recovery':
        return ERROR_RECOVERY_STRATEGIES.get('tool_failure', ADVANCED_REASONING_PROMPT)
    
    else:
        return ADVANCED_REASONING_PROMPT


def inject_memory_context(template: str, memory_data: Dict[str, Any]) -> str:
    """Inject memory context into prompt templates.
    
    Args:
        template: Prompt template with memory placeholders
        memory_data: Memory data from AgentMemory system
        
    Returns:
        Template with memory context injected
    """
    # Extract memory components
    reasoning_chains = memory_data.get('reasoning_chains', [])
    tool_executions = memory_data.get('tool_executions', [])
    usage_patterns = memory_data.get('usage_patterns', [])
    
    # Format memory context
    memory_context = []
    
    # Recent reasoning patterns
    if reasoning_chains:
        recent_reasoning = reasoning_chains[-2:]  # Last 2 reasoning chains
        memory_context.append("RECENT REASONING PATTERNS:")
        for i, chain in enumerate(recent_reasoning, 1):
            memory_context.append(f"  {i}. {chain.get('summary', 'Reasoning available')}")
    
    # Tool usage patterns
    if usage_patterns:
        memory_context.append("\nUSAGE PATTERNS:")
        for pattern in usage_patterns[:3]:  # Top 3 patterns
            memory_context.append(f"  - {pattern.get('description', 'Pattern detected')}")
    
    # Performance insights
    if tool_executions:
        successful_tools = [t for t in tool_executions if t.get('success', False)]
        success_rate = len(successful_tools) / len(tool_executions) if tool_executions else 0
        memory_context.append(f"\nPERFORMANCE: {success_rate:.1%} success rate, {len(tool_executions)} total executions")
    
    # Inject into template
    memory_text = '\n'.join(memory_context) if memory_context else "No memory context available."
    return template.replace('{memory_context}', memory_text)


def get_performance_context(performance_data: Dict[str, Any]) -> str:
    """Format performance data for prompt context.
    
    Args:
        performance_data: Performance metrics and patterns
        
    Returns:
        Formatted performance context string
    """
    if not performance_data:
        return "No performance data available."
    
    context_parts = []
    
    # Success patterns
    if 'successful_patterns' in performance_data:
        patterns = performance_data['successful_patterns'][:3]
        context_parts.append("SUCCESSFUL PATTERNS:")
        for pattern in patterns:
            context_parts.append(f"  - {pattern}")
    
    # Recent performance
    if 'recent_metrics' in performance_data:
        metrics = performance_data['recent_metrics']
        context_parts.append(f"\nRECENT PERFORMANCE:")
        context_parts.append(f"  Success rate: {metrics.get('success_rate', 0):.1%}")
        context_parts.append(f"  Avg response time: {metrics.get('avg_response_time', 0):.1f}s")
    
    # Tool preferences
    if 'preferred_tools' in performance_data:
        tools = performance_data['preferred_tools'][:3]
        context_parts.append(f"\nPREFERRED TOOLS: {', '.join(tools)}")
    
    return '\n'.join(context_parts)


# ============================================================================
# PROMPT TEMPLATE CONSTANTS
# ============================================================================

# Main reasoning prompt for tool selection and action planning (original, maintained for compatibility)
REASONING_PROMPT = ADVANCED_REASONING_PROMPT

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

# Prompt for error recovery when tools fail (enhanced)
ERROR_RECOVERY_PROMPT = """
You are an essay writing agent. A tool execution failed, but you can help the user continue their progress.

USER REQUEST: "{user_input}"
FAILED TOOL: "{tool_name}"
ERROR: "{error_message}"
CONTEXT: {context}
AVAILABLE TOOLS: {tool_descriptions}

Recovery strategy:
1. Acknowledge the setback without dwelling on it
2. Quickly pivot to a solution that maintains momentum  
3. Use context to suggest the best alternative approach
4. Keep the user focused on their progress, not the failure

Respond with:
{{
    "recovery_action": "retry_tool" or "try_different_tool" or "ask_clarification" or "manual_guidance",
    "alternative_tool": "tool_name or null",
    "alternative_args": {{"adjusted": "parameters"}},
    "clarification_question": "question text or null",
    "explanation": "Brief, encouraging explanation for the user",
    "confidence": 0.8
}}
"""

# Prompt for conversational responses (enhanced) 
CONVERSATION_PROMPT = ENHANCED_CONVERSATION_PROMPT 