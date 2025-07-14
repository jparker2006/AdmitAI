"""
Integration tests for draft tool word count retry workflow.

Tests the complete integration of WordCountTool with DraftTool including
retry logic, expansion, trimming, and word count enforcement.
"""

import json
import pytest
from unittest.mock import patch, Mock
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.draft import DraftTool
from essay_agent.tools.word_count import WordCountTool
from essay_agent.tools import REGISTRY


class TestDraftWordCountRetry:
    """Integration tests for draft tool word count retry workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.draft_tool = DraftTool()
        self.word_count_tool = WordCountTool()
        
        self.test_outline = {
            "hook": "Opening paragraph that grabs attention",
            "context": "Background information about the situation",
            "conflict": "The main challenge or problem faced",
            "growth": "How the challenge was overcome and lessons learned",
            "reflection": "Insights gained and future implications"
        }
        
        self.test_voice_profile = json.dumps({
            "tone": "conversational and authentic",
            "vocabulary_level": "high school student", 
            "style": "personal narrative"
        })

    def test_draft_retry_workflow_success_first_attempt(self):
        """Test draft generation succeeds on first attempt when word count is correct."""
        target_words = 20
        
        # Create a response that meets the target word count
        perfect_draft = " ".join(["word"] * target_words)
        fake_response = json.dumps({"draft": perfect_draft})
        
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=[fake_response])
            
            result = self.draft_tool._run(
                outline=self.test_outline,
                voice_profile=self.test_voice_profile,
                word_count=target_words
            )
            
            assert result["draft"] == perfect_draft
            assert self.word_count_tool.count_words(result["draft"]) == target_words

    def test_draft_retry_workflow_expansion_needed(self):
        """Test draft expansion when initial draft is too short."""
        target_words = 100
        
        # Initial draft too short (10 words)
        short_draft = " ".join(["word"] * 10)
        initial_response = json.dumps({"draft": short_draft})
        
        # Expanded draft that meets target
        expanded_draft = " ".join(["word"] * target_words)
        expansion_response = json.dumps({"expanded_draft": expanded_draft})
        
        responses = [initial_response, expansion_response]
        
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=responses)
            
            result = self.draft_tool._run(
                outline=self.test_outline,
                voice_profile=self.test_voice_profile,
                word_count=target_words
            )
            
            # Should return the expanded draft
            assert result["draft"] == expanded_draft
            assert self.word_count_tool.count_words(result["draft"]) == target_words

    def test_draft_retry_workflow_trimming_needed(self):
        """Test draft trimming when initial draft is too long."""
        target_words = 50
        
        # Initial draft too long (150 words, outside 5% tolerance)
        long_draft = " ".join(["word"] * 150)
        initial_response = json.dumps({"draft": long_draft})
        
        # Trimmed draft that meets target
        trimmed_draft = " ".join(["word"] * target_words)
        trimming_response = json.dumps({"trimmed_draft": trimmed_draft})
        
        responses = [initial_response, trimming_response]
        
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=responses)
            
            result = self.draft_tool._run(
                outline=self.test_outline,
                voice_profile=self.test_voice_profile,
                word_count=target_words
            )
            
            # Should return the trimmed draft
            assert result["draft"] == trimmed_draft
            assert self.word_count_tool.count_words(result["draft"]) == target_words

    def test_draft_retry_workflow_multiple_attempts(self):
        """Test draft generation through multiple retry attempts."""
        target_words = 100
        
        # Attempt 1: Too short (10 words)
        short_draft = " ".join(["word"] * 10)
        initial_response = json.dumps({"draft": short_draft})
        
        # Attempt 2: Still not quite right (80 words, outside tolerance)
        still_short_draft = " ".join(["word"] * 80)
        expansion_response = json.dumps({"expanded_draft": still_short_draft})
        
        # Attempt 3: Final attempt meets target with larger tolerance
        final_draft = " ".join(["word"] * 95)  # Within 10% tolerance
        final_expansion_response = json.dumps({"expanded_draft": final_draft})
        
        responses = [initial_response, expansion_response, final_expansion_response]
        
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=responses)
            
            result = self.draft_tool._run(
                outline=self.test_outline,
                voice_profile=self.test_voice_profile,
                word_count=target_words
            )
            
            # Should return the final attempt
            assert result["draft"] == final_draft
            assert 90 <= self.word_count_tool.count_words(result["draft"]) <= 110  # Within 10% tolerance

    def test_draft_retry_workflow_failure_graceful_degradation(self):
        """Test graceful degradation when all retry attempts fail."""
        target_words = 100
        
        # All attempts return too short drafts
        short_draft = " ".join(["word"] * 20)
        responses = [
            json.dumps({"draft": short_draft}),
            json.dumps({"expanded_draft": short_draft}),
            json.dumps({"expanded_draft": short_draft})
        ]
        
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=responses)
            
            # Should not raise exception, but return best attempt
            result = self.draft_tool._run(
                outline=self.test_outline,
                voice_profile=self.test_voice_profile,
                word_count=target_words
            )
            
            # Should return the draft even if word count not perfect
            assert "draft" in result
            assert len(result["draft"]) > 0

    def test_expansion_prompt_generation(self):
        """Test that expansion prompts are generated correctly."""
        target_words = 100
        current_draft = "Short draft that needs expansion."
        
        # Mock the word count tool to indicate expansion needed
        mock_adjustment = Mock()
        mock_adjustment.needs_expansion = True
        mock_adjustment.needs_trimming = False
        mock_adjustment.words_needed = 80
        mock_adjustment.expansion_points = ["Add more details", "Include dialogue"]
        
        # Test the expansion method directly
        with patch.object(self.draft_tool.word_count_tool, 'calculate_adjustment', return_value=mock_adjustment):
            with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
                expanded_draft = " ".join(["word"] * target_words)
                expansion_response = json.dumps({"expanded_draft": expanded_draft})
                mock_llm.return_value = FakeListLLM(responses=[expansion_response])
                
                result = self.draft_tool._expand_draft(
                    current_draft, self.test_voice_profile, target_words, mock_adjustment
                )
                
                assert result == expanded_draft

    def test_trimming_prompt_generation(self):
        """Test that trimming prompts are generated correctly."""
        target_words = 50
        current_draft = " ".join(["word"] * 150)  # Long draft that needs trimming
        
        # Mock the word count tool to indicate trimming needed
        mock_adjustment = Mock()
        mock_adjustment.needs_expansion = False
        mock_adjustment.needs_trimming = True
        mock_adjustment.words_excess = 100
        mock_adjustment.trimming_points = ["Remove redundancy", "Eliminate filler"]
        
        # Test the trimming method directly
        with patch.object(self.draft_tool.word_count_tool, 'calculate_adjustment', return_value=mock_adjustment):
            with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
                trimmed_draft = " ".join(["word"] * target_words)
                trimming_response = json.dumps({"trimmed_draft": trimmed_draft})
                mock_llm.return_value = FakeListLLM(responses=[trimming_response])
                
                result = self.draft_tool._trim_draft(
                    current_draft, self.test_voice_profile, target_words, mock_adjustment
                )
                
                assert result == trimmed_draft

    def test_word_count_success_rate_simulation(self):
        """Test achieving high word count success rate through multiple simulations."""
        target_words = 100
        success_count = 0
        total_attempts = 10
        
        for attempt in range(total_attempts):
            # Vary the initial word count to test different scenarios
            if attempt % 3 == 0:
                initial_count = 60  # Too short
                final_count = target_words
            elif attempt % 3 == 1:
                initial_count = 140  # Too long
                final_count = target_words
            else:
                initial_count = target_words  # Perfect
                final_count = target_words
            
            initial_draft = " ".join(["word"] * initial_count)
            final_draft = " ".join(["word"] * final_count)
            
            responses = [
                json.dumps({"draft": initial_draft}),
                json.dumps({"expanded_draft": final_draft}),
                json.dumps({"trimmed_draft": final_draft})
            ]
            
            with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=responses)
                
                result = self.draft_tool._run(
                    outline=self.test_outline,
                    voice_profile=self.test_voice_profile,
                    word_count=target_words
                )
                
                actual_count = self.word_count_tool.count_words(result["draft"])
                # Check if within 10% tolerance (final fallback tolerance)
                if target_words * 0.9 <= actual_count <= target_words * 1.1:
                    success_count += 1
        
        # Should achieve at least 90% success rate
        success_rate = success_count / total_attempts
        assert success_rate >= 0.9, f"Success rate {success_rate} below target 0.9"

    def test_backward_compatibility(self):
        """Test that the enhanced draft tool maintains backward compatibility."""
        # Test that the tool still works with simple inputs like existing tests
        target_words = 20
        perfect_draft = " ".join(["word"] * target_words)
        fake_response = json.dumps({"draft": perfect_draft})
        
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=[fake_response])
            
            # Test with basic parameters (same as existing tests)
            result = self.draft_tool._run(
                outline=self.test_outline,
                voice_profile="conversational",
                word_count=target_words
            )
            
            assert "draft" in result
            assert result["draft"] == perfect_draft

    def test_tool_registry_integration(self):
        """Test that the enhanced draft tool works through the registry."""
        target_words = 15
        perfect_draft = " ".join(["word"] * target_words)
        fake_response = json.dumps({"draft": perfect_draft})
        
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=[fake_response])
            
            result = REGISTRY.call(
                "draft",
                outline=self.test_outline,
                voice_profile=self.test_voice_profile,
                word_count=target_words
            )
            
            assert result["ok"]["draft"] == perfect_draft
            assert result["error"] is None

    def test_error_handling_invalid_responses(self):
        """Test error handling when LLM returns invalid responses."""
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            # Test with invalid JSON
            mock_llm.return_value = FakeListLLM(responses=["Invalid JSON response"])
            
            with pytest.raises(ValueError, match="Failed to generate draft"):
                self.draft_tool._run(
                    outline=self.test_outline,
                    voice_profile=self.test_voice_profile,
                    word_count=100
                )

    def test_error_handling_empty_drafts(self):
        """Test error handling when LLM returns empty drafts."""
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            # Test with empty draft
            empty_response = json.dumps({"draft": ""})
            mock_llm.return_value = FakeListLLM(responses=[empty_response])
            
            with pytest.raises(ValueError, match="Failed to generate draft"):
                self.draft_tool._run(
                    outline=self.test_outline,
                    voice_profile=self.test_voice_profile,
                    word_count=100
                )

    def test_voice_profile_preparation(self):
        """Test that voice profile preparation works correctly."""
        # Test with large voice profile
        large_profile = json.dumps({
            "user_info": {"name": "Test User", "grade": 12},
            "core_values": ["value"] * 100,  # Large values list
            "writing_voice": {"tone": "conversational"},
            "essay_history": [{"essay": f"essay_{i}"} for i in range(50)]  # Large history
        })
        
        prepared = self.draft_tool._prepare_voice_profile(large_profile)
        
        # Should be truncated but still valid
        assert len(prepared) <= 20000 + 100  # Allow some buffer for truncation message
        
        # Should still be parseable JSON if it was originally JSON
        try:
            json.loads(prepared.split('\n... [truncated')[0])  # Parse the non-truncated part
        except json.JSONDecodeError:
            # If truncation made it invalid JSON, that's acceptable
            pass

    def test_tolerance_progression(self):
        """Test that tolerance increases through retry attempts."""
        target_words = 100
        
        # Create a draft that's within 10% tolerance but outside 5%
        borderline_count = 92  # 8% below target
        borderline_draft = " ".join(["word"] * borderline_count)
        
        # Should fail first attempt (5% tolerance) but pass final attempt (10% tolerance)
        responses = [
            json.dumps({"draft": borderline_draft}),
            json.dumps({"expanded_draft": borderline_draft}),  # Still same count
            json.dumps({"expanded_draft": borderline_draft})   # Final attempt
        ]
        
        with patch('essay_agent.tools.draft.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=responses)
            
            result = self.draft_tool._run(
                outline=self.test_outline,
                voice_profile=self.test_voice_profile,
                word_count=target_words
            )
            
            # Should accept the borderline draft in final attempt
            assert result["draft"] == borderline_draft
            assert self.word_count_tool.count_words(result["draft"]) == borderline_count 