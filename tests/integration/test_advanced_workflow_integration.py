"""Integration tests for advanced workflow engine.

Tests demonstrate complete workflow execution including:
- Quality-driven branching
- Revision loops with max attempts
- Error recovery
- Performance characteristics
- Backward compatibility
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from essay_agent.executor import EssayExecutor
from essay_agent.planner import EssayPlan, Phase
from essay_agent.workflows.essay_workflow import AdvancedEssayWorkflow


class TestAdvancedWorkflowIntegration:
    """Integration tests for advanced workflow engine."""
    
    @pytest.fixture
    def mock_tools(self):
        """Mock tools for testing."""
        return {
            "brainstorm": AsyncMock(return_value={"ideas": ["idea1", "idea2", "idea3"]}),
            "outline": AsyncMock(return_value={"outline": "I. Introduction\nII. Body\nIII. Conclusion"}),
            "draft": AsyncMock(return_value={"essay_text": "This is a draft essay about challenges I faced."}),
            "essay_scoring": AsyncMock(return_value={
                "overall_score": 6.0,
                "scores": {"clarity": 6, "insight": 5, "structure": 7, "voice": 6, "prompt_fit": 6},
                "is_strong_essay": False,
                "feedback": "Essay needs more specific examples and better structure."
            }),
            "revise": AsyncMock(return_value={"revised_essay": "This is a revised essay with better examples."}),
            "polish": AsyncMock(return_value={"polished_essay": "This is a polished essay with improved flow."}),
        }
    
    @pytest.fixture
    def mock_high_quality_scoring(self):
        """Mock scoring tool that returns high quality scores."""
        return AsyncMock(return_value={
            "overall_score": 8.5,
            "scores": {"clarity": 9, "insight": 8, "structure": 8, "voice": 9, "prompt_fit": 8},
            "is_strong_essay": True,
            "feedback": "Excellent essay with compelling narrative and strong voice."
        })
    
    @pytest.mark.asyncio
    async def test_linear_workflow_high_quality(self, mock_tools, mock_high_quality_scoring):
        """Test linear workflow when essay meets quality threshold immediately."""
        # Setup mocks
        mock_tools["essay_scoring"] = mock_high_quality_scoring
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor = EssayExecutor(mode="advanced")
            
            result = await executor.arun(
                user_input="Write about overcoming a challenge",
                context={
                    "user_id": "test_user",
                    "word_limit": 650,
                    "quality_threshold": 8.0,
                    "essay_prompt": "Describe a challenge you overcame"
                }
            )
            
            # Verify workflow execution
            assert "tool_outputs" in result["data"]
            tool_outputs = result["data"]["tool_outputs"]
            
            # Should execute brainstorm → outline → draft → evaluate → finish
            assert "brainstorm" in tool_outputs
            assert "outline" in tool_outputs
            assert "draft" in tool_outputs
            assert "evaluate" in tool_outputs
            
            # Should NOT execute revision tools (high quality)
            assert "revise" not in tool_outputs
            assert "polish" not in tool_outputs
            
            # Verify final state
            assert result["metadata"]["workflow_completed"] is True
            assert result["metadata"]["final_score"] == 8.5
            assert result["metadata"]["total_revision_attempts"] == 0
    
    @pytest.mark.asyncio
    async def test_revision_loop_workflow(self, mock_tools):
        """Test revision loop workflow when essay needs improvement."""
        # Setup progressive scoring: low → medium → high
        score_progression = [
            {"overall_score": 6.0, "scores": {"clarity": 6, "insight": 5, "structure": 7, "voice": 6, "prompt_fit": 6}},
            {"overall_score": 7.0, "scores": {"clarity": 7, "insight": 6, "structure": 7, "voice": 7, "prompt_fit": 7}},
            {"overall_score": 8.2, "scores": {"clarity": 8, "insight": 8, "structure": 8, "voice": 8, "prompt_fit": 8}},
        ]
        
        call_count = 0
        def mock_scoring(*args, **kwargs):
            nonlocal call_count
            result = score_progression[min(call_count, len(score_progression) - 1)]
            call_count += 1
            return result
        
        mock_tools["essay_scoring"] = AsyncMock(side_effect=mock_scoring)
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor = EssayExecutor(mode="advanced")
            
            result = await executor.arun(
                user_input="Write about overcoming a challenge",
                context={
                    "user_id": "test_user",
                    "word_limit": 650,
                    "quality_threshold": 8.0,
                    "essay_prompt": "Describe a challenge you overcame"
                }
            )
            
            tool_outputs = result["data"]["tool_outputs"]
            
            # Should execute full workflow including revision cycle
            assert "brainstorm" in tool_outputs
            assert "outline" in tool_outputs
            assert "draft" in tool_outputs
            assert "evaluate" in tool_outputs
            assert "revise" in tool_outputs
            assert "polish" in tool_outputs
            
            # Should have called scoring multiple times
            assert mock_tools["essay_scoring"].call_count >= 2
            
            # Verify final state
            assert result["metadata"]["workflow_completed"] is True
            assert result["metadata"]["final_score"] == 8.2
            assert result["metadata"]["total_revision_attempts"] > 0
    
    @pytest.mark.asyncio
    async def test_max_revision_attempts(self, mock_tools):
        """Test workflow stops after max revision attempts."""
        # Setup scoring to always return low quality
        mock_tools["essay_scoring"] = AsyncMock(return_value={
            "overall_score": 6.0,
            "scores": {"clarity": 6, "insight": 5, "structure": 7, "voice": 6, "prompt_fit": 6},
            "is_strong_essay": False,
            "feedback": "Essay consistently needs improvement."
        })
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor = EssayExecutor(mode="advanced")
            
            result = await executor.arun(
                user_input="Write about overcoming a challenge",
                context={
                    "user_id": "test_user",
                    "word_limit": 650,
                    "quality_threshold": 8.0,
                    "essay_prompt": "Describe a challenge you overcame"
                }
            )
            
            # Should stop after max attempts even with low quality
            assert result["metadata"]["workflow_completed"] is True
            assert result["metadata"]["total_revision_attempts"] == 3  # Max attempts
            assert result["metadata"]["final_score"] == 6.0  # Still low quality
            
            # Should have tried revision/polish cycle 3 times
            assert mock_tools["revise"].call_count == 3
            assert mock_tools["polish"].call_count == 3
            assert mock_tools["essay_scoring"].call_count == 4  # Initial + 3 revision cycles
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_tools):
        """Test error handling and recovery in advanced workflow."""
        # Setup tool to fail once then succeed
        fail_count = 0
        def mock_draft_with_failure(*args, **kwargs):
            nonlocal fail_count
            fail_count += 1
            if fail_count == 1:
                raise Exception("Tool temporarily unavailable")
            return {"essay_text": "This is a draft essay after recovery."}
        
        mock_tools["draft"] = AsyncMock(side_effect=mock_draft_with_failure)
        mock_tools["essay_scoring"] = AsyncMock(return_value={
            "overall_score": 8.5,
            "scores": {"clarity": 9, "insight": 8, "structure": 8, "voice": 9, "prompt_fit": 8},
            "is_strong_essay": True,
            "feedback": "Excellent essay."
        })
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor = EssayExecutor(mode="advanced")
            
            result = await executor.arun(
                user_input="Write about overcoming a challenge",
                context={
                    "user_id": "test_user",
                    "word_limit": 650,
                    "quality_threshold": 8.0,
                    "essay_prompt": "Describe a challenge you overcame"
                }
            )
            
            # Should recover from error and complete successfully
            assert result["metadata"]["workflow_completed"] is True
            assert result["metadata"]["final_score"] == 8.5
            
            # Draft tool should have been called twice (fail then succeed)
            assert mock_tools["draft"].call_count == 2
            
            # Should have completed workflow despite initial failure
            tool_outputs = result["data"]["tool_outputs"]
            assert "brainstorm" in tool_outputs
            assert "outline" in tool_outputs
            assert "draft" in tool_outputs
            assert "evaluate" in tool_outputs
    
    @pytest.mark.asyncio
    async def test_evaluation_error_handling(self, mock_tools):
        """Test handling of evaluation tool errors."""
        # Setup evaluation tool to fail
        mock_tools["essay_scoring"] = AsyncMock(side_effect=Exception("Evaluation service unavailable"))
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor = EssayExecutor(mode="advanced")
            
            result = await executor.arun(
                user_input="Write about overcoming a challenge",
                context={
                    "user_id": "test_user",
                    "word_limit": 650,
                    "quality_threshold": 8.0,
                    "essay_prompt": "Describe a challenge you overcame"
                }
            )
            
            # Should handle evaluation failure gracefully
            assert result["metadata"]["workflow_completed"] is True
            assert result["metadata"]["final_score"] == 0.0  # Default score on error
            assert len(result["errors"]) > 0
            
            # Should not attempt revision with failed evaluation
            tool_outputs = result["data"]["tool_outputs"]
            assert "revise" not in tool_outputs
            assert "polish" not in tool_outputs
    
    @pytest.mark.asyncio
    async def test_custom_quality_threshold(self, mock_tools):
        """Test custom quality threshold configuration."""
        # Setup scoring to return 7.0 (above default but below custom threshold)
        mock_tools["essay_scoring"] = AsyncMock(return_value={
            "overall_score": 7.0,
            "scores": {"clarity": 7, "insight": 7, "structure": 7, "voice": 7, "prompt_fit": 7},
            "is_strong_essay": False,
            "feedback": "Good essay but needs refinement."
        })
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor = EssayExecutor(mode="advanced")
            
            result = await executor.arun(
                user_input="Write about overcoming a challenge",
                context={
                    "user_id": "test_user",
                    "word_limit": 650,
                    "quality_threshold": 7.5,  # Custom threshold
                    "essay_prompt": "Describe a challenge you overcame"
                }
            )
            
            # Should trigger revision with custom threshold
            tool_outputs = result["data"]["tool_outputs"]
            assert "revise" in tool_outputs
            assert "polish" in tool_outputs
    
    @pytest.mark.asyncio
    async def test_performance_characteristics(self, mock_tools):
        """Test performance characteristics of advanced workflow."""
        # Setup fast-responding mocks
        mock_tools["essay_scoring"] = AsyncMock(return_value={
            "overall_score": 8.5,
            "scores": {"clarity": 9, "insight": 8, "structure": 8, "voice": 9, "prompt_fit": 8},
            "is_strong_essay": True,
            "feedback": "Excellent essay."
        })
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor = EssayExecutor(mode="advanced")
            
            start_time = asyncio.get_event_loop().time()
            
            result = await executor.arun(
                user_input="Write about overcoming a challenge",
                context={
                    "user_id": "test_user",
                    "word_limit": 650,
                    "quality_threshold": 8.0,
                    "essay_prompt": "Describe a challenge you overcame"
                }
            )
            
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            
            # Should complete quickly (under 2 seconds for mocked tools)
            assert execution_time < 2.0
            assert result["metadata"]["workflow_completed"] is True
    
    @pytest.mark.asyncio
    async def test_backward_compatibility_with_legacy_mode(self, mock_tools):
        """Test that legacy mode still works as before."""
        # Setup legacy-compatible mocks
        mock_tools["essay_scoring"] = AsyncMock(return_value={
            "overall_score": 8.0,
            "scores": {"clarity": 8, "insight": 8, "structure": 8, "voice": 8, "prompt_fit": 8},
            "is_strong_essay": True,
            "feedback": "Good essay."
        })
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            # Test legacy mode
            legacy_executor = EssayExecutor(mode="legacy")
            
            plan = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={
                    "user_input": "Write about overcoming a challenge",
                    "context": {"user_id": "test_user", "word_limit": 650},
                    "args": {"user_id": "test_user", "word_limit": 650},
                }
            )
            
            # Should work with existing interface
            result = legacy_executor.run_plan(plan)
            
            # Should return tool outputs in legacy format
            assert isinstance(result, dict)
            assert "errors" not in result or len(result["errors"]) == 0
            
            # Compare with advanced mode
            advanced_executor = EssayExecutor(mode="advanced")
            advanced_result = await advanced_executor.arun(
                user_input="Write about overcoming a challenge",
                context={"user_id": "test_user", "word_limit": 650}
            )
            
            # Both should produce valid results
            assert result is not None
            assert advanced_result is not None
    
    def test_mode_switching_preserves_functionality(self):
        """Test that mode switching preserves core functionality."""
        executor = EssayExecutor(mode="legacy")
        
        # Verify initial state
        assert executor.get_mode() == "legacy"
        assert not executor.get_workflow_capabilities()["supports_branching"]
        
        # Switch to advanced
        executor.set_mode("advanced")
        assert executor.get_mode() == "advanced"
        assert executor.get_workflow_capabilities()["supports_branching"]
        
        # Switch back to legacy
        executor.set_mode("legacy")
        assert executor.get_mode() == "legacy"
        assert not executor.get_workflow_capabilities()["supports_branching"]
    
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, mock_tools):
        """Test that workflow state is properly maintained throughout execution."""
        # Setup progressive scoring
        scores = [6.0, 7.0, 8.2]
        call_count = 0
        def mock_scoring(*args, **kwargs):
            nonlocal call_count
            score = scores[min(call_count, len(scores) - 1)]
            call_count += 1
            return {
                "overall_score": score,
                "scores": {"clarity": int(score), "insight": int(score), "structure": int(score), "voice": int(score), "prompt_fit": int(score)},
                "is_strong_essay": score >= 8.0,
                "feedback": f"Essay scored {score}/10"
            }
        
        mock_tools["essay_scoring"] = AsyncMock(side_effect=mock_scoring)
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor = EssayExecutor(mode="advanced")
            
            result = await executor.arun(
                user_input="Write about overcoming a challenge",
                context={
                    "user_id": "test_user",
                    "word_limit": 650,
                    "quality_threshold": 8.0,
                    "essay_prompt": "Describe a challenge you overcame"
                }
            )
            
            # Verify state progression
            assert result["metadata"]["total_revision_attempts"] == 2
            assert result["metadata"]["final_score"] == 8.2
            assert result["metadata"]["workflow_completed"] is True
            
            # Verify tool execution order
            tool_outputs = result["data"]["tool_outputs"]
            assert all(tool in tool_outputs for tool in ["brainstorm", "outline", "draft", "evaluate", "revise", "polish"])
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, mock_tools):
        """Test that multiple workflows can run concurrently."""
        # Setup mocks
        mock_tools["essay_scoring"] = AsyncMock(return_value={
            "overall_score": 8.5,
            "scores": {"clarity": 9, "insight": 8, "structure": 8, "voice": 9, "prompt_fit": 8},
            "is_strong_essay": True,
            "feedback": "Excellent essay."
        })
        
        with patch('essay_agent.tools.REGISTRY', mock_tools):
            executor1 = EssayExecutor(mode="advanced")
            executor2 = EssayExecutor(mode="advanced")
            
            # Run workflows concurrently
            results = await asyncio.gather(
                executor1.arun(
                    user_input="Write about overcoming a challenge",
                    context={"user_id": "user1", "word_limit": 650}
                ),
                executor2.arun(
                    user_input="Write about a meaningful experience",
                    context={"user_id": "user2", "word_limit": 500}
                )
            )
            
            # Both should complete successfully
            assert len(results) == 2
            for result in results:
                assert result["metadata"]["workflow_completed"] is True
                assert result["metadata"]["final_score"] == 8.5 