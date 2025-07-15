"""Unit tests for workflow infrastructure foundation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from essay_agent.planner import EssayPlan, Phase
from essay_agent.workflows import WorkflowRegistry, WORKFLOW_REGISTRY, register_workflow_node
from essay_agent.workflows.base import WorkflowNode, ConditionalNode, LoopNode, QualityGate, WorkflowState
from essay_agent.workflows.nodes import ToolCallNode, EvaluationNode, DecisionNode, BranchNode


class TestWorkflowRegistry:
    """Test the workflow registry system."""
    
    def test_registry_creation(self):
        """Test registry can be created and is a dict."""
        registry = WorkflowRegistry()
        assert isinstance(registry, dict)
        assert len(registry) == 0
    
    def test_node_registration(self):
        """Test registering workflow nodes."""
        registry = WorkflowRegistry()
        
        # Create a mock node
        mock_node = MagicMock()
        mock_node.get_name.return_value = "test_node"
        
        # Register the node
        registry.register(mock_node)
        
        # Verify registration
        assert "test_node" in registry
        assert registry["test_node"] == mock_node
        assert registry.get_node("test_node") == mock_node
    
    def test_node_registration_overwrite(self):
        """Test node registration with overwrite flag."""
        registry = WorkflowRegistry()
        
        # Create two mock nodes
        mock_node1 = MagicMock()
        mock_node1.get_name.return_value = "test_node"
        
        mock_node2 = MagicMock()
        mock_node2.get_name.return_value = "test_node"
        
        # Register first node
        registry.register(mock_node1)
        assert registry["test_node"] == mock_node1
        
        # Try to register second node without overwrite - should warn and skip
        with pytest.warns(UserWarning, match="already registered"):
            registry.register(mock_node2)
        assert registry["test_node"] == mock_node1
        
        # Register second node with overwrite
        registry.register(mock_node2, overwrite=True)
        assert registry["test_node"] == mock_node2
    
    @pytest.mark.asyncio
    async def test_execute_node(self):
        """Test executing a node through the registry."""
        registry = WorkflowRegistry()
        
        # Create mock node with async execute
        mock_node = MagicMock()
        mock_node.get_name.return_value = "test_node"
        mock_node.execute = AsyncMock(return_value={"result": "success"})
        
        # Register and execute
        registry.register(mock_node)
        
        mock_state = MagicMock()
        result = await registry.execute_node("test_node", mock_state)
        
        assert result == {"result": "success"}
        mock_node.execute.assert_called_once_with(mock_state)
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_node(self):
        """Test executing a non-existent node raises error."""
        registry = WorkflowRegistry()
        
        with pytest.raises(KeyError, match="not found"):
            await registry.execute_node("nonexistent", MagicMock())


class TestWorkflowNodeDecorator:
    """Test the workflow node registration decorator."""
    
    def test_decorator_registration(self):
        """Test decorator properly registers nodes."""
        # Clear registry for clean test
        test_registry = WorkflowRegistry()
        
        # Create test node class
        class TestNode(WorkflowNode):
            def get_name(self) -> str:
                return self._name or "test_node"
            
            async def execute(self, state: EssayPlan) -> Dict[str, Any]:
                return {"test": "result"}
        
        # Apply decorator manually
        decorator = register_workflow_node("test_decorated")
        decorated_class = decorator(TestNode)
        
        # Verify registration in global registry
        assert "test_decorated" in WORKFLOW_REGISTRY
        assert isinstance(WORKFLOW_REGISTRY["test_decorated"], TestNode)
        assert WORKFLOW_REGISTRY["test_decorated"].get_name() == "test_decorated"
    
    def test_decorator_invalid_class(self):
        """Test decorator with invalid class raises error."""
        with pytest.raises(TypeError, match="requires a class"):
            register_workflow_node("invalid")(lambda: None)


class TestWorkflowState:
    """Test the enhanced workflow state management."""
    
    def test_workflow_state_creation(self):
        """Test WorkflowState can be created with defaults."""
        state = WorkflowState()
        
        assert state.iteration_count == 0
        assert state.max_iterations == 3
        assert state.node_history == []
        assert state.quality_scores == {}
    
    def test_evaluation_score_tracking(self):
        """Test evaluation score tracking."""
        state = WorkflowState()
        
        # Initially no score
        assert state.get_evaluation_score() == 0.0
        
        # Add scores
        state.quality_scores["overall"] = 0.85
        assert state.get_evaluation_score() == 0.85
    
    def test_iteration_tracking(self):
        """Test iteration counting."""
        state = WorkflowState()
        
        assert not state.has_exceeded_max_iterations()
        
        # Increment iterations
        state.increment_iteration()
        assert state.iteration_count == 1
        assert not state.has_exceeded_max_iterations()
        
        # Reach max iterations
        state.increment_iteration()
        state.increment_iteration()
        assert state.iteration_count == 3
        assert state.has_exceeded_max_iterations()
    
    def test_node_history_tracking(self):
        """Test node execution history tracking."""
        state = WorkflowState()
        
        # Add nodes to history
        state.add_node_execution("node1")
        state.add_node_execution("node2")
        state.add_node_execution("node3")
        
        assert state.node_history == ["node1", "node2", "node3"]
        
        # Test last n nodes
        assert state.get_last_n_nodes(2) == ["node2", "node3"]
        assert state.get_last_n_nodes(5) == ["node1", "node2", "node3"]


class TestToolCallNode:
    """Test the ToolCallNode implementation."""
    
    @pytest.mark.asyncio
    async def test_tool_execution_success(self):
        """Test successful tool execution."""
        # Mock tool registry
        mock_tool_result = {"essay": "Generated essay content"}
        
        with patch("essay_agent.tools.REGISTRY") as mock_registry:
            mock_registry.__contains__ = lambda self, key: key == "draft"
            mock_registry.acall = AsyncMock(return_value=mock_tool_result)
            
            # Create node and state
            node = ToolCallNode("draft")
            state = EssayPlan(
                phase=Phase.DRAFTING,
                data={"args": {"prompt": "Test prompt"}},
            )
            
            # Execute node
            result = await node.execute(state)
            
            # Verify results
            assert "data" in result
            assert "tool_outputs" in result["data"]
            assert result["data"]["tool_outputs"]["draft"] == mock_tool_result
            assert result["metadata"]["tool_call_draft_executed"] is True
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """Test handling of non-existent tool."""
        with patch("essay_agent.tools.REGISTRY") as mock_registry:
            mock_registry.__contains__ = lambda self, key: False
            
            node = ToolCallNode("nonexistent")
            state = EssayPlan(phase=Phase.DRAFTING)
            
            result = await node.execute(state)
            
            assert "errors" in result
            assert "not found in registry" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_tool_execution_failure(self):
        """Test handling of tool execution failure."""
        with patch("essay_agent.tools.REGISTRY") as mock_registry:
            mock_registry.__contains__ = lambda self, key: key == "draft"
            mock_registry.acall = AsyncMock(side_effect=Exception("Tool failed"))
            
            node = ToolCallNode("draft")
            state = EssayPlan(phase=Phase.DRAFTING, data={"args": {}})
            
            result = await node.execute(state)
            
            assert "errors" in result
            assert "execution failed" in result["errors"][0]


class TestEvaluationNode:
    """Test the EvaluationNode implementation."""
    
    @pytest.mark.asyncio
    async def test_evaluation_with_essay_content(self):
        """Test evaluation with essay content."""
        # Create state with essay content
        state = EssayPlan(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "draft": {"essay": "This is a test essay with multiple sentences. It has good structure and content."}
                }
            }
        )
        
        with patch("essay_agent.tools.REGISTRY") as mock_registry:
            mock_registry.__contains__ = lambda self, key: False  # No advanced tools
            
            node = EvaluationNode()
            result = await node.execute(state)
            
            # Verify quality scores were calculated
            assert "quality_scores" in result
            assert "overall" in result["quality_scores"]
            assert result["quality_scores"]["overall"] > 0
    
    @pytest.mark.asyncio
    async def test_evaluation_no_essay_content(self):
        """Test evaluation without essay content."""
        state = EssayPlan(phase=Phase.BRAINSTORMING)
        
        node = EvaluationNode()
        result = await node.execute(state)
        
        assert "errors" in result
        assert "No essay content found" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_keyword_similarity_calculation(self):
        """Test keyword similarity calculation."""
        state = EssayPlan(
            phase=Phase.POLISHING,
            data={
                "tool_outputs": {
                    "draft": {"essay": "leadership experience team project success achievement"},
                    "outline": {"outline": "leadership team project achievement goals success"}
                }
            }
        )
        
        with patch("essay_agent.tools.REGISTRY") as mock_registry:
            mock_registry.__contains__ = lambda self, key: False
            
            node = EvaluationNode(evaluation_metrics=["keyword_similarity"])
            result = await node.execute(state)
            
            # Should find some keyword overlap
            assert "quality_scores" in result
            assert "keyword_similarity" in result["quality_scores"]
            assert result["quality_scores"]["keyword_similarity"] > 0


class TestDecisionNode:
    """Test the DecisionNode implementation."""
    
    @pytest.mark.asyncio
    async def test_decision_true_path(self):
        """Test decision node taking true path."""
        def condition(state: EssayPlan) -> bool:
            return True
        
        node = DecisionNode(condition, ["true_node"], ["false_node"])
        state = EssayPlan(phase=Phase.DRAFTING)
        
        result = await node.execute(state)
        
        assert result["metadata"]["decision_condition"] is True
        assert result["metadata"]["decision_next_nodes"] == ["true_node"]
    
    @pytest.mark.asyncio
    async def test_decision_false_path(self):
        """Test decision node taking false path."""
        def condition(state: EssayPlan) -> bool:
            return False
        
        node = DecisionNode(condition, ["true_node"], ["false_node"])
        state = EssayPlan(phase=Phase.DRAFTING)
        
        result = await node.execute(state)
        
        assert result["metadata"]["decision_condition"] is False
        assert result["metadata"]["decision_next_nodes"] == ["false_node"]


class TestQualityGate:
    """Test the QualityGate implementation."""
    
    @pytest.mark.asyncio
    async def test_quality_gate_pass(self):
        """Test quality gate with passing score."""
        gate = QualityGate(threshold=0.7)
        state = WorkflowState(
            phase=Phase.POLISHING,
            quality_scores={"overall": 0.85}
        )
        
        result = await gate.execute(state)
        
        assert result["metadata"]["quality_gate_overall_0.7_passed"] is True
        assert result["metadata"]["quality_gate_overall_0.7_condition"] is True
        assert result["metadata"]["quality_gate_overall_0.7_next_nodes"] == ["finish"]
    
    @pytest.mark.asyncio
    async def test_quality_gate_fail(self):
        """Test quality gate with failing score."""
        gate = QualityGate(threshold=0.7)
        state = WorkflowState(
            phase=Phase.POLISHING,
            quality_scores={"overall": 0.5}
        )
        
        result = await gate.execute(state)
        
        assert result["metadata"]["quality_gate_overall_0.7_passed"] is False
        assert result["metadata"]["quality_gate_overall_0.7_condition"] is False
        assert result["metadata"]["quality_gate_overall_0.7_next_nodes"] == ["revise", "polish"]


class TestBranchNode:
    """Test the BranchNode implementation."""
    
    @pytest.mark.asyncio
    async def test_branch_selection(self):
        """Test branch node path selection."""
        def selector(state: EssayPlan) -> str:
            return "path_a"
        
        branch_paths = {
            "path_a": ["node1", "node2"],
            "path_b": ["node3", "node4"]
        }
        
        node = BranchNode(branch_paths, selector)
        state = EssayPlan(phase=Phase.DRAFTING)
        
        result = await node.execute(state)
        
        assert result["metadata"]["branch_selected_branch"] == "path_a"
        assert result["metadata"]["branch_branch_nodes"] == ["node1", "node2"]
    
    @pytest.mark.asyncio
    async def test_branch_invalid_selection(self):
        """Test branch node with invalid path selection."""
        def selector(state: EssayPlan) -> str:
            return "invalid_path"
        
        branch_paths = {
            "path_a": ["node1", "node2"],
            "path_b": ["node3", "node4"]
        }
        
        node = BranchNode(branch_paths, selector)
        state = EssayPlan(phase=Phase.DRAFTING)
        
        result = await node.execute(state)
        
        assert "errors" in result
        assert "not found in branch paths" in result["errors"][0]


class TestRegisteredNodes:
    """Test the pre-registered workflow nodes."""
    
    def test_quality_gate_default_registered(self):
        """Test that default quality gate is registered."""
        assert "quality_gate_default" in WORKFLOW_REGISTRY
        
        node = WORKFLOW_REGISTRY["quality_gate_default"]
        assert node.get_name() == "quality_gate_default"
        assert hasattr(node, 'threshold')
    
    def test_word_count_decision_registered(self):
        """Test that word count decision is registered."""
        assert "word_count_decision" in WORKFLOW_REGISTRY
        
        node = WORKFLOW_REGISTRY["word_count_decision"]
        assert node.get_name() == "word_count_decision"
        assert hasattr(node, 'target_words')
        assert hasattr(node, 'tolerance')
    
    @pytest.mark.asyncio
    async def test_word_count_decision_logic(self):
        """Test word count decision logic."""
        node = WORKFLOW_REGISTRY["word_count_decision"]
        
        # Test with essay in target range
        state = EssayPlan(
            phase=Phase.DRAFTING,
            data={
                "tool_outputs": {
                    "draft": {"essay": " ".join(["word"] * 650)}  # Exactly 650 words
                }
            }
        )
        
        result = await node.execute(state)
        
        assert result["metadata"]["word_count_decision_condition"] is True
        assert result["metadata"]["word_count_decision_next_nodes"] == ["polish"] 