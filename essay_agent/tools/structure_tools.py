"""essay_agent.tools.structure_tools

LangChain-compatible tools for essay structure and outline optimization.
Each tool uses GPT-4 with high-stakes prompts to analyze and improve essay structure.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field, field_validator

# Tool infrastructure
from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import pydantic_parser, safe_parse
from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.prompts.structure import (
    OUTLINE_GENERATOR_PROMPT,
    STRUCTURE_VALIDATOR_PROMPT,
    TRANSITION_SUGGESTION_PROMPT,
    LENGTH_OPTIMIZER_PROMPT
)

# ---------------------------------------------------------------------------
# Pydantic schemas for response validation
# ---------------------------------------------------------------------------

class OutlineSection(BaseModel):
    hook: str = Field(..., description="Compelling opening that grabs attention")
    context: str = Field(..., description="Background and setting that establishes stakes")
    growth_moment: str = Field(..., description="Vivid scene showing challenge and response")
    reflection: str = Field(..., description="Lessons learned and forward-looking insight")

class SectionWordCounts(BaseModel):
    hook: int = Field(..., ge=50, le=150, description="Word count for hook section")
    context: int = Field(..., ge=100, le=300, description="Word count for context section")
    growth_moment: int = Field(..., ge=200, le=500, description="Word count for growth moment section")
    reflection: int = Field(..., ge=75, le=200, description="Word count for reflection section")

class OutlineGeneratorResult(BaseModel):
    outline: OutlineSection
    section_word_counts: SectionWordCounts
    estimated_word_count: int = Field(..., description="Sum of all section word counts")
    
    @field_validator('estimated_word_count')
    @classmethod
    def validate_word_count_sum(cls, v, info):
        if 'section_word_counts' in info.data:
            counts = info.data['section_word_counts']
            expected_sum = counts.hook + counts.context + counts.growth_moment + counts.reflection
            if v != expected_sum:
                raise ValueError(f"estimated_word_count ({v}) must equal sum of section counts ({expected_sum})")
        return v

class StructureValidatorResult(BaseModel):
    is_valid: bool = Field(..., description="True if overall score >= 7.0")
    score: float = Field(..., ge=0.0, le=10.0, description="Average score across all rubric dimensions")
    issues: List[str] = Field(..., description="Specific problems found in the outline")
    overall_feedback: str = Field(..., max_length=120, description="Concise actionable advice")
    
    @field_validator('is_valid')
    @classmethod
    def validate_is_valid(cls, v, info):
        if 'score' in info.data:
            expected_valid = info.data['score'] >= 7.0
            if v != expected_valid:
                raise ValueError(f"is_valid ({v}) must match score >= 7.0 ({expected_valid})")
        return v

class TransitionSuggestions(BaseModel):
    hook_to_context: str = Field(..., max_length=150, description="Transition from hook to context")
    context_to_growth: str = Field(..., max_length=150, description="Transition from context to growth moment")
    growth_to_reflection: str = Field(..., max_length=150, description="Transition from growth to reflection")

class TransitionSuggestionResult(BaseModel):
    transitions: TransitionSuggestions

class OptimizedCounts(BaseModel):
    hook: int = Field(..., ge=50, le=150, description="Optimized word count for hook")
    context: int = Field(..., ge=100, le=300, description="Optimized word count for context")
    growth_moment: int = Field(..., ge=200, le=500, description="Optimized word count for growth moment")
    reflection: int = Field(..., ge=75, le=200, description="Optimized word count for reflection")

class LengthOptimizerResult(BaseModel):
    optimized_counts: OptimizedCounts
    total: int = Field(..., description="Total word count (must equal target)")
    
    @field_validator('total')
    @classmethod
    def validate_total(cls, v, info):
        if 'optimized_counts' in info.data:
            counts = info.data['optimized_counts']
            expected_total = counts.hook + counts.context + counts.growth_moment + counts.reflection
            if v != expected_total:
                raise ValueError(f"total ({v}) must equal sum of optimized counts ({expected_total})")
        return v

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@register_tool("outline_generator")
class OutlineGeneratorTool(ValidatedTool):
    """Generate a structured four-part outline from a story idea and essay prompt"""
    
    name: str = "outline_generator"
    description: str = (
        "Create a structured outline with hook, context, growth moment, and reflection sections "
        "with appropriate word count allocation."
    )
    
    timeout: float = 15.0  # Outline generation may take longer
    
    def _run(self, *, story: str, essay_prompt: str, word_count: int = 650, **_: Any) -> Dict[str, Any]:
        # Input validation
        story = str(story).strip()
        essay_prompt = str(essay_prompt).strip()
        if not story:
            raise ValueError("story must not be empty")
        if not essay_prompt:
            raise ValueError("essay_prompt must not be empty")
        if not isinstance(word_count, int) or word_count <= 0:
            raise ValueError("word_count must be a positive integer")
        
        # Render prompt
        rendered_prompt = render_template(
            OUTLINE_GENERATOR_PROMPT,
            story=story,
            essay_prompt=essay_prompt,
            word_count=word_count
        )
        
        # LLM call
        llm = get_chat_llm(temperature=0.2)  # Low creativity for structured output
        raw = call_llm(llm, rendered_prompt)
        
        # Parse and validate
        parser = pydantic_parser(OutlineGeneratorResult)
        parsed = safe_parse(parser, raw)
        
        return parsed.model_dump()

@register_tool("structure_validator")
class StructureValidatorTool(ValidatedTool):
    """Validate outline's logical flow and emotional arc with scoring"""
    
    name: str = "structure_validator"
    description: str = (
        "Evaluate an outline's structure, flow, and quality with detailed feedback and scoring."
    )
    
    timeout: float = 12.0
    
    def _run(self, *, outline: Union[str, Dict[str, Any]], **_: Any) -> Dict[str, Any]:
        # Input validation and normalization
        if isinstance(outline, dict):
            outline_str = json.dumps(outline, indent=2)
        else:
            outline_str = str(outline).strip()
        
        if not outline_str:
            raise ValueError("outline must not be empty")
        
        # Render prompt
        rendered_prompt = render_template(
            STRUCTURE_VALIDATOR_PROMPT,
            outline=outline_str
        )
        
        # LLM call
        llm = get_chat_llm(temperature=0.1)  # Very low temperature for consistent scoring
        raw = call_llm(llm, rendered_prompt)
        
        # Parse and validate
        parser = pydantic_parser(StructureValidatorResult)
        parsed = safe_parse(parser, raw)
        
        return parsed.model_dump()

