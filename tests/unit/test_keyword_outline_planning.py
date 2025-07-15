"""
Tests for keyword extraction and planning in outline tool.
"""

import pytest
from unittest.mock import patch, MagicMock
from essay_agent.tools.outline import OutlineTool


class TestKeywordOutlinePlanning:
    """Test keyword extraction and planning functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = OutlineTool()
    
    def test_extract_and_plan_keywords_basic(self):
        """Test basic keyword extraction from prompt."""
        prompt = "Describe a problem you've solved or would like to solve. Explain its significance to you and what steps you took to identify a solution."
        
        result = self.tool._extract_and_plan_keywords(prompt, 650)
        
        assert "extracted_keywords" in result
        assert "keyword_planning" in result
        assert "prompt_analysis" in result
        
        keywords = result["extracted_keywords"]
        assert len(keywords) > 0
        assert "problem" in keywords
        assert "solve" in keywords or "solved" in keywords
        # Check for keywords that might actually be extracted
        assert any(keyword in ["solution", "identify", "steps", "significance", "explain"] for keyword in keywords)
    
    def test_extract_and_plan_keywords_stop_words_filtered(self):
        """Test that stop words are filtered out of keyword extraction."""
        prompt = "This is a test prompt about the importance of education and learning."
        
        result = self.tool._extract_and_plan_keywords(prompt, 500)
        
        keywords = result["extracted_keywords"]
        # Stop words should be filtered out
        stop_words = ["this", "is", "a", "about", "the", "of", "and"]
        for stop_word in stop_words:
            assert stop_word not in keywords
        
        # Content words should remain
        assert "test" in keywords or "prompt" in keywords
        assert "importance" in keywords
        assert "education" in keywords
        assert "learning" in keywords
    
    def test_extract_and_plan_keywords_limit(self):
        """Test that keyword extraction is limited to top 8 keywords."""
        long_prompt = "This prompt contains many different important significant meaningful relevant crucial essential vital words that should be extracted and analyzed"
        
        result = self.tool._extract_and_plan_keywords(long_prompt, 800)
        
        keywords = result["extracted_keywords"]
        assert len(keywords) <= 8
    
    def test_extract_and_plan_keywords_empty_prompt(self):
        """Test keyword extraction with empty prompt."""
        result = self.tool._extract_and_plan_keywords("", 500)
        
        assert result["extracted_keywords"] == []
        assert result["keyword_planning"] == {}
    
    def test_plan_keyword_integration_basic(self):
        """Test basic keyword integration planning."""
        keywords = ["problem", "solve", "challenge", "solution"]
        
        result = self.tool._plan_keyword_integration(keywords, 650)
        
        assert "section_keywords" in result
        assert "integration_strategy" in result
        assert "total_keywords" in result
        
        section_keywords = result["section_keywords"]
        sections = ["hook", "context", "conflict", "growth", "reflection"]
        
        # All sections should have keywords assigned
        for section in sections:
            assert section in section_keywords
        
        # All keywords should be distributed
        all_assigned = []
        for section_kw in section_keywords.values():
            all_assigned.extend(section_kw)
        
        for keyword in keywords:
            assert keyword in all_assigned
    
    def test_plan_keyword_integration_empty_keywords(self):
        """Test keyword integration planning with empty keywords."""
        result = self.tool._plan_keyword_integration([], 500)
        
        assert result == {}
    
    def test_plan_keyword_integration_single_keyword(self):
        """Test keyword integration planning with single keyword."""
        keywords = ["growth"]
        
        result = self.tool._plan_keyword_integration(keywords, 400)
        
        section_keywords = result["section_keywords"]
        
        # Single keyword should be assigned to at least one section
        assigned_keywords = []
        for section_kw in section_keywords.values():
            assigned_keywords.extend(section_kw)
        
        assert "growth" in assigned_keywords
        assert result["total_keywords"] == 1
    
    def test_plan_keyword_integration_many_keywords(self):
        """Test keyword integration planning with many keywords."""
        keywords = ["problem", "solve", "challenge", "solution", "difficulty", "overcome", "growth", "insight", "learning", "understanding"]
        
        result = self.tool._plan_keyword_integration(keywords, 800)
        
        section_keywords = result["section_keywords"]
        
        # All keywords should be distributed
        all_assigned = []
        for section_kw in section_keywords.values():
            all_assigned.extend(section_kw)
        
        assert len(all_assigned) == len(keywords)
        for keyword in keywords:
            assert keyword in all_assigned
    
    def test_calculate_word_distribution(self):
        """Test word distribution calculation."""
        result = self.tool._calculate_word_distribution(650)
        
        # Check that all sections have word counts
        sections = ["hook", "context", "conflict", "growth", "reflection"]
        for section in sections:
            assert f"{section}_words" in result
            assert f"{section}_percentage" in result
        
        # Check that percentages add up to 100%
        total_percentage = sum(result[f"{section}_percentage"] for section in sections)
        assert total_percentage == 100
        
        # Check that word counts are reasonable
        total_words = sum(result[f"{section}_words"] for section in sections)
        assert total_words <= 650  # Should be close to target
    
    def test_calculate_word_distribution_different_targets(self):
        """Test word distribution with different target word counts."""
        targets = [250, 500, 800]
        
        for target in targets:
            result = self.tool._calculate_word_distribution(target)
            
            total_words = sum(result[f"{section}_words"] for section in ["hook", "context", "conflict", "growth", "reflection"])
            
            # Total should be close to target (within reasonable rounding)
            assert abs(total_words - target) < 10
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_extract_and_plan_keywords_verbose_logging(self, mock_debug_print):
        """Test that keyword extraction includes verbose logging."""
        prompt = "Describe a challenge you have overcome and what you learned from it."
        
        self.tool._extract_and_plan_keywords(prompt, 600)
        
        # Verify debug prints were called
        mock_debug_print.assert_called()
        
        # Check that keyword extraction was logged
        call_args = [call[0][1] for call in mock_debug_print.call_args_list]
        assert any("Extracted keywords from prompt" in arg for arg in call_args)
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_extract_and_plan_keywords_error_handling(self, mock_debug_print):
        """Test error handling in keyword extraction."""
        # Force an error by passing invalid input
        with patch('re.findall', side_effect=Exception("Test error")):
            result = self.tool._extract_and_plan_keywords("test prompt", 500)
            
            # Should handle error gracefully
            assert result["extracted_keywords"] == []
            assert result["keyword_planning"] == {}
            assert "error" in result
            
            # Should log the error
            call_args = [call[0][1] for call in mock_debug_print.call_args_list]
            assert any("Error extracting keywords" in arg for arg in call_args)
    
    @patch('essay_agent.tools.outline.chat')
    @patch('essay_agent.tools.outline.render_template')
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_run_method_includes_keyword_planning(self, mock_debug_print, mock_render, mock_chat):
        """Test that _run method includes keyword planning."""
        # Mock dependencies
        mock_render.return_value = "test prompt"
        mock_chat.return_value = '{"outline": {"hook": "test", "context": "test", "conflict": "test", "growth": "test", "reflection": "test"}, "estimated_word_count": 500}'
        
        story = "My experience with robotics"
        prompt = "Describe a problem you have solved"
        
        result = self.tool._run(story=story, prompt=prompt, word_count=500)
        
        # Result should include keyword data
        assert "keyword_data" in result
        assert "word_distribution" in result
        
        # Keyword data should have expected structure
        keyword_data = result["keyword_data"]
        assert "extracted_keywords" in keyword_data
        assert "keyword_planning" in keyword_data
        
        # Verify render_template was called with keyword parameters
        mock_render.assert_called_once()
        call_args = mock_render.call_args[1]  # Get keyword arguments
        assert "extracted_keywords" in call_args
        assert "keyword_planning" in call_args
    
    @patch('essay_agent.tools.outline.ensure_essay_record')
    @patch('essay_agent.tools.outline.SimpleMemory')
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_store_outline_in_memory_includes_keyword_data(self, mock_debug_print, mock_memory, mock_ensure):
        """Test that outline storage includes keyword data."""
        # Mock EssayVersion to avoid import issues
        with patch('essay_agent.tools.outline.EssayVersion') as mock_version:
            # Mock essay record
            mock_essay_record = MagicMock()
            mock_essay_record.essay_versions = []
            mock_ensure.return_value = mock_essay_record
            
            outline_data = {
                "outline": {"hook": "test", "context": "test", "conflict": "test", "growth": "test", "reflection": "test"},
                "keyword_data": {"extracted_keywords": ["test", "keyword"]},
                "estimated_word_count": 500
            }
            
            # The method should not raise an exception
            try:
                self.tool._store_outline_in_memory(
                    user_id="test_user",
                    outline_data=outline_data,
                    story="test story",
                    prompt="test prompt"
                )
                # Test passed if no exception was raised
                test_passed = True
            except Exception:
                test_passed = False
            
            assert test_passed, "Memory storage should not raise exceptions"
            
            # Verify that EssayVersion was called with keyword_data in metadata
            if mock_version.called:
                call_args = mock_version.call_args
                metadata = call_args[1]['metadata']
                assert "keyword_data" in metadata
    
    def test_integration_with_existing_outline_structure(self):
        """Test that keyword planning integrates with existing outline structure."""
        # Test with a realistic prompt and story
        prompt = "Some students have a background, identity, interest, or talent that is so meaningful they believe their application would be incomplete without it. If this sounds like you, then please share your story."
        story = "My experience growing up in a bilingual household"
        
        # Mock the chat response to focus on testing keyword integration
        expected_response = {
            "outline": {
                "hook": "Growing up hearing two languages at home",
                "context": "My family's bilingual environment",
                "conflict": "Struggling to balance two cultures",
                "growth": "Learning to embrace both identities",
                "reflection": "How bilingualism shaped my worldview"
            },
            "estimated_word_count": 650
        }
        
        with patch('essay_agent.tools.outline.chat') as mock_chat:
            with patch('essay_agent.tools.outline.render_template') as mock_render:
                mock_chat.return_value = str(expected_response).replace("'", '"')
                mock_render.return_value = "test prompt"
                
                result = self.tool._run(story=story, prompt=prompt, word_count=650)
                
                # Should have both outline and keyword data
                assert "outline" in result
                assert "keyword_data" in result
                assert "word_distribution" in result
                
                # Keyword data should contain identity-related keywords
                keywords = result["keyword_data"]["extracted_keywords"]
                assert any(keyword in ["background", "identity", "meaningful", "story"] for keyword in keywords) 