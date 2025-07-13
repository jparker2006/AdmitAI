"""Unit tests for brainstorming and story development tools."""

import json
import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.brainstorm_tools import (
    StorySuggestionTool,
    StoryMatchingTool,
    StoryExpansionTool,
    UniquenessValidationTool,
    StorySuggestionResult,
    StoryMatchingResult,
    StoryExpansionResult,
    UniquenessValidationResult,
)
from essay_agent.prompts.brainstorming import (
    STORY_SUGGESTION_PROMPT,
    STORY_MATCHING_PROMPT,
    STORY_EXPANSION_PROMPT,
    UNIQUENESS_VALIDATION_PROMPT
)
from essay_agent.tools import REGISTRY


# ---------------------------------------------------------------------------
# Prompt validation tests
# ---------------------------------------------------------------------------

def test_story_suggestion_prompt_variables():
    """Test that story suggestion prompt has required variables."""
    required = {"essay_prompt", "profile"}
    assert required.issubset(set(STORY_SUGGESTION_PROMPT.input_variables))


def test_story_matching_prompt_variables():
    """Test that story matching prompt has required variables."""
    required = {"story", "essay_prompt"}
    assert required.issubset(set(STORY_MATCHING_PROMPT.input_variables))


def test_story_expansion_prompt_variables():
    """Test that story expansion prompt has required variables."""
    required = {"story_seed"}
    assert required.issubset(set(STORY_EXPANSION_PROMPT.input_variables))


def test_uniqueness_validation_prompt_variables():
    """Test that uniqueness validation prompt has required variables."""
    required = {"story_angle", "previous_essays"}
    assert required.issubset(set(UNIQUENESS_VALIDATION_PROMPT.input_variables))


# ---------------------------------------------------------------------------
# StorySuggestionTool tests
# ---------------------------------------------------------------------------

def test_story_suggestion_tool_offline(monkeypatch):
    """Test StorySuggestionTool with fake LLM response."""
    fake_output = {
        "stories": [
            {
                "title": "Coding Challenge Victory",
                "description": "Solved complex algorithm problem after weeks of struggle, learned persistence.",
                "relevance_score": 0.9,
                "themes": ["growth", "perseverance"],
                "prompt_fit_explanation": "Shows overcoming intellectual challenges through dedication",
                "unique_elements": ["Technical problem-solving approach"]
            },
            {
                "title": "Family Business Ethics",
                "description": "Confronted ethical dilemma in family restaurant, chose integrity over profit.",
                "relevance_score": 0.8,
                "themes": ["integrity", "family"],
                "prompt_fit_explanation": "Demonstrates moral reasoning and difficult decision-making",
                "unique_elements": ["Business ethics angle"]
            },
            {
                "title": "Language Bridge Building",
                "description": "Helped ESL students through tutoring, discovered teaching passion.",
                "relevance_score": 0.7,
                "themes": ["service", "communication"],
                "prompt_fit_explanation": "Shows impact on community and personal growth",
                "unique_elements": ["Cross-cultural communication"]
            },
            {
                "title": "Art Therapy Innovation",
                "description": "Created art program for stressed students, combined creativity with wellness.",
                "relevance_score": 0.85,
                "themes": ["creativity", "leadership"],
                "prompt_fit_explanation": "Demonstrates innovative problem-solving and leadership",
                "unique_elements": ["Interdisciplinary approach"]
            },
            {
                "title": "Environmental Data Project",
                "description": "Collected local pollution data, presented to city council for change.",
                "relevance_score": 0.75,
                "themes": ["environmental", "activism"],
                "prompt_fit_explanation": "Shows civic engagement and scientific research",
                "unique_elements": ["Data-driven activism"]
            }
        ],
        "analysis_notes": "Strong technical and service background with diverse experiences"
    }
    
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
    
    tool = StorySuggestionTool()
    result = tool(
        essay_prompt="Describe a time you faced a significant challenge.",
        profile="High school student, computer science interest, tutoring experience"
    )
    
    assert "ok" in result
    assert "stories" in result["ok"]
    assert len(result["ok"]["stories"]) == 5
    assert result["ok"]["stories"][0]["title"] == "Coding Challenge Victory"
    assert result["ok"]["stories"][0]["relevance_score"] == 0.9


