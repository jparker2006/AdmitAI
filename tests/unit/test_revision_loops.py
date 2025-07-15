"""Unit tests for revision loop functionality.

Tests cover RevisionLoopController, RevisionTracker, targeted feedback generation,
and workflow integration.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
import time

from essay_agent.workflows.revision_loops import (
    RevisionLoopController,
    RevisionTracker,
    RevisionProgress,
    RevisionLoopNode,
    RevisionQualityGate,
    create_revision_controller,
    create_quality_gate,
    execute_intelligent_revision_loop,
)
from essay_agent.workflows.base import WorkflowState
from essay_agent.planner import EssayPlan, Phase


class TestRevisionProgress:
    """Test RevisionProgress dataclass functionality."""
    
    def test_initialization(self):
        """Test basic initialization."""
        progress = RevisionProgress(
            attempt_number=1,
            previous_score=6.0,
            current_score=7.5,
            score_improvement=1.5,
            focus_areas=["clarity", "structure"],
            changes_made=["Improved transitions", "Added examples"],
            time_taken=45.0
        )
        
        assert progress.attempt_number == 1
        assert progress.previous_score == 6.0
        assert progress.current_score == 7.5
        assert progress.score_improvement == 1.5
        assert progress.focus_areas == ["clarity", "structure"]
        assert progress.changes_made == ["Improved transitions", "Added examples"]
        assert progress.time_taken == 45.0
    
    def test_improvement_percentage(self):
        """Test improvement percentage calculation."""
        progress = RevisionProgress(
            attempt_number=1,
            previous_score=6.0,
            current_score=7.5,
            score_improvement=1.5,
            focus_areas=[],
            changes_made=[],
            time_taken=0.0
        )
        
        assert progress.improvement_percentage == 25.0
        
        # Test with zero previous score
        progress.previous_score = 0.0
        assert progress.improvement_percentage == 0.0
    
    def test_is_improvement(self):
        """Test improvement detection."""
        progress = RevisionProgress(
            attempt_number=1,
            previous_score=6.0,
            current_score=7.5,
            score_improvement=1.5,
            focus_areas=[],
            changes_made=[],
            time_taken=0.0
        )
        
        assert progress.is_improvement is True
        
        # Test no improvement
        progress.score_improvement = 0.0
        assert progress.is_improvement is False
        
        # Test negative improvement
        progress.score_improvement = -0.5
        assert progress.is_improvement is False
    
    def test_is_significant_improvement(self):
        """Test significant improvement detection."""
        # Test significant by score threshold
        progress = RevisionProgress(
            attempt_number=1,
            previous_score=6.0,
            current_score=7.0,
            score_improvement=1.0,
            focus_areas=[],
            changes_made=[],
            time_taken=0.0
        )
        
        assert progress.is_significant_improvement is True
        
        # Test significant by percentage threshold
        progress = RevisionProgress(
            attempt_number=1,
            previous_score=6.0,
            current_score=6.4,
            score_improvement=0.4,
            focus_areas=[],
            changes_made=[],
            time_taken=0.0
        )
        
        assert progress.is_significant_improvement is False
        
        # Test percentage threshold
        progress.score_improvement = 0.4  # 6.67% improvement
        assert progress.is_significant_improvement is True


class TestRevisionTracker:
    """Test RevisionTracker functionality."""
    
    def test_initialization(self):
        """Test basic initialization."""
        tracker = RevisionTracker()
        
        assert tracker.attempts == []
        assert tracker.start_time > 0
        assert tracker.total_time == 0.0
    
    def test_track_attempt(self):
        """Test tracking revision attempts."""
        tracker = RevisionTracker()
        
        progress = RevisionProgress(
            attempt_number=1,
            previous_score=6.0,
            current_score=7.0,
            score_improvement=1.0,
            focus_areas=["clarity"],
            changes_made=["Better transitions"],
            time_taken=30.0
        )
        
        tracker.track_attempt(progress)
        
        assert len(tracker.attempts) == 1
        assert tracker.attempts[0] == progress
        assert tracker.total_time > 0
    
    def test_get_progress_summary_empty(self):
        """Test progress summary with no attempts."""
        tracker = RevisionTracker()
        summary = tracker.get_progress_summary()
        
        expected = {
            "total_attempts": 0,
            "total_improvement": 0.0,
            "average_time_per_attempt": 0.0,
            "final_score": 0.0,
            "initial_score": 0.0,
            "improvement_trend": "none"
        }
        
        assert summary == expected
    
    def test_get_progress_summary_with_attempts(self):
        """Test progress summary with attempts."""
        tracker = RevisionTracker()
        
        # Add first attempt
        progress1 = RevisionProgress(
            attempt_number=1,
            previous_score=6.0,
            current_score=7.0,
            score_improvement=1.0,
            focus_areas=["clarity"],
            changes_made=["Better transitions"],
            time_taken=30.0
        )
        tracker.track_attempt(progress1)
        
        # Add second attempt
        progress2 = RevisionProgress(
            attempt_number=2,
            previous_score=7.0,
            current_score=8.0,
            score_improvement=1.0,
            focus_areas=["structure"],
            changes_made=["Better conclusion"],
            time_taken=25.0
        )
        tracker.track_attempt(progress2)
        
        summary = tracker.get_progress_summary()
        
        assert summary["total_attempts"] == 2
        assert summary["total_improvement"] == 2.0  # 8.0 - 6.0
        assert summary["final_score"] == 8.0
        assert summary["initial_score"] == 6.0
        assert summary["improvement_trend"] == "improving"
        assert summary["successful_attempts"] == 2
        assert summary["significant_improvements"] == 2
    
    def test_get_latest_attempt(self):
        """Test getting latest attempt."""
        tracker = RevisionTracker()
        
        # No attempts
        assert tracker.get_latest_attempt() is None
        
        # Add attempts
        progress1 = RevisionProgress(1, 6.0, 7.0, 1.0, [], [], 30.0)
        progress2 = RevisionProgress(2, 7.0, 8.0, 1.0, [], [], 25.0)
        
        tracker.track_attempt(progress1)
        tracker.track_attempt(progress2)
        
        assert tracker.get_latest_attempt() == progress2
    
    def test_is_plateauing(self):
        """Test plateauing detection."""
        tracker = RevisionTracker()
        
        # Not enough attempts
        assert tracker.is_plateauing() is False
        
        # Add attempts with small improvements
        progress1 = RevisionProgress(1, 6.0, 6.05, 0.05, [], [], 30.0)
        progress2 = RevisionProgress(2, 6.05, 6.08, 0.03, [], [], 25.0)
        
        tracker.track_attempt(progress1)
        tracker.track_attempt(progress2)
        
        assert tracker.is_plateauing() is True
        
        # Add significant improvement
        progress3 = RevisionProgress(3, 6.08, 7.0, 0.92, [], [], 35.0)
        tracker.track_attempt(progress3)
        
        assert tracker.is_plateauing() is False


class TestRevisionLoopController:
    """Test RevisionLoopController functionality."""
    
    def test_initialization(self):
        """Test basic initialization."""
        controller = RevisionLoopController()
        
        assert controller.max_attempts == 3
        assert controller.target_score == 8.0
        assert controller.min_improvement == 0.2
        assert isinstance(controller.tracker, RevisionTracker)
    
    def test_initialization_with_params(self):
        """Test initialization with custom parameters."""
        controller = RevisionLoopController(
            max_attempts=5,
            target_score=7.5,
            min_improvement=0.3
        )
        
        assert controller.max_attempts == 5
        assert controller.target_score == 7.5
        assert controller.min_improvement == 0.3
    
    @pytest.mark.asyncio
    async def test_should_continue_revision_max_attempts(self):
        """Test revision continuation with max attempts."""
        controller = RevisionLoopController(max_attempts=3)
        
        # Create mock state
        state = MagicMock()
        state.revision_attempts = 3
        state.get_evaluation_score.return_value = 6.0
        
        # Mock tracker
        controller.tracker.is_plateauing.return_value = False
        
        should_continue = await controller.should_continue_revision(state)
        assert should_continue is False
    
    @pytest.mark.asyncio
    async def test_should_continue_revision_target_reached(self):
        """Test revision continuation with target score reached."""
        controller = RevisionLoopController(target_score=8.0)
        
        # Create mock state
        state = MagicMock()
        state.revision_attempts = 1
        state.get_evaluation_score.return_value = 8.5
        
        # Mock tracker
        controller.tracker.is_plateauing.return_value = False
        
        should_continue = await controller.should_continue_revision(state)
        assert should_continue is False
    
    @pytest.mark.asyncio
    async def test_should_continue_revision_plateauing(self):
        """Test revision continuation with plateauing."""
        controller = RevisionLoopController()
        
        # Create mock state
        state = MagicMock()
        state.revision_attempts = 1
        state.get_evaluation_score.return_value = 6.0
        
        # Mock tracker to return plateauing
        controller.tracker.is_plateauing.return_value = True
        
        should_continue = await controller.should_continue_revision(state)
        assert should_continue is False
    
    @pytest.mark.asyncio
    async def test_should_continue_revision_continue(self):
        """Test revision continuation when should continue."""
        controller = RevisionLoopController()
        
        # Create mock state
        state = MagicMock()
        state.revision_attempts = 1
        state.get_evaluation_score.return_value = 6.0
        
        # Mock tracker
        controller.tracker.is_plateauing.return_value = False
        
        should_continue = await controller.should_continue_revision(state)
        assert should_continue is True
    
    def test_get_revision_focus_no_evaluation(self):
        """Test revision focus generation without evaluation."""
        controller = RevisionLoopController()
        
        focus = controller.get_revision_focus({})
        assert focus == "Focus on overall clarity and structure"
        
        focus = controller.get_revision_focus({"no_scores": True})
        assert focus == "Focus on overall clarity and structure"
    
    def test_get_revision_focus_with_evaluation(self):
        """Test revision focus generation with evaluation."""
        controller = RevisionLoopController()
        
        evaluation_result = {
            "scores": {
                "clarity": 5,
                "insight": 6,
                "structure": 4,
                "voice": 7,
                "prompt_fit": 6
            },
            "feedback": "Essay needs better flow and examples"
        }
        
        focus = controller.get_revision_focus(evaluation_result)
        
        # Should focus on lowest scoring dimensions
        assert "structure" in focus
        assert "clarity" in focus
        assert "Current: 4/10" in focus
        assert "Current: 5/10" in focus
        assert "Essay needs better flow and examples" in focus
    
    def test_identify_weak_areas(self):
        """Test weak areas identification."""
        controller = RevisionLoopController()
        
        evaluation_result = {
            "scores": {
                "clarity": 5,
                "insight": 6,
                "structure": 4,
                "voice": 7,
                "prompt_fit": 6
            }
        }
        
        weak_areas = controller._identify_weak_areas(evaluation_result)
        
        # Should return sorted by score (ascending), limited to 3
        assert len(weak_areas) == 3
        assert weak_areas[0] == ("structure", 4)
        assert weak_areas[1] == ("clarity", 5)
        assert weak_areas[2] == ("insight", 6)
    
    def test_generate_revision_prompt(self):
        """Test revision prompt generation."""
        controller = RevisionLoopController()
        
        weak_areas = [("structure", 4), ("clarity", 5)]
        evaluation_result = {"feedback": "Needs improvement"}
        
        prompt = controller._generate_revision_prompt(weak_areas, evaluation_result)
        
        assert "Strengthen narrative arc" in prompt
        assert "Current: 4/10" in prompt
        assert "Improve logical flow" in prompt
        assert "Current: 5/10" in prompt
        assert "Needs improvement" in prompt
    
    @pytest.mark.asyncio
    async def test_execute_revision_cycle_no_draft(self):
        """Test revision cycle execution with no draft."""
        controller = RevisionLoopController()
        
        # Create mock state with no draft
        state = MagicMock()
        state.get_current_draft.return_value = ""
        state.errors = []
        
        result = await controller.execute_revision_cycle(state)
        
        assert result["revision_completed"] is False
        assert "No draft available" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_execute_revision_cycle_evaluation_failure(self):
        """Test revision cycle execution with evaluation failure."""
        controller = RevisionLoopController()
        
        # Create mock state
        state = MagicMock()
        state.get_current_draft.return_value = "Test draft"
        state.get_essay_prompt.return_value = "Test prompt"
        state.errors = []
        
        # Mock evaluation failure
        controller._evaluate_draft = AsyncMock(return_value={"error": "Evaluation failed"})
        
        result = await controller.execute_revision_cycle(state)
        
        assert result["revision_completed"] is False
        assert "Evaluation failed" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_execute_revision_cycle_no_revision_needed(self):
        """Test revision cycle when no revision is needed."""
        controller = RevisionLoopController()
        
        # Create mock state
        state = MagicMock()
        state.get_current_draft.return_value = "Test draft"
        state.get_essay_prompt.return_value = "Test prompt"
        state.errors = []
        
        # Mock evaluation with high score
        controller._evaluate_draft = AsyncMock(return_value={"overall_score": 8.5})
        controller.should_continue_revision = AsyncMock(return_value=False)
        
        result = await controller.execute_revision_cycle(state)
        
        assert result["revision_completed"] is True
        assert result["revision_needed"] is False
        assert result["final_score"] == 8.5
    
    @pytest.mark.asyncio
    async def test_execute_revision_cycle_success(self):
        """Test successful revision cycle execution."""
        controller = RevisionLoopController()
        
        # Create mock state
        state = MagicMock()
        state.get_current_draft.return_value = "Test draft"
        state.get_essay_prompt.return_value = "Test prompt"
        state.errors = []
        state.revision_attempts = 1
        state.data = {"tool_outputs": {}}
        state.metadata = {}
        
        # Mock evaluation results
        initial_eval = {
            "overall_score": 6.0,
            "scores": {"clarity": 5, "insight": 6, "structure": 6, "voice": 7, "prompt_fit": 6},
            "feedback": "Needs improvement"
        }
        
        final_eval = {
            "overall_score": 7.5,
            "scores": {"clarity": 7, "insight": 7, "structure": 7, "voice": 8, "prompt_fit": 8},
            "feedback": "Much better"
        }
        
        revision_result = {
            "revised_draft": "Improved draft",
            "changes": ["Better transitions", "More examples"]
        }
        
        controller._evaluate_draft = AsyncMock(side_effect=[initial_eval, final_eval])
        controller._execute_revision = AsyncMock(return_value=revision_result)
        controller.should_continue_revision = AsyncMock(side_effect=[True, False])
        
        result = await controller.execute_revision_cycle(state)
        
        assert result["revision_completed"] is True
        assert result["revision_needed"] is True
        assert result["progress"].score_improvement == 1.5
        assert result["progress"].attempt_number == 2
        assert result["should_continue"] is False
    
    @pytest.mark.asyncio
    async def test_evaluate_draft(self):
        """Test draft evaluation."""
        controller = RevisionLoopController()
        
        mock_result = {"overall_score": 7.0, "feedback": "Good essay"}
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY') as mock_registry:
            mock_registry.acall = AsyncMock(return_value=mock_result)
            
            result = await controller._evaluate_draft("Test draft", "Test prompt")
            
            assert result == mock_result
            mock_registry.acall.assert_called_once_with(
                "essay_scoring",
                essay_text="Test draft",
                essay_prompt="Test prompt"
            )
    
    @pytest.mark.asyncio
    async def test_evaluate_draft_exception(self):
        """Test draft evaluation with exception."""
        controller = RevisionLoopController()
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY') as mock_registry:
            mock_registry.acall = AsyncMock(side_effect=Exception("Tool error"))
            
            result = await controller._evaluate_draft("Test draft", "Test prompt")
            
            assert "error" in result
            assert "Tool error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_revision(self):
        """Test revision execution."""
        controller = RevisionLoopController()
        
        state = MagicMock()
        state.data = {"context": {"word_limit": 500}}
        
        mock_result = {"revised_draft": "Improved draft", "changes": ["Better flow"]}
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY') as mock_registry:
            mock_registry.acall = AsyncMock(return_value=mock_result)
            
            result = await controller._execute_revision("Test draft", "Improve clarity", state)
            
            assert result == mock_result
            mock_registry.acall.assert_called_once_with(
                "revise",
                draft="Test draft",
                revision_focus="Improve clarity",
                word_count=500
            )
    
    def test_get_controller_status(self):
        """Test getting controller status."""
        controller = RevisionLoopController(max_attempts=5, target_score=7.5)
        
        status = controller.get_controller_status()
        
        assert status["max_attempts"] == 5
        assert status["target_score"] == 7.5
        assert status["is_active"] is False
        assert status["latest_attempt"] is None
        
        # Add an attempt
        progress = RevisionProgress(1, 6.0, 7.0, 1.0, [], [], 30.0)
        controller.tracker.track_attempt(progress)
        
        status = controller.get_controller_status()
        assert status["is_active"] is True
        assert status["latest_attempt"] == progress


class TestRevisionLoopNode:
    """Test RevisionLoopNode functionality."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = RevisionLoopNode()
        
        assert node.controller is not None
        assert node.controller.max_attempts == 3
        assert node.controller.target_score == 8.0
        assert node.get_name() == "revision_loop_controller"
    
    def test_initialization_with_params(self):
        """Test node initialization with custom parameters."""
        node = RevisionLoopNode(max_attempts=5, target_score=7.5)
        
        assert node.controller.max_attempts == 5
        assert node.controller.target_score == 7.5
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test node execution."""
        node = RevisionLoopNode()
        
        # Mock the controller
        mock_result = {
            "data": {"tool_outputs": {"revise": {"revised_draft": "Improved"}}},
            "errors": [],
            "metadata": {"revision_progress": "test"},
            "revision_completed": True
        }
        
        node.controller.execute_revision_cycle = AsyncMock(return_value=mock_result)
        
        plan = EssayPlan(
            phase=Phase.REVISING,
            data={"user_input": "test"},
        )
        
        result = await node.execute(plan)
        
        assert result["revision_completed"] is True
        assert result["controller_status"] is not None
        assert result["data"]["tool_outputs"]["revise"]["revised_draft"] == "Improved"


class TestRevisionQualityGate:
    """Test RevisionQualityGate functionality."""
    
    def test_initialization(self):
        """Test quality gate initialization."""
        gate = RevisionQualityGate()
        
        assert gate.target_score == 8.0
        assert gate.max_attempts == 3
    
    def test_initialization_with_params(self):
        """Test quality gate initialization with custom parameters."""
        gate = RevisionQualityGate(target_score=7.5, max_attempts=5)
        
        assert gate.target_score == 7.5
        assert gate.max_attempts == 5
    
    def test_should_continue_target_reached(self):
        """Test continuation decision when target is reached."""
        gate = RevisionQualityGate(target_score=8.0)
        
        state = MagicMock()
        state.get_evaluation_score.return_value = 8.5
        state.revision_attempts = 1
        
        assert gate.should_continue(state) is False
    
    def test_should_continue_max_attempts(self):
        """Test continuation decision when max attempts reached."""
        gate = RevisionQualityGate(max_attempts=3)
        
        state = MagicMock()
        state.get_evaluation_score.return_value = 6.0
        state.revision_attempts = 3
        
        assert gate.should_continue(state) is False
    
    def test_should_continue_yes(self):
        """Test continuation decision when should continue."""
        gate = RevisionQualityGate()
        
        state = MagicMock()
        state.get_evaluation_score.return_value = 6.0
        state.revision_attempts = 1
        
        assert gate.should_continue(state) is True
    
    def test_get_decision_reason(self):
        """Test getting decision reason."""
        gate = RevisionQualityGate(target_score=8.0, max_attempts=3)
        
        # Target reached
        state = MagicMock()
        state.get_evaluation_score.return_value = 8.5
        state.revision_attempts = 1
        
        reason = gate.get_decision_reason(state)
        assert "Target score 8.0 reached" in reason
        assert "current: 8.5" in reason
        
        # Max attempts reached
        state.get_evaluation_score.return_value = 6.0
        state.revision_attempts = 3
        
        reason = gate.get_decision_reason(state)
        assert "Maximum attempts 3 reached" in reason
        
        # Should continue
        state.revision_attempts = 1
        
        reason = gate.get_decision_reason(state)
        assert "Continue revision" in reason
        assert "score: 6.0/8.0" in reason
        assert "attempts: 1/3" in reason


class TestFactoryFunctions:
    """Test factory functions."""
    
    def test_create_revision_controller(self):
        """Test creating revision controller."""
        controller = create_revision_controller()
        
        assert isinstance(controller, RevisionLoopController)
        assert controller.max_attempts == 3
        assert controller.target_score == 8.0
        
        # Test with custom parameters
        controller = create_revision_controller(max_attempts=5, target_score=7.5)
        assert controller.max_attempts == 5
        assert controller.target_score == 7.5
    
    def test_create_quality_gate(self):
        """Test creating quality gate."""
        gate = create_quality_gate()
        
        assert isinstance(gate, RevisionQualityGate)
        assert gate.target_score == 8.0
        assert gate.max_attempts == 3
        
        # Test with custom parameters
        gate = create_quality_gate(target_score=7.5, max_attempts=5)
        assert gate.target_score == 7.5
        assert gate.max_attempts == 5
    
    @pytest.mark.asyncio
    async def test_execute_intelligent_revision_loop(self):
        """Test executing intelligent revision loop."""
        state = MagicMock()
        state.get_current_draft.return_value = ""
        state.errors = []
        
        result = await execute_intelligent_revision_loop(state)
        
        assert result["revision_completed"] is False
        assert "No draft available" in result["errors"][0] 