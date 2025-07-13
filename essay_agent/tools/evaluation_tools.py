"""essay_agent.tools.evaluation_tools

LangChain-compatible tools for essay evaluation and scoring.
Each tool uses GPT-4 with high-stakes prompts to analyze completed essays.
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
from essay_agent.prompts.evaluation import (
    ESSAY_SCORING_PROMPT,
    WEAKNESS_HIGHLIGHT_PROMPT,
    CLICHE_DETECTION_PROMPT,
    ALIGNMENT_CHECK_PROMPT
)

# ---------------------------------------------------------------------------
# Pydantic schemas for response validation
# ---------------------------------------------------------------------------

class EssayScores(BaseModel):
    clarity: int = Field(..., ge=0, le=10, description="Clarity score (0-10)")
    insight: int = Field(..., ge=0, le=10, description="Insight score (0-10)")
    structure: int = Field(..., ge=0, le=10, description="Structure score (0-10)")
    voice: int = Field(..., ge=0, le=10, description="Voice score (0-10)")
    prompt_fit: int = Field(..., ge=0, le=10, description="Prompt fit score (0-10)")

class EssayScoringResult(BaseModel):
    scores: EssayScores = Field(..., description="Scores for each dimension")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Average of all dimension scores")
    is_strong_essay: bool = Field(..., description="True if overall_score >= 7.0")
    feedback: str = Field(..., max_length=200, description="Concise actionable feedback")
    
    @field_validator('overall_score')
    @classmethod
    def validate_overall_score(cls, v, info):
        if 'scores' in info.data:
            scores = info.data['scores']
            expected_avg = (scores.clarity + scores.insight + scores.structure + scores.voice + scores.prompt_fit) / 5
            if abs(v - expected_avg) > 0.1:  # Allow small floating point errors
                raise ValueError(f"overall_score ({v}) must be average of dimension scores ({expected_avg})")
        return v
    
    @field_validator('is_strong_essay')
    @classmethod
    def validate_is_strong_essay(cls, v, info):
        if 'overall_score' in info.data:
            expected_strong = info.data['overall_score'] >= 7.0
            if v != expected_strong:
                raise ValueError(f"is_strong_essay ({v}) must match overall_score >= 7.0 ({expected_strong})")
        return v

class WeaknessItem(BaseModel):
    text_excerpt: str = Field(..., max_length=150, description="Exact text from essay")
    weakness_type: str = Field(..., description="Type of weakness")
    severity: int = Field(..., ge=1, le=5, description="Severity level (1-5)")
    explanation: str = Field(..., max_length=100, description="Why this is weak")
    improvement_advice: str = Field(..., max_length=150, description="Specific actionable fix")
    
    @field_validator('weakness_type')
    @classmethod
    def validate_weakness_type(cls, v):
        allowed_types = ["content", "style", "structure", "clarity"]
        if v not in allowed_types:
            raise ValueError(f"weakness_type must be one of: {allowed_types}")
        return v

class WeaknessHighlightResult(BaseModel):
    weaknesses: List[WeaknessItem] = Field(..., description="List of weaknesses found")
    overall_weakness_count: int = Field(..., description="Total number of weaknesses")
    priority_focus: str = Field(..., max_length=50, description="Most important area to improve")
    
    @field_validator('weaknesses')
    @classmethod
    def validate_weakness_count(cls, v):
        if len(v) < 3 or len(v) > 5:
            raise ValueError(f"Must identify 3-5 weaknesses, got {len(v)}")
        return v
    
    @field_validator('overall_weakness_count')
    @classmethod
    def validate_overall_count(cls, v, info):
        if 'weaknesses' in info.data:
            expected_count = len(info.data['weaknesses'])
            if v != expected_count:
                raise ValueError(f"overall_weakness_count ({v}) must match number of weaknesses ({expected_count})")
        return v

class ClicheItem(BaseModel):
    text_excerpt: str = Field(..., max_length=100, description="Exact cliché phrase from essay")
    cliche_type: str = Field(..., description="Type of cliché")
    severity: int = Field(..., ge=1, le=5, description="Severity level (1-5)")
    frequency: int = Field(..., ge=1, description="Times this phrase appears")
    alternative_suggestion: str = Field(..., max_length=150, description="Specific replacement idea")
    
    @field_validator('cliche_type')
    @classmethod
    def validate_cliche_type(cls, v):
        allowed_types = ["overused_phrase", "generic_description", "essay_trope"]
        if v not in allowed_types:
            raise ValueError(f"cliche_type must be one of: {allowed_types}")
        return v

class ClicheDetectionResult(BaseModel):
    cliches_found: List[ClicheItem] = Field(..., description="List of clichés detected")
    total_cliches: int = Field(..., description="Number of clichés found")
    uniqueness_score: float = Field(..., ge=0.0, le=1.0, description="Uniqueness score (0.0-1.0)")
    overall_assessment: str = Field(..., max_length=100, description="Brief authenticity summary")
    
    @field_validator('total_cliches')
    @classmethod
    def validate_total_cliches(cls, v, info):
        if 'cliches_found' in info.data:
            expected_count = len(info.data['cliches_found'])
            if v != expected_count:
                raise ValueError(f"total_cliches ({v}) must match number of clichés found ({expected_count})")
        return v

class RequirementAnalysis(BaseModel):
    requirement: str = Field(..., max_length=100, description="Specific requirement from prompt")
    addressed: bool = Field(..., description="True if adequately addressed")
    quality: int = Field(..., ge=0, le=2, description="Quality score (0-2)")
    evidence: str = Field(..., max_length=150, description="Where/how essay addresses this")
    
    @field_validator('addressed')
    @classmethod
    def validate_addressed(cls, v, info):
        if 'quality' in info.data:
            expected_addressed = info.data['quality'] >= 1
            if v != expected_addressed:
                raise ValueError(f"addressed ({v}) must be true if quality >= 1")
        return v

class AlignmentCheckResult(BaseModel):
    alignment_score: float = Field(..., ge=0.0, le=10.0, description="Alignment score (0.0-10.0)")
    requirements_analysis: List[RequirementAnalysis] = Field(..., description="Analysis of each requirement")
    missing_elements: List[str] = Field(..., description="Requirements not adequately addressed")
    is_fully_aligned: bool = Field(..., description="True if alignment_score >= 8.0")
    improvement_priority: str = Field(..., max_length=100, description="Most important missing element")
    
    @field_validator('is_fully_aligned')
    @classmethod
    def validate_is_fully_aligned(cls, v, info):
        if 'alignment_score' in info.data:
            expected_aligned = info.data['alignment_score'] >= 8.0
            if v != expected_aligned:
                raise ValueError(f"is_fully_aligned ({v}) must match alignment_score >= 8.0 ({expected_aligned})")
        return v

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@register_tool("essay_scoring")
class EssayScoringTool(ValidatedTool):
    """Score essay on admissions rubric: clarity, insight, structure, voice, prompt fit"""
    
    name: str = "essay_scoring"
    description: str = (
        "Score a complete essay on the 5-dimension admissions rubric: clarity, insight, structure, voice, and prompt fit. "
        "Returns detailed scores (0-10 each) with overall assessment and feedback."
    )
    
    timeout: float = 20.0  # Essay scoring may take longer
    
    def _run(self, *, essay_text: str, essay_prompt: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        if not essay_text or not essay_text.strip():
            raise ValueError("essay_text cannot be empty")
        
        if not essay_prompt or not essay_prompt.strip():
            raise ValueError("essay_prompt cannot be empty")
        
        if len(essay_text) > 5000:
            raise ValueError("essay_text too long (max 5000 characters)")
        
        try:
            # Generate prompt and call LLM
            rendered_prompt = render_template(ESSAY_SCORING_PROMPT, essay_text=essay_text, essay_prompt=essay_prompt)
            llm = get_chat_llm(temperature=0.1)  # Low temperature for consistent scoring
            response = call_llm(llm, rendered_prompt)
            
            # Parse and validate response
            parser = pydantic_parser(EssayScoringResult)
            parsed = safe_parse(parser, response)
            
            return parsed.model_dump()
            
        except Exception as e:
            return {"error": f"Essay scoring failed: {str(e)}"}

@register_tool("weakness_highlight")
class WeaknessHighlightTool(ValidatedTool):
    """Identify specific weak sentences/paragraphs and explain why they're weak"""
    
    name: str = "weakness_highlight"
    description: str = (
        "Analyze an essay to identify 3-5 specific weaknesses that most need improvement. "
        "Returns weak sections with explanations and actionable improvement advice."
    )
    
    timeout: float = 15.0
    
    def _run(self, *, essay_text: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        if not essay_text or not essay_text.strip():
            raise ValueError("essay_text cannot be empty")
        
        if len(essay_text) > 5000:
            raise ValueError("essay_text too long (max 5000 characters)")
        
        try:
            # Generate prompt and call LLM
            rendered_prompt = render_template(WEAKNESS_HIGHLIGHT_PROMPT, essay_text=essay_text)
            llm = get_chat_llm(temperature=0.2)  # Slightly higher temperature for creativity
            response = call_llm(llm, rendered_prompt)
            
            # Parse and validate response
            parser = pydantic_parser(WeaknessHighlightResult)
            parsed = safe_parse(parser, response)
            
            return parsed.model_dump()
            
        except Exception as e:
            return {"error": f"Weakness highlighting failed: {str(e)}"}

@register_tool("cliche_detection")
class ClicheDetectionTool(ValidatedTool):
    """Flag overused phrases, tropes, and generic college essay language"""
    
    name: str = "cliche_detection"
    description: str = (
        "Identify clichés, overused phrases, and generic language that make essays blend into the crowd. "
        "Returns found clichés with severity ratings and alternative suggestions."
    )
    
    timeout: float = 12.0
    
    def _run(self, *, essay_text: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        if not essay_text or not essay_text.strip():
            raise ValueError("essay_text cannot be empty")
        
        if len(essay_text) > 5000:
            raise ValueError("essay_text too long (max 5000 characters)")
        
        try:
            # Generate prompt and call LLM
            rendered_prompt = render_template(CLICHE_DETECTION_PROMPT, essay_text=essay_text)
            llm = get_chat_llm(temperature=0.1)  # Low temperature for consistent detection
            response = call_llm(llm, rendered_prompt)
            
            # Parse and validate response
            parser = pydantic_parser(ClicheDetectionResult)
            parsed = safe_parse(parser, response)
            
            return parsed.model_dump()
            
        except Exception as e:
            return {"error": f"Cliché detection failed: {str(e)}"}

@register_tool("alignment_check")
class AlignmentCheckTool(ValidatedTool):
    """Check if essay directly addresses the prompt requirements"""
    
    name: str = "alignment_check"
    description: str = (
        "Verify that an essay addresses all explicit and implicit requirements of the prompt. "
        "Returns alignment score and analysis of missing elements."
    )
    
    timeout: float = 18.0  # Alignment checking may take longer
    
    def _run(self, *, essay_text: str, essay_prompt: str, **_: Any) -> Dict[str, Any]:
        # Input validation
        if not essay_text or not essay_text.strip():
            raise ValueError("essay_text cannot be empty")
        
        if not essay_prompt or not essay_prompt.strip():
            raise ValueError("essay_prompt cannot be empty")
        
        if len(essay_text) > 5000:
            raise ValueError("essay_text too long (max 5000 characters)")
        
        try:
            # Generate prompt and call LLM
            rendered_prompt = render_template(ALIGNMENT_CHECK_PROMPT, essay_text=essay_text, essay_prompt=essay_prompt)
            llm = get_chat_llm(temperature=0.1)  # Low temperature for consistent analysis
            response = call_llm(llm, rendered_prompt)
            
            # Parse and validate response
            parser = pydantic_parser(AlignmentCheckResult)
            parsed = safe_parse(parser, response)
            
            return parsed.model_dump()
            
        except Exception as e:
            return {"error": f"Alignment check failed: {str(e)}"}

# ---------------------------------------------------------------------------
# All tools are registered via decorators above
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Convenience functions for direct usage
# ---------------------------------------------------------------------------

def score_essay(essay_text: str, essay_prompt: str) -> Dict[str, Any]:
    """Score an essay on the admissions rubric."""
    tool = EssayScoringTool()
    return tool(essay_text=essay_text, essay_prompt=essay_prompt)

def highlight_weaknesses(essay_text: str) -> Dict[str, Any]:
    """Identify specific weaknesses in an essay."""
    tool = WeaknessHighlightTool()
    return tool(essay_text=essay_text)

def detect_cliches(essay_text: str) -> Dict[str, Any]:
    """Detect clichés and overused phrases in an essay."""
    tool = ClicheDetectionTool()
    return tool(essay_text=essay_text)

def check_alignment(essay_text: str, essay_prompt: str) -> Dict[str, Any]:
    """Check if essay addresses prompt requirements."""
    tool = AlignmentCheckTool()
    return tool(essay_text=essay_text, essay_prompt=essay_prompt) 