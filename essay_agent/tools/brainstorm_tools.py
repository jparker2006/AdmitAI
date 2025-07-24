"""essay_agent.tools.brainstorm_tools

LangChain-compatible tools for brainstorming and story development.
Each tool uses GPT-4 with high-stakes prompts for story generation and analysis.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

# Tool infrastructure
from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import pydantic_parser, safe_parse
from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools.base import ValidatedTool, safe_model_to_dict
from essay_agent.tools import register_tool
from essay_agent.prompts.brainstorming import (
    STORY_SUGGESTION_PROMPT,
    STORY_MATCHING_PROMPT,
    STORY_EXPANSION_PROMPT,
    UNIQUENESS_VALIDATION_PROMPT,
    SPECIFIC_BRAINSTORM_PROMPT
)

# ---------------------------------------------------------------------------
# Pydantic schemas for response validation
# ---------------------------------------------------------------------------

class StorySuggestion(BaseModel):
    title: str = Field(..., max_length=60, description="Compelling story title")
    description: str = Field(..., max_length=500, description="Vivid story summary")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score 0.0-1.0")
    themes: List[str] = Field(..., min_length=1, max_length=5, description="Story themes")
    prompt_fit_explanation: str = Field(..., max_length=200, description="Why story fits prompt")
    unique_elements: List[str] = Field(..., min_length=1, max_length=3, description="Unique aspects")

class StorySuggestionResult(BaseModel):
    stories: List[StorySuggestion] = Field(..., min_length=1, description="One or more story suggestions")
    analysis_notes: str = Field("", max_length=300, description="Profile analysis notes")

class StoryMatchingResult(BaseModel):
    match_score: float = Field(..., ge=0.0, le=10.0, description="Match score 0.0-10.0")
    rationale: str = Field(..., max_length=800, description="Detailed score explanation")
    strengths: List[str] = Field(..., min_length=1, max_length=5, description="Story strengths")
    weaknesses: List[str] = Field(..., min_length=1, max_length=5, description="Story weaknesses")
    improvement_suggestions: List[str] = Field(..., min_length=1, max_length=5, description="Improvement strategies")
    optimization_priority: str = Field(..., max_length=200, description="Priority focus area")

class StoryExpansionResult(BaseModel):
    expansion_questions: List[str] = Field(..., min_length=5, max_length=8, description="Development questions")
    focus_areas: List[str] = Field(..., min_length=2, max_length=4, description="Priority development areas")
    missing_details: List[str] = Field(..., min_length=2, max_length=5, description="Missing story elements")
    development_priority: str = Field(..., max_length=200, description="Most important development focus")

class UniquenessValidationResult(BaseModel):
    uniqueness_score: float = Field(..., ge=0.0, le=1.0, description="Uniqueness score 0.0-1.0")
    is_unique: bool = Field(..., description="Whether story is sufficiently unique")
    cliche_risks: List[str] = Field(..., min_length=0, max_length=5, description="Cliché risks")
    differentiation_suggestions: List[str] = Field(..., min_length=1, max_length=5, description="Differentiation strategies")
    unique_elements: List[str] = Field(..., min_length=0, max_length=5, description="Unique story aspects")
    risk_mitigation: List[str] = Field(..., min_length=0, max_length=5, description="Risk mitigation strategies")
    recommendation: str = Field(..., max_length=300, description="Overall strategic guidance")

class BrainstormingResult(BaseModel):
    ideas: List[str] = Field(..., min_length=3, max_length=5, description="3-5 short idea strings")
    next_steps: str = Field(..., description="Suggested next action for the user")
    brainstorming_result: Optional[str] = Field(None, description="Human-readable preface")

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@register_tool("suggest_stories")
class StorySuggestionTool(ValidatedTool):
    """Generate five personal story suggestions for a given essay prompt.

    Args:
        essay_prompt: The college essay question or prompt text.
        profile: A narrative profile of the student (experiences, background, values).

    Returns (dict):
        stories (List[dict]): Exactly 5 story objects as defined in the output schema.
        analysis_notes (str): Short rationale for story selection.
        success / error keys handled by ValidatedTool wrapper.
    """
    
    name: str = "suggest_stories"  # Keep primary name for description
    description: str = (
        "Generate 5 relevant personal story suggestions from user profile for essay prompt."
    )
    
    timeout: float = 20.0  # Story suggestion may take longer
    
    def _run(
        self,
        *,
        tool_input: str = "",
        prompt: str = "",
        essay_prompt: str = "",
        profile: str = "",
        **_: Any,
    ) -> Dict[str, Any]:
        # Prioritize the most specific prompt argument available.
        effective_prompt = (prompt or essay_prompt or tool_input).strip()
        profile_str = (
            str(profile).strip()
            if isinstance(profile, str)
            else json.dumps(profile)
        )

        if not effective_prompt:
            raise ValueError(
                "An essay prompt must be provided via 'prompt', 'essay_prompt', or 'tool_input'."
            )
        if not profile_str:
            raise ValueError("profile must be a non-empty string")

        # Render prompt
        try:
            prompt_text = render_template(
                STORY_SUGGESTION_PROMPT,
                essay_prompt=effective_prompt,
                profile=profile_str,
            )
        except ValueError as exc:
            # Surface template errors for debugging
            print("⚠️  STORY_SUGGESTION_PROMPT render failed:", exc)
            raise

        # Call LLM with deterministic low temperature --------------------------------
        import os, textwrap
        temp = float(os.getenv("ESSAY_AGENT_BRAINSTORM_TEMP", "0.2"))
        llm = get_chat_llm(temperature=temp)

        # Optional prompt preview when debugging --------------------------------------
        if os.getenv("ESSAY_AGENT_SHOW_PROMPTS", "0") == "1":
            preview = textwrap.shorten(prompt_text.replace("\n", " "), width=500, placeholder="…")
            print(f"\n=== SUGGEST_STORIES PROMPT (temp={temp}) ===\n{preview}\n==============================\n")

        parser = pydantic_parser(StorySuggestionResult)

        response = self._call_llm_with_prompt_and_parser(
            llm,
            prompt_text=prompt_text,
            parser=parser,
            required_keys=["stories"],
        )
        # Return parsed payload; ValidatedTool will wrap it.
        return response

@register_tool("match_story")
class StoryMatchingTool(ValidatedTool):
    """Assess how well a story aligns with a specific essay prompt.

    Args:
        story: The full story text or concise summary to be evaluated.
        essay_prompt: The college essay prompt to match against.

    Returns (dict):
        match_score (float): Composite alignment score 0.0-10.0 (0.1 precision).
        rationale (str): Brief justification for the score.
        strengths (List[str]): Concrete alignment strengths.
        weaknesses (List[str]): Concrete alignment weaknesses.
        improvement_suggestions (List[str]): Actionable ways to improve alignment.
        optimization_priority (str): The single most impactful focus area.
    """
    
    name: str = "match_story"
    description: str = (
        "Rate how well a specific story matches an essay prompt with detailed analysis."
    )
    
    timeout: float = 15.0
    
    def _run(self, *, story: str, essay_prompt: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        story = str(story).strip()
        essay_prompt = str(essay_prompt).strip()
        
        if not story:
            raise ValueError("story must be a non-empty string")
        if not essay_prompt:
            raise ValueError("essay_prompt must be a non-empty string")
        
        if len(story) > 5000:
            raise ValueError("story too long (max 5000 chars)")
        if len(essay_prompt) > 2000:
            raise ValueError("essay_prompt too long (max 2000 chars)")
        
        # Render prompt
        try:
            prompt_text = render_template(
                STORY_MATCHING_PROMPT,
                story=story,
                essay_prompt=essay_prompt
            )
        except ValueError:
            prompt_text = (
                "SYSTEM: You are an essay story matching assistant.\n"
                f"Story: {story}\n"
                f"Essay Prompt: {essay_prompt}\n"
                "Provide alignment score and analysis in JSON."
            )
        
        # Call LLM
        llm = get_chat_llm()
        response = call_llm(llm, prompt_text)
        
        # Parse response
        parser = pydantic_parser(StoryMatchingResult)
        parsed_result = safe_parse(parser, response)
        return safe_model_to_dict(parsed_result)

@register_tool("expand_story")
class StoryExpansionTool(ValidatedTool):
    """Generate development questions and focus areas to expand a story seed.

    Args:
        story_seed: A short description or seed of the story that needs expansion.

    Returns (dict):
        expansion_questions (List[str]): 5-8 targeted questions.
        focus_areas (List[str]): 2-4 narrative aspects to focus on.
        missing_details (List[str]): 2-5 key details still needed.
        development_priority (str): Highest-priority area to tackle first.
    """
    
    name: str = "expand_story"
    description: str = (
        "Generate strategic follow-up questions to expand and develop a story seed."
    )
    
    timeout: float = 12.0
    
    def _run(self, *, story_seed: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        story_seed = str(story_seed).strip()
        
        if not story_seed:
            raise ValueError("story_seed must be a non-empty string")
        
        if len(story_seed) > 2000:
            raise ValueError("story_seed too long (max 2000 chars)")
        if len(story_seed) < 20:
            raise ValueError("story_seed too short (min 20 chars)")
        
        # Render prompt
        try:
            prompt_text = render_template(
                STORY_EXPANSION_PROMPT,
                story_seed=story_seed
            )
        except ValueError:
            prompt_text = (
                "SYSTEM: You are a story expansion assistant.\n"
                f"Story Seed: {story_seed}\n"
                "Ask follow-up questions in JSON."
            )
        
        # Call LLM
        llm = get_chat_llm()
        response = call_llm(llm, prompt_text)
        
        # Parse response
        parser = pydantic_parser(StoryExpansionResult)
        parsed_result = safe_parse(parser, response)
        return safe_model_to_dict(parsed_result)


@register_tool("brainstorm_specific")
class SpecificBrainstormTool(ValidatedTool):
    """Brainstorm specific ideas for a given topic or experience.

    Args:
        topic: A concise phrase capturing the subject or experience to brainstorm around.
        user_input: Raw user text (fallback if *topic* empty) to guide idea generation.

    Returns (dict):
        ideas (List[str]): 3-5 short idea strings.
        next_steps (str): Suggested next action for the user.
        success (bool): Indicates execution success.
        brainstorming_result (str, optional): Human-readable preface.
    """
    
    name: str = "brainstorm_specific"
    description: str = (
        "Generate specific, targeted brainstorming ideas around a particular topic or experience."
    )
    
    timeout: float = 15.0
    
    def _run(self, *, topic: str = "", user_input: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Run the brainstorming tool with validated inputs."""

        # Use topic if present, otherwise fallback to user_input
        effective_topic = (topic or user_input or "").strip()
        if not effective_topic:
            raise ValueError("Must provide either 'topic' or 'user_input'.")

        # Render prompt
        try:
            prompt_text = render_template(
                SPECIFIC_BRAINSTORM_PROMPT,
                topic=effective_topic,
                user_input=user_input  # Template expects both topic and user_input
            )
        except ValueError:
            prompt_text = (
                "SYSTEM: You are a brainstorming assistant.\n"
                f"Topic: {effective_topic}\n"
                "Provide specific ideas in JSON."
            )

        # Prepare for LLM call
        llm = get_chat_llm()
        parser = pydantic_parser(BrainstormingResult)

        # Call the helper and crucially, return its result
        return self._call_llm_with_prompt_and_parser(
            llm,
            prompt_text=prompt_text,
            parser=parser,
        )


