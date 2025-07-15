"""Unit tests for advanced workflow engine.

Tests cover branching logic, quality gates, revision loops, error handling,
and backward compatibility.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from essay_agent.workflows.essay_workflow import (
    AdvancedWorkflowState,
    AdvancedEssayWorkflow,
    AdvancedEssayWorkflowNode,
)
from essay_agent.executor import EssayExecutor
from essay_agent.planner import EssayPlan, Phase


class TestAdvancedWorkflowState:
    """Test AdvancedWorkflowState functionality."""
    
    def test_initialization(self):
        """Test basic state initialization."""
        state = AdvancedWorkflowState(
            phase=Phase.BRAINSTORMING,
            data={"user_input": "test prompt"},
            quality_threshold=8.0,
            max_revision_attempts=3,
        )
        
        assert state.phase == Phase.BRAINSTORMING
        assert state.quality_threshold == 8.0
        assert state.max_revision_attempts == 3
        assert state.revision_attempts == 0
        assert state.get_evaluation_score() == 0.0
    
    def test_quality_score_tracking(self):
        """Test quality score tracking."""
        state = AdvancedWorkflowState()
        
        # Initially no score
        assert state.get_evaluation_score() == 0.0
        
        # Set quality score
        state.quality_scores = {"overall": 7.5}
        assert state.get_evaluation_score() == 7.5
    
    def test_revision_attempt_tracking(self):
        """Test revision attempt tracking."""
        state = AdvancedWorkflowState(max_revision_attempts=3)
        
        # Initially no attempts
        assert state.revision_attempts == 0
        assert state.should_continue_revision() is True
        
        # Increment attempts
        state.increment_revision_attempt()
        assert state.revision_attempts == 1
        assert state.iteration_count == 1
        
        # Max attempts reached
        state.revision_attempts = 3
        assert state.should_continue_revision() is False
    
    def test_should_continue_revision_logic(self):
        """Test revision continuation logic."""
        state = AdvancedWorkflowState(
            max_revision_attempts=3,
            quality_threshold=8.0,
        )
        
        # Should continue: low score, under max attempts
        state.quality_scores = {"overall": 6.0}
        state.revision_attempts = 1
        assert state.should_continue_revision() is True
        
        # Should stop: high score
        state.quality_scores = {"overall": 8.5}
        assert state.should_continue_revision() is False
        
        # Should stop: max attempts reached
        state.quality_scores = {"overall": 6.0}
        state.revision_attempts = 3
        assert state.should_continue_revision() is False
    
    def test_get_current_draft(self):
        """Test current draft extraction."""
        state = AdvancedWorkflowState()
        
        # No draft initially
        assert state.get_current_draft() == ""
        
        # Set current draft directly
        state.current_draft = "Direct draft text"
        assert state.get_current_draft() == "Direct draft text"
        
        # Extract from tool outputs - polish takes precedence
        state.current_draft = ""
        state.data = {
            "tool_outputs": {
                "draft": {"essay_text": "Draft text"},
                "polish": {"polished_essay": "Polished text"},
            }
        }
        assert state.get_current_draft() == "Polished text"
        
        # Extract from draft when no polish
        state.data = {
            "tool_outputs": {
                "draft": {"essay_text": "Draft text"},
            }
        }
        assert state.get_current_draft() == "Draft text"
    
    def test_get_essay_prompt(self):
        """Test essay prompt extraction."""
        state = AdvancedWorkflowState()
        
        # No prompt initially
        assert state.get_essay_prompt() == ""
        
        # Set prompt directly
        state.essay_prompt = "Direct prompt"
        assert state.get_essay_prompt() == "Direct prompt"
        
        # Extract from context
        state.essay_prompt = ""
        state.data = {
            "context": {"essay_prompt": "Context prompt"}
        }
        assert state.get_essay_prompt() == "Context prompt"


class TestAdvancedEssayWorkflow:
    """Test AdvancedEssayWorkflow functionality."""
    
    def test_initialization(self):
        """Test workflow initialization."""
        workflow = AdvancedEssayWorkflow()
        
        assert workflow.max_revision_attempts == 3
        assert workflow.quality_threshold == 8.0
        assert workflow._workflow is None
    
    def test_build_workflow(self):
        """Test workflow graph construction."""
        workflow = AdvancedEssayWorkflow()
        graph = workflow.build_workflow()
        
        # Graph should be compiled and ready
        assert graph is not None
        assert hasattr(graph, 'invoke')
        assert hasattr(graph, 'ainvoke')
    
    def test_quality_gate_decision(self):
        """Test quality gate decision logic."""
        workflow = AdvancedEssayWorkflow()
        
        # High score -> finish
        state = AdvancedWorkflowState(
            quality_scores={"overall": 8.5},
            revision_attempts=1,
        )
        assert workflow._quality_gate_decision(state) == "finish"
        
        # Low score, under max attempts -> revise
        state = AdvancedWorkflowState(
            quality_scores={"overall": 6.0},
            revision_attempts=1,
        )
        assert workflow._quality_gate_decision(state) == "revise"
        
        # Max attempts reached -> max_attempts
        state = AdvancedWorkflowState(
            quality_scores={"overall": 6.0},
            revision_attempts=3,
        )
        assert workflow._quality_gate_decision(state) == "max_attempts"
    
    @pytest.mark.asyncio
    async def test_evaluate_node(self):
        """Test evaluation node execution."""
        workflow = AdvancedEssayWorkflow()
        
        # Mock the scoring tool
        mock_result = {
            "overall_score": 7.5,
            "scores": {"clarity": 8, "insight": 7, "structure": 8, "voice": 7, "prompt_fit": 8},
            "feedback": "Good essay with room for improvement"
        }
        
        with patch.object(workflow.registry, 'acall', return_value=mock_result) as mock_call:
            state = AdvancedWorkflowState(
                current_draft="Test essay text",
                essay_prompt="Test prompt",
            )
            
            result = await workflow._evaluate_node(state)
            
            # Verify tool was called correctly
            mock_call.assert_called_once_with(
                "essay_scoring",
                essay_text="Test essay text",
                essay_prompt="Test prompt"
            )
            
            # Verify result structure
            assert result["quality_scores"]["overall"] == 7.5
            assert result["metadata"]["evaluation_score"] == 7.5
            assert "evaluate" in result["data"]["tool_outputs"]
    
    @pytest.mark.asyncio
    async def test_evaluate_node_no_essay_text(self):
        """Test evaluation node with no essay text."""
        workflow = AdvancedEssayWorkflow()
        
        state = AdvancedWorkflowState(
            current_draft="",  # No essay text
            essay_prompt="Test prompt",
        )
        
        result = await workflow._evaluate_node(state)
        
        # Should return error
        assert len(result["errors"]) > 0
        assert "No essay text available" in result["errors"][0]
        assert result["quality_scores"]["overall"] == 0.0
    
    @pytest.mark.asyncio
    async def test_evaluate_node_error_handling(self):
        """Test evaluation node error handling."""
        workflow = AdvancedEssayWorkflow()
        
        # Mock tool to raise exception
        with patch.object(workflow.registry, 'acall', side_effect=Exception("Tool error")) as mock_call:
            state = AdvancedWorkflowState(
                current_draft="Test essay text",
                essay_prompt="Test prompt",
            )
            
            result = await workflow._evaluate_node(state)
            
            # Should handle error gracefully
            assert len(result["errors"]) > 0
            assert "Evaluation failed" in result["errors"][0]
            assert result["quality_scores"]["overall"] == 0.0
            assert "evaluation_error" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_revise_node(self):
        """Test revision node execution."""
        workflow = AdvancedEssayWorkflow()
        
        mock_result = {"revised_essay": "Revised essay text"}
        
        with patch.object(workflow, '_execute_tool', return_value={"data": {"tool_outputs": {"revise": mock_result}}}) as mock_execute:
            state = AdvancedWorkflowState(revision_attempts=1)
            
            result = await workflow._revise_node(state)
            
            # Verify tool execution
            mock_execute.assert_called_once_with("revise", state)
            
            # Verify revision attempt tracking
            assert result["revision_attempts"] == 2
    
    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test successful tool execution."""
        workflow = AdvancedEssayWorkflow()
        
        mock_result = {"output": "Tool output"}
        
        with patch.object(workflow.registry, 'acall', return_value=mock_result) as mock_call:
            state = AdvancedWorkflowState(
                data={"args": {"param": "value"}},
                node_history=[],
            )
            
            result = await workflow._execute_tool("test_tool", state)
            
            # Verify tool call
            mock_call.assert_called_once_with("test_tool", param="value")
            
            # Verify result structure
            assert result["data"]["tool_outputs"]["test_tool"] == mock_result
            assert result["metadata"]["test_tool_executed"] is True
            assert "test_tool" in result["node_history"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test tool execution when tool not found."""
        workflow = AdvancedEssayWorkflow()
        
        state = AdvancedWorkflowState(node_history=[])
        
        result = await workflow._execute_tool("nonexistent_tool", state)
        
        # Should return error
        assert len(result["errors"]) > 0
        assert "not found in registry" in result["errors"][0]
        assert "nonexistent_tool" in result["node_history"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_retry(self):
        """Test tool execution with retry logic."""
        workflow = AdvancedEssayWorkflow()
        
        # Mock tool to fail twice then succeed
        mock_result = {"output": "Success"}
        call_count = 0
        
        def mock_acall(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return mock_result
        
        with patch.object(workflow.registry, 'acall', side_effect=mock_acall):
            state = AdvancedWorkflowState(
                data={"args": {}},
                node_history=[],
            )
            
            result = await workflow._execute_tool("test_tool", state)
            
            # Should succeed after retries
            assert result["data"]["tool_outputs"]["test_tool"] == mock_result
            assert call_count == 3  # Failed twice, succeeded on third try
    
    @pytest.mark.asyncio
    async def test_finish_node(self):
        """Test finish node execution."""
        workflow = AdvancedEssayWorkflow()
        
        state = AdvancedWorkflowState(
            quality_scores={"overall": 8.5},
            revision_attempts=2,
            node_history=[],
        )
        
        result = await workflow._finish_node(state)
        
        # Verify finish metadata
        assert result["metadata"]["workflow_completed"] is True
        assert result["metadata"]["final_score"] == 8.5
        assert result["metadata"]["total_revision_attempts"] == 2
        assert "finish" in result["node_history"]


class TestAdvancedEssayWorkflowNode:
    """Test AdvancedEssayWorkflowNode functionality."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = AdvancedEssayWorkflowNode()
        
        assert node.workflow_engine is not None
        assert node._compiled_workflow is None
        assert node.get_name() == "advanced_essay_workflow"
    
    def test_convert_to_workflow_state(self):
        """Test EssayPlan to AdvancedWorkflowState conversion."""
        node = AdvancedEssayWorkflowNode()
        
        plan = EssayPlan(
            phase=Phase.DRAFTING,
            data={
                "user_input": "Test prompt",
                "context": {"essay_prompt": "Essay prompt"},
            },
            errors=["Test error"],
            metadata={"test": "metadata"},
        )
        
        workflow_state = node._convert_to_workflow_state(plan)
        
        assert workflow_state.phase == Phase.DRAFTING
        assert workflow_state.data["user_input"] == "Test prompt"
        assert workflow_state.errors == ["Test error"]
        assert workflow_state.metadata["test"] == "metadata"
        assert workflow_state.essay_prompt == "Essay prompt"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test node execution."""
        node = AdvancedEssayWorkflowNode()
        
        # Mock compiled workflow
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke.return_value = {
            "data": {"tool_outputs": {"draft": {"essay_text": "Test essay"}}},
            "errors": [],
            "metadata": {"completed": True},
        }
        node._compiled_workflow = mock_workflow
        
        plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={"user_input": "Test prompt"},
        )
        
        result = await node.execute(plan)
        
        # Verify workflow execution
        mock_workflow.ainvoke.assert_called_once()
        
        # Verify result
        assert result["data"]["tool_outputs"]["draft"]["essay_text"] == "Test essay"
        assert result["errors"] == []
        assert result["metadata"]["completed"] is True


class TestEssayExecutorAdvancedMode:
    """Test EssayExecutor in advanced mode."""
    
    def test_initialization_advanced_mode(self):
        """Test executor initialization in advanced mode."""
        executor = EssayExecutor(mode="advanced")
        
        assert executor.mode == "advanced"
        assert executor.get_mode() == "advanced"
        
        capabilities = executor.get_workflow_capabilities()
        assert capabilities["supports_branching"] is True
        assert capabilities["supports_quality_gates"] is True
        assert capabilities["supports_revision_loops"] is True
        assert capabilities["max_revision_attempts"] == 3
        assert capabilities["quality_threshold"] == 8.0
    
    def test_initialization_legacy_mode(self):
        """Test executor initialization in legacy mode."""
        executor = EssayExecutor(mode="legacy")
        
        assert executor.mode == "legacy"
        assert executor.get_mode() == "legacy"
        
        capabilities = executor.get_workflow_capabilities()
        assert capabilities["supports_branching"] is False
        assert capabilities["supports_quality_gates"] is False
        assert capabilities["supports_revision_loops"] is False
        assert capabilities["max_revision_attempts"] == 0
        assert capabilities["quality_threshold"] is None
    
    def test_invalid_mode(self):
        """Test invalid mode raises error."""
        with pytest.raises(ValueError, match="Invalid mode"):
            EssayExecutor(mode="invalid")
    
    def test_mode_switching(self):
        """Test switching between modes."""
        executor = EssayExecutor(mode="legacy")
        
        # Switch to advanced
        executor.set_mode("advanced")
        assert executor.get_mode() == "advanced"
        
        # Switch back to legacy
        executor.set_mode("legacy")
        assert executor.get_mode() == "legacy"
        
        # Invalid mode
        with pytest.raises(ValueError, match="Invalid mode"):
            executor.set_mode("invalid")
    
    def test_extract_args_from_context(self):
        """Test argument extraction from context."""
        executor = EssayExecutor(mode="advanced")
        
        context = {
            "user_id": "test_user",
            "word_limit": 500,
            "conversation_history": [{"role": "user", "content": "Hello"}],
            "user_profile": {"name": "Test User"},
            "extra_field": "ignored",
        }
        
        args = executor._extract_args_from_context(context)
        
        assert args["user_id"] == "test_user"
        assert args["word_limit"] == 500
        assert args["conversation_history"] == [{"role": "user", "content": "Hello"}]
        assert args["user_profile"] == {"name": "Test User"}
        assert "extra_field" not in args
    
    @pytest.mark.asyncio
    async def test_arun_advanced_mode(self):
        """Test async run in advanced mode."""
        executor = EssayExecutor(mode="advanced")
        
        # Mock the graph
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "data": {"tool_outputs": {"draft": {"essay_text": "Test essay"}}},
            "errors": [],
            "metadata": {"completed": True},
        }
        executor._graph = mock_graph
        
        context = {
            "user_id": "test_user",
            "word_limit": 650,
            "quality_threshold": 7.5,
            "essay_prompt": "Write about challenges",
        }
        
        result = await executor.arun("Test prompt", context)
        
        # Verify graph invocation
        mock_graph.ainvoke.assert_called_once()
        call_args = mock_graph.ainvoke.call_args[0][0]
        
        assert call_args["phase"] == Phase.BRAINSTORMING
        assert call_args["data"]["user_input"] == "Test prompt"
        assert call_args["quality_threshold"] == 7.5
        assert call_args["essay_prompt"] == "Write about challenges"
        assert call_args["revision_attempts"] == 0
        assert call_args["max_revision_attempts"] == 3
    
    @pytest.mark.asyncio
    async def test_run_plan_async_advanced_mode(self):
        """Test async plan execution in advanced mode."""
        executor = EssayExecutor(mode="advanced")
        
        # Mock the graph
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "phase": Phase.POLISHING,
            "data": {"tool_outputs": {"polish": {"polished_essay": "Polished essay"}}},
            "errors": [],
            "metadata": {"completed": True},
        }
        executor._graph = mock_graph
        
        plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={"user_input": "Test prompt"},
        )
        
        result = await executor.run_plan_async(plan)
        
        # Verify result conversion
        assert isinstance(result, EssayPlan)
        assert result.phase == Phase.POLISHING
        assert result.data["tool_outputs"]["polish"]["polished_essay"] == "Polished essay"
        assert result.errors == []
        assert result.metadata["completed"] is True
    
    def test_backward_compatibility(self):
        """Test that legacy mode works as before."""
        executor = EssayExecutor(mode="legacy")
        
        # Should have same interface as original
        assert hasattr(executor, 'run_plan')
        assert hasattr(executor, 'run_plan_async')
        assert hasattr(executor, 'arun')
        
        # Should use legacy graph
        assert executor._graph is not None
        
        # Should not have advanced capabilities
        capabilities = executor.get_workflow_capabilities()
        assert capabilities["supports_branching"] is False
        assert capabilities["supports_quality_gates"] is False
        assert capabilities["supports_revision_loops"] is False 