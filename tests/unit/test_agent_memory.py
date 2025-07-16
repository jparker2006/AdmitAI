"""Unit tests for enhanced agent memory system.

Tests cover AgentMemory, ContextRetriever, MemoryIndexer, and ReAct data models
to ensure proper functionality of the memory system for ReAct operations.
"""
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from essay_agent.agent.memory import (
    AgentMemory,
    ContextRetriever,
    MemoryIndexer,
    ReasoningChain,
    ToolExecution,
    UsagePattern,
    ErrorPattern,
    ContextElement,
    RetrievedContext,
    MemoryStats,
    generate_id
)


class TestReActDataModels:
    """Test ReAct memory data models."""
    
    def test_reasoning_chain_creation(self):
        """Test creating a ReasoningChain with all fields."""
        from essay_agent.agent.memory.react_models import ReasoningStep
        
        steps = [
            ReasoningStep(
                step_number=1,
                thought="User needs help with brainstorming",
                tool_considered="brainstorm",
                confidence=0.9,
                context_used=["user_profile", "essay_prompt"]
            )
        ]
        
        chain = ReasoningChain(
            user_input="I need help brainstorming essay ideas",
            reasoning_steps=steps,
            final_action="brainstorm",
            result={"stories": ["story1", "story2"]},
            success=True,
            execution_time=2.5,
            context_tokens=150
        )
        
        assert chain.user_input == "I need help brainstorming essay ideas"
        assert len(chain.reasoning_steps) == 1
        assert chain.final_action == "brainstorm"
        assert chain.success is True
        assert chain.execution_time == 2.5
        assert chain.context_tokens == 150
        assert chain.id  # Should have generated ID
        assert chain.timestamp  # Should have timestamp
    
    def test_tool_execution_creation(self):
        """Test creating a ToolExecution record."""
        execution = ToolExecution(
            tool_name="brainstorm",
            input_params={"prompt": "challenge essay", "profile": "student"},
            result={"stories": [{"title": "Story 1"}]},
            execution_time=1.2,
            success=True,
            reasoning_context="User requested brainstorming for challenge essay",
            confidence_score=0.85,
            tokens_used=200
        )
        
        assert execution.tool_name == "brainstorm"
        assert execution.execution_time == 1.2
        assert execution.success is True
        assert execution.confidence_score == 0.85
        assert execution.tokens_used == 200
        assert execution.id  # Should have generated ID
    
    def test_usage_pattern_creation(self):
        """Test creating a UsagePattern."""
        pattern = UsagePattern(
            pattern_type="sequence",
            tools=["brainstorm", "outline"],
            frequency=5,
            success_rate=0.8,
            avg_execution_time=3.2,
            confidence=0.7,
            context_indicators=["essay", "help", "structure"]
        )
        
        assert pattern.pattern_type == "sequence"
        assert pattern.tools == ["brainstorm", "outline"]
        assert pattern.frequency == 5
        assert pattern.success_rate == 0.8
        assert pattern.confidence == 0.7
    
    def test_context_element_creation(self):
        """Test creating a ContextElement."""
        element = ContextElement(
            source="conversation",
            content={"role": "user", "content": "Help me write an essay"},
            relevance_score=0.9,
            tokens=15
        )
        
        assert element.source == "conversation"
        assert element.relevance_score == 0.9
        assert element.tokens == 15
        assert element.timestamp  # Should have timestamp


