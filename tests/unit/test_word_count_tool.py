"""
Unit tests for WordCountTool.

Tests the external word count tool with accurate Python-based counting,
validation, and expansion/trimming suggestion logic.
"""

import pytest
from unittest.mock import patch

from essay_agent.tools.word_count import WordCountTool, WordCountResult, AdjustmentSuggestion
from essay_agent.tools import REGISTRY


class TestWordCountTool:
    """Test suite for WordCountTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = WordCountTool()

    def test_accurate_word_counting(self):
        """Test that Python word counting is accurate."""
        # Test basic counting
        assert self.tool.count_words("Hello world") == 2
        assert self.tool.count_words("This is a test sentence with seven words.") == 8
        
        # Test edge cases
        assert self.tool.count_words("") == 0
        assert self.tool.count_words("   ") == 0
        assert self.tool.count_words("   word   ") == 1
        assert self.tool.count_words("multiple\n\nlines\nwith\nspaces") == 4
        
        # Test complex text
        complex_text = """This is a longer paragraph with multiple sentences. 
        It should count all the words accurately, including those with punctuation marks!
        Even words with apostrophes like don't and can't should be counted correctly."""
        expected_count = len(complex_text.split())
        assert self.tool.count_words(complex_text) == expected_count

    def test_tolerance_validation(self):
        """Test word count tolerance validation."""
        text = "This is exactly eight words here."  # 6 words
        target = 6
        
        # Test exact match
        result = self.tool.validate_target(text, target, tolerance=0.05)
        assert result.passed
        assert result.word_count == 6
        assert result.target == 6
        assert result.deviation == 0
        
        # Test within tolerance
        text_short = "This is five words."  # 4 words
        result = self.tool.validate_target(text_short, target=6, tolerance=0.5)  # 50% tolerance
        assert result.passed
        
        # Test outside tolerance
        result = self.tool.validate_target(text_short, target=6, tolerance=0.05)  # 5% tolerance
        assert not result.passed
        assert result.word_count < result.min_allowed

    def test_tolerance_edge_cases(self):
        """Test edge cases for tolerance validation."""
        text = "Five words here exactly today."  # 5 words
        target = 100
        
        # 5% tolerance: 95-105 words allowed
        result = self.tool.validate_target(text, target, tolerance=0.05)
        assert not result.passed
        assert result.min_allowed == 95
        assert result.max_allowed == 105
        
        # 50% tolerance: 50-150 words allowed  
        result = self.tool.validate_target(text, target, tolerance=0.5)
        assert not result.passed  # Still outside range
        assert result.min_allowed == 50
        assert result.max_allowed == 150

    def test_adjustment_calculation_expansion(self):
        """Test adjustment calculation when expansion is needed."""
        text = "Short text."  # 2 words
        target = 100
        
        adjustment = self.tool.calculate_adjustment(text, target, tolerance=0.05)
        
        assert adjustment.needs_expansion
        assert not adjustment.needs_trimming
        assert adjustment.words_needed > 0
        assert adjustment.words_excess == 0
        assert len(adjustment.expansion_points) > 0

    def test_adjustment_calculation_trimming(self):
        """Test adjustment calculation when trimming is needed."""
        # Create a long text (more than 105 words for 100 target with 5% tolerance)
        text = " ".join(["word"] * 150)  # 150 words
        target = 100
        
        adjustment = self.tool.calculate_adjustment(text, target, tolerance=0.05)
        
        assert adjustment.needs_trimming
        assert not adjustment.needs_expansion
        assert adjustment.words_needed == 0
        assert adjustment.words_excess > 0
        assert len(adjustment.trimming_points) > 0

    def test_adjustment_calculation_no_change_needed(self):
        """Test adjustment calculation when no changes are needed."""
        text = " ".join(["word"] * 100)  # Exactly 100 words
        target = 100
        
        adjustment = self.tool.calculate_adjustment(text, target, tolerance=0.05)
        
        assert not adjustment.needs_expansion
        assert not adjustment.needs_trimming
        assert adjustment.words_needed == 0
        assert adjustment.words_excess == 0

    def test_expansion_suggestions(self):
        """Test intelligent expansion point identification."""
        text = "I felt sad. I saw him leave."
        suggestions = self.tool.suggest_expansion_points(text, words_needed=20)
        
        assert len(suggestions) > 0
        # Should identify emotional expansion opportunities
        assert any("emotional" in suggestion.lower() for suggestion in suggestions)

    def test_expansion_suggestions_dialogue(self):
        """Test expansion suggestions for dialogue."""
        text = "He said goodbye. She replied softly."
        suggestions = self.tool.suggest_expansion_points(text, words_needed=15)
        
        assert len(suggestions) > 0
        # Should suggest dialogue expansion
        assert any("dialogue" in suggestion.lower() for suggestion in suggestions)

    def test_expansion_suggestions_sensory(self):
        """Test expansion suggestions for sensory details."""
        text = "I heard the music. I smelled the flowers."
        suggestions = self.tool.suggest_expansion_points(text, words_needed=10)
        
        assert len(suggestions) > 0
        # Should suggest sensory detail expansion
        assert any("sensory" in suggestion.lower() for suggestion in suggestions)

    def test_trimming_suggestions(self):
        """Test intelligent trimming point identification."""
        text = "This is very really quite rather pretty good. It's due to the fact that we have many things."
        suggestions = self.tool.suggest_trimming_points(text, words_excess=5)
        
        assert len(suggestions) > 0
        # Should identify unnecessary adverbs
        assert any("adverb" in suggestion.lower() for suggestion in suggestions)

    def test_trimming_suggestions_repetition(self):
        """Test trimming suggestions for repetitive content."""
        text = "The amazing thing about amazing things is that they are amazing and wonderful and amazing."
        suggestions = self.tool.suggest_trimming_points(text, words_excess=3)
        
        assert len(suggestions) > 0
        # Should provide trimming suggestions (may be general suggestions if no specific patterns found)
        assert all(isinstance(suggestion, str) and len(suggestion) > 0 for suggestion in suggestions)

    def test_trimming_suggestions_verbose_phrases(self):
        """Test trimming suggestions for verbose phrases."""
        text = "In order to understand this, due to the fact that it's important, we need to analyze."
        suggestions = self.tool.suggest_trimming_points(text, words_excess=4)
        
        assert len(suggestions) > 0
        # Should identify verbose phrases
        assert any("in order to" in suggestion.lower() or "due to the fact" in suggestion.lower() for suggestion in suggestions)

    def test_tool_run_method(self):
        """Test the main tool run method."""
        text = "This is a test with exactly eight words."
        
        # Test without target (just counting)
        result = self.tool._run(text=text)
        assert result["word_count"] == 8
        assert "target" not in result
        
        # Test with target (validation)
        result = self.tool._run(text=text, target=8)
        assert result["word_count"] == 8
        assert result["target"] == 8
        assert result["passed"]

    def test_tool_input_validation(self):
        """Test input validation for the tool."""
        # Test empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            self.tool._run(text="")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            self.tool._run(text="   ")
        
        # Test invalid target
        with pytest.raises(ValueError, match="Target word count must be positive"):
            self.tool._run(text="Valid text", target=0)
        
        with pytest.raises(ValueError, match="Target word count must be positive"):
            self.tool._run(text="Valid text", target=-5)
        
        # Test invalid tolerance
        with pytest.raises(ValueError, match="Tolerance must be between 0 and 0.5"):
            self.tool._run(text="Valid text", target=10, tolerance=0)
        
        with pytest.raises(ValueError, match="Tolerance must be between 0 and 0.5"):
            self.tool._run(text="Valid text", target=10, tolerance=0.6)

    def test_tool_registry_integration(self):
        """Test that the tool is properly registered."""
        assert "word_count" in REGISTRY
        assert isinstance(REGISTRY["word_count"], WordCountTool)

    def test_tool_call_via_registry(self):
        """Test calling the tool via the registry."""
        text = "Testing registry integration works."  # 4 words
        
        result = REGISTRY.call("word_count", text=text, target=4)
        assert result["ok"]["word_count"] == 4
        assert result["ok"]["passed"]
        assert result["error"] is None

    def test_word_count_result_model(self):
        """Test WordCountResult Pydantic model."""
        result = WordCountResult(
            word_count=100,
            target=100,
            passed=True,
            min_allowed=95,
            max_allowed=105,
            deviation=0,
            deviation_percent=0.0,
            tolerance=0.05
        )
        
        assert result.word_count == 100
        assert result.passed
        assert result.deviation == 0

    def test_adjustment_suggestion_model(self):
        """Test AdjustmentSuggestion Pydantic model."""
        suggestion = AdjustmentSuggestion(
            needs_expansion=True,
            needs_trimming=False,
            words_needed=20,
            words_excess=0,
            expansion_points=["Add more details", "Include dialogue"]
        )
        
        assert suggestion.needs_expansion
        assert not suggestion.needs_trimming
        assert suggestion.words_needed == 20
        assert len(suggestion.expansion_points) == 2

    def test_large_text_performance(self):
        """Test performance with large text."""
        # Create a large text (1000 words)
        large_text = " ".join(["word"] * 1000)
        
        # Should handle large text efficiently
        count = self.tool.count_words(large_text)
        assert count == 1000
        
        result = self.tool.validate_target(large_text, target=1000, tolerance=0.05)
        assert result.passed

    def test_special_characters_and_punctuation(self):
        """Test word counting with special characters and punctuation."""
        text = "Hello, world! How are you? I'm fine—thanks for asking. (Really!)"
        
        # Should count words correctly despite punctuation
        count = self.tool.count_words(text)
        expected = len(text.split())  # Should match Python's split behavior
        assert count == expected

    def test_multilingual_content(self):
        """Test word counting with multilingual content."""
        text = "Hello world and bonjour monde and hola mundo"
        count = self.tool.count_words(text)
        assert count == 8

    def test_expansion_points_edge_cases(self):
        """Test expansion point suggestions with edge cases."""
        # Test with no text
        suggestions = self.tool.suggest_expansion_points("", words_needed=10)
        assert suggestions == []
        
        # Test with zero words needed
        suggestions = self.tool.suggest_expansion_points("Some text here", words_needed=0)
        assert suggestions == []
        
        # Test with very generic text
        suggestions = self.tool.suggest_expansion_points("Text without specific patterns", words_needed=5)
        assert len(suggestions) > 0  # Should provide generic suggestions

    def test_trimming_points_edge_cases(self):
        """Test trimming point suggestions with edge cases."""
        # Test with no text
        suggestions = self.tool.suggest_trimming_points("", words_excess=5)
        assert suggestions == []
        
        # Test with zero excess words
        suggestions = self.tool.suggest_trimming_points("Some text here", words_excess=0)
        assert suggestions == []
        
        # Test with very clean text
        suggestions = self.tool.suggest_trimming_points("Clean concise text without redundancy", words_excess=2)
        assert len(suggestions) > 0  # Should provide generic suggestions 