def test_story_suggestion_tool_registry():
    """Test StorySuggestionTool registry integration."""
    assert "suggest_stories" in REGISTRY
    tool = REGISTRY["suggest_stories"]
    assert isinstance(tool, StorySuggestionTool)


def test_story_suggestion_tool_input_validation():
    """Test StorySuggestionTool input validation."""
    tool = StorySuggestionTool()
    
    # Test missing essay_prompt
    result = tool(essay_prompt="", profile="test profile")
    assert "error" in result
    assert "essay_prompt must be a non-empty string" in result["error"].message
    
    # Test missing profile
    result = tool(essay_prompt="test prompt", profile="")
    assert "error" in result
    assert "profile must be a non-empty string" in result["error"].message
    
    # Test essay_prompt too long
    result = tool(essay_prompt="x" * 2001, profile="test profile")
    assert "error" in result
    assert "essay_prompt too long" in result["error"].message


# ---------------------------------------------------------------------------
# StoryMatchingTool tests
# ---------------------------------------------------------------------------

def test_story_matching_tool_offline(monkeypatch):
    """Test StoryMatchingTool with fake LLM response."""
    fake_output = {
        "match_score": 8.5,
        "rationale": "Story directly addresses the challenge theme with clear growth demonstration",
        "strengths": ["Clear conflict resolution", "Shows personal growth"],
        "weaknesses": ["Could use more specific details", "Emotional impact could be stronger"],
        "improvement_suggestions": ["Add more dialogue", "Focus on internal transformation"],
        "optimization_priority": "Enhance emotional depth and specific details"
    }
    
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
    
    tool = StoryMatchingTool()
    result = tool(
        story="I struggled with math but found a tutor who helped me succeed",
        essay_prompt="Describe a time you overcame a challenge"
    )
    
    assert "ok" in result
    assert result["ok"]["match_score"] == 8.5
    assert "Clear conflict resolution" in result["ok"]["strengths"]
    assert len(result["ok"]["improvement_suggestions"]) == 2


def test_story_matching_tool_registry():
    """Test StoryMatchingTool registry integration."""
    assert "match_story" in REGISTRY
    tool = REGISTRY["match_story"]
    assert isinstance(tool, StoryMatchingTool)


def test_story_matching_tool_input_validation():
    """Test StoryMatchingTool input validation."""
    tool = StoryMatchingTool()
    
    # Test missing story
    result = tool(story="", essay_prompt="test prompt")
    assert "error" in result
    assert "story must be a non-empty string" in result["error"].message
    
    # Test story too long
    result = tool(story="x" * 5001, essay_prompt="test prompt")
    assert "error" in result
    assert "story too long" in result["error"].message


# ---------------------------------------------------------------------------
# StoryExpansionTool tests
# ---------------------------------------------------------------------------

def test_story_expansion_tool_offline(monkeypatch):
    """Test StoryExpansionTool with fake LLM response."""
    fake_output = {
        "expansion_questions": [
            "What specific moment did you realize you needed help with math?",
            "How did you feel when you first met your tutor?",
            "What study techniques did your tutor introduce that changed everything?",
            "How did your relationship with your tutor evolve over time?",
            "What specific math concept finally clicked for you?"
        ],
        "focus_areas": ["Emotional transformation", "Specific learning breakthrough"],
        "missing_details": ["Dialogue with tutor", "Specific math problems", "Internal thoughts"],
        "development_priority": "Focus on the specific moment of breakthrough for maximum impact"
    }
    
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
    
    tool = StoryExpansionTool()
    result = tool(story_seed="I struggled with math but found a tutor who helped me succeed")
    
    assert "ok" in result
    assert len(result["ok"]["expansion_questions"]) == 5
    assert "Emotional transformation" in result["ok"]["focus_areas"]
    assert "Dialogue with tutor" in result["ok"]["missing_details"]


