"""essay_agent.tools.polish_tools

LangChain-compatible polish and refinement tools (Section 3.6). These tools handle
final essay polishing including grammar correction, vocabulary enhancement, 
consistency checking, and intelligent word count optimization.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from pydantic import BaseModel, Field

# Tool infrastructure
from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import schema_parser, safe_parse
from essay_agent.response_parser import pydantic_parser, safe_parse
from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.prompts.polish import (
    GRAMMAR_FIX_PROMPT,
    VOCABULARY_ENHANCEMENT_PROMPT,
    CONSISTENCY_CHECK_PROMPT,
    OPTIMIZE_WORD_COUNT_PROMPT,
)

# ---------------------------------------------------------------------------
# JSON Schemas for Response Validation
# ---------------------------------------------------------------------------

_GRAMMAR_FIX_SCHEMA = {
    "type": "object",
    "properties": {
        "corrected_essay": {"type": "string"},
        "corrections_made": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0
        },
        "voice_preservation_notes": {"type": "string"},
        "error_count": {"type": "integer", "minimum": 0}
    },
    "required": ["corrected_essay", "corrections_made", "voice_preservation_notes", "error_count"]
}

_VOCABULARY_ENHANCEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "enhanced_essay": {"type": "string"},
        "vocabulary_changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "enhanced": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["original", "enhanced", "reason"]
            },
            "minItems": 0
        },
        "enhancement_summary": {"type": "string"},
        "voice_preservation_confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"]
        },
        "total_enhancements": {"type": "integer", "minimum": 0}
    },
    "required": ["enhanced_essay", "vocabulary_changes", "enhancement_summary", "voice_preservation_confidence", "total_enhancements"]
}

_CONSISTENCY_CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "consistency_report": {
            "type": "object",
            "properties": {
                "overall_consistency_score": {"type": "number", "minimum": 0, "maximum": 10},
                "tense_consistency": {
                    "type": "string",
                    "enum": ["strong", "moderate", "weak"]
                },
                "voice_consistency": {
                    "type": "string", 
                    "enum": ["strong", "moderate", "weak"]
                },
                "style_consistency": {
                    "type": "string",
                    "enum": ["strong", "moderate", "weak"]
                },
                "total_issues_found": {"type": "integer", "minimum": 0}
            },
            "required": ["overall_consistency_score", "tense_consistency", "voice_consistency", "style_consistency", "total_issues_found"]
        },
        "identified_issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue_type": {"type": "string"},
                    "location": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                    },
                    "current_text": {"type": "string"},
                    "recommended_fix": {"type": "string"}
                },
                "required": ["issue_type", "location", "description", "severity", "current_text", "recommended_fix"]
            },
            "minItems": 0
        },
        "consistency_improvements": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0
        },
        "corrected_essay": {"type": "string"},
        "improvement_summary": {"type": "string"}
    },
    "required": ["consistency_report", "identified_issues", "consistency_improvements", "corrected_essay", "improvement_summary"]
}

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _call_and_parse(prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:  # noqa: D401
    """Helper: call LLM with prompt and parse against schema."""
    try:
        llm = get_chat_llm()
        raw = call_llm(llm, prompt)
        parsed = safe_parse(schema_parser(schema), raw)

        # ``safe_parse`` returns a plain dict when using ``schema_parser``
        if isinstance(parsed, dict):
            return parsed

        # Unexpected – handle gracefully
        try:
            result = json.loads(str(parsed))
            return result
        except Exception as exc:
            return {"error": f"Failed to parse tool output: {exc}"}
    except Exception as e:
        return {"error": f"LLM call failed: {str(e)}"}

def _count_words(text: str) -> int:
    """Count words in text using essay-specific rules."""
    if not text or not text.strip():
        return 0
    
    # Remove extra whitespace and split on whitespace
    words = text.strip().split()
    
    # Filter out empty strings
    words = [word for word in words if word.strip()]
    
    return len(words)

def _intelligent_trim_text(text: str, target_words: int, preserve_meaning: bool = True) -> str:
    """Intelligently trim text to target word count while preserving meaning."""
    current_words = _count_words(text)
    
    if current_words == target_words:
        return text
    
    if current_words < target_words:
        # Text is already under target, return as-is
        return text
    
    # Need to trim words
    words_to_remove = current_words - target_words
    sentences = text.split('.')
    
    if preserve_meaning:
        # Try to remove less important words first
        # Remove redundant adverbs, adjectives, and filler words
        filler_words = {
            'very', 'really', 'quite', 'rather', 'somewhat', 'actually', 'basically',
            'essentially', 'literally', 'obviously', 'clearly', 'certainly', 'definitely',
            'absolutely', 'completely', 'totally', 'entirely', 'extremely', 'incredibly'
        }
        
        words = text.split()
        trimmed_words = []
        removed_count = 0
        
        for word in words:
            # Remove punctuation for comparison
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            # Skip filler words if we still need to remove words
            if removed_count < words_to_remove and clean_word in filler_words:
                removed_count += 1
                continue
            
            trimmed_words.append(word)
        
        # If we still need to remove words, trim from end of sentences
        if removed_count < words_to_remove:
            remaining_to_remove = words_to_remove - removed_count
            trimmed_words = trimmed_words[:-remaining_to_remove]
        
        return ' '.join(trimmed_words)
    
    else:
        # Simple truncation
        words = text.split()
        return ' '.join(words[:target_words])

# ---------------------------------------------------------------------------
# Tool Implementations
# ---------------------------------------------------------------------------

@register_tool("fix_grammar")
class GrammarFixTool(ValidatedTool):
    """Fix grammar, spelling, and style errors while preserving authentic voice."""
    
    name: str = "fix_grammar"
    description: str = (
        "Fix grammar, spelling, and style errors in an essay while preserving the student's authentic voice and meaning."
    )
    
    timeout: float = 15.0
    
    def _run(self, *, essay_text: str, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        # Input validation
        essay_text = str(essay_text).strip()
        if not essay_text:
            return {"error": "essay_text cannot be empty"}
        
        if len(essay_text) < 50:
            return {"error": "essay_text must be at least 50 characters"}
        
        # Render prompt and call LLM
        prompt = render_template(GRAMMAR_FIX_PROMPT, essay_text=essay_text)
        return _call_and_parse(prompt, _GRAMMAR_FIX_SCHEMA)


@register_tool("enhance_vocabulary")
class VocabularyEnhancementTool(ValidatedTool):
    """Suggest stronger, more precise vocabulary while maintaining authentic voice."""
    
    name: str = "enhance_vocabulary"
    description: str = (
        "Enhance vocabulary precision and strength in an essay while maintaining the student's authentic voice."
    )
    
    timeout: float = 18.0
    
    def _run(self, *, essay_text: str, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        # Input validation
        essay_text = str(essay_text).strip()
        if not essay_text:
            return {"error": "essay_text cannot be empty"}
        
        if len(essay_text) < 50:
            return {"error": "essay_text must be at least 50 characters"}
        
        # Render prompt and call LLM
        prompt = render_template(VOCABULARY_ENHANCEMENT_PROMPT, essay_text=essay_text)
        return _call_and_parse(prompt, _VOCABULARY_ENHANCEMENT_SCHEMA)


@register_tool("check_consistency")
class ConsistencyCheckTool(ValidatedTool):
    """Check for tense, voice, and stylistic consistency with detailed reporting."""
    
    name: str = "check_consistency"
    description: str = (
        "Check an essay for tense, voice, and stylistic consistency and provide detailed analysis and fixes."
    )
    
    timeout: float = 20.0
    
    def _run(self, *, essay_text: str, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        # Input validation
        essay_text = str(essay_text).strip()
        if not essay_text:
            return {"error": "essay_text cannot be empty"}
        
        if len(essay_text) < 50:
            return {"error": "essay_text must be at least 50 characters"}
        
        # Render prompt and call LLM
        prompt = render_template(CONSISTENCY_CHECK_PROMPT, essay_text=essay_text)
        return _call_and_parse(prompt, _CONSISTENCY_CHECK_SCHEMA)


class OptimizeWordCountResult(BaseModel):
    optimized_text: str = Field(..., description="Text adjusted to the target word count")
    original_word_count: int = Field(..., description="Original word count")
    final_word_count: int = Field(..., description="Final word count after optimization")


@register_tool("optimize_word_count")
class WordCountOptimizerTool(ValidatedTool):
    """Adjust text to meet a target word count.

    Args:
        text (str): The text to be optimized.
        target_count (int): The desired word count.
    """

    name: str = "optimize_word_count"
    description: str = "Adjust text to meet a target word count."
    timeout: float = 20.0

    def _run(self, *, text: str, target_count: int, **_: Any) -> Dict[str, Any]:
        text = str(text).strip()
        if not text:
            raise ValueError("text must not be empty.")
        if not isinstance(target_count, int) or target_count <= 0:
            raise ValueError("target_count must be a positive integer.")

        original_word_count = len(text.split())

        rendered_prompt = render_template(
            OPTIMIZE_WORD_COUNT_PROMPT,
            text=text,
            target_count=target_count,
        )

        llm = get_chat_llm(temperature=0.2)
        raw = call_llm(llm, rendered_prompt)

        parser = pydantic_parser(OptimizeWordCountResult)
        parsed = safe_parse(parser, raw)

        # Ensure the final word count from the model is accurate
        parsed.final_word_count = len(parsed.optimized_text.split())
        parsed.original_word_count = original_word_count
        
        return parsed.model_dump() 