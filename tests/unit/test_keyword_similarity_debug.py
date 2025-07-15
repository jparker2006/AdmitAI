"""
Tests for enhanced keyword similarity debugging functionality.
"""

import pytest
from essay_agent.eval.metrics import KeywordSimilarityScorer


class TestKeywordSimilarityDebug:
    """Test the keyword_similarity_debug method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = KeywordSimilarityScorer()
    
    def test_keyword_similarity_debug_empty_essay(self):
        """Test keyword debugging with empty essay text."""
        keywords = ["problem", "solve", "challenge"]
        result = self.scorer.keyword_similarity_debug("", keywords)
        
        assert result["matched_keywords"] == []
        assert result["missing_keywords"] == keywords
        assert result["partial_matches"] == []
        assert result["similarity_score"] == 0.0
        assert "Essay text is empty" in result["recommendations"][0]
    
    def test_keyword_similarity_debug_no_keywords(self):
        """Test keyword debugging with no keywords specified."""
        essay_text = "This is a sample essay about robotics and problem solving."
        result = self.scorer.keyword_similarity_debug(essay_text, [])
        
        assert result["matched_keywords"] == []
        assert result["missing_keywords"] == []
        assert result["partial_matches"] == []
        assert result["similarity_score"] == 1.0
        assert "No keywords specified" in result["recommendations"][0]
    
    def test_keyword_similarity_debug_perfect_match(self):
        """Test keyword debugging with all keywords matched."""
        essay_text = "I faced a significant problem in robotics class. I had to solve the challenge by working through the solution step by step."
        keywords = ["problem", "solve", "challenge", "solution"]
        result = self.scorer.keyword_similarity_debug(essay_text, keywords)
        
        assert len(result["matched_keywords"]) == 4
        assert result["missing_keywords"] == []
        assert result["similarity_score"] == 1.0
        assert "Good keyword coverage" in result["recommendations"][0]
    
    def test_keyword_similarity_debug_partial_matches(self):
        """Test keyword debugging with partial keyword matches."""
        essay_text = "The challenging situation required problem-solving skills."
        keywords = ["challenge", "problem", "solve"]
        result = self.scorer.keyword_similarity_debug(essay_text, keywords)
        
        # Since our tokenizer splits on word boundaries, "challenging" will be a full match for "challenge"
        # "problem-solving" will be tokenized as "problem" and "solving", so we should get matches
        assert result["similarity_score"] > 0.0
        assert len(result["matched_keywords"]) > 0 or len(result["partial_matches"]) > 0
        # Check that we found some form of match for the keywords
        all_found = result["matched_keywords"] + [pm.split(" ")[0] for pm in result["partial_matches"]]
        assert any(keyword in all_found for keyword in keywords)
    
    def test_keyword_similarity_debug_missing_keywords(self):
        """Test keyword debugging with missing keywords."""
        essay_text = "This essay is about my experiences in high school."
        keywords = ["problem", "solve", "challenge", "solution"]
        result = self.scorer.keyword_similarity_debug(essay_text, keywords)
        
        assert result["missing_keywords"] == keywords
        assert result["similarity_score"] == 0.0
        assert "Consider incorporating these missing keywords" in result["recommendations"][0]
    
    def test_keyword_similarity_debug_analysis_details(self):
        """Test that analysis details are properly populated."""
        essay_text = "I solved a difficult problem through perseverance."
        keywords = ["problem", "solve", "challenge"]
        result = self.scorer.keyword_similarity_debug(essay_text, keywords)
        
        details = result["analysis_details"]
        assert details["total_keywords"] == 3
        assert details["essay_word_count"] > 0
        assert details["full_matches"] >= 0
        assert details["partial_matches"] >= 0
    
    def test_keyword_similarity_debug_recommendations(self):
        """Test that appropriate recommendations are generated."""
        essay_text = "This is a short essay."
        keywords = ["problem", "solve", "challenge", "solution"]
        result = self.scorer.keyword_similarity_debug(essay_text, keywords)
        
        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        assert any("missing keywords" in rec for rec in recommendations)
        assert any("stronger connection" in rec for rec in recommendations)


class TestPromptAlignmentDetailed:
    """Test the prompt_alignment_detailed method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = KeywordSimilarityScorer()
    
    def test_prompt_alignment_detailed_empty_story(self):
        """Test prompt alignment with empty story."""
        result = self.scorer.prompt_alignment_detailed({}, "identity")
        
        assert result["prompt_category"] == "identity"
        assert result["story_themes"] == []
        assert result["alignment_score"] == 0.0
        assert "No story provided" in result["alignment_reasons"]
        assert "Select a story that matches" in result["improvement_suggestions"][0]
    
    def test_prompt_alignment_detailed_identity_story(self):
        """Test prompt alignment for identity story."""
        story = {
            "title": "My Cultural Heritage",
            "description": "Growing up in a multicultural family shaped my identity",
            "themes": ["heritage", "culture", "family"],
            "insights": ["I learned to appreciate different perspectives"]
        }
        result = self.scorer.prompt_alignment_detailed(story, "identity")
        
        assert result["prompt_category"] == "identity"
        assert result["alignment_score"] > 0.0
        assert len(result["alignment_reasons"]) > 0
        assert "Story themes match prompt type" in result["alignment_reasons"][0]
    
    def test_prompt_alignment_detailed_challenge_story(self):
        """Test prompt alignment for challenge story."""
        story = {
            "title": "Overcoming Adversity",
            "description": "I faced a significant obstacle in my project",
            "themes": ["obstacle", "difficulty", "perseverance"],
            "insights": ["I learned that failure leads to growth"]
        }
        result = self.scorer.prompt_alignment_detailed(story, "challenge")
        
        assert result["prompt_category"] == "challenge"
        assert result["alignment_score"] > 0.0
        assert any("obstacle" in reason for reason in result["alignment_reasons"])
    
    def test_prompt_alignment_detailed_mismatched_story(self):
        """Test prompt alignment with mismatched story type."""
        story = {
            "title": "Robotics Competition",
            "description": "I built a robot for the competition",
            "themes": ["technology", "engineering"],
            "insights": ["I learned programming skills"]
        }
        result = self.scorer.prompt_alignment_detailed(story, "identity")
        
        assert result["alignment_score"] < 0.5
        assert len(result["improvement_suggestions"]) > 0
        # Check that some improvement suggestion is provided (exact text may vary)
        assert any("identity" in suggestion for suggestion in result["improvement_suggestions"])
    
    def test_prompt_alignment_detailed_analysis_details(self):
        """Test that analysis details are properly populated."""
        story = {
            "title": "Community Service",
            "description": "I volunteered at the local shelter",
            "themes": ["service", "community"],
            "insights": ["I realized the importance of helping others"]
        }
        result = self.scorer.prompt_alignment_detailed(story, "community")
        
        details = result["analysis_details"]
        assert "expected_themes" in details
        assert "story_title" in details
        assert "has_insights" in details
        assert details["has_insights"] == True
    
    def test_prompt_alignment_detailed_passion_story(self):
        """Test prompt alignment for passion story."""
        story = {
            "title": "My Love for Creative Writing",
            "description": "Writing captivates me and makes me lose track of time",
            "themes": ["creative", "artistic", "hobby"],
            "insights": ["I discovered my intellectual curiosity through writing"]
        }
        result = self.scorer.prompt_alignment_detailed(story, "passion")
        
        assert result["prompt_category"] == "passion"
        assert result["alignment_score"] > 0.5
        assert any("creative" in reason for reason in result["alignment_reasons"])
    
    def test_prompt_alignment_detailed_achievement_story(self):
        """Test prompt alignment for achievement story."""
        story = {
            "title": "Winning the Science Fair",
            "description": "My project won first place at the regional competition",
            "themes": ["accomplishment", "success", "recognition"],
            "insights": ["I grew to understand the value of perseverance"]
        }
        result = self.scorer.prompt_alignment_detailed(story, "achievement")
        
        assert result["prompt_category"] == "achievement"
        assert result["alignment_score"] > 0.5
        assert any("growth" in reason for reason in result["alignment_reasons"])
    
    def test_prompt_alignment_detailed_unknown_prompt_type(self):
        """Test prompt alignment with unknown prompt type."""
        story = {
            "title": "Test Story",
            "description": "A test story",
            "themes": ["test"],
            "insights": ["Test insight"]
        }
        result = self.scorer.prompt_alignment_detailed(story, "unknown_type")
        
        assert result["prompt_category"] == "unknown_type"
        assert result["alignment_score"] >= 0.0
        # Should still work with empty expected themes
        assert "expected_themes" in result["analysis_details"]


class TestKeywordSimilarityScorer:
    """Test the enhanced KeywordSimilarityScorer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = KeywordSimilarityScorer()
    
    def test_existing_score_method_unchanged(self):
        """Test that existing score method still works as expected."""
        essay_text = "I faced a problem and found a solution through careful analysis."
        keywords = ["problem", "solution", "analysis"]
        score = self.scorer.score(essay_text, keywords)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should have good coverage
    
    def test_scorer_initialization(self):
        """Test that scorer can be initialized with custom parameters."""
        custom_scorer = KeywordSimilarityScorer(k1=1.5, b=0.8)
        assert custom_scorer.k1 == 1.5
        assert custom_scorer.b == 0.8
    
    def test_tokenization_consistency(self):
        """Test that tokenization is consistent across methods."""
        essay_text = "This is a test essay with various words."
        keywords = ["test", "essay", "words"]
        
        # Test both methods use same tokenization
        score = self.scorer.score(essay_text, keywords)
        debug_result = self.scorer.keyword_similarity_debug(essay_text, keywords)
        
        # Both should identify the same keywords
        assert score > 0.0
        assert debug_result["similarity_score"] > 0.0
        assert len(debug_result["matched_keywords"]) > 0 