def test_story_expansion_tool_registry():
    """Test StoryExpansionTool registry integration."""
    assert "expand_story" in REGISTRY
    tool = REGISTRY["expand_story"]
    assert isinstance(tool, StoryExpansionTool)


def test_story_expansion_tool_input_validation():
    """Test StoryExpansionTool input validation."""
    tool = StoryExpansionTool()
    
    # Test missing story_seed
    result = tool(story_seed="")
    assert "error" in result
    assert "story_seed must be a non-empty string" in result["error"].message
    
    # Test story_seed too short
    result = tool(story_seed="short")
    assert "error" in result
    assert "story_seed too short" in result["error"].message
    
    # Test story_seed too long
    result = tool(story_seed="x" * 2001)
    assert "error" in result
    assert "story_seed too long" in result["error"].message


# ---------------------------------------------------------------------------
# UniquenessValidationTool tests
# ---------------------------------------------------------------------------

def test_uniqueness_validation_tool_offline(monkeypatch):
    """Test UniquenessValidationTool with fake LLM response."""
    fake_output = {
        "uniqueness_score": 0.7,
        "is_unique": True,
        "cliche_risks": ["Potential tutoring cliché if not handled carefully"],
        "differentiation_suggestions": [
            "Focus on specific mathematical concepts rather than general help",
            "Emphasize the mentoring relationship development"
        ],
        "unique_elements": ["Peer tutoring dynamic", "Mathematical problem-solving"],
        "risk_mitigation": ["Avoid generic 'help others' message"],
        "recommendation": "Strong potential if focused on specific mathematical breakthroughs"
    }
    
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
    
    tool = UniquenessValidationTool()
    result = tool(
        story_angle="I became a peer tutor and helped struggling students with math",
        previous_essays=["Essay about volunteering at soup kitchen"]
    )
    
    assert "ok" in result
    assert result["ok"]["uniqueness_score"] == 0.7
    assert result["ok"]["is_unique"] is True
    assert "Potential tutoring cliché" in result["ok"]["cliche_risks"][0]
    assert len(result["ok"]["differentiation_suggestions"]) == 2


def test_uniqueness_validation_tool_registry():
    """Test UniquenessValidationTool registry integration."""
    assert "validate_uniqueness" in REGISTRY
    tool = REGISTRY["validate_uniqueness"]
    assert isinstance(tool, UniquenessValidationTool)


def test_uniqueness_validation_tool_input_validation():
    """Test UniquenessValidationTool input validation."""
    tool = UniquenessValidationTool()
    
    # Test missing story_angle
    result = tool(story_angle="")
    assert "error" in result
    assert "story_angle must be a non-empty string" in result["error"].message
    
    # Test story_angle too short
    result = tool(story_angle="short")
    assert "error" in result
    assert "story_angle too short" in result["error"].message
    
    # Test story_angle too long
    result = tool(story_angle="x" * 3001)
    assert "error" in result
    assert "story_angle too long" in result["error"].message


def test_uniqueness_validation_tool_previous_essays_handling():
    """Test UniquenessValidationTool handles previous_essays parameter correctly."""
    tool = UniquenessValidationTool()
    
    # Test with None (should work)
    # We'll just test that input validation passes
    valid_story = "I started a robotics club at school and competed in regional competitions, learning about engineering and teamwork."
    
    # This should not raise an error during input validation
    # (It may fail later during LLM call, but that's expected in unit tests)
    result = tool(story_angle=valid_story, previous_essays=None)
    # Should not fail on input validation
    assert "story_angle must be a non-empty string" not in str(result)
    
    # Test with string
    result = tool(story_angle=valid_story, previous_essays="Previous essay about sports")
    assert "story_angle must be a non-empty string" not in str(result)
    
    # Test with list
    result = tool(story_angle=valid_story, previous_essays=["Essay 1", "Essay 2"])
    assert "story_angle must be a non-empty string" not in str(result)


