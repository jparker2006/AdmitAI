"""Simple tool orchestrator that always works.

Maps user messages to simple tool calls without complex parameter resolution.
"""

from typing import Dict, Any, List, Optional
import re
from essay_agent.tools.simple_tools import (
    SimpleBrainstormTool, SimpleOutlineTool, SimpleDraftTool, 
    SimplePolishTool, SimpleChatTool, WordCountTool
)


class SimpleOrchestrator:
    """Dead simple tool orchestrator that always works."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Initialize tools
        self.tools = {
            "simple_brainstorm": SimpleBrainstormTool(),
            "simple_outline": SimpleOutlineTool(),
            "simple_draft": SimpleDraftTool(),
            "simple_polish": SimplePolishTool(), 
            "simple_chat": SimpleChatTool(),
            "word_count": WordCountTool()
        }
    
    def handle_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route message to appropriate tool with simple logic."""
        if context is None:
            context = {}
            
        message_lower = message.lower()
        
        # Extract common context
        college = context.get("college", "")
        essay_prompt = context.get("essay_prompt", context.get("prompt", ""))
        
        # Simple pattern matching to determine tool
        if any(word in message_lower for word in ["brainstorm", "ideas", "stories", "think of"]):
            return self._handle_brainstorm(message, essay_prompt, college)
            
        elif any(word in message_lower for word in ["outline", "structure", "organize"]):
            return self._handle_outline(message, essay_prompt, college, context)
            
        elif any(word in message_lower for word in ["write", "draft", "compose"]):
            return self._handle_draft(message, essay_prompt, context)
            
        elif any(word in message_lower for word in ["polish", "improve", "fix", "edit"]):
            return self._handle_polish(message, context)
            
        elif any(word in message_lower for word in ["words", "count", "length"]):
            return self._handle_word_count(message, context)
            
        else:
            return self._handle_chat(message, context)
    
    def _handle_brainstorm(self, message: str, essay_prompt: str, college: str) -> Dict[str, Any]:
        """Handle brainstorming requests."""
        tool = self.tools["simple_brainstorm"]
        
        # Use provided prompt or ask for clarification
        if not essay_prompt:
            return {
                "result": "I'd love to help you brainstorm! Could you share the essay prompt you're working on?",
                "success": True,
                "tool_used": "simple_chat",
                "needs_clarification": True
            }
        
        try:
            result = tool._run(
                user_id=self.user_id,
                prompt=essay_prompt,
                college=college
            )
            result["tool_used"] = "simple_brainstorm"
            return result
        except Exception as e:
            return {
                "result": f"I had trouble brainstorming ideas. Let me help in another way: {str(e)}",
                "success": False,
                "tool_used": "simple_brainstorm",
                "error": str(e)
            }
    
    def _handle_outline(self, message: str, essay_prompt: str, college: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle outline requests."""
        tool = self.tools["simple_outline"]
        
        # Look for story idea in message or context
        idea = context.get("selected_story", context.get("idea", ""))
        
        # Extract idea from message if not in context
        if not idea:
            # Simple extraction - look for quoted text or after "for"
            if '"' in message:
                parts = message.split('"')
                if len(parts) >= 3:
                    idea = parts[1]
            elif " for " in message.lower():
                parts = message.lower().split(" for ", 1)
                if len(parts) > 1:
                    idea = parts[1]
        
        if not idea or not essay_prompt:
            return {
                "result": "I can help you create an outline! I need the essay prompt and your story idea. Could you share both?",
                "success": True,
                "tool_used": "simple_chat",
                "needs_clarification": True
            }
        
        try:
            result = tool._run(
                user_id=self.user_id,
                idea=idea,
                prompt=essay_prompt,
                college=college
            )
            result["tool_used"] = "simple_outline"
            return result
        except Exception as e:
            return {
                "result": f"I had trouble creating an outline. Let me help in another way: {str(e)}",
                "success": False,
                "tool_used": "simple_outline", 
                "error": str(e)
            }
    
    def _handle_draft(self, message: str, essay_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle drafting requests."""
        tool = self.tools["simple_draft"]
        
        # Look for outline in context
        outline = context.get("outline", context.get("selected_outline", ""))
        
        # Extract word count from message
        word_count = 650  # default
        word_match = re.search(r'(\d+)\s*words?', message.lower())
        if word_match:
            word_count = int(word_match.group(1))
        
        if not outline or not essay_prompt:
            return {
                "result": "I can help you write a draft! I need your essay outline and prompt. Do you have an outline ready?",
                "success": True,
                "tool_used": "simple_chat",
                "needs_clarification": True
            }
        
        try:
            result = tool._run(
                user_id=self.user_id,
                outline=outline,
                prompt=essay_prompt,
                word_count=word_count
            )
            result["tool_used"] = "simple_draft"
            return result
        except Exception as e:
            return {
                "result": f"I had trouble writing a draft. Let me help in another way: {str(e)}",
                "success": False,
                "tool_used": "simple_draft",
                "error": str(e)
            }
    
    def _handle_polish(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle polishing requests."""
        tool = self.tools["simple_polish"]
        
        # Look for text in context or message
        text = context.get("current_draft", context.get("selected_text", ""))
        
        # Determine focus area
        focus = "overall"
        if "grammar" in message.lower():
            focus = "grammar"
        elif "flow" in message.lower():
            focus = "flow"
        elif "voice" in message.lower():
            focus = "voice"
        
        if not text:
            return {
                "result": "I can help you polish your essay! Could you share the text you'd like me to improve?",
                "success": True,
                "tool_used": "simple_chat",
                "needs_clarification": True
            }
        
        try:
            result = tool._run(
                user_id=self.user_id,
                text=text,
                focus=focus
            )
            result["tool_used"] = "simple_polish"
            return result
        except Exception as e:
            return {
                "result": f"I had trouble polishing the text. Let me help in another way: {str(e)}",
                "success": False,
                "tool_used": "simple_polish",
                "error": str(e)
            }
    
    def _handle_word_count(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle word counting requests."""
        tool = self.tools["word_count"]
        
        # Look for text in context
        text = context.get("current_draft", context.get("selected_text", ""))
        
        if not text:
            return {
                "result": "I can count words for you! Could you share the text you'd like me to analyze?",
                "success": True,
                "tool_used": "simple_chat",
                "needs_clarification": True
            }
        
        try:
            result = tool._run(text=text)
            result["tool_used"] = "word_count"
            return result
        except Exception as e:
            return {
                "result": f"I had trouble counting words: {str(e)}",
                "success": False,
                "tool_used": "word_count",
                "error": str(e)
            }
    
    def _handle_chat(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general conversation."""
        tool = self.tools["simple_chat"]
        
        # Build context string
        context_str = ""
        if context.get("college"):
            context_str += f"Working on {context['college']} essay. "
        if context.get("essay_prompt"):
            context_str += f"Prompt: {context['essay_prompt'][:100]}..."
        
        try:
            result = tool._run(
                user_id=self.user_id,
                message=message,
                context=context_str
            )
            result["tool_used"] = "simple_chat"
            return result
        except Exception as e:
            return {
                "result": f"I'm here to help with your essay! What would you like to work on?",
                "success": True,
                "tool_used": "simple_chat",
                "fallback": True
            } 