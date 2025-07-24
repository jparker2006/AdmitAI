"""Simple, reliable tools with consistent signatures.

All tools follow the same pattern:
- Standard parameter names (user_id, text, college, prompt)
- Simple string inputs/outputs  
- No complex validation
- Always return {"result": str, "success": bool}
"""

from typing import Dict, Any, List
import json
from essay_agent.tools import register_tool
from essay_agent.tools.base import ValidatedTool
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.llm_client import get_chat_llm, call_llm


# =============================================================================
# STANDARD TOOL INTERFACE
# =============================================================================

class SimpleTool(ValidatedTool):
    """Base class for simple, reliable tools."""
    
    def _call_llm(self, prompt: str) -> str:
        """Simple LLM call with basic error handling."""
        try:
            llm = get_chat_llm(temperature=0.3)
            return call_llm(llm, prompt)
        except Exception as e:
            return f"I encountered an error: {str(e)}"
    
    def _load_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Load user profile or return empty dict."""
        try:
            return SimpleMemory.load_user_profile(user_id)
        except:
            return {}


# =============================================================================
# BRAINSTORMING TOOLS
# =============================================================================

@register_tool("simple_brainstorm")
class SimpleBrainstormTool(SimpleTool):
    """Generate essay ideas using simple, reliable interface.
    
    Args:
        user_id: User identifier
        prompt: Essay prompt text
        college: Target college name (optional)
    
    Returns:
        {"result": "3 essay ideas as text", "success": True}
    """
    
    name: str = "simple_brainstorm"
    description: str = "Generate 3 essay ideas for a user and prompt"
    timeout: float = 15.0
    
    def _run(self, *, user_id: str, prompt: str, college: str = "", **_: Any) -> Dict[str, Any]:
        # Load user profile
        profile = self._load_user_profile(user_id)
        
        # Extract key profile info
        profile_summary = "No profile available"
        if profile:
            user_info = profile.get("user_info", {})
            activities = profile.get("academic_profile", {}).get("activities", [])
            
            if user_info.get("name"):
                profile_summary = f"{user_info['name']}"
                if activities:
                    activity_names = [a.get("name", "") for a in activities[:3]]
                    profile_summary += f" (activities: {', '.join(filter(None, activity_names))})"
        
        # Simple, direct prompt
        brainstorm_prompt = f"""Generate 3 specific, personal essay ideas for this student:

STUDENT: {profile_summary}
COLLEGE: {college or "Any college"}
ESSAY PROMPT: {prompt}

For each idea, provide:
1. A clear title
2. 2-3 sentences describing the story
3. Why it fits the prompt

Format as numbered list. Be specific and personal."""

        response = self._call_llm(brainstorm_prompt)
        
        return {
            "result": response,
            "success": True,
            "ideas_count": 3,
            "user_profile_used": bool(profile)
        }


@register_tool("simple_outline")
class SimpleOutlineTool(SimpleTool):
    """Create essay outline using simple interface.
    
    Args:
        user_id: User identifier
        idea: Story idea or essay topic
        prompt: Essay prompt text
        college: Target college name (optional)
    
    Returns:
        {"result": "Essay outline as text", "success": True}
    """
    
    name: str = "simple_outline"
    description: str = "Create essay outline from idea and prompt"
    timeout: float = 15.0
    
    def _run(self, *, user_id: str, idea: str, prompt: str, college: str = "", **_: Any) -> Dict[str, Any]:
        # Simple outline prompt
        outline_prompt = f"""Create a detailed essay outline for this story:

STORY IDEA: {idea}
ESSAY PROMPT: {prompt}
COLLEGE: {college or "Any college"}

Create a 4-part outline:
1. HOOK (opening that grabs attention)
2. CONTEXT (background and setting) 
3. MAIN STORY (the key experience/challenge)
4. REFLECTION (lessons learned and growth)

