"""essay_agent.tools.prompt_tools

LangChain-compatible tools for essay prompt analysis.
Each tool uses GPT-4 with high-stakes prompts to analyze essay prompts.
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
from essay_agent.prompts.prompt_analysis import (
    CLASSIFY_PROMPT_PROMPT,
    EXTRACT_REQUIREMENTS_PROMPT,
    SUGGEST_STRATEGY_PROMPT,
    DETECT_OVERLAP_PROMPT
)

# ---------------------------------------------------------------------------
# Pydantic schemas for response validation
# ---------------------------------------------------------------------------

class ClassifyResult(BaseModel):
    theme: str = Field(..., description="One of the allowed themes")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    rationale: str = Field(..., max_length=150, description="Brief explanation")
    
    @field_validator('theme')
    @classmethod
    def validate_theme(cls, v):
        allowed_themes = {
            'adversity', 'growth', 'identity', 'leadership', 'creativity',
            'service', 'challenge', 'career', 'curiosity', 'other'
        }
        if v not in allowed_themes:
            raise ValueError(f"Theme must be one of: {allowed_themes}")
        return v

class ExtractRequirementsResult(BaseModel):
    word_limit: Optional[int] = Field(None, description="Word limit or null if unspecified")
    key_questions: List[str] = Field(..., description="Direct questions from the prompt")
    evaluation_criteria: List[str] = Field(..., description="What will be evaluated")
    
    @field_validator('word_limit')
    @classmethod
    def validate_word_limit(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Word limit must be positive")
        return v

class SuggestStrategyResult(BaseModel):
    overall_strategy: str = Field(..., max_length=600, description="Strategic approach")
    recommended_story_traits: List[str] = Field(..., min_length=2, max_length=4, description="Story traits to highlight")
    potential_pitfalls: List[str] = Field(..., min_length=2, max_length=5, description="Common mistakes to avoid")

class DetectOverlapResult(BaseModel):
    overlaps_found: bool = Field(..., description="Whether overlaps were detected")
    overlap_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score 0.0-1.0")
    conflicting_essays: List[int] = Field(..., description="Indices of conflicting essays")
    
    @field_validator('conflicting_essays')
    @classmethod
    def validate_conflicting_essays(cls, v, info):
        if info.data.get('overlaps_found', False) and not v:
            raise ValueError("If overlaps_found is True, conflicting_essays cannot be empty")
        return v

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@register_tool("classify_prompt")
class ClassifyPromptTool(ValidatedTool):
    """Classify essay prompt by theme (adversity, growth, identity, etc.)"""
    
    name: str = "classify_prompt"
    description: str = (
        "Classify an essay prompt by its dominant theme and provide confidence scoring."
    )
    
    timeout: float = 10.0
    
    def _run(self, *, essay_prompt: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        essay_prompt = str(essay_prompt).strip()
        if not essay_prompt:
            raise ValueError("essay_prompt must not be empty")
        
        # Render prompt
        rendered_prompt = render_template(
            CLASSIFY_PROMPT_PROMPT,
            essay_prompt=essay_prompt
        )
        
        # LLM call
        llm = get_chat_llm(temperature=0.1)  # Low temperature for consistent classification
        raw = call_llm(llm, rendered_prompt)
        
        # Parse and validate
        parser = pydantic_parser(ClassifyResult)
        parsed = safe_parse(parser, raw)
        
        return parsed.model_dump()

@register_tool("extract_requirements")
class ExtractRequirementsTool(ValidatedTool):
    """Extract word limits, key questions, and evaluation criteria from essay prompt"""
    
    name: str = "extract_requirements"
    description: str = (
        "Extract explicit constraints and requirements from an essay prompt."
    )
    
    timeout: float = 10.0
    
    def _run(self, *, essay_prompt: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        essay_prompt = str(essay_prompt).strip()
        if not essay_prompt:
            raise ValueError("essay_prompt must not be empty")
        
        # Render prompt
        rendered_prompt = render_template(
            EXTRACT_REQUIREMENTS_PROMPT,
            essay_prompt=essay_prompt
        )
        
        # LLM call
        llm = get_chat_llm(temperature=0.0)  # Deterministic extraction
        raw = call_llm(llm, rendered_prompt)
        
        # Parse and validate
        parser = pydantic_parser(ExtractRequirementsResult)
        parsed = safe_parse(parser, raw)
        
        return parsed.model_dump()

@register_tool("suggest_strategy")
class SuggestStrategyTool(ValidatedTool):
    """Suggest response strategy for essay prompt given user's profile"""
    
    name: str = "suggest_strategy"
    description: str = (
        "Suggest a strategic approach for responding to an essay prompt based on user profile."
    )
    
    timeout: float = 15.0  # Strategy generation may take longer
    
    def _run(self, *, essay_prompt: str, profile: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        essay_prompt = str(essay_prompt).strip()
        profile = str(profile).strip()
        if not essay_prompt:
            raise ValueError("essay_prompt must not be empty")
        if not profile:
            raise ValueError("profile must not be empty")
        
        # Render prompt
        rendered_prompt = render_template(
            SUGGEST_STRATEGY_PROMPT,
            essay_prompt=essay_prompt,
            profile=profile
        )
        
        # LLM call
        llm = get_chat_llm(temperature=0.3)  # Moderate creativity for strategy
        raw = call_llm(llm, rendered_prompt)
        
        # Parse and validate
        parser = pydantic_parser(SuggestStrategyResult)
        parsed = safe_parse(parser, raw)
        
        return parsed.model_dump()

@register_tool("detect_overlap")
class DetectOverlapTool(ValidatedTool):
    """Check if story overlaps with previous essays"""
    
    name: str = "detect_overlap"
    description: str = (
        "Detect thematic or anecdotal overlap between a candidate story and previous essays."
    )
    
    timeout: float = 15.0  # Overlap detection may require analysis of multiple essays
    
    def _run(self, *, story: str, previous_essays: Union[List[str], str], **_: Any) -> Dict[str, Any]:
        # Input validation
        story = str(story).strip()
        if not story:
            raise ValueError("story must not be empty")
        
        # Handle previous_essays as either list or JSON string
        if isinstance(previous_essays, str):
            try:
                previous_essays = json.loads(previous_essays)
            except json.JSONDecodeError:
                # Treat as single essay string
                previous_essays = [previous_essays]
        
        if not isinstance(previous_essays, list):
            raise ValueError("previous_essays must be a list of strings or JSON array")
        
        # Filter out empty essays
        previous_essays = [essay.strip() for essay in previous_essays if essay.strip()]
        
        # Render prompt
        rendered_prompt = render_template(
            DETECT_OVERLAP_PROMPT,
            story=story,
            previous_essays=json.dumps(previous_essays)
        )
        
        # LLM call
        llm = get_chat_llm(temperature=0.1)  # Low temperature for consistent analysis
        raw = call_llm(llm, rendered_prompt)
        
        # Parse and validate
        parser = pydantic_parser(DetectOverlapResult)
        parsed = safe_parse(parser, raw)
        
        # Additional validation: ensure conflicting_essays indices are valid
        if parsed.conflicting_essays:
            max_index = len(previous_essays) - 1
            for idx in parsed.conflicting_essays:
                if idx < 0 or idx > max_index:
                    raise ValueError(f"Invalid essay index {idx}, must be 0-{max_index}")
        
        return parsed.model_dump()

# ---------------------------------------------------------------------------
# Convenience call wrappers (following existing tool patterns)
# ---------------------------------------------------------------------------

# All tools inherit the __call__ method from ValidatedTool which handles
# the standard BaseTool interface. No additional wrappers needed. 