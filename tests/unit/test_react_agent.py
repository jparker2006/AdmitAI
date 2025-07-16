"""Unit tests for ReAct agent components.

This module provides comprehensive test coverage for the ReAct agent implementation,
including reasoning engine, action executor, and main agent functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any
import time

from essay_agent.agent.core.react_agent import EssayReActAgent
from essay_agent.agent.core.reasoning_engine import (
    ReasoningEngine, ReasoningResult, ReasoningError
)
from essay_agent.agent.core.action_executor import (
    ActionExecutor, ActionResult, ActionExecutionError
)


@pytest.fixture
def mock_memory():
    """Mock AgentMemory for testing."""
    memory = Mock()
    memory.retrieve_context = Mock(return_value={
        "user_profile": {"user_id": "test_user", "name": "Test User"},
        "conversation_history": [],
        "essay_state": {"current_phase": "brainstorming"},
        "patterns": [],
        "recent_tools": []
    })
    memory.store_conversation_turn = AsyncMock()
    memory.store_reasoning_chain = AsyncMock()
    memory.store_tool_execution = AsyncMock()
    return memory


@pytest.fixture
def mock_prompt_builder():
    """Mock PromptBuilder for testing."""
    builder = Mock()
    builder.build_reasoning_prompt = AsyncMock(return_value={
        "prompt": "Test reasoning prompt",
        "version": "test_v1"
    })
    builder.build_response_prompt = AsyncMock(return_value={
        "prompt": "Test response prompt",
        "version": "test_v1"
    })
    return builder


@pytest.fixture
def mock_prompt_optimizer():
    """Mock PromptOptimizer for testing."""
    optimizer = Mock()
    optimizer.track_performance = AsyncMock()
    return optimizer


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry for testing."""
    registry = Mock()
    registry.has_tool = Mock(return_value=True)
    registry.get_tool = Mock(return_value=AsyncMock(return_value="Tool result"))
    registry.get_tool_description = Mock(return_value={
        "required_args": ["content"],
        "arg_types": {"content": str}
    })
    return registry


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    llm = Mock()
    llm.apredict = AsyncMock(return_value='{"context_understanding": "User wants help", "reasoning": "Should brainstorm", "response_type": "tool_execution", "chosen_tool": "brainstorm", "tool_args": {"topic": "test"}, "confidence": 0.8}')
    return llm


