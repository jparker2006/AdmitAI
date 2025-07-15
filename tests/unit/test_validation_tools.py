"""Tests for validation tools."""

import json
import pytest
from unittest.mock import MagicMock, patch

from essay_agent.tools.validation_tools import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    ComprehensiveValidationResult,
    PlagiarismValidator,
    ClicheDetectionValidator,
    OutlineAlignmentValidator,
    FinalPolishValidator,
)


class TestPlagiarismValidator:
    """Test plagiarism detection validator."""

    def setup_method(self):
        self.validator = PlagiarismValidator()

    def test_clean_text_passes(self):
        """Test that original text passes plagiarism check."""
        essay = """
        My grandmother's hands tell a story of resilience. Every wrinkle represents
        a challenge overcome, every scar a lesson learned. When I was twelve, she
        taught me to make empanadas using a recipe passed down through generations.
        As we worked together in her small kitchen, I realized that tradition isn't
        just about preserving the past—it's about creating connections that transcend time.
        """

        context = {"essay_prompt": "Describe a meaningful tradition"}

        # Mock LLM response for clean text
        mock_response = {
            "similarity_score": 0.05,
            "flagged_sections": [],
            "authenticity_score": 0.95,
            "overall_assessment": "pass",
            "recommendations": []
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is True
            assert result.score > 0.7
            assert len(result.issues) == 0

    def test_plagiarized_text_fails(self):
        """Test that plagiarized text is detected."""
        essay = """
        Education is the most powerful weapon which you can use to change the world.
        It is through education that we can break the cycle of poverty and create
        opportunities for future generations. The role of education in society cannot
        be overstated, as it serves as the foundation for progress and development.
        """

        context = {"essay_prompt": "Describe your educational goals"}

        # Mock LLM response for plagiarized text
        mock_response = {
            "similarity_score": 0.75,
            "flagged_sections": [
                {
                    "text": "Education is the most powerful weapon which you can use to change the world",
                    "reason": "Famous quote from Nelson Mandela",
                    "severity": "critical"
                }
            ],
            "authenticity_score": 0.25,
            "overall_assessment": "fail",
            "recommendations": ["Use your own words to express ideas about education"]
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is False
            assert result.score < 0.7
            assert len(result.issues) > 0

    def test_fallback_on_llm_failure(self):
        """Test fallback behavior when LLM fails."""
        essay = "This is a test essay with generic phrases like 'this experience taught me' and 'i learned that'."
        context = {}

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM API error")

            result = self.validator.validate(essay, context)

            assert result.passed is False
            assert result.score == 0.5
            assert len(result.issues) == 1
            assert "validation_error" in result.issues[0].issue_type


class TestClicheDetectionValidator:
    """Test cliche detection validator."""

    def setup_method(self):
        self.validator = ClicheDetectionValidator()

    def test_cliche_detection(self):
        """Test detection of common cliches."""
        essay = """
        This experience changed my life in ways I never imagined. I learned that
        hard work pays off and that I should never give up on my dreams. It taught
        me to step out of my comfort zone and embrace new challenges. Through this
        journey of discovery, I found my passion for helping others and making a
        difference in the world.
        """

        context = {"essay_prompt": "Describe a transformative experience"}

        # Mock LLM response detecting cliches
        mock_response = {
            "cliches_found": [
                {
                    "text": "changed my life",
                    "severity": 5,
                    "context": "This experience changed my life in ways I never imagined",
                    "suggestion": "Describe specific ways the experience affected you",
                    "explanation": "Extremely overused phrase in college essays"
                },
                {
                    "text": "hard work pays off",
                    "severity": 3,
                    "context": "I learned that hard work pays off",
                    "suggestion": "Explain what you learned through your efforts",
                    "explanation": "Common motivational cliche"
                },
                {
                    "text": "step out of my comfort zone",
                    "severity": 3,
                    "context": "It taught me to step out of my comfort zone",
                    "suggestion": "Describe the specific challenge you faced",
                    "explanation": "Overused phrase about facing challenges"
                }
            ],
            "cliche_density": 0.4,
            "overall_originality": 0.6,
            "assessment": "fail",
            "recommendations": ["Replace cliches with more specific, personal language"]
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is False
            assert result.score < 0.7
            assert len(result.issues) > 0

    def test_original_text_passes(self):
        """Test that original text without cliches passes."""
        essay = """
        The smell of cardamom and cinnamon filled our small apartment every Sunday
        morning. My mother would wake up at 5 AM to prepare elaborate breakfast
        spreads for our extended family gatherings. Initially, I resented these
        weekly obligations, preferring to sleep in like my American friends. However,
        as I grew older, I began to appreciate the intricate stories shared over
        steaming cups of chai and the way my grandmother's eyes lit up when
        describing her childhood in Mumbai.
        """

        context = {"essay_prompt": "Describe a family tradition"}

        # Mock LLM response for original text
        mock_response = {
            "cliches_found": [],
            "cliche_density": 0.05,
            "overall_originality": 0.95,
            "assessment": "pass",
            "recommendations": []
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is True
            assert result.score > 0.7
            assert len(result.issues) == 0

    def test_basic_cliche_detection_fallback(self):
        """Test basic fallback cliche detection."""
        essay = "This changed my life. I learned that hard work pays off."
        context = {}

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM error")

            result = self.validator.validate(essay, context)

            # Should fall back to basic detection
            assert result.passed is False
            assert result.score == 0.5


class TestOutlineAlignmentValidator:
    """Test outline alignment validator."""

    def setup_method(self):
        self.validator = OutlineAlignmentValidator()

    def test_perfect_alignment(self):
        """Test perfectly aligned essay scores highly."""
        essay = """
        The moment I stepped into the robotics lab, I knew I was entering uncharted
        territory. As the only freshman on the team, I felt overwhelmed by the
        complexity of the mechanisms and the expertise of my teammates. The real
        challenge came when our robot failed spectacularly during the first
        competition, short-circuiting on stage in front of hundreds of spectators.

        Rather than giving up, I spent the next three months meticulously studying
        circuit diagrams and practicing soldering techniques. I learned to embrace
        failure as a teacher, not an enemy. By the regional championship, I had
        become the team's lead electrician and our robot performed flawlessly.

        This experience taught me that expertise isn't about never failing—it's
        about learning from every mistake and persistently improving. I now approach
        every challenge with the same methodical curiosity I developed in that lab.
        """

        outline = {
            "hook": "The moment I stepped into the robotics lab",
            "context": "First-year student joining experienced robotics team",
            "conflict": "Robot failed during competition due to electrical issues",
            "growth": "Spent months learning circuit design and soldering",
            "reflection": "Learned that expertise comes from learning from failure"
        }

        context = {"outline": outline, "essay_prompt": "Describe a challenge you overcame"}

        # Mock LLM response for perfect alignment
        mock_response = {
            "section_coverage": {
                "hook": {
                    "coverage_percentage": 95,
                    "found_content": "The moment I stepped into the robotics lab",
                    "assessment": "well_covered"
                },
                "context": {
                    "coverage_percentage": 90,
                    "found_content": "As the only freshman on the team",
                    "assessment": "well_covered"
                },
                "conflict": {
                    "coverage_percentage": 90,
                    "found_content": "robot failed spectacularly during the first competition",
                    "assessment": "well_covered"
                },
                "growth": {
                    "coverage_percentage": 85,
                    "found_content": "spent the next three months meticulously studying",
                    "assessment": "well_covered"
                },
                "reflection": {
                    "coverage_percentage": 90,
                    "found_content": "expertise isn't about never failing",
                    "assessment": "well_covered"
                }
            },
            "overall_alignment": 0.9,
            "structural_flow": 0.95,
            "missing_elements": [],
            "recommendations": []
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is True
            assert result.score > 0.7
            assert len(result.issues) == 0

    def test_poor_alignment(self):
        """Test poorly aligned essay scores low."""
        essay = """
        I like science and math. They are interesting subjects that I enjoy studying.
        I want to become an engineer someday because engineering is a good career.
        I think I would be good at it because I am hardworking and dedicated.
        """

        outline = {
            "hook": "Describe a specific moment when you discovered your passion for engineering",
            "context": "Explain the circumstances that led to this discovery",
            "conflict": "Describe a challenge you faced in pursuing this interest",
            "growth": "Explain how you overcame the challenge and what you learned",
            "reflection": "Reflect on how this experience shapes your future goals"
        }

        context = {"outline": outline, "essay_prompt": "Describe your passion for engineering"}

        # Mock LLM response for poor alignment
        mock_response = {
            "section_coverage": {
                "hook": {
                    "coverage_percentage": 10,
                    "found_content": "I like science and math",
                    "assessment": "missing"
                },
                "context": {
                    "coverage_percentage": 20,
                    "found_content": "They are interesting subjects",
                    "assessment": "missing"
                },
                "conflict": {
                    "coverage_percentage": 0,
                    "found_content": "",
                    "assessment": "missing"
                },
                "growth": {
                    "coverage_percentage": 0,
                    "found_content": "",
                    "assessment": "missing"
                },
                "reflection": {
                    "coverage_percentage": 30,
                    "found_content": "I want to become an engineer",
                    "assessment": "partially_covered"
                }
            },
            "overall_alignment": 0.2,
            "structural_flow": 0.1,
            "missing_elements": ["Specific discovery moment", "Challenges faced", "Growth through overcoming challenges"],
            "recommendations": ["Add specific examples and personal experiences"]
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is False
            assert result.score < 0.7
            assert len(result.issues) > 0

    def test_missing_outline_error(self):
        """Test error handling when outline is missing."""
        essay = "Test essay content"
        context = {}  # No outline provided

        result = self.validator.validate(essay, context)

        assert result.passed is False
        assert result.score == 0.5
        assert len(result.issues) == 1
        assert "outline" in result.issues[0].message.lower()


class TestFinalPolishValidator:
    """Test final polish validator."""

    def setup_method(self):
        self.validator = FinalPolishValidator()

    def test_polished_essay_passes(self):
        """Test that well-polished essay passes validation."""
        essay = """
        The aroma of my grandmother's kitchen always transported me back to my
        childhood in Seoul. Every Sunday, she would prepare kimchi jjigae using
        a recipe passed down through three generations. As I watched her skilled
        hands chop vegetables with practiced precision, I realized that cooking
        was more than mere sustenance—it was our family's way of preserving
        cultural identity across continents.

        When my family immigrated to America, I initially felt embarrassed by
        our traditional foods. I longed for peanut butter sandwiches and apple
        pie, anything that would help me blend in with my American classmates.
        However, as I grew older, I began to appreciate the complexity of flavors
        in Korean cuisine and the stories embedded in each dish.

        Now, as I prepare for college, I understand that my multicultural
        background is not a burden to hide but a strength to celebrate. I plan
        to study international business, hoping to bridge the gap between Eastern
        and Western cultures in the global marketplace. Just as my grandmother's
        recipes connect me to my heritage, I want to help others find common
        ground across cultural divides.
        """

        context = {
            "word_limit": 650,
            "essay_prompt": "Describe how your background influences your goals",
            "user_profile": {}
        }

        # Mock LLM response for polished essay
        mock_response = {
            "technical_issues": [],
            "word_count": {
                "actual": 247,
                "limit": 650,
                "status": "within",
                "variance": 0
            },
            "prompt_adherence": {
                "score": 0.95,
                "missing_elements": [],
                "assessment": "fully_addresses"
            },
            "voice_consistency": 0.9,
            "overall_polish": 0.95,
            "submission_ready": True,
            "critical_issues": [],
            "recommendations": []
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is True
            assert result.score > 0.8
            assert len(result.issues) == 0

    def test_overlength_essay_fails(self):
        """Test that essay exceeding word limit fails validation."""
        # Create a long essay that exceeds word limit
        essay = " ".join(["word"] * 700)  # 700 words

        context = {
            "word_limit": 650,
            "essay_prompt": "Test prompt",
            "user_profile": {}
        }

        # Mock LLM response for overlength essay
        mock_response = {
            "technical_issues": [],
            "word_count": {
                "actual": 700,
                "limit": 650,
                "status": "over",
                "variance": 50
            },
            "prompt_adherence": {
                "score": 0.8,
                "missing_elements": [],
                "assessment": "fully_addresses"
            },
            "voice_consistency": 0.8,
            "overall_polish": 0.7,
            "submission_ready": False,
            "critical_issues": ["Essay exceeds word limit"],
            "recommendations": ["Reduce word count to meet requirements"]
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is False
            assert result.score < 0.8
            assert len(result.issues) > 0

    def test_grammar_issues_detected(self):
        """Test detection of grammar and technical issues."""
        essay = """
        This experiance changed my life in many ways. I learned alot about myself
        and others, and it effected how I view the world. Their were many challenges
        that I faced, but I overcame them threw hard work and dedication.
        """

        context = {
            "word_limit": 650,
            "essay_prompt": "Describe a transformative experience",
            "user_profile": {}
        }

        # Mock LLM response detecting grammar issues
        mock_response = {
            "technical_issues": [
                {
                    "type": "spelling",
                    "text": "experiance",
                    "correction": "experience",
                    "severity": "medium"
                },
                {
                    "type": "spelling",
                    "text": "alot",
                    "correction": "a lot",
                    "severity": "medium"
                },
                {
                    "type": "grammar",
                    "text": "effected",
                    "correction": "affected",
                    "severity": "medium"
                },
                {
                    "type": "grammar",
                    "text": "Their were",
                    "correction": "There were",
                    "severity": "medium"
                },
                {
                    "type": "spelling",
                    "text": "threw",
                    "correction": "through",
                    "severity": "medium"
                }
            ],
            "word_count": {
                "actual": 42,
                "limit": 650,
                "status": "under",
                "variance": -608
            },
            "prompt_adherence": {
                "score": 0.6,
                "missing_elements": ["Specific details about the experience"],
                "assessment": "partially_addresses"
            },
            "voice_consistency": 0.6,
            "overall_polish": 0.4,
            "submission_ready": False,
            "critical_issues": [],
            "recommendations": ["Fix grammar and spelling errors", "Add more specific details"]
        }

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = self.validator.validate(essay, context)

            assert result.passed is False
            assert result.score < 0.8
            assert len(result.issues) > 0

    def test_basic_polish_check_fallback(self):
        """Test basic fallback polish check."""
        essay = "This is a short essay with no major issues."
        context = {"word_limit": 650, "essay_prompt": "Test prompt"}

        with patch('essay_agent.tools.validation_tools.call_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM error")

            result = self.validator.validate(essay, context)

            # Should fall back to basic checks
            assert result.passed is False
            assert result.score == 0.5


class TestValidationDataModels:
    """Test validation data models."""
    
    def test_validation_issue_creation(self):
        """Test ValidationIssue model creation."""
        issue = ValidationIssue(
            issue_type="test",
            severity=ValidationSeverity.HIGH,
            message="Test message",
            text_excerpt="Test excerpt",
            suggestion="Test suggestion"
        )
        
        assert issue.issue_type == "test"
        assert issue.severity == ValidationSeverity.HIGH
        assert issue.message == "Test message"
        assert issue.text_excerpt == "Test excerpt"
        assert issue.suggestion == "Test suggestion"
    
    def test_validation_result_critical_failure(self):
        """Test ValidationResult critical failure detection."""
        critical_issue = ValidationIssue(
            issue_type="critical",
            severity=ValidationSeverity.CRITICAL,
            message="Critical error",
            text_excerpt="Error text"
        )
        
        non_critical_issue = ValidationIssue(
            issue_type="minor",
            severity=ValidationSeverity.LOW,
            message="Minor issue",
            text_excerpt="Issue text"
        )
        
        result_with_critical = ValidationResult(
            validator_name="test",
            passed=False,
            score=0.0,
            issues=[critical_issue, non_critical_issue],
            execution_time=1.0
        )
        
        result_without_critical = ValidationResult(
            validator_name="test",
            passed=True,
            score=1.0,
            issues=[non_critical_issue],
            execution_time=1.0
        )
        
        assert result_with_critical.is_critical_failure() is True
        assert result_without_critical.is_critical_failure() is False 