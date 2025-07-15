"""
Unit tests for the enhanced conversational tool execution system.
Tests the ConversationalToolExecutor, ToolExecutionResult, and related components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from dataclasses import dataclass

from essay_agent.conversation import (
    ConversationManager, ConversationalToolExecutor, ToolExecutionResult, 
    ExecutionStatus, ConversationState, ConversationTurn, ResponseGenerator,
    ClarificationDetector, ProactiveSuggestionEngine, ConversationFlowManager,
    ConversationShortcuts, ClarificationQuestion, ProactiveSuggestion,
    ConversationShortcut, EnhancedResponseGenerator
)
from essay_agent.planning import ConversationalPlanner, PlanningContext
from essay_agent.planner import EssayPlan, Phase
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile, CoreValue, Activity
from essay_agent.tools import REGISTRY as TOOL_REGISTRY


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


@pytest.fixture
def mock_plan():
    """Create a mock essay plan for testing"""
    return EssayPlan(
        phase=Phase.BRAINSTORMING,
        data={"prompt": "Test prompt", "num_stories": 3, "reasoning": "Test reasoning"},
        errors=[],
        metadata={}
    )


@pytest.fixture
def mock_planner(mock_plan):
    """Create a mock conversational planner"""
    planner = Mock(spec=ConversationalPlanner)
    planner.create_conversational_plan.return_value = mock_plan
    return planner


@pytest.fixture
def tool_executor(mock_planner):
    """Create a ConversationalToolExecutor instance"""
    return ConversationalToolExecutor(mock_planner)


@pytest.fixture
def conversation_state(mock_profile):
    """Create a conversation state for testing"""
    return ConversationState(
        user_id="test_user",
        profile=mock_profile
    )


@pytest.fixture
def mock_conversation_state(mock_profile):
    """Create a mock conversation state for testing"""
    return ConversationState(user_id="test_user", profile=mock_profile)


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing"""
    mock = Mock()
    mock.predict.return_value = "Mock LLM response"
    mock.invoke.return_value = "Mock LLM response"
    return mock


# Advanced Conversation Features Tests

class TestClarificationDetector:
    """Test ClarificationDetector class"""
    
    def test_detect_ambiguity_missing_essay_type(self, mock_llm, mock_conversation_state):
        """Test detection of missing essay type"""
        detector = ClarificationDetector(mock_llm)
        
        # Test with vague input and no essay context
        result = detector.detect_ambiguity("help me with my essay", mock_conversation_state)
        
        assert result is not None
        assert isinstance(result, ClarificationQuestion)
        assert "type of essay" in result.question.lower()
        assert result.priority == 5
        assert len(result.suggestions) > 0
    
    def test_detect_ambiguity_vague_request(self, mock_llm, mock_conversation_state):
        """Test detection of vague requests"""
        detector = ClarificationDetector(mock_llm)
        
        # Test with very short vague request
        result = detector.detect_ambiguity("help", mock_conversation_state)
        
        assert result is not None
        assert "more specific" in result.question.lower()
        assert result.priority >= 2
    
    def test_detect_ambiguity_clear_request(self, mock_llm, mock_conversation_state):
        """Test that clear requests don't trigger clarification"""
        detector = ClarificationDetector(mock_llm)
        
        # Add some context to the state
        from essay_agent.conversation import EssayContext
        mock_conversation_state.current_essay_context = EssayContext(
            essay_type="personal statement",
            college_target="Stanford",
            progress_stage="drafting"
        )
        
        # Test with clear, specific request
        result = detector.detect_ambiguity("help me write a strong introduction paragraph for my essay", mock_conversation_state)
        
        assert result is None
    
    def test_detect_ambiguous_pronouns(self, mock_llm, mock_conversation_state):
        """Test detection of ambiguous pronouns"""
        detector = ClarificationDetector(mock_llm)
        
        # Test with ambiguous pronouns
        result = detector.detect_ambiguity("make this better", mock_conversation_state)
        
        assert result is not None
        assert result.priority >= 2
    
    def test_clarification_question_formatting(self):
        """Test clarification question formatting"""
        question = ClarificationQuestion(
            question="What type of essay?",
            context="Missing essay type",
            suggestions=["Personal statement", "Supplemental essay"],
            priority=3
        )
        
        formatted = question.format_for_display()
        
        assert "🤔" in formatted
        assert "What type of essay?" in formatted
        assert "💡" in formatted
        assert "Personal statement" in formatted
        assert "Supplemental essay" in formatted


