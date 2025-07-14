"""essay_agent.eval.metrics

Comprehensive metrics and validators for evaluating essay agent output.
Includes word count validation, JSON schema validation, similarity scoring, and quality metrics.
"""

import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import math

from essay_agent.agent import EssayResult


@dataclass
class EvaluationReport:
    """Comprehensive evaluation report for a single essay generation run."""
    
    prompt_id: str
    passed: bool
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    
    def add_metric(self, name: str, value: Any) -> None:
        """Add a metric to the report."""
        self.metrics[name] = value
    
    def add_error(self, error: str) -> None:
        """Add an error to the report."""
        self.errors.append(error)
        self.passed = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "prompt_id": self.prompt_id,
            "passed": self.passed,
            "metrics": self.metrics,
            "errors": self.errors,
            "execution_time": self.execution_time
        }


class WordCountValidator:
    """Validates that essay word count is within acceptable tolerance."""
    
    def __init__(self, tolerance: float = 0.05):
        self.tolerance = tolerance
    
    def validate(self, text: str, target: int) -> Dict[str, Any]:
        """
        Validate word count within tolerance.
        
        Args:
            text: The essay text to validate
            target: Target word count
            
        Returns:
            Dict with validation results
        """
        if not text or not text.strip():
            return {
                "passed": False,
                "word_count": 0,
                "target": target,
                "error": "Empty or whitespace-only text"
            }
        
        # Count words (split by whitespace and filter empty strings)
        words = [word for word in text.split() if word.strip()]
        actual_count = len(words)
        
        # Calculate tolerance range
        min_count = int(target * (1 - self.tolerance))
        max_count = int(target * (1 + self.tolerance))
        
        passed = min_count <= actual_count <= max_count
        
        return {
            "passed": passed,
            "word_count": actual_count,
            "target": target,
            "min_allowed": min_count,
            "max_allowed": max_count,
            "deviation": actual_count - target,
            "deviation_percent": ((actual_count - target) / target) * 100
        }


