#!/usr/bin/env python3
"""
Smart Outline Tool - Dynamic Approach
====================================

Creates outlines by dynamically extracting context from user profile and conversation.
No hardcoded activities - works for any user with any background.
"""

from typing import Dict, Any, List
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.models.natural_essay_state import EssayAgentState
from essay_agent.llm_client import get_chat_llm, call_llm
import json
import re


@register_tool("smart_outline_dynamic")
class SmartOutlineDynamicTool(ValidatedTool):
    """
    Create personalized essay outlines using dynamic context extraction.
    
    🎯 Dynamic Approach:
    - Extracts activities/experiences from user profile automatically
    - Uses conversation to understand what story user wants outlined
    - No hardcoded activities or responses
    """
    
    name: str = "smart_outline_dynamic"
    description: str = "Create a structured essay outline from user profile and conversation context"
    timeout: float = 20.0
    
    def _run(self, state: EssayAgentState, **_: Any) -> Dict[str, Any]:
        """Generate outline using dynamic context extraction"""
        
        try:
            # Dynamically extract story context from profile and conversation
            story_context = self._extract_dynamic_context(state)
            
            # Build outline prompt using extracted context
            outline_prompt = self._build_dynamic_prompt(state, story_context)
            
            # Generate outline using LLM
            llm = get_chat_llm(temperature=0.3)
            response = call_llm(llm, outline_prompt)
            
            # Return structured data (not formatted response)
            outline_data = self._parse_outline_response(response)
            
            # Add context for response formatter
            if outline_data and not outline_data.get("error"):
                outline_data["context"] = story_context
                outline_data["user_background"] = self._get_user_background_summary(state)
            
            return outline_data
            
        except Exception as e:
            return {
                "error": f"Failed to create outline: {str(e)}",
                "context": None
            }
    
    def _extract_dynamic_context(self, state: EssayAgentState) -> Dict[str, Any]:
        """
        Dynamically extract story context from user profile and conversation.
        
        Works for ANY user - no hardcoded activities.
        """
        context = {
            "story_focus": None,
            "relevant_activities": [],
            "mentioned_experiences": [],
            "extracted_themes": [],
            "conversation_hints": []
        }
        
        # Extract activities from user profile dynamically
        if state.user_profile:
            activities = state.user_profile.get("academic_profile", {}).get("activities", [])
            
            for activity in activities:
                activity_info = {
                    "name": activity.get("name", ""),
                    "role": activity.get("role", ""),
                    "impact": activity.get("impact", ""),
                    "themes": self._extract_themes_from_activity(activity)
                }
                if activity_info["name"]:  # Only add if has name
                    context["relevant_activities"].append(activity_info)
        
        # Extract experiences mentioned in conversation
        recent_messages = state.get_recent_conversation(10)
        conversation_text = " ".join([msg["content"] for msg in recent_messages])
        
        # Look for story mentions in conversation
        context["mentioned_experiences"] = self._extract_mentioned_experiences(
            conversation_text, 
            context["relevant_activities"]
        )
        
        # Extract themes from conversation
        context["extracted_themes"] = self._extract_conversation_themes(conversation_text)
        
        # Determine story focus from conversation + profile
        context["story_focus"] = self._determine_story_focus(
            conversation_text,
            context["relevant_activities"], 
            context["mentioned_experiences"]
        )
        
        return context
    
    def _extract_themes_from_activity(self, activity: Dict[str, Any]) -> List[str]:
        """Extract themes from an activity description"""
        
        name = activity.get("name", "").lower()
        role = activity.get("role", "").lower()
        impact = activity.get("impact", "").lower()
        
        activity_text = f"{name} {role} {impact}"
        
        # Theme keywords - dynamic, not hardcoded activities
        theme_patterns = {
            "leadership": ["president", "leader", "captain", "head", "director", "founder", "organize"],
            "entrepreneurship": ["business", "startup", "enterprise", "company", "founder", "revenue"],
            "service": ["volunteer", "community", "help", "serve", "charity", "nonprofit"],
            "education": ["tutor", "teach", "mentor", "educate", "academic", "student"],
            "research": ["research", "study", "investigate", "analyze", "experiment"],
            "creativity": ["art", "design", "creative", "music", "write", "innovative"],
            "athletics": ["team", "sport", "athletic", "compete", "tournament", "varsity"]
        }
        
        themes = []
        for theme, keywords in theme_patterns.items():
            if any(keyword in activity_text for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def _extract_mentioned_experiences(self, conversation: str, activities: List[Dict]) -> List[str]:
        """Extract specific experiences mentioned in conversation"""
        
        mentioned = []
        conversation_lower = conversation.lower()
        
        # Look for activities mentioned in conversation
        for activity in activities:
            activity_name = activity.get("name", "").lower()
            activity_role = activity.get("role", "").lower()
            
            # Check if activity is mentioned
            if activity_name and activity_name in conversation_lower:
                mentioned.append(f"{activity.get('role', '')} of {activity.get('name', '')}")
            elif activity_role and activity_role in conversation_lower:
                mentioned.append(f"{activity.get('role', '')} experience")
        
        # Look for general experience patterns
        experience_patterns = [
            r"(challenge|difficult|problem|struggle|obstacle) (?:with|in|during) ([^.]+)",
            r"(started|founded|created|began) ([^.]+)",
            r"(experience|time|story) (?:with|about|of) ([^.]+)"
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, conversation_lower)
            for match in matches:
                if len(match) == 2:
                    mentioned.append(f"{match[0]} {match[1]}")
        
        return mentioned
    
    def _extract_conversation_themes(self, conversation: str) -> List[str]:
        """Extract themes from conversation patterns"""
        
        conversation_lower = conversation.lower()
        themes = []
        
        # Theme detection patterns
        if any(word in conversation_lower for word in ["lead", "leadership", "organize", "manage"]):
            themes.append("leadership")
        if any(word in conversation_lower for word in ["challenge", "difficult", "overcome", "struggle"]):
            themes.append("overcoming_challenges")
        if any(word in conversation_lower for word in ["help", "impact", "community", "serve"]):
            themes.append("service")
        if any(word in conversation_lower for word in ["creative", "innovative", "new", "original"]):
            themes.append("innovation")
        
        return themes
    
    def _determine_story_focus(self, conversation: str, activities: List[Dict], mentioned: List[str]) -> str:
        """Determine what story to focus the outline on"""
        
        # If user specifically mentioned an experience
        if mentioned:
            return mentioned[0]  # Use first mentioned experience
        
        # If user has activities, pick most relevant to conversation themes
        if activities:
            conversation_lower = conversation.lower()
            
            # Score activities by relevance to conversation
            scored_activities = []
            for activity in activities:
                score = 0
                activity_text = f"{activity.get('name', '')} {activity.get('role', '')}".lower()
                
                # Check overlap with conversation
                conversation_words = set(conversation_lower.split())
                activity_words = set(activity_text.split())
                overlap = len(conversation_words.intersection(activity_words))
                score += overlap * 10
                
                # Boost leadership activities if leadership mentioned
                if "leadership" in conversation_lower and "leadership" in activity.get("themes", []):
                    score += 20
                
                scored_activities.append((score, activity))
            
            if scored_activities:
                # Return highest scoring activity
                best_activity = max(scored_activities, key=lambda x: x[0])[1]
                return f"{best_activity.get('role', '')} of {best_activity.get('name', '')}"
        
        # Default: general personal experience
        return "meaningful personal experience"
    
    def _get_user_background_summary(self, state: EssayAgentState) -> str:
        """Get a summary of user background for response formatting"""
        
        if not state.user_profile:
            return "student"
        
        user_info = state.user_profile.get("user_info", {})
        name = user_info.get("name", "Student")
        
        activities = state.user_profile.get("academic_profile", {}).get("activities", [])
        if activities:
            top_activity = activities[0]  # Assume first is most important
            role = top_activity.get("role", "")
            activity_name = top_activity.get("name", "")
            return f"{name}, {role} of {activity_name}"
        
        return name
    
    def _build_dynamic_prompt(self, state: EssayAgentState, story_context: Dict[str, Any]) -> str:
        """Build outline prompt using dynamically extracted context"""
        
        user_background = self._get_user_background_summary(state)
        story_focus = story_context.get("story_focus", "personal experience")
        themes = story_context.get("extracted_themes", [])
        activities = story_context.get("relevant_activities", [])
        
        # Build activity context
        activity_context = ""
        if activities:
            activity_summaries = []
            for activity in activities[:3]:  # Top 3
                role = activity.get("role", "")
                name = activity.get("name", "")
                if role and name:
                    activity_summaries.append(f"{role} of {name}")
            
            if activity_summaries:
                activity_context = f"Student activities: {', '.join(activity_summaries)}"
        
        # Build theme context
        theme_context = ""
        if themes:
            theme_context = f"Relevant themes: {', '.join(themes)}"
        
        prompt = f"""Create a compelling 5-part essay outline for a college application essay.

Essay Prompt: "{state.essay_prompt}"
Target College: {state.college or "college application"}
Word Limit: {state.word_limit} words

Story Focus: {story_focus}
Student: {user_background}
{activity_context}
{theme_context}

Create a structured outline with these 5 parts:

1. HOOK - Compelling opening that grabs attention and sets the scene
2. CONTEXT - Background information that establishes stakes and setting  
3. CONFLICT/CHALLENGE - The central problem, obstacle, or tension
4. GROWTH/ACTION - How you responded, what you learned, actions taken
5. REFLECTION - Lessons learned, future impact, deeper insights

Requirements:
- Make it specific and personal based on the student's actual background
- Include vivid details and concrete examples from their experiences
- Show genuine growth and self-reflection
- Connect clearly to the essay prompt
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
    "story_focus": "{story_focus}",
    "key_themes": {json.dumps(themes)}
}}"""

        return prompt
    
    def _parse_outline_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data (not formatted for conversation)"""
        
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                outline_data = json.loads(json_str)
                
                # Validate structure
                if "outline" in outline_data and isinstance(outline_data["outline"], dict):
                    required_parts = ["hook", "context", "conflict", "growth", "reflection"]
                    if all(part in outline_data["outline"] for part in required_parts):
                        return outline_data
            
            # Fallback structure
            return self._create_fallback_outline(response)
            
        except Exception as e:
            return {
                "error": f"Failed to parse outline: {str(e)}",
                "raw_response": response
            }
    
    def _create_fallback_outline(self, response: str) -> Dict[str, Any]:
        """Create basic outline structure if parsing fails"""
        
        return {
            "outline": {
                "hook": "Open with a compelling scene that draws the reader in",
                "context": "Provide background information and establish the stakes", 
                "conflict": "Describe the central challenge or obstacle faced",
                "growth": "Explain actions taken and lessons learned",
                "reflection": "Share deeper insights and future impact"
            },
            "story_focus": "personal experience",
            "estimated_word_count": 650,
            "key_themes": [],
            "note": "Generated basic outline structure"
        } 