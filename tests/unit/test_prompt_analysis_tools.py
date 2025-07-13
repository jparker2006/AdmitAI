"""Unit tests for prompt analysis tools.

Tests each tool with FakeListLLM to ensure deterministic behavior
and proper JSON schema validation.
"""

import json
import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.prompt_tools import (
    ClassifyPromptTool,
    ExtractRequirementsTool,
    SuggestStrategyTool,
    DetectOverlapTool
)
from essay_agent.tools import REGISTRY
from essay_agent.prompts.prompt_analysis import (
    CLASSIFY_PROMPT_PROMPT,
    EXTRACT_REQUIREMENTS_PROMPT,
    SUGGEST_STRATEGY_PROMPT,
    DETECT_OVERLAP_PROMPT
)


class TestClassifyPromptTool:
    """Test ClassifyPromptTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"essay_prompt", "today"}
        assert required.issubset(set(CLASSIFY_PROMPT_PROMPT.input_variables))
    
    def test_classify_prompt_offline(self, monkeypatch):
        """Test classification with mocked LLM."""
        fake_output = {
            "theme": "challenge",
            "confidence": 0.9,
            "rationale": "Directly asks about challenging beliefs, core challenge theme"
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = ClassifyPromptTool()
        result = tool(essay_prompt="Describe a time you challenged a belief or idea.")
        
        assert result["ok"]["theme"] == "challenge"
        assert result["ok"]["confidence"] == 0.9
        assert "challenge" in result["ok"]["rationale"]
    
    def test_classify_prompt_registry(self, monkeypatch):
        """Test tool is properly registered."""
        fake_output = {
            "theme": "growth",
            "confidence": 0.8,
            "rationale": "Focuses on personal development and learning"
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        result = REGISTRY.call("classify_prompt", essay_prompt="What motivates you to learn?")
        assert result["ok"]["theme"] == "growth"
    
    def test_classify_prompt_validation_error(self, monkeypatch):
        """Test validation catches invalid theme."""
        fake_output = {
            "theme": "invalid_theme",
            "confidence": 0.9,
            "rationale": "This should fail validation"
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = ClassifyPromptTool()
        result = tool(essay_prompt="Test prompt")
        
        # Should return error due to validation failure
        assert result["error"] is not None
    
    def test_empty_prompt_error(self):
        """Test empty prompt raises error."""
        tool = ClassifyPromptTool()
        result = tool(essay_prompt="")
        
        assert result["error"] is not None
        assert "empty" in result["error"].message


class TestExtractRequirementsTool:
    """Test ExtractRequirementsTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"essay_prompt", "today"}
        assert required.issubset(set(EXTRACT_REQUIREMENTS_PROMPT.input_variables))
    
    def test_extract_requirements_offline(self, monkeypatch):
        """Test requirements extraction with mocked LLM."""
        fake_output = {
            "word_limit": 650,
            "key_questions": ["What challenge did you overcome?", "What did you learn?"],
            "evaluation_criteria": ["problem-solving", "resilience", "self-reflection", "growth mindset"]
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = ExtractRequirementsTool()
        result = tool(essay_prompt="In 650 words or less, describe a challenge you overcame. What did you learn?")
        
        assert result["ok"]["word_limit"] == 650
        assert len(result["ok"]["key_questions"]) == 2
        assert "problem-solving" in result["ok"]["evaluation_criteria"]
    
    def test_extract_requirements_no_word_limit(self, monkeypatch):
        """Test extraction when no word limit is specified."""
        fake_output = {
            "word_limit": None,
            "key_questions": ["Who are you?"],
            "evaluation_criteria": ["self-awareness", "personality", "values"]
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = ExtractRequirementsTool()
        result = tool(essay_prompt="Tell us about yourself.")
        
        assert result["ok"]["word_limit"] is None
        assert "self-awareness" in result["ok"]["evaluation_criteria"]
    
    def test_extract_requirements_registry(self, monkeypatch):
        """Test tool is properly registered."""
        fake_output = {
            "word_limit": 500,
            "key_questions": ["What defines you?"],
            "evaluation_criteria": ["authenticity", "self-reflection"]
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        result = REGISTRY.call("extract_requirements", essay_prompt="Define yourself in 500 words.")
        assert result["ok"]["word_limit"] == 500


class TestSuggestStrategyTool:
    """Test SuggestStrategyTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"essay_prompt", "profile", "today"}
        assert required.issubset(set(SUGGEST_STRATEGY_PROMPT.input_variables))
    
    def test_suggest_strategy_offline(self, monkeypatch):
        """Test strategy suggestion with mocked LLM."""
        fake_output = {
            "overall_strategy": "Focus on a specific debate loss that taught resilience. Use immigrant perspective to show unique challenges. Structure: setup stakes, describe failure moment, analyze what went wrong, demonstrate growth through specific actions taken afterward.",
            "recommended_story_traits": ["cultural perspective", "leadership under pressure", "analytical thinking", "resilience"],
            "potential_pitfalls": ["avoid generic 'failure made me stronger'", "don't blame others", "avoid victim narrative", "ensure clear lesson learned"]
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = SuggestStrategyTool()
        result = tool(
            essay_prompt="Describe a failure and what you learned",
            profile="Debate team captain, immigrant family"
        )
        
        assert "debate" in result["ok"]["overall_strategy"]
        assert len(result["ok"]["recommended_story_traits"]) == 4
        assert len(result["ok"]["potential_pitfalls"]) == 4
        assert "cultural perspective" in result["ok"]["recommended_story_traits"]
    
    def test_suggest_strategy_registry(self, monkeypatch):
        """Test tool is properly registered."""
        fake_output = {
            "overall_strategy": "Focus on leadership moment that shows growth.",
            "recommended_story_traits": ["leadership", "problem-solving"],
            "potential_pitfalls": ["avoid clichés", "be specific"]
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        result = REGISTRY.call(
            "suggest_strategy",
            essay_prompt="Describe a leadership experience",
            profile="Student body president"
        )
        assert "leadership" in result["ok"]["overall_strategy"]
    
    def test_empty_profile_error(self):
        """Test empty profile raises error."""
        tool = SuggestStrategyTool()
        result = tool(essay_prompt="Test prompt", profile="")
        
        assert result["error"] is not None
        assert "empty" in result["error"].message


class TestDetectOverlapTool:
    """Test DetectOverlapTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"story", "previous_essays", "today"}
        assert required.issubset(set(DETECT_OVERLAP_PROMPT.input_variables))
    
    def test_detect_overlap_offline(self, monkeypatch):
        """Test overlap detection with mocked LLM."""
        fake_output = {
            "overlaps_found": True,
            "overlap_score": 0.7,
            "conflicting_essays": [1]
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = DetectOverlapTool()
        result = tool(
            story="Debate team failure",
            previous_essays=["Soccer injury recovery", "Debate championship win"]
        )
        
        assert result["ok"]["overlaps_found"] is True
        assert result["ok"]["overlap_score"] == 0.7
        assert result["ok"]["conflicting_essays"] == [1]
    
    def test_detect_overlap_no_conflicts(self, monkeypatch):
        """Test when no overlaps are found."""
        fake_output = {
            "overlaps_found": False,
            "overlap_score": 0.2,
            "conflicting_essays": []
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = DetectOverlapTool()
        result = tool(
            story="Coding project",
            previous_essays=["Soccer injury", "Volunteer work"]
        )
        
        assert result["ok"]["overlaps_found"] is False
        assert result["ok"]["overlap_score"] == 0.2
        assert result["ok"]["conflicting_essays"] == []
    
    def test_detect_overlap_json_string_input(self, monkeypatch):
        """Test handling JSON string input for previous_essays."""
        fake_output = {
            "overlaps_found": False,
            "overlap_score": 0.1,
            "conflicting_essays": []
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = DetectOverlapTool()
        result = tool(
            story="New story",
            previous_essays='["Essay 1", "Essay 2"]'  # JSON string
        )
        
        assert result["ok"]["overlaps_found"] is False
    
    def test_detect_overlap_single_essay_string(self, monkeypatch):
        """Test handling single essay string as previous_essays."""
        fake_output = {
            "overlaps_found": False,
            "overlap_score": 0.3,
            "conflicting_essays": []
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        tool = DetectOverlapTool()
        result = tool(
            story="New story",
            previous_essays="Single previous essay"  # Single string
        )
        
        assert result["ok"]["overlaps_found"] is False
    
    def test_detect_overlap_registry(self, monkeypatch):
        """Test tool is properly registered."""
        fake_output = {
            "overlaps_found": True,
            "overlap_score": 0.8,
            "conflicting_essays": [0]
        }
        fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
        monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
        
        result = REGISTRY.call(
            "detect_overlap",
            story="Similar story",
            previous_essays=["Very similar essay"]
        )
        assert result["ok"]["overlaps_found"] is True
    
    def test_empty_story_error(self):
        """Test empty story raises error."""
        tool = DetectOverlapTool()
        result = tool(story="", previous_essays=["Essay 1"])
        
        assert result["error"] is not None
        assert "empty" in result["error"].message


class TestToolRegistration:
    """Test that all tools are properly registered."""
    
    def test_all_tools_registered(self):
        """Test that all four tools are in the registry."""
        expected_tools = {
            "classify_prompt",
            "extract_requirements", 
            "suggest_strategy",
            "detect_overlap"
        }
        
        registered_tools = set(REGISTRY.keys())
        assert expected_tools.issubset(registered_tools)
    
    def test_tool_descriptions(self):
        """Test that all tools have meaningful descriptions."""
        for tool_name in ["classify_prompt", "extract_requirements", "suggest_strategy", "detect_overlap"]:
            tool = REGISTRY[tool_name]
            assert hasattr(tool, 'description')
            assert len(tool.description) > 10  # Non-trivial description 