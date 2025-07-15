"""
Integration tests for conversation persistence and memory features.
Tests that conversation state persists across sessions and CLI restarts.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime

from essay_agent.conversation import ConversationManager, EssayContext, UserPreferences
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile, CoreValue, Activity
from essay_agent.cli import _cmd_chat
from argparse import Namespace


@pytest.fixture
def test_profile():
    """Create a test user profile"""
    return UserProfile(
        user_info=UserInfo(
            name="Persistence Test User",
            grade=12,
            intended_major="Computer Science",
            college_list=["Harvard", "MIT"],
            platforms=["Common App"]
        ),
        academic_profile=AcademicProfile(
            gpa=3.9,
            test_scores={"SAT": 1500, "ACT": None},
            courses=["AP Computer Science", "AP Calculus"],
            activities=[
                Activity(
                    name="Robotics Club",
                    role="Team Lead",
                    duration="3 years",
                    description="Built and programmed robots for competition",
                    impact="Developed engineering and leadership skills"
                )
            ]
        ),
        core_values=[
            CoreValue(
                value="Innovation",
                description="Creating new solutions to complex problems",
                evidence=["Built winning robot design", "Created coding tutorial videos"],
                used_in_essays=[]
            )
        ]
    )


@pytest.fixture
def temp_memory_dir():
    """Create a temporary directory for memory storage"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up environment to use temp directory
        os.environ['ESSAY_AGENT_MEMORY_DIR'] = temp_dir
        yield temp_dir


class TestConversationPersistence:
    """Test that conversation state persists across sessions"""
    
    def test_conversation_state_persists_across_sessions(self, test_profile, temp_memory_dir):
        """Test that conversation state is saved and loaded correctly"""
        user_id = "persistence_test_user"
        
        # Mock memory_store path to use temp directory
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            # First session - create conversation and add some interaction
            manager1 = ConversationManager(user_id, test_profile)
            
            # Simulate conversation turns
            response1 = manager1.handle_message("Help me write a personal statement for Stanford")
            response2 = manager1.handle_message("I want it to be conversational and personal")
            response3 = manager1.handle_message("Let's focus on my leadership experience")
            
            # Check that conversation history exists
            assert len(manager1.state.history) == 3
            assert manager1.state.current_essay_context is not None
            assert manager1.state.user_preferences.preferred_tone == "conversational"
            
            # Save state
            manager1.state.save_state()
            
            # Second session - create new manager and check state is loaded
            manager2 = ConversationManager(user_id, test_profile)
            
            # Check that state was loaded
            assert len(manager2.state.history) == 3
            assert manager2.state.history[0].user_input == "Help me write a personal statement for Stanford"
            assert manager2.state.history[1].user_input == "I want it to be conversational and personal"
            assert manager2.state.history[2].user_input == "Let's focus on my leadership experience"
            
            # Check that preferences were loaded
            assert manager2.state.user_preferences.preferred_tone == "conversational"
            
            # Check that essay context was loaded
            if manager2.state.current_essay_context:
                assert manager2.state.current_essay_context.essay_type == "personal statement"
                assert manager2.state.current_essay_context.college_target == "Stanford"
    
    def test_conversation_context_carries_forward(self, test_profile, temp_memory_dir):
        """Test that essay context carries forward between tool calls"""
        user_id = "context_test_user"
        
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            manager = ConversationManager(user_id, test_profile)
            
            # First message establishes context
            response1 = manager.handle_message("I'm working on a supplemental essay for MIT about my robotics experience")
            
            # Check that context was set
            assert manager.state.current_essay_context is not None
            assert manager.state.current_essay_context.essay_type == "supplemental"
            assert manager.state.current_essay_context.college_target == "MIT"
            
            # Second message should maintain context
            response2 = manager.handle_message("Let's work on the introduction")
            
            # Check that context was updated but maintained
            assert manager.state.current_essay_context.essay_type == "supplemental"
            assert manager.state.current_essay_context.college_target == "MIT"
            assert manager.state.current_essay_context.current_section == "introduction"
            
            # Third message should still maintain context
            response3 = manager.handle_message("Make it 500 words")
            
            # Check that word count was added to context
            assert manager.state.current_essay_context.word_count_target == 500
            assert manager.state.current_essay_context.essay_type == "supplemental"  # Still maintained
    
    def test_user_preferences_improve_over_time(self, test_profile, temp_memory_dir):
        """Test that user preferences are learned and improve recommendations"""
        user_id = "preferences_test_user"
        
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            manager = ConversationManager(user_id, test_profile)
            
            # Initial preferences should be empty
            assert manager.state.user_preferences.preferred_tone is None
            assert manager.state.user_preferences.writing_style is None
            assert manager.state.user_preferences.favorite_topics == []
            
            # Simulate interactions that reveal preferences
            manager.handle_message("I want my essay to be conversational and personal")
            manager.handle_message("I love writing about leadership and community service")
            manager.handle_message("Help me create a narrative-style essay")
            
            # Check that preferences were learned
            assert manager.state.user_preferences.preferred_tone == "conversational"
            assert manager.state.user_preferences.writing_style == "narrative"
            assert "leadership" in manager.state.user_preferences.favorite_topics
            assert "community" in manager.state.user_preferences.favorite_topics
            
            # Save and reload to test persistence
            manager.state.save_state()
            manager2 = ConversationManager(user_id, test_profile)
            
            # Check that preferences persist
            assert manager2.state.user_preferences.preferred_tone == "conversational"
            assert manager2.state.user_preferences.writing_style == "narrative"
            assert "leadership" in manager2.state.user_preferences.favorite_topics
    
    def test_conversation_auto_save_functionality(self, test_profile, temp_memory_dir):
        """Test that conversation state auto-saves at appropriate intervals"""
        user_id = "autosave_test_user"
        
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            manager = ConversationManager(user_id, test_profile)
            
            # Add turns one by one and check auto-save logic
            for i in range(1, 6):
                manager.handle_message(f"Message {i}")
                if i == 5:
                    # After 5 turns, should trigger auto-save
                    assert manager._should_auto_save() is True
                else:
                    # Before 5 turns, should not trigger auto-save
                    assert manager._should_auto_save() is False
    
    def test_conversation_resume_shows_context(self, test_profile, temp_memory_dir):
        """Test that resuming a conversation shows appropriate context"""
        user_id = "resume_test_user"
        
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            # First session
            manager1 = ConversationManager(user_id, test_profile)
            manager1.handle_message("Help me write a personal statement for Harvard")
            manager1.state.save_state()
            
            # Second session - test that start_conversation shows context
            manager2 = ConversationManager(user_id, test_profile)
            
            # Mock print to capture output
            with patch('builtins.print') as mock_print:
                manager2.start_conversation()
                
                # Check that welcome back message was printed
                print_calls = [call.args[0] for call in mock_print.call_args_list]
                welcome_messages = [msg for msg in print_calls if "Welcome back" in msg]
                assert len(welcome_messages) > 0
                
                # Check that context was shown
                context_messages = [msg for msg in print_calls if "Working on" in msg]
                if manager2.state.current_essay_context:
                    assert len(context_messages) > 0
    
    def test_conversation_state_corruption_handling(self, test_profile, temp_memory_dir):
        """Test graceful handling of corrupted state files"""
        user_id = "corruption_test_user"
        
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            # Create a corrupted state file
            state_file = Path(temp_memory_dir) / f"{user_id}.conv_state.json"
            state_file.parent.mkdir(exist_ok=True)
            state_file.write_text("invalid json content")
            
            # Should handle corruption gracefully
            manager = ConversationManager(user_id, test_profile)
            
            # Should initialize with fresh state
            assert len(manager.state.history) == 0
            assert manager.state.current_essay_context is None
            assert manager.state.user_preferences.preferred_tone is None
            
            # Should still work normally
            response = manager.handle_message("Hello")
            assert len(manager.state.history) == 1
    
    def test_conversation_memory_with_preferences_in_response(self, test_profile, temp_memory_dir):
        """Test that learned preferences influence response generation"""
        user_id = "response_test_user"
        
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            manager = ConversationManager(user_id, test_profile)
            
            # Set up preferences
            manager.state.user_preferences.preferred_tone = "conversational"
            manager.state.user_preferences.writing_style = "narrative"
            manager.state.user_preferences.favorite_topics = ["leadership", "technology"]
            
            # Set up essay context
            manager.state.current_essay_context = EssayContext(
                essay_type="personal statement",
                college_target="MIT",
                current_section="introduction",
                word_count_target=650,
                progress_stage="drafting"
            )
            
            # Mock LLM to capture the prompt
            with patch('essay_agent.conversation.get_chat_llm') as mock_llm:
                mock_llm_instance = Mock()
                mock_llm_instance.predict.return_value = "Test response"
                mock_llm.return_value = mock_llm_instance
                
                response = manager.handle_message("What should I write about?")
                
                # Check that LLM was called with preferences in prompt
                llm_call_args = mock_llm_instance.predict.call_args[0][0]
                assert "conversational" in llm_call_args
                assert "narrative" in llm_call_args
                assert "leadership" in llm_call_args
                assert "technology" in llm_call_args
                assert "MIT" in llm_call_args
                assert "personal statement" in llm_call_args


