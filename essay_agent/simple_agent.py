"""Simple, reliable essay agent without complex reasoning chains.

Just maps user messages to appropriate tools with consistent parameters.
"""

from typing import Dict, Any
from essay_agent.tools.simple_orchestrator import SimpleOrchestrator
from essay_agent.memory.simple_memory import SimpleMemory


class SimpleEssayAgent:
    """Dead simple essay agent that always works."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.orchestrator = SimpleOrchestrator(user_id)
        self.memory = SimpleMemory(user_id)
        
    def handle_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """Handle user message and return response."""
        if context is None:
            context = {}
            
        # Add memory context
        context["user_profile"] = self.memory.load()
        
        # Route to appropriate tool
        result = self.orchestrator.handle_message(message, context)
        
        # Save conversation
        self.memory.add_message("user", message)
        response = result.get("result", "I'm here to help with your essay!")
        self.memory.add_message("assistant", response)
        
        return response
    
    def set_essay_context(self, college: str, essay_prompt: str):
        """Set essay context for the session."""
        self.essay_context = {
            "college": college,
            "essay_prompt": essay_prompt
        }
        
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the agent state."""
        return {
            "user_id": self.user_id,
            "has_profile": bool(self.memory.load()),
            "recent_messages": self.memory.get_conversation()[-5:] if self.memory.get_conversation() else [],
            "available_tools": list(self.orchestrator.tools.keys())
        } 