class TestMemoryIndexer:
    """Test MemoryIndexer functionality."""
    
    @pytest.fixture
    def temp_memory_dir(self):
        """Create temporary memory directory."""
        temp_dir = tempfile.mkdtemp()
        original_memory_store = Path("memory_store")
        
        # Mock the memory_store path
        with patch('essay_agent.agent.memory.memory_indexer.Path') as mock_path:
            mock_path.return_value = Path(temp_dir)
            yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def indexer(self, temp_memory_dir):
        """Create MemoryIndexer for testing."""
        with patch('essay_agent.agent.memory.memory_indexer.Path') as mock_path:
            mock_path.return_value = Path(temp_memory_dir)
            indexer = MemoryIndexer("test_user")
            return indexer
    
    def test_indexer_initialization(self, indexer):
        """Test MemoryIndexer initializes properly."""
        assert indexer.user_id == "test_user"
        assert isinstance(indexer.memory_index, dict)
        assert isinstance(indexer.pattern_cache, dict)
    
    def test_index_reasoning_chain(self, indexer):
        """Test indexing a reasoning chain."""
        from essay_agent.agent.memory.react_models import ReasoningStep
        
        steps = [ReasoningStep(
            step_number=1,
            thought="Need to brainstorm ideas",
            tool_considered="brainstorm",
            confidence=0.8
        )]
        
        chain = ReasoningChain(
            user_input="Help me brainstorm",
            reasoning_steps=steps,
            final_action="brainstorm",
            result={"stories": []},
            success=True
        )
        
        indexer.index_reasoning_chain(chain)
        
        # Check that chain was indexed
        assert chain.id in indexer.memory_index
        index_entry = indexer.memory_index[chain.id]
        assert index_entry.type == "reasoning_chain"
        assert "brainstorm" in index_entry.keywords
    
    def test_index_tool_execution(self, indexer):
        """Test indexing a tool execution."""
        execution = ToolExecution(
            tool_name="brainstorm",
            input_params={"prompt": "challenge"},
            result={"stories": ["story1"]},
            execution_time=1.0,
            success=True,
            reasoning_context="User needs brainstorming help"
        )
        
        indexer.index_tool_execution(execution)
        
        # Check that execution was indexed
        assert execution.id in indexer.memory_index
        index_entry = indexer.memory_index[execution.id]
        assert index_entry.type == "tool_execution"
        assert "brainstorm" in index_entry.keywords
    
    def test_detect_usage_patterns(self, indexer):
        """Test usage pattern detection."""
        # Mock recent tool executions
        executions = []
        for i in range(5):
            execution = ToolExecution(
                tool_name="brainstorm",
                input_params={},
                result={"stories": [f"story{i}"]},
                execution_time=1.0,
                success=True,
                reasoning_context="brainstorming help"
            )
            executions.append(execution)
        
        # Mock the method to return our test executions
        with patch.object(indexer, '_get_recent_tool_executions', return_value=executions):
            patterns = indexer.detect_usage_patterns(30)
        
        # Should detect frequency pattern for brainstorm tool
        assert len(patterns) > 0
        brainstorm_patterns = [p for p in patterns if "brainstorm" in p.tools]
        assert len(brainstorm_patterns) > 0
    
    def test_detect_error_patterns(self, indexer):
        """Test error pattern detection."""
        # Mock failed executions
        failed_executions = []
        for i in range(3):
            execution = ToolExecution(
                tool_name="validate",
                input_params={},
                result=None,
                execution_time=0.5,
                success=False,
                error_message="Validation failed: missing parameter",
                reasoning_context="validation attempt"
            )
            failed_executions.append(execution)
        
        with patch.object(indexer, '_get_failed_tool_executions', return_value=failed_executions):
            error_patterns = indexer.detect_error_patterns(30)
        
        # Should detect error pattern
        assert len(error_patterns) > 0
        validation_errors = [p for p in error_patterns if "validate" in p.tools_involved]
        assert len(validation_errors) > 0
    
    def test_memory_stats(self, indexer):
        """Test memory statistics calculation."""
        stats = indexer.get_memory_stats()
        
        assert isinstance(stats, MemoryStats)
        assert stats.total_reasoning_chains >= 0
        assert stats.total_tool_executions >= 0
        assert stats.success_rate >= 0.0
        assert stats.memory_size_mb >= 0.0


