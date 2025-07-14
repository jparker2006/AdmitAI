"""Unit tests for evaluation metrics including story diversity and prompt alignment."""

import pytest
from essay_agent.agent import EssayResult
from essay_agent.eval.metrics import (
    StoryDiversityScorer,
    story_diversity_score,
    prompt_alignment_score,
    _categorize_prompt_type,
    evaluate_essay_result,
    EvaluationReport
)


class TestStoryDiversityScorer:
    """Test story diversity scoring functionality."""
    
    def test_empty_results(self):
        """Test diversity scoring with empty results."""
        scorer = StoryDiversityScorer("test_college")
        score = scorer.calculate_diversity_score([])
        assert score == 1.0
    
    def test_single_result(self):
        """Test diversity scoring with single result."""
        result = EssayResult(
            final_draft="Test essay",
            stories=[{"title": "Test Story", "description": "Test description"}]
        )
        scorer = StoryDiversityScorer("test_college")
        score = scorer.calculate_diversity_score([result])
        assert score == 1.0
    
    def test_all_different_stories(self):
        """Test diversity scoring with all different stories."""
        results = [
            EssayResult(
                final_draft="Essay 1",
                stories=[{"title": "Story 1", "description": "First story"}]
            ),
            EssayResult(
                final_draft="Essay 2", 
                stories=[{"title": "Story 2", "description": "Second story"}]
            ),
            EssayResult(
                final_draft="Essay 3",
                stories=[{"title": "Story 3", "description": "Third story"}]
            )
        ]
        scorer = StoryDiversityScorer("test_college")
        score = scorer.calculate_diversity_score(results)
        assert score == 1.0
    
    def test_all_same_stories(self):
        """Test diversity scoring with all same stories."""
        results = [
            EssayResult(
                final_draft="Essay 1",
                stories=[{"title": "Same Story", "description": "Same description"}]
            ),
            EssayResult(
                final_draft="Essay 2",
                stories=[{"title": "Same Story", "description": "Same description"}]
            ),
            EssayResult(
                final_draft="Essay 3",
                stories=[{"title": "Same Story", "description": "Same description"}]
            )
        ]
        scorer = StoryDiversityScorer("test_college")
        score = scorer.calculate_diversity_score(results)
        assert score < 0.5  # Should be heavily penalized
    
    def test_partial_duplicates(self):
        """Test diversity scoring with partial duplicates."""
        results = [
            EssayResult(
                final_draft="Essay 1",
                stories=[{"title": "Unique Story", "description": "First story"}]
            ),
            EssayResult(
                final_draft="Essay 2",
                stories=[{"title": "Repeated Story", "description": "Second story"}]
            ),
            EssayResult(
                final_draft="Essay 3",
                stories=[{"title": "Repeated Story", "description": "Third story"}]
            )
        ]
        scorer = StoryDiversityScorer("test_college")
        score = scorer.calculate_diversity_score(results)
        assert 0.4 < score < 0.9  # Should be partially penalized
    
    def test_missing_stories(self):
        """Test diversity scoring with missing stories."""
        results = [
            EssayResult(final_draft="Essay 1", stories=None),
            EssayResult(final_draft="Essay 2", stories=[])
        ]
        scorer = StoryDiversityScorer("test_college")
        score = scorer.calculate_diversity_score(results)
        assert score == 1.0


class TestPromptAlignmentScorer:
    """Test prompt alignment scoring functionality."""
    
    def test_perfect_alignment(self):
        """Test perfect alignment between story and prompt."""
        scorer = StoryDiversityScorer()
        
        # Identity story for identity prompt
        story = {
            "title": "Cultural Heritage",
            "description": "Learning about my family's cultural background",
            "category": "identity"
        }
        score = scorer.calculate_prompt_alignment_score(story, "identity")
        assert score == 1.0
        
        # Passion story for passion prompt
        story = {
            "title": "Coding Passion",
            "description": "My love for programming and problem-solving",
            "category": "passion"
        }
        score = scorer.calculate_prompt_alignment_score(story, "passion")
        assert score == 1.0
    
    def test_related_alignment(self):
        """Test related alignment between story and prompt."""
        scorer = StoryDiversityScorer()
        
        # Achievement story for passion prompt (related)
        story = {
            "title": "Science Competition Win",
            "description": "Winning a regional science competition",
            "category": "achievement"
        }
        score = scorer.calculate_prompt_alignment_score(story, "passion")
        assert score == 0.7
    
    def test_poor_alignment(self):
        """Test poor alignment between story and prompt."""
        scorer = StoryDiversityScorer()
        
        # Unrelated story and prompt
        story = {
            "title": "Random Story",
            "description": "Something completely unrelated",
            "category": "general"
        }
        score = scorer.calculate_prompt_alignment_score(story, "identity")
        assert score == 0.3
    
    def test_missing_data(self):
        """Test alignment scoring with missing data."""
        scorer = StoryDiversityScorer()
        
        # Missing story
        score = scorer.calculate_prompt_alignment_score(None, "identity")
        assert score == 0.5
        
        # Missing prompt type
        story = {"title": "Test", "description": "Test"}
        score = scorer.calculate_prompt_alignment_score(story, "")
        assert score == 0.5
    
    def test_keyword_based_alignment(self):
        """Test alignment based on keywords in story content."""
        scorer = StoryDiversityScorer()
        
        # Story with identity keywords
        story = {
            "title": "Family Heritage",
            "description": "Learning about my cultural traditions and background",
            "category": "general"
        }
        score = scorer.calculate_prompt_alignment_score(story, "identity")
        assert score >= 0.5
        
        # Story with challenge keywords  
        story = {
            "title": "Difficult Problem",
            "description": "Overcoming obstacles and solving challenges",
            "category": "general"
        }
        score = scorer.calculate_prompt_alignment_score(story, "challenge")
        assert score >= 0.5


