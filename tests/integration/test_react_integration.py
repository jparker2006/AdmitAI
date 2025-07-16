"""Integration tests for ReAct agent end-to-end workflows.

This module provides comprehensive integration testing for the complete ReAct agent
implementation, testing real workflow scenarios with minimal mocking.
"""
import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any
from unittest.mock import patch, AsyncMock

from essay_agent.agent.core.react_agent import EssayReActAgent
from essay_agent.agent.core.reasoning_engine import ReasoningResult
from essay_agent.agent.core.action_executor import ActionResult


@pytest.fixture
def temp_user_id():
    """Generate a temporary user ID for testing."""
    return f"test_user_{os.getpid()}"


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for predictable testing."""
    return {
        "brainstorm_reasoning": """{
            "context_understanding": "User wants help brainstorming essay ideas",
            "reasoning": "The user needs creative ideas for their essay topic. I should use the brainstorm tool to generate multiple story ideas they can choose from.",
            "response_type": "tool_execution",
            "chosen_tool": "brainstorm",
            "tool_args": {"topic": "overcoming challenges", "count": 5},
            "confidence": 0.9,
            "anticipated_follow_up": "User will select an idea to develop further",
            "context_flags": ["first_interaction", "needs_ideas"]
        }""",
        
        "outline_reasoning": """{
            "context_understanding": "User has selected a story idea and wants to create an outline",
            "reasoning": "The user has chosen their story about overcoming stage fright. Now they need a structured outline to organize their thoughts.",
            "response_type": "tool_execution", 
            "chosen_tool": "outline",
            "tool_args": {"story_idea": "overcoming stage fright in school play", "essay_type": "personal"},
            "confidence": 0.85,
            "anticipated_follow_up": "User will want to start drafting sections",
            "context_flags": ["has_story_idea", "ready_to_outline"]
        }""",
        
        "conversation_reasoning": """{
            "context_understanding": "User is feeling stuck and needs encouragement",
            "reasoning": "The user seems overwhelmed. I should provide supportive guidance and break down the task into manageable steps.",
            "response_type": "conversation",
            "chosen_tool": null,
            "tool_args": {},
            "confidence": 0.8,
            "anticipated_follow_up": "User will feel more confident to continue",
            "context_flags": ["feeling_stuck", "needs_encouragement"]
        }""",
        
        "response_generation": "I've brainstormed some great ideas for your essay! Here are five story ideas about overcoming challenges:\n\n1. **Overcoming Stage Fright**: The time you had to perform in the school play despite being terrified of speaking in public.\n\n2. **Learning a Difficult Skill**: When you struggled to learn a musical instrument or sport but persevered through frustration.\n\n3. **Standing Up for Others**: A moment when you found the courage to defend someone being bullied or treated unfairly.\n\n4. **Academic Challenge**: Conquering a subject that seemed impossible, like advanced math or a foreign language.\n\n5. **Personal Growth**: Overcoming a fear of trying new things by joining a club or activity outside your comfort zone.\n\nWhich of these resonates with you, or would you like to explore other directions?"
    }


class TestReActIntegration:
    """Integration tests for complete ReAct workflows."""
    
    @pytest.mark.asyncio
    async def test_brainstorm_workflow_end_to_end(self, temp_user_id, mock_llm_responses):
        """Test complete brainstorming workflow from user input to response."""
        # Mock the LLM calls with realistic responses
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            
            # Setup response sequence
            call_count = 0
            async def mock_predict(prompt):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return mock_llm_responses["brainstorm_reasoning"]
                else:
                    return mock_llm_responses["response_generation"]
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            # Mock the brainstorm tool
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool.return_value = AsyncMock(return_value="Mocked brainstorm result")
                mock_registry.get_tool_description.return_value = {
                    "required_args": ["topic"],
                    "arg_types": {"topic": str}
                }
                
                # Create agent and test workflow
                agent = EssayReActAgent(temp_user_id)
                
                user_input = "I need help brainstorming ideas for my college essay about overcoming challenges"
                response = await agent.handle_message(user_input)
                
                # Verify response quality
                assert isinstance(response, str)
                assert len(response) > 50  # Substantial response
                assert "brainstorm" in response.lower() or "ideas" in response.lower()
                
                # Verify agent state
                assert agent.interaction_count == 1
                assert agent.total_response_time > 0
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation_flow(self, temp_user_id, mock_llm_responses):
        """Test multi-turn conversation with memory continuity."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            
            # Track conversation turns
            conversation_turn = 0
            
            async def mock_predict(prompt):
                nonlocal conversation_turn
                conversation_turn += 1
                
                if conversation_turn <= 2:  # First exchange (reasoning + response)
                    if "context_understanding" in prompt or "reasoning" in prompt:
                        return mock_llm_responses["brainstorm_reasoning"]
                    else:
                        return "I'd love to help you brainstorm! What's your essay topic?"
                        
                elif conversation_turn <= 4:  # Second exchange
                    if "context_understanding" in prompt:
                        return mock_llm_responses["outline_reasoning"] 
                    else:
                        return "Great choice! Let me help you outline that story."
                        
                else:  # Third exchange
                    if "context_understanding" in prompt:
                        return mock_llm_responses["conversation_reasoning"]
                    else:
                        return "You're doing great! Take it one step at a time."
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            # Mock tools
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool.return_value = AsyncMock(return_value="Tool result")
                mock_registry.get_tool_description.return_value = {}
                
                agent = EssayReActAgent(temp_user_id)
                
                # First turn: Brainstorming request
                response1 = await agent.handle_message("Help me brainstorm essay ideas")
                assert len(response1) > 0
                assert agent.interaction_count == 1
                
                # Second turn: Story selection
                response2 = await agent.handle_message("I like the stage fright idea, help me outline it")
                assert len(response2) > 0
                assert agent.interaction_count == 2
                
                # Third turn: Encouragement needed
                response3 = await agent.handle_message("I'm feeling stuck and don't know how to continue")
                assert len(response3) > 0
                assert agent.interaction_count == 3
                
                # Verify conversation memory
                assert agent.total_response_time > 0
                metrics = agent.get_session_metrics()
                assert metrics["interaction_count"] == 3
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, temp_user_id, mock_llm_responses):
        """Test error recovery and graceful degradation."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            # First call succeeds, second call fails
            mock_llm = AsyncMock()
            call_count = 0
            
            async def mock_predict(prompt):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return mock_llm_responses["brainstorm_reasoning"]
                else:
                    raise Exception("LLM service temporarily unavailable")
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            # Mock failing tool
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool.side_effect = Exception("Tool execution failed")
                mock_registry.get_tool_description.return_value = {}
                
                agent = EssayReActAgent(temp_user_id)
                
                # This should handle the error gracefully
                response = await agent.handle_message("Help me with my essay")
                
                # Should still get a helpful response despite errors
                assert isinstance(response, str)
                assert len(response) > 0
                assert ("help" in response.lower() or 
                        "sorry" in response.lower() or 
                        "issue" in response.lower())
    
    @pytest.mark.asyncio
    async def test_tool_validation_and_execution(self, temp_user_id, mock_llm_responses):
        """Test tool validation and execution pathways."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = mock_llm_responses["brainstorm_reasoning"]
            mock_get_llm.return_value = mock_llm
            
            # Mock tool registry with validation
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool_description.return_value = {
                    "required_args": ["topic"],
                    "arg_types": {"topic": str}
                }
                
                # Mock successful tool execution
                async def mock_tool(**kwargs):
                    assert "topic" in kwargs
                    return f"Brainstormed ideas for: {kwargs['topic']}"
                
                mock_registry.get_tool.return_value = mock_tool
                
                agent = EssayReActAgent(temp_user_id)
                response = await agent.handle_message("Brainstorm ideas about resilience")
                
                assert isinstance(response, str)
                assert len(response) > 0
                
                # Verify tool was called with proper validation
                mock_registry.has_tool.assert_called()
                mock_registry.get_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, temp_user_id, mock_llm_responses):
        """Test performance metrics tracking across interactions."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = mock_llm_responses["conversation_reasoning"]
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool.return_value = AsyncMock(return_value="Result")
                mock_registry.get_tool_description.return_value = {}
                
                agent = EssayReActAgent(temp_user_id)
                
                # Multiple interactions
                await agent.handle_message("First message")
                await agent.handle_message("Second message") 
                await agent.handle_message("Third message")
                
                # Check performance metrics
                metrics = agent.get_session_metrics()
                
                assert metrics["interaction_count"] == 3
                assert metrics["total_response_time"] > 0
                assert metrics["average_response_time"] > 0
                assert "reasoning_metrics" in metrics
                assert "execution_metrics" in metrics
                
                # Check reasoning engine metrics
                reasoning_metrics = agent.reasoning_engine.get_performance_metrics()
                assert reasoning_metrics["total_reasoning_requests"] >= 3
                
                # Check action executor metrics
                execution_metrics = agent.action_executor.get_performance_metrics()
                assert execution_metrics["total_executions"] >= 3
    
    @pytest.mark.asyncio
    async def test_context_continuity_across_turns(self, temp_user_id, mock_llm_responses):
        """Test that context is maintained across conversation turns."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            
            # Track what context is being passed to the reasoning engine
            observed_contexts = []
            
            async def mock_predict(prompt):
                # Capture context information from prompts
                if "conversation_history" in prompt:
                    observed_contexts.append("has_history")
                if "essay_state" in prompt:
                    observed_contexts.append("has_essay_state")
                return mock_llm_responses["conversation_reasoning"]
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool.return_value = AsyncMock(return_value="Result")
                mock_registry.get_tool_description.return_value = {}
                
                agent = EssayReActAgent(temp_user_id)
                
                # First interaction establishes context
                await agent.handle_message("I'm working on a college essay about leadership")
                
                # Second interaction should have access to previous context
                await agent.handle_message("Can you help me develop that theme further?")
                
                # Verify context was maintained
                assert agent.interaction_count == 2
                
                # Check that observation is working
                context = agent._observe()
                assert "session_info" in context
                assert context["session_info"]["interaction_count"] == 2
    
    @pytest.mark.asyncio
    async def test_different_response_types(self, temp_user_id, mock_llm_responses):
        """Test handling of different response types (tool vs conversation)."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            
            # Alternate between tool execution and conversation
            response_type_toggle = True
            
            async def mock_predict(prompt):
                nonlocal response_type_toggle
                response_type_toggle = not response_type_toggle
                
                if response_type_toggle:
                    return mock_llm_responses["brainstorm_reasoning"]  # Tool execution
                else:
                    return mock_llm_responses["conversation_reasoning"]  # Conversation
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool.return_value = AsyncMock(return_value="Tool output")
                mock_registry.get_tool_description.return_value = {}
                
                agent = EssayReActAgent(temp_user_id)
                
                # Tool execution response
                response1 = await agent.handle_message("Help me brainstorm")
                assert len(response1) > 0
                
                # Conversation response
                response2 = await agent.handle_message("I'm feeling overwhelmed")
                assert len(response2) > 0
                
                # Both should be valid responses
                assert isinstance(response1, str)
                assert isinstance(response2, str)
                
                # Verify different response paths were taken
                execution_metrics = agent.action_executor.get_performance_metrics()
                assert execution_metrics["total_executions"] == 2


@pytest.mark.asyncio
async def test_react_agent_memory_integration(temp_user_id):
    """Test integration between ReAct agent and memory system."""
    # This test uses more real components to test actual integration
    with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.apredict.return_value = """{
            "context_understanding": "User greeting",
            "reasoning": "User is starting conversation",
            "response_type": "conversation",
            "confidence": 0.8
        }"""
        mock_get_llm.return_value = mock_llm
        
        # Use a temporary directory for memory storage
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('essay_agent.agent.memory.agent_memory.HierarchicalMemory') as mock_hierarchical:
                # Mock the memory components to avoid file system dependencies
                mock_hierarchical.return_value = Mock()
                
                agent = EssayReActAgent(temp_user_id)
                
                # Test that memory methods are called
                response = await agent.handle_message("Hello, I need help with my essay")
                
                assert isinstance(response, str)
                assert len(response) > 0
                
                # Verify memory integration points were called
                # The exact calls depend on the memory implementation
                assert agent.memory is not None


class TestReActStressScenarios:
    """Stress testing for ReAct agent under various conditions."""
    
    @pytest.mark.asyncio
    async def test_rapid_sequential_messages(self, temp_user_id, mock_llm_responses):
        """Test handling of rapid sequential messages."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = mock_llm_responses["conversation_reasoning"]
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool.return_value = AsyncMock(return_value="Quick result")
                mock_registry.get_tool_description.return_value = {}
                
                agent = EssayReActAgent(temp_user_id)
                
                # Send multiple messages rapidly
                tasks = [
                    agent.handle_message(f"Message {i}")
                    for i in range(5)
                ]
                
                responses = await asyncio.gather(*tasks)
                
                # All should complete successfully
                assert len(responses) == 5
                for response in responses:
                    assert isinstance(response, str)
                    assert len(response) > 0
                
                # Check final state
                assert agent.interaction_count == 5
    
    @pytest.mark.asyncio
    async def test_long_conversation_session(self, temp_user_id, mock_llm_responses):
        """Test extended conversation session."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = mock_llm_responses["conversation_reasoning"]
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool.return_value = AsyncMock(return_value="Result")
                mock_registry.get_tool_description.return_value = {}
                
                agent = EssayReActAgent(temp_user_id)
                
                # Simulate long conversation (20 turns)
                for i in range(20):
                    response = await agent.handle_message(f"Turn {i}: Help with my essay")
                    assert len(response) > 0
                
                # Check performance metrics for long session
                metrics = agent.get_session_metrics()
                assert metrics["interaction_count"] == 20
                assert metrics["average_response_time"] > 0
                assert metrics["session_duration"] > 0 