class TestProactiveSuggestionEngine:
    """Test ProactiveSuggestionEngine class"""
    
    def test_generate_suggestions_planning_stage(self, mock_llm, mock_conversation_state):
        """Test suggestion generation for planning stage"""
        engine = ProactiveSuggestionEngine(mock_llm)
        
        # Set up planning stage context
        from essay_agent.conversation import EssayContext
        mock_conversation_state.current_essay_context = EssayContext(
            essay_type="personal statement",
            progress_stage="planning"
        )
        
        suggestions = engine.generate_suggestions(mock_conversation_state, [])
        
        assert len(suggestions) > 0
        assert all(isinstance(s, ProactiveSuggestion) for s in suggestions)
        assert any("brainstorm" in s.suggestion.lower() or "outline" in s.suggestion.lower() 
                  for s in suggestions)
    
    def test_generate_suggestions_drafting_stage(self, mock_llm, mock_conversation_state):
        """Test suggestion generation for drafting stage"""
        engine = ProactiveSuggestionEngine(mock_llm)
        
        # Set up drafting stage context
        from essay_agent.conversation import EssayContext
        mock_conversation_state.current_essay_context = EssayContext(
            essay_type="personal statement",
            progress_stage="drafting"
        )
        
        suggestions = engine.generate_suggestions(mock_conversation_state, ["outline"])
        
        assert len(suggestions) > 0
        assert any("draft" in s.suggestion.lower() or "write" in s.suggestion.lower() 
                  for s in suggestions)
    
    def test_suggestion_personalization(self, mock_llm, mock_conversation_state):
        """Test suggestion personalization based on user preferences"""
        engine = ProactiveSuggestionEngine(mock_llm)
        
        # Set up user preferences
        from essay_agent.conversation import UserPreferences
        mock_conversation_state.user_preferences = UserPreferences(
            writing_style="creative",
            tool_usage_patterns={"brainstorm": 5, "outline": 3}
        )
        
        suggestions = engine.generate_suggestions(mock_conversation_state, [])
        
        assert len(suggestions) > 0
        # Check that confidence scores are adjusted for preferred tools
        brainstorm_suggestions = [s for s in suggestions if "brainstorm" in s.suggestion.lower()]
        if brainstorm_suggestions:
            assert any(s.confidence > 0.5 for s in brainstorm_suggestions)
    
    def test_suggestion_formatting(self):
        """Test suggestion formatting for display"""
        suggestion = ProactiveSuggestion(
            suggestion="Create an outline for your essay",
            reasoning="Organization helps with writing",
            action_type="planning",
            confidence=0.8
        )
        
        formatted = suggestion.format_for_display()
        
        assert "📋" in formatted  # Planning icon
        assert "Create an outline for your essay" in formatted


class TestConversationFlowManager:
    """Test ConversationFlowManager class"""
    
    def test_detect_conversation_phase_exploration(self, mock_conversation_state):
        """Test detection of exploration phase"""
        manager = ConversationFlowManager()
        
        # Empty conversation should be exploration
        phase = manager._detect_conversation_phase(mock_conversation_state)
        
        assert phase == "exploration"
    
    def test_detect_conversation_phase_work(self, mock_conversation_state):
        """Test detection of work phase"""
        manager = ConversationFlowManager()
        
        # Add some tool usage history
        from essay_agent.conversation import ConversationTurn, ToolExecutionResult, ExecutionStatus
        tool_result = ToolExecutionResult(
            tool_name="brainstorm",
            status=ExecutionStatus.SUCCESS,
            result="Mock brainstorm result"
        )
        
        turn = ConversationTurn(
            user_input="help me brainstorm",
            agent_response="Here are some ideas",
            tool_results=[tool_result]
        )
        
        mock_conversation_state.history.append(turn)
        
        phase = manager._detect_conversation_phase(mock_conversation_state)
        
        assert phase == "work"
    
    def test_analyze_user_intent(self):
        """Test user intent analysis"""
        manager = ConversationFlowManager()
        
        # Test various intent patterns
        assert manager._analyze_user_intent("help me brainstorm ideas") == "brainstorm"
        assert manager._analyze_user_intent("create an outline") == "outline"
        assert manager._analyze_user_intent("write a draft") == "write"
        assert manager._analyze_user_intent("revise my essay") == "revise"
        assert manager._analyze_user_intent("polish my essay") == "polish"
        assert manager._analyze_user_intent("can you help me?") == "help"
    
    def test_should_ask_clarification(self, mock_conversation_state):
        """Test clarification need detection"""
        manager = ConversationFlowManager()
        
        # Short requests should trigger clarification
        assert manager._should_ask_clarification("help", mock_conversation_state) == True
        
        # Ambiguous pronouns should trigger clarification
        assert manager._should_ask_clarification("improve this", mock_conversation_state) == True
        
        # Clear requests should not trigger clarification
        assert manager._should_ask_clarification("help me write an introduction paragraph", mock_conversation_state) == False
    
    def test_manage_conversation_flow(self, mock_conversation_state):
        """Test complete conversation flow management"""
        manager = ConversationFlowManager()
        
        flow_analysis = manager.manage_conversation_flow("help me brainstorm", mock_conversation_state)
        
        assert "current_phase" in flow_analysis
        assert "user_intent" in flow_analysis
        assert "needs_clarification" in flow_analysis
        assert "suggested_response_type" in flow_analysis
        assert "conversation_context" in flow_analysis
        
        assert flow_analysis["user_intent"] == "brainstorm"
        assert flow_analysis["current_phase"] in ["exploration", "work", "review", "completion"]