@register_tool("story_development")
class StoryDevelopmentTool(ValidatedTool):
    """Develop and expand a story with rich details.

    Args:
        story: Draft or seed text of the story to enrich.
        user_input: Fallback user text if *story* empty.

    Returns (dict):
        developed_story (str): Short enriched version.
        development_questions (List[str]): 5 questions to deepen narrative.
        themes (List[str]): 3-5 thematic labels.
        next_steps (str): Recommended next action.
    """
    
    name: str = "story_development"
    description: str = (
        "Take a story seed and develop it with rich details, emotions, and insights."
    )
    
    timeout: float = 15.0
    
    def _run(self, *, story: str = "", user_input: str = "", **kwargs: Any) -> Dict[str, Any]:
        import os, json
        from essay_agent.prompts.templates import render_template
        from essay_agent.llm_client import get_chat_llm, call_llm

        story_content = story or user_input
        if not story_content:
            raise ValueError("story cannot be empty")

        # Offline deterministic stub ----------------------------
        offline = os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1"
        if offline:
            return {
                "developed_story": f"Let's develop your story about {story_content}:",
                "development_questions": [
                    "What specific moment stands out most?",
                    "What emotions were you feeling?",
                    "What details can you add to set the scene?",
                    "What was the turning point?",
                    "How did this experience change you?"
                ],
                "themes": ["growth", "challenge", "insight", "transformation"],
                "next_steps": "Add specific details and emotions to your story",
                "success": True,
            }

        # Online path ------------------------------------------
        from essay_agent.prompts.brainstorming import STORY_DEVELOPMENT_PROMPT

        rendered = render_template(STORY_DEVELOPMENT_PROMPT, story=story_content)
        llm = get_chat_llm(temperature=0.3)
        raw = call_llm(llm, rendered)
        try:
            data = json.loads(raw)
            # minimal key checks
            if not all(k in data for k in ("developed_story", "development_questions", "themes")):
                raise ValueError
        except Exception:
            data = {
                "developed_story": story_content,
                "development_questions": [],
                "themes": [],
            }
        data["success"] = True
        if "next_steps" not in data:
            data["next_steps"] = "Reflect on the development questions and expand your narrative."
        return data


