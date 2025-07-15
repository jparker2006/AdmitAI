"""
Unit tests for draft tool error handling and retry logic.

Tests ensure that draft tool properly handles failures, empty responses,
and provides comprehensive debug logging for troubleshooting.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from essay_agent.tools.draft import DraftTool


class TestDraftToolErrorHandling:
    """Test comprehensive error handling in draft tool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.draft_tool = DraftTool()
        self.sample_outline = {
            "hook": "A compelling opening line",
            "context": "Background information",
            "conflict": "The main challenge",
            "growth": "How I overcame it",
            "reflection": "What I learned"
        }
        self.sample_voice_profile = '{"name": "Test User", "grade": 12}'
        self.target_word_count = 500
    
    def test_identity_prompt_success(self):
        """Test that identity prompts can be processed successfully."""
        # Mock successful LLM response
        mock_response = '{"draft": "This is a compelling identity essay about my cultural heritage and family background. It explores how my upbringing shaped my values and worldview. The story begins with a family tradition that has been passed down through generations. Through this experience, I learned the importance of preserving cultural identity while embracing new opportunities. This moment defined my understanding of who I am and where I come from."}'
        
        with patch('essay_agent.llm_client.call_llm') as mock_call_llm:
            mock_call_llm.return_value = mock_response
            
            result = self.draft_tool(
                outline=self.sample_outline,
                voice_profile=self.sample_voice_profile,
                word_count=self.target_word_count
            )
            
            assert result["error"] is None
            assert "draft" in result["ok"]
            assert len(result["ok"]["draft"]) > 0
    
    def test_empty_draft_retry_logic(self):
        """Test retry logic when draft generation returns empty result."""
        # Mock responses: first empty, then successful
        mock_responses = [
            '{"draft": ""}',  # Empty first attempt
            '{"draft": ""}',  # Empty second attempt  
            '{"draft": "This is a successful draft after retry. It contains meaningful content about the student\'s experiences and growth. The story provides insight into character development and personal values. This demonstrates resilience and the ability to overcome challenges through determination and support from family."}',  # Successful third attempt
        ]
        
        with patch('essay_agent.llm_client.call_llm') as mock_call_llm:
            mock_call_llm.side_effect = mock_responses
            
            result = self.draft_tool(
                outline=self.sample_outline,
                voice_profile=self.sample_voice_profile,
                word_count=self.target_word_count
            )
            
            assert result["error"] is None
            assert "draft" in result["ok"]
            assert len(result["ok"]["draft"]) > 0
            assert "successful draft after retry" in result["ok"]["draft"]
    
    def test_complete_failure_after_retries(self):
        """Test behavior when all retry attempts fail."""
        # Mock all attempts to return empty drafts
        mock_responses = ['{"draft": ""}'] * 5  # More than max_retries
        
        with patch('essay_agent.llm_client.call_llm') as mock_call_llm:
            mock_call_llm.side_effect = mock_responses
            
            result = self.draft_tool(
                outline=self.sample_outline,
                voice_profile=self.sample_voice_profile,
                word_count=self.target_word_count
            )
            
            assert result["error"] is not None
            assert "Failed to generate" in result["error"]["message"]
    
    def test_json_parse_error_handling(self):
        """Test handling of malformed JSON responses."""
        mock_responses = [
            'invalid json response',  # Invalid JSON
            '{"draft": "This is a valid response after JSON error handling. The tool successfully recovered from the parsing error and generated a complete essay. This demonstrates the robustness of the error handling system in place."}',  # Valid response
        ]
        
        with patch('essay_agent.llm_client.call_llm') as mock_call_llm:
            mock_call_llm.side_effect = mock_responses
            
            result = self.draft_tool(
                outline=self.sample_outline,
                voice_profile=self.sample_voice_profile,
                word_count=self.target_word_count
            )
            
            assert result["error"] is None
            assert "draft" in result["ok"]
            assert "valid response after JSON error" in result["ok"]["draft"]
    
    def test_outline_validation(self):
        """Test that outline validation works correctly."""
        # Test with invalid outline
        invalid_outline = ""
        
        result = self.draft_tool(
            outline=invalid_outline,
            voice_profile=self.sample_voice_profile,
            word_count=self.target_word_count
        )
        
        assert result["error"] is not None
        assert "outline must not be empty" in result["error"]["message"]
    
    def test_voice_profile_validation(self):
        """Test that voice profile validation works correctly."""
        # Test with empty voice profile
        result = self.draft_tool(
            outline=self.sample_outline,
            voice_profile="",
            word_count=self.target_word_count
        )
        
        assert result["error"] is not None
        assert "voice_profile must not be empty" in result["error"]["message"]
    
    def test_word_count_range_validation(self):
        """Test word count range validation."""
        # Test with invalid word count (too low)
        result = self.draft_tool(
            outline=self.sample_outline,
            voice_profile=self.sample_voice_profile,
            word_count=5  # Below minimum
        )
        
        assert result["error"] is not None
        assert "word_count must be between 10 and 1000" in result["error"]["message"]
        
        # Test with invalid word count (too high)
        result = self.draft_tool(
            outline=self.sample_outline,
            voice_profile=self.sample_voice_profile,
            word_count=1500  # Above maximum
        )
        
        assert result["error"] is not None
        assert "word_count must be between 10 and 1000" in result["error"]["message"]
    
    def test_upstream_tool_failure_handling(self):
        """Test handling of upstream tool failures."""
        # Test with failed outline tool result
        failed_outline = {"error": {"message": "Outline generation failed", "type": "ValueError"}}
        
        result = self.draft_tool(
            outline=failed_outline,
            voice_profile=self.sample_voice_profile,
            word_count=self.target_word_count
        )
        
        assert result["error"] is not None
        assert "upstream outline tool failed" in result["error"]["message"]


class TestWordCountIntegration:
    """Test integration with word count validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.draft_tool = DraftTool()
    
    def test_word_count_tool_initialization(self):
        """Test that word count tool is properly initialized."""
        assert hasattr(self.draft_tool, 'word_count_tool')
        # The word count tool is created dynamically, so we just check it exists
        word_count_tool = self.draft_tool.word_count_tool
        assert word_count_tool is not None 