class TestContextRetriever:
    """Test ContextRetriever functionality."""
    
    @pytest.fixture
    def mock_memory_components(self):
        """Mock memory components for testing."""
        hierarchical_memory = Mock()
        semantic_search = Mock()
        conversation_memory = Mock()
        context_manager = Mock()
        
        return {
            "hierarchical_memory": hierarchical_memory,
            "semantic_search": semantic_search,
            "conversation_memory": conversation_memory,
            "context_manager": context_manager
        }
    
    @pytest.fixture
    def retriever(self, mock_memory_components):
        """Create ContextRetriever with mocked components."""
        with patch('essay_agent.agent.memory.context_retrieval.HierarchicalMemory') as mock_h, \
             patch('essay_agent.agent.memory.context_retrieval.SemanticSearchIndex') as mock_s, \
             patch('essay_agent.agent.memory.context_retrieval.JSONConversationMemory') as mock_c, \
             patch('essay_agent.agent.memory.context_retrieval.ContextWindowManager') as mock_cm:
            
            mock_h.return_value = mock_memory_components["hierarchical_memory"]
            mock_s.load_or_build.return_value = mock_memory_components["semantic_search"]
            mock_c.return_value = mock_memory_components["conversation_memory"]
            mock_cm.return_value = mock_memory_components["context_manager"]
            
            retriever = ContextRetriever("test_user")
            return retriever
    
    def test_retriever_initialization(self, retriever):
        """Test ContextRetriever initializes properly."""
        assert retriever.user_id == "test_user"
        assert retriever.hierarchical_memory is not None
        assert retriever.semantic_search is not None
    
    def test_retrieve_context_basic(self, retriever):
        """Test basic context retrieval."""
        # Mock conversation context
        mock_message = Mock()
        mock_message.type = "human"
        mock_message.content = "Help me brainstorm ideas"
        
        mock_buffer = Mock()
        mock_buffer.messages = [mock_message]
        retriever.conversation_memory.buffer = mock_buffer
        
        # Mock semantic search results
        retriever.semantic_search.search.return_value = []
        
        context = retriever.retrieve_context("I need help brainstorming")
        
        assert isinstance(context, RetrievedContext)
        assert context.query == "I need help brainstorming"
        assert context.total_tokens >= 0
        assert context.retrieval_time >= 0
    
    def test_context_optimization(self, retriever):
        """Test context optimization for token limits."""
        # Create large context elements
        large_elements = []
        for i in range(10):
            element = ContextElement(
                source="test",
                content={"data": "x" * 1000},  # Large content
                relevance_score=0.5,
                tokens=250  # Each element is 250 tokens
            )
            large_elements.append(element)
        
        # Test optimization with small token limit
        optimized, was_optimized = retriever._optimize_context_window(large_elements, 500)
        
        assert was_optimized  # Should have been optimized
        assert sum(e.tokens for e in optimized) <= 500  # Should fit budget
        assert len(optimized) <= len(large_elements)  # Should have fewer elements
    
    def test_relevance_scoring(self, retriever):
        """Test relevance scoring functionality."""
        elements = [
            ContextElement(
                source="conversation",
                content={"content": "help me brainstorm essay ideas"},
                relevance_score=0.0,  # Will be calculated
                tokens=50
            ),
            ContextElement(
                source="semantic",
                content={"description": "leadership experience"},
                relevance_score=0.0,
                tokens=30
            )
        ]
        
        # Calculate relevance for brainstorming query
        query = "I need brainstorming help"
        
        scored_elements = retriever._score_relevance(elements, query)
        
        # Should be sorted by relevance
        assert len(scored_elements) == 2
        # First element should have higher relevance (contains "brainstorm")
        assert "brainstorm" in scored_elements[0].content.get("content", "").lower()


