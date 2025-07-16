"""Integration tests for revision loop functionality.

Tests demonstrate complete revision loop execution including:
- End-to-end revision cycles
- Quality improvement tracking
- Error handling and recovery
- Integration with existing workflow engine
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from essay_agent.workflows.revision_loops import (
    RevisionLoopController,
    RevisionTracker,
    RevisionProgress,
    execute_intelligent_revision_loop,
)
from essay_agent.workflows.base import WorkflowState
from essay_agent.models import EssayPlan, Phase
from essay_agent.executor import EssayExecutor


class TestRevisionLoopIntegration:
    """Integration tests for revision loop functionality."""
    
    @pytest.fixture
    def mock_tools(self):
        """Mock tools for testing."""
        return {
            "essay_scoring": AsyncMock(),
            "revise": AsyncMock(),
            "weakness_highlight": AsyncMock(),
        }
    
    @pytest.fixture
    def sample_essay_data(self):
        """Sample essay data for testing."""
        return {
            "draft": "This is a sample essay about overcoming challenges in my life.",
            "prompt": "Describe a significant challenge you faced and how you overcame it.",
            "user_id": "test_user",
            "word_limit": 650
        }
    
    @pytest.fixture
    def progressive_scoring_results(self):
        """Progressive scoring results for testing improvement."""
        return [
            {
                "overall_score": 5.5,
                "scores": {"clarity": 5, "insight": 4, "structure": 6, "voice": 6, "prompt_fit": 6},
                "is_strong_essay": False,
                "feedback": "Essay needs more specific examples and better structure."
            },
            {
                "overall_score": 7.0,
                "scores": {"clarity": 7, "insight": 6, "structure": 7, "voice": 7, "prompt_fit": 7},
                "is_strong_essay": True,
                "feedback": "Much improved clarity and examples."
            },
            {
                "overall_score": 8.2,
                "scores": {"clarity": 8, "insight": 8, "structure": 8, "voice": 8, "prompt_fit": 8},
                "is_strong_essay": True,
                "feedback": "Excellent essay with compelling narrative."
            }
        ]
    
    @pytest.mark.asyncio
    async def test_single_revision_cycle_improvement(self, mock_tools, sample_essay_data, progressive_scoring_results):
        """Test single revision cycle with improvement."""
        # Setup progressive scoring
        mock_tools["essay_scoring"].side_effect = progressive_scoring_results[:2]
        mock_tools["revise"].return_value = {
            "revised_draft": "This is an improved essay with better examples and structure.",
            "changes": ["Added specific examples", "Improved paragraph structure"]
        }
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController(max_attempts=3, target_score=8.0)
            
            # Create workflow state
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": sample_essay_data["draft"]}},
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            result = await controller.execute_revision_cycle(state)
            
            # Verify successful execution
            assert result["revision_completed"] is True
            assert result["revision_needed"] is True
            assert result["progress"].score_improvement == 1.5  # 7.0 - 5.5
            assert result["progress"].attempt_number == 1
            
            # Verify tool calls
            assert mock_tools["essay_scoring"].call_count == 2
            assert mock_tools["revise"].call_count == 1
            
            # Verify progress tracking
            assert len(controller.tracker.attempts) == 1
            assert controller.tracker.attempts[0].is_improvement is True
    
    @pytest.mark.asyncio
    async def test_multiple_revision_cycles_until_target(self, mock_tools, sample_essay_data, progressive_scoring_results):
        """Test multiple revision cycles until target score reached."""
        # Setup progressive scoring for multiple cycles
        scoring_sequence = progressive_scoring_results
        revision_sequence = [
            {
                "revised_draft": "First revision with better examples.",
                "changes": ["Added specific examples", "Improved introduction"]
            },
            {
                "revised_draft": "Second revision with excellent structure.",
                "changes": ["Enhanced conclusion", "Better transitions"]
            }
        ]
        
        mock_tools["essay_scoring"].side_effect = scoring_sequence
        mock_tools["revise"].side_effect = revision_sequence
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController(max_attempts=3, target_score=8.0)
            
            # Create workflow state
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": sample_essay_data["draft"]}},
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            # Execute multiple revision cycles
            results = []
            for i in range(3):  # Max attempts
                result = await controller.execute_revision_cycle(state)
                results.append(result)
                
                if not result.get("should_continue", False):
                    break
                
                # Update state for next cycle
                state.revision_attempts = result["revision_attempts"]
                state.quality_scores = result["quality_scores"]
                state.data.update(result["data"])
            
            # Verify progression
            assert len(results) == 2  # Should stop after reaching target
            assert results[0]["progress"].current_score == 7.0
            assert results[1]["progress"].current_score == 8.2
            
            # Verify final state
            final_result = results[-1]
            assert final_result["should_continue"] is False
            assert final_result["progress"].current_score >= 8.0
            
            # Verify progress tracking
            progress_summary = controller.tracker.get_progress_summary()
            assert progress_summary["total_attempts"] == 2
            assert progress_summary["total_improvement"] == 2.7  # 8.2 - 5.5
            assert progress_summary["improvement_trend"] == "improving"
    
    @pytest.mark.asyncio
    async def test_revision_cycle_max_attempts_reached(self, mock_tools, sample_essay_data):
        """Test revision cycle stops at max attempts."""
        # Setup scoring that never reaches target
        low_score_result = {
            "overall_score": 6.0,
            "scores": {"clarity": 6, "insight": 5, "structure": 6, "voice": 6, "prompt_fit": 6},
            "is_strong_essay": False,
            "feedback": "Essay consistently needs more work."
        }
        
        mock_tools["essay_scoring"].return_value = low_score_result
        mock_tools["revise"].return_value = {
            "revised_draft": "Slightly improved essay.",
            "changes": ["Minor improvements"]
        }
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController(max_attempts=3, target_score=8.0)
            
            # Create workflow state
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": sample_essay_data["draft"]}},
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            # Execute revision cycles until max attempts
            results = []
            for i in range(4):  # Try more than max attempts
                result = await controller.execute_revision_cycle(state)
                results.append(result)
                
                if not result.get("should_continue", False):
                    break
                
                # Update state for next cycle
                state.revision_attempts = result["revision_attempts"]
                state.quality_scores = result["quality_scores"]
                state.data.update(result["data"])
            
            # Verify max attempts reached
            assert len(results) == 3  # Should stop at max attempts
            assert results[-1]["should_continue"] is False
            
            # Verify progress tracking
            progress_summary = controller.tracker.get_progress_summary()
            assert progress_summary["total_attempts"] == 3
            assert progress_summary["final_score"] == 6.0  # Never improved
    
    @pytest.mark.asyncio
    async def test_revision_cycle_with_evaluation_failure(self, mock_tools, sample_essay_data):
        """Test revision cycle handles evaluation failures gracefully."""
        # Setup evaluation to fail
        mock_tools["essay_scoring"].side_effect = Exception("Evaluation service unavailable")
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController()
            
            # Create workflow state
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": sample_essay_data["draft"]}},
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            result = await controller.execute_revision_cycle(state)
            
            # Verify error handling
            assert result["revision_completed"] is False
            assert len(result["errors"]) > 0
            assert "Evaluation failed" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_revision_cycle_with_revision_failure(self, mock_tools, sample_essay_data):
        """Test revision cycle handles revision tool failures gracefully."""
        # Setup evaluation to succeed but revision to fail
        mock_tools["essay_scoring"].return_value = {
            "overall_score": 6.0,
            "scores": {"clarity": 6, "insight": 5, "structure": 6, "voice": 6, "prompt_fit": 6},
            "is_strong_essay": False,
            "feedback": "Needs improvement."
        }
        
        mock_tools["revise"].side_effect = Exception("Revision service unavailable")
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController()
            
            # Create workflow state
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": sample_essay_data["draft"]}},
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            result = await controller.execute_revision_cycle(state)
            
            # Verify error handling
            assert result["revision_completed"] is False
            assert len(result["errors"]) > 0
            assert "Revision failed" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_revision_cycle_no_draft_available(self, mock_tools, sample_essay_data):
        """Test revision cycle handles missing draft gracefully."""
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController()
            
            # Create workflow state without draft
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {},  # No draft
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            result = await controller.execute_revision_cycle(state)
            
            # Verify error handling
            assert result["revision_completed"] is False
            assert len(result["errors"]) > 0
            assert "No draft available" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_targeted_feedback_generation(self, mock_tools, sample_essay_data):
        """Test targeted feedback generation based on evaluation results."""
        # Setup evaluation with specific weak areas
        evaluation_result = {
            "overall_score": 5.5,
            "scores": {"clarity": 4, "insight": 5, "structure": 3, "voice": 7, "prompt_fit": 6},
            "is_strong_essay": False,
            "feedback": "Focus on improving structure and clarity."
        }
        
        mock_tools["essay_scoring"].return_value = evaluation_result
        mock_tools["revise"].return_value = {
            "revised_draft": "Improved essay with better structure.",
            "changes": ["Better paragraph structure", "Clearer transitions"]
        }
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController()
            
            # Test targeted feedback generation
            feedback = controller.get_revision_focus(evaluation_result)
            
            # Verify feedback targets weakest areas
            assert "structure" in feedback.lower()
            assert "clarity" in feedback.lower()
            assert "Current: 3/10" in feedback  # Structure score
            assert "Current: 4/10" in feedback  # Clarity score
            assert "Focus on improving structure and clarity" in feedback
    
    @pytest.mark.asyncio
    async def test_revision_progress_tracking(self, mock_tools, sample_essay_data):
        """Test detailed progress tracking throughout revision cycles."""
        # Setup progressive scoring
        scoring_results = [
            {"overall_score": 5.0, "scores": {"clarity": 5, "insight": 4, "structure": 5, "voice": 5, "prompt_fit": 5}},
            {"overall_score": 6.5, "scores": {"clarity": 6, "insight": 6, "structure": 6, "voice": 7, "prompt_fit": 7}},
            {"overall_score": 7.8, "scores": {"clarity": 8, "insight": 7, "structure": 8, "voice": 8, "prompt_fit": 8}}
        ]
        
        mock_tools["essay_scoring"].side_effect = scoring_results
        mock_tools["revise"].return_value = {
            "revised_draft": "Improved essay",
            "changes": ["Better examples", "Improved flow"]
        }
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController(max_attempts=3, target_score=8.0)
            
            # Create workflow state
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": sample_essay_data["draft"]}},
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            # Execute revision cycles
            for i in range(2):  # Two cycles should be enough
                result = await controller.execute_revision_cycle(state)
                
                if not result.get("should_continue", False):
                    break
                
                # Update state
                state.revision_attempts = result["revision_attempts"]
                state.quality_scores = result["quality_scores"]
                state.data.update(result["data"])
            
            # Verify progress tracking
            tracker = controller.tracker
            progress_summary = tracker.get_progress_summary()
            
            assert progress_summary["total_attempts"] == 2
            assert progress_summary["total_improvement"] == 2.8  # 7.8 - 5.0
            assert progress_summary["improvement_trend"] == "improving"
            assert progress_summary["successful_attempts"] == 2
            assert progress_summary["significant_improvements"] == 2
            
            # Verify individual attempts
            attempts = tracker.attempts
            assert len(attempts) == 2
            assert attempts[0].score_improvement == 1.5  # 6.5 - 5.0
            assert attempts[1].score_improvement == 1.3  # 7.8 - 6.5
            assert all(attempt.is_improvement for attempt in attempts)
    
    @pytest.mark.asyncio
    async def test_integration_with_existing_workflow(self, mock_tools, sample_essay_data):
        """Test integration with existing workflow engine."""
        # Setup mocks for workflow integration
        mock_tools["essay_scoring"].return_value = {
            "overall_score": 8.5,
            "scores": {"clarity": 9, "insight": 8, "structure": 8, "voice": 9, "prompt_fit": 8},
            "is_strong_essay": True,
            "feedback": "Excellent essay."
        }
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            # Test with execute_intelligent_revision_loop function
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": sample_essay_data["draft"]}},
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            result = await execute_intelligent_revision_loop(state, target_score=8.0)
            
            # Verify integration works
            assert result["revision_completed"] is True
            assert result["revision_needed"] is False  # High score, no revision needed
            assert result["final_score"] == 8.5
    
    @pytest.mark.asyncio
    async def test_performance_characteristics(self, mock_tools, sample_essay_data):
        """Test performance characteristics of revision loops."""
        # Setup fast-responding mocks
        mock_tools["essay_scoring"].return_value = {
            "overall_score": 8.0,
            "scores": {"clarity": 8, "insight": 8, "structure": 8, "voice": 8, "prompt_fit": 8},
            "is_strong_essay": True,
            "feedback": "Good essay."
        }
        
        mock_tools["revise"].return_value = {
            "revised_draft": "Improved essay",
            "changes": ["Minor improvements"]
        }
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            controller = RevisionLoopController()
            
            # Create workflow state
            state = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": sample_essay_data["draft"]}},
                    "context": {
                        "essay_prompt": sample_essay_data["prompt"],
                        "word_limit": sample_essay_data["word_limit"]
                    }
                },
                revision_attempts=0
            )
            
            # Measure execution time
            start_time = asyncio.get_event_loop().time()
            
            result = await controller.execute_revision_cycle(state)
            
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            
            # Verify performance (should be fast with mocked tools)
            assert execution_time < 1.0  # Should complete quickly
            assert result["revision_completed"] is True
            
            # Verify progress timing is tracked
            if result.get("progress"):
                assert result["progress"].time_taken > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_revision_cycles(self, mock_tools, sample_essay_data):
        """Test that multiple revision cycles can run concurrently."""
        # Setup mocks
        mock_tools["essay_scoring"].return_value = {
            "overall_score": 8.0,
            "scores": {"clarity": 8, "insight": 8, "structure": 8, "voice": 8, "prompt_fit": 8},
            "is_strong_essay": True,
            "feedback": "Good essay."
        }
        
        with patch('essay_agent.workflows.revision_loops.TOOL_REGISTRY', mock_tools):
            # Create multiple controllers
            controller1 = RevisionLoopController()
            controller2 = RevisionLoopController()
            
            # Create states
            state1 = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": "Essay 1"}},
                    "context": {"essay_prompt": "Prompt 1", "word_limit": 650}
                },
                revision_attempts=0
            )
            
            state2 = WorkflowState(
                phase=Phase.REVISING,
                data={
                    "tool_outputs": {"draft": {"essay_text": "Essay 2"}},
                    "context": {"essay_prompt": "Prompt 2", "word_limit": 650}
                },
                revision_attempts=0
            )
            
            # Run concurrently
            results = await asyncio.gather(
                controller1.execute_revision_cycle(state1),
                controller2.execute_revision_cycle(state2)
            )
            
            # Verify both completed successfully
            assert len(results) == 2
            for result in results:
                assert result["revision_completed"] is True 