@register_tool("story_themes")
class StoryThemesTool(ValidatedTool):
    """Identify and analyze themes within a story.

    Args:
        story: Full story text; fallback to user_input.

    Returns (dict):
        story_analysis (str): Summary line.
        identified_themes (List[str]): 3-5 themes.
        core_message (str): Essence of story in ≤20 words.
        essay_potential (str): High|Medium|Low.
        suggestions (str): Advice to strengthen theme focus.
    """
    
    name: str = "story_themes"
    description: str = (
        "Analyze a story to identify key themes, values, and messages."
    )
    
    timeout: float = 15.0
    
    def _run(self, *, story: str = "", user_input: str = "", **kwargs: Any) -> Dict[str, Any]:
        import os, json
        from essay_agent.prompts.templates import render_template
        from essay_agent.llm_client import get_chat_llm, call_llm

        story_content = story or user_input
        if not story_content:
            raise ValueError("story cannot be empty")

        offline = os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1"
        if offline:
            return {
                "story_analysis": f"Analyzing themes in: {story_content}",
                "identified_themes": [
                    "Personal growth and resilience",
                    "Overcoming challenges",
                    "Community and relationships",
                ],
                "core_message": "This story demonstrates growth through challenge",
                "essay_potential": "High",
                "suggestions": "Focus on the transformation aspect of your experience",
                "success": True,
            }

        from essay_agent.prompts.brainstorming import STORY_THEMES_PROMPT

        rendered = render_template(STORY_THEMES_PROMPT, story=story_content)
        llm = get_chat_llm(temperature=0.3)
        raw = call_llm(llm, rendered)
        try:
            data = json.loads(raw)
            if not all(k in data for k in ("identified_themes", "core_message")):
                raise ValueError
        except Exception:
            data = {
                "story_analysis": f"Analyzing themes in: {story_content}",
                "identified_themes": [],
                "core_message": "",
                "essay_potential": "Medium",
                "suggestions": "Add more specific details to highlight unique themes",
            }
        data["success"] = True
        return data

