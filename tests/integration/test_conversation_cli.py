"""
Integration tests for conversational CLI system.
Tests the complete workflow from user input to tool execution and response generation.
"""

import pytest
import tempfile
import os
import unittest.mock
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
from io import StringIO
import sys

from essay_agent.conversation import ConversationManager, ExecutionStatus, ToolExecutionResult
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile, CoreValue, Activity
from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.models import Phase


@pytest.fixture
def temp_memory_dir():
    """Create a temporary directory for memory storage"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def test_profile():
    """Create a test user profile"""
    return UserProfile(
        user_info=UserInfo(
            name="Integration Test User",
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
def conversation_manager(temp_memory_dir, test_profile):
    """Create a ConversationManager with test profile"""
    with patch('essay_agent.conversation.SimpleMemory') as mock_memory_class:
        mock_memory = Mock()
        mock_memory.load.return_value = test_profile
        mock_memory_class.return_value = mock_memory
        
        manager = ConversationManager("test_user", test_profile)
        yield manager


@contextmanager
def capture_output():
    """Context manager to capture stdout and stderr"""
    old_stdout, old_stderr = sys.stdout, sys.stderr
    try:
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        sys.stdout, sys.stderr = stdout_capture, stderr_capture
        yield stdout_capture, stderr_capture
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


class TestConversationManagerIntegration:
    """Integration tests for ConversationManager"""
    
    def test_handle_help_message(self, conversation_manager):
        """Test handling help message"""
        response = conversation_manager.handle_message("help")
        
        assert "Essay Agent Chat Help" in response
        assert "brainstorm" in response
        assert "outline" in response
        assert "draft" in response
        assert len(conversation_manager.state.history) == 1
    
    def test_handle_quit_message(self, conversation_manager):
        """Test handling quit message"""
        response = conversation_manager.handle_message("quit")
        
        assert "Goodbye!" in response
        assert not conversation_manager.state.active
        assert len(conversation_manager.state.history) == 1
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_handle_brainstorm_request(self, mock_registry, conversation_manager):
        """Test handling brainstorm request with tool execution"""
        # Mock tool result
        mock_story = Mock()
        mock_story.title = "Leadership Challenge"
        mock_story.description = "A story about overcoming leadership challenges"
        
        mock_result = Mock()
        mock_result.stories = [mock_story]
        
        mock_registry.call.return_value = mock_result
        mock_registry.__contains__ = Mock(return_value=True)
        
        response = conversation_manager.handle_message("Help me brainstorm ideas for my leadership essay")
        
        assert "Story Ideas Generated" in response
        assert "Leadership Challenge" in response
        assert len(conversation_manager.state.history) == 1
        
        # Check that tool was called
        mock_registry.call.assert_called_once()
        call_args = mock_registry.call.call_args
        assert call_args[0][0] == "brainstorm"  # Tool name
        assert "profile" in call_args[1]  # Profile passed as kwarg
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_handle_outline_request(self, mock_registry, conversation_manager):
        """Test handling outline request with tool execution"""
        # Mock tool result
        mock_result = Mock()
        mock_result.outline = "I. Introduction\nII. Body Paragraph 1\nIII. Body Paragraph 2\nIV. Conclusion"
        
        mock_registry.call.return_value = mock_result
        mock_registry.__contains__ = Mock(return_value=True)
        
        response = conversation_manager.handle_message("Help me create an outline for my essay")
        
        assert "Essay Outline Created" in response
        assert "Introduction" in response
        assert "Conclusion" in response
        assert len(conversation_manager.state.history) == 1
        
        # Check that tool was called
        mock_registry.call.assert_called_once()
        call_args = mock_registry.call.call_args
        assert call_args[0][0] == "outline"  # Tool name
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_handle_draft_request(self, mock_registry, conversation_manager):
        """Test handling draft request with tool execution"""
        # Mock tool result
        mock_result = Mock()
        mock_result.draft = "This is a test essay draft about leadership and personal growth. " * 20
        
        mock_registry.call.return_value = mock_result
        mock_registry.__contains__ = Mock(return_value=True)
        
        response = conversation_manager.handle_message("Help me write a draft of my essay")
        
        assert "Essay Draft Completed" in response
        assert "words" in response
        assert "revise any part" in response
        assert len(conversation_manager.state.history) == 1
        
        # Check that tool was called
        mock_registry.call.assert_called_once()
        call_args = mock_registry.call.call_args
        assert call_args[0][0] == "draft"  # Tool name
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_handle_revision_request(self, mock_registry, conversation_manager):
        """Test handling revision request with tool execution"""
        # Mock tool result
        mock_result = Mock()
        mock_result.revised_draft = "This is a revised and improved essay draft about leadership."
        
        mock_registry.call.return_value = mock_result
        mock_registry.__contains__ = Mock(return_value=True)
        
        response = conversation_manager.handle_message("Revise my essay to make it stronger")
        
        assert "Essay Revised" in response
        assert "improved" in response
        assert len(conversation_manager.state.history) == 1
        
        # Check that tool was called
        mock_registry.call.assert_called_once()
        call_args = mock_registry.call.call_args
        assert call_args[0][0] == "revise"  # Tool name
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_handle_polish_request(self, mock_registry, conversation_manager):
        """Test handling polish request with tool execution"""
        # Mock tool result
        mock_result = Mock()
        mock_result.polished_draft = "This is a polished, final essay draft ready for submission."
        
        mock_registry.call.return_value = mock_result
        mock_registry.__contains__ = Mock(return_value=True)
        
        response = conversation_manager.handle_message("Polish my essay for final submission")
        
        assert "Essay Polished" in response
        assert "ready for submission" in response
        assert len(conversation_manager.state.history) == 1
        
        # Check that tool was called
        mock_registry.call.assert_called_once()
        call_args = mock_registry.call.call_args
        assert call_args[0][0] == "polish"  # Tool name
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_handle_multiple_tool_request(self, mock_registry, conversation_manager):
        """Test handling request that triggers multiple tools"""
        # Mock tool results
        mock_brainstorm_result = Mock()
        mock_brainstorm_result.stories = [Mock(title="Test Story", description="Test Description")]
        
        mock_registry.call.return_value = mock_brainstorm_result
        mock_registry.__contains__ = Mock(return_value=True)
        
        response = conversation_manager.handle_message("Help me brainstorm and check grammar")
        
        assert "Story Ideas Generated" in response
        assert len(conversation_manager.state.history) == 1
        
        # Should execute multiple tools
        assert mock_registry.call.call_count >= 1
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_handle_tool_failure(self, mock_registry, conversation_manager):
        """Test handling tool execution failure"""
        mock_registry.__contains__ = Mock(return_value=True)
        mock_registry.call.side_effect = Exception("Tool execution failed")
        
        response = conversation_manager.handle_message("Help me brainstorm")
        
        assert "encountered some issues" in response or "failed" in response
        assert len(conversation_manager.state.history) == 1
        
        # Check that tool failure was recorded
        turn = conversation_manager.state.history[0]
        assert len(turn.tool_results) > 0
        assert turn.tool_results[0].status == ExecutionStatus.FAILED
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_handle_tool_not_found(self, mock_registry, conversation_manager):
        """Test handling when tool is not found"""
        mock_registry.__contains__ = Mock(return_value=False)
        
        response = conversation_manager.handle_message("Help me brainstorm")
        
        assert "not found" in response or "issues" in response
        assert len(conversation_manager.state.history) == 1
        
        # Check that tool failure was recorded
        turn = conversation_manager.state.history[0]
        assert len(turn.tool_results) > 0
        assert turn.tool_results[0].status == ExecutionStatus.FAILED
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_handle_general_question(self, mock_get_llm, conversation_manager):
        """Test handling general questions without tool execution"""
        mock_llm = Mock()
        mock_llm.predict.return_value = "College essays should be personal and authentic."
        mock_get_llm.return_value = mock_llm
        
        response = conversation_manager.handle_message("What makes a good college essay?")
        
        assert "College essays should be personal and authentic." in response
        assert len(conversation_manager.state.history) == 1
        
        # Check that LLM was called
        mock_llm.predict.assert_called_once()
    
    def test_conversation_context_preservation(self, conversation_manager):
        """Test that conversation context is preserved across turns"""
        # First turn
        response1 = conversation_manager.handle_message("help")
        assert "Essay Agent Chat Help" in response1
        
        # Second turn
        response2 = conversation_manager.handle_message("What did you just tell me?")
        
        # Should have both turns in history
        assert len(conversation_manager.state.history) == 2
        
        # Context should be available for second turn
        context = conversation_manager.state.get_recent_context()
        assert "help" in context
        assert "Essay Agent Chat Help" in context
    
    def test_execution_time_tracking(self, conversation_manager):
        """Test that execution time is tracked for each turn"""
        response = conversation_manager.handle_message("help")
        
        assert len(conversation_manager.state.history) == 1
        turn = conversation_manager.state.history[0]
        assert turn.execution_time > 0
    
    def test_conversation_state_management(self, conversation_manager):
        """Test that conversation state is properly managed"""
        # Initially active
        assert conversation_manager.state.active
        
        # Add some turns
        conversation_manager.handle_message("help")
        conversation_manager.handle_message("How are you?")
        
        # Still active
        assert conversation_manager.state.active
        
        # Quit
        conversation_manager.handle_message("quit")
        
        # Should be inactive
        assert not conversation_manager.state.active


class TestCLIIntegration:
    """Integration tests for CLI with conversation system"""
    
    @patch('essay_agent.cli.ConversationManager')
    def test_cli_chat_command_integration(self, mock_conversation_manager_class):
        """Test CLI chat command integration with ConversationManager"""
        # Mock ConversationManager
        mock_manager = Mock()
        mock_manager.start_conversation.return_value = None
        mock_conversation_manager_class.return_value = mock_manager
        
        # Mock user profile loading
        with patch('essay_agent.cli.SimpleMemory') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory_instance.load.return_value = UserProfile(
                user_info=UserInfo(
                    name="Test User",
                    grade=12,
                    intended_major="Computer Science",
                    college_list=["Harvard", "MIT"],
                    platforms=["Common App"]
                ),
                academic_profile=AcademicProfile(
                    gpa=3.8,
                    test_scores={"SAT": 1450, "ACT": None},
                    courses=["AP Computer Science", "AP English Literature"],
                    activities=[
                        Activity(
                            name="Debate Team",
                            role="Captain",
                            duration="2 years",
                            description="Led school debate team to regional championships",
                            impact="Improved public speaking skills and logical reasoning"
                        )
                    ]
                ),
                core_values=[
                    CoreValue(
                        value="Perseverance",
                        description="Never giving up in the face of challenges",
                        evidence=["Overcame coding challenges", "Maintained GPA during difficult times"],
                        used_in_essays=[]
                    )
                ]
            )
            mock_memory.return_value = mock_memory_instance
            
            # Test the chat command by importing and calling the function
            from essay_agent.cli import _cmd_chat
            from argparse import Namespace
            
            # Create mock args
            args = Namespace(user="test_user", profile=None)
            
            # Should not raise exception
            try:
                _cmd_chat(args)
            except SystemExit:
                # CLI might exit normally
                pass
            except Exception as e:
                # Check that it's expected ConversationManager integration
                assert "ConversationManager" in str(e) or "conversation" in str(e)
        
        # Verify ConversationManager was created
        mock_conversation_manager_class.assert_called_once()
        call_args = mock_conversation_manager_class.call_args
        assert call_args.kwargs['user_id'] == "test_user"  # user_id as keyword
        assert call_args.kwargs['profile'] is not None  # profile as keyword
    
    @patch('essay_agent.cli.ConversationManager')
    def test_cli_chat_with_profile_integration(self, mock_conversation_manager_class):
        """Test CLI chat command with existing profile integration"""
        # Mock ConversationManager
        mock_manager = Mock()
        mock_conversation_manager_class.return_value = mock_manager
        
        # Create test profile
        test_profile = UserProfile(
            user_info=UserInfo(
                name="Test User",
                grade=12,
                intended_major="Computer Science",
                college_list=["Harvard", "MIT"],
                platforms=["Common App"]
            ),
            academic_profile=AcademicProfile(
                gpa=3.7,
                test_scores={"SAT": 1400, "ACT": None},
                courses=["AP Biology", "AP Chemistry"],
                activities=[
                    Activity(
                        name="Science Club",
                        role="Member",
                        duration="2 years",
                        description="Participated in science fair competitions",
                        impact="Deepened understanding of scientific method"
                    )
                ]
            ),
            core_values=[
                CoreValue(
                    value="Curiosity",
                    description="Always asking questions and seeking knowledge",
                    evidence=["Independent research projects", "Tutoring younger students"],
                    used_in_essays=[]
                )
            ]
        )
        
        # Mock memory loading
        with patch('essay_agent.cli.SimpleMemory') as mock_memory:
            mock_memory_instance = Mock()
            mock_memory_instance.load.return_value = test_profile
            mock_memory.return_value = mock_memory_instance
            
            # Test the chat command
            from essay_agent.cli import _cmd_chat
            from argparse import Namespace
            
            # Create mock args
            args = Namespace(user="test_user", profile=None)
            
            try:
                _cmd_chat(args)
            except SystemExit:
                pass
            except Exception as e:
                # Expected for CLI integration
                assert "ConversationManager" in str(e) or "conversation" in str(e)
        
        # Verify profile was loaded and passed to ConversationManager
        mock_conversation_manager_class.assert_called_once()
        call_args = mock_conversation_manager_class.call_args
        assert call_args.kwargs['user_id'] == "test_user"  # user_id as keyword
        assert call_args.kwargs['profile'] == test_profile  # profile as keyword


class TestRealToolIntegration:
    """Integration tests with real tools (if available)"""
    
    def test_echo_tool_integration(self, conversation_manager):
        """Test integration with real echo tool"""
        # Check if echo tool is available
        if "echo" in TOOL_REGISTRY:
            response = conversation_manager.handle_message("echo test message")
            
            # Should get some response
            assert len(response) > 0
            assert len(conversation_manager.state.history) == 1
            
            # Check if tool was executed
            turn = conversation_manager.state.history[0]
            if turn.tool_results:
                # If tool was executed, check result
                assert any(r.tool_name == "echo" for r in turn.tool_results)
    
    def test_available_tools_integration(self, conversation_manager):
        """Test integration with available tools in registry"""
        # Get available tools
        available_tools = list(TOOL_REGISTRY.keys())
        
        if available_tools:
            # Test with first available tool
            tool_name = available_tools[0]
            response = conversation_manager.handle_message(f"Use {tool_name} tool")
            
            # Should get some response
            assert len(response) > 0
            assert len(conversation_manager.state.history) == 1
    
    def test_tool_execution_error_handling(self, conversation_manager):
        """Test error handling with real tool execution"""
        # Try to execute a request that might fail
        response = conversation_manager.handle_message("Execute nonexistent tool")
        
        # Should handle gracefully
        assert len(response) > 0
        assert len(conversation_manager.state.history) == 1
        
        # Should not crash the conversation
        assert conversation_manager.state.active


class TestConversationWorkflowIntegration:
    """Integration tests for complete conversation workflows"""
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_complete_essay_workflow(self, mock_registry, conversation_manager):
        """Test complete essay writing workflow through conversation"""
        # Mock tool results for complete workflow
        mock_brainstorm_result = Mock()
        mock_brainstorm_result.stories = [Mock(title="Test Story", description="Test Description")]
        
        mock_outline_result = Mock()
        mock_outline_result.outline = "I. Introduction\nII. Body\nIII. Conclusion"
        
        mock_draft_result = Mock()
        mock_draft_result.draft = "This is a test essay draft. " * 30
        
        mock_polish_result = Mock()
        mock_polish_result.polished_draft = "This is a polished essay draft ready for submission."
        
        # Configure mock registry
        mock_registry.__contains__ = Mock(return_value=True)
        mock_registry.call.side_effect = [
            mock_brainstorm_result,
            mock_outline_result,
            mock_draft_result,
            mock_polish_result
        ]
        
        # Step 1: Brainstorm
        response1 = conversation_manager.handle_message("Help me brainstorm ideas")
        assert "Story Ideas Generated" in response1
        
        # Step 2: Outline
        response2 = conversation_manager.handle_message("Create an outline")
        assert "Essay Outline Created" in response2
        
        # Step 3: Draft
        response3 = conversation_manager.handle_message("Write a draft")
        assert "Essay Draft Completed" in response3
        
        # Step 4: Polish
        response4 = conversation_manager.handle_message("Polish my essay")
        assert "Essay Polished" in response4
        
        # Check conversation history
        assert len(conversation_manager.state.history) == 4
        
        # Verify all tools were called
        assert mock_registry.call.call_count >= 4
    
    @patch('essay_agent.conversation.TOOL_REGISTRY')
    def test_error_recovery_workflow(self, mock_registry, conversation_manager):
        """Test error recovery in conversation workflow"""
        # Mock first tool to fail, second to succeed
        mock_success_result = Mock()
        mock_success_result.stories = [Mock(title="Recovery Story", description="Success after failure")]
        
        mock_registry.__contains__ = Mock(return_value=True)
        mock_registry.call.side_effect = [
            Exception("First attempt failed"),
            mock_success_result
        ]
        
        # First attempt fails
        response1 = conversation_manager.handle_message("Help me brainstorm")
        assert "encountered" in response1 or "issues" in response1
        
        # Second attempt succeeds
        response2 = conversation_manager.handle_message("Try brainstorming again")
        assert "Story Ideas Generated" in response2
        
        # Check that both attempts are recorded
        assert len(conversation_manager.state.history) == 2
        
        # First attempt should have failed tool
        turn1 = conversation_manager.state.history[0]
        assert any(r.status == ExecutionStatus.FAILED for r in turn1.tool_results)
        
        # Second attempt should have successful tool
        turn2 = conversation_manager.state.history[1]
        assert any(r.status == ExecutionStatus.SUCCESS for r in turn2.tool_results)
    
    def test_conversation_memory_persistence(self, conversation_manager):
        """Test that conversation memory persists across interactions"""
        # Add several conversation turns
        conversation_manager.handle_message("Hello")
        conversation_manager.handle_message("I'm working on a leadership essay")
        conversation_manager.handle_message("What should I write about?")
        
        # Check that context includes previous turns
        context = conversation_manager.state.get_recent_context()
        assert "Hello" in context
        assert "leadership essay" in context
        
        # Verify all turns are in history
        assert len(conversation_manager.state.history) == 3
    
    def test_contextual_response_generation(self, conversation_manager):
        """Test that responses are contextual based on conversation history"""
        # First turn about leadership
        response1 = conversation_manager.handle_message("I need help with my leadership essay")
        
        # Second turn should be contextual
        response2 = conversation_manager.handle_message("What's a good story to use?")
        
        # Response should be relevant to leadership context
        context = conversation_manager.state.get_recent_context()
        assert "leadership" in context
        
        # Both turns should be recorded
        assert len(conversation_manager.state.history) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 