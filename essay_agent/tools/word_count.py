"""essay_agent.tools.word_count

External Word Count Tool for accurate word counting and validation.
Provides Python-based word counting that is 100% reliable vs unreliable LLM counting.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool


class WordCountResult(BaseModel):
    """Result of word count validation."""
    word_count: int
    target: int
    passed: bool
    min_allowed: int
    max_allowed: int
    deviation: int
    deviation_percent: float
    tolerance: float


class AdjustmentSuggestion(BaseModel):
    """Suggestion for adjusting word count."""
    needs_expansion: bool
    needs_trimming: bool
    words_needed: int
    words_excess: int
    expansion_points: List[str] = Field(default_factory=list)
    trimming_points: List[str] = Field(default_factory=list)


@register_tool("word_count")
class WordCountTool(ValidatedTool):
    """External word count tool with accurate Python-based counting."""

    name: str = "word_count"
    description: str = (
        "Accurate word counting and validation tool using Python-based counting."
    )

    timeout: float = 5.0  # Word counting is fast

    def _run(self, *, text: str, target: Optional[int] = None, tolerance: float = 0.05, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        """Count words and optionally validate against target."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if tolerance is not None and not (0 < tolerance <= 0.5):
            raise ValueError("Tolerance must be between 0 and 0.5")

        word_count = self.count_words(text)
        
        result = {"word_count": word_count}
        
        if target is not None:
            if target <= 0:
                raise ValueError("Target word count must be positive")
            validation = self.validate_target(text, target, tolerance)
            result.update(validation.model_dump())
        
        return result

    def count_words(self, text: str) -> int:
        """
        Accurate Python-based word counting using split() method.
        
        Args:
            text: Text to count words in
            
        Returns:
            Number of words (spaces-separated tokens)
        """
        if not text or not text.strip():
            return 0
        
        # Split by whitespace and filter out empty strings
        words = [word for word in text.split() if word.strip()]
        return len(words)

    def validate_target(self, text: str, target: int, tolerance: float = 0.05) -> WordCountResult:
        """
        Validate that text meets target word count within tolerance.
        
        Args:
            text: Text to validate
            target: Target word count
            tolerance: Allowed deviation as decimal (0.05 = 5%)
            
        Returns:
            WordCountResult with validation details
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        if target <= 0:
            raise ValueError("Target word count must be positive")
        if not 0 < tolerance <= 0.5:
            raise ValueError("Tolerance must be between 0 and 0.5")

        word_count = self.count_words(text)
        
        # Calculate tolerance range
        min_allowed = int(target * (1 - tolerance))
        max_allowed = int(target * (1 + tolerance))
        
        passed = min_allowed <= word_count <= max_allowed
        deviation = word_count - target
        deviation_percent = (deviation / target) * 100
        
        return WordCountResult(
            word_count=word_count,
            target=target,
            passed=passed,
            min_allowed=min_allowed,
            max_allowed=max_allowed,
            deviation=deviation,
            deviation_percent=deviation_percent,
            tolerance=tolerance
        )

    def calculate_adjustment(self, text: str, target: int, tolerance: float = 0.05) -> AdjustmentSuggestion:
        """
        Calculate what adjustments are needed to meet target word count.
        
        Args:
            text: Current text
            target: Target word count
            tolerance: Allowed tolerance
            
        Returns:
            AdjustmentSuggestion with details on needed changes
        """
        validation = self.validate_target(text, target, tolerance)
        
        if validation.passed:
            return AdjustmentSuggestion(
                needs_expansion=False,
                needs_trimming=False,
                words_needed=0,
                words_excess=0
            )
        
        if validation.word_count < validation.min_allowed:
            # Need to expand
            words_needed = validation.min_allowed - validation.word_count
            expansion_points = self.suggest_expansion_points(text, words_needed)
            
            return AdjustmentSuggestion(
                needs_expansion=True,
                needs_trimming=False,
                words_needed=words_needed,
                words_excess=0,
                expansion_points=expansion_points
            )
        else:
            # Need to trim
            words_excess = validation.word_count - validation.max_allowed
            trimming_points = self.suggest_trimming_points(text, words_excess)
            
            return AdjustmentSuggestion(
                needs_expansion=False,
                needs_trimming=True,
                words_needed=0,
                words_excess=words_excess,
                trimming_points=trimming_points
            )

    def suggest_expansion_points(self, text: str, words_needed: int) -> List[str]:
        """
        Identify sections that can be expanded to add more words.
        
        Args:
            text: Current text
            words_needed: Number of words to add
            
        Returns:
            List of suggestions for expansion
        """
        if not text or words_needed <= 0:
            return []
        
        suggestions = []
        
        # Look for short paragraphs that could be expanded
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            word_count = len(paragraph.split())
            
            # Suggest expanding short paragraphs
            if word_count < 50:
                suggestions.append(f"Paragraph {i+1}: Add more vivid details and sensory descriptions")
            
            # Look for specific expansion opportunities
            if 'I felt' in paragraph or 'I thought' in paragraph:
                suggestions.append(f"Paragraph {i+1}: Expand emotional responses with specific examples")
            
            if any(action in paragraph.lower() for action in ['said', 'told', 'asked', 'replied']):
                suggestions.append(f"Paragraph {i+1}: Add dialogue and character interactions")
            
            if any(sense in paragraph.lower() for sense in ['saw', 'heard', 'smelled', 'tasted', 'felt']):
                suggestions.append(f"Paragraph {i+1}: Enhance sensory details and environment description")
        
        # Generic suggestions if no specific ones found
        if not suggestions:
            suggestions = [
                "Add more specific examples and concrete details",
                "Expand on emotional reactions and internal thoughts",
                "Include more dialogue and character interactions",
                "Add sensory details and environmental descriptions"
            ]
        
        # Limit suggestions based on words needed
        max_suggestions = min(len(suggestions), max(2, words_needed // 20))
        return suggestions[:max_suggestions]

    def suggest_trimming_points(self, text: str, words_excess: int) -> List[str]:
        """
        Identify sections that can be trimmed to remove excess words.
        
        Args:
            text: Current text
            words_excess: Number of words to remove
            
        Returns:
            List of suggestions for trimming
        """
        if not text or words_excess <= 0:
            return []
        
        suggestions = []
        
        # Look for common redundancies and verbose patterns
        if re.search(r'\b(very|really|quite|rather|somewhat|pretty)\b', text, re.IGNORECASE):
            suggestions.append("Remove unnecessary adverbs (very, really, quite, rather)")
        
        if re.search(r'\bthat\b', text):
            suggestions.append("Remove unnecessary 'that' conjunctions where possible")
        
        if re.search(r'\bin order to\b', text, re.IGNORECASE):
            suggestions.append("Replace 'in order to' with 'to'")
        
        if re.search(r'\bdue to the fact that\b', text, re.IGNORECASE):
            suggestions.append("Replace wordy phrases like 'due to the fact that' with 'because'")
        
        # Look for repetitive phrases
        words = text.lower().split()
        word_frequency = {}
        for word in words:
            if len(word) > 3:  # Only consider longer words
                word_frequency[word] = word_frequency.get(word, 0) + 1
        
        repeated_words = [word for word, count in word_frequency.items() if count > 3]
        if repeated_words:
            suggestions.append(f"Reduce repetition of words: {', '.join(repeated_words[:3])}")
        
        # Look for long paragraphs that could be condensed
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        for i, paragraph in enumerate(paragraphs):
            word_count = len(paragraph.split())
            if word_count > 150:
                suggestions.append(f"Paragraph {i+1}: Condense lengthy descriptions while preserving key details")
        
        # Generic suggestions if no specific ones found
        if not suggestions:
            suggestions = [
                "Remove redundant phrases and unnecessary words",
                "Combine similar sentences for better flow",
                "Eliminate filler words and weak modifiers",
                "Condense verbose descriptions while keeping essential details"
            ]
        
        # Limit suggestions based on words that need trimming
        max_suggestions = min(len(suggestions), max(2, words_excess // 15))
        return suggestions[:max_suggestions] 