@register_tool("transition_suggestion")
class TransitionSuggestionTool(ValidatedTool):
    """Suggest smooth transitions between outline sections"""
    
    name: str = "transition_suggestion"
    description: str = (
        "Generate seamless transition sentences between outline sections: hook, context, growth moment, and reflection."
    )
    
    timeout: float = 10.0
    
    def _run(self, *, outline: Union[str, Dict[str, Any]], **_: Any) -> Dict[str, Any]:
        # Input validation and normalization
        if isinstance(outline, dict):
            outline_str = json.dumps(outline, indent=2)
        else:
            outline_str = str(outline).strip()
        
        if not outline_str:
            raise ValueError("outline must not be empty")
        
        # Render prompt
        rendered_prompt = render_template(
            TRANSITION_SUGGESTION_PROMPT,
            outline=outline_str
        )
        
        # LLM call
        llm = get_chat_llm(temperature=0.3)  # Moderate creativity for natural transitions
        raw = call_llm(llm, rendered_prompt)
        
        # Parse and validate
        parser = pydantic_parser(TransitionSuggestionResult)
        parsed = safe_parse(parser, raw)
        
        return parsed.model_dump()

@register_tool("length_optimizer")
class LengthOptimizerTool(ValidatedTool):
    """Optimize word count distribution across outline sections"""
    
    name: str = "length_optimizer"
    description: str = (
        "Redistribute word counts across outline sections to hit target length while maintaining balance."
    )
    
    timeout: float = 8.0  # Word count optimization is relatively fast
    
    def _run(self, *, outline: Union[str, Dict[str, Any]], target_word_count: int, **_: Any) -> Dict[str, Any]:
        # Input validation and normalization
        if isinstance(outline, dict):
            outline_str = json.dumps(outline, indent=2)
        else:
            outline_str = str(outline).strip()
        
        if not outline_str:
            raise ValueError("outline must not be empty")
        if not isinstance(target_word_count, int) or target_word_count <= 0:
            raise ValueError("target_word_count must be a positive integer")
        
        # Render prompt
        rendered_prompt = render_template(
            LENGTH_OPTIMIZER_PROMPT,
            outline=outline_str,
            target_word_count=target_word_count
        )
        
        # LLM call
        llm = get_chat_llm(temperature=0.0)  # Deterministic for word count calculations
        raw = call_llm(llm, rendered_prompt)
        
        # Parse and validate
        parser = pydantic_parser(LengthOptimizerResult)
        parsed = safe_parse(parser, raw)
        
        # Additional validation that total matches target
        if parsed.total != target_word_count:
            raise ValueError(f"Optimized total ({parsed.total}) must equal target ({target_word_count})")
        
        return parsed.model_dump()

# ---------------------------------------------------------------------------
# Convenience functions for testing and direct usage
# ---------------------------------------------------------------------------

def generate_outline(story: str, essay_prompt: str, word_count: int = 650) -> Dict[str, Any]:
    """Convenience function to generate an outline."""
    tool = OutlineGeneratorTool()
    return tool(story=story, essay_prompt=essay_prompt, word_count=word_count)

def validate_structure(outline: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function to validate outline structure."""
    tool = StructureValidatorTool()
    return tool(outline=outline)

def suggest_transitions(outline: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function to suggest transitions."""
    tool = TransitionSuggestionTool()
    return tool(outline=outline)

def optimize_length(outline: Union[str, Dict[str, Any]], target_word_count: int) -> Dict[str, Any]:
    """Convenience function to optimize word count distribution."""
    tool = LengthOptimizerTool()
    return tool(outline=outline, target_word_count=target_word_count)

__all__ = [
    "OutlineGeneratorTool",
    "StructureValidatorTool", 
    "TransitionSuggestionTool",
    "LengthOptimizerTool",
    "generate_outline",
    "validate_structure",
    "suggest_transitions",
    "optimize_length"
] 