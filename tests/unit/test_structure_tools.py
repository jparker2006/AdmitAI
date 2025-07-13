"""Unit tests for structure tools.

Tests each tool with FakeListLLM to ensure deterministic behavior
and proper JSON schema validation.
"""

import json
import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.structure_tools import (
    OutlineGeneratorTool,
    StructureValidatorTool,
    TransitionSuggestionTool,
    LengthOptimizerTool
)
from essay_agent.tools import REGISTRY
from essay_agent.prompts.structure import (
    OUTLINE_GENERATOR_PROMPT,
    STRUCTURE_VALIDATOR_PROMPT,
    TRANSITION_SUGGESTION_PROMPT,
    LENGTH_OPTIMIZER_PROMPT
)


def _mock_llm(monkeypatch, fake_output):
    """Helper to mock both get_chat_llm and call_llm."""
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.structure_tools.get_chat_llm", lambda **_: fake_llm)
    monkeypatch.setattr("essay_agent.llm_client.call_llm", lambda llm, prompt, **kwargs: json.dumps(fake_output))


class TestOutlineGeneratorTool:
    """Test OutlineGeneratorTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"story", "essay_prompt", "word_count", "today"}
        assert required.issubset(set(OUTLINE_GENERATOR_PROMPT.input_variables))
    
    def test_outline_generator_offline(self, monkeypatch):
        """Test outline generation with mocked LLM."""
        fake_output = {
            "outline": {
                "hook": "The debate tournament that changed everything started with a simple question about gender roles.",
                "context": "As the only female captain of our high school debate team, I had noticed patterns in how male and female debaters were treated differently during competitions.",
                "growth_moment": "When I presented my research on gender bias in debate judging to our team, I faced resistance from teammates who dismissed my findings. I decided to document instances during our next tournament, collecting data on interruption patterns and scoring disparities.",
                "reflection": "This experience taught me that challenging systems requires both courage and evidence, shaping my commitment to data-driven advocacy."
            },
            "section_word_counts": {
                "hook": 100,
                "context": 160,
                "growth_moment": 260,
                "reflection": 130
            },
            "estimated_word_count": 650
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = OutlineGeneratorTool()
        result = tool(
            story="Questioning Traditional Gender Roles in Debate",
            essay_prompt="Describe a time you challenged a belief or idea.",
            word_count=650
        )
        
        assert result["ok"]["outline"]["hook"].startswith("The debate tournament")
        assert result["ok"]["section_word_counts"]["hook"] == 100
        assert result["ok"]["estimated_word_count"] == 650
    
    def test_outline_generator_registry(self, monkeypatch):
        """Test tool is properly registered."""
        fake_output = {
            "outline": {
                "hook": "Test hook",
                "context": "Test context",
                "growth_moment": "Test growth moment",
                "reflection": "Test reflection"
            },
            "section_word_counts": {
                "hook": 75,
                "context": 125,
                "growth_moment": 200,
                "reflection": 100
            },
            "estimated_word_count": 500
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = REGISTRY.call(
            "outline_generator",
            story="Test story",
            essay_prompt="Test prompt",
            word_count=500
        )
        assert result["ok"]["estimated_word_count"] == 500
    
    def test_empty_story_error(self):
        """Test empty story raises error."""
        tool = OutlineGeneratorTool()
        result = tool(story="", essay_prompt="Test prompt", word_count=650)
        
        assert result["error"] is not None
        assert "empty" in result["error"].message
    
    def test_invalid_word_count_error(self):
        """Test invalid word count raises error."""
        tool = OutlineGeneratorTool()
        result = tool(story="Test story", essay_prompt="Test prompt", word_count=0)
        
        assert result["error"] is not None
        assert "positive integer" in result["error"].message


class TestStructureValidatorTool:
    """Test StructureValidatorTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"outline", "today"}
        assert required.issubset(set(STRUCTURE_VALIDATOR_PROMPT.input_variables))
    
    def test_structure_validator_offline(self, monkeypatch):
        """Test structure validation with mocked LLM."""
        fake_output = {
            "is_valid": True,
            "score": 8.5,
            "issues": ["Minor transition weakness between context and growth moment"],
            "overall_feedback": "Strong outline with clear progression and authentic voice. Consider strengthening transitions between sections."
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = StructureValidatorTool()
        test_outline = {
            "hook": "Test hook",
            "context": "Test context",
            "growth_moment": "Test growth",
            "reflection": "Test reflection"
        }
        result = tool(outline=test_outline)
        
        assert result["ok"]["is_valid"] is True
        assert result["ok"]["score"] == 8.5
        assert len(result["ok"]["issues"]) == 1
        assert len(result["ok"]["overall_feedback"]) <= 120
    
    def test_structure_validator_string_input(self, monkeypatch):
        """Test validator with string input."""
        fake_output = {
            "is_valid": False,
            "score": 6.0,
            "issues": ["Weak hook lacks intrigue", "Growth moment too vague"],
            "overall_feedback": "The outline needs more specific details and a stronger opening to engage readers effectively."
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = StructureValidatorTool()
        result = tool(outline="Hook: Weak opening\nContext: Basic setup\nGrowth: Vague challenge\nReflection: Generic lesson")
        
        assert result["ok"]["is_valid"] is False
        assert result["ok"]["score"] == 6.0
    
    def test_structure_validator_registry(self, monkeypatch):
        """Test tool is properly registered."""
        fake_output = {
            "is_valid": True,
            "score": 7.5,
            "issues": [],
            "overall_feedback": "Solid outline with good structure and flow."
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = REGISTRY.call("structure_validator", outline="Test outline")
        assert result["ok"]["score"] == 7.5
    
    def test_empty_outline_error(self):
        """Test empty outline raises error."""
        tool = StructureValidatorTool()
        result = tool(outline="")
        
        assert result["error"] is not None
        assert "empty" in result["error"].message


class TestTransitionSuggestionTool:
    """Test TransitionSuggestionTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"outline", "today"}
        assert required.issubset(set(TRANSITION_SUGGESTION_PROMPT.input_variables))
    
    def test_transition_suggestion_offline(self, monkeypatch):
        """Test transition suggestion with mocked LLM."""
        fake_output = {
            "transitions": {
                "hook_to_context": "This question would define my junior year.",
                "context_to_growth": "But my research revealed an uncomfortable truth.",
                "growth_to_reflection": "Standing up required more than just data."
            }
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = TransitionSuggestionTool()
        test_outline = {
            "hook": "Debate question about gender roles",
            "context": "Female debate captain observing patterns",
            "growth_moment": "Presenting research and facing resistance",
            "reflection": "Learning about evidence-based advocacy"
        }
        result = tool(outline=test_outline)
        
        assert "hook_to_context" in result["ok"]["transitions"]
        assert "context_to_growth" in result["ok"]["transitions"]
        assert "growth_to_reflection" in result["ok"]["transitions"]
        assert len(result["ok"]["transitions"]["hook_to_context"]) <= 150
    
    def test_transition_suggestion_string_input(self, monkeypatch):
        """Test transition suggestion with string input."""
        fake_output = {
            "transitions": {
                "hook_to_context": "The story began in my hometown.",
                "context_to_growth": "Then everything changed.",
                "growth_to_reflection": "I learned something vital."
            }
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = TransitionSuggestionTool()
        result = tool(outline="Hook: Opening\nContext: Background\nGrowth: Challenge\nReflection: Lesson")
        
        assert len(result["ok"]["transitions"]) == 3
    
    def test_transition_suggestion_registry(self, monkeypatch):
        """Test tool is properly registered."""
        fake_output = {
            "transitions": {
                "hook_to_context": "This moment changed everything.",
                "context_to_growth": "But I wasn't prepared for what happened next.",
                "growth_to_reflection": "The experience taught me a crucial lesson."
            }
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = REGISTRY.call("transition_suggestion", outline="Test outline")
        assert len(result["ok"]["transitions"]) == 3
    
    def test_empty_outline_error(self):
        """Test empty outline raises error."""
        tool = TransitionSuggestionTool()
        result = tool(outline="")
        
        assert result["error"] is not None
        assert "empty" in result["error"].message


class TestLengthOptimizerTool:
    """Test LengthOptimizerTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"outline", "target_word_count", "today"}
        assert required.issubset(set(LENGTH_OPTIMIZER_PROMPT.input_variables))
    
    def test_length_optimizer_offline(self, monkeypatch):
        """Test length optimization with mocked LLM."""
        fake_output = {
            "optimized_counts": {
                "hook": 100,
                "context": 160,
                "growth_moment": 260,
                "reflection": 130
            },
            "total": 650
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = LengthOptimizerTool()
        test_outline = {
            "hook": "Current hook",
            "context": "Current context",
            "growth_moment": "Current growth moment",
            "reflection": "Current reflection"
        }
        result = tool(outline=test_outline, target_word_count=650)
        
        assert result["ok"]["total"] == 650
        assert result["ok"]["optimized_counts"]["growth_moment"] == 260  # Should be largest
        assert result["ok"]["optimized_counts"]["hook"] == 100
    
    def test_length_optimizer_different_target(self, monkeypatch):
        """Test length optimization with different target."""
        fake_output = {
            "optimized_counts": {
                "hook": 75,
                "context": 125,
                "growth_moment": 200,
                "reflection": 100
            },
            "total": 500
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = LengthOptimizerTool()
        result = tool(outline="Test outline", target_word_count=500)
        
        assert result["ok"]["total"] == 500
        assert result["ok"]["optimized_counts"]["growth_moment"] > result["ok"]["optimized_counts"]["hook"]
    
    def test_length_optimizer_registry(self):
        """Test tool is properly registered."""
        # Just check that the tool is in the registry
        assert "length_optimizer" in REGISTRY
        assert isinstance(REGISTRY["length_optimizer"], LengthOptimizerTool)
    
    def test_empty_outline_error(self):
        """Test empty outline raises error."""
        tool = LengthOptimizerTool()
        result = tool(outline="", target_word_count=650)
        
        assert result["error"] is not None
        assert "empty" in result["error"].message
    
    def test_invalid_target_error(self):
        """Test invalid target word count raises error."""
        tool = LengthOptimizerTool()
        result = tool(outline="Test outline", target_word_count=0)
        
        assert result["error"] is not None
        assert "positive integer" in result["error"].message


class TestToolRegistration:
    """Test that all structure tools are properly registered."""
    
    def test_all_tools_registered(self):
        """Test that all four tools are registered in REGISTRY."""
        expected_tools = [
            "outline_generator",
            "structure_validator", 
            "transition_suggestion",
            "length_optimizer"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in REGISTRY, f"Tool '{tool_name}' not found in registry"
    
    def test_tool_descriptions(self):
        """Test that all tools have meaningful descriptions."""
        tool_names = [
            "outline_generator",
            "structure_validator",
            "transition_suggestion", 
            "length_optimizer"
        ]
        
        for tool_name in tool_names:
            tool = REGISTRY[tool_name]
            assert len(tool.description) > 20, f"Tool '{tool_name}' has insufficient description"
            assert "outline" in tool.description.lower(), f"Tool '{tool_name}' description should mention outline"


class TestConvenienceFunctions:
    """Test the convenience functions for direct usage."""
    
    def test_generate_outline_function(self, monkeypatch):
        """Test generate_outline convenience function."""
        fake_output = {
            "outline": {
                "hook": "Test hook",
                "context": "Test context", 
                "growth_moment": "Test growth",
                "reflection": "Test reflection"
            },
            "section_word_counts": {
                "hook": 100,
                "context": 160,
                "growth_moment": 260,
                "reflection": 130
            },
            "estimated_word_count": 650
        }
        _mock_llm(monkeypatch, fake_output)
        
        from essay_agent.tools.structure_tools import generate_outline
        result = generate_outline("Test story", "Test prompt", 650)
        
        assert result["ok"]["estimated_word_count"] == 650
    
    def test_validate_structure_function(self, monkeypatch):
        """Test validate_structure convenience function."""
        fake_output = {
            "is_valid": True,
            "score": 8.0,
            "issues": [],
            "overall_feedback": "Good structure overall."
        }
        _mock_llm(monkeypatch, fake_output)
        
        from essay_agent.tools.structure_tools import validate_structure
        result = validate_structure({"hook": "test", "context": "test", "growth_moment": "test", "reflection": "test"})
        
        assert result["ok"]["score"] == 8.0 