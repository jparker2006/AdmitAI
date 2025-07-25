#!/usr/bin/env python3
"""
Response Formatting Engine
=========================

Converts structured tool outputs into natural conversation responses.
This separates tool logic from response formatting.
"""

from typing import Dict, Any, List
from essay_agent.models.natural_essay_state import EssayAgentState


class ResponseFormatter:
    """
    Converts any tool output into natural conversation responses.
    
    🎯 Clean Separation:
    - Tools return structured data
    - Formatter handles natural language generation
    - No hardcoded formatting in tools
    """
    
    def format_tool_response(
        self, 
        tool_name: str, 
        tool_result: Dict[str, Any], 
        user_message: str, 
        state: EssayAgentState
    ) -> str:
        """Format any tool result into natural conversation response"""
        
        # Handle errors consistently
        if tool_result.get("error"):
            return self._format_error_response(tool_result["error"], tool_name)
        
        # Route to specific formatter based on tool
        if tool_name in ["smart_brainstorm", "smart_brainstorm_natural"]:
            return self._format_brainstorm_response(tool_result, state)
        elif tool_name in ["smart_outline", "smart_outline_dynamic"]:
            return self._format_outline_response(tool_result, state)
        elif tool_name == "smart_improve_paragraph":
            return self._format_improvement_response(tool_result, state)
        elif tool_name == "smart_essay_chat":
            return self._format_chat_response(tool_result, state)
        else:
            # Generic formatter for unknown tools
            return self._format_generic_response(tool_result, tool_name, state)
    
    def _format_error_response(self, error: str, tool_name: str) -> str:
        """Format error responses consistently"""
        
        friendly_names = {
            "smart_brainstorm": "brainstorming ideas",
            "smart_outline": "creating an outline",
            "smart_improve_paragraph": "improving that text",
            "smart_essay_chat": "processing your request"
        }
        
        activity = friendly_names.get(tool_name, "completing that task")
        return f"Sorry, I had trouble {activity}: {error}"
    
    def _format_brainstorm_response(self, result: Dict[str, Any], state: EssayAgentState) -> str:
        """Format brainstorming results naturally"""
        
        stories = result.get("stories", [])
        if not stories:
            return "I've generated some ideas for you, but let me know if you'd like different approaches!"
        
        # Get user name for personalization
        user_name = state.user_profile.get("user_info", {}).get("name", "")
        user_context = self._get_user_context_summary(state)
        
        response_parts = [
            f"Great! I've brainstormed some compelling story ideas{' for you' if not user_name else f' for you, {user_name}'}:"
        ]
        
        if user_context:
            response_parts.append(f"These draw from your {user_context}:")
        
        response_parts.append("")
        
        # Format each story idea
        for i, story in enumerate(stories[:3], 1):  # Show top 3
            title = story.get("title", f"Story Idea {i}")
            description = story.get("description", "")
            
            response_parts.append(f"**{i}. {title}**")
            if description:
                # Truncate long descriptions
                desc_preview = description[:120] + "..." if len(description) > 120 else description
                response_parts.append(f"   {desc_preview}")
            response_parts.append("")
        
        # Add next steps suggestion
        response_parts.extend([
            "Which of these resonates with you?",
            "You can say something like: 'Create an outline for the first story' or ask for different ideas."
        ])
        
        return "\n".join(response_parts)
    
    def _format_outline_response(self, result: Dict[str, Any], state: EssayAgentState) -> str:
        """Format outline results naturally"""
        
        outline = result.get("outline", {})
        story_focus = result.get("story_focus", "your story")
        user_background = result.get("user_background", "")
        
        if not outline:
            return "I created an outline structure for you!"
        
        response_parts = [
            f"Perfect! I've created a structured outline for {story_focus}:",
            "",
            "**Your Essay Structure:**",
            ""
        ]
        
        # Format each outline section
        sections = [
            ("Hook", outline.get("hook", "Compelling opening")),
            ("Context", outline.get("context", "Background and setting")),
            ("Conflict", outline.get("conflict", "Challenge or problem")),
            ("Growth", outline.get("growth", "Actions and learning")),
            ("Reflection", outline.get("reflection", "Insights and impact"))
        ]
        
        for i, (section_name, section_content) in enumerate(sections, 1):
            response_parts.append(f"**{i}. {section_name}**: {section_content}")
            response_parts.append("")
        
        # Add context about word count if available
        word_count = result.get("estimated_word_count")
        if word_count:
            response_parts.append(f"Target length: {word_count} words")
            response_parts.append("")
        
        response_parts.extend([
            "This outline is saved in your notes. Ready to start writing, or would you like me to adjust anything?"
        ])
        
        return "\n".join(response_parts)
    
    def _format_improvement_response(self, result: Dict[str, Any], state: EssayAgentState) -> str:
        """Format text improvement results"""
        
        improved_text = result.get("improved_text", "")
        improvement_type = result.get("improvement_type", "improvement")
        
        if not improved_text:
            return "I've improved that text for you!"
        
        response_parts = [
            f"Here's your improved text:",
            "",
            f'"{improved_text}"',
            "",
            "Does this capture what you were looking for? I can adjust the tone or style if needed."
        ]
        
        return "\n".join(response_parts)
    
    def _format_chat_response(self, result: Dict[str, Any], state: EssayAgentState) -> str:
        """Format general chat responses"""
        
        response_text = result.get("response", "")
        suggestions = result.get("suggestions", [])
        
        if not response_text:
            return "I'm here to help with your essay. What would you like to work on?"
        
        response_parts = [response_text]
        
        if suggestions:
            response_parts.append("")
            response_parts.append("Here are some things we could work on:")
            for suggestion in suggestions[:3]:  # Top 3 suggestions
                response_parts.append(f"• {suggestion}")
        
        return "\n".join(response_parts)
    
    def _format_generic_response(self, result: Dict[str, Any], tool_name: str, state: EssayAgentState) -> str:
        """Generic formatter for unknown tools"""
        
        # Try to find main content
        content = None
        for key in ["result", "output", "response", "text", "content"]:
            if key in result:
                content = result[key]
                break
        
        if content:
            if isinstance(content, str):
                return content
            elif isinstance(content, dict):
                # Try to format structured data
                formatted_parts = []
                for key, value in content.items():
                    if isinstance(value, str) and len(value) < 200:
                        formatted_parts.append(f"**{key.title()}**: {value}")
                
                if formatted_parts:
                    return "\n".join(formatted_parts)
        
        return f"I completed the {tool_name.replace('_', ' ')} task for you!"
    
    def _get_user_context_summary(self, state: EssayAgentState) -> str:
        """Get a brief summary of user context for personalization"""
        
        if not state.user_profile:
            return ""
        
        activities = state.user_profile.get("academic_profile", {}).get("activities", [])
        if activities:
            # Get top 2 activities
            activity_summaries = []
            for activity in activities[:2]:
                name = activity.get("name", "")
                role = activity.get("role", "")
                if name and role:
                    activity_summaries.append(f"{role.lower()} role in {name}")
            
            if activity_summaries:
                return "experience with " + " and ".join(activity_summaries)
        
        return "background and experiences" 