"""
Unit tests for conversation memory and context tracking functionality.
Tests UserPreferences, EssayContext, and enhanced ConversationState features.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open

from essay_agent.conversation import (
    UserPreferences, EssayContext, ConversationState, ConversationManager,
    ConversationTurn, ToolExecutionResult, ExecutionStatus
)
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile
from essay_agent.planner import EssayPlan, Phase


@pytest.fixture
def mock_profile():
    """Create a mock user profile for testing"""
    return UserProfile(
        user_info=UserInfo(
            name="Test User",
            grade=12,
            intended_major="Computer Science",
            college_list=["MIT", "Stanford"],
            platforms=["Common App"]
        ),
        academic_profile=AcademicProfile(
            gpa=3.8,
            test_scores={"SAT": 1450, "ACT": None},
            courses=["AP Computer Science", "AP English Literature"],
            activities=[]
        ),
        core_values=[]
    )


@pytest.fixture
def temp_memory_dir():
    """Create a temporary directory for memory storage"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_path = Path("memory_store")
        # Mock the memory_store path to use temp directory
        with patch('essay_agent.conversation.Path') as mock_path:
            mock_path.return_value = Path(temp_dir)
            yield temp_dir


class TestUserPreferences:
    """Test UserPreferences data structure and serialization"""
    
    def test_user_preferences_initialization(self):
        """Test UserPreferences can be initialized with defaults"""
        prefs = UserPreferences()
        
        assert prefs.preferred_tone is None
        assert prefs.writing_style is None
        assert prefs.favorite_topics == []
        assert prefs.revision_patterns == {}
        assert prefs.tool_usage_patterns == {}
        assert isinstance(prefs.last_updated, datetime)
    
    def test_user_preferences_with_values(self):
        """Test UserPreferences with specific values"""
        prefs = UserPreferences(
            preferred_tone="conversational",
            writing_style="narrative",
            favorite_topics=["leadership", "community"],
            revision_patterns={"improvement_focused": 3},
            tool_usage_patterns={"brainstorm": 5, "outline": 2}
        )
        
        assert prefs.preferred_tone == "conversational"
        assert prefs.writing_style == "narrative"
        assert "leadership" in prefs.favorite_topics
        assert prefs.revision_patterns["improvement_focused"] == 3
        assert prefs.tool_usage_patterns["brainstorm"] == 5
    
    def test_user_preferences_serialization(self):
        """Test UserPreferences to_dict and from_dict methods"""
        prefs = UserPreferences(
            preferred_tone="formal",
            writing_style="analytical",
            favorite_topics=["academics", "technology"],
            revision_patterns={"grammar_focused": 2},
            tool_usage_patterns={"revise": 3}
        )
        
        # Test to_dict
        data = prefs.to_dict()
        assert data["preferred_tone"] == "formal"
        assert data["writing_style"] == "analytical"
        assert data["favorite_topics"] == ["academics", "technology"]
        assert data["revision_patterns"] == {"grammar_focused": 2}
        assert data["tool_usage_patterns"] == {"revise": 3}
        assert "last_updated" in data
        
        # Test from_dict
        restored_prefs = UserPreferences.from_dict(data)
        assert restored_prefs.preferred_tone == "formal"
        assert restored_prefs.writing_style == "analytical"
        assert restored_prefs.favorite_topics == ["academics", "technology"]
        assert restored_prefs.revision_patterns == {"grammar_focused": 2}
        assert restored_prefs.tool_usage_patterns == {"revise": 3}