For each section, provide:
- 2-3 sentences of content
- Approximate word count (total 650 words)"""

        response = self._call_llm(outline_prompt)
        
        return {
            "result": response, 
            "success": True,
            "sections": 4
        }


# =============================================================================
# WRITING TOOLS  
# =============================================================================

@register_tool("simple_draft")
class SimpleDraftTool(SimpleTool):
    """Write essay draft using simple interface.
    
    Args:
        user_id: User identifier
        outline: Essay outline text
        prompt: Essay prompt text
        word_count: Target word count (default 650)
    
    Returns:
        {"result": "Essay draft text", "success": True}
    """
    
    name: str = "simple_draft"
    description: str = "Write essay draft from outline"
    timeout: float = 30.0
    
    def _run(self, *, user_id: str, outline: str, prompt: str, word_count: int = 650, **_: Any) -> Dict[str, Any]:
        # Load profile for authentic voice
        profile = self._load_user_profile(user_id)
        
        # Simple drafting prompt
        draft_prompt = f"""Write a compelling college essay draft:

OUTLINE: {outline}
ESSAY PROMPT: {prompt}
TARGET LENGTH: {word_count} words

Requirements:
- Use first person narrative
- Include specific details and examples
- Show personal growth and reflection
- Write in an authentic, conversational tone
- Stay close to {word_count} words

Write the complete essay."""

        response = self._call_llm(draft_prompt)
        
        return {
            "result": response,
            "success": True,
            "target_words": word_count,
            "actual_words": len(response.split())
        }


@register_tool("simple_polish")
class SimplePolishTool(SimpleTool):
    """Polish essay text using simple interface.
    
    Args:
        user_id: User identifier  
        text: Essay text to polish
        focus: What to focus on (optional: "grammar", "flow", "voice")
    
    Returns:
        {"result": "Polished essay text", "success": True}
    """
    
    name: str = "simple_polish"
    description: str = "Polish and improve essay text"
    timeout: float = 20.0
    
    def _run(self, *, user_id: str, text: str, focus: str = "overall", **_: Any) -> Dict[str, Any]:
        # Simple polishing prompt
        polish_prompt = f"""Polish this essay text while preserving the student's authentic voice:

FOCUS: {focus}
TEXT TO POLISH:
{text}

Improvements to make:
- Fix grammar and spelling errors
- Improve sentence flow and transitions
- Enhance word choice where appropriate
- Maintain authentic, personal tone
- Keep the same meaning and content

Provide the improved version."""

        response = self._call_llm(polish_prompt)
        
        return {
            "result": response,
            "success": True,
            "focus_area": focus,
            "original_words": len(text.split()),
            "polished_words": len(response.split())
        }


# =============================================================================
# CHAT TOOL
# =============================================================================

@register_tool("simple_chat")
class SimpleChatTool(SimpleTool):
    """Handle general conversation using simple interface.
    
    Args:
        user_id: User identifier
        message: User's message/question
        context: Current essay context (optional)
    
    Returns:
        {"result": "Chat response text", "success": True}
    """
    
    name: str = "simple_chat"
    description: str = "Handle general conversation and questions"
    timeout: float = 10.0
    
    def _run(self, *, user_id: str, message: str, context: str = "", **_: Any) -> Dict[str, Any]:
        # Load user profile
        profile = self._load_user_profile(user_id)
        
        # Simple chat prompt
        chat_prompt = f"""You are a helpful college essay assistant. Respond to the student's message:

STUDENT MESSAGE: {message}
CONTEXT: {context or "General conversation"}

Guidelines:
- Be encouraging and supportive
- Provide specific, actionable advice
- Reference their background if relevant
- Keep responses conversational and helpful
- If they need tools (brainstorming, outlining, etc), suggest next steps

Response:"""

        response = self._call_llm(chat_prompt)
        
        return {
            "result": response,
            "success": True,
            "has_context": bool(context),
            "has_profile": bool(profile)
        }


# =============================================================================
# WORD COUNT TOOL
# =============================================================================

@register_tool("word_count")
class WordCountTool(SimpleTool):
    """Count words in text using simple interface.
    
    Args:
        text: Text to count
    
    Returns:
        {"result": "Text has X words", "success": True}
    """
    
    name: str = "word_count" 
    description: str = "Count words in essay text"
    timeout: float = 1.0
    
    def _run(self, *, text: str, **_: Any) -> Dict[str, Any]:
        word_count = len(text.split())
        
        return {
            "result": f"Text has {word_count} words",
            "success": True,
            "word_count": word_count,
            "character_count": len(text)
        } 