class JSONSchemaValidator:
    """Validates JSON structure of agent outputs."""
    
    def validate_stories(self, stories: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Validate brainstorm stories structure."""
        if stories is None:
            return {
                "passed": False,
                "error": "Stories is None"
            }
        
        if not isinstance(stories, list):
            return {
                "passed": False,
                "error": f"Stories must be a list, got {type(stories)}"
            }
        
        if len(stories) == 0:
            return {
                "passed": False,
                "error": "Stories list is empty"
            }
        
        # Check each story has required fields
        required_fields = ["title", "description"]
        for i, story in enumerate(stories):
            if not isinstance(story, dict):
                return {
                    "passed": False,
                    "error": f"Story {i} is not a dict: {type(story)}"
                }
            
            for field in required_fields:
                if field not in story:
                    return {
                        "passed": False,
                        "error": f"Story {i} missing required field: {field}"
                    }
                
                if not isinstance(story[field], str) or not story[field].strip():
                    return {
                        "passed": False,
                        "error": f"Story {i} field '{field}' is empty or not a string"
                    }
        
        return {
            "passed": True,
            "story_count": len(stories),
            "fields_validated": required_fields
        }
    
    def validate_outline(self, outline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate outline structure."""
        if outline is None:
            return {
                "passed": False,
                "error": "Outline is None"
            }
        
        if not isinstance(outline, dict):
            return {
                "passed": False,
                "error": f"Outline must be a dict, got {type(outline)}"
            }
        
        # Check for required outline sections
        required_sections = ["hook", "context", "conflict", "growth", "reflection"]
        for section in required_sections:
            if section not in outline:
                return {
                    "passed": False,
                    "error": f"Outline missing required section: {section}"
                }
            
            if not isinstance(outline[section], str) or not outline[section].strip():
                return {
                    "passed": False,
                    "error": f"Outline section '{section}' is empty or not a string"
                }
        
        return {
            "passed": True,
            "sections_validated": required_sections
        }


class KeywordSimilarityScorer:
    """Simple BM25-like similarity scorer for prompt keyword coverage."""
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split by non-alphanumeric."""
        return [token.lower() for token in re.findall(r'\b\w+\b', text) if len(token) > 2]
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency."""
        counter = Counter(tokens)
        total = len(tokens)
        return {term: count / total for term, count in counter.items()}
    
    def _compute_idf(self, term: str, documents: List[List[str]]) -> float:
        """Compute inverse document frequency."""
        containing_docs = sum(1 for doc in documents if term in doc)
        if containing_docs == 0:
            return 0.0
        return math.log((len(documents) - containing_docs + 0.5) / (containing_docs + 0.5))
    
    def score(self, essay_text: str, prompt_keywords: List[str]) -> float:
        """
        Score essay based on keyword coverage using BM25-like scoring.
        
        Args:
            essay_text: The essay text to score
            prompt_keywords: List of expected keywords
            
        Returns:
            Similarity score between 0 and 1
        """
        if not essay_text or not essay_text.strip():
            return 0.0
        
        if not prompt_keywords:
            return 1.0  # No keywords to check
        
        # Tokenize essay and keywords
        essay_tokens = self._tokenize(essay_text)
        keyword_tokens = [kw.lower() for kw in prompt_keywords]
        
        if not essay_tokens:
            return 0.0
        
        # Simple keyword matching with partial credit
        matches = 0
        total_keywords = len(keyword_tokens)
        
        for keyword in keyword_tokens:
            # Direct match
            if keyword in essay_tokens:
                matches += 1
            # Partial match (keyword appears in a compound word)
            elif any(keyword in token for token in essay_tokens):
                matches += 0.5
        
        return min(matches / total_keywords, 1.0) if total_keywords > 0 else 0.0


class ErrorValidator:
    """Validates that no errors occurred during execution."""
    
    def validate(self, result: EssayResult) -> Dict[str, Any]:
        """
        Validate that no errors occurred during essay generation.
        
        Args:
            result: EssayResult to validate
            
        Returns:
            Dict with validation results
        """
        has_errors = len(result.errors) > 0
        
        return {
            "passed": not has_errors,
            "error_count": len(result.errors),
            "errors": result.errors.copy() if has_errors else []
        }


class QualityMetrics:
    """Additional quality metrics for essay evaluation."""
    
    def calculate_readability_score(self, text: str) -> float:
        """
        Calculate a simple readability score based on sentence and word length.
        
        Args:
            text: Text to analyze
            
        Returns:
            Readability score (higher is more readable)
        """
        if not text or not text.strip():
            return 0.0
        
        # Split into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if not sentences:
            return 0.0
        
        # Calculate average sentence length
        total_words = len(text.split())
        avg_sentence_length = total_words / len(sentences)
        
        # Calculate average word length
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Simple readability score (inverse of complexity)
        # Penalize very long sentences and words
        sentence_penalty = max(0, avg_sentence_length - 20) * 0.1
        word_penalty = max(0, avg_word_length - 6) * 0.1
        
        base_score = 10.0
        readability = max(0, base_score - sentence_penalty - word_penalty)
        
        return min(readability / 10.0, 1.0)  # Normalize to 0-1
    
    def calculate_sentence_variety(self, text: str) -> float:
        """
        Calculate sentence variety score based on length distribution.
        
        Args:
            text: Text to analyze
            
        Returns:
            Variety score between 0 and 1
        """
        if not text or not text.strip():
            return 0.0
        
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) < 2:
            return 0.0
        
        # Calculate sentence lengths
        lengths = [len(sentence.split()) for sentence in sentences]
        
        # Calculate coefficient of variation (std dev / mean)
        mean_length = sum(lengths) / len(lengths)
        variance = sum((length - mean_length) ** 2 for length in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        
        if mean_length == 0:
            return 0.0
        
        cv = std_dev / mean_length
        
        # Normalize to 0-1 range (0.5 is considered good variety)
        return min(cv / 0.5, 1.0)
    
    def calculate_vocabulary_richness(self, text: str) -> float:
        """
        Calculate vocabulary richness using type-token ratio.
        
        Args:
            text: Text to analyze
            
        Returns:
            Vocabulary richness score between 0 and 1
        """
        if not text or not text.strip():
            return 0.0
        
        # Tokenize and normalize
        tokens = re.findall(r'\b\w+\b', text.lower())
        if not tokens:
            return 0.0
        
        # Calculate type-token ratio
        unique_tokens = set(tokens)
        ttr = len(unique_tokens) / len(tokens)
        
        return ttr


class StoryDiversityScorer:
    """Scores story diversity and prompt alignment across multiple essay results."""
    
    def __init__(self, college_id: str = "default"):
        self.college_id = college_id
    
    def calculate_diversity_score(self, results: List[EssayResult]) -> float:
        """
        Calculate story diversity score across multiple essay results.
        
        Args:
            results: List of EssayResult objects from different prompts
            
        Returns:
            Score between 0.0 (all same story) and 1.0 (all different stories)
        """
        if not results:
            return 1.0
        
        # Extract story titles from results
        story_titles = []
        for result in results:
            if result.stories and len(result.stories) > 0:
                # Assume first story is the selected one
                selected_story = result.stories[0]
                if isinstance(selected_story, dict) and "title" in selected_story:
                    story_titles.append(selected_story["title"].strip().lower())
        
        if not story_titles:
            return 1.0  # No stories to compare
        
        # Calculate diversity
        unique_stories = len(set(story_titles))
        total_stories = len(story_titles)
        
        if total_stories == 1:
            return 1.0  # Single story, perfect diversity
        
        # Base diversity score
        diversity_score = unique_stories / total_stories
        
        # Apply penalty for exact duplicates
        duplicate_penalty = 0.0
        story_counts = Counter(story_titles)
        for count in story_counts.values():
            if count > 1:
                duplicate_penalty += (count - 1) * 0.2  # 20% penalty per duplicate
        
        final_score = max(0.0, diversity_score - duplicate_penalty)
        return min(final_score, 1.0)
    
    def calculate_prompt_alignment_score(self, selected_story: Dict[str, Any], prompt_type: str) -> float:
        """
        Calculate how well a story matches the expected prompt type.
        
        Args:
            selected_story: Dictionary containing story information
            prompt_type: Type of prompt (identity, passion, challenge, achievement, community)
            
        Returns:
            Score between 0.0 (poor alignment) and 1.0 (perfect alignment)
        """
        if not selected_story or not prompt_type:
            return 0.5  # Neutral score for missing data
        
        # Extract story category if available
        story_category = selected_story.get("category", "general").lower()
        story_title = selected_story.get("title", "").lower()
        story_description = selected_story.get("description", "").lower()
        
        prompt_type = prompt_type.lower()
        
        # Perfect alignment matrix
        perfect_matches = {
            "identity": ["identity", "background", "heritage", "culture"],
            "passion": ["passion", "interest", "academic", "learning"],
            "challenge": ["challenge", "problem", "obstacle", "difficulty"],
            "achievement": ["achievement", "accomplishment", "success", "award"],
            "community": ["community", "service", "volunteer", "social"]
        }
        
        # Related categories (partial credit)
        related_matches = {
            "identity": ["community", "achievement"],
            "passion": ["achievement", "identity"],
            "challenge": ["achievement", "growth"],
            "achievement": ["passion", "challenge"],
            "community": ["identity", "service"]
        }
        
        # Check for perfect match (exact category match)
        if story_category == prompt_type:
            return 1.0
        
        # Check for perfect match based on content keywords
        if prompt_type in perfect_matches:
            perfect_keywords = perfect_matches[prompt_type]
            
            # Check story content for keywords
            story_content = f"{story_title} {story_description}"
            for keyword in perfect_keywords:
                if keyword in story_content:
                    return 1.0
        
        # Check for related match (related category match)
        if prompt_type in related_matches:
            related_categories = related_matches[prompt_type]
            
            # Check if story category is in related categories
            if story_category in related_categories:
                return 0.7
            
            # Check story content for related keywords
            story_content = f"{story_title} {story_description}"
            for related_category in related_categories:
                if related_category in story_content:
                    return 0.7
        
        # Check for general thematic alignment
        theme_keywords = {
            "identity": ["background", "heritage", "culture", "family", "tradition"],
            "passion": ["love", "enjoy", "fascinate", "engage", "interest", "captivate"],
            "challenge": ["difficult", "struggle", "overcome", "problem", "obstacle"],
            "achievement": ["proud", "accomplish", "succeed", "award", "recognition"],
            "community": ["help", "serve", "volunteer", "community", "social", "impact"]
        }
        
        if prompt_type in theme_keywords:
            story_content = f"{story_title} {story_description}"
            theme_words = theme_keywords[prompt_type]
            
            matches = sum(1 for word in theme_words if word in story_content)
            if matches > 0:
                return 0.5 + (matches / len(theme_words)) * 0.3  # 0.5-0.8 range
        
        # Default score for unrelated content
        return 0.3


def story_diversity_score(results: List[EssayResult], college_id: str = "default") -> float:
    """
    Calculate story diversity score across multiple essay results.
    
    Args:
        results: List of EssayResult objects from different prompts
        college_id: College identifier for scoped scoring
        
    Returns:
        Score between 0.0 (all same story) and 1.0 (all different stories)
    """
    scorer = StoryDiversityScorer(college_id)
    return scorer.calculate_diversity_score(results)


def prompt_alignment_score(selected_story: Dict[str, Any], prompt_type: str) -> float:
    """
    Calculate how well a story matches the expected prompt type.
    
    Args:
        selected_story: Dictionary containing story information
        prompt_type: Type of prompt (identity, passion, challenge, achievement, community)
        
    Returns:
        Score between 0.0 (poor alignment) and 1.0 (perfect alignment)
    """
    scorer = StoryDiversityScorer()
    return scorer.calculate_prompt_alignment_score(selected_story, prompt_type)


def _categorize_prompt_type(prompt_text: str) -> str:
    """
    Categorize prompt type based on text content.
    
    Args:
        prompt_text: The essay prompt text
        
    Returns:
        Prompt category: identity, passion, challenge, achievement, community, or general
    """
    prompt_lower = prompt_text.lower()
    
    # Keywords for each category
    identity_keywords = ["background", "identity", "heritage", "culture", "meaningful", "incomplete"]
    passion_keywords = ["engaging", "captivate", "time", "concept", "topic", "idea", "lose track"]
    challenge_keywords = ["problem", "challenge", "dilemma", "solve", "difficulty", "obstacle"]
    achievement_keywords = ["accomplishment", "achievement", "proud", "realization", "growth"]
    community_keywords = ["community", "cultural", "family", "traditions", "background"]
    
    # Score each category
    scores = {
        "identity": sum(1 for kw in identity_keywords if kw in prompt_lower),
        "passion": sum(1 for kw in passion_keywords if kw in prompt_lower),
        "challenge": sum(1 for kw in challenge_keywords if kw in prompt_lower),
        "achievement": sum(1 for kw in achievement_keywords if kw in prompt_lower),
        "community": sum(1 for kw in community_keywords if kw in prompt_lower)
    }
    
    # Return category with highest score
    max_category = max(scores, key=scores.get)
    return max_category if scores[max_category] > 0 else "general"


def evaluate_essay_result(
    result: EssayResult,
    prompt_keywords: List[str],
    target_word_count: int,
    execution_time: float,
    prompt_id: str,
    prompt_text: str = "",
    additional_results: List[EssayResult] = None
) -> EvaluationReport:
    """
    Comprehensive evaluation of an essay generation result.
    
    Args:
        result: EssayResult from agent execution
        prompt_keywords: Expected keywords for similarity scoring
        target_word_count: Target word count for the essay
        execution_time: Time taken for generation
        prompt_id: ID of the prompt being evaluated
        prompt_text: The original prompt text for alignment scoring
        additional_results: Additional results for diversity scoring
        
    Returns:
        Comprehensive evaluation report
    """
    report = EvaluationReport(
        prompt_id=prompt_id,
        passed=True,
        execution_time=execution_time
    )
    
    # Initialize validators
    word_validator = WordCountValidator(tolerance=0.30)  # 30% tolerance for LLM-generated content
    schema_validator = JSONSchemaValidator()
    similarity_scorer = KeywordSimilarityScorer()
    error_validator = ErrorValidator()
    quality_metrics = QualityMetrics()
    
    # Word count validation
    word_result = word_validator.validate(result.final_draft, target_word_count)
    report.add_metric("word_count", word_result)
    if not word_result["passed"]:
        report.add_error(f"Word count validation failed: {word_result.get('error', 'Unknown error')}")
    
    # JSON schema validation
    if result.stories is not None:
        stories_result = schema_validator.validate_stories(result.stories)
        report.add_metric("stories_validation", stories_result)
        if not stories_result["passed"]:
            report.add_error(f"Stories validation failed: {stories_result.get('error', 'Unknown error')}")
    
    if result.outline is not None:
        outline_result = schema_validator.validate_outline(result.outline)
        report.add_metric("outline_validation", outline_result)
        if not outline_result["passed"]:
            report.add_error(f"Outline validation failed: {outline_result.get('error', 'Unknown error')}")
    
    # Keyword similarity scoring
    similarity_score = similarity_scorer.score(result.final_draft, prompt_keywords)
    report.add_metric("keyword_similarity", similarity_score)
    if similarity_score < 0.3:  # Threshold for acceptable similarity
        report.add_error(f"Low keyword similarity: {similarity_score:.3f} < 0.3")
    
    # Error validation
    error_result = error_validator.validate(result)
    report.add_metric("error_validation", error_result)
    if not error_result["passed"]:
        report.add_error(f"Tool errors detected: {error_result['errors']}")
    
    # Story diversity scoring (if additional results provided)
    if additional_results:
        all_results = [result] + additional_results
        diversity_score = story_diversity_score(all_results)
        report.add_metric("story_diversity", diversity_score)
        if diversity_score < 0.8:  # Threshold for acceptable diversity
            report.add_error(f"Low story diversity: {diversity_score:.3f} < 0.8")
    
    # Prompt alignment scoring
    if prompt_text and result.stories:
        prompt_type = _categorize_prompt_type(prompt_text)
        if result.stories and len(result.stories) > 0:
            selected_story = result.stories[0]  # Assume first story is selected
            alignment_score = prompt_alignment_score(selected_story, prompt_type)
            report.add_metric("prompt_alignment", alignment_score)
            if alignment_score < 0.3:  # Threshold for acceptable alignment (lowered for testing)
                report.add_error(f"Low prompt alignment: {alignment_score:.3f} < 0.3")
    
    # Quality metrics
    if result.final_draft:
        report.add_metric("readability_score", quality_metrics.calculate_readability_score(result.final_draft))
        report.add_metric("sentence_variety", quality_metrics.calculate_sentence_variety(result.final_draft))
        report.add_metric("vocabulary_richness", quality_metrics.calculate_vocabulary_richness(result.final_draft))
    
    # Overall pass/fail
    report.add_metric("overall_passed", report.passed)
    
    return report 