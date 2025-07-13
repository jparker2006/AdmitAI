"""Unit tests for evaluation tools.

Tests each tool with FakeListLLM to ensure deterministic behavior
and proper JSON schema validation.
"""

import json
import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.evaluation_tools import (
    EssayScoringTool,
    WeaknessHighlightTool,
    ClicheDetectionTool,
    AlignmentCheckTool,
    score_essay,
    highlight_weaknesses,
    detect_cliches,
    check_alignment
)
from essay_agent.tools import REGISTRY
from essay_agent.prompts.evaluation import (
    ESSAY_SCORING_PROMPT,
    WEAKNESS_HIGHLIGHT_PROMPT,
    CLICHE_DETECTION_PROMPT,
    ALIGNMENT_CHECK_PROMPT
)


def _mock_llm(monkeypatch, fake_output):
    """Helper to mock both get_chat_llm and call_llm."""
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.evaluation_tools.get_chat_llm", lambda **_: fake_llm)
    monkeypatch.setattr("essay_agent.llm_client.call_llm", lambda llm, prompt, **kwargs: json.dumps(fake_output))


class TestEssayScoringTool:
    """Test EssayScoringTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"essay_text", "essay_prompt", "today"}
        assert required.issubset(set(ESSAY_SCORING_PROMPT.input_variables))
    
    def test_essay_scoring_offline(self, monkeypatch):
        """Test essay scoring with mocked LLM."""
        fake_output = {
            "scores": {
                "clarity": 8,
                "insight": 9,
                "structure": 7,
                "voice": 8,
                "prompt_fit": 9
            },
            "overall_score": 8.2,
            "is_strong_essay": True,
            "feedback": "Strong essay with vivid examples. Consider tightening the conclusion for more impact."
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = EssayScoringTool()
        result = tool(
            essay_text="I've always been fascinated by the intersection of technology and human behavior...",
            essay_prompt="Describe a personal experience that shaped your values."
        )
        
        assert result["ok"]["scores"]["clarity"] == 8
        assert result["ok"]["scores"]["insight"] == 9
        assert result["ok"]["overall_score"] == 8.2
        assert result["ok"]["is_strong_essay"] is True
        assert len(result["ok"]["feedback"]) <= 200
    
    def test_essay_scoring_registry(self, monkeypatch):
        """Test essay scoring tool via registry."""
        fake_output = {
            "scores": {
                "clarity": 6,
                "insight": 7,
                "structure": 6,
                "voice": 5,
                "prompt_fit": 6
            },
            "overall_score": 6.0,
            "is_strong_essay": False,
            "feedback": "Good foundation but needs more specific examples and stronger voice."
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = REGISTRY.call(
            "essay_scoring",
            essay_text="I learned a lot from this experience...",
            essay_prompt="What challenge have you overcome?"
        )
        
        assert result["ok"]["overall_score"] == 6.0
        assert result["ok"]["is_strong_essay"] is False
    
    def test_empty_essay_error(self):
        """Test error handling for empty essay."""
        tool = EssayScoringTool()
        result = tool(essay_text="", essay_prompt="Some prompt")
        assert result["error"] is not None
        assert "essay_text cannot be empty" in result["error"].message
    
    def test_empty_prompt_error(self):
        """Test error handling for empty prompt."""
        tool = EssayScoringTool()
        result = tool(essay_text="Some essay", essay_prompt="")
        assert result["error"] is not None
        assert "essay_prompt cannot be empty" in result["error"].message
    
    def test_essay_too_long_error(self):
        """Test error handling for essay that's too long."""
        tool = EssayScoringTool()
        long_essay = "A" * 5001
        result = tool(essay_text=long_essay, essay_prompt="Some prompt")
        assert result["error"] is not None
        assert "essay_text too long" in result["error"].message


