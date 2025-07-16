"""Integration tests for CLI with ReAct agent integration.

This module tests the complete CLI functionality including the new ReAct agent
commands and ensures backward compatibility with existing functionality.
"""
import pytest
import asyncio
import subprocess
import sys
import json
import os
from unittest.mock import patch, AsyncMock, Mock
from typing import Dict, Any

from essay_agent.cli import main, _cmd_chat, _cmd_agent_status, _cmd_agent_memory, _cmd_agent_debug
from essay_agent.agent.core.react_agent import EssayReActAgent


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        yield


@pytest.fixture
def mock_react_agent():
    """Mock ReAct agent for testing."""
    agent = Mock(spec=EssayReActAgent)
    agent.handle_message = AsyncMock(return_value="Test agent response")
    agent.get_session_metrics.return_value = {
        "session_duration": 10.5,
        "interaction_count": 3,
        "average_response_time": 1.2,
        "total_response_time": 3.6,
        "reasoning_metrics": {
            "total_reasoning_requests": 3,
            "successful_requests": 3,
            "success_rate": 1.0,
            "average_reasoning_time": 0.8
        },
        "execution_metrics": {
            "total_executions": 3,
            "successful_executions": 3,
            "success_rate": 1.0,
            "average_execution_time": 0.4,
            "tool_usage_stats": {
                "brainstorm": {
                    "usage_count": 1,
                    "success_count": 1,
                    "avg_time": 0.5,
                    "total_time": 0.5
                }
            }
        },
        "interactions_per_minute": 17.1
    }
    agent._observe.return_value = {
        "user_profile": {"user_id": "test_user", "name": "Test User"},
        "conversation_history": [
            {"user_input": "Hello", "agent_response": "Hi there!"},
            {"user_input": "Help me", "agent_response": "Of course!"}
        ],
        "essay_state": {"current_phase": "brainstorming"},
        "patterns": ["writing_assistance", "creative_help"],
        "session_info": {
            "interaction_count": 2,
            "session_duration": 5.0,
            "avg_response_time": 1.0
        }
    }
    return agent


class TestCLIBackwardCompatibility:
    """Test that existing CLI commands still work unchanged."""
    
    def test_write_command_help(self):
        """Test that write command help is available."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "write", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Essay prompt" in result.stdout
    
    def test_tool_command_help(self):
        """Test that tool command help is available."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "tool", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Invoke a single registered tool" in result.stdout
    
    def test_eval_command_help(self):
        """Test that eval command help is available."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "eval", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Run evaluation harness" in result.stdout
    
    def test_chat_command_help(self):
        """Test that chat command help shows new ReAct features."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "chat", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "ReAct agent" in result.stdout