class TestAgentMemory:
    """Test enhanced AgentMemory functionality."""
    
    @pytest.fixture
    def mock_memory_components(self):
        """Mock all memory components."""
        hierarchical_memory = Mock()
        conversation_memory = Mock()
        context_manager = Mock()
        context_retriever = Mock()
        memory_indexer = Mock()
        
        return {
            "hierarchical_memory": hierarchical_memory,
            "conversation_memory": conversation_memory,
            "context_manager": context_manager,
            "context_retriever": context_retriever,
            "memory_indexer": memory_indexer
        }
    
    @pytest.fixture
    def agent_memory(self, mock_memory_components):
        """Create AgentMemory with mocked components."""
        with patch('essay_agent.agent.memory.agent_memory.HierarchicalMemory') as mock_h, \
             patch('essay_agent.agent.memory.agent_memory.JSONConversationMemory') as mock_c, \
             patch('essay_agent.agent.memory.agent_memory.ContextWindowManager') as mock_cm, \
             patch('essay_agent.agent.memory.agent_memory.ContextRetriever') as mock_cr, \
             patch('essay_agent.agent.memory.agent_memory.MemoryIndexer') as mock_mi:
            
            mock_h.return_value = mock_memory_components["hierarchical_memory"]
            mock_c.return_value = mock_memory_components["conversation_memory"]
            mock_cm.return_value = mock_memory_components["context_manager"]
            mock_cr.return_value = mock_memory_components["context_retriever"]
            mock_mi.return_value = mock_memory_components["memory_indexer"]
            
            memory = AgentMemory("test_user")
            return memory
    
    def test_agent_memory_initialization(self, agent_memory):
        """Test AgentMemory initializes properly."""
        assert agent_memory.user_id == "test_user"
        assert agent_memory.hierarchical_memory is not None
        assert agent_memory.context_retriever is not None
        assert agent_memory.memory_indexer is not None
        assert isinstance(agent_memory.recent_reasoning_chains, list)
        assert isinstance(agent_memory.recent_tool_executions, list)
    
    def test_store_reasoning_chain(self, agent_memory):
        """Test storing reasoning chain."""
        reasoning_data = {
            "user_input": "Help me brainstorm ideas",
            "steps": [
                {
                    "thought": "User needs brainstorming help",
                    "tool_considered": "brainstorm",
                    "confidence": 0.8
                }
            ],
            "final_action": "brainstorm",
            "result": {"stories": ["story1", "story2"]},
            "success": True,
            "execution_time": 2.0
        }
        
        chain_id = agent_memory.store_reasoning_chain(reasoning_data)
        
        assert chain_id  # Should return an ID
        assert len(agent_memory.recent_reasoning_chains) == 1
        
        stored_chain = agent_memory.recent_reasoning_chains[0]
        assert stored_chain.user_input == "Help me brainstorm ideas"
        assert stored_chain.final_action == "brainstorm"
        assert stored_chain.success is True
        
        # Should have called indexer
        agent_memory.memory_indexer.index_reasoning_chain.assert_called_once()
    
    def test_track_tool_execution(self, agent_memory):
        """Test tracking tool execution."""
        execution_id = agent_memory.track_tool_execution(
            tool_name="brainstorm",
            result={"stories": ["story1"]},
            reasoning="User requested brainstorming help",
            execution_time=1.5,
            success=True,
            confidence_score=0.9
        )
        
        assert execution_id  # Should return an ID
        assert len(agent_memory.recent_tool_executions) == 1
        
        tracked_execution = agent_memory.recent_tool_executions[0]
        assert tracked_execution.tool_name == "brainstorm"
        assert tracked_execution.success is True
        assert tracked_execution.confidence_score == 0.9
        
        # Should have called indexer
        agent_memory.memory_indexer.index_tool_execution.assert_called_once()
    
    def test_get_relevant_context(self, agent_memory):
        """Test getting relevant context."""
        # Mock context retriever response
        mock_context = RetrievedContext(
            query="test query",
            elements=[],
            total_tokens=100,
            retrieval_time=0.1
        )
        agent_memory.context_retriever.retrieve_context.return_value = mock_context
        
        context = agent_memory.get_relevant_context("I need help")
        
        assert isinstance(context, RetrievedContext)
        assert context.query == "test query"
        agent_memory.context_retriever.retrieve_context.assert_called_once()
    
    def test_detect_patterns(self, agent_memory):
        """Test pattern detection."""
        # Mock indexer responses
        mock_usage_patterns = [
            UsagePattern(
                pattern_type="frequency",
                tools=["brainstorm"],
                frequency=5,
                success_rate=0.8,
                avg_execution_time=1.5,
                confidence=0.7
            )
        ]
        mock_error_patterns = []
        
        agent_memory.memory_indexer.detect_usage_patterns.return_value = mock_usage_patterns
        agent_memory.memory_indexer.detect_error_patterns.return_value = mock_error_patterns
        
        patterns = agent_memory.detect_patterns()
        
        assert "usage_patterns" in patterns
        assert "error_patterns" in patterns
        assert len(patterns["usage_patterns"]) == 1
        assert patterns["usage_patterns"][0].pattern_type == "frequency"
    
    def test_get_context_comprehensive(self, agent_memory):
        """Test comprehensive context retrieval."""
        # Mock user profile
        mock_profile = Mock()
        mock_profile.name = "Test User"
        mock_profile.core_values = []
        mock_profile.defining_moments = []
        agent_memory.hierarchical_memory.user_profile = mock_profile
        
        # Mock conversation memory
        mock_messages = []
        agent_memory.conversation_memory.buffer.messages = mock_messages
        
        context = agent_memory.get_context()
        
        assert isinstance(context, dict)
        assert "user_profile" in context
        assert "essay_state" in context
        assert "conversation_history" in context
        assert "recent_tools" in context
        assert "usage_patterns" in context
    
    def test_update_context(self, agent_memory):
        """Test context updating."""
        agent_memory.update_context(
            user_input="Help me brainstorm",
            reasoning="User needs idea generation",
            action="brainstorm",
            result={"stories": ["story1"]}
        )
        
        # Should have stored reasoning chain
        assert len(agent_memory.recent_reasoning_chains) == 1
        
        # Should have updated conversation memory
        agent_memory.conversation_memory.chat_memory.add_user_message.assert_called_once()
        agent_memory.conversation_memory.chat_memory.add_ai_message.assert_called_once()
    
    def test_memory_optimization(self, agent_memory):
        """Test memory optimization."""
        # Mock pattern detection
        agent_memory.memory_indexer.detect_usage_patterns.return_value = []
        agent_memory.memory_indexer.detect_error_patterns.return_value = []
        
        result = agent_memory.optimize_memory()
        
        assert isinstance(result, dict)
        assert "patterns_detected" in result
        assert "cache_cleared" in result
        assert "recommendations" in result
        
        # Should have called indexer save
        agent_memory.memory_indexer.save_indexes.assert_called_once()
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components fail."""
        # Test initialization with failing components
        with patch('essay_agent.agent.memory.agent_memory.HierarchicalMemory', 
                  side_effect=Exception("Memory init failed")):
            memory = AgentMemory("test_user")
            
            # Should still initialize but with None components
            assert memory.user_id == "test_user"
            assert memory.hierarchical_memory is None
            
            # Should still work with fallback methods
            context = memory.get_relevant_context("test query")
            assert isinstance(context, RetrievedContext)


class TestIntegration:
    """Integration tests for the complete agent memory system."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from reasoning to pattern detection."""
        # This would be a complex integration test combining all components
        # For now, we'll test basic integration
        
        with patch('essay_agent.agent.memory.agent_memory.HierarchicalMemory'), \
             patch('essay_agent.agent.memory.agent_memory.JSONConversationMemory'), \
             patch('essay_agent.agent.memory.agent_memory.ContextWindowManager'), \
             patch('essay_agent.agent.memory.agent_memory.ContextRetriever'), \
             patch('essay_agent.agent.memory.agent_memory.MemoryIndexer'):
            
            memory = AgentMemory("integration_test_user")
            
            # Store reasoning chain
            reasoning_data = {
                "user_input": "Help me write an essay",
                "steps": [{"thought": "User needs essay help", "tool_considered": "brainstorm"}],
                "final_action": "brainstorm",
                "result": {"stories": []},
                "success": True
            }
            chain_id = memory.store_reasoning_chain(reasoning_data)
            assert chain_id
            
            # Track tool execution
            execution_id = memory.track_tool_execution(
                tool_name="brainstorm",
                result={"stories": ["story1"]},
                reasoning="Helping user brainstorm"
            )
            assert execution_id
            
            # Get context
            context = memory.get_context()
            assert isinstance(context, dict)
            
            # Should work without errors
            assert True
    
    def test_data_model_serialization(self):
        """Test that data models can be serialized/deserialized."""
        # Test ReasoningChain serialization
        chain = ReasoningChain(
            user_input="test input",
            reasoning_steps=[],
            final_action="test_action",
            result={"test": "result"},
            success=True
        )
        
        # Should be able to convert to dict (for JSON serialization)
        chain_dict = chain.dict()
        assert isinstance(chain_dict, dict)
        assert chain_dict["user_input"] == "test input"
        
        # Should be able to recreate from dict
        recreated_chain = ReasoningChain(**chain_dict)
        assert recreated_chain.user_input == chain.user_input
        assert recreated_chain.final_action == chain.final_action


if __name__ == "__main__":
    pytest.main([__file__]) 