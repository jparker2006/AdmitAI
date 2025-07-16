"""
Unit tests for enhanced QualityMetrics with LLM integration.

Tests both LLM-powered evaluation and legacy heuristic evaluation modes
to ensure backward compatibility and enhanced functionality.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from essay_agent.eval.metrics import QualityMetrics
from essay_agent.eval.llm_evaluator import ConversationEvaluation


class TestQualityMetrics:
    """Test QualityMetrics class with both LLM and legacy modes."""

    def test_legacy_mode_initialization(self):
        """Test that legacy mode initializes correctly."""
        metrics = QualityMetrics(use_legacy=True)
        assert metrics.use_legacy is True
        assert metrics.llm_evaluator is None

    def test_llm_mode_initialization(self):
        """Test that LLM mode initializes correctly."""
        with patch('essay_agent.eval.metrics.LLMEvaluator') as mock_llm:
            metrics = QualityMetrics(use_legacy=False)
            assert metrics.use_legacy is False
            assert metrics.llm_evaluator is not None
            mock_llm.assert_called_once()

    def test_legacy_readability_score(self):
        """Test legacy readability score calculation."""
        metrics = QualityMetrics(use_legacy=True)
        
        # Test with normal text
        text = "This is a simple sentence. This is another simple sentence."
        score = metrics.calculate_readability_score(text)
        assert 0.0 <= score <= 1.0
        
        # Test with empty text
        assert metrics.calculate_readability_score("") == 0.0
        assert metrics.calculate_readability_score(None) == 0.0

    def test_legacy_sentence_variety(self):
        """Test legacy sentence variety calculation."""
        metrics = QualityMetrics(use_legacy=True)
        
        # Test with varied sentences
        text = "Short. This is a medium length sentence. This is a much longer sentence with many words and complexity."
        score = metrics.calculate_sentence_variety(text)
        assert 0.0 <= score <= 1.0
        
        # Test with single sentence
        single_sentence = "This is one sentence."
        assert metrics.calculate_sentence_variety(single_sentence) == 0.0

    def test_legacy_vocabulary_richness(self):
        """Test legacy vocabulary richness calculation."""
        metrics = QualityMetrics(use_legacy=True)
        
        # Test with rich vocabulary
        text = "The magnificent elephant wandered through the verdant forest."
        score = metrics.calculate_vocabulary_richness(text)
        assert 0.0 <= score <= 1.0
        
        # Test with repetitive vocabulary
        repetitive = "The cat sat on the cat mat with the cat."
        score_repetitive = metrics.calculate_vocabulary_richness(repetitive)
        assert score_repetitive < score  # Should be lower than rich text

    def test_legacy_text_evaluation(self):
        """Test legacy text evaluation method."""
        metrics = QualityMetrics(use_legacy=True)
        
        text = "This is a well-written essay with good structure. It demonstrates clear thinking and organization."
        results = metrics._legacy_text_evaluation(text)
        
        expected_keys = {
            "readability_score", "sentence_variety", "vocabulary_richness",
            "overall_quality", "engagement_score", "coherence_score"
        }
        assert set(results.keys()) == expected_keys
        
        # All scores should be between 0 and 1
        for score in results.values():
            assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_llm_text_evaluation_success(self):
        """Test successful LLM text evaluation."""
        # Mock the LLMEvaluator and its response
        mock_evaluation = ConversationEvaluation(
            conversation_id="test",
            overall_quality_score=0.8,
            goal_achievement_score=0.7,
            user_satisfaction_prediction=0.9,
            conversation_flow_score=0.85,
            prompt_response_quality=0.75,
            memory_utilization_effectiveness=0.6,
            tool_usage_appropriateness=0.8
        )
        
        with patch('essay_agent.eval.metrics.LLMEvaluator') as mock_llm_class:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.evaluate_conversation_quality.return_value = mock_evaluation
            mock_llm_class.return_value = mock_llm_instance
            
            metrics = QualityMetrics(use_legacy=False)
            
            text = "This is a well-crafted essay with excellent structure and compelling arguments."
            results = await metrics._llm_text_evaluation(text, {"test": "context"}, "Essay prompt")
            
            # Check that LLM evaluator was called
            mock_llm_instance.evaluate_conversation_quality.assert_called_once()
            
            # Check expected return structure
            expected_keys = {
                "readability_score", "sentence_variety", "vocabulary_richness",
                "overall_quality", "engagement_score", "coherence_score"
            }
            assert set(results.keys()) == expected_keys
            
            # All scores should be between 0 and 1
            for score in results.values():
                assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_llm_text_evaluation_fallback(self):
        """Test that LLM evaluation falls back to legacy on error."""
        with patch('essay_agent.eval.metrics.LLMEvaluator') as mock_llm_class:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.evaluate_conversation_quality.side_effect = Exception("API Error")
            mock_llm_class.return_value = mock_llm_instance
            
            metrics = QualityMetrics(use_legacy=False)
            
            text = "This is a test essay."
            results = await metrics._llm_text_evaluation(text, None, None)
            
            # Should fallback to legacy evaluation
            expected_keys = {
                "readability_score", "sentence_variety", "vocabulary_richness",
                "overall_quality", "engagement_score", "coherence_score"
            }
            assert set(results.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_evaluate_text_quality_legacy_mode(self):
        """Test evaluate_text_quality in legacy mode."""
        metrics = QualityMetrics(use_legacy=True)
        
        text = "This is a well-structured essay with clear arguments and good flow."
        results = await metrics.evaluate_text_quality(text)
        
        # Should use legacy evaluation
        expected_keys = {
            "readability_score", "sentence_variety", "vocabulary_richness",
            "overall_quality", "engagement_score", "coherence_score"
        }
        assert set(results.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_evaluate_text_quality_llm_mode(self):
        """Test evaluate_text_quality in LLM mode."""
        mock_evaluation = ConversationEvaluation(
            conversation_id="test",
            overall_quality_score=0.8,
            goal_achievement_score=0.7,
            user_satisfaction_prediction=0.9,
            conversation_flow_score=0.85,
            prompt_response_quality=0.75,
            memory_utilization_effectiveness=0.6,
            tool_usage_appropriateness=0.8
        )
        
        with patch('essay_agent.eval.metrics.LLMEvaluator') as mock_llm_class:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.evaluate_conversation_quality.return_value = mock_evaluation
            mock_llm_class.return_value = mock_llm_instance
            
            metrics = QualityMetrics(use_legacy=False)
            
            text = "This is a sophisticated essay with nuanced arguments."
            context = {"word_limit": 500}
            prompt = "Write about leadership"
            
            results = await metrics.evaluate_text_quality(text, context, prompt)
            
            expected_keys = {
                "readability_score", "sentence_variety", "vocabulary_richness",
                "overall_quality", "engagement_score", "coherence_score"
            }
            assert set(results.keys()) == expected_keys

    def test_score_conversation_legacy_mode(self):
        """Test score_conversation method in legacy mode."""
        metrics = QualityMetrics(use_legacy=True)
        
        # Test with empty turns
        result = metrics.score_conversation([])
        assert result == {"overall_quality": 0.0}
        
        # Test with mock turns
        mock_turns = [Mock(agent_response="Response 1"), Mock(agent_response="Response 2")]
        result = metrics.score_conversation(mock_turns)
        assert "overall_quality" in result
        assert 0.0 <= result["overall_quality"] <= 1.0

    def test_score_conversation_llm_mode(self):
        """Test score_conversation method in LLM mode."""
        with patch('essay_agent.eval.metrics.LLMEvaluator') as mock_llm_class:
            mock_llm_class.return_value = AsyncMock()
            
            metrics = QualityMetrics(use_legacy=False)
            
            # Test with mock turns
            mock_turns = [Mock(agent_response="Response 1"), Mock(agent_response="Response 2")]
            
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"overall_quality": 0.8}
                result = metrics.score_conversation(mock_turns)
                assert "overall_quality" in result
                mock_run.assert_called_once()

    def test_score_conversation_llm_mode_error_fallback(self):
        """Test score_conversation error handling in LLM mode."""
        with patch('essay_agent.eval.metrics.LLMEvaluator') as mock_llm_class:
            mock_llm_class.return_value = AsyncMock()
            
            metrics = QualityMetrics(use_legacy=False)
            
            mock_turns = [Mock(agent_response="Response 1")]
            
            with patch('asyncio.run', side_effect=Exception("Async error")):
                result = metrics.score_conversation(mock_turns)
                assert result == {"overall_quality": 0.5}  # Fallback value


class TestIntegration:
    """Integration tests for QualityMetrics."""

    def test_mode_consistency(self):
        """Test that mode setting is consistent across methods."""
        legacy_metrics = QualityMetrics(use_legacy=True)
        llm_metrics = QualityMetrics(use_legacy=False)
        
        assert legacy_metrics.use_legacy is True
        assert llm_metrics.use_legacy is False

    @pytest.mark.asyncio
    async def test_text_quality_comparison(self):
        """Test that LLM and legacy modes produce reasonable results."""
        text = "This is a well-written essay with excellent structure and compelling arguments. The author demonstrates clear thinking and provides solid evidence for their claims."
        
        # Test legacy mode
        legacy_metrics = QualityMetrics(use_legacy=True)
        legacy_results = await legacy_metrics.evaluate_text_quality(text)
        
        # Test LLM mode with mocking
        mock_evaluation = ConversationEvaluation(
            conversation_id="test",
            overall_quality_score=0.85,
            goal_achievement_score=0.8,
            user_satisfaction_prediction=0.9,
            conversation_flow_score=0.8,
            prompt_response_quality=0.85,
            memory_utilization_effectiveness=0.7,
            tool_usage_appropriateness=0.8
        )
        
        with patch('essay_agent.eval.metrics.LLMEvaluator') as mock_llm_class:
            mock_llm_instance = AsyncMock()
            mock_llm_instance.evaluate_conversation_quality.return_value = mock_evaluation
            mock_llm_class.return_value = mock_llm_instance
            
            llm_metrics = QualityMetrics(use_legacy=False)
            llm_results = await llm_metrics.evaluate_text_quality(text)
            
            # Both should return valid score structures
            expected_keys = {
                "readability_score", "sentence_variety", "vocabulary_richness",
                "overall_quality", "engagement_score", "coherence_score"
            }
            
            assert set(legacy_results.keys()) == expected_keys
            assert set(llm_results.keys()) == expected_keys
            
            # All scores should be valid
            for results in [legacy_results, llm_results]:
                for score in results.values():
                    assert 0.0 <= score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__]) 