class TestReasoningEngine:
    """Test cases for ReasoningEngine."""
    
    def test_reasoning_engine_initialization(self, mock_prompt_builder, mock_prompt_optimizer):
        """Test ReasoningEngine initialization."""
        with patch('essay_agent.agent.core.reasoning_engine.get_chat_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            
            engine = ReasoningEngine(mock_prompt_builder, mock_prompt_optimizer)
            
            assert engine.prompt_builder == mock_prompt_builder
            assert engine.prompt_optimizer == mock_prompt_optimizer
            assert engine.reasoning_count == 0
            assert engine.success_count == 0
    
    @pytest.mark.asyncio
    async def test_reason_about_action_success(self, mock_prompt_builder, mock_prompt_optimizer, mock_llm):
        """Test successful reasoning about action."""
        with patch('essay_agent.agent.core.reasoning_engine.get_chat_llm', return_value=mock_llm):
            engine = ReasoningEngine(mock_prompt_builder, mock_prompt_optimizer)
            
            user_input = "Help me brainstorm ideas"
            context = {"user_profile": {"name": "Test"}}
            
            result = await engine.reason_about_action(user_input, context)
            
            assert isinstance(result, ReasoningResult)
            assert result.context_understanding == "User wants help"
            assert result.reasoning == "Should brainstorm"
            assert result.chosen_tool == "brainstorm"
            assert result.confidence == 0.8
            assert result.response_type == "tool_execution"
            
            # Verify tracking
            assert engine.reasoning_count == 1
            assert engine.success_count == 1
            mock_prompt_optimizer.track_performance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reason_about_action_llm_failure(self, mock_prompt_builder, mock_prompt_optimizer):
        """Test reasoning when LLM fails."""
        failing_llm = Mock()
        failing_llm.apredict = AsyncMock(side_effect=Exception("LLM Error"))
        
        with patch('essay_agent.agent.core.reasoning_engine.get_chat_llm', return_value=failing_llm):
            engine = ReasoningEngine(mock_prompt_builder, mock_prompt_optimizer)
            
            with pytest.raises(ReasoningError):
                await engine.reason_about_action("test input", {})
            
            assert engine.reasoning_count == 1
            assert engine.success_count == 0
    
    @pytest.mark.asyncio
    async def test_reason_about_response(self, mock_prompt_builder, mock_prompt_optimizer, mock_llm):
        """Test response generation."""
        mock_llm.apredict = AsyncMock(return_value="Here's my helpful response!")
        
        with patch('essay_agent.agent.core.reasoning_engine.get_chat_llm', return_value=mock_llm):
            engine = ReasoningEngine(mock_prompt_builder, mock_prompt_optimizer)
            
            response = await engine.reason_about_response(
                "test input",
                {"reasoning": "test"},
                ("tool_execution", "result")
            )
            
            assert response == "Here's my helpful response!"
            mock_prompt_builder.build_response_prompt.assert_called_once()
    
    def test_parse_reasoning_response_valid(self, mock_prompt_builder, mock_prompt_optimizer):
        """Test parsing valid reasoning response."""
        with patch('essay_agent.agent.core.reasoning_engine.get_chat_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            engine = ReasoningEngine(mock_prompt_builder, mock_prompt_optimizer)
            
            valid_response = '{"context_understanding": "test", "reasoning": "test", "response_type": "conversation", "confidence": 0.7}'
            
            with patch('essay_agent.agent.core.reasoning_engine.safe_parse') as mock_parse:
                mock_parse.return_value = {
                    "context_understanding": "test",
                    "reasoning": "test", 
                    "response_type": "conversation",
                    "confidence": 0.7
                }
                
                result = engine._parse_reasoning_response(valid_response)
                
                assert result["context_understanding"] == "test"
                assert result["confidence"] == 0.7
                assert result["response_type"] == "conversation"
    
    def test_parse_reasoning_response_invalid(self, mock_prompt_builder, mock_prompt_optimizer):
        """Test parsing invalid reasoning response."""
        with patch('essay_agent.agent.core.reasoning_engine.get_chat_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            engine = ReasoningEngine(mock_prompt_builder, mock_prompt_optimizer)
            
            with patch('essay_agent.agent.core.reasoning_engine.safe_parse') as mock_parse:
                mock_parse.side_effect = Exception("Parse error")
                
                with pytest.raises(ReasoningError):
                    engine._parse_reasoning_response("invalid json")
    
    def test_get_performance_metrics(self, mock_prompt_builder, mock_prompt_optimizer):
        """Test performance metrics calculation."""
        with patch('essay_agent.agent.core.reasoning_engine.get_chat_llm') as mock_get_llm:
            mock_get_llm.return_value = Mock()
            engine = ReasoningEngine(mock_prompt_builder, mock_prompt_optimizer)
            
            # Simulate some activity
            engine.reasoning_count = 10
            engine.success_count = 8
            engine.total_reasoning_time = 50.0
            
            metrics = engine.get_performance_metrics()
            
            assert metrics["total_reasoning_requests"] == 10
            assert metrics["successful_requests"] == 8
            assert metrics["success_rate"] == 0.8
            assert metrics["average_reasoning_time"] == 5.0


class TestActionExecutor:
    """Test cases for ActionExecutor."""
    
    def test_action_executor_initialization(self, mock_tool_registry, mock_memory):
        """Test ActionExecutor initialization."""
        executor = ActionExecutor(mock_tool_registry, mock_memory)
        
        assert executor.tool_registry == mock_tool_registry
        assert executor.memory == mock_memory
        assert executor.execution_count == 0
        assert executor.success_count == 0
        assert len(executor.recovery_strategies) == 5
    
    @pytest.mark.asyncio
    async def test_execute_tool_action_success(self, mock_tool_registry, mock_memory):
        """Test successful tool execution."""
        executor = ActionExecutor(mock_tool_registry, mock_memory)
        
        reasoning = {
            "response_type": "tool_execution",
            "chosen_tool": "brainstorm",
            "tool_args": {"topic": "test"},
            "confidence": 0.8
        }
        
        result = await executor.execute_action(reasoning)
        
        assert result.success is True
        assert result.action_type == "tool_execution"
        assert result.tool_name == "brainstorm"
        assert result.result == "Tool result"
        assert executor.success_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_conversation_action(self, mock_tool_registry, mock_memory):
        """Test conversation action execution."""
        executor = ActionExecutor(mock_tool_registry, mock_memory)
        
        reasoning = {
            "response_type": "conversation",
            "reasoning": "User needs encouragement",
            "context": {},
            "confidence": 0.7
        }
        
        result = await executor.execute_action(reasoning)
        
        assert result.success is True
        assert result.action_type == "conversation"
        assert isinstance(result.result, str)
        assert len(result.result) > 0
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_validation_error(self, mock_tool_registry, mock_memory):
        """Test tool execution with validation failure."""
        mock_tool_registry.get_tool_description.return_value = {
            "required_args": ["required_param"],
            "arg_types": {"required_param": str}
        }
        
        executor = ActionExecutor(mock_tool_registry, mock_memory)
        
        with pytest.raises(ActionExecutionError):
            await executor.execute_tool("test_tool", {})  # Missing required param
    
    @pytest.mark.asyncio
    async def test_execute_tool_timeout(self, mock_tool_registry, mock_memory):
        """Test tool execution timeout."""
        slow_tool = AsyncMock()
        slow_tool.side_effect = lambda **kwargs: asyncio.sleep(100)  # Long delay
        mock_tool_registry.get_tool.return_value = slow_tool
        
        executor = ActionExecutor(mock_tool_registry, mock_memory)
        
        with pytest.raises(ActionExecutionError) as exc_info:
            await executor.execute_tool("slow_tool", {})
        
        assert "timed out" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_handle_conversation_types(self, mock_tool_registry, mock_memory):
        """Test different conversation handling types."""
        executor = ActionExecutor(mock_tool_registry, mock_memory)
        
        # Test encouragement response
        response = await executor.handle_conversation("user feels stuck", {})
        assert "stuck" in response.lower() or "normal" in response.lower()
        
        # Test guidance response
        response = await executor.handle_conversation("user needs guidance", {})
        assert len(response) > 0
    
    def test_error_classification(self, mock_tool_registry, mock_memory):
        """Test error type classification."""
        executor = ActionExecutor(mock_tool_registry, mock_memory)
        
        assert executor._classify_error(Exception("timeout error")) == "timeout"
        assert executor._classify_error(Exception("validation failed")) == "validation"
        assert executor._classify_error(Exception("network connection")) == "network"
        assert executor._classify_error(Exception("llm api error")) == "llm"
        assert executor._classify_error(Exception("general error")) == "execution"
    
    def test_get_performance_metrics(self, mock_tool_registry, mock_memory):
        """Test performance metrics calculation."""
        executor = ActionExecutor(mock_tool_registry, mock_memory)
        
        # Simulate some activity
        executor.execution_count = 15
        executor.success_count = 12
        executor.total_execution_time = 75.0
        executor.tool_usage_stats = {
            "brainstorm": {
                "usage_count": 5,
                "success_count": 5,
                "total_time": 25.0,
                "avg_time": 5.0
            }
        }
        
        metrics = executor.get_performance_metrics()
        
        assert metrics["total_executions"] == 15
        assert metrics["successful_executions"] == 12
        assert metrics["success_rate"] == 0.8
        assert metrics["average_execution_time"] == 5.0
        assert "brainstorm" in metrics["tool_usage_stats"]


class TestEssayReActAgent:
    """Test cases for EssayReActAgent."""
    
    @patch('essay_agent.agent.core.react_agent.AgentMemory')
    @patch('essay_agent.agent.core.react_agent.PromptBuilder')
    @patch('essay_agent.agent.core.react_agent.PromptOptimizer')
    @patch('essay_agent.agent.core.react_agent.ReasoningEngine')
    @patch('essay_agent.agent.core.react_agent.ActionExecutor')
    def test_agent_initialization(self, mock_executor, mock_reasoning, mock_optimizer, mock_builder, mock_memory):
        """Test EssayReActAgent initialization."""
        agent = EssayReActAgent("test_user")
        
        assert agent.user_id == "test_user"
        assert agent.interaction_count == 0
        assert mock_memory.called
        assert mock_builder.called
        assert mock_optimizer.called
        assert mock_reasoning.called
        assert mock_executor.called
    
    @pytest.mark.asyncio
    async def test_handle_message_success(self):
        """Test successful message handling."""
        with patch('essay_agent.agent.core.react_agent.AgentMemory') as mock_memory_cls, \
             patch('essay_agent.agent.core.react_agent.PromptBuilder') as mock_builder_cls, \
             patch('essay_agent.agent.core.react_agent.PromptOptimizer') as mock_optimizer_cls, \
             patch('essay_agent.agent.core.react_agent.ReasoningEngine') as mock_reasoning_cls, \
             patch('essay_agent.agent.core.react_agent.ActionExecutor') as mock_executor_cls:
            
            # Setup mocks
            mock_memory = Mock()
            mock_memory.retrieve_context.return_value = {"test": "context"}
            mock_memory.store_conversation_turn = AsyncMock()
            mock_memory.store_reasoning_chain = AsyncMock()
            mock_memory_cls.return_value = mock_memory
            
            mock_reasoning = Mock()
            mock_reasoning.reason_about_action = AsyncMock(return_value=ReasoningResult(
                context_understanding="Test understanding",
                reasoning="Test reasoning",
                chosen_tool="brainstorm",
                tool_args={"topic": "test"},
                confidence=0.8,
                response_type="tool_execution",
                anticipated_follow_up="Continue with outline",
                context_flags=[],
                reasoning_time=1.0,
                prompt_version="v1"
            ))
            mock_reasoning.get_performance_metrics.return_value = {}
            mock_reasoning_cls.return_value = mock_reasoning
            
            mock_executor = Mock()
            mock_executor.execute_action = AsyncMock(return_value=ActionResult(
                action_type="tool_execution",
                success=True,
                result="Great brainstorm results!",
                execution_time=0.5,
                tool_name="brainstorm"
            ))
            mock_executor.get_performance_metrics.return_value = {}
            mock_executor_cls.return_value = mock_executor
            
            # Initialize and test agent
            agent = EssayReActAgent("test_user")
            response = await agent.handle_message("Help me brainstorm ideas")
            
            assert isinstance(response, str)
            assert len(response) > 0
            assert agent.interaction_count == 1
            
            # Verify method calls
            mock_reasoning.reason_about_action.assert_called_once()
            mock_executor.execute_action.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_message_with_error(self):
        """Test message handling with errors."""
        with patch('essay_agent.agent.core.react_agent.AgentMemory') as mock_memory_cls, \
             patch('essay_agent.agent.core.react_agent.PromptBuilder') as mock_builder_cls, \
             patch('essay_agent.agent.core.react_agent.PromptOptimizer') as mock_optimizer_cls, \
             patch('essay_agent.agent.core.react_agent.ReasoningEngine') as mock_reasoning_cls, \
             patch('essay_agent.agent.core.react_agent.ActionExecutor') as mock_executor_cls:
            
            # Setup failing reasoning engine
            mock_reasoning = Mock()
            mock_reasoning.reason_about_action = AsyncMock(side_effect=Exception("Reasoning failed"))
            mock_reasoning.get_performance_metrics.return_value = {}
            mock_reasoning_cls.return_value = mock_reasoning
            
            agent = EssayReActAgent("test_user")
            response = await agent.handle_message("test input")
            
            assert isinstance(response, str)
            assert "technical difficulties" in response.lower()
    
    def test_observe_context_success(self):
        """Test successful context observation."""
        with patch('essay_agent.agent.core.react_agent.AgentMemory') as mock_memory_cls, \
             patch('essay_agent.agent.core.react_agent.PromptBuilder'), \
             patch('essay_agent.agent.core.react_agent.PromptOptimizer'), \
             patch('essay_agent.agent.core.react_agent.ReasoningEngine') as mock_reasoning_cls, \
             patch('essay_agent.agent.core.react_agent.ActionExecutor') as mock_executor_cls:
            
            mock_memory = Mock()
            mock_memory.retrieve_context.return_value = {
                "user_profile": {"user_id": "test"},
                "conversation_history": [],
                "essay_state": {}
            }
            mock_memory_cls.return_value = mock_memory
            
            mock_reasoning = Mock()
            mock_reasoning.get_performance_metrics.return_value = {}
            mock_reasoning_cls.return_value = mock_reasoning
            
            mock_executor = Mock()
            mock_executor.get_performance_metrics.return_value = {}
            mock_executor_cls.return_value = mock_executor
            
            agent = EssayReActAgent("test_user")
            context = agent._observe()
            
            assert "user_profile" in context
            assert "session_info" in context
            assert "agent_metrics" in context
    
    def test_observe_context_failure(self):
        """Test context observation with failure."""
        with patch('essay_agent.agent.core.react_agent.AgentMemory') as mock_memory_cls, \
             patch('essay_agent.agent.core.react_agent.PromptBuilder'), \
             patch('essay_agent.agent.core.react_agent.PromptOptimizer'), \
             patch('essay_agent.agent.core.react_agent.ReasoningEngine') as mock_reasoning_cls, \
             patch('essay_agent.agent.core.react_agent.ActionExecutor') as mock_executor_cls:
            
            mock_memory = Mock()
            mock_memory.retrieve_context.side_effect = Exception("Memory error")
            mock_memory_cls.return_value = mock_memory
            
            mock_reasoning = Mock()
            mock_reasoning.get_performance_metrics.return_value = {}
            mock_reasoning_cls.return_value = mock_reasoning
            
            mock_executor = Mock()
            mock_executor.get_performance_metrics.return_value = {}
            mock_executor_cls.return_value = mock_executor
            
            agent = EssayReActAgent("test_user")
            context = agent._observe()
            
            assert "error" in context
            assert context["user_profile"]["user_id"] == "test_user"
    
    def test_format_tool_response(self):
        """Test tool response formatting."""
        with patch('essay_agent.agent.core.react_agent.AgentMemory'), \
             patch('essay_agent.agent.core.react_agent.PromptBuilder'), \
             patch('essay_agent.agent.core.react_agent.PromptOptimizer'), \
             patch('essay_agent.agent.core.react_agent.ReasoningEngine'), \
             patch('essay_agent.agent.core.react_agent.ActionExecutor'):
            
            agent = EssayReActAgent("test_user")
            
            # Test brainstorm response
            action_result = ActionResult(
                action_type="tool_execution",
                success=True,
                result="1. Idea one\n2. Idea two",
                execution_time=1.0,
                tool_name="brainstorm"
            )
            reasoning = Mock()
            
            response = agent._format_tool_response(action_result, reasoning)
            assert "brainstormed" in response.lower()
            assert "ideas" in response.lower()
            
            # Test outline response
            action_result.tool_name = "outline"
            action_result.result = "I. Introduction\nII. Body"
            
            response = agent._format_tool_response(action_result, reasoning)
            assert "outline" in response.lower()
            assert "structure" in response.lower()
    
    def test_get_session_metrics(self):
        """Test session metrics calculation."""
        with patch('essay_agent.agent.core.react_agent.AgentMemory'), \
             patch('essay_agent.agent.core.react_agent.PromptBuilder'), \
             patch('essay_agent.agent.core.react_agent.PromptOptimizer'), \
             patch('essay_agent.agent.core.react_agent.ReasoningEngine') as mock_reasoning_cls, \
             patch('essay_agent.agent.core.react_agent.ActionExecutor') as mock_executor_cls:
            
            mock_reasoning = Mock()
            mock_reasoning.get_performance_metrics.return_value = {"reasoning": "metrics"}
            mock_reasoning_cls.return_value = mock_reasoning
            
            mock_executor = Mock()
            mock_executor.get_performance_metrics.return_value = {"execution": "metrics"}
            mock_executor_cls.return_value = mock_executor
            
            agent = EssayReActAgent("test_user")
            agent.interaction_count = 5
            agent.total_response_time = 25.0
            
            # Simulate some time passing
            time.sleep(0.1)
            
            metrics = agent.get_session_metrics()
            
            assert metrics["interaction_count"] == 5
            assert metrics["total_response_time"] == 25.0
            assert metrics["average_response_time"] == 5.0
            assert "reasoning_metrics" in metrics
            assert "execution_metrics" in metrics 