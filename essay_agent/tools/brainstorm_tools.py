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
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.prompts.brainstorming import (
    STORY_SUGGESTION_PROMPT,
    STORY_MATCHING_PROMPT,
    STORY_EXPANSION_PROMPT,
    UNIQUENESS_VALIDATION_PROMPT
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
    stories: List[StorySuggestion] = Field(..., min_length=5, max_length=5, description="Exactly 5 stories")
    analysis_notes: str = Field(..., max_length=300, description="Profile analysis notes")
    
    @field_validator('stories')
    @classmethod
    def validate_stories_count(cls, v):
        if len(v) != 5:
            raise ValueError("Must provide exactly 5 story suggestions")
        return v

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

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@register_tool("suggest_stories")
class StorySuggestionTool(ValidatedTool):
    """Generate 5 relevant personal story suggestions from user profile"""
    
    name: str = "suggest_stories"
    description: str = (
        "Generate 5 relevant personal story suggestions from user profile for essay prompt."
    )
    
    timeout: float = 20.0  # Story suggestion may take longer
    
    def _run(self, *, essay_prompt: str, profile: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        essay_prompt = str(essay_prompt).strip()
        profile = str(profile).strip()
        
        if not essay_prompt:
            raise ValueError("essay_prompt must be a non-empty string")
        if not profile:
            raise ValueError("profile must be a non-empty string")
        
        if len(essay_prompt) > 2000:
            raise ValueError("essay_prompt too long (max 2000 chars)")
        if len(profile) > 10000:
            raise ValueError("profile too long (max 10000 chars)")
        
        # Render prompt
        try:
            prompt_text = render_template(
                STORY_SUGGESTION_PROMPT,
                essay_prompt=essay_prompt,
                profile=profile
            )
        except ValueError:
            # Fallback to minimal prompt if template variable mismatch occurs
            prompt_text = (
                "SYSTEM: You are an essay brainstorming assistant.\n"
                f"Essay Prompt: {essay_prompt}\n"
                f"User Profile: {profile}\n"
                "Generate 5 relevant personal story suggestions in valid JSON."
            )
        
        # Call LLM
        llm = get_chat_llm()
        response = call_llm(llm, prompt_text)
        
        # Parse response
        parser = pydantic_parser(StorySuggestionResult)
        parsed_result = safe_parse(parser, response)
        return parsed_result.model_dump()

@register_tool("match_story")
class StoryMatchingTool(ValidatedTool):
    """Rate how well a story matches an essay prompt (0-10 scale)"""
    
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
        return parsed_result.model_dump()

@register_tool("expand_story")
class StoryExpansionTool(ValidatedTool):
    """Generate follow-up questions to expand a story seed"""
    
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
        return parsed_result.model_dump()

@register_tool("validate_uniqueness")
class UniquenessValidationTool(ValidatedTool):
    """Check if story angle is unique and avoid clichés"""
    
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
        return parsed_result.model_dump() 