"""Tests for QA validation pipeline."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from essay_agent.planner import Phase
from essay_agent.workflows.base import WorkflowState
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
from essay_agent.workflows.qa_pipeline import (
    QAValidationPipeline,
    QAValidationNode,
    QAGateNode,
    should_run_qa_validation,
    get_qa_validation_recommendations,
)


class TestQAValidationPipeline:
    """Test QA validation pipeline functionality."""
    
    def setup_method(self):
        self.pipeline = QAValidationPipeline()
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_success(self):
        """Test successful execution of complete pipeline."""
        essay = "This is a well-written, original essay without any issues."
        context = {
            "essay_prompt": "Test prompt",
            "outline": {"hook": "test", "context": "test"},
            "word_limit": 650
        }
        
        # Mock all validators to return successful results
        mock_results = []
        for validator_name in ["plagiarism", "cliche_detection", "outline_alignment", "final_polish"]:
            mock_result = ValidationResult(
                validator_name=validator_name,
                passed=True,
                score=0.9,
                issues=[],
                execution_time=1.0,
                metadata={}
            )
            mock_results.append(mock_result)
        
        # Mock validator validate methods
        with patch.object(self.pipeline.validators[0], 'validate', return_value=mock_results[0]), \
             patch.object(self.pipeline.validators[1], 'validate', return_value=mock_results[1]), \
             patch.object(self.pipeline.validators[2], 'validate', return_value=mock_results[2]), \
             patch.object(self.pipeline.validators[3], 'validate', return_value=mock_results[3]):
            
            result = await self.pipeline.run_validation(essay, context)
            
            assert isinstance(result, ComprehensiveValidationResult)
            assert result.overall_status == "pass"
            assert result.overall_score == 0.9
            assert len(result.stage_results) == 4
            assert len(result.recommendations) == 0
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_with_failures(self):
        """Test pipeline behavior with validation failures."""
        essay = "This essay has multiple issues that need to be addressed."
        context = {"essay_prompt": "Test prompt"}
        
        # Mock mixed results - some pass, some fail
        plagiarism_result = ValidationResult(
            validator_name="plagiarism",
            passed=False,
            score=0.3,
            issues=[
                ValidationIssue(
                    issue_type="plagiarism",
                    severity=ValidationSeverity.HIGH,
                    message="Potential plagiarism detected",
                    text_excerpt="copied text",
                    suggestion="Rewrite in your own words"
                )
            ],
            execution_time=1.0,
            metadata={}
        )
        
        cliche_result = ValidationResult(
            validator_name="cliche_detection",
            passed=False,
            score=0.5,
            issues=[
                ValidationIssue(
                    issue_type="cliche",
                    severity=ValidationSeverity.MEDIUM,
                    message="Cliche detected",
                    text_excerpt="changed my life",
                    suggestion="Use more original language"
                )
            ],
            execution_time=1.0,
            metadata={}
        )
        
        outline_result = ValidationResult(
            validator_name="outline_alignment",
            passed=True,
            score=0.8,
            issues=[],
            execution_time=1.0,
            metadata={}
        )
        
        polish_result = ValidationResult(
            validator_name="final_polish",
            passed=True,
            score=0.9,
            issues=[],
            execution_time=1.0,
            metadata={}
        )
        
        mock_results = [plagiarism_result, cliche_result, outline_result, polish_result]
        
        # Mock validator validate methods
        with patch.object(self.pipeline.validators[0], 'validate', return_value=mock_results[0]), \
             patch.object(self.pipeline.validators[1], 'validate', return_value=mock_results[1]), \
             patch.object(self.pipeline.validators[2], 'validate', return_value=mock_results[2]), \
             patch.object(self.pipeline.validators[3], 'validate', return_value=mock_results[3]):
            
            result = await self.pipeline.run_validation(essay, context)
            
            assert result.overall_status == "warning"  # Changed from "fail" to "warning"
            assert result.overall_score == 0.625  # (0.3 + 0.5 + 0.8 + 0.9) / 4
            assert len(result.stage_results) == 4  # Fixed: stage_results instead of validator_results
            assert len(result.critical_issues) == 0  # Fixed: critical_issues property
            assert len(result.recommendations) > 0  # Fixed: recommendations field
    
    @pytest.mark.asyncio
    async def test_pipeline_stops_on_critical_failure(self):
        """Test that pipeline stops when critical failure occurs."""
        essay = "Essay with critical issues"
        context = {"essay_prompt": "Test prompt"}
        
        # Mock critical failure in first validator
        critical_result = ValidationResult(
            validator_name="plagiarism",
            passed=False,
            score=0.0,
            issues=[
                ValidationIssue(
                    issue_type="plagiarism",
                    severity=ValidationSeverity.CRITICAL,
                    message="Critical plagiarism detected",
                    text_excerpt="completely copied text",
                    suggestion="Rewrite entirely"
                )
            ],
            execution_time=1.0,
            metadata={}
        )
        
        with patch.object(self.pipeline.validators[0], 'validate', return_value=critical_result):
            result = await self.pipeline.run_validation(essay, context)
            
            assert result.overall_status == "fail"
            assert len(result.stage_results) == 1  # Should stop after first validator
            assert len(result.critical_issues) == 1
            assert result.critical_issues[0].severity == ValidationSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_pipeline_handles_validator_exceptions(self):
        """Test pipeline handles validator exceptions gracefully."""
        essay = "Test essay"
        context = {"essay_prompt": "Test prompt"}
        
        # Mock first validator to raise exception
        with patch.object(self.pipeline.validators[0], 'validate', side_effect=Exception("Validator error")):
            result = await self.pipeline.run_validation(essay, context)
            
            assert result.overall_status == "fail"
            assert len(result.stage_results) == 1
            assert result.stage_results[0].passed is False
            assert result.stage_results[0].metadata.get("error") == "Validator error"
    
    def test_determine_overall_status(self):
        """Test overall status determination logic."""
        # Test all pass
        all_pass = [
            ValidationResult(validator_name="v1", passed=True, score=0.9, issues=[], execution_time=1.0),
            ValidationResult(validator_name="v2", passed=True, score=0.8, issues=[], execution_time=1.0)
        ]
        assert self.pipeline._determine_overall_status(all_pass) == "pass"
        
        # Test some fail (warning)
        some_fail = [
            ValidationResult(validator_name="v1", passed=False, score=0.6, issues=[], execution_time=1.0),
            ValidationResult(validator_name="v2", passed=True, score=0.8, issues=[], execution_time=1.0)
        ]
        assert self.pipeline._determine_overall_status(some_fail) == "warning"
        
        # Test most fail
        most_fail = [
            ValidationResult(validator_name="v1", passed=False, score=0.4, issues=[], execution_time=1.0),
            ValidationResult(validator_name="v2", passed=False, score=0.3, issues=[], execution_time=1.0)
        ]
        assert self.pipeline._determine_overall_status(most_fail) == "fail"
        
        # Test empty results
        assert self.pipeline._determine_overall_status([]) == "fail"
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        results = [
            ValidationResult(
                validator_name="plagiarism",
                passed=False,
                score=0.3,
                issues=[
                    ValidationIssue(
                        issue_type="plagiarism",
                        severity=ValidationSeverity.HIGH,
                        message="High severity issue",
                        text_excerpt="text",
                        suggestion="Specific suggestion"
                    )
                ],
                execution_time=1.0
            ),
            ValidationResult(
                validator_name="cliche_detection",
                passed=False,
                score=0.5,
                issues=[],
                execution_time=1.0
            )
        ]
        
        recommendations = self.pipeline._generate_recommendations(results)
        
        assert len(recommendations) > 0
        assert "Review flagged sections for originality and add more personal details" in recommendations
        assert "Specific suggestion" in recommendations
        assert "Replace identified cliches with more original and specific language" in recommendations


class TestQAValidationNode:
    """Test QA validation workflow node."""
    
    def setup_method(self):
        self.node = QAValidationNode()
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_essay(self):
        """Test node execution with valid essay."""
        # Create workflow state with essay content
        state = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "context": {
                    "essay_prompt": "Test prompt",
                    "word_limit": 650
                },
                "tool_outputs": {
                    "draft": {
                        "essay_text": "This is a well-written test essay."
                    }
                }
            }
        )
        
        # Mock the validation pipeline
        mock_result = ComprehensiveValidationResult(
            overall_status="pass",
            overall_score=0.9,
            stage_results=[],  # Fixed: stage_results instead of validator_results
            recommendations=[],
            execution_time=1.0
        )
        
        with patch.object(self.node.pipeline, 'run_validation', return_value=mock_result):
            result = await self.node.execute(state)
            
            assert result.phase == Phase.POLISHING
            assert "qa_validation" in result.data["tool_outputs"]
            assert result.data["tool_outputs"]["qa_validation"]["overall_status"] == "pass"
    
    @pytest.mark.asyncio
    async def test_execute_without_essay(self):
        """Test node execution without essay content."""
        # Create workflow state without essay content
        state = WorkflowState(
            phase=Phase.BRAINSTORMING,
            data={"context": {}}
        )
        
        result = await self.node.execute(state)
        
        # Should return unchanged state when no essay content
        assert result.phase == Phase.BRAINSTORMING
        assert result.data == {"context": {}}
    
    def test_get_essay_text_from_various_sources(self):
        """Test essay text extraction from different sources."""
        # Test extraction from polish output
        state_polish = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "polish": {"polished_essay": "polished text"}
                }
            }
        )
        
        essay_text = self.node._get_essay_text(state_polish)
        assert essay_text == "polished text"
        
        # Test extraction from draft output
        state_draft = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "draft": {"essay_text": "draft text"}
                }
            }
        )
        
        essay_text = self.node._get_essay_text(state_draft)
        assert essay_text == "draft text"

        # Test with no essay text
        state_empty = WorkflowState(
            phase=Phase.BRAINSTORMING,
            data={"tool_outputs": {}}
        )
        
        essay_text = self.node._get_essay_text(state_empty)
        assert essay_text is None
    
    def test_prepare_validation_context(self):
        """Test validation context preparation."""
        state = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "context": {
                    "essay_prompt": "Test prompt",
                    "word_limit": 650,
                    "user_profile": {"name": "Test User"}
                },
                "tool_outputs": {
                    "outline": {"hook": "test hook"},
                    "brainstorm": {"selected_story": "test story"}
                }
            }
        )
        
        context = self.node._prepare_validation_context(state)
        
        assert context["essay_prompt"] == "Test prompt"
        assert context["word_limit"] == 650
        assert context["user_profile"]["name"] == "Test User"
        assert context["outline"]["hook"] == "test hook"
        assert context["brainstorm"]["selected_story"] == "test story"
    
    def test_get_name(self):
        """Test node name."""
        assert self.node.get_name() == "qa_validation"


class TestQAGateNode:
    """Test QA gate workflow node."""
    
    def setup_method(self):
        self.gate = QAGateNode(pass_threshold=0.7)
    
    @pytest.mark.asyncio
    async def test_execute_with_passing_validation(self):
        """Test gate execution with passing validation."""
        state = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "qa_validation": {
                        "overall_score": 0.9,
                        "overall_status": "pass",
                        "critical_issues": []
                    }
                }
            }
        )
        
        result = await self.gate.execute(state)
        
        assert result.phase == Phase.POLISHING
        assert result.data.get("next_action") == "complete"
    
    @pytest.mark.asyncio
    async def test_execute_with_failing_validation(self):
        """Test gate execution with failing validation."""
        state = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "qa_validation": {
                        "overall_score": 0.4,
                        "overall_status": "fail",
                        "critical_issues": []
                    }
                }
            }
        )
        
        result = await self.gate.execute(state)
        
        assert result.phase == Phase.POLISHING
        assert result.data.get("next_action") == "revision"
    
    @pytest.mark.asyncio
    async def test_execute_with_critical_issues(self):
        """Test gate execution with critical issues."""
        state = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "qa_validation": {
                        "overall_score": 0.8,
                        "overall_status": "fail",
                        "critical_issues": ["Critical issue 1", "Critical issue 2"]
                    }
                }
            }
        )
        
        result = await self.gate.execute(state)
        
        assert result.phase == Phase.POLISHING
        assert result.data.get("next_action") == "revision"
        assert result.data.get("revision_focus") == "critical_issues"
    
    @pytest.mark.asyncio
    async def test_execute_with_warnings(self):
        """Test gate execution with warnings."""
        state = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "qa_validation": {
                        "overall_score": 0.75,
                        "overall_status": "warning",
                        "critical_issues": []
                    }
                }
            }
        )
        
        result = await self.gate.execute(state)
        
        assert result.phase == Phase.POLISHING
        assert result.data.get("next_action") == "conditional_complete"
    
    @pytest.mark.asyncio
    async def test_execute_without_validation_results(self):
        """Test gate execution without validation results."""
        state = WorkflowState(
            phase=Phase.POLISHING,
            data={"tool_outputs": {}}
        )
        
        result = await self.gate.execute(state)
        
        assert result.phase == Phase.POLISHING
        assert result.data.get("next_action") == "complete"  # Default to complete
    
    def test_get_name(self):
        """Test gate node name."""
        assert self.gate.get_name() == "qa_gate"


class TestQAUtilityFunctions:
    """Test QA utility functions."""
    
    def test_should_run_qa_validation(self):
        """Test QA validation trigger logic."""
        # Test with essay content and advanced phase
        state_ready = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "draft": {"essay_text": "test essay"}
                }
            }
        )
        
        assert should_run_qa_validation(state_ready) is True
        
        # Test with early phase
        state_early = WorkflowState(
            phase=Phase.BRAINSTORMING,
            data={
                "tool_outputs": {
                    "draft": {"essay_text": "test essay"}
                }
            }
        )
        
        assert should_run_qa_validation(state_early) is False
        
        # Test without essay content
        state_no_essay = WorkflowState(
            phase=Phase.POLISHING,
            data={"tool_outputs": {}}
        )
        
        assert should_run_qa_validation(state_no_essay) is False
    
    def test_get_qa_validation_recommendations(self):
        """Test recommendation extraction."""
        state = WorkflowState(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "qa_validation": {
                        "recommendations": ["Fix grammar", "Improve structure"]
                    }
                }
            }
        )
        
        recommendations = get_qa_validation_recommendations(state)
        assert recommendations == ["Fix grammar", "Improve structure"]
        
        # Test with no recommendations
        state_empty = WorkflowState(
            phase=Phase.POLISHING,
            data={"tool_outputs": {}}
        )
        
        recommendations = get_qa_validation_recommendations(state_empty)
        assert recommendations == [] 