class TestNewAgentCommands:
    """Test new agent-specific commands."""
    
    def test_agent_status_command_help(self):
        """Test agent-status command help."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "agent-status", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "ReAct agent performance metrics" in result.stdout
    
    def test_agent_memory_command_help(self):
        """Test agent-memory command help."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "agent-memory", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "agent memory and conversation history" in result.stdout
    
    def test_agent_debug_command_help(self):
        """Test agent-debug command help."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "agent-debug", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "Debug ReAct agent reasoning" in result.stdout
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_status_command(self, mock_agent_class, mock_api_key, mock_react_agent):
        """Test agent-status command execution."""
        mock_agent_class.return_value = mock_react_agent
        
        # Test human-readable output
        with patch('sys.argv', ['cli.py', 'agent-status', '--user', 'test_user']):
            main()
        
        mock_agent_class.assert_called_once_with(user_id='test_user')
        mock_react_agent.get_session_metrics.assert_called_once()
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_memory_command(self, mock_agent_class, mock_api_key, mock_react_agent):
        """Test agent-memory command execution."""
        mock_agent_class.return_value = mock_react_agent
        
        with patch('sys.argv', ['cli.py', 'agent-memory', '--user', 'test_user', '--recent', '5']):
            main()
        
        mock_agent_class.assert_called_once_with(user_id='test_user')
        mock_react_agent._observe.assert_called_once()
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_debug_command(self, mock_agent_class, mock_api_key, mock_react_agent):
        """Test agent-debug command execution."""
        mock_agent_class.return_value = mock_react_agent
        
        with patch('sys.argv', ['cli.py', 'agent-debug', '--user', 'test_user']):
            main()
        
        mock_agent_class.assert_called_once_with(user_id='test_user')
        mock_react_agent.get_session_metrics.assert_called_once()


class TestReActChatIntegration:
    """Test ReAct agent chat integration."""
    
    @pytest.mark.asyncio
    @patch('essay_agent.cli.EssayReActAgent')
    @patch('essay_agent.cli._load_profile')
    async def test_chat_with_react_agent(self, mock_load_profile, mock_agent_class, mock_api_key, mock_react_agent):
        """Test chat command using ReAct agent."""
        mock_load_profile.return_value = Mock()
        mock_agent_class.return_value = mock_react_agent
        
        # Mock argument namespace
        args = Mock()
        args.user = 'test_user'
        args.profile = None
        args.shortcuts = False
        args.shortcut = None
        args.debug = False
        
        # Test shortcut execution
        args.shortcut = 'ideas'
        await _cmd_chat(args)
        
        mock_agent_class.assert_called_with(user_id='test_user')
        mock_react_agent.handle_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('essay_agent.cli.EssayReActAgent')
    @patch('essay_agent.cli._load_profile')
    @patch('builtins.input')
    async def test_interactive_chat_loop(self, mock_input, mock_load_profile, mock_agent_class, mock_api_key, mock_react_agent):
        """Test interactive chat loop with ReAct agent."""
        mock_load_profile.return_value = Mock()
        mock_agent_class.return_value = mock_react_agent
        
        # Simulate user interaction: message, status check, quit
        mock_input.side_effect = ['Help me with my essay', 'status', 'quit']
        
        args = Mock()
        args.user = 'test_user'
        args.profile = None
        args.shortcuts = False
        args.shortcut = None
        args.debug = False
        
        await _cmd_chat(args)
        
        # Should have called handle_message for the essay help
        mock_react_agent.handle_message.assert_called_with('Help me with my essay')
        # Should have called get_session_metrics for status
        assert mock_react_agent.get_session_metrics.call_count >= 1
    
    @patch('essay_agent.cli.ReActShortcuts')
    def test_shortcuts_system(self, mock_shortcuts_class):
        """Test ReAct shortcuts system."""
        mock_shortcuts = Mock()
        mock_shortcuts.get_message_for_shortcut.return_value = "Help me brainstorm ideas"
        mock_shortcuts.get_available_shortcuts.return_value = [
            {"trigger": "ideas", "description": "Brainstorm creative essay ideas"}
        ]
        mock_shortcuts_class.return_value = mock_shortcuts
        
        from essay_agent.cli import ReActShortcuts
        shortcuts = ReActShortcuts()
        
        # Test shortcut message retrieval
        message = shortcuts.get_message_for_shortcut('ideas')
        assert message == "Help me brainstorm ideas for my essay"
        
        # Test shortcuts listing
        available = shortcuts.get_available_shortcuts()
        assert len(available) == 8  # All defined shortcuts
        assert any(s['trigger'] == 'ideas' for s in available)


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""
    
    def test_chat_without_api_key(self):
        """Test chat command fails gracefully without API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = subprocess.run(
                [sys.executable, "-m", "essay_agent.cli", "chat", "--shortcuts"],
                capture_output=True, text=True
            )
            assert result.returncode == 1
            assert "OPENAI_API_KEY environment variable not set" in result.stderr
    
    def test_agent_status_without_api_key(self):
        """Test agent-status command fails gracefully without API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = subprocess.run(
                [sys.executable, "-m", "essay_agent.cli", "agent-status"],
                capture_output=True, text=True
            )
            assert result.returncode == 1
            assert "OPENAI_API_KEY environment variable not set" in result.stderr
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_initialization_error(self, mock_agent_class, mock_api_key):
        """Test handling of agent initialization errors."""
        mock_agent_class.side_effect = Exception("Agent initialization failed")
        
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "agent-status"],
            capture_output=True, text=True
        )
        assert result.returncode == 1
        assert "Error getting agent status" in result.stderr


class TestCLIPerformance:
    """Test CLI performance and responsiveness."""
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_status_response_time(self, mock_agent_class, mock_api_key, mock_react_agent):
        """Test that agent-status command responds quickly."""
        import time
        mock_agent_class.return_value = mock_react_agent
        
        start_time = time.time()
        with patch('sys.argv', ['cli.py', 'agent-status', '--user', 'test_user']):
            main()
        end_time = time.time()
        
        # Should complete within reasonable time (allowing for overhead)
        assert end_time - start_time < 2.0
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_memory_with_large_history(self, mock_agent_class, mock_api_key, mock_react_agent):
        """Test agent-memory command with large conversation history."""
        # Mock large conversation history
        large_history = [
            {"user_input": f"Message {i}", "agent_response": f"Response {i}"}
            for i in range(100)
        ]
        
        context = mock_react_agent._observe.return_value
        context["conversation_history"] = large_history
        
        with patch('sys.argv', ['cli.py', 'agent-memory', '--user', 'test_user', '--recent', '10']):
            main()
        
        # Should handle large history without issues
        mock_react_agent._observe.assert_called_once()


class TestCLIJSONOutput:
    """Test JSON output functionality."""
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_status_json_output(self, mock_agent_class, mock_api_key, mock_react_agent, capsys):
        """Test agent-status JSON output format."""
        mock_agent_class.return_value = mock_react_agent
        
        with patch('sys.argv', ['cli.py', 'agent-status', '--user', 'test_user', '--json']):
            main()
        
        captured = capsys.readouterr()
        
        # Should be valid JSON
        output_data = json.loads(captured.out)
        assert 'session_duration' in output_data
        assert 'interaction_count' in output_data
        assert 'reasoning_metrics' in output_data
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_memory_json_output(self, mock_agent_class, mock_api_key, mock_react_agent, capsys):
        """Test agent-memory JSON output format."""
        mock_agent_class.return_value = mock_react_agent
        
        with patch('sys.argv', ['cli.py', 'agent-memory', '--user', 'test_user', '--json']):
            main()
        
        captured = capsys.readouterr()
        
        # Should be valid JSON
        output_data = json.loads(captured.out)
        assert 'user_id' in output_data
        assert 'context' in output_data
        assert 'recent_count' in output_data
    
    @patch('essay_agent.cli.EssayReActAgent')
    def test_agent_debug_json_output(self, mock_agent_class, mock_api_key, mock_react_agent, capsys):
        """Test agent-debug JSON output format."""
        mock_agent_class.return_value = mock_react_agent
        
        with patch('sys.argv', ['cli.py', 'agent-debug', '--user', 'test_user', '--json']):
            main()
        
        captured = capsys.readouterr()
        
        # Should be valid JSON
        output_data = json.loads(captured.out)
        assert 'user_id' in output_data
        assert 'reasoning_metrics' in output_data
        assert 'execution_metrics' in output_data
        assert 'session_metrics' in output_data


class TestDemoIntegration:
    """Test demo.py integration with ReAct agent."""
    
    def test_demo_use_react_flag(self):
        """Test demo --use-react flag is available."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.demo", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "--use-react" in result.stdout
    
    @patch('essay_agent.demo.EssayReActAgent')
    def test_demo_with_react_agent(self, mock_agent_class, mock_api_key):
        """Test demo execution with ReAct agent."""
        mock_agent = Mock()
        mock_agent.handle_message = AsyncMock(return_value="Demo response")
        mock_agent.get_session_metrics.return_value = {
            "interaction_count": 5,
            "session_duration": 10.0,
            "average_response_time": 2.0,
            "reasoning_metrics": {"success_rate": 1.0},
            "execution_metrics": {"success_rate": 1.0}
        }
        mock_agent_class.return_value = mock_agent
        
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.demo", "--use-react"],
            capture_output=True, text=True
        )
        
        # Should complete successfully
        assert result.returncode == 0
        # Should show enhanced demo output
        assert "ReAct" in result.stdout or "enhanced" in result.stdout.lower()


