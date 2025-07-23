"""essay_agent.tools.evaluation_tools

LangChain-compatible tools for essay evaluation and scoring.
Each tool uses GPT-4 with high-stakes prompts to analyze completed essays.
Enhanced with workflow integration methods for revision loop orchestration.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Union, Tuple, Optional

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
    alternative_suggestion: str = Field(..., max_length=150, description="Better alternative")
    
    @field_validator('cliche_type')
    @classmethod
    def validate_cliche_type(cls, v):
        allowed_types = ["overused_phrase", "generic_opening", "predictable_conclusion", "common_metaphor"]
        if v not in allowed_types:
            raise ValueError(f"cliche_type must be one of: {allowed_types}")
        return v

class ClicheDetectionResult(BaseModel):
    cliches: List[ClicheItem] = Field(..., description="List of clichés found")
    overall_cliche_count: int = Field(..., description="Total number of clichés")
    originality_score: int = Field(..., ge=0, le=10, description="Originality score (0-10)")
    
    @field_validator('overall_cliche_count')
    @classmethod
    def validate_overall_count(cls, v, info):
        if 'cliches' in info.data:
            expected_count = len(info.data['cliches'])
            if v != expected_count:
                raise ValueError(f"overall_cliche_count ({v}) must match number of clichés ({expected_count})")
        return v

class AlignmentCheckResult(BaseModel):
    alignment_score: int = Field(..., ge=0, le=10, description="Prompt alignment score (0-10)")
    covered_aspects: List[str] = Field(..., description="Prompt aspects that are covered")
    missing_aspects: List[str] = Field(..., description="Prompt aspects that are missing")
    improvement_suggestions: List[str] = Field(..., description="Specific suggestions for better alignment")

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

            # Guarantee plain dict regardless of parser return type ---------
            from pydantic import BaseModel

            if isinstance(parsed, BaseModel):
                parsed = parsed.model_dump()
            return parsed
            
        except Exception as e:
            return {"error": f"Essay scoring failed: {str(e)}"}
    
    # ---------------------------------------------------------------------------
    # Workflow integration methods
    # ---------------------------------------------------------------------------
    
    def get_weakest_dimensions(self, result: Dict[str, Any]) -> List[Tuple[str, int]]:
        """Return dimensions with lowest scores for targeted revision."""
        if not result or "scores" not in result:
            return []
        
        scores = result["scores"]
        dimension_scores = [
            (dim, score) for dim, score in scores.items()
            if isinstance(score, (int, float))
        ]
        
        # Sort by score (ascending) and return all dimensions with their scores
        dimension_scores.sort(key=lambda x: x[1])
        return dimension_scores
    
    def generate_revision_feedback(self, result: Dict[str, Any]) -> str:
        """Generate specific revision instructions based on evaluation."""
        if not result or "scores" not in result:
            return "Focus on overall clarity and structure"
        
        weakest_dims = self.get_weakest_dimensions(result)
        if not weakest_dims:
            return "Focus on overall improvement and polish"
        
        # Focus on the lowest 2-3 scoring dimensions
        focus_dimensions = weakest_dims[:3]
        
        # Map dimensions to specific revision instructions
        dimension_instructions = {
            "clarity": "Improve logical organization and paragraph transitions. Make arguments clearer and more coherent.",
            "insight": "Develop deeper self-reflection and personal growth. Add more meaningful insights and lessons learned.",
            "structure": "Strengthen narrative flow and pacing. Improve introduction hook and conclusion impact.",
            "voice": "Enhance authentic personal voice with more specific details and vivid examples.",
            "prompt_fit": "Better address all aspects of the prompt. Ensure complete response to the question."
        }
        
        # Generate targeted feedback
        feedback_parts = []
        for dim, score in focus_dimensions:
            if dim in dimension_instructions:
                feedback_parts.append(f"**{dim.title()}** (Score: {score}/10): {dimension_instructions[dim]}")
        
        # Add overall feedback if available
        if "feedback" in result:
            feedback_parts.append(f"**Additional guidance**: {result['feedback']}")
        
        return " ".join(feedback_parts)
    
    async def evaluate_with_workflow_integration(self, essay_text: str, essay_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced evaluation with workflow-specific metadata."""
        # Run standard evaluation
        result = self._run(essay_text=essay_text, essay_prompt=essay_prompt)
        
        if "error" in result:
            return result
        
        # Add workflow-specific enhancements
        workflow_metadata = {
            "weakest_dimensions": self.get_weakest_dimensions(result),
            "revision_feedback": self.generate_revision_feedback(result),
            "improvement_priority": self._get_improvement_priority(result),
            "context_metadata": self._analyze_context(context)
        }
        
        # Merge with original result
        return {**result, "workflow_metadata": workflow_metadata}
    
    def _get_improvement_priority(self, result: Dict[str, Any]) -> str:
        """Determine the highest priority area for improvement."""
        weakest_dims = self.get_weakest_dimensions(result)
        if not weakest_dims:
            return "general_improvement"
        
        lowest_dim, lowest_score = weakest_dims[0]
        
        # Determine priority based on score thresholds
        if lowest_score <= 4:
            return f"critical_{lowest_dim}"
        elif lowest_score <= 6:
            return f"major_{lowest_dim}"
        else:
            return f"minor_{lowest_dim}"
    
    def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow context for additional insights."""
        metadata = {
            "revision_attempt": context.get("revision_attempt", 0),
            "previous_score": context.get("previous_score", 0.0),
            "time_elapsed": context.get("time_elapsed", 0.0)
        }
        
        # Calculate improvement if this is a revision
        if metadata["revision_attempt"] > 0 and metadata["previous_score"] > 0:
            current_score = context.get("current_score", 0.0)
            metadata["score_improvement"] = current_score - metadata["previous_score"]
            metadata["improvement_percentage"] = (metadata["score_improvement"] / metadata["previous_score"]) * 100
        
        return metadata
    
    def is_ready_for_polish(self, result: Dict[str, Any], threshold: float = 7.5) -> bool:
        """Check if essay is ready for polishing phase."""
        if not result or "overall_score" not in result:
            return False
        
        return result["overall_score"] >= threshold
    
    def get_revision_urgency(self, result: Dict[str, Any]) -> str:
        """Determine urgency level for revision."""
        if not result or "overall_score" not in result:
            return "unknown"
        
        score = result["overall_score"]
        
        if score >= 8.0:
            return "none"
        elif score >= 7.0:
            return "low"
        elif score >= 5.0:
            return "medium"
        else:
            return "high"

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
    
    def get_targeted_revision_focus(self, result: Dict[str, Any]) -> str:
        """Generate targeted revision focus based on weakness analysis."""
        if not result or "weaknesses" not in result:
            return "Focus on overall improvement"
        
        weaknesses = result["weaknesses"]
        priority_focus = result.get("priority_focus", "general improvement")
        
        # Group weaknesses by type
        weakness_groups = {}
        for weakness in weaknesses:
            weakness_type = weakness.get("weakness_type", "general")
            if weakness_type not in weakness_groups:
                weakness_groups[weakness_type] = []
            weakness_groups[weakness_type].append(weakness)
        
        # Generate focus based on most common weakness types
        focus_parts = [f"Priority: {priority_focus}"]
        
        for weakness_type, items in weakness_groups.items():
            if len(items) >= 2:  # If multiple weaknesses of same type
                focus_parts.append(f"Address {weakness_type} issues ({len(items)} identified)")
        
        return ". ".join(focus_parts)

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
    """Check how well essay aligns with prompt requirements"""
    
    name: str = "alignment_check"
    description: str = (
        "Analyze how well an essay addresses the specific prompt requirements. "
        "Returns alignment score and identifies missing aspects."
    )
    
    timeout: float = 15.0
    
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
# Utility functions for workflow integration
# ---------------------------------------------------------------------------

def create_enhanced_evaluator() -> EssayScoringTool:
    """Create an enhanced EssayScoringTool with workflow integration."""
    return EssayScoringTool()


async def evaluate_for_revision_loop(essay_text: str, essay_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate essay specifically for revision loop workflow."""
    evaluator = create_enhanced_evaluator()
    return await evaluator.evaluate_with_workflow_integration(essay_text, essay_prompt, context)