class TestConversationShortcuts:
    """Test ConversationShortcuts class"""
    
    def test_load_shortcuts(self):
        """Test loading of predefined shortcuts"""
        shortcuts = ConversationShortcuts()
        
        assert len(shortcuts.shortcuts) > 0
        assert "ideas" in shortcuts.shortcuts
        assert "outline" in shortcuts.shortcuts
        assert "draft" in shortcuts.shortcuts
        assert "revise" in shortcuts.shortcuts
        assert "polish" in shortcuts.shortcuts
        assert "help" in shortcuts.shortcuts
        assert "status" in shortcuts.shortcuts
    
    def test_process_shortcut_valid(self):
        """Test processing valid shortcuts"""
        shortcuts = ConversationShortcuts()
        
        result = shortcuts.process_shortcut("ideas")
        assert result == "Help me brainstorm ideas for my essay"
        
        result = shortcuts.process_shortcut("outline")
        assert result == "Create an outline for my essay"
        
        result = shortcuts.process_shortcut("draft")
        assert result == "Write a draft of my essay"
    
    def test_process_shortcut_invalid(self):
        """Test processing invalid shortcuts"""
        shortcuts = ConversationShortcuts()
        
        result = shortcuts.process_shortcut("invalid")
        assert result is None
        
        result = shortcuts.process_shortcut("")
        assert result is None
    
    def test_get_available_shortcuts(self):
        """Test getting available shortcuts"""
        shortcuts = ConversationShortcuts()
        
        available = shortcuts.get_available_shortcuts()
        
        assert len(available) > 0
        assert all(isinstance(s, ConversationShortcut) for s in available)
        assert any(s.trigger == "ideas" for s in available)
        assert any(s.trigger == "outline" for s in available)
    
    def test_get_shortcuts_by_category(self):
        """Test getting shortcuts by category"""
        shortcuts = ConversationShortcuts()
        
        brainstorming = shortcuts.get_shortcuts_by_category("brainstorming")
        planning = shortcuts.get_shortcuts_by_category("planning")
        writing = shortcuts.get_shortcuts_by_category("writing")
        
        assert len(brainstorming) > 0
        assert len(planning) > 0
        assert len(writing) > 0
        
        assert all(s.category == "brainstorming" for s in brainstorming)
        assert all(s.category == "planning" for s in planning)
        assert all(s.category == "writing" for s in writing)
    
    def test_format_shortcuts_help(self):
        """Test formatting shortcuts help"""
        shortcuts = ConversationShortcuts()
        
        help_text = shortcuts.format_shortcuts_help()
        
        assert "Available Shortcuts" in help_text
        assert "💡" in help_text  # Brainstorming icon
        assert "📋" in help_text  # Planning icon
        assert "✍️" in help_text  # Writing icon
        assert "Usage:" in help_text
        assert "essay-agent chat --shortcut" in help_text