class TestEssayContext:
    """Test EssayContext data structure and serialization"""
    
    def test_essay_context_initialization(self):
        """Test EssayContext can be initialized with defaults"""
        ctx = EssayContext()
        
        assert ctx.essay_type is None
        assert ctx.college_target is None
        assert ctx.current_section is None
        assert ctx.word_count_target is None
        assert ctx.deadline is None
        assert ctx.progress_stage == "planning"
        assert isinstance(ctx.last_updated, datetime)
    
    def test_essay_context_with_values(self):
        """Test EssayContext with specific values"""
        deadline = datetime(2024, 1, 15)
        ctx = EssayContext(
            essay_type="personal statement",
            college_target="Stanford",
            current_section="introduction",
            word_count_target=650,
            deadline=deadline,
            progress_stage="drafting"
        )
        
        assert ctx.essay_type == "personal statement"
        assert ctx.college_target == "Stanford"
        assert ctx.current_section == "introduction"
        assert ctx.word_count_target == 650
        assert ctx.deadline == deadline
        assert ctx.progress_stage == "drafting"
    
    def test_essay_context_serialization(self):
        """Test EssayContext to_dict and from_dict methods"""
        deadline = datetime(2024, 2, 1)
        ctx = EssayContext(
            essay_type="supplemental",
            college_target="MIT",
            current_section="body",
            word_count_target=500,
            deadline=deadline,
            progress_stage="revising"
        )
        
        # Test to_dict
        data = ctx.to_dict()
        assert data["essay_type"] == "supplemental"
        assert data["college_target"] == "MIT"
        assert data["current_section"] == "body"
        assert data["word_count_target"] == 500
        assert data["deadline"] == deadline.isoformat()
        assert data["progress_stage"] == "revising"
        assert "last_updated" in data
        
        # Test from_dict
        restored_ctx = EssayContext.from_dict(data)
        assert restored_ctx.essay_type == "supplemental"
        assert restored_ctx.college_target == "MIT"
        assert restored_ctx.current_section == "body"
        assert restored_ctx.word_count_target == 500
        assert restored_ctx.deadline == deadline
        assert restored_ctx.progress_stage == "revising"


class TestConversationState:
    """Test enhanced ConversationState with persistence"""
    
    def test_conversation_state_initialization(self, mock_profile):
        """Test ConversationState initialization with new fields"""
        state = ConversationState(user_id="test_user", profile=mock_profile)
        
        assert state.user_id == "test_user"
        assert state.profile == mock_profile
        assert state.history == []
        assert state.current_essay_context is None
        assert isinstance(state.user_preferences, UserPreferences)
        assert state.essay_context_history == []
        assert state.active is True
        assert state.last_saved is None
    
    def test_conversation_state_add_turn(self, mock_profile):
        """Test adding conversation turns"""
        state = ConversationState(user_id="test_user", profile=mock_profile)
        
        # Add a turn
        state.add_turn("Hello", "Hi there!", None, [], 0.5)
        
        assert len(state.history) == 1
        turn = state.history[0]
        assert turn.user_input == "Hello"
        assert turn.agent_response == "Hi there!"
        assert turn.execution_time == 0.5
    
    def test_conversation_state_update_preferences(self, mock_profile):
        """Test updating user preferences"""
        state = ConversationState(user_id="test_user", profile=mock_profile)
        
        # Update preferences
        preferences_update = {
            "preferred_tone": "conversational",
            "writing_style": "narrative",
            "favorite_topics": ["leadership", "community"],
            "revision_patterns": {"improvement_focused": 1},
            "tool_usage_patterns": {"brainstorm": 2}
        }
        
        state.update_preferences(preferences_update)
        
        assert state.user_preferences.preferred_tone == "conversational"
        assert state.user_preferences.writing_style == "narrative"
        assert "leadership" in state.user_preferences.favorite_topics
        assert state.user_preferences.revision_patterns["improvement_focused"] == 1
        assert state.user_preferences.tool_usage_patterns["brainstorm"] == 2
    
    def test_conversation_state_update_essay_context(self, mock_profile):
        """Test updating essay context"""
        state = ConversationState(user_id="test_user", profile=mock_profile)
        
        # Update essay context
        context_update = {
            "essay_type": "personal statement",
            "college_target": "Stanford",
            "current_section": "introduction",
            "word_count_target": 650,
            "progress_stage": "drafting"
        }
        
        state.update_essay_context(context_update)
        
        assert state.current_essay_context.essay_type == "personal statement"
        assert state.current_essay_context.college_target == "Stanford"
        assert state.current_essay_context.current_section == "introduction"
        assert state.current_essay_context.word_count_target == 650
        assert state.current_essay_context.progress_stage == "drafting"
    
    def test_conversation_state_get_state_path(self, mock_profile):
        """Test getting state file path"""
        state = ConversationState(user_id="test_user", profile=mock_profile)
        
        path = state.get_state_path()
        assert str(path).endswith("test_user.conv_state.json")
    
    @patch('essay_agent.conversation.FileLock')
    def test_conversation_state_save_state(self, mock_filelock, mock_profile):
        """Test saving conversation state"""
        # Setup mocks
        mock_filelock.return_value.__enter__ = Mock()
        mock_filelock.return_value.__exit__ = Mock(return_value=False)
        
        state = ConversationState(user_id="test_user", profile=mock_profile)
        state.add_turn("Hello", "Hi!", None, [], 0.5)
        
        # Mock the open function and json.dump
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump, \
             patch.object(state, 'get_state_path') as mock_get_path:
            
            # Mock the path to avoid path construction issues
            mock_path = Mock()
            mock_path.parent.mkdir = Mock()
            mock_path.with_suffix.return_value = Mock()
            mock_get_path.return_value = mock_path
            
            state.save_state()
            
            # Verify state was saved
            assert state.last_saved is not None
            mock_json_dump.assert_called_once()
    
    @patch('essay_agent.conversation.FileLock')
    def test_conversation_state_load_state(self, mock_filelock, mock_profile):
        """Test loading conversation state"""
        # Setup mocks
        mock_filelock.return_value.__enter__ = Mock()
        mock_filelock.return_value.__exit__ = Mock(return_value=False)
        
        # Mock saved state data
        saved_data = {
            "user_id": "test_user",
            "profile": mock_profile.model_dump() if hasattr(mock_profile, 'model_dump') else mock_profile.dict(),
            "history": [{
                "user_input": "Hello",
                "agent_response": "Hi!",
                "timestamp": datetime.now().isoformat(),
                "plan": None,
                "tool_results": [],
                "execution_time": 0.5
            }],
            "current_essay_context": None,
            "user_preferences": {},
            "essay_context_history": [],
            "active": True,
            "last_saved": datetime.now().isoformat()
        }
        
        state = ConversationState(user_id="test_user", profile=mock_profile)
        
        # Mock the open function and json.load
        with patch('builtins.open', mock_open()), \
             patch('json.load', return_value=saved_data), \
             patch.object(state, 'get_state_path') as mock_get_path:
            
            # Mock the path to avoid path construction issues
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.with_suffix.return_value = Mock()
            mock_get_path.return_value = mock_path
            
            state.load_state()
            
            # Verify state was loaded
            assert len(state.history) == 1
            assert state.history[0].user_input == "Hello"
            assert state.history[0].agent_response == "Hi!"


