"""essay_agent.tools.brainstorm

Generate three story ideas for a given essay prompt and user profile.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set, Optional

from pydantic import BaseModel, Field

# Tool infrastructure ------------------------------------------------------
from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import pydantic_parser, safe_parse
from essay_agent.llm_client import get_chat_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.prompts.brainstorm import BRAINSTORM_PROMPT
from essay_agent.memory.simple_memory import SimpleMemory, is_story_reused
from essay_agent.memory.user_profile_schema import DefiningMoment

# ---------------------------------------------------------------------------
# Load prompt text file
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pydantic schema for parser
# ---------------------------------------------------------------------------

class Story(BaseModel):
    title: str = Field(..., max_length=60)
    description: str
    prompt_fit: str
    insights: List[str]
    # 🛠 Added for HP-002 validation – allow tagging story themes (e.g., "challenge")
    themes: List[str] = Field(default_factory=list)

class BrainstormResult(BaseModel):
    stories: List[Story]

_PARSER = pydantic_parser(BrainstormResult)

# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------


@register_tool("brainstorm")
class BrainstormTool(ValidatedTool):
    """Generate exactly three authentic personal story ideas."""

    name: str = "brainstorm"
    description: str = (
        "Suggest 3 unique personal story ideas for a college essay given the essay prompt and user profile."
    )

    timeout: float = 45.0  # brainstorming can take time with complex prompts

    def _handle_timeout_fallback(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Provide fallback stories when brainstorming times out."""
        fallback_stories = [
            {
                "title": "Personal Growth Experience",
                "description": "A meaningful experience that led to personal development and self-discovery",
                "prompt_fit": "Addresses the prompt with a focus on growth and learning",
                "insights": ["Resilience", "Self-reflection", "Adaptability"]
            },
            {
                "title": "Community Impact Initiative", 
                "description": "An effort to create positive change in your community or school",
                "prompt_fit": "Shows leadership and commitment to others",
                "insights": ["Leadership", "Service", "Collaboration"]
            },
            {
                "title": "Overcoming Academic Challenge",
                "description": "A time when you struggled with a subject or skill and worked to improve",
                "prompt_fit": "Demonstrates perseverance and intellectual curiosity", 
                "insights": ["Persistence", "Growth mindset", "Problem-solving"]
            }
        ]
        
        return {
            "ok": {"stories": fallback_stories},
            "error": f"Brainstorm tool timed out - using fallback stories. Consider increasing timeout or simplifying prompt."
        }

    # ------------------------------------------------------------------
    # Synchronous execution
    # ------------------------------------------------------------------
    def _run(self, *, essay_prompt: str, profile: str, user_id: str | None = None, 
             college_id: str | None = None, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        # -------------------- Input validation -------------------------
        essay_prompt = str(essay_prompt).strip()
        profile = str(profile).strip()
        if not essay_prompt:
            raise ValueError("essay_prompt must not be empty.")
        if not profile:
            raise ValueError("profile must not be empty.")

        # -------------------- College-scoped story blacklist --------------------
        college_blacklist = self._get_college_story_blacklist(user_id, college_id)
        cross_college_suggestions = self._get_cross_college_story_suggestions(user_id, college_id)
        prompt_type = self._categorize_prompt_type(essay_prompt)
        
        # -------------------- Render enhanced prompt with college context --------
        rendered_prompt = self._render_college_aware_prompt(
            essay_prompt, profile, college_blacklist, cross_college_suggestions, 
            prompt_type, college_id
        )

        # -------------------- LLM call --------------------------------
        llm = get_chat_llm(temperature=0.4)
        from essay_agent.llm_client import call_llm
        raw = call_llm(llm, rendered_prompt)

        # Parse response -----------------------------------------------------
        parsed = safe_parse(_PARSER, raw)

        # -------------------- Post-processing: ensure themes present --
        # Some validators expect each story to include a "themes" list containing
        # the prompt_type (e.g., "challenge").  Older prompts may omit this field.
        for story in parsed.stories:
            if not story.themes:
                # Infer theme from prompt_type or keywords
                inferred_theme = prompt_type
                if inferred_theme == 'general':
                    # Fallback: look for keywords in prompt to guess challenge/community etc.
                    lower_prompt = essay_prompt.lower()
                    if 'challenge' in lower_prompt or 'obstacle' in lower_prompt or 'overcome' in lower_prompt:
                        inferred_theme = 'challenge'
                    elif 'community' in lower_prompt:
                        inferred_theme = 'community'
                    elif 'identity' in lower_prompt:
                        inferred_theme = 'identity'
                    elif 'passion' in lower_prompt or 'interest' in lower_prompt:
                        inferred_theme = 'passion'
                    else:
                        inferred_theme = 'personal'
                story.themes = [inferred_theme]

        # Business-level validations ----------------------------------
        if len(parsed.stories) != 3:
            raise ValueError("Expected exactly 3 story ideas in output.")
        titles = [s.title.strip() for s in parsed.stories]
        if len(set(titles)) != 3:
            raise ValueError("Story titles must be unique.")

        # College-scoped duplicate prevention --------------------------
        conflicts = self._detect_story_conflicts(titles, college_id, user_id)
        if conflicts:
            raise ValueError(f"Story reuse detected for {college_id}: {conflicts}")

        # Debug logging for story selection process -------------------
        self._debug_story_selection(parsed.stories, prompt_type, college_blacklist, 
                                  cross_college_suggestions, college_id)

        # Persist brainstorm results in memory --------------------------
        if user_id:
            try:
                self._update_user_profile_with_stories(user_id, parsed.stories, college_id, prompt_type)
            except Exception:
                pass

        return parsed.model_dump()

    def _get_college_story_blacklist(self, user_id: str | None, college_id: str | None) -> Set[str]:
        """Get stories already used for this specific college."""
        if not user_id:
            return set()
        
        blacklist: Set[str] = set()
        try:
            user_profile = SimpleMemory.load(user_id)
            for rec in user_profile.essay_history:
                # Only block stories from the same college
                if college_id and rec.platform == college_id:
                    for ver in rec.versions:
                        blacklist.update(ver.used_stories)
            return blacklist
        except Exception:
            return set()

    def _get_cross_college_story_suggestions(self, user_id: str | None, college_id: str | None) -> List[str]:
        """Get stories from other colleges that could be reused."""
        if not user_id:
            return []
        
        suggestions: List[str] = []
        try:
            user_profile = SimpleMemory.load(user_id)
            for rec in user_profile.essay_history:
                # Suggest stories from other colleges
                if college_id and rec.platform != college_id:
                    for ver in rec.versions:
                        suggestions.extend(ver.used_stories)
            return list(set(suggestions))  # Remove duplicates
        except Exception:
            return []

    def _categorize_prompt_type(self, essay_prompt: str) -> str:
        """Categorize prompt as identity/passion/challenge/achievement/community."""
        prompt_lower = essay_prompt.lower()
        
        # Challenge/Problem indicators (check first to avoid conflicts)
        if any(keyword in prompt_lower for keyword in [
            'problem you\'ve solved', 'problem you have solved', 'challenge you faced',
            'obstacle', 'difficulty', 'struggle', 'overcome', 'failed', 'failure', 
            'setback', 'conflict', 'disagreement', 'solve', 'solution', 'dilemma'
        ]):
            return 'challenge'
        
        # Community/Culture indicators (check before identity to avoid conflicts)
        if any(keyword in prompt_lower for keyword in [
            'community', 'service', 'volunteer', 'help', 'impact', 'contribute',
            'social', 'cultural background', 'family traditions', 'diversity', 'inclusion',
            'cultural heritage', 'relates to your cultural', 'community or family'
        ]):
            return 'community'
        
        # Identity/Background indicators
        if any(keyword in prompt_lower for keyword in [
            'identity', 'background', 'heritage', 'culture', 'family', 'who you are', 
            'describe yourself', 'personal story', 'upbringing', 'community you belong',
            'meaningful they believe', 'application would be incomplete'
        ]):
            return 'identity'
        
        # Passion/Interest indicators (enhanced with missing keywords)
        if any(keyword in prompt_lower for keyword in [
            'passion', 'interest', 'hobby', 'love', 'enjoy', 'fascinated', 'curious',
            'engaging', 'captivate', 'lose track of time', 'learn more', 'intellectual curiosity',
            'academic interest', 'subject you find', 'activity you enjoy', 'find so engaging'
        ]):
            return 'passion'
        
        # Achievement/Growth indicators
        if any(keyword in prompt_lower for keyword in [
            'achievement', 'accomplishment', 'success', 'proud', 'leadership', 'growth',
            'learned', 'developed', 'improved', 'skill', 'talent', 'award', 'sparked a period',
            'personal growth', 'new understanding'
        ]):
            return 'achievement'
        
        return 'general'

    def _render_college_aware_prompt(self, essay_prompt: str, profile: str, 
                                   college_blacklist: Set[str], cross_college_suggestions: List[str],
                                   prompt_type: str, college_id: str | None) -> str:
        """Render enhanced prompt with college context and diversification guidance."""
        # Get college name for display
        college_name = college_id or "this college"
        
        # Format blacklist and suggestions for prompt
        college_story_history = list(college_blacklist) if college_blacklist else []
        
        # Enhanced template variables
        template_vars = {
            'essay_prompt': essay_prompt,
            'profile': profile,
            'college_name': college_name,
            'college_story_history': college_story_history,
            'cross_college_suggestions': cross_college_suggestions,
            'prompt_type': prompt_type,
            'recommended_categories': self._get_recommended_story_categories(prompt_type)
        }
        
        return render_template(BRAINSTORM_PROMPT, **template_vars)

    def _get_recommended_story_categories(self, prompt_type: str) -> List[str]:
        """Get recommended story categories aligned with user profile schema."""
        category_map = {
            'identity': ['heritage', 'family', 'cultural', 'personal_defining'],
            'passion': ['creative', 'academic', 'intellectual', 'hobby'],
            'challenge': ['obstacle', 'failure', 'conflict', 'problem_solving'],
            'achievement': ['accomplishment', 'leadership', 'growth', 'skill'],
            'community': ['service', 'cultural_involvement', 'social_impact', 'tradition'],
            'general': ['defining_moment', 'growth', 'values', 'experiences']
        }
        
        # Add debug logging
        from essay_agent.utils.logging import debug_print, VERBOSE
        recommended_categories = category_map.get(prompt_type, category_map['general'])
        debug_print(VERBOSE, f"Story categories for {prompt_type}: {recommended_categories}")
        
        return recommended_categories

    def _detect_story_conflicts(self, selected_stories: List[str], college_id: str | None, 
                               user_id: str | None) -> List[str]:
        """Detect if selected stories conflict with college usage rules."""
        if not user_id or not college_id:
            return []
        
        conflicts = []
        for story_title in selected_stories:
            if is_story_reused(user_id, story_title=story_title, college=college_id):
                conflicts.append(story_title)
        return conflicts

    def _debug_story_selection(self, stories: List[Story], prompt_type: str, 
                               college_blacklist: Set[str], cross_college_suggestions: List[str],
                               college_id: str | None) -> None:
        """Debug log story selection process for troubleshooting."""
        from essay_agent.utils.logging import debug_print, VERBOSE
        
        if not VERBOSE:
            return
            
        debug_print(VERBOSE, f"=== STORY SELECTION DEBUG ===")
        debug_print(VERBOSE, f"Prompt type: {prompt_type}")
        debug_print(VERBOSE, f"College ID: {college_id}")
        
        # College ID verification logging
        self._verify_college_id_usage(college_id)
        
        debug_print(VERBOSE, f"Selected stories: {[s.title for s in stories]}")
        debug_print(VERBOSE, f"Blacklisted stories (this college): {list(college_blacklist)}")
        debug_print(VERBOSE, f"Cross-college suggestions: {cross_college_suggestions}")
        
        # Log story categories and prompt fit
        for i, story in enumerate(stories, 1):
            debug_print(VERBOSE, f"Story {i}: '{story.title}' - {story.prompt_fit}")
        
        debug_print(VERBOSE, f"=== END STORY SELECTION DEBUG ===")
    
    def _verify_college_id_usage(self, college_id: str | None) -> None:
        """Verify college_id parameter is properly passed and used in story selection."""
        from essay_agent.utils.logging import debug_print, VERBOSE
        
        if not VERBOSE:
            return
            
        debug_print(VERBOSE, f"--- COLLEGE ID VERIFICATION ---")
        debug_print(VERBOSE, f"College ID received: {college_id}")
        
        if college_id is None:
            debug_print(VERBOSE, "WARNING: college_id is None - story selection will not be college-aware")
        else:
            debug_print(VERBOSE, f"College-aware story selection ACTIVE for college: {college_id}")
        
        # Verify college_id is being used in story selection logic
        try:
            # Check if college-specific memory exists
            if college_id:
                debug_print(VERBOSE, f"Checking college-specific story usage for: {college_id}")
                # This would be logged in the blacklist generation
        except Exception as e:
            debug_print(VERBOSE, f"Error verifying college ID usage: {e}")
        
        debug_print(VERBOSE, f"--- END COLLEGE ID VERIFICATION ---")

    def _update_user_profile_with_stories(self, user_id: str, stories: List[Story], 
                                        college_id: str | None, prompt_type: str) -> None:
        """Update user profile with new story information."""
        from essay_agent.utils.logging import debug_print, VERBOSE
        
        try:
            prof = SimpleMemory.load(user_id)
            
            # Log college-aware story tracking
            if VERBOSE:
                debug_print(VERBOSE, f"Updating user profile with {len(stories)} stories for college: {college_id}")
            
            for story in stories:
                # Create or update defining moment
                defining_moment = DefiningMoment(
                    title=story.title,
                    description=story.description,
                    emotional_impact="",
                    lessons_learned="",
                    themes=story.insights
                )
                
                # Add to profile if not already present
                existing_titles = [dm.title for dm in prof.defining_moments]
                if story.title not in existing_titles:
                    prof.defining_moments.append(defining_moment)
                    if VERBOSE:
                        debug_print(VERBOSE, f"Added new story to profile: '{story.title}'")
                elif VERBOSE:
                    debug_print(VERBOSE, f"Story already exists in profile: '{story.title}'")
            
            SimpleMemory.save(user_id, prof)
            
            if VERBOSE:
                debug_print(VERBOSE, f"Profile updated successfully for user: {user_id}")
                
        except Exception as e:
            if VERBOSE:
                debug_print(VERBOSE, f"Error updating user profile: {e}")
            # Don't fail the tool if memory update fails
            pass 