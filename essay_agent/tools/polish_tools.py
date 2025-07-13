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
from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.prompts.polish import (
    GRAMMAR_FIX_PROMPT,
    VOCABULARY_ENHANCEMENT_PROMPT,
    CONSISTENCY_CHECK_PROMPT,
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


@register_tool("optimize_word_count")
class WordCountOptimizerTool(ValidatedTool):
    """Intelligently trim essay to exact word count while preserving meaning and impact."""
    
    name: str = "optimize_word_count"
    description: str = (
        "Intelligently optimize essay word count to meet target requirements while preserving meaning and impact."
    )
    
    timeout: float = 5.0  # Pure Python function, should be fast
    
    def _run(self, *, essay_text: str, target_words: int, preserve_meaning: bool = True, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        # Input validation
        essay_text = str(essay_text).strip()
        if not essay_text:
            return {"error": "essay_text cannot be empty"}
        
        try:
            target_words = int(target_words)
        except (ValueError, TypeError):
            return {"error": "target_words must be a valid integer"}
        
        if target_words < 50:
            return {"error": "target_words must be at least 50"}
        
        if target_words > 2000:
            return {"error": "target_words cannot exceed 2000"}
        
        # Get current word count
        current_words = _count_words(essay_text)
        
        # Optimize text
        try:
            optimized_text = _intelligent_trim_text(essay_text, target_words, preserve_meaning)
            final_word_count = _count_words(optimized_text)
            
            # Calculate reduction statistics
            words_removed = current_words - final_word_count
            reduction_percentage = (words_removed / current_words) * 100 if current_words > 0 else 0
            
            return {
                "optimized_essay": optimized_text,
                "original_word_count": current_words,
                "final_word_count": final_word_count,
                "target_word_count": target_words,
                "words_removed": words_removed,
                "reduction_percentage": round(reduction_percentage, 1),
                "target_achieved": final_word_count <= target_words,
                "optimization_notes": (
                    f"Successfully reduced from {current_words} to {final_word_count} words "
                    f"({reduction_percentage:.1f}% reduction). "
                    f"{'Target achieved.' if final_word_count <= target_words else 'Additional trimming may be needed.'}"
                )
            }
        
        except Exception as e:
            return {"error": f"Word count optimization failed: {str(e)}"} 