class TestPromptCategorization:
    """Test prompt type categorization."""
    
    def test_identity_prompt(self):
        """Test identity prompt categorization."""
        prompt = "Some students have a background, identity, interest, or talent that is so meaningful they believe their application would be incomplete without it."
        category = _categorize_prompt_type(prompt)
        assert category == "identity"
    
    def test_passion_prompt(self):
        """Test passion prompt categorization."""
        prompt = "Describe a topic, idea, or concept you find so engaging that it makes you lose all track of time."
        category = _categorize_prompt_type(prompt)
        assert category == "passion"
    
    def test_challenge_prompt(self):
        """Test challenge prompt categorization."""
        prompt = "Describe a problem you've solved or would like to solve. It can be an intellectual challenge, a research query, an ethical dilemma."
        category = _categorize_prompt_type(prompt)
        assert category == "challenge"
    
    def test_achievement_prompt(self):
        """Test achievement prompt categorization."""
        prompt = "Describe an accomplishment, event, or realization that sparked a period of personal growth."
        category = _categorize_prompt_type(prompt)
        assert category == "achievement"
    
    def test_community_prompt(self):
        """Test community prompt categorization."""
        prompt = "Discuss an accomplishment that relates to your cultural background, community, or family traditions."
        category = _categorize_prompt_type(prompt)
        assert category == "community"
    
    def test_general_prompt(self):
        """Test general prompt categorization."""
        prompt = "Write about something interesting."
        category = _categorize_prompt_type(prompt)
        assert category == "general"


class TestConvenienceFunctions:
    """Test convenience functions for diversity and alignment scoring."""
    
    def test_story_diversity_score_function(self):
        """Test the story_diversity_score convenience function."""
        results = [
            EssayResult(
                final_draft="Essay 1",
                stories=[{"title": "Story 1", "description": "First story"}]
            ),
            EssayResult(
                final_draft="Essay 2",
                stories=[{"title": "Story 2", "description": "Second story"}]
            )
        ]
        score = story_diversity_score(results, "test_college")
        assert score == 1.0
    
    def test_prompt_alignment_score_function(self):
        """Test the prompt_alignment_score convenience function."""
        story = {
            "title": "Cultural Heritage",
            "description": "Learning about my family's cultural background",
            "category": "identity"
        }
        score = prompt_alignment_score(story, "identity")
        assert score == 1.0


class TestEvaluationIntegration:
    """Test integration of new metrics into evaluation pipeline."""
    
    def test_evaluation_with_diversity_metrics(self):
        """Test evaluation report includes diversity metrics."""
        result = EssayResult(
            final_draft="This is a test essay with exactly fifty words to meet the requirements and demonstrate proper word count validation functionality for the evaluation system.",
            stories=[{"title": "Test Story", "description": "Test description"}],
            outline={"hook": "Test", "context": "Test", "conflict": "Test", "growth": "Test", "reflection": "Test"}
        )
        
        additional_results = [
            EssayResult(
                final_draft="Another test essay",
                stories=[{"title": "Different Story", "description": "Different description"}]
            )
        ]
        
        report = evaluate_essay_result(
            result=result,
            prompt_keywords=["test", "essay"],
            target_word_count=50,
            execution_time=1.0,
            prompt_id="test_prompt",
            prompt_text="Describe a topic you find engaging",
            additional_results=additional_results
        )
        
        assert "story_diversity" in report.metrics
        assert "prompt_alignment" in report.metrics
        assert isinstance(report.metrics["story_diversity"], float)
        assert isinstance(report.metrics["prompt_alignment"], float)
    
    def test_evaluation_without_diversity_metrics(self):
        """Test evaluation report without diversity metrics."""
        result = EssayResult(
            final_draft="This is a test essay with exactly fifty words to meet the requirements and demonstrate proper word count validation functionality for the evaluation system.",
            stories=[{"title": "Test Story", "description": "Test description"}],
            outline={"hook": "Test", "context": "Test", "conflict": "Test", "growth": "Test", "reflection": "Test"}
        )
        
        report = evaluate_essay_result(
            result=result,
            prompt_keywords=["test", "essay"],
            target_word_count=50,
            execution_time=1.0,
            prompt_id="test_prompt"
        )
        
        # Should not have diversity metrics without additional results
        assert "story_diversity" not in report.metrics
        # Should not have alignment metrics without prompt text
        assert "prompt_alignment" not in report.metrics


if __name__ == "__main__":
    pytest.main([__file__]) 