#!/usr/bin/env python3
"""
Smart Brainstorm Tool - Natural State Approach  
==============================================

Generates personalized essay ideas using natural conversation context.
"""

from typing import Dict, Any, List
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.models.natural_essay_state import EssayAgentState
from essay_agent.llm_client import get_chat_llm, call_llm
import json


@register_tool("smart_brainstorm_natural")
class SmartBrainstormNaturalTool(ValidatedTool):
    """
    Generate personalized essay ideas using natural conversation context.
    
    🎯 Natural State Approach:
    - Uses conversation history for context
    - References user profile for personalization  
    - No hardcoded parameter mapping
    """
    
    name: str = "smart_brainstorm_natural" 
    description: str = "Generate personalized essay ideas using full conversation context"
    timeout: float = 20.0
    
    def _run(self, state: EssayAgentState, **_: Any) -> Dict[str, Any]:
        """Generate ideas with full context awareness"""
        
        try:
            # Build personalized brainstorming prompt
            brainstorm_prompt = self._build_brainstorm_prompt(state)
            
            # Generate ideas using LLM
            llm = get_chat_llm(temperature=0.4)  # Creative but focused
            response = call_llm(llm, brainstorm_prompt)
            
            # Parse and structure the response
            ideas_data = self._parse_brainstorm_response(response)
            
            # Update state with conversation
            if ideas_data and not ideas_data.get("error"):
                state.add_chat_message("assistant", f"Generated {len(ideas_data.get('stories', []))} personalized story ideas")
            
            return ideas_data
            
        except Exception as e:
            return {
                "error": f"Failed to generate ideas: {str(e)}",
                "stories": []
            }
    
    def _build_brainstorm_prompt(self, state: EssayAgentState) -> str:
        """Build personalized prompt for idea generation"""
        
        # Extract user background
        user_name = "Student"
        user_background = ""
        
        if state.user_profile:
            user_name = state.user_profile.get("user_info", {}).get("name", "Student")
            
            # Extract activities for personalization
            activities = state.user_profile.get("academic_profile", {}).get("activities", [])
            if activities:
                activity_summaries = []
                for activity in activities[:3]:  # Top 3 activities
                    name = activity.get("name", "")
                    role = activity.get("role", "")
                    impact = activity.get("impact", "")
                    
                    if name and role:
                        summary = f"{role} of {name}"
                        if impact:
                            summary += f" ({impact[:50]}...)"
                        activity_summaries.append(summary)
                
                if activity_summaries:
                    user_background = f"Background: {user_name} - {', '.join(activity_summaries)}"
        
        # Check conversation for additional context
        recent_conversation = state.get_recent_conversation(5)
        conversation_context = ""
        
        if recent_conversation:
            user_messages = [msg["content"] for msg in recent_conversation if msg["role"] == "user"]
            if user_messages:
                latest_request = user_messages[-1]
                if "leadership" in latest_request.lower():
                    conversation_context = "Focus on leadership experiences and situations where you guided others."
                elif "challenge" in latest_request.lower():
                    conversation_context = "Focus on overcoming obstacles and problem-solving experiences."
        
        prompt = f"""Generate 3-5 compelling personal story ideas for a college application essay.

Essay Prompt: "{state.essay_prompt}"
Target College: {state.college or "college application"}
Word Limit: {state.word_limit} words

{user_background}
{conversation_context}

Generate specific, personal story ideas that:
- Draw from the student's actual experiences and background
- Show genuine growth, learning, and self-reflection
- Connect clearly to the essay prompt
- Include vivid, specific details rather than generic concepts
- Demonstrate the student's unique perspective and voice

For each story idea, provide:
- A compelling title that captures the essence
- A brief description of the story and its significance
- Key themes and lessons that emerge
- Why this story fits the prompt well

Format as JSON:
{{
    "stories": [
        {{
            "title": "Compelling story title",
            "description": "Brief story description focusing on key moments and growth",
            "themes": ["theme1", "theme2", "theme3"],
            "prompt_fit": "Why this story perfectly addresses the essay prompt",
            "personal_connection": "How this relates to the student's background"
        }}
    ]
}}"""

        return prompt
    
    def _parse_brainstorm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured ideas"""
        
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                ideas_data = json.loads(json_str)
                
                # Validate structure
                if "stories" in ideas_data and isinstance(ideas_data["stories"], list):
                    return ideas_data
            
            # Fallback: create basic structure from text
            return self._create_fallback_ideas(response)
            
        except Exception as e:
            return {
                "error": f"Failed to parse ideas: {str(e)}",
                "raw_response": response
            }
    
    def _create_fallback_ideas(self, response: str) -> Dict[str, Any]:
        """Create basic ideas structure if JSON parsing fails"""
        
        # Simple fallback ideas
        fallback_stories = [
            {
                "title": "Leadership Through Challenge",
                "description": "A time when you had to step up and lead others through a difficult situation",
                "themes": ["leadership", "resilience", "problem-solving"],
                "prompt_fit": "Shows how you overcame challenges and grew as a leader",
                "personal_connection": "Relates to your background and experiences"
            },
            {
                "title": "Innovation Under Pressure", 
                "description": "When you had to think creatively to solve an unexpected problem",
                "themes": ["creativity", "adaptability", "innovation"],
                "prompt_fit": "Demonstrates problem-solving and thinking outside the box",
                "personal_connection": "Shows your unique approach to challenges"
            },
            {
                "title": "Making a Difference",
                "description": "A time when you positively impacted others or your community",
                "themes": ["service", "impact", "empathy"],
                "prompt_fit": "Shows your commitment to helping others and creating change",
                "personal_connection": "Reflects your values and character"
            }
        ]
        
        return {
            "stories": fallback_stories,
            "note": "Generated fallback ideas - consider personalizing based on your specific experiences"
        } 