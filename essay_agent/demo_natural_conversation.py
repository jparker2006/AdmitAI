#!/usr/bin/env python3
"""
Demo: Natural Conversation Flow
==============================

Shows how the new natural state approach works with smart tools.
Perfect for testing the conversation flow you want to see.
"""

import asyncio
import json
from essay_agent.natural_state_manager import NaturalStateManager
from essay_agent.models.natural_essay_state import EssayAgentState
from essay_agent.tools.smart_outline_tool import SmartOutlineTool
from essay_agent.tools.smart_brainstorm_natural import SmartBrainstormNaturalTool


class SimpleNaturalAgent:
    """
    Simple agent that demonstrates natural conversation flow.
    
    Uses the new natural state approach - no parameter mapping complexity.
    """
    
    def __init__(self):
        self.state_manager = NaturalStateManager()
        self.tools = {
            "smart_brainstorm": SmartBrainstormNaturalTool(),
            "smart_outline": SmartOutlineTool()
        }
    
    def handle_message(self, state: EssayAgentState, user_message: str) -> str:
        """Handle user message and decide which tool to use"""
        
        # Add user message to conversation
        state.add_chat_message("user", user_message)
        
        # Simple tool selection based on user intent
        tool_name = self._select_tool(user_message)
        
        if tool_name:
            # Execute tool with full state
            try:
                result = self.tools[tool_name]._run(state)
                
                # Generate natural response
                response = self._format_response(tool_name, result, user_message, state)
                
                # Add response to conversation
                state.add_chat_message("assistant", response)
                
                # Save updated state
                self.state_manager.save_session(state)
                
                return response
                
            except Exception as e:
                error_response = f"Sorry, I encountered an error: {str(e)}"
                state.add_chat_message("assistant", error_response)
                return error_response
        else:
            # General conversation
            response = self._general_chat_response(user_message, state)
            state.add_chat_message("assistant", response)
            self.state_manager.save_session(state)
            return response
    
    def _select_tool(self, message: str) -> str:
        """Simple tool selection based on user message"""
        
        message_lower = message.lower()
        
        # Outlining patterns (check first to avoid conflict)
        if "outline" in message_lower:
            return "smart_outline"
        
        # Brainstorming patterns
        if any(word in message_lower for word in ["brainstorm", "ideas"]) and "outline" not in message_lower:
            return "smart_brainstorm"
        
        return None  # No specific tool
    
    def _format_response(self, tool_name: str, result: dict, user_message: str, state: EssayAgentState) -> str:
        """Format tool result into natural conversation response"""
        
        if tool_name == "smart_brainstorm":
            return self._format_brainstorm_response(result, state)
        elif tool_name == "smart_outline":
            return self._format_outline_response(result, state)
        else:
            return "I completed that task for you!"
    
    def _format_brainstorm_response(self, result: dict, state: EssayAgentState) -> str:
        """Format brainstorm results naturally"""
        
        if result.get("error"):
            return f"Sorry, I had trouble brainstorming ideas: {result['error']}"
        
        # Extract ideas from result
        ideas = result.get("stories", [])
        if not ideas:
            return "I generated some ideas for you, but let me know if you'd like different approaches!"
        
        response_parts = [
            f"Great! I've brainstormed some compelling story ideas based on your background:",
            ""
        ]
        
        for i, idea in enumerate(ideas[:3], 1):  # Show top 3
            title = idea.get("title", f"Idea {i}")
            description = idea.get("description", "")
            response_parts.append(f"**{i}. {title}**")
            if description:
                response_parts.append(f"   {description[:100]}...")
            response_parts.append("")
        
        response_parts.extend([
            "These ideas draw from your experiences - which one resonates with you?",
            "You can say something like: 'Create an outline for the tutoring business story'"
        ])
        
        return "\n".join(response_parts)
    
    def _format_outline_response(self, result: dict, state: EssayAgentState) -> str:
        """Format outline results naturally"""
        
        if result.get("error"):
            return f"Sorry, I had trouble creating an outline: {result['error']}"
        
        outline = result.get("outline", {})
        story_focus = result.get("story_focus", "your story")
        
        if not outline:
            return "I created an outline structure for you!"
        
        response_parts = [
            f"Perfect! I've created a structured outline for {story_focus}:",
            "",
            "**Your Essay Structure:**",
            "",
            f"1. **Hook**: {outline.get('hook', 'Compelling opening')}",
            "",
            f"2. **Context**: {outline.get('context', 'Background and setting')}",
            "",
            f"3. **Conflict**: {outline.get('conflict', 'Challenge or problem')}",
            "",
            f"4. **Growth**: {outline.get('growth', 'Actions and learning')}",
            "",
            f"5. **Reflection**: {outline.get('reflection', 'Insights and impact')}",
            "",
            "This outline is saved in your notes. Ready to start writing, or would you like me to adjust anything?"
        ]
        
        return "\n".join(response_parts)
    
    def _general_chat_response(self, message: str, state: EssayAgentState) -> str:
        """Handle general conversation"""
        
        user_name = state.user_profile.get("user_info", {}).get("name", "there")
        
        responses = [
            f"Hi {user_name}! I'm here to help with your essay. What would you like to work on?",
            f"I can help you brainstorm ideas, create outlines, or improve your writing. What sounds good?",
            f"Based on your background, I can help you develop compelling stories. What interests you most?",
            f"Let me know how I can assist with your {state.college} essay!"
        ]
        
        # Simple response selection
        if "help" in message.lower():
            return responses[1]
        elif "hi" in message.lower() or "hello" in message.lower():
            return responses[0]
        else:
            return responses[2]


def demo_conversation_flow():
    """
    Demonstrate the natural conversation flow you want to test.
    
    Shows:
    1. "Brainstorm me ideas" → smart_brainstorm
    2. "Create an outline for tutoring business story" → smart_outline
    """
    
    print("🚀 Demo: Natural Conversation Flow")
    print("=" * 50)
    
    # Initialize
    agent = SimpleNaturalAgent()
    
    # Create new session for Alex Kim
    state = agent.state_manager.create_new_essay_session(
        user_id="alex_kim",
        essay_prompt="Tell us about a time when you faced a challenge and how you overcame it.",
        college="Stanford",
        word_limit=650
    )
    
    print(f"📝 Essay Session Created:")
    print(f"   User: {state.user_id}")
    print(f"   Prompt: {state.essay_prompt}")
    print(f"   College: {state.college}")
    print()
    
    # Demo conversation
    conversations = [
        "Hi! I need help with my Stanford essay.",
        "Brainstorm me ideas for leadership stories", 
        "Create an outline for the tutoring business story"
    ]
    
    for i, user_message in enumerate(conversations, 1):
        print(f"👤 User: {user_message}")
        
        response = agent.handle_message(state, user_message)
        
        print(f"🤖 Assistant: {response}")
        print("-" * 50)
        print()
    
    # Show final state
    print("📊 Final State:")
    print(f"   Conversation messages: {len(state.chat_history)}")
    print(f"   Notes length: {len(state.notes)} chars")
    print(f"   Session ID: {state.session_id}")
    
    # Show conversation extract
    print("\n💬 Conversation Summary:")
    for msg in state.chat_history[-4:]:  # Last 4 messages
        role_icon = "👤" if msg["role"] == "user" else "🤖"
        content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"   {role_icon} {content_preview}")


if __name__ == "__main__":
    demo_conversation_flow() 