class TestCLIUsabilityFeatures:
    """Test CLI usability and user experience features."""
    
    def test_shortcuts_help_display(self):
        """Test shortcuts help display."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "chat", "--shortcuts"],
            capture_output=True, text=True
        )
        # Should exit with error due to missing API key, but show shortcuts
        assert "Available shortcuts" in result.stdout or "shortcuts" in result.stderr
    
    @patch('essay_agent.cli.EssayReActAgent')
    @patch('essay_agent.cli._load_profile')
    @patch('builtins.input')
    async def test_status_command_in_chat(self, mock_input, mock_load_profile, mock_agent_class, mock_api_key, mock_react_agent):
        """Test status command within chat interface."""
        mock_load_profile.return_value = Mock()
        mock_agent_class.return_value = mock_react_agent
        mock_input.side_effect = ['status', 'quit']
        
        args = Mock()
        args.user = 'test_user'
        args.profile = None
        args.shortcuts = False
        args.shortcut = None
        args.debug = False
        
        await _cmd_chat(args)
        
        # Should have called get_session_metrics for status display
        mock_react_agent.get_session_metrics.assert_called()
    
    def test_main_command_help(self):
        """Test main CLI help shows all commands."""
        result = subprocess.run(
            [sys.executable, "-m", "essay_agent.cli", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        
        # Should show all commands
        assert "write" in result.stdout
        assert "tool" in result.stdout
        assert "eval" in result.stdout
        assert "chat" in result.stdout
        assert "agent-status" in result.stdout
        assert "agent-memory" in result.stdout
        assert "agent-debug" in result.stdout 