class TestWeaknessHighlightTool:
    """Test WeaknessHighlightTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"essay_text", "today"}
        assert required.issubset(set(WEAKNESS_HIGHLIGHT_PROMPT.input_variables))
    
    def test_weakness_highlight_offline(self, monkeypatch):
        """Test weakness highlighting with mocked LLM."""
        fake_output = {
            "weaknesses": [
                {
                    "text_excerpt": "I learned a lot from this experience",
                    "weakness_type": "content",
                    "severity": 4,
                    "explanation": "Vague and generic statement without specific details",
                    "improvement_advice": "Replace with specific lessons learned with concrete examples"
                },
                {
                    "text_excerpt": "This experience changed my life",
                    "weakness_type": "style",
                    "severity": 5,
                    "explanation": "Overused cliché phrase that lacks originality",
                    "improvement_advice": "Show the change through specific actions and decisions instead of stating it"
                },
                {
                    "text_excerpt": "In conclusion, I think that",
                    "weakness_type": "structure",
                    "severity": 3,
                    "explanation": "Weak transition that doesn't connect to main theme",
                    "improvement_advice": "Connect conclusion to opening with specific callback or reflection"
                }
            ],
            "overall_weakness_count": 3,
            "priority_focus": "content specificity"
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = WeaknessHighlightTool()
        result = tool(essay_text="I learned a lot from this experience. This experience changed my life. In conclusion, I think that...")
        
        assert len(result["ok"]["weaknesses"]) == 3
        assert result["ok"]["overall_weakness_count"] == 3
        assert result["ok"]["weaknesses"][0]["severity"] == 4
        assert result["ok"]["weaknesses"][0]["weakness_type"] == "content"
        assert len(result["ok"]["priority_focus"]) <= 50
    
    def test_weakness_highlight_registry(self, monkeypatch):
        """Test weakness highlighting tool via registry."""
        fake_output = {
            "weaknesses": [
                {
                    "text_excerpt": "I always wanted to help people",
                    "weakness_type": "content",
                    "severity": 3,
                    "explanation": "Generic motivation without specific examples",
                    "improvement_advice": "Provide specific instance of helping someone"
                },
                {
                    "text_excerpt": "The experience taught me a lot",
                    "weakness_type": "clarity",
                    "severity": 4,
                    "explanation": "Vague language that doesn't specify what was learned",
                    "improvement_advice": "List specific lessons or insights gained"
                },
                {
                    "text_excerpt": "I became a better person",
                    "weakness_type": "style",
                    "severity": 5,
                    "explanation": "Cliché conclusion without evidence",
                    "improvement_advice": "Show specific behavioral changes or growth"
                }
            ],
            "overall_weakness_count": 3,
            "priority_focus": "specificity"
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = REGISTRY.call("weakness_highlight", essay_text="I always wanted to help people. The experience taught me a lot. I became a better person.")
        
        assert len(result["ok"]["weaknesses"]) == 3
        assert result["ok"]["priority_focus"] == "specificity"
    
    def test_empty_essay_error(self):
        """Test error handling for empty essay."""
        tool = WeaknessHighlightTool()
        result = tool(essay_text="")
        assert result["error"] is not None
        assert "essay_text cannot be empty" in result["error"].message


class TestClicheDetectionTool:
    """Test ClicheDetectionTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"essay_text", "today"}
        assert required.issubset(set(CLICHE_DETECTION_PROMPT.input_variables))
    
    def test_cliche_detection_offline(self, monkeypatch):
        """Test cliché detection with mocked LLM."""
        fake_output = {
            "cliches_found": [
                {
                    "text_excerpt": "Ever since I was little",
                    "cliche_type": "overused_phrase",
                    "severity": 4,
                    "frequency": 1,
                    "alternative_suggestion": "Start with specific age and concrete memory: 'At age seven, I discovered...'"
                },
                {
                    "text_excerpt": "I want to change the world",
                    "cliche_type": "overused_phrase",
                    "severity": 5,
                    "frequency": 1,
                    "alternative_suggestion": "Focus on specific community or problem: 'I want to reduce food waste in my city'"
                },
                {
                    "text_excerpt": "helped me grow as a person",
                    "cliche_type": "generic_description",
                    "severity": 3,
                    "frequency": 1,
                    "alternative_suggestion": "Specify exact ways you changed: 'taught me to listen before speaking'"
                }
            ],
            "total_cliches": 3,
            "uniqueness_score": 0.4,
            "overall_assessment": "Multiple overused phrases reduce originality; focus on specific, personal details"
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = ClicheDetectionTool()
        result = tool(essay_text="Ever since I was little, I want to change the world. This experience helped me grow as a person.")
        
        assert len(result["ok"]["cliches_found"]) == 3
        assert result["ok"]["total_cliches"] == 3
        assert result["ok"]["uniqueness_score"] == 0.4
        assert result["ok"]["cliches_found"][0]["severity"] == 4
        assert result["ok"]["cliches_found"][0]["cliche_type"] == "overused_phrase"
        assert len(result["ok"]["overall_assessment"]) <= 100
    
    def test_cliche_detection_registry(self, monkeypatch):
        """Test cliché detection tool via registry."""
        fake_output = {
            "cliches_found": [
                {
                    "text_excerpt": "This experience changed my life",
                    "cliche_type": "overused_phrase",
                    "severity": 5,
                    "frequency": 1,
                    "alternative_suggestion": "Show specific changes in behavior or perspective"
                }
            ],
            "total_cliches": 1,
            "uniqueness_score": 0.7,
            "overall_assessment": "One major cliché detected but otherwise original language"
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = REGISTRY.call("cliche_detection", essay_text="This experience changed my life in many ways.")
        
        assert len(result["ok"]["cliches_found"]) == 1
        assert result["ok"]["uniqueness_score"] == 0.7
    
    def test_empty_essay_error(self):
        """Test error handling for empty essay."""
        tool = ClicheDetectionTool()
        result = tool(essay_text="")
        assert result["error"] is not None
        assert "essay_text cannot be empty" in result["error"].message


class TestAlignmentCheckTool:
    """Test AlignmentCheckTool functionality."""
    
    def test_prompt_variables(self):
        """Test that prompt has required variables."""
        required = {"essay_text", "essay_prompt", "today"}
        assert required.issubset(set(ALIGNMENT_CHECK_PROMPT.input_variables))
    
    def test_alignment_check_offline(self, monkeypatch):
        """Test alignment checking with mocked LLM."""
        fake_output = {
            "alignment_score": 8.5,
            "requirements_analysis": [
                {
                    "requirement": "Describe a personal experience",
                    "addressed": True,
                    "quality": 2,
                    "evidence": "Essay focuses on volunteering at local shelter, provides specific details"
                },
                {
                    "requirement": "Explain how it shaped your values",
                    "addressed": True,
                    "quality": 2,
                    "evidence": "Clear connection between experience and developing empathy and service"
                },
                {
                    "requirement": "Demonstrate personal growth",
                    "addressed": True,
                    "quality": 1,
                    "evidence": "Shows change but could be more specific about growth process"
                }
            ],
            "missing_elements": [],
            "is_fully_aligned": True,
            "improvement_priority": "Strengthen personal growth narrative with specific examples"
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = AlignmentCheckTool()
        result = tool(
            essay_text="My experience volunteering at the local shelter taught me about empathy...",
            essay_prompt="Describe a personal experience that shaped your values."
        )
        
        assert result["ok"]["alignment_score"] == 8.5
        assert result["ok"]["is_fully_aligned"] is True
        assert len(result["ok"]["requirements_analysis"]) == 3
        assert result["ok"]["requirements_analysis"][0]["quality"] == 2
        assert result["ok"]["requirements_analysis"][0]["addressed"] is True
        assert len(result["ok"]["missing_elements"]) == 0
        assert len(result["ok"]["improvement_priority"]) <= 100
    
    def test_alignment_check_poor_alignment(self, monkeypatch):
        """Test alignment check with poor alignment."""
        fake_output = {
            "alignment_score": 4.2,
            "requirements_analysis": [
                {
                    "requirement": "Describe a personal experience",
                    "addressed": True,
                    "quality": 1,
                    "evidence": "Mentions experience but lacks specific details"
                },
                {
                    "requirement": "Explain how it shaped your values",
                    "addressed": False,
                    "quality": 0,
                    "evidence": "No clear connection made between experience and values"
                }
            ],
            "missing_elements": ["Clear values connection", "Specific impact description"],
            "is_fully_aligned": False,
            "improvement_priority": "Explicitly connect experience to specific values developed"
        }
        _mock_llm(monkeypatch, fake_output)
        
        tool = AlignmentCheckTool()
        result = tool(
            essay_text="I did some volunteer work once...",
            essay_prompt="Describe a personal experience that shaped your values."
        )
        
        assert result["ok"]["alignment_score"] == 4.2
        assert result["ok"]["is_fully_aligned"] is False
        assert len(result["ok"]["missing_elements"]) == 2
        assert "Clear values connection" in result["ok"]["missing_elements"]
    
    def test_alignment_check_registry(self, monkeypatch):
        """Test alignment check tool via registry."""
        fake_output = {
            "alignment_score": 9.0,
            "requirements_analysis": [
                {
                    "requirement": "Describe a challenge you overcame",
                    "addressed": True,
                    "quality": 2,
                    "evidence": "Detailed account of overcoming stage fright through debate practice"
                }
            ],
            "missing_elements": [],
            "is_fully_aligned": True,
            "improvement_priority": "None - essay fully addresses all requirements"
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = REGISTRY.call(
            "alignment_check",
            essay_text="I overcame my stage fright through months of debate practice...",
            essay_prompt="Describe a challenge you overcame."
        )
        
        assert result["ok"]["alignment_score"] == 9.0
        assert result["ok"]["is_fully_aligned"] is True
    
    def test_empty_essay_error(self):
        """Test error handling for empty essay."""
        tool = AlignmentCheckTool()
        result = tool(essay_text="", essay_prompt="Some prompt")
        assert result["error"] is not None
        assert "essay_text cannot be empty" in result["error"].message
    
    def test_empty_prompt_error(self):
        """Test error handling for empty prompt."""
        tool = AlignmentCheckTool()
        result = tool(essay_text="Some essay", essay_prompt="")
        assert result["error"] is not None
        assert "essay_prompt cannot be empty" in result["error"].message


class TestToolRegistration:
    """Test that all evaluation tools are properly registered."""
    
    def test_all_tools_registered(self):
        """Test that all evaluation tools are in the registry."""
        expected_tools = [
            "essay_scoring",
            "weakness_highlight", 
            "cliche_detection",
            "alignment_check"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in REGISTRY, f"Tool {tool_name} not found in registry"
            assert REGISTRY[tool_name] is not None
    
    def test_tool_descriptions(self):
        """Test that all tools have meaningful descriptions."""
        evaluation_tools = [
            "essay_scoring",
            "weakness_highlight",
            "cliche_detection", 
            "alignment_check"
        ]
        
        for tool_name in evaluation_tools:
            tool = REGISTRY[tool_name]
            assert hasattr(tool, 'description')
            assert len(tool.description) > 20  # Meaningful description
            assert tool.description.strip() != ""


class TestConvenienceFunctions:
    """Test convenience functions for direct usage."""
    
    def test_score_essay_function(self, monkeypatch):
        """Test score_essay convenience function."""
        fake_output = {
            "scores": {
                "clarity": 7,
                "insight": 8,
                "structure": 7,
                "voice": 6,
                "prompt_fit": 8
            },
            "overall_score": 7.2,
            "is_strong_essay": True,
            "feedback": "Solid essay with good insight. Work on strengthening voice and examples."
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = score_essay("Sample essay text", "Sample prompt")
        assert result["ok"]["overall_score"] == 7.2
        assert result["ok"]["is_strong_essay"] is True
    
    def test_highlight_weaknesses_function(self, monkeypatch):
        """Test highlight_weaknesses convenience function."""
        fake_output = {
            "weaknesses": [
                {
                    "text_excerpt": "I learned things",
                    "weakness_type": "content",
                    "severity": 4,
                    "explanation": "Too vague",
                    "improvement_advice": "Be more specific"
                },
                {
                    "text_excerpt": "It was good",
                    "weakness_type": "style",
                    "severity": 3,
                    "explanation": "Generic language",
                    "improvement_advice": "Use more descriptive words"
                },
                {
                    "text_excerpt": "The end",
                    "weakness_type": "structure",
                    "severity": 5,
                    "explanation": "Abrupt conclusion",
                    "improvement_advice": "Connect to opening theme"
                }
            ],
            "overall_weakness_count": 3,
            "priority_focus": "content"
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = highlight_weaknesses("Sample essay text")
        assert len(result["ok"]["weaknesses"]) == 3
        assert result["ok"]["priority_focus"] == "content"
    
    def test_detect_cliches_function(self, monkeypatch):
        """Test detect_cliches convenience function."""
        fake_output = {
            "cliches_found": [
                {
                    "text_excerpt": "I learned that",
                    "cliche_type": "overused_phrase",
                    "severity": 3,
                    "frequency": 1,
                    "alternative_suggestion": "Show the learning through actions"
                }
            ],
            "total_cliches": 1,
            "uniqueness_score": 0.8,
            "overall_assessment": "Mostly original with one minor cliché"
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = detect_cliches("Sample essay text")
        assert len(result["ok"]["cliches_found"]) == 1
        assert result["ok"]["uniqueness_score"] == 0.8
    
    def test_check_alignment_function(self, monkeypatch):
        """Test check_alignment convenience function."""
        fake_output = {
            "alignment_score": 8.0,
            "requirements_analysis": [
                {
                    "requirement": "Answer the question",
                    "addressed": True,
                    "quality": 2,
                    "evidence": "Directly addresses prompt"
                }
            ],
            "missing_elements": [],
            "is_fully_aligned": True,
            "improvement_priority": "None needed"
        }
        _mock_llm(monkeypatch, fake_output)
        
        result = check_alignment("Sample essay text", "Sample prompt")
        assert result["ok"]["alignment_score"] == 8.0
        assert result["ok"]["is_fully_aligned"] is True


class TestPydanticValidation:
    """Test Pydantic schema validation for tool responses."""
    
    def test_essay_scoring_result_validation(self):
        """Test EssayScoringResult validation."""
        from essay_agent.tools.evaluation_tools import EssayScoringResult, EssayScores
        
        # Valid data
        valid_data = {
            "scores": {
                "clarity": 8,
                "insight": 7,
                "structure": 9,
                "voice": 6,
                "prompt_fit": 8
            },
            "overall_score": 7.6,
            "is_strong_essay": True,
            "feedback": "Good essay with strong structure."
        }
        
        result = EssayScoringResult(**valid_data)
        assert result.overall_score == 7.6
        assert result.is_strong_essay is True
        
        # Invalid overall_score (doesn't match average)
        invalid_data = valid_data.copy()
        invalid_data["overall_score"] = 9.0  # Should be 7.6
        
        with pytest.raises(ValueError, match="overall_score"):
            EssayScoringResult(**invalid_data)
        
        # Invalid is_strong_essay (doesn't match score)
        invalid_data = valid_data.copy()
        invalid_data["is_strong_essay"] = False  # Should be True for score 7.6
        
        with pytest.raises(ValueError, match="is_strong_essay"):
            EssayScoringResult(**invalid_data)
    
    def test_weakness_highlight_result_validation(self):
        """Test WeaknessHighlightResult validation."""
        from essay_agent.tools.evaluation_tools import WeaknessHighlightResult, WeaknessItem
        
        # Valid data with 3 weaknesses
        valid_data = {
            "weaknesses": [
                {
                    "text_excerpt": "I learned things",
                    "weakness_type": "content",
                    "severity": 4,
                    "explanation": "Too vague",
                    "improvement_advice": "Be more specific"
                },
                {
                    "text_excerpt": "It was good",
                    "weakness_type": "style",
                    "severity": 3,
                    "explanation": "Generic language",
                    "improvement_advice": "Use better adjectives"
                },
                {
                    "text_excerpt": "The end",
                    "weakness_type": "structure",
                    "severity": 5,
                    "explanation": "Abrupt conclusion",
                    "improvement_advice": "Connect to opening"
                }
            ],
            "overall_weakness_count": 3,
            "priority_focus": "content"
        }
        
        result = WeaknessHighlightResult(**valid_data)
        assert len(result.weaknesses) == 3
        assert result.overall_weakness_count == 3
        
        # Invalid weakness count (too few)
        invalid_data = valid_data.copy()
        invalid_data["weaknesses"] = invalid_data["weaknesses"][:2]  # Only 2 weaknesses
        
        with pytest.raises(ValueError, match="Must identify 3-5 weaknesses"):
            WeaknessHighlightResult(**invalid_data)
        
        # Invalid weakness type
        invalid_data = valid_data.copy()
        invalid_data["weaknesses"][0]["weakness_type"] = "invalid_type"
        
        with pytest.raises(ValueError, match="weakness_type must be one of"):
            WeaknessHighlightResult(**invalid_data) 