class TestCLIIntegrationWithPersistence:
    """Test CLI integration with conversation persistence"""
    
    def test_cli_chat_loads_previous_conversation(self, test_profile, temp_memory_dir):
        """Test that CLI chat command loads previous conversation"""
        user_id = "cli_test_user"
        
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            # Create a conversation with some history
            manager = ConversationManager(user_id, test_profile)
            manager.handle_message("Help me with my college essay")
            manager.handle_message("I want to write about leadership")
            manager.state.save_state()
            
            # Test CLI loading
            with patch('essay_agent.cli.ConversationManager') as mock_manager_class:
                mock_manager_instance = Mock()
                mock_manager_class.return_value = mock_manager_instance
                
                # Mock successful CLI execution
                with patch('essay_agent.cli._load_profile', return_value=test_profile):
                    args = Namespace(user=user_id, profile=None, debug=False)
                    
                    try:
                        _cmd_chat(args)
                    except SystemExit:
                        pass
                    except Exception:
                        pass  # Expected for CLI integration
                
                # Verify ConversationManager was created with correct user_id
                mock_manager_class.assert_called_once_with(user_id=user_id, profile=test_profile)
    
    def test_cli_chat_saves_state_on_exit(self, test_profile, temp_memory_dir):
        """Test that CLI chat saves state when exiting"""
        user_id = "cli_exit_test_user"
        
        with patch('essay_agent.conversation.Path') as mock_path:
            def path_side_effect(path_str):
                if path_str == "memory_store":
                    return Path(temp_memory_dir)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            
            manager = ConversationManager(user_id, test_profile)
            
            # Mock the save_state method to verify it's called
            with patch.object(manager.state, 'save_state') as mock_save:
                # Simulate quit command
                response = manager.handle_message("quit")
                
                # Verify save_state was called
                mock_save.assert_called_once()
                
                # Verify conversation is inactive
                assert manager.state.active is False
                
                # Verify quit message
                assert "Goodbye" in response 