class TestEnhancedResponseGenerator:
    """Test EnhancedResponseGenerator class"""
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_generate_response_with_clarification(self, mock_get_llm, mock_conversation_state):
        """Test response generation with clarification"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        generator = EnhancedResponseGenerator()
        
        # Test with ambiguous input
        response = generator.generate_response(
            "help me",
            None,
            mock_conversation_state,
            []
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Should ask for clarification
        assert "🤔" in response or "more specific" in response.lower()
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_generate_response_with_suggestions(self, mock_get_llm, mock_conversation_state):
        """Test response generation with proactive suggestions"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        generator = EnhancedResponseGenerator()
        
        # Add some context to avoid clarification
        from essay_agent.conversation import EssayContext
        mock_conversation_state.current_essay_context = EssayContext(
            essay_type="personal statement",
            progress_stage="planning"
        )
        
        # Mock tool results
        tool_results = [
            ToolExecutionResult(
                tool_name="brainstorm",
                status=ExecutionStatus.SUCCESS,
                result="Mock brainstorm result"
            )
        ]
        
        response = generator.generate_response(
            "help me brainstorm ideas",
            None,
            mock_conversation_state,
            tool_results
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain suggestions
        assert "Suggestions:" in response or "🔮" in response
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_generate_enhanced_help_response(self, mock_get_llm, mock_conversation_state):
        """Test enhanced help response generation"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        generator = EnhancedResponseGenerator()
        
        # Add context for personalized help
        from essay_agent.conversation import EssayContext
        mock_conversation_state.current_essay_context = EssayContext(
            essay_type="personal statement",
            college_target="Stanford",
            progress_stage="drafting"
        )
        
        response = generator._generate_enhanced_help_response(mock_conversation_state)
        
        assert isinstance(response, str)
        assert "Current Context:" in response
        assert "personal statement" in response
        assert "Stanford" in response
        assert "drafting" in response
        assert "Available Shortcuts:" in response
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_handle_quit_request(self, mock_get_llm, mock_conversation_state):
        """Test handling of quit requests"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        generator = EnhancedResponseGenerator()
        
        response = generator.generate_response(
            "quit",
            None,
            mock_conversation_state,
            []
        )
        
        assert "Goodbye" in response
        assert "conversation has been saved" in response
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_handle_help_request(self, mock_get_llm, mock_conversation_state):
        """Test handling of help requests"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        generator = EnhancedResponseGenerator()
        
        response = generator.generate_response(
            "help",
            None,
            mock_conversation_state,
            []
        )
        
        assert "Essay Agent Chat Help" in response
        assert "Available Shortcuts:" in response


# Integration tests for advanced conversation features

class TestAdvancedConversationIntegration:
    """Integration tests for advanced conversation features"""
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_conversation_with_clarification_flow(self, mock_get_llm, mock_profile):
        """Test complete conversation flow with clarification"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create conversation manager
        conversation = ConversationManager(user_id="test_user", profile=mock_profile)
        
        # Test vague request that should trigger clarification
        response = conversation.handle_message("help me")
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Should ask for clarification
        assert "🤔" in response or "more specific" in response.lower()
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_conversation_with_shortcut_processing(self, mock_get_llm, mock_profile):
        """Test conversation with shortcut processing"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create conversation manager
        conversation = ConversationManager(user_id="test_user", profile=mock_profile)
        
        # Test shortcut processing
        shortcuts = ConversationShortcuts()
        shortcut_command = shortcuts.process_shortcut("ideas")
        
        assert shortcut_command == "Help me brainstorm ideas for my essay"
        
        # Test that shortcut can be processed by conversation
        response = conversation.handle_message(shortcut_command)
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @patch('essay_agent.conversation.get_chat_llm')
    def test_conversation_flow_progression(self, mock_get_llm, mock_profile):
        """Test conversation flow progression through phases"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Create conversation manager
        conversation = ConversationManager(user_id="test_user", profile=mock_profile)
        
        # Start with exploration phase
        response1 = conversation.handle_message("I need help with my college essay")
        assert isinstance(response1, str)
        
        # Move to work phase
        response2 = conversation.handle_message("It's a personal statement for Stanford")
        assert isinstance(response2, str)
        
        # Should maintain context across turns
        assert len(conversation.state.history) == 2
        assert conversation.state.history[0].user_input == "I need help with my college essay"
        assert conversation.state.history[1].user_input == "It's a personal statement for Stanford"


# New test classes for conversation evaluation features

class TestConversationQualityEvaluator:
    """Test ConversationQualityEvaluator class"""
    
    @patch('essay_agent.eval.conversation.get_chat_llm')
    def test_evaluate_conversation_quality(self, mock_get_llm, mock_conversation_state):
        """Test basic conversation quality evaluation"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        from essay_agent.eval.conversation import ConversationQualityEvaluator
        evaluator = ConversationQualityEvaluator(mock_llm)
        
        # Add some conversation history
        turn1 = ConversationTurn(
            user_input="Help me brainstorm ideas",
            agent_response="I can help you brainstorm ideas for your essay. Here are some suggestions:",
            tool_results=[
                ToolExecutionResult(
                    tool_name="brainstorm",
                    status=ExecutionStatus.SUCCESS,
                    result="Mock brainstorm result"
                )
            ]
        )
        
        turn2 = ConversationTurn(
            user_input="Create an outline",
            agent_response="I'll help you create an outline based on your ideas.",
            tool_results=[
                ToolExecutionResult(
                    tool_name="outline",
                    status=ExecutionStatus.SUCCESS,
                    result="Mock outline result"
                )
            ]
        )
        
        mock_conversation_state.history = [turn1, turn2]
        
        # Evaluate quality
        metrics = evaluator.evaluate_conversation_quality(mock_conversation_state)
        
        assert metrics.turn_count == 2
        assert 0.0 <= metrics.relevance_score <= 1.0
        assert 0.0 <= metrics.helpfulness_score <= 1.0
        assert 0.0 <= metrics.coherence_score <= 1.0
        assert 0.0 <= metrics.overall_quality <= 1.0
    
    @patch('essay_agent.eval.conversation.get_chat_llm')
    def test_calculate_relevance_score(self, mock_get_llm, mock_conversation_state):
        """Test relevance score calculation"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        from essay_agent.eval.conversation import ConversationQualityEvaluator
        evaluator = ConversationQualityEvaluator(mock_llm)
        
        # Test with relevant conversation
        turn = ConversationTurn(
            user_input="Help me brainstorm essay ideas",
            agent_response="I can help you brainstorm ideas for your essay. Here are some suggestions for your brainstorming session.",
            tool_results=[]
        )
        
        score = evaluator._calculate_relevance_score([turn])
        
        assert 0.0 <= score <= 1.0
        assert score > 0.3  # Should be reasonably high due to keyword overlap
    
    @patch('essay_agent.eval.conversation.get_chat_llm')
    def test_calculate_helpfulness_score(self, mock_get_llm, mock_conversation_state):
        """Test helpfulness score calculation"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        from essay_agent.eval.conversation import ConversationQualityEvaluator
        evaluator = ConversationQualityEvaluator(mock_llm)
        
        # Test with successful tool execution
        turn = ConversationTurn(
            user_input="Help me brainstorm",
            agent_response="Here are some brainstorming suggestions:",
            tool_results=[
                ToolExecutionResult(
                    tool_name="brainstorm",
                    status=ExecutionStatus.SUCCESS,
                    result="Mock result"
                )
            ]
        )
        
        score = evaluator._calculate_helpfulness_score([turn])
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high due to successful tool execution
    
    @patch('essay_agent.eval.conversation.get_chat_llm')
    def test_calculate_coherence_score(self, mock_get_llm, mock_conversation_state):
        """Test coherence score calculation"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        from essay_agent.eval.conversation import ConversationQualityEvaluator
        evaluator = ConversationQualityEvaluator(mock_llm)
        
        # Test with coherent conversation
        turns = [
            ConversationTurn(
                user_input="Help me with my essay",
                agent_response="I can help you with your essay. What type of essay are you working on?",
                tool_results=[]
            ),
            ConversationTurn(
                user_input="It's a personal statement",
                agent_response="Great! I can help you with your personal statement. Let's start brainstorming.",
                tool_results=[]
            )
        ]
        
        score = evaluator._calculate_coherence_score(turns)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.2  # Should have some coherence due to topic consistency
    
    @patch('essay_agent.eval.conversation.get_chat_llm')
    def test_empty_conversation_handling(self, mock_get_llm, mock_conversation_state):
        """Test handling of empty conversations"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        from essay_agent.eval.conversation import ConversationQualityEvaluator
        evaluator = ConversationQualityEvaluator(mock_llm)
        
        # Test with empty conversation
        mock_conversation_state.history = []
        
        metrics = evaluator.evaluate_conversation_quality(mock_conversation_state)
        
        assert metrics.turn_count == 0
        assert metrics.relevance_score == 0.0
        assert metrics.helpfulness_score == 0.0
        assert metrics.coherence_score == 0.0
        assert metrics.overall_quality == 0.0


class TestIntentRecognitionEvaluator:
    """Test IntentRecognitionEvaluator class"""
    
    def test_evaluate_intent_accuracy(self):
        """Test intent recognition accuracy evaluation"""
        from essay_agent.eval.conversation import IntentRecognitionEvaluator
        from essay_agent.conversation import ConversationFlowManager
        
        flow_manager = ConversationFlowManager()
        evaluator = IntentRecognitionEvaluator(flow_manager)
        
        # Run evaluation
        results = evaluator.evaluate_intent_accuracy()
        
        assert 'overall_accuracy' in results
        assert 'accuracy_by_intent' in results
        assert 'precision_by_intent' in results
        assert 'recall_by_intent' in results
        assert 'f1_by_intent' in results
        
        assert 0.0 <= results['overall_accuracy'] <= 1.0
        
        # Check that all expected intents are covered
        expected_intents = ['help', 'brainstorm', 'outline', 'write', 'revise', 'polish', 'review', 'general']
        for intent in expected_intents:
            assert intent in results['accuracy_by_intent']
            assert 0.0 <= results['accuracy_by_intent'][intent] <= 1.0
    
    def test_load_intent_test_cases(self):
        """Test loading of intent test cases"""
        from essay_agent.eval.conversation import IntentRecognitionEvaluator
        from essay_agent.conversation import ConversationFlowManager
        
        flow_manager = ConversationFlowManager()
        evaluator = IntentRecognitionEvaluator(flow_manager)
        
        test_cases = evaluator._load_intent_test_cases()
        
        assert len(test_cases) > 0
        assert all(hasattr(case, 'user_input') for case in test_cases)
        assert all(hasattr(case, 'expected_intent') for case in test_cases)
        assert all(hasattr(case, 'category') for case in test_cases)
        
        # Check for variety of intents
        intents = set(case.expected_intent for case in test_cases)
        assert len(intents) >= 7  # Should have at least 7 different intents
    
    def test_generate_intent_report(self):
        """Test intent recognition report generation"""
        from essay_agent.eval.conversation import IntentRecognitionEvaluator
        from essay_agent.conversation import ConversationFlowManager
        
        flow_manager = ConversationFlowManager()
        evaluator = IntentRecognitionEvaluator(flow_manager)
        
        report = evaluator.generate_intent_report()
        
        assert 'overall_accuracy' in report
        assert 'average_precision' in report
        assert 'average_recall' in report
        assert 'average_f1' in report
        assert 'total_test_cases' in report
        assert 'intents_tested' in report
        
        assert 0.0 <= report['overall_accuracy'] <= 1.0
        assert 0.0 <= report['average_precision'] <= 1.0
        assert 0.0 <= report['average_recall'] <= 1.0
        assert 0.0 <= report['average_f1'] <= 1.0
        assert report['total_test_cases'] > 0
        assert len(report['intents_tested']) > 0


class TestContextTrackingEvaluator:
    """Test ContextTrackingEvaluator class"""
    
    def test_evaluate_context_tracking(self, mock_profile):
        """Test context tracking evaluation"""
        from essay_agent.eval.conversation import ContextTrackingEvaluator
        
        evaluator = ContextTrackingEvaluator(mock_profile)
        
        # Run evaluation
        results = evaluator.evaluate_context_tracking()
        
        assert 'scenario_success_rates' in results
        assert 'overall_success_rate' in results
        assert 'context_preservation_rate' in results
        assert 'long_conversation_success' in results
        assert 'preference_learning_accuracy' in results
        
        assert 0.0 <= results['overall_success_rate'] <= 1.0
        assert 0.0 <= results['context_preservation_rate'] <= 1.0
        assert 0.0 <= results['long_conversation_success'] <= 1.0
        assert 0.0 <= results['preference_learning_accuracy'] <= 1.0
    
    def test_load_context_scenarios(self, mock_profile):
        """Test loading of context scenarios"""
        from essay_agent.eval.conversation import ContextTrackingEvaluator
        
        evaluator = ContextTrackingEvaluator(mock_profile)
        
        scenarios = evaluator._load_context_scenarios()
        
        assert len(scenarios) > 0
        assert all(hasattr(scenario, 'scenario_name') for scenario in scenarios)
        assert all(hasattr(scenario, 'turns') for scenario in scenarios)
        assert all(hasattr(scenario, 'expected_context') for scenario in scenarios)
        assert all(hasattr(scenario, 'success_criteria') for scenario in scenarios)
        
        # Check for variety of scenarios
        scenario_names = set(scenario.scenario_name for scenario in scenarios)
        assert len(scenario_names) >= 3  # Should have at least 3 different scenarios
        
        # Check for long conversation scenarios
        long_scenarios = [s for s in scenarios if len(s.turns) >= 10]
        assert len(long_scenarios) >= 1  # Should have at least one long scenario
    
    def test_validate_context(self, mock_profile):
        """Test context validation"""
        from essay_agent.eval.conversation import ContextTrackingEvaluator
        from essay_agent.conversation import EssayContext
        
        evaluator = ContextTrackingEvaluator(mock_profile)
        
        # Test perfect match
        context = EssayContext(
            essay_type="personal statement",
            college_target="Stanford",
            progress_stage="planning"
        )
        
        expected = {
            "essay_type": "personal statement",
            "college_target": "Stanford",
            "progress_stage": "planning"
        }
        
        score = evaluator._validate_context(context, expected)
        assert score == 1.0
        
        # Test partial match
        context = EssayContext(
            essay_type="personal statement",
            college_target="Harvard",  # Different college
            progress_stage="planning"
        )
        
        score = evaluator._validate_context(context, expected)
        assert 0.0 <= score < 1.0
    
    def test_generate_context_report(self, mock_profile):
        """Test context tracking report generation"""
        from essay_agent.eval.conversation import ContextTrackingEvaluator
        
        evaluator = ContextTrackingEvaluator(mock_profile)
        
        report = evaluator.generate_context_report()
        
        assert 'overall_success_rate' in report
        assert 'context_preservation_rate' in report
        assert 'long_conversation_success' in report
        assert 'preference_learning_accuracy' in report
        assert 'scenario_results' in report
        assert 'total_scenarios' in report
        assert 'scenarios_tested' in report
        
        assert 0.0 <= report['overall_success_rate'] <= 1.0
        assert 0.0 <= report['context_preservation_rate'] <= 1.0
        assert 0.0 <= report['long_conversation_success'] <= 1.0
        assert report['total_scenarios'] > 0
        assert len(report['scenarios_tested']) > 0


class TestConversationTestRunner:
    """Test ConversationTestRunner class"""
    
    def test_run_comprehensive_evaluation(self, mock_profile):
        """Test comprehensive conversation evaluation"""
        from essay_agent.eval.conversation import ConversationTestRunner
        
        runner = ConversationTestRunner(mock_profile)
        
        # Run evaluation
        report = runner.run_comprehensive_evaluation()
        
        assert hasattr(report, 'quality_metrics')
        assert hasattr(report, 'intent_recognition_accuracy')
        assert hasattr(report, 'context_tracking_success')
        assert hasattr(report, 'integration_test_results')
        assert hasattr(report, 'overall_score')
        assert hasattr(report, 'recommendations')
        assert hasattr(report, 'execution_time')
        assert hasattr(report, 'test_timestamp')
        
        assert 0.0 <= report.overall_score <= 1.0
        assert 0.0 <= report.intent_recognition_accuracy <= 1.0
        assert 0.0 <= report.context_tracking_success <= 1.0
        assert isinstance(report.recommendations, list)
        assert report.execution_time > 0
        assert len(report.test_timestamp) > 0
    
    def test_run_quality_evaluation(self, mock_profile):
        """Test quality evaluation"""
        from essay_agent.eval.conversation import ConversationTestRunner
        
        runner = ConversationTestRunner(mock_profile)
        
        # Run quality evaluation
        metrics = runner.run_quality_evaluation()
        
        assert hasattr(metrics, 'relevance_score')
        assert hasattr(metrics, 'helpfulness_score')
        assert hasattr(metrics, 'coherence_score')
        assert hasattr(metrics, 'overall_quality')
        assert hasattr(metrics, 'turn_count')
        
        assert 0.0 <= metrics.overall_quality <= 1.0
        assert metrics.turn_count > 0
    
    def test_run_intent_evaluation(self, mock_profile):
        """Test intent evaluation"""
        from essay_agent.eval.conversation import ConversationTestRunner
        
        runner = ConversationTestRunner(mock_profile)
        
        # Run intent evaluation
        results = runner.run_intent_evaluation()
        
        assert 'overall_accuracy' in results
        assert 'accuracy_by_intent' in results
        assert 0.0 <= results['overall_accuracy'] <= 1.0
    
    def test_run_context_evaluation(self, mock_profile):
        """Test context evaluation"""
        from essay_agent.eval.conversation import ConversationTestRunner
        
        runner = ConversationTestRunner(mock_profile)
        
        # Run context evaluation
        results = runner.run_context_evaluation()
        
        assert 'overall_success_rate' in results
        assert 'context_preservation_rate' in results
        assert 0.0 <= results['overall_success_rate'] <= 1.0
    
    def test_run_integration_tests(self, mock_profile):
        """Test integration tests"""
        from essay_agent.eval.conversation import ConversationTestRunner
        
        runner = ConversationTestRunner(mock_profile)
        
        # Run integration tests
        results = runner.run_integration_tests()
        
        assert 'basic_workflow' in results
        assert 'tool_execution' in results
        assert 'context_persistence' in results
        assert 'conversation_flow' in results
        
        assert isinstance(results['basic_workflow'], bool)
        assert isinstance(results['tool_execution'], bool)
        assert isinstance(results['context_persistence'], bool)
        assert isinstance(results['conversation_flow'], bool)
    
    def test_calculate_overall_score(self, mock_profile):
        """Test overall score calculation"""
        from essay_agent.eval.conversation import ConversationTestRunner, ConversationQualityMetrics
        
        runner = ConversationTestRunner(mock_profile)
        
        # Create mock metrics
        quality_metrics = ConversationQualityMetrics(
            overall_quality=0.8,
            turn_count=5
        )
        
        intent_results = {'overall_accuracy': 0.9}
        context_results = {'overall_success_rate': 0.85}
        integration_results = {
            'basic_workflow': True,
            'tool_execution': True,
            'context_persistence': True,
            'conversation_flow': True
        }
        
        # Calculate overall score
        score = runner._calculate_overall_score(
            quality_metrics, intent_results, context_results, integration_results
        )
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be reasonably high with good metrics
    
    def test_generate_recommendations(self, mock_profile):
        """Test recommendation generation"""
        from essay_agent.eval.conversation import ConversationTestRunner, ConversationQualityMetrics
        
        runner = ConversationTestRunner(mock_profile)
        
        # Create mock metrics with some low scores
        quality_metrics = ConversationQualityMetrics(
            relevance_score=0.5,  # Low relevance
            helpfulness_score=0.9,
            coherence_score=0.6,  # Low coherence
            overall_quality=0.7
        )
        
        intent_results = {'overall_accuracy': 0.8}  # Low intent accuracy
        context_results = {'context_preservation_rate': 0.7}  # Low context preservation
        integration_results = {
            'basic_workflow': True,
            'tool_execution': False,  # Failed integration
            'context_persistence': True,
            'conversation_flow': True
        }
        
        # Generate recommendations
        recommendations = runner._generate_recommendations(
            quality_metrics, intent_results, context_results, integration_results
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check that recommendations address the issues
        recommendation_text = ' '.join(recommendations).lower()
        assert 'relevance' in recommendation_text
        assert 'coherence' in recommendation_text
        assert 'integration' in recommendation_text


class TestConversationEvaluationReport:
    """Test ConversationEvaluationReport class"""
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        from essay_agent.eval.conversation import ConversationEvaluationReport, ConversationQualityMetrics
        
        quality_metrics = ConversationQualityMetrics(
            relevance_score=0.8,
            helpfulness_score=0.9,
            coherence_score=0.7,
            overall_quality=0.8,
            turn_count=5
        )
        
        report = ConversationEvaluationReport(
            quality_metrics=quality_metrics,
            intent_recognition_accuracy=0.95,
            context_tracking_success=0.9,
            integration_test_results={'basic_workflow': True},
            overall_score=0.85,
            recommendations=['Test recommendation'],
            execution_time=10.5,
            test_timestamp='2024-01-01 12:00:00'
        )
        
        report_dict = report.to_dict()
        
        assert 'quality_metrics' in report_dict
        assert 'intent_recognition_accuracy' in report_dict
        assert 'context_tracking_success' in report_dict
        assert 'integration_test_results' in report_dict
        assert 'overall_score' in report_dict
        assert 'recommendations' in report_dict
        assert 'execution_time' in report_dict
        assert 'test_timestamp' in report_dict
        
        assert report_dict['intent_recognition_accuracy'] == 0.95
        assert report_dict['context_tracking_success'] == 0.9
        assert report_dict['overall_score'] == 0.85
    
    def test_save_to_file(self, tmp_path):
        """Test saving report to file"""
        from essay_agent.eval.conversation import ConversationEvaluationReport, ConversationQualityMetrics
        
        quality_metrics = ConversationQualityMetrics(
            relevance_score=0.8,
            helpfulness_score=0.9,
            coherence_score=0.7,
            overall_quality=0.8,
            turn_count=5
        )
        
        report = ConversationEvaluationReport(
            quality_metrics=quality_metrics,
            intent_recognition_accuracy=0.95,
            context_tracking_success=0.9,
            integration_test_results={'basic_workflow': True},
            overall_score=0.85,
            recommendations=['Test recommendation'],
            execution_time=10.5,
            test_timestamp='2024-01-01 12:00:00'
        )
        
        # Save to file
        filepath = tmp_path / "test_report.json"
        report.save_to_file(str(filepath))
        
        # Verify file exists and contains correct data
        assert filepath.exists()
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data['intent_recognition_accuracy'] == 0.95
        assert data['context_tracking_success'] == 0.9
        assert data['overall_score'] == 0.85 