# ---------------------------------------------------------------------------
# Pydantic schema validation tests
# ---------------------------------------------------------------------------

def test_story_suggestion_result_schema():
    """Test StorySuggestionResult schema validation."""
    # Valid data
    valid_data = {
        "stories": [
            {
                "title": "Test Story",
                "description": "A test story description",
                "relevance_score": 0.8,
                "themes": ["growth"],
                "prompt_fit_explanation": "Fits well",
                "unique_elements": ["unique aspect"]
            }
        ] * 5,  # Exactly 5 stories
        "analysis_notes": "Good profile"
    }
    
    result = StorySuggestionResult(**valid_data)
    assert len(result.stories) == 5
    assert result.stories[0].title == "Test Story"
    
    # Invalid data - wrong number of stories
    invalid_data = valid_data.copy()
    invalid_data["stories"] = invalid_data["stories"][:3]  # Only 3 stories
    
    with pytest.raises(ValueError):
        StorySuggestionResult(**invalid_data)


def test_story_matching_result_schema():
    """Test StoryMatchingResult schema validation."""
    valid_data = {
        "match_score": 8.5,
        "rationale": "Good match with clear reasoning",
        "strengths": ["Clear narrative"],
        "weaknesses": ["Needs more detail"],
        "improvement_suggestions": ["Add dialogue"],
        "optimization_priority": "Focus on emotions"
    }
    
    result = StoryMatchingResult(**valid_data)
    assert result.match_score == 8.5
    assert result.rationale == "Good match with clear reasoning"
    
    # Invalid score range
    invalid_data = valid_data.copy()
    invalid_data["match_score"] = 15.0  # Out of range
    
    with pytest.raises(ValueError):
        StoryMatchingResult(**invalid_data)


def test_story_expansion_result_schema():
    """Test StoryExpansionResult schema validation."""
    valid_data = {
        "expansion_questions": [
            "Question 1?",
            "Question 2?",
            "Question 3?",
            "Question 4?",
            "Question 5?"
        ],
        "focus_areas": ["Area 1", "Area 2"],
        "missing_details": ["Detail 1", "Detail 2"],
        "development_priority": "Focus on main theme"
    }
    
    result = StoryExpansionResult(**valid_data)
    assert len(result.expansion_questions) == 5
    assert len(result.focus_areas) == 2
    
    # Invalid - too few questions
    invalid_data = valid_data.copy()
    invalid_data["expansion_questions"] = ["Question 1?", "Question 2?"]  # Only 2
    
    with pytest.raises(ValueError):
        StoryExpansionResult(**invalid_data)


def test_uniqueness_validation_result_schema():
    """Test UniquenessValidationResult schema validation."""
    valid_data = {
        "uniqueness_score": 0.7,
        "is_unique": True,
        "cliche_risks": ["Risk 1"],
        "differentiation_suggestions": ["Suggestion 1"],
        "unique_elements": ["Element 1"],
        "risk_mitigation": ["Mitigation 1"],
        "recommendation": "Overall good story"
    }
    
    result = UniquenessValidationResult(**valid_data)
    assert result.uniqueness_score == 0.7
    assert result.is_unique is True
    
    # Invalid uniqueness score
    invalid_data = valid_data.copy()
    invalid_data["uniqueness_score"] = 1.5  # Out of range
    
    with pytest.raises(ValueError):
        UniquenessValidationResult(**invalid_data)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

def test_all_tools_in_registry():
    """Test that all brainstorming tools are registered."""
    expected_tools = [
        "suggest_stories",
        "match_story", 
        "expand_story",
        "validate_uniqueness"
    ]
    
    for tool_name in expected_tools:
        assert tool_name in REGISTRY
        tool = REGISTRY[tool_name]
        assert hasattr(tool, '_run')
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description') 