@register_tool("validate_uniqueness")
class UniquenessValidationTool(ValidatedTool):
    """Evaluate a story angle for uniqueness and cliché risk.

    Args:
        story_angle: Short description of the proposed story.
        previous_essays: List or single string of prior essays to compare against.

    Returns (dict):
        uniqueness_score (float): 0.00-1.00 uniqueness metric (two-decimal precision).
        is_unique (bool): Whether the angle is sufficiently unique.
        cliche_risks (List[str]): Potential cliché patterns.
        differentiation_suggestions (List[str]): Ways to make the story more original.
        unique_elements (List[str]): Elements already unique.
        risk_mitigation (List[str]): Actions to reduce cliché risk.
        recommendation (str): Concise overall guidance.
    """
    
    name: str = "validate_uniqueness"
    description: str = (
        "Check if a story angle is unique and help avoid overused college essay clichés."
    )
    
    timeout: float = 15.0
    
    def _run(self, *, story_angle: str, previous_essays: Optional[Union[List[str], str]] = None, **_: Any) -> Dict[str, Any]:
        # Input validation
        story_angle = str(story_angle).strip()
        
        if not story_angle:
            raise ValueError("story_angle must be a non-empty string")
        
        if len(story_angle) > 3000:
            raise ValueError("story_angle too long (max 3000 chars)")
        if len(story_angle) < 50:
            raise ValueError("story_angle too short (min 50 chars)")
        
        # Handle previous_essays
        if previous_essays is None:
            previous_essays = []
        elif isinstance(previous_essays, str):
            previous_essays = [previous_essays]
        elif not isinstance(previous_essays, list):
            raise ValueError("previous_essays must be a list of strings or a single string")
        
        # Convert to string for template
        previous_essays_str = "\n\n".join(previous_essays) if previous_essays else "None provided"
        
        # Render prompt
        try:
            prompt_text = render_template(
                UNIQUENESS_VALIDATION_PROMPT,
                story_angle=story_angle,
                previous_essays=previous_essays_str
            )
        except ValueError:
            prompt_text = (
                "SYSTEM: You are a uniqueness validation assistant.\n"
                f"Story Angle: {story_angle}\n"
                f"Previous Essays: {previous_essays_str}\n"
                "Assess uniqueness and provide JSON feedback."
            )
        
        # Call LLM
        llm = get_chat_llm()
        response = call_llm(llm, prompt_text)
        
        # Parse response
        parser = pydantic_parser(UniquenessValidationResult)
        parsed_result = safe_parse(parser, response)
        return safe_model_to_dict(parsed_result) 