class TestConversationManager:
    """Test enhanced ConversationManager with memory features"""
    
    @patch('essay_agent.conversation.SimpleMemory')
    @patch('essay_agent.conversation.ConversationalPlanner')
    def test_conversation_manager_initialization(self, mock_planner, mock_memory, mock_profile):
        """Test ConversationManager initialization with state loading"""
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        mock_memory_instance.load.return_value = mock_profile
        
        with patch.object(ConversationState, 'load_state') as mock_load:
            manager = ConversationManager("test_user", mock_profile)
            
            assert manager.user_id == "test_user"
            assert manager.state.user_id == "test_user"
            assert manager.state.profile == mock_profile
            mock_load.assert_called_once()
    
    @patch('essay_agent.conversation.SimpleMemory')
    @patch('essay_agent.conversation.ConversationalPlanner')
    def test_conversation_manager_learn_from_interaction(self, mock_planner, mock_memory, mock_profile):
        """Test learning from user interactions"""
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        mock_memory_instance.load.return_value = mock_profile
        
        with patch.object(ConversationState, 'load_state'), \
             patch.object(ConversationState, 'update_preferences') as mock_update_prefs:
            
            manager = ConversationManager("test_user", mock_profile)
            
            # Create mock tool results
            tool_results = [
                ToolExecutionResult(
                    tool_name="brainstorm",
                    status=ExecutionStatus.SUCCESS,
                    execution_time=1.0
                )
            ]
            
            # Test learning from interaction
            manager._learn_from_interaction("I want a conversational tone", tool_results)
            
            # Verify preferences were updated
            mock_update_prefs.assert_called_once()
            call_args = mock_update_prefs.call_args[0][0]
            assert call_args["preferred_tone"] == "conversational"
            assert call_args["tool_usage_patterns"]["brainstorm"] == 1
    
    @patch('essay_agent.conversation.SimpleMemory')
    @patch('essay_agent.conversation.ConversationalPlanner')
    def test_conversation_manager_update_essay_context(self, mock_planner, mock_memory, mock_profile):
        """Test updating essay context from user input"""
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        mock_memory_instance.load.return_value = mock_profile
        
        mock_plan = Mock()
        mock_plan.phase = Phase.DRAFTING
        
        with patch.object(ConversationState, 'load_state'), \
             patch.object(ConversationState, 'update_essay_context') as mock_update_context:
            
            manager = ConversationManager("test_user", mock_profile)
            
            # Test context update
            manager._update_essay_context("Help me write a personal statement for Stanford", mock_plan)
            
            # Verify context was updated
            mock_update_context.assert_called_once()
            call_args = mock_update_context.call_args[0][0]
            assert call_args["essay_type"] == "personal statement"
            assert call_args["college_target"] == "Stanford"
            assert call_args["progress_stage"] == "drafting"
    
    @patch('essay_agent.conversation.SimpleMemory')
    @patch('essay_agent.conversation.ConversationalPlanner')
    def test_conversation_manager_auto_save(self, mock_planner, mock_memory, mock_profile):
        """Test auto-save functionality"""
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        mock_memory_instance.load.return_value = mock_profile
        
        with patch.object(ConversationState, 'load_state'), \
             patch.object(ConversationState, 'save_state') as mock_save:
            
            manager = ConversationManager("test_user", mock_profile)
            
            # Add 5 turns to trigger auto-save
            for i in range(5):
                manager.state.add_turn(f"Message {i}", f"Response {i}", None, [], 0.5)
            
            # Test auto-save trigger
            assert manager._should_auto_save() is True
            
            # Verify save would be called
            mock_save.assert_not_called()  # Not called yet
            
            # Test with recent context update
            manager.state.update_essay_context({"essay_type": "personal statement"})
            assert manager._should_auto_save() is True
    
    @patch('essay_agent.conversation.SimpleMemory')
    @patch('essay_agent.conversation.ConversationalPlanner')
    def test_conversation_manager_preferences_in_response(self, mock_planner, mock_memory, mock_profile):
        """Test that preferences influence response generation"""
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        mock_memory_instance.load.return_value = mock_profile
        
        with patch.object(ConversationState, 'load_state'):
            manager = ConversationManager("test_user", mock_profile)
            
            # Set up preferences
            manager.state.user_preferences.preferred_tone = "conversational"
            manager.state.user_preferences.writing_style = "narrative"
            manager.state.user_preferences.favorite_topics = ["leadership", "community"]
            
            # Test preferences context building
            prefs_context = manager.response_generator._build_preferences_context(
                manager.state.user_preferences
            )
            
            assert "conversational" in prefs_context
            assert "narrative" in prefs_context
            assert "leadership" in prefs_context
            assert "community" in prefs_context
    
    @patch('essay_agent.conversation.SimpleMemory')
    @patch('essay_agent.conversation.ConversationalPlanner')
    def test_conversation_manager_essay_context_in_response(self, mock_planner, mock_memory, mock_profile):
        """Test that essay context influences response generation"""
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        mock_memory_instance.load.return_value = mock_profile
        
        with patch.object(ConversationState, 'load_state'):
            manager = ConversationManager("test_user", mock_profile)
            
            # Set up essay context
            manager.state.current_essay_context = EssayContext(
                essay_type="personal statement",
                college_target="Stanford",
                current_section="introduction",
                word_count_target=650,
                progress_stage="drafting"
            )
            
            # Test essay context building
            essay_context = manager.response_generator._build_essay_context(
                manager.state.current_essay_context
            )
            
            assert "personal statement" in essay_context
            assert "Stanford" in essay_context
            assert "introduction" in essay_context
            assert "650" in essay_context
            assert "drafting" in essay_context 