def generate_comprehensive_feedback(scoring_result: Dict[str, Any], weakness_result: Dict[str, Any]) -> str:
    """Generate comprehensive revision feedback from multiple evaluation tools."""
    feedback_parts = []
    
    # Add scoring-based feedback
    if scoring_result and "workflow_metadata" in scoring_result:
        feedback_parts.append(scoring_result["workflow_metadata"]["revision_feedback"])
    
    # Add weakness-based feedback
    if weakness_result and "weaknesses" in weakness_result:
        weakness_tool = WeaknessHighlightTool()
        feedback_parts.append(weakness_tool.get_targeted_revision_focus(weakness_result))
    
    return " | ".join(feedback_parts)


# ---------------------------------------------------------------------------
# Test utility for validating tools
# ---------------------------------------------------------------------------

tool = EssayScoringTool()
test_essay = "This is a test essay about overcoming challenges in my life."
test_prompt = "Describe a challenge you faced and how you overcame it."

async def test_workflow_integration():
    """Test the workflow integration features."""
    result = await tool.evaluate_with_workflow_integration(test_essay, test_prompt, {"revision_attempt": 1})
    print("Workflow integration test result:", result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_workflow_integration()) 

# ---------------------------------------------------------------------------
# Legacy convenience wrappers (maintain backward-compat with older tests)
# ---------------------------------------------------------------------------

def score_essay(*, essay_text: str, essay_prompt: str, **kwargs):  # noqa: D401
    """Backwards-compat functional alias for EssayScoringTool."""
    tool = EssayScoringTool()
    return tool(essay_text=essay_text, essay_prompt=essay_prompt, **kwargs)


def highlight_weaknesses(*, essay_text: str, **kwargs):  # noqa: D401
    tool = WeaknessHighlightTool()
    return tool(essay_text=essay_text, **kwargs)


def detect_cliches(*, essay_text: str, **kwargs):  # noqa: D401
    tool = ClicheDetectionTool()
    return tool(essay_text=essay_text, **kwargs)


def check_alignment(*, essay_text: str, essay_prompt: str, **kwargs):  # noqa: D401
    tool = AlignmentCheckTool()
    return tool(essay_text=essay_text, essay_prompt=essay_prompt, **kwargs) 