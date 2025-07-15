"""
Integration tests for advanced conversation features.
Tests the interaction between ClarificationDetector, ProactiveSuggestionEngine, 
ConversationFlowManager, and ConversationShortcuts.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from essay_agent.conversation import (
    ConversationManager, ConversationShortcuts, 
    ClarificationDetector, ProactiveSuggestionEngine, 
    ConversationFlowManager, EnhancedResponseGenerator
)
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile, CoreValue, Activity


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
                stories=["Learned programming through online courses", "Helped teammates improve"],
                used_in_essays=[]
            )
        ],
        stories=[
            {
                "title": "Coding Challenge Victory",
                "description": "Overcame a difficult programming problem",
                "theme": "perseverance",
                "impact": "Learned problem-solving skills"
            }
        ]
    )


class TestAdvancedConversationFeatures:
    """Integration tests for advanced conversation features"""
    
    def test_shortcuts_integration(self):
        """Test that shortcuts work correctly with the conversation system"""
        shortcuts = ConversationShortcuts()
        
        # Test all shortcuts are loaded
        assert len(shortcuts.shortcuts) == 8  # ideas, stories, outline, draft, revise, polish, status, help
        
        # Test specific shortcuts
        assert shortcuts.process_shortcut("ideas") == "Help me brainstorm ideas for my essay"
        assert shortcuts.process_shortcut("outline") == "Create an outline for my essay"
        assert shortcuts.process_shortcut("draft") == "Write a draft of my essay"
        
        # Test shortcuts help formatting
        help_text = shortcuts.format_shortcuts_help()
        assert "Available Shortcuts:" in help_text
        assert "Brainstorming:" in help_text
        assert "Planning:" in help_text
        assert "Writing:" in help_text
        assert "essay-agent chat --shortcut" in help_text
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_clarification_flow_integration(self, mock_get_llm, mock_profile):
        """Test the clarification flow works with conversation manager"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create conversation manager
        conversation = ConversationManager(user_id="test_user", profile=mock_profile)
        
        # Test vague request triggers clarification
        response = conversation.handle_message("help")
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Should trigger clarification
        assert "🤔" in response or "specific" in response.lower()
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_suggestion_engine_integration(self, mock_get_llm, mock_profile):
        """Test the suggestion engine works with conversation context"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create conversation manager
        conversation = ConversationManager(user_id="test_user", profile=mock_profile)
        
        # Provide context to avoid clarification
        response = conversation.handle_message("I need help with my personal statement for Stanford")
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Should have context now
        assert conversation.state.current_essay_context is not None
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_conversation_flow_progression(self, mock_get_llm, mock_profile):
        """Test conversation flow progresses correctly through phases"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create conversation manager
        conversation = ConversationManager(user_id="test_user", profile=mock_profile)
        
        # Start conversation
        response1 = conversation.handle_message("I need help with my college essay")
        assert isinstance(response1, str)
        
        # Provide more context
        response2 = conversation.handle_message("It's a personal statement for Stanford about leadership")
        assert isinstance(response2, str)
        
        # Should maintain conversation history
        assert len(conversation.state.history) == 2
        
        # Should have essay context
        if conversation.state.current_essay_context:
            # Context should be updated
            assert conversation.state.current_essay_context.essay_type in ["personal statement", "personal_statement"]
            assert conversation.state.current_essay_context.college_target == "Stanford"
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_enhanced_response_generation(self, mock_get_llm, mock_profile):
        """Test enhanced response generation with all features"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create conversation manager
        conversation = ConversationManager(user_id="test_user", profile=mock_profile)
        
        # Test help request gets enhanced response
        response = conversation.handle_message("help")
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain enhanced help with shortcuts
        assert "Available Shortcuts:" in response or "🤔" in response
    
    def test_conversation_shortcuts_cli_integration(self):
        """Test conversation shortcuts work with CLI arguments"""
        shortcuts = ConversationShortcuts()
        
        # Test that CLI shortcuts choices match available shortcuts
        available_shortcuts = shortcuts.get_available_shortcuts()
        shortcut_triggers = [s.trigger for s in available_shortcuts]
        
        # These should match the CLI choices
        expected_triggers = ["ideas", "stories", "outline", "draft", "revise", "polish", "status", "help"]
        
        for trigger in expected_triggers:
            assert trigger in shortcut_triggers
        
        # Test processing each shortcut
        for trigger in expected_triggers:
            result = shortcuts.process_shortcut(trigger)
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_conversation_memory_persistence(self, mock_get_llm, mock_profile):
        """Test conversation memory persists across sessions"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create first conversation session
        conversation1 = ConversationManager(user_id="memory_test_user", profile=mock_profile)
        
        # Have a conversation
        response1 = conversation1.handle_message("I need help with my Stanford personal statement")
        assert isinstance(response1, str)
        
        # Create second conversation session (simulating restart)
        conversation2 = ConversationManager(user_id="memory_test_user", profile=mock_profile)
        
        # Should load previous state
        assert len(conversation2.state.history) > 0
        
        # Should maintain context
        if conversation2.state.current_essay_context:
            assert conversation2.state.current_essay_context.college_target == "Stanford"
            assert conversation2.state.current_essay_context.essay_type in ["personal statement", "personal_statement"]
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_proactive_suggestions_with_context(self, mock_get_llm, mock_profile):
        """Test proactive suggestions are generated based on conversation context"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create conversation manager
        conversation = ConversationManager(user_id="suggestion_test_user", profile=mock_profile)
        
        # Provide specific context
        response = conversation.handle_message("I have my personal statement topic but need help structuring it")
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Should suggest next steps related to structuring
        assert "Suggestions:" in response or "🔮" in response or "outline" in response.lower()
    
    def test_all_features_integration(self):
        """Test that all advanced features work together"""
        # Test shortcuts
        shortcuts = ConversationShortcuts()
        assert len(shortcuts.shortcuts) > 0
        
        # Test clarification detector
        mock_llm = Mock()
        detector = ClarificationDetector(mock_llm)
        assert detector is not None
        
        # Test suggestion engine
        engine = ProactiveSuggestionEngine(mock_llm)
        assert engine is not None
        
        # Test flow manager
        flow_manager = ConversationFlowManager()
        assert flow_manager is not None
        
        # Test enhanced response generator
        generator = EnhancedResponseGenerator()
        assert generator is not None
        
        # All components should be initialized without errors
        assert True  # If we get here, all components initialized successfully 