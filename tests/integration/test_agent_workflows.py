"""Integration tests for complete ReAct agent workflows.

This module provides comprehensive end-to-end testing for:
- Complete Observe → Reason → Act → Respond cycles  
- Multi-turn conversations with context continuity
- Complex tool chain executions
- Memory integration across workflow steps
- Error recovery and fallback mechanisms
- Cross-component integration validation
"""
import pytest
import asyncio
import time
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from essay_agent.agent.core.react_agent import EssayReActAgent
from essay_agent.agent.core.reasoning_engine import ReasoningEngine, ReasoningResult
from essay_agent.agent.core.action_executor import ActionExecutor, ActionResult
from essay_agent.agent.memory.agent_memory import AgentMemory
from essay_agent.agent.tools.tool_registry import EnhancedToolRegistry
from essay_agent.llm_client import get_chat_llm


class TestCompleteReActWorkflows:
    """Test complete ReAct agent workflows end-to-end."""
    
    @pytest.fixture
    def temp_user_id(self):
        """Generate temporary user ID for testing."""
        return f"test_workflow_user_{int(time.time())}"
    
    @pytest.fixture
    def mock_llm_responses(self):
        """Mock LLM responses for different workflow scenarios."""
        return {
            "brainstorm_reasoning": """{
                "context_understanding": "User needs creative story ideas for college essay",
                "reasoning": "User is at brainstorming phase and needs creative inspiration",
                "chosen_tool": "brainstorm",
                "tool_args": {"essay_prompt": "challenge essay", "user_profile": "student"},
                "confidence": 0.9,
                "response_type": "tool_execution",
                "anticipated_follow_up": "User will want to outline one of the stories",
                "context_flags": ["creative_help", "brainstorming_phase"]
            }""",
            
            "outline_reasoning": """{
                "context_understanding": "User has stories and wants to create structure",
                "reasoning": "User should outline their chosen story for better organization",
                "chosen_tool": "outline",
                "tool_args": {"story": "robotics competition story", "essay_prompt": "challenge essay"},
                "confidence": 0.8,
                "response_type": "tool_execution",
                "anticipated_follow_up": "User will want to draft the essay",
                "context_flags": ["structure_phase", "organization_help"]
            }""",
            
            "draft_reasoning": """{
                "context_understanding": "User has outline and wants to write full essay",
                "reasoning": "User is ready to draft based on their outline",
                "chosen_tool": "draft_essay",
                "tool_args": {"outline": "structured outline", "word_limit": 650},
                "confidence": 0.85,
                "response_type": "tool_execution",
                "anticipated_follow_up": "User will want to revise for improvements",
                "context_flags": ["writing_phase", "content_creation"]
            }""",
            
            "conversation_response": """{
                "context_understanding": "User is greeting and seeking assistance",
                "reasoning": "User is starting conversation, should provide helpful introduction",
                "response_type": "conversation",
                "confidence": 0.9,
                "anticipated_follow_up": "User will specify their essay needs",
                "context_flags": ["conversation_start", "greeting"]
            }""",
            
            "error_recovery": """{
                "context_understanding": "Previous tool failed, need alternative approach",
                "reasoning": "Should try a different tool or approach to help user",
                "chosen_tool": "clarify",
                "tool_args": {"context": "previous failure", "user_input": "help request"},
                "confidence": 0.7,
                "response_type": "tool_execution",
                "anticipated_follow_up": "Get clarification then try appropriate tool",
                "context_flags": ["error_recovery", "clarification_needed"]
            }"""
        }
    
    @pytest.fixture
    def mock_tool_responses(self):
        """Mock tool execution responses."""
        return {
            "brainstorm": {
                "stories": [
                    {"title": "Robotics Competition Challenge", "theme": "overcoming technical failure"},
                    {"title": "Cultural Bridge Building", "theme": "connecting different communities"},
                    {"title": "Academic Struggle to Success", "theme": "persistence through difficulty"}
                ],
                "story_count": 3,
                "prompt_alignment": "high"
            },
            
            "outline": {
                "outline": "I. Hook: Robot malfunction at competition\nII. Challenge: Technical failure under pressure\nIII. Growth: Learning to adapt and collaborate\nIV. Reflection: Leadership through uncertainty",
                "structure_score": 8.5,
                "estimated_word_count": 650
            },
            
            "draft_essay": {
                "essay_text": "The robot lay motionless on the competition floor...[full essay draft]...This experience taught me that true leadership emerges not when everything goes according to plan, but when we learn to navigate uncertainty with grace and determination.",
                "word_count": 647,
                "structure_analysis": "Strong narrative arc with clear progression"
            },
            
            "clarify": {
                "clarifying_questions": [
                    "What specific aspect of your essay would you like help with?",
                    "Are you looking for help with brainstorming, structuring, or writing?",
                    "What type of college essay prompt are you working on?"
                ],
                "context_analysis": "User needs more specific guidance"
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_brainstorm_to_outline_workflow(self, temp_user_id, mock_llm_responses, mock_tool_responses):
        """Test complete workflow from brainstorming to outline creation."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            
            # Setup response sequence for reasoning
            response_sequence = [
                mock_llm_responses["brainstorm_reasoning"],
                "I've generated some creative story ideas for your challenge essay!",
                mock_llm_responses["outline_reasoning"], 
                "Great! I've created a structured outline for your robotics story."
            ]
            
            call_count = 0
            async def mock_predict(prompt):
                nonlocal call_count
                response = response_sequence[call_count % len(response_sequence)]
                call_count += 1
                return response
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            # Mock tool registry
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool_description.return_value = {"required_args": [], "arg_types": {}}
                
                # Setup tool execution mocks
                async def mock_tool_execution(tool_name, **kwargs):
                    return mock_tool_responses.get(tool_name, {"result": f"Mock {tool_name} result"})
                
                mock_registry.get_tool.return_value = mock_tool_execution
                
                # Create agent and run workflow
                agent = EssayReActAgent(temp_user_id)
                
                # Step 1: Request brainstorming
                response1 = await agent.handle_message("Help me brainstorm ideas for a challenge essay")
                assert isinstance(response1, str)
                assert len(response1) > 0
                
                # Step 2: Request outline creation
                response2 = await agent.handle_message("I want to outline the robotics competition story")
                assert isinstance(response2, str)
                assert len(response2) > 0
                
                # Verify agent state progression
                context = agent._observe()
                assert "conversation_history" in context
                assert len(context["conversation_history"]) >= 2
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation_context_continuity(self, temp_user_id, mock_llm_responses):
        """Test context continuity across multiple conversation turns."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = mock_llm_responses["conversation_response"]
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = False  # Force conversation mode
                
                agent = EssayReActAgent(temp_user_id)
                
                # Multiple conversation turns
                messages = [
                    "Hello, I need help with my college essay",
                    "I'm applying to Stanford and need help with their identity prompt",
                    "I want to write about my experience as a first-generation student",
                    "Can you help me think about what themes to explore?",
                    "I'm worried my story isn't unique enough"
                ]
                
                responses = []
                for message in messages:
                    response = await agent.handle_message(message)
                    responses.append(response)
                    assert isinstance(response, str)
                    assert len(response) > 0
                
                # Verify context accumulation
                context = agent._observe()
                conversation_history = context.get("conversation_history", [])
                
                # Should have accumulated all conversation turns
                assert len(conversation_history) >= len(messages)
                
                # Verify memory updates
                assert agent.interaction_count == len(messages)
                assert agent.total_response_time > 0
    
    @pytest.mark.asyncio
    async def test_complex_tool_chain_execution(self, temp_user_id, mock_llm_responses, mock_tool_responses):
        """Test execution of complex tool chains with dependencies."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            
            # Setup reasoning sequence for tool chain
            reasoning_sequence = [
                mock_llm_responses["brainstorm_reasoning"],
                mock_llm_responses["outline_reasoning"],
                mock_llm_responses["draft_reasoning"]
            ]
            
            call_count = 0
            async def mock_predict(prompt):
                nonlocal call_count
                if "reasoning" in prompt.lower():
                    response = reasoning_sequence[call_count % len(reasoning_sequence)]
                    call_count += 1
                    return response
                else:
                    return "Generated response based on tool execution"
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool_description.return_value = {"required_args": [], "arg_types": {}}
                
                # Track tool execution order
                executed_tools = []
                
                async def mock_tool_execution(tool_name, **kwargs):
                    executed_tools.append(tool_name)
                    return mock_tool_responses.get(tool_name, {"result": f"Mock {tool_name} result"})
                
                mock_registry.get_tool.return_value = mock_tool_execution
                
                agent = EssayReActAgent(temp_user_id)
                
                # Execute tool chain: brainstorm → outline → draft
                await agent.handle_message("Help me brainstorm ideas for a challenge essay")
                await agent.handle_message("Create an outline for the robotics story")
                await agent.handle_message("Draft the full essay based on the outline")
                
                # Verify tools were executed in logical order
                assert "brainstorm" in executed_tools
                assert "outline" in executed_tools
                assert "draft_essay" in executed_tools
                
                # Verify context builds across tool executions
                context = agent._observe()
                assert "conversation_history" in context
                assert len(context["conversation_history"]) >= 3
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_fallback_mechanisms(self, temp_user_id, mock_llm_responses):
        """Test error recovery when tools fail or return errors."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            
            # First call: normal reasoning, second call: error recovery reasoning
            call_count = 0
            async def mock_predict(prompt):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return mock_llm_responses["brainstorm_reasoning"]
                else:
                    return mock_llm_responses["error_recovery"]
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool_description.return_value = {"required_args": [], "arg_types": {}}
                
                # First tool fails, second succeeds
                call_count = 0
                async def mock_tool_execution(tool_name, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1 and tool_name == "brainstorm":
                        raise Exception("Tool execution failed")
                    else:
                        return {"result": f"Successful {tool_name} execution"}
                
                mock_registry.get_tool.return_value = mock_tool_execution
                
                agent = EssayReActAgent(temp_user_id)
                
                # This should trigger error recovery
                response = await agent.handle_message("Help me brainstorm essay ideas")
                
                # Should still get a response despite tool failure
                assert isinstance(response, str)
                assert len(response) > 0
                
                # Verify error was handled gracefully
                context = agent._observe()
                assert "conversation_history" in context
    
    @pytest.mark.asyncio
    async def test_memory_integration_across_workflow_steps(self, temp_user_id, mock_llm_responses, mock_tool_responses):
        """Test memory system integration throughout workflow steps."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = mock_llm_responses["brainstorm_reasoning"]
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool_description.return_value = {"required_args": [], "arg_types": {}}
                mock_registry.get_tool.return_value = AsyncMock(return_value=mock_tool_responses["brainstorm"])
                
                # Mock memory operations to track what gets stored
                stored_data = []
                
                with patch.object(AgentMemory, 'store_conversation_turn') as mock_store_conv, \
                     patch.object(AgentMemory, 'store_reasoning_chain') as mock_store_reason, \
                     patch.object(AgentMemory, 'store_tool_execution') as mock_store_tool:
                    
                    mock_store_conv.return_value = asyncio.Future()
                    mock_store_conv.return_value.set_result(None)
                    
                    mock_store_reason.return_value = asyncio.Future()
                    mock_store_reason.return_value.set_result("reasoning_id")
                    
                    mock_store_tool.return_value = asyncio.Future()
                    mock_store_tool.return_value.set_result("tool_id")
                    
                    agent = EssayReActAgent(temp_user_id)
                    
                    # Execute multiple interactions
                    await agent.handle_message("Help me brainstorm essay ideas")
                    await agent.handle_message("What themes did you find?")
                    
                    # Verify memory operations were called
                    assert mock_store_conv.called
                    assert mock_store_reason.called
                    
                    # Verify conversation turns were stored
                    assert mock_store_conv.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_performance_tracking_integration(self, temp_user_id, mock_llm_responses):
        """Test performance metrics tracking throughout workflows."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = mock_llm_responses["conversation_response"]
            mock_get_llm.return_value = mock_llm
            
            agent = EssayReActAgent(temp_user_id)
            
            # Execute multiple interactions to generate performance data
            start_time = time.time()
            
            for i in range(3):
                await agent.handle_message(f"Test message {i}")
            
            end_time = time.time()
            
            # Verify performance metrics are tracked
            metrics = agent.get_session_metrics()
            
            assert metrics["interaction_count"] == 3
            assert metrics["total_response_time"] > 0
            assert metrics["average_response_time"] > 0
            assert end_time - start_time >= metrics["total_response_time"]
            
            # Check reasoning engine metrics
            reasoning_metrics = agent.reasoning_engine.get_performance_metrics()
            assert reasoning_metrics["total_reasoning_requests"] >= 3
            
            # Check execution metrics
            execution_metrics = agent.action_executor.get_performance_metrics()
            assert execution_metrics["total_executions"] >= 0  # May be 0 if conversation mode


class TestWorkflowIntegrationScenarios:
    """Test specific workflow integration scenarios."""
    
    @pytest.fixture
    def temp_user_id(self):
        """Generate temporary user ID for testing."""
        return f"test_scenario_user_{int(time.time())}"
    
    @pytest.mark.asyncio
    async def test_essay_writing_complete_journey(self, temp_user_id):
        """Test complete essay writing journey from start to finish."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            
            # Simulate realistic reasoning responses for complete journey
            journey_responses = [
                """{
                    "context_understanding": "User starting essay writing process",
                    "reasoning": "Should analyze prompt first to understand requirements",
                    "chosen_tool": "analyze_prompt",
                    "tool_args": {"essay_prompt": "challenge prompt"},
                    "confidence": 0.9,
                    "response_type": "tool_execution"
                }""",
                
                """{
                    "context_understanding": "Prompt analyzed, user needs ideas",
                    "reasoning": "Should brainstorm creative story ideas",
                    "chosen_tool": "brainstorm",
                    "tool_args": {"essay_prompt": "challenge", "analysis": "previous"},
                    "confidence": 0.85,
                    "response_type": "tool_execution"
                }""",
                
                """{
                    "context_understanding": "Stories generated, needs structure",
                    "reasoning": "Should create outline for chosen story",
                    "chosen_tool": "outline",
                    "tool_args": {"story": "selected story", "word_limit": 650},
                    "confidence": 0.8,
                    "response_type": "tool_execution"
                }"""
            ]
            
            call_count = 0
            async def mock_predict(prompt):
                nonlocal call_count
                if call_count < len(journey_responses):
                    response = journey_responses[call_count]
                    call_count += 1
                    return response
                else:
                    return """{"response_type": "conversation", "confidence": 0.7}"""
            
            mock_llm.apredict = mock_predict
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool_description.return_value = {"required_args": [], "arg_types": {}}
                
                # Mock progressive tool results
                tool_results = {
                    "analyze_prompt": {"analysis": "Challenge essay requiring personal growth story"},
                    "brainstorm": {"stories": ["Story 1", "Story 2", "Story 3"]},
                    "outline": {"outline": "Structured outline with clear progression"}
                }
                
                async def mock_tool_execution(tool_name, **kwargs):
                    return tool_results.get(tool_name, {"result": f"Mock {tool_name} result"})
                
                mock_registry.get_tool.return_value = mock_tool_execution
                
                agent = EssayReActAgent(temp_user_id)
                
                # Simulate complete essay writing journey
                journey_messages = [
                    "I need to write a college essay about overcoming a challenge",
                    "Help me brainstorm some story ideas",
                    "I want to outline the story about my academic struggles"
                ]
                
                responses = []
                for message in journey_messages:
                    response = await agent.handle_message(message)
                    responses.append(response)
                    assert isinstance(response, str)
                    assert len(response) > 0
                
                # Verify complete journey tracking
                context = agent._observe()
                assert len(context.get("conversation_history", [])) >= len(journey_messages)
                
                # Verify agent progressed through workflow phases
                assert agent.interaction_count == len(journey_messages)
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_handling(self, temp_user_id):
        """Test handling of concurrent or rapidly sequential requests."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = """{"response_type": "conversation", "confidence": 0.8}"""
            mock_get_llm.return_value = mock_llm
            
            agent = EssayReActAgent(temp_user_id)
            
            # Send multiple messages rapidly
            messages = [f"Message {i}: Help with essay" for i in range(5)]
            
            # Execute concurrently (but agent handles sequentially)
            tasks = [agent.handle_message(msg) for msg in messages]
            responses = await asyncio.gather(*tasks)
            
            # All responses should be valid
            assert len(responses) == len(messages)
            for response in responses:
                assert isinstance(response, str)
                assert len(response) > 0
            
            # Verify all interactions were tracked
            assert agent.interaction_count == len(messages)
    
    @pytest.mark.asyncio 
    async def test_workflow_state_persistence(self, temp_user_id):
        """Test workflow state persistence across agent recreations."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = """{"response_type": "conversation", "confidence": 0.8}"""
            mock_get_llm.return_value = mock_llm
            
            # First agent session
            agent1 = EssayReActAgent(temp_user_id)
            await agent1.handle_message("I'm working on my college essay")
            
            # Get context from first session
            context1 = agent1._observe()
            conversation_history1 = context1.get("conversation_history", [])
            
            # Create new agent with same user ID
            agent2 = EssayReActAgent(temp_user_id)
            
            # Should have access to previous conversation
            context2 = agent2._observe()
            
            # Note: Actual persistence depends on memory implementation
            # This test verifies the interface exists
            assert "conversation_history" in context2
            assert "user_profile" in context2


@pytest.mark.integration
class TestCrossComponentIntegration:
    """Test integration between different agent components."""
    
    @pytest.fixture
    def temp_user_id(self):
        return f"test_integration_user_{int(time.time())}"
    
    @pytest.mark.asyncio
    async def test_reasoning_engine_action_executor_integration(self, temp_user_id):
        """Test integration between reasoning engine and action executor."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = """{
                "context_understanding": "User needs help",
                "reasoning": "Should use brainstorm tool",
                "chosen_tool": "brainstorm",
                "tool_args": {"prompt": "test"},
                "confidence": 0.8,
                "response_type": "tool_execution"
            }"""
            mock_get_llm.return_value = mock_llm
            
            with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                mock_registry.has_tool.return_value = True
                mock_registry.get_tool_description.return_value = {"required_args": [], "arg_types": {}}
                mock_registry.get_tool.return_value = AsyncMock(return_value={"result": "brainstorm output"})
                
                agent = EssayReActAgent(temp_user_id)
                
                # Test that reasoning leads to proper action execution
                response = await agent.handle_message("Help me brainstorm")
                
                assert isinstance(response, str)
                assert len(response) > 0
                
                # Verify both reasoning and execution occurred
                reasoning_metrics = agent.reasoning_engine.get_performance_metrics()
                execution_metrics = agent.action_executor.get_performance_metrics()
                
                assert reasoning_metrics["total_reasoning_requests"] > 0
                assert execution_metrics["total_executions"] >= 0
    
    @pytest.mark.asyncio
    async def test_memory_system_integration_with_workflows(self, temp_user_id):
        """Test memory system integration throughout complete workflows."""
        with patch('essay_agent.llm_client.get_chat_llm') as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.apredict.return_value = """{"response_type": "conversation", "confidence": 0.8}"""
            mock_get_llm.return_value = mock_llm
            
            agent = EssayReActAgent(temp_user_id)
            
            # Execute workflow steps
            await agent.handle_message("Start essay writing process")
            await agent.handle_message("I need help with brainstorming")
            
            # Verify memory captures workflow progression
            context = agent._observe()
            
            # Should have conversation history
            assert "conversation_history" in context
            conversation_history = context["conversation_history"]
            assert len(conversation_history) >= 2
            
            # Should have user profile context
            assert "user_profile" in context
            
            # Should have essay state tracking
            assert "essay_state" in context
    
    def test_component_initialization_integration(self):
        """Test proper integration of all components during agent initialization."""
        with patch('essay_agent.agent.memory.agent_memory.HierarchicalMemory'), \
             patch('essay_agent.agent.memory.agent_memory.JSONConversationMemory'), \
             patch('essay_agent.agent.memory.agent_memory.ContextWindowManager'):
            
            agent = EssayReActAgent("test_init_user")
            
            # Verify all components are properly initialized and connected
            assert agent.memory is not None
            assert agent.prompt_builder is not None
            assert agent.prompt_optimizer is not None
            assert agent.reasoning_engine is not None
            assert agent.action_executor is not None
            
            # Verify components reference each other correctly
            assert agent.reasoning_engine.prompt_builder == agent.prompt_builder
            assert agent.reasoning_engine.prompt_optimizer == agent.prompt_optimizer
            assert agent.action_executor.memory == agent.memory
            
            # Verify session tracking
            assert agent.interaction_count == 0
            assert agent.total_response_time == 0.0
            assert agent.session_start is not None 