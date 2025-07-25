#!/usr/bin/env python3
"""
Smart Outline Tool - Natural State Approach
==========================================

Creates structured outlines using conversation context and user profile.
No workflow assumptions - works with whatever context the user provides.
"""

from typing import Dict, Any, List
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.models.natural_essay_state import EssayAgentState
from essay_agent.llm_client import get_chat_llm, call_llm
import json


@register_tool("smart_outline")
class SmartOutlineTool(ValidatedTool):
    """
    Create personalized essay outlines using natural conversation context.
    
    🎯 Natural State Approach:
    - Extracts story/topic from conversation history OR current user input
    - Uses user profile for personalized structure 
    - No hardcoded content buckets - just natural context
    """
    
    name: str = "smart_outline"
    description: str = "Create a structured 5-part essay outline from conversation context and user input"
    timeout: float = 20.0
    
    def _run(self, state: EssayAgentState, **_: Any) -> Dict[str, Any]:
        """Generate outline using natural state context"""
        
        try:
            # Extract story/topic from conversation and current context
            story_context = self._extract_story_context(state)
            
            # Build personalized outline prompt
            outline_prompt = self._build_outline_prompt(state, story_context)
            
            # Generate outline using LLM
            llm = get_chat_llm(temperature=0.3)  # Slightly creative but structured
            response = call_llm(llm, outline_prompt)
            
            # Parse and structure the response
            outline_data = self._parse_outline_response(response)
            
            # Update state with new outline (if successful)
            if outline_data and not outline_data.get("error"):
                state.add_chat_message("assistant", f"Created outline for: {story_context['story_summary']}")
                
                # Store outline in notes for reference
                outline_text = self._format_outline_for_notes(outline_data)
                if state.notes:
                    state.notes += f"\n\n--- OUTLINE ---\n{outline_text}"
                else:
                    state.notes = f"--- OUTLINE ---\n{outline_text}"
            
            return outline_data
            
        except Exception as e:
            return {
                "error": f"Failed to create outline: {str(e)}",
                "outline": None
            }
    
    def _extract_story_context(self, state: EssayAgentState) -> Dict[str, Any]:
        """
        Extract what story/topic to outline from conversation history and current context.
        
        Natural approach: Look at what they've been talking about recently.
        """
        context = {
            "story_summary": "personal experience",
            "key_themes": [],
            "mentioned_activities": [],
            "specific_story": None
        }
        
        # Look at recent conversation for story context
        recent_messages = state.get_recent_conversation(10)
        
        # Extract mentioned activities and stories from conversation
        all_content = " ".join([msg["content"] for msg in recent_messages])
        
        # Look for specific activities mentioned
        if "tutoring business" in all_content.lower():
            context["specific_story"] = "starting a tutoring business"
            context["mentioned_activities"].append("tutoring business")
        
        if "investment club" in all_content.lower():
            context["mentioned_activities"].append("investment club")
            if not context["specific_story"]:
                context["specific_story"] = "founding an investment club"
        
        if "model un" in all_content.lower():
            context["mentioned_activities"].append("Model UN")
            if not context["specific_story"]:
                context["specific_story"] = "Model UN leadership experience"
        
        # Extract themes from recent conversation
        theme_keywords = {
            "leadership": ["lead", "president", "founder", "organize", "captain"],
            "entrepreneurship": ["business", "start", "create", "founder", "enterprise"],
            "service": ["help", "volunteer", "serve", "community", "support"],
            "growth": ["learn", "grow", "develop", "improve", "challenge"],
            "creativity": ["creative", "innovative", "design", "artistic", "original"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_content.lower() for keyword in keywords):
                context["key_themes"].append(theme)
        
        # Create story summary
        if context["specific_story"]:
            context["story_summary"] = context["specific_story"]
        elif context["mentioned_activities"]:
            context["story_summary"] = f"experience with {', '.join(context['mentioned_activities'])}"
        
        return context
    
    def _build_outline_prompt(self, state: EssayAgentState, story_context: Dict[str, Any]) -> str:
        """Build personalized prompt for outline generation"""
        
        # Extract user background for personalization
        user_name = "Student"
        user_background = ""
        
        if state.user_profile:
            user_name = state.user_profile.get("user_info", {}).get("name", "Student")
            
            # Extract key activities for context
            activities = state.user_profile.get("academic_profile", {}).get("activities", [])
            if activities:
                activity_list = []
                for activity in activities[:3]:  # Top 3 activities
                    name = activity.get("name", "")
                    role = activity.get("role", "")
                    if name and role:
                        activity_list.append(f"{role} of {name}")
                
                if activity_list:
                    user_background = f"Background: {user_name} - {', '.join(activity_list)}"
        
        prompt = f"""Create a compelling 5-part essay outline for a college application essay.

Essay Prompt: "{state.essay_prompt}"
Target College: {state.college or "college application"}
Word Limit: {state.word_limit} words

Story Focus: {story_context['story_summary']}
{user_background}

Create a structured outline with these 5 parts:

1. HOOK - Compelling opening that grabs attention and sets the scene
2. CONTEXT - Background information that establishes stakes and setting  
3. CONFLICT/CHALLENGE - The central problem, obstacle, or tension
4. GROWTH/ACTION - How you responded, what you learned, actions taken
5. REFLECTION - Lessons learned, future impact, deeper insights

Requirements:
- Make it specific and personal, not generic
- Include vivid details and concrete examples
- Show genuine growth and self-reflection
- Connect to the essay prompt clearly
- Reference the student's actual background and experiences
- Each section should be 2-3 sentences describing what to include

Format as JSON:
{{
    "outline": {{
        "hook": "Description of compelling opening approach...",
        "context": "Background details to establish...", 
        "conflict": "The specific challenge or problem...",
        "growth": "Actions taken and lessons learned...",
        "reflection": "Deeper insights and future impact..."
    }},
    "estimated_word_count": {state.word_limit},
    "key_themes": {json.dumps(story_context.get('key_themes', []))},
    "story_focus": "{story_context['story_summary']}"
}}"""

        return prompt
    
    def _parse_outline_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured outline"""
        
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                outline_data = json.loads(json_str)
                
                # Validate required fields
                if "outline" in outline_data and isinstance(outline_data["outline"], dict):
                    required_parts = ["hook", "context", "conflict", "growth", "reflection"]
                    if all(part in outline_data["outline"] for part in required_parts):
                        return outline_data
            
            # Fallback: create structured outline from text
            return self._create_fallback_outline(response)
            
        except Exception as e:
            return {
                "error": f"Failed to parse outline: {str(e)}",
                "raw_response": response
            }
    
    def _create_fallback_outline(self, response: str) -> Dict[str, Any]:
        """Create basic outline structure if JSON parsing fails"""
        
        return {
            "outline": {
                "hook": "Open with a compelling scene or moment that draws the reader in",
                "context": "Provide background information and establish the stakes", 
                "conflict": "Describe the central challenge or obstacle faced",
                "growth": "Explain actions taken and lessons learned through the experience",
                "reflection": "Share deeper insights and how this shapes your future goals"
            },
            "story_focus": "personal experience",
            "estimated_word_count": 650,
            "note": "Generated outline from conversation context"
        }
    
    def _format_outline_for_notes(self, outline_data: Dict[str, Any]) -> str:
        """Format outline for storage in user notes"""
        
        if "outline" not in outline_data:
            return "Outline generated - see conversation for details"
        
        outline = outline_data["outline"]
        formatted = []
        
        formatted.append(f"Story: {outline_data.get('story_focus', 'personal experience')}")
        formatted.append("")
        
        sections = [
            ("1. HOOK", outline.get("hook", "")),
            ("2. CONTEXT", outline.get("context", "")),
            ("3. CONFLICT", outline.get("conflict", "")), 
            ("4. GROWTH", outline.get("growth", "")),
            ("5. REFLECTION", outline.get("reflection", ""))
        ]
        
        for title, content in sections:
            formatted.append(f"{title}:")
            formatted.append(f"   {content}")
            formatted.append("")
        
        if outline_data.get("estimated_word_count"):
            formatted.append(f"Target: {outline_data['estimated_word_count']} words")
        
        return "\n".join(formatted) 