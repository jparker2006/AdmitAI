"""essay_agent.eval.metrics

Comprehensive metrics and validators for evaluating essay agent output.
Enhanced with LLM-powered evaluation for nuanced conversation quality assessment.
Includes word count validation, JSON schema validation, similarity scoring, and quality metrics.
"""

import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import math
import asyncio

from essay_agent.agent_legacy import EssayResult
from .llm_evaluator import LLMEvaluator, ConversationEvaluation, TurnEvaluation


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
        Validate word count against target.
        
        Args:
            text: The essay text to validate
            target: Target word count
            
        Returns:
            Dictionary with validation results
        """
        if not text or not text.strip():
            return {
                "passed": False,
                "actual_count": 0,
                "target_count": target,
                "percentage": 0.0,
                "error": "Empty essay text"
            }
        
        # Simple word count - split by whitespace
        actual_count = len(text.split())
        percentage = actual_count / target if target > 0 else 0.0
        
        # Check if within tolerance
        lower_bound = target * (1 - self.tolerance)
        upper_bound = target * (1 + self.tolerance)
        passed = lower_bound <= actual_count <= upper_bound
        
        return {
            "passed": passed,
            "actual_count": actual_count,
            "target_count": target,
            "percentage": percentage,
            "tolerance": self.tolerance,
            "bounds": {"lower": int(lower_bound), "upper": int(upper_bound)},
            "error": None if passed else f"Word count {actual_count} outside tolerance range {int(lower_bound)}-{int(upper_bound)}"
        }


class JSONSchemaValidator:
    """Validates JSON structure and required fields."""
    
    def validate_stories(self, stories: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Validate brainstorm stories structure.
        
        Args:
            stories: List of story dictionaries
            
        Returns:
            Dictionary with validation results
        """
        if not stories:
            return {
                "passed": False,
                "error": "No stories provided"
            }
        
        if not isinstance(stories, list):
            return {
                "passed": False,
                "error": "Stories must be a list"
            }
        
        # Check each story has required fields
        required_fields = ["title", "description", "prompt_fit", "insights"]
        errors = []
        
        for i, story in enumerate(stories):
            if not isinstance(story, dict):
                errors.append(f"Story {i} is not a dictionary")
                continue
            
            for field in required_fields:
                if field not in story:
                    errors.append(f"Story {i} missing required field: {field}")
                elif not story[field]:
                    errors.append(f"Story {i} has empty {field}")
        
        passed = len(errors) == 0
        return {
            "passed": passed,
            "story_count": len(stories),
            "errors": errors,
            "error": None if passed else f"Schema validation failed: {errors}"
        }
    
    def validate_outline(self, outline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate outline structure.
        
        Args:
            outline: Outline dictionary
            
        Returns:
            Dictionary with validation results
        """
        if not outline:
            return {
                "passed": False,
                "error": "No outline provided"
            }
        
        if not isinstance(outline, dict):
            return {
                "passed": False,
                "error": "Outline must be a dictionary"
            }
        
        # Check required sections
        required_sections = ["hook", "context", "conflict", "growth", "reflection"]
        errors = []
        
        for section in required_sections:
            if section not in outline:
                errors.append(f"Missing required section: {section}")
            elif not outline[section] or not isinstance(outline[section], str):
                errors.append(f"Section {section} is empty or not a string")
        
        passed = len(errors) == 0
        return {
            "passed": passed,
            "sections": list(outline.keys()),
            "errors": errors,
            "error": None if passed else f"Outline validation failed: {errors}"
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
    
    def keyword_similarity_debug(self, essay_text: str, prompt_keywords: List[str]) -> Dict[str, Any]:
        """
        Detailed keyword similarity analysis for debugging.
        
        Args:
            essay_text: The essay text to analyze
            prompt_keywords: List of expected keywords
            
        Returns:
            Dictionary with detailed analysis including:
            - matched_keywords: List of keywords found in essay
            - missing_keywords: List of keywords not found
            - partial_matches: List of partial keyword matches
            - similarity_score: Overall similarity score
            - recommendations: Suggestions for improvement
        """
        if not essay_text or not essay_text.strip():
            return {
                "matched_keywords": [],
                "missing_keywords": prompt_keywords,
                "partial_matches": [],
                "similarity_score": 0.0,
                "recommendations": ["Essay text is empty - cannot analyze keywords"]
            }
        
        if not prompt_keywords:
            return {
                "matched_keywords": [],
                "missing_keywords": [],
                "partial_matches": [],
                "similarity_score": 1.0,
                "recommendations": ["No keywords specified for this prompt"]
            }
        
        # Tokenize essay and keywords
        essay_tokens = self._tokenize(essay_text)
        keyword_tokens = [kw.lower() for kw in prompt_keywords]
        
        if not essay_tokens:
            return {
                "matched_keywords": [],
                "missing_keywords": prompt_keywords,
                "partial_matches": [],
                "similarity_score": 0.0,
                "recommendations": ["Essay contains no analyzable words"]
            }
        
        # Analyze keyword matches
        matched_keywords = []
        missing_keywords = []
        partial_matches = []
        
        for keyword in keyword_tokens:
            # Direct match
            if keyword in essay_tokens:
                matched_keywords.append(keyword)
            # Partial match (keyword appears in a compound word)
            elif any(keyword in token for token in essay_tokens):
                partial_token = next(token for token in essay_tokens if keyword in token)
                partial_matches.append(f"{keyword} (found in '{partial_token}')")
            else:
                missing_keywords.append(keyword)
        
        # Calculate similarity score
        full_match_score = len(matched_keywords)
        partial_match_score = len(partial_matches) * 0.5
        total_score = full_match_score + partial_match_score
        similarity_score = min(total_score / len(keyword_tokens), 1.0)
        
        # Generate recommendations
        recommendations = []
        if missing_keywords:
            recommendations.append(f"Consider incorporating these missing keywords: {', '.join(missing_keywords)}")
        if similarity_score < 0.3:
            recommendations.append("Essay needs stronger connection to prompt keywords")
        if len(matched_keywords) < len(keyword_tokens) * 0.5:
            recommendations.append("Try to use more prompt-specific terminology")
        if not recommendations:
            recommendations.append("Good keyword coverage - essay addresses prompt effectively")
        
        return {
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "partial_matches": partial_matches,
            "similarity_score": similarity_score,
            "recommendations": recommendations,
            "analysis_details": {
                "total_keywords": len(keyword_tokens),
                "essay_word_count": len(essay_tokens),
                "full_matches": len(matched_keywords),
                "partial_matches": len(partial_matches)
            }
        }
    
    def prompt_alignment_detailed(self, selected_story: Dict[str, Any], prompt_type: str) -> Dict[str, Any]:
        """
        Detailed prompt-story alignment analysis.
        
        Args:
            selected_story: Dictionary containing story information
            prompt_type: Type of prompt (identity, passion, challenge, etc.)
            
        Returns:
            Dictionary with detailed alignment analysis
        """
        if not selected_story:
            return {
                "prompt_category": prompt_type,
                "story_themes": [],
                "alignment_score": 0.0,
                "alignment_reasons": ["No story provided"],
                "improvement_suggestions": ["Select a story that matches the prompt type"]
            }
        
        # Extract story information
        story_title = selected_story.get("title", "")
        story_description = selected_story.get("description", "")
        story_themes = selected_story.get("themes", [])
        story_insights = selected_story.get("insights", [])
        
        # Define expected themes for each prompt type
        prompt_theme_mapping = {
            "identity": ["heritage", "background", "culture", "family", "identity", "personal"],
            "passion": ["creative", "academic", "intellectual", "hobby", "interest", "curiosity"],
            "challenge": ["obstacle", "difficulty", "problem", "adversity", "failure", "conflict"],
            "achievement": ["accomplishment", "success", "growth", "realization", "milestone"],
            "community": ["service", "impact", "leadership", "volunteering", "helping", "community"]
        }
        
        expected_themes = prompt_theme_mapping.get(prompt_type, [])
        
        # Calculate alignment score
        alignment_score = 0.0
        alignment_reasons = []
        
        # Check story themes against expected themes
        if story_themes:
            theme_matches = [theme for theme in story_themes if any(expected in theme.lower() for expected in expected_themes)]
            if theme_matches:
                alignment_score += 0.4
                alignment_reasons.append(f"Story themes match prompt type: {', '.join(theme_matches)}")
        
        # Check story title and description for prompt-relevant keywords
        combined_text = f"{story_title} {story_description}".lower()
        keyword_matches = [theme for theme in expected_themes if theme in combined_text]
        if keyword_matches:
            alignment_score += 0.3
            alignment_reasons.append(f"Story content contains relevant keywords: {', '.join(keyword_matches)}")
        
        # Check insights for growth/reflection elements
        if story_insights:
            growth_indicators = ["learned", "grew", "realized", "understood", "changed", "developed"]
            insight_text = " ".join(story_insights).lower()
            if any(indicator in insight_text for indicator in growth_indicators):
                alignment_score += 0.3
                alignment_reasons.append("Story includes growth and reflection elements")
        
        # Ensure score doesn't exceed 1.0
        alignment_score = min(alignment_score, 1.0)
        
        # Generate improvement suggestions
        improvement_suggestions = []
        if alignment_score < 0.3:
            improvement_suggestions.append(f"Consider selecting a story that better matches {prompt_type} prompts")
        if not theme_matches and story_themes:
            improvement_suggestions.append(f"Story themes don't align with {prompt_type} expectations")
        if not keyword_matches:
            improvement_suggestions.append(f"Story lacks keywords typical of {prompt_type} prompts")
        if not story_insights:
            improvement_suggestions.append("Add insights about personal growth or lessons learned")
        
        if not improvement_suggestions:
            improvement_suggestions.append("Good alignment - story matches prompt type well")
        
        return {
            "prompt_category": prompt_type,
            "story_themes": story_themes,
            "alignment_score": alignment_score,
            "alignment_reasons": alignment_reasons,
            "improvement_suggestions": improvement_suggestions,
            "analysis_details": {
                "expected_themes": expected_themes,
                "theme_matches": theme_matches if 'theme_matches' in locals() else [],
                "keyword_matches": keyword_matches if 'keyword_matches' in locals() else [],
                "story_title": story_title,
                "has_insights": bool(story_insights)
            }
        }


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
    """Enhanced quality metrics for essay evaluation with LLM integration.
    
    This class provides both sophisticated LLM-powered text analysis and legacy
    heuristic-based evaluation as a fallback option.
    """
    
    def __init__(self, use_legacy: bool = False):
        """Initialize quality metrics evaluator.
        
        Args:
            use_legacy: If True, use heuristic evaluation. If False, use LLM evaluation.
        """
        self.use_legacy = use_legacy
        if not use_legacy:
            # Import here to avoid circular imports
            from .llm_evaluator import LLMEvaluator
            self.llm_evaluator = LLMEvaluator()
        else:
            self.llm_evaluator = None
    
    async def evaluate_text_quality(
        self, 
        text: str, 
        context: Optional[Dict[str, Any]] = None,
        essay_prompt: Optional[str] = None
    ) -> Dict[str, float]:
        """Evaluate text quality using LLM or legacy heuristics.
        
        Args:
            text: Text to analyze
            context: Additional context for evaluation
            essay_prompt: Original essay prompt for context
            
        Returns:
            Dictionary with quality scores (0-1 range)
        """
        if self.use_legacy:
            return self._legacy_text_evaluation(text)
        return await self._llm_text_evaluation(text, context, essay_prompt)
    
    async def _llm_text_evaluation(
        self, 
        text: str, 
        context: Optional[Dict[str, Any]] = None,
        essay_prompt: Optional[str] = None
    ) -> Dict[str, float]:
        """Use LLMEvaluator for sophisticated text quality assessment."""
        try:
            # Create a simplified conversation turn for text evaluation
            from .conversation_runner import ConversationTurn
            from .conversational_scenarios import ConversationScenario
            from datetime import datetime
            
            # Create mock turn for text evaluation
            turn = ConversationTurn(
                turn_number=1,
                timestamp=datetime.now(),
                user_input=f"Please evaluate this essay: {essay_prompt or 'Essay evaluation request'}",
                agent_response=text,
                tools_used=["draft_essay"],
                memory_accessed=[],
                phase_name="evaluation",
                success_indicators_met=["essay_completed"],
                expected_behavior_match=1.0,
                response_time_seconds=0.0,
                word_count=len(text.split())
            )
            
            # Create mock scenario for evaluation context
            from .conversational_scenarios import ScenarioCategory, SuccessCriteria
            scenario = ConversationScenario(
                eval_id="text_quality_eval",
                name="Text Quality Evaluation",
                category=ScenarioCategory.NEW_USER,
                description="Text quality evaluation scenario",
                school="Generic",
                prompt=essay_prompt or "Evaluate essay quality",
                word_limit=len(text.split()),
                user_profile="evaluation_user",
                conversation_flow=[],
                success_criteria=SuccessCriteria(
                    conversation_turns={"min": 1, "max": 1},
                    tools_used={},
                    final_word_count={},
                    prompt_relevance={},
                    conversation_quality={}
                ),
                difficulty="easy",
                estimated_duration_minutes=1,
                tags=["evaluation", "text_quality"]
            )
            
            # Use default profile for evaluation
            from ..memory.user_profile_schema import UserProfile
            profile = UserProfile(
                user_id="evaluation_user",
                name="Evaluation User",
                email="eval@example.com"
            )
            
            # Get LLM evaluation
            evaluation = await self.llm_evaluator.evaluate_conversation_quality(
                conversation_history=[turn],
                user_profile=profile,
                scenario=scenario,
                context=context or {}
            )
            
            # Map LLM evaluation to text quality metrics
            return {
                "readability_score": evaluation.conversation_flow_score,
                "sentence_variety": evaluation.prompt_response_quality,
                "vocabulary_richness": evaluation.overall_quality_score,
                "overall_quality": evaluation.overall_quality_score,
                "engagement_score": evaluation.user_satisfaction_prediction,
                "coherence_score": evaluation.conversation_flow_score
            }
            
        except Exception as e:
            # Fallback to legacy evaluation on error
            print(f"Warning: LLM evaluation failed ({e}), falling back to legacy metrics")
            return self._legacy_text_evaluation(text)
    
    def _legacy_text_evaluation(self, text: str) -> Dict[str, float]:
        """Fallback to existing heuristic methods."""
        return {
            "readability_score": self.calculate_readability_score(text),
            "sentence_variety": self.calculate_sentence_variety(text),
            "vocabulary_richness": self.calculate_vocabulary_richness(text),
            "overall_quality": (
                self.calculate_readability_score(text) + 
                self.calculate_sentence_variety(text) + 
                self.calculate_vocabulary_richness(text)
            ) / 3.0,
            "engagement_score": self.calculate_readability_score(text),  # Approximation
            "coherence_score": self.calculate_sentence_variety(text)  # Approximation
        }
    
    # Synchronous wrapper for backward compatibility
    def score_conversation(self, turns: List, profile: Any = None, scenario: Any = None) -> Dict[str, float]:
        """Synchronous wrapper for backward compatibility.
        
        Args:
            turns: Conversation turns (legacy interface)
            profile: User profile 
            scenario: Conversation scenario
            
        Returns:
            Quality scores dictionary
        """
        if not turns:
            return {"overall_quality": 0.0}
        
        if self.use_legacy:
            # Legacy heuristic scoring
            return {"overall_quality": 0.5}  # Simple fallback
        
        # For synchronous calls, use asyncio.run with basic evaluation
        import asyncio
        try:
            # Simple text extraction for sync evaluation
            text = " ".join([getattr(turn, 'agent_response', str(turn)) for turn in turns])
            return asyncio.run(self.evaluate_text_quality(text))
        except Exception as e:
            print(f"Warning: Sync evaluation failed ({e}), using fallback")
            return {"overall_quality": 0.5}
    
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
    additional_results: List[EssayResult] = None,
    use_legacy_metrics: bool = False
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
    quality_metrics = QualityMetrics(use_legacy=use_legacy_metrics)
    
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
        if use_legacy_metrics:
            # Legacy heuristic evaluation
            report.add_metric("readability_score", quality_metrics.calculate_readability_score(result.final_draft))
            report.add_metric("sentence_variety", quality_metrics.calculate_sentence_variety(result.final_draft))
            report.add_metric("vocabulary_richness", quality_metrics.calculate_vocabulary_richness(result.final_draft))
        else:
            # Enhanced LLM evaluation (synchronous wrapper)
            try:
                import asyncio
                quality_scores = asyncio.run(quality_metrics.evaluate_text_quality(
                    text=result.final_draft,
                    context={"target_word_count": target_word_count},
                    essay_prompt=prompt_text
                ))
                
                # Add all LLM-derived scores
                for metric_name, score in quality_scores.items():
                    report.add_metric(metric_name, score)
                    
            except Exception as e:
                # Fallback to legacy metrics if LLM evaluation fails
                print(f"Warning: LLM quality evaluation failed ({e}), using legacy metrics")
                report.add_metric("readability_score", quality_metrics.calculate_readability_score(result.final_draft))
                report.add_metric("sentence_variety", quality_metrics.calculate_sentence_variety(result.final_draft))
                report.add_metric("vocabulary_richness", quality_metrics.calculate_vocabulary_richness(result.final_draft))
    
    # Overall pass/fail
    report.add_metric("overall_passed", report.passed)
    
    return report 