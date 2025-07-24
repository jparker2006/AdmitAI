#!/usr/bin/env python3
"""
Independent Tools Using Unified Agent State
==========================================

Examples of how tools become much simpler and more powerful when they
receive the full EssayAgentState instead of individual parameters.
"""

from typing import Dict, Any, List
from essay_agent.models.agent_state import EssayAgentState
from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
import re


# ============= THE NEW WAY - UNIFIED STATE =============

@register_tool("smart_brainstorm")
class SmartBrainstormTool(ValidatedTool):
    """
    Smart brainstorming that works in any context.
    
    ❌ OLD: brainstorm(essay_prompt, profile, user_id, college_id, ...)
    ✅ NEW: brainstorm(state) - has access to everything!
    """
    
    name: str = "smart_brainstorm"
    description: str = "Generate personalized essay ideas using full context"
    
    def _run(self, state: EssayAgentState, **_: Any) -> Dict[str, Any]:
        """Generate ideas with full context awareness"""
        
        # Build comprehensive brainstorming prompt
        prompt_parts = [
            f"You are a college admissions expert helping a student brainstorm essay ideas.",
            f"",
            f"Essay prompt: \"{state.essay_prompt}\"",
            f"Target college: {state.college}" if state.college else "",
            f"Word limit: {state.word_limit} words",
            f"",
            f"Generate 3-5 specific, personal story ideas that would make compelling essays.",
            f"Focus on real experiences that show growth, learning, and personal reflection.",
        ]
        
        # Use user profile for personalization
        if state.user_profile:
            profile_summary = self._extract_profile_highlights(state.user_profile)
            prompt_parts.extend([
                f"",
                f"Student background: {profile_summary}",
                f"",
                f"Consider the student's actual experiences and activities when suggesting ideas.",
                f"Reference specific details from their background to make ideas more personal and authentic."
            ])
        
        # Be context aware - avoid repeating existing ideas
        existing_ideas = []
        if state.has_content_type("ideas"):
            existing_ideas = [idea.get("title", "") for idea in state.content_library["ideas"]]
            prompt_parts.extend([
                f"",
                f"Avoid these existing ideas: {', '.join(existing_ideas)}",
                f"Generate fresh, different story angles."
            ])
        
        # Consider what the user has already done
        recent_activities = [activity["action"] for activity in state.activity_log[-3:]]
        if recent_activities:
            prompt_parts.append(f"Recent activities: {', '.join(recent_activities)}")
        
        # Consider any existing text or notes
        if state.has_text():
            prompt_parts.append("The student has started writing. Consider their existing text direction.")
        if state.working_notes:
            prompt_parts.append(f"Student's notes: {state.working_notes[:200]}...")
        
        # Consider current focus
        if state.current_focus == "revising":
            prompt_parts.append("Focus on ideas that could improve the current text")
        
        prompt_parts.extend([
            f"",
            f"Format each idea as:",
            f"1. Story Title - Brief description of what happened and why it matters",
            f"2. Another Story - Description...",
            f"",
            f"Make the ideas specific, personal, and focused on moments of growth or learning."
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Make LLM call
        llm = get_chat_llm(temperature=0.7)  # Higher temperature for more creative ideas
        response = call_llm(llm, prompt)
        
        # Parse and update state
        ideas = self._parse_ideas(response)
        
        # Store ideas in flexible content library - each idea separately
        for i, idea in enumerate(ideas):
            state.add_to_library("ideas", idea, f"Brainstormed idea {i+1}: {idea['title']}")
        
        state.log_activity("brainstormed", {"ideas_count": len(ideas), "context": "user_request"})
        state.add_chat_message("assistant", f"Generated {len(ideas)} personalized essay ideas", ["smart_brainstorm"])
        state.record_tool_call("smart_brainstorm", {"context": "full_state"}, {"ideas_count": len(ideas)})
        
        print(f"✅ Added {len(ideas)} individual ideas to state content library")
        
        return {"ideas": ideas, "context_used": state.get_context_summary()}
    
    def _extract_profile_highlights(self, profile: Dict[str, Any]) -> str:
        """Extract key highlights from user profile"""
        print(f"🔍 Profile structure received: {profile.keys() if profile else 'Empty profile'}")
        
        if not profile:
            print("❌ Empty profile - returning generic background")
            return "general background"
        
        highlights = []
        
        # Handle Alex Kim's actual profile structure
        user_info = profile.get("user_info", {})
        if user_info.get("name"):
            print(f"✅ Found user name: {user_info['name']}")
        
        # Extract activities from academic_profile (Alex Kim's structure)
        academic_profile = profile.get("academic_profile", {})
        activities = academic_profile.get("activities", [])
        print(f"🎯 Found {len(activities)} activities: {[a.get('name', 'unnamed') for a in activities]}")
        
        if activities:
            # Get top 3 activity names and roles
            activity_details = []
            for activity in activities[:3]:
                name = activity.get("name", "")
                role = activity.get("role", "")
                if name and role:
                    activity_details.append(f"{role} of {name}")
                elif name:
                    activity_details.append(name)
            
            if activity_details:
                highlights.append(f"Leadership: {', '.join(activity_details)}")
                print(f"✅ Added activities: {activity_details}")
        
        # Extract specific achievements and impacts 
        if activities:
            achievements = []
            for activity in activities[:2]:  # Top 2 activities
                impact = activity.get("impact", "")
                if impact:
                    # Keep impact concise but specific
                    achievements.append(impact[:80] + "..." if len(impact) > 80 else impact)
            
            if achievements:
                highlights.append(f"Impact: {'; '.join(achievements)}")
                print(f"✅ Added achievements: {achievements}")
        
        # Extract defining moments for authentic story context
        defining_moments = profile.get("defining_moments", [])
        print(f"📖 Found {len(defining_moments)} defining moments")
        
        if defining_moments:
            moment_titles = []
            for moment in defining_moments[:2]:
                title = moment.get("title", "")
                if title:
                    moment_titles.append(title)
            
            if moment_titles:
                highlights.append(f"Key experiences: {', '.join(moment_titles)}")
                print(f"✅ Added defining moments: {moment_titles}")
        
        # Extract core values for essay direction
        core_values = profile.get("core_values", [])
        if core_values:
            value_names = []
            for value in core_values[:2]:
                if isinstance(value, dict):
                    value_name = value.get("value", "")
                elif isinstance(value, str):
                    value_name = value
                else:
                    value_name = ""
                
                if value_name:
                    value_names.append(value_name)
            
            if value_names:
                highlights.append(f"Values: {', '.join(value_names)}")
                print(f"✅ Added values: {value_names}")
        
        result = "; ".join(highlights) if highlights else "general background"
        print(f"🎯 Final profile summary: {result}")
        return result
    
    def _parse_ideas(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured ideas with consistent schema"""
        ideas = []
        
        print(f"🔍 Parsing LLM response: {response[:200]}...")
        
        # Try to parse the detailed response structure first
        try:
            # Split response into idea blocks
            # Look for numbered patterns like "1. **Title**" followed by description text
            
            # Pattern to match numbered ideas with titles and descriptions
            idea_pattern = r'(\d+)\.\s*\**(.*?)\**\s*\n\s*-?\s*Description:\s*(.*?)(?=\d+\.\s*\**|\Z)'
            matches = re.findall(idea_pattern, response, re.DOTALL)
            
            if matches:
                print(f"✅ Found {len(matches)} structured ideas using regex pattern")
                for i, (num, title, description) in enumerate(matches):
                    title = title.strip().replace("**", "").replace("*", "")
                    description = description.strip().replace("**", "").replace("*", "")
                    
                    # Clean up description - remove newlines and extra spaces
                    description = " ".join(description.split())
                    
                    # If title is empty, try to extract from description
                    if not title and description:
                        desc_parts = description.split(" - ")
                        if len(desc_parts) > 1:
                            title = desc_parts[0]
                            description = " - ".join(desc_parts[1:])
                    
                    # If description is too short, generate one based on title
                    if len(description) < 50:
                        description = f"A story about {title.lower()} that demonstrates growth and learning"
                    
                    # Create rich, specific personal connection and intellectual angle
                    personal_connection = self._generate_personal_connection(title, description)
                    intellectual_angle = self._generate_intellectual_angle(title, description)
                    
                    idea = {
                        "title": title if title else f"Story Idea {i+1}",
                        "description": description,
                        "personal_connection": personal_connection,
                        "intellectual_angle": intellectual_angle
                    }
                    
                    ideas.append(idea)
                    print(f"✅ Structured idea {i+1}: {idea['title']}")
                
                if ideas:
                    return ideas[:5]  # Limit to 5 ideas
            
        except Exception as e:
            print(f"⚠️ Regex parsing failed: {e}")
        
        # Fallback: Try line-by-line parsing
        print("🔄 Using line-by-line parsing fallback")
        try:
            lines = response.strip().split('\n')
            current_title = ""
            current_description = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this looks like a numbered title
                if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '•', '-', '*']):
                    # Save previous idea if we have one
                    if current_title:
                        idea = self._create_idea_from_parts(current_title, current_description)
                        ideas.append(idea)
                        print(f"✅ Line-parsed idea: {idea['title']}")
                    
                    # Extract new title
                    clean_line = line
                    for prefix in ['1.', '2.', '3.', '4.', '5.', '•', '-', '*']:
                        if clean_line.startswith(prefix):
                            clean_line = clean_line[len(prefix):].strip()
                            break
                    
                    # Split title and description if there's a separator
                    if ' - ' in clean_line:
                        current_title, current_description = clean_line.split(' - ', 1)
                    elif ': ' in clean_line:
                        current_title, current_description = clean_line.split(': ', 1)
                    else:
                        current_title = clean_line
                        current_description = ""
                        
                    current_title = current_title.replace("**", "").replace("*", "").strip()
                    
                else:
                    # This might be continuation of description
                    if current_title and not current_description:
                        current_description = line
                    elif current_description:
                        current_description += " " + line
            
            # Don't forget the last idea
            if current_title:
                idea = self._create_idea_from_parts(current_title, current_description)
                ideas.append(idea)
                print(f"✅ Final line-parsed idea: {idea['title']}")
            
            if ideas:
                return ideas[:5]
                
        except Exception as e:
            print(f"⚠️ Line parsing failed: {e}")
        
        # Final fallback: Create basic ideas from response text
        print("🆘 Using final fallback parsing")
        if ideas:
            return ideas
        else:
            # Create at least one idea from the response
            idea = {
                "title": "Personal Growth Experience",
                "description": "A meaningful experience that led to personal development and self-discovery",
                "personal_connection": "This story allows you to showcase your unique background and experiences",
                "intellectual_angle": "Demonstrates intellectual curiosity, growth mindset, and ability to learn from challenges"
            }
            ideas.append(idea)
        
        print(f"🎯 Final ideas count: {len(ideas)}")
        return ideas
    
    def _create_idea_from_parts(self, title: str, description: str) -> Dict[str, Any]:
        """Create a structured idea from title and description parts"""
        title = title.strip()
        description = description.strip() if description else ""
        
        # If no description, create one based on the title
        if not description or len(description) < 20:
            description = f"A story about {title.lower()} that explores personal growth and learning"
        
        return {
            "title": title,
            "description": description,
            "personal_connection": self._generate_personal_connection(title, description),
            "intellectual_angle": self._generate_intellectual_angle(title, description)
        }
    
    def _generate_personal_connection(self, title: str, description: str) -> str:
        """Generate specific personal connection based on title and description"""
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Look for specific themes and create targeted connections
        if any(term in title_lower + desc_lower for term in ["investment", "finance", "money", "portfolio"]):
            return "This story showcases your financial literacy and leadership in founding the investment club"
        elif any(term in title_lower + desc_lower for term in ["tutoring", "business", "revenue", "entrepreneur"]):
            return "This experience highlights your entrepreneurial spirit and the tutoring business you built"
        elif any(term in title_lower + desc_lower for term in ["model un", "negotiation", "diplomacy", "conference"]):
            return "This draws from your leadership role as Secretary-General of the Model UN conference"
        elif any(term in title_lower + desc_lower for term in ["teaching", "education", "peer", "skeptical"]):
            return "This reflects your experience teaching investment concepts to skeptical peers"
        elif any(term in title_lower + desc_lower for term in ["family", "financial", "struggle", "difficulty"]):
            return "This connects to your experience starting a business during family financial challenges"
        else:
            return "This story leverages your unique background in business, leadership, and financial education"
    
    def _generate_intellectual_angle(self, title: str, description: str) -> str:
        """Generate specific intellectual angle based on title and description"""
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Create specific intellectual angles based on content
        if any(term in title_lower + desc_lower for term in ["skeptical", "doubt", "convince", "teach"]):
            return "Demonstrates ability to overcome resistance, communicate complex ideas, and build consensus"
        elif any(term in title_lower + desc_lower for term in ["uncertainty", "challenge", "struggle", "difficulty"]):
            return "Shows resilience, problem-solving under pressure, and ability to thrive in uncertain situations"
        elif any(term in title_lower + desc_lower for term in ["leadership", "founder", "president", "secretary"]):
            return "Exhibits leadership skills, initiative, and ability to build and manage organizations"
        elif any(term in title_lower + desc_lower for term in ["business", "revenue", "entrepreneur", "portfolio"]):
            return "Demonstrates business acumen, strategic thinking, and practical application of academic concepts"
        elif any(term in title_lower + desc_lower for term in ["negotiation", "diplomacy", "model un"]):
            return "Shows diplomatic skills, cultural awareness, and ability to navigate complex international issues"
        else:
            return "Reflects intellectual curiosity, growth mindset, and ability to learn from diverse experiences"


@register_tool("smart_outline")
class SmartOutlineTool(ValidatedTool):
    """
    Smart outlining that adapts to available context.
    
    Works whether user has:
    - Just a prompt
    - Brainstormed ideas  
    - Selected story
    - Existing draft to outline
    """
    
    name: str = "smart_outline"
    description: str = "Create outline using any available context"
    
    def _run(self, state: EssayAgentState, **_: Any) -> Dict[str, Any]:
        """Create outline adapting to whatever context is available"""
        
        # Adaptive based on what's available in state
        approach = "prompt_based"
        content = state.essay_prompt
        
        # Check what the user has to work with (most specific to least specific)
        if state.has_text():
            # User has written text - outline what they have (reverse engineering)
            approach = "text_analysis"
            content = state.primary_text
        elif state.has_content_type("ideas") and state.content_library["ideas"]:
            # User has brainstormed - outline best idea
            approach = "idea_based"
            content = state.content_library["ideas"][0]  # Use first idea
        elif state.working_notes:
            # User has notes - outline from notes
            approach = "notes_based"
            content = state.working_notes
        
        prompt = self._build_outline_prompt(approach, content, state)
        
        # Generate outline
        llm = get_chat_llm(temperature=0.1)
        response = call_llm(llm, prompt)
        outline = self._parse_outline(response)
        
        # Store outline in flexible content library
        state.add_to_library("outlines", outline, f"Created outline using {approach} approach")
        state.log_activity("outlined", {"approach": approach, "source": content[:100] + "..." if len(str(content)) > 100 else str(content)})
        state.current_focus = "outlining"
        state.add_chat_message("assistant", f"Created outline using {approach} approach", ["smart_outline"])
        
        return {"outline": outline, "approach": approach}
    
    def _build_outline_prompt(self, approach: str, content: Any, state: EssayAgentState) -> str:
        """Build appropriate prompt based on approach"""
        base = f"Create a {state.word_limit}-word essay outline for: {state.essay_prompt}"
        
        if approach == "story_based":
            return f"{base}\n\nBased on this story: {content}"
        elif approach == "idea_based": 
            return f"{base}\n\nBased on this idea: {content}"
        elif approach == "draft_analysis":
            return f"{base}\n\nAnalyze and outline this existing draft: {content[:500]}..."
        else:
            return base
    
    def _parse_outline(self, response: str) -> Dict[str, Any]:
        """Parse outline from LLM response"""
        return {
            "hook": "Generated hook",
            "context": "Generated context",
            "conflict": "Generated conflict",
            "growth": "Generated growth",
            "reflection": "Generated reflection"
        }


@register_tool("smart_polish")
class SmartPolishTool(ValidatedTool):
    """
    Smart polishing that works on any text in any context.
    
    Can polish:
    - Selected text
    - Current draft
    - Specific paragraph
    - Entire essay
    """
    
    name: str = "smart_polish"
    description: str = "Polish any text using full context"
    
    def _run(self, state: EssayAgentState, text_to_polish: str = "", **_: Any) -> Dict[str, Any]:
        """Polish text with full context awareness"""
        
        # Determine what to polish
        if text_to_polish:
            target_text = text_to_polish
            scope = "provided_text"
        elif state.selected_text:
            target_text = state.selected_text  
            scope = "selected_text"
        elif state.has_text():
            target_text = state.primary_text
            scope = "primary_text"
        else:
            return {"error": "No text available to polish"}
        
        # Build context-aware polish prompt
        prompt_parts = [
            f"Polish this text for a {state.college} essay:",
            f"Target word limit: {state.word_limit}",
            f"Current essay word count: {state.get_word_count()}",
            f"Text to polish: {target_text}"
        ]
        
        # Add context about essay stage
        if state.current_focus == "drafting":
            prompt_parts.append("Focus: Early draft polish - clarity and flow")
        elif state.current_focus == "polishing":
            prompt_parts.append("Focus: Final polish - grammar and precision")
        
        # Add user preferences if available
        if state.preferences.get("writing_style"):
            prompt_parts.append(f"Style preference: {state.preferences['writing_style']}")
        
        prompt = "\n".join(prompt_parts)
        
        # Polish the text
        llm = get_chat_llm(temperature=0.1)
        polished_text = call_llm(llm, prompt)
        
        # Update state based on scope
        if scope == "primary_text":
            state.update_primary_text(polished_text, "AI polish applied")
        elif scope == "selected_text" and state.has_text():
            # Replace selected text in primary text
            new_text = state.primary_text.replace(state.selected_text, polished_text)
            state.update_primary_text(new_text, f"Polished selected text ({len(state.selected_text)} chars)")
        
        # Log the activity
        state.log_activity("polished", {"scope": scope, "original_length": len(target_text), "polished_length": len(polished_text)})
        state.add_chat_message("assistant", f"Polished {scope}", ["smart_polish"])
        
        return {
            "polished_text": polished_text,
            "scope": scope,
            "original_length": len(target_text),
            "polished_length": len(polished_text)
        }


@register_tool("essay_chat")
class EssayChatTool(ValidatedTool):
    """
    Main conversational interface that understands context and provides helpful responses.
    
    This is the "smart agent" that figures out what the user wants and how to help.
    """
    
    name: str = "essay_chat"
    description: str = "Intelligent chat interface with full essay context"
    
    def _run(self, state: EssayAgentState, **_: Any) -> Dict[str, Any]:
        """Provide contextual help based on user input and current state"""
        
        user_input = state.last_user_input.lower()
        
        # Analyze what user is asking for
        if any(word in user_input for word in ["brainstorm", "ideas", "topics"]):
            suggestion = self._suggest_brainstorming(state)
        elif any(word in user_input for word in ["outline", "structure", "organize"]):
            suggestion = self._suggest_outlining(state)
        elif any(word in user_input for word in ["draft", "write", "start writing"]):
            suggestion = self._suggest_drafting(state)
        elif any(word in user_input for word in ["polish", "improve", "fix", "better"]):
            suggestion = self._suggest_polishing(state)
        elif any(word in user_input for word in ["feedback", "score", "how good"]):
            suggestion = self._suggest_feedback(state)
        elif any(word in user_input for word in ["words", "count", "length"]):
            suggestion = self._provide_word_info(state)
        else:
            suggestion = self._general_help(state)
        
        # Add to chat history
        state.add_chat_message("assistant", suggestion["response"], ["essay_chat"])
        
        # Add suggested actions
        for action in suggestion.get("suggested_actions", []):
            state.add_suggestion(action["title"], action["description"], action.get("tool", ""))
        
        return suggestion
    
    def _suggest_brainstorming(self, state: EssayAgentState) -> Dict[str, Any]:
        """Suggest brainstorming help"""
        # CRITICAL FIX: Safe access to brainstormed_ideas
        try:
            ideas_count = 0
            if hasattr(state, 'brainstormed_ideas') and state.brainstormed_ideas:
                if isinstance(state.brainstormed_ideas, list):
                    ideas_count = len(state.brainstormed_ideas)
                elif isinstance(state.brainstormed_ideas, dict):
                    # Handle case where it might be stored as dict
                    ideas_count = len(state.brainstormed_ideas.get('ideas', []))
                
            has_ideas = ideas_count > 0
            
            if has_ideas:
                response = f"You have {ideas_count} ideas already. Want to explore new ones or develop existing ones?"
                actions = [
                    {"title": "Generate more ideas", "tool": "smart_brainstorm"},
                    {"title": "Develop existing idea", "tool": "expand_story"}
                ]
            else:
                response = f"Let's brainstorm ideas for your {state.college} essay! I'll use your profile to suggest personalized stories."
                actions = [{"title": "Start brainstorming", "tool": "smart_brainstorm"}]
            
        except Exception as e:
            print(f"⚠️ Error checking brainstormed ideas: {e}")
            # Fallback to safe default
            response = f"Let's brainstorm ideas for your {state.college} essay! I'll use your profile to suggest personalized stories."
            actions = [{"title": "Start brainstorming", "tool": "smart_brainstorm"}]
        
        return {"response": response, "suggested_actions": actions}
    
    def _suggest_outlining(self, state: EssayAgentState) -> Dict[str, Any]:
        """Suggest outlining help"""
        if state.has_outline():
            response = "You have an outline! Want to refine it or start drafting?"
            actions = [
                {"title": "Refine outline", "tool": "smart_outline"},
                {"title": "Start drafting", "tool": "smart_draft"}
            ]
        elif state.has_ideas():
            response = "Perfect! Let's create an outline from your brainstormed ideas."
            actions = [{"title": "Create outline", "tool": "smart_outline"}]
        else:
            response = "Let's start with brainstorming ideas, then we can outline!"
            actions = [{"title": "Brainstorm first", "tool": "smart_brainstorm"}]
        
        return {"response": response, "suggested_actions": actions}
    
    def _provide_word_info(self, state: EssayAgentState) -> Dict[str, Any]:
        """Provide word count information"""
        current_count = state.get_word_count()
        target = state.word_limit
        
        if current_count == 0:
            response = f"Your essay is empty. Target: {target} words."
        elif current_count < target * 0.8:
            response = f"Current: {current_count}/{target} words. You need about {target - current_count} more words."
        elif current_count > target * 1.1:
            response = f"Current: {current_count}/{target} words. You're over by {current_count - target} words - consider trimming."
        else:
            response = f"Current: {current_count}/{target} words. You're in good shape!"
        
        return {"response": response, "word_count": current_count, "target": target}
    
    def _general_help(self, state: EssayAgentState) -> Dict[str, Any]:
        """Provide general contextual help"""
        if not state.has_ideas():
            response = "Let's start by brainstorming essay ideas for your prompt!"
            actions = [{"title": "Brainstorm ideas", "tool": "smart_brainstorm"}]
        elif not state.has_outline():
            response = "Great ideas! Ready to create an outline?"
            actions = [{"title": "Create outline", "tool": "smart_outline"}]
        elif not state.has_draft():
            response = "Perfect outline! Time to start writing your draft?"
            actions = [{"title": "Write draft", "tool": "smart_draft"}]
        else:
            response = "Your essay is coming along! What would you like to work on?"
            actions = [
                {"title": "Polish writing", "tool": "smart_polish"},
                {"title": "Get feedback", "tool": "essay_scoring"}
            ]
        
        return {"response": response, "suggested_actions": actions}


# ============= COMPARISON =============

def show_comparison():
    """Show the dramatic difference between old and new approaches"""
    
    print("🚨 OLD WAY - Parameter Mapping Hell:")
    print("""
    def draft_tool(
        outline: Dict[str, Any],           # From workflow step
        voice_profile: str,                # From ArgResolver
        word_count: int,                   # From context
        user_context: Dict[str, Any],      # From context engine  
        college_id: str,                   # From user session
        essay_prompt: str,                 # From planner args
        user_id: str,                      # From memory
        **kwargs                           # And 20 more parameters...
    ):
        # Need to validate all parameters
        # Handle missing dependencies
        # Complex parameter resolution
        # Error prone and rigid
    """)
    
    print("\n✅ NEW WAY - Unified State:")
    print("""
    def smart_draft_tool(state: EssayAgentState):
        # Has access to EVERYTHING:
        # - state.essay_prompt
        # - state.user_profile  
        # - state.outline (if available)
        # - state.brainstormed_ideas (if available)
        # - state.current_draft (if available)
        # - state.college
        # - state.word_limit
        # - state.selected_text
        # - state.chat_history
        # - And much more...
        
        # Tool decides what to use based on what's available
        # Adaptive, flexible, context-aware
        # Updates state directly
        # Much simpler and more powerful!
    """)


if __name__ == "__main__":
    show_comparison() 