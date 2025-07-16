"""Test suite for TASK-004: Agent Prompt Templates.

This module tests all prompt-related functionality including:
- Enhanced prompt templates
- Dynamic prompt building  
- Context injection
- Performance optimization
- Prompt variant management
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the components we're testing
from essay_agent.agent.prompts import (
    ADVANCED_REASONING_PROMPT,
    ENHANCED_CONVERSATION_PROMPT, 
    TOOL_SPECIFIC_PROMPTS,
    ERROR_RECOVERY_STRATEGIES,
    PERFORMANCE_OPTIMIZED_PROMPTS,
    format_context_for_reasoning,
    format_tool_descriptions,
    format_tool_result,
    select_reasoning_template,
    inject_memory_context,
    get_performance_context
)

from essay_agent.agent.prompt_builder import (
    PromptBuilder,
    ContextInjector
)

from essay_agent.agent.prompt_optimizer import (
    PromptOptimizer,
    PromptVariantManager,
    PromptPerformanceMetrics,
    PromptVariant
)


class TestPromptTemplates:
    """Test the enhanced prompt templates and their structure."""
    
    def test_advanced_reasoning_prompt_structure(self):
        """Test that the advanced reasoning prompt has all required placeholders."""
        required_placeholders = [
            'conversation_context',
            'memory_context', 
            'user_state',
            'tool_descriptions',
            'performance_context',
            'user_input'
        ]
        
        for placeholder in required_placeholders:
            assert f'{{{placeholder}}}' in ADVANCED_REASONING_PROMPT, \
                f"Missing placeholder: {placeholder}"
    
    def test_enhanced_conversation_prompt_structure(self):
        """Test that the enhanced conversation prompt has required placeholders."""
        required_placeholders = [
            'conversation_context',
            'memory_context',
            'user_profile',
            'user_input'
        ]
        
        for placeholder in required_placeholders:
            assert f'{{{placeholder}}}' in ENHANCED_CONVERSATION_PROMPT, \
                f"Missing placeholder: {placeholder}"
    
    def test_tool_specific_prompts_coverage(self):
        """Test that tool-specific prompts cover key essay workflow tools."""
        expected_tools = ['brainstorm', 'outline', 'draft', 'revise', 'polish']
        
        for tool in expected_tools:
            assert tool in TOOL_SPECIFIC_PROMPTS, \
                f"Missing tool-specific prompt for: {tool}"
            assert len(TOOL_SPECIFIC_PROMPTS[tool]) > 50, \
                f"Tool prompt for {tool} is too short"
    
    def test_error_recovery_strategies_coverage(self):
        """Test that error recovery strategies cover common error types."""
        expected_strategies = ['tool_failure', 'unclear_intent', 'context_missing']
        
        for strategy in expected_strategies:
            assert strategy in ERROR_RECOVERY_STRATEGIES, \
                f"Missing error recovery strategy: {strategy}"
    
    def test_performance_optimized_prompts_variants(self):
        """Test that performance-optimized prompts include different variants."""
        expected_variants = [
            'high_confidence_reasoning',
            'exploratory_reasoning', 
            'support_focused'
        ]
        
        for variant in expected_variants:
            assert variant in PERFORMANCE_OPTIMIZED_PROMPTS, \
                f"Missing performance variant: {variant}"


class TestContextFormatting:
    """Test context formatting functions."""
    
    def test_format_context_for_reasoning_empty(self):
        """Test formatting with empty context."""
        result = format_context_for_reasoning({})
        assert result == "No context available."
    
    def test_format_context_for_reasoning_full(self):
        """Test formatting with full context data."""
        context = {
            'conversation_history': [
                {'user': 'Hello', 'agent': 'Hi there!'},
                {'user': 'Help me brainstorm', 'agent': 'Sure, let me help.'}
            ],
            'essay_state': {
                'phase': 'brainstorming',
                'progress': '25%',
                'current_draft': 'This is my draft with many words here.'
            },
            'user_profile': {
                'writing_style': 'conversational',
                'experience_level': 'intermediate',
                'values': ['creativity', 'authenticity', 'growth']
            },
            'relevant_memories': [
                {'summary': 'Previous essay about challenges'},
                {'summary': 'Story about leadership experience'}
            ]
        }
        
        result = format_context_for_reasoning(context)
        
        # Check that all major sections are included
        assert "RECENT CONVERSATION:" in result
        assert "ESSAY STATE:" in result
        assert "USER PROFILE:" in result
        assert "RELEVANT MEMORIES:" in result
        assert "brainstorming" in result
        assert "intermediate" in result
    
    def test_format_tool_descriptions_empty(self):
        """Test formatting with no tools."""
        result = format_tool_descriptions({})
        assert result == "No tools available."
    
    def test_format_tool_descriptions_full(self):
        """Test formatting with tool descriptions."""
        mock_tool_desc = Mock()
        mock_tool_desc.category = 'core_workflow'
        mock_tool_desc.description = 'Generate story ideas'
        mock_tool_desc.when_to_use = 'When user needs brainstorming'
        mock_tool_desc.input_requirements = ['essay_prompt', 'user_profile']
        mock_tool_desc.confidence_threshold = 0.8
        
        tools = {'brainstorm': mock_tool_desc}
        result = format_tool_descriptions(tools)
        
        assert "CORE WORKFLOW TOOLS:" in result
        assert "brainstorm:" in result
        assert "Generate story ideas" in result
        assert "Use when:" in result
        assert "Needs:" in result
        assert "Confidence needed: 0.8" in result
    
    def test_format_tool_result_brainstorm(self):
        """Test formatting brainstorm tool results."""
        result_data = {
            'stories': [
                {
                    'title': 'Overcoming Stage Fright',
                    'description': 'A story about conquering fear of public speaking during debate team.',
                    'prompt_fit': '9/10'
                },
                {
                    'title': 'Learning from Failure',
                    'description': 'How a failed science project taught me persistence.',
                    'prompt_fit': '8/10'
                }
            ]
        }
        
        result = format_tool_result('brainstorm', result_data)
        
        assert "Generated 2 story ideas:" in result
        assert "Overcoming Stage Fright" in result
        assert "Prompt fit: 9/10" in result
    
    def test_format_tool_result_outline(self):
        """Test formatting outline tool results."""
        result_data = {
            'outline': {
                'hook': 'I never thought I could speak in front of hundreds of people.',
                'context': 'As a shy freshman, joining debate team was terrifying.',
                'conflict': 'My first tournament was a disaster.',
                'growth': 'I practiced daily and found my voice.',
                'reflection': 'Now I know fear is just excitement in disguise.'
            },
            'estimated_word_count': 650
        }
        
        result = format_tool_result('outline', result_data)
        
        assert "Created essay outline:" in result
        assert "Hook:" in result
        assert "Estimated length: 650 words" in result
    
    def test_format_tool_result_generic(self):
        """Test formatting generic tool results."""
        result = format_tool_result('unknown_tool', {'message': 'Tool completed successfully'})
        assert "Tool 'unknown_tool' says: Tool completed successfully" in result
    
    def test_format_tool_result_none(self):
        """Test formatting when tool returns None."""
        result = format_tool_result('test_tool', None)
        assert "Tool 'test_tool' completed but returned no result." in result


class TestTemplateSelection:
    """Test template selection logic."""
    
    def test_select_reasoning_template_tool_selection(self):
        """Test template selection for tool selection tasks."""
        context = {
            'user_profile': {'experience_level': 'beginner'},
            'conversation_history': [],
            'recent_errors': False
        }
        
        template = select_reasoning_template('tool_selection', context)
        # Should return support-focused for beginners
        assert template == PERFORMANCE_OPTIMIZED_PROMPTS['support_focused']
    
    def test_select_reasoning_template_long_conversation(self):
        """Test template selection for long conversations."""
        context = {
            'user_profile': {'experience_level': 'advanced'},
            'conversation_history': [{}] * 15,  # Long conversation
            'recent_errors': False
        }
        
        template = select_reasoning_template('tool_selection', context)
        # Should return high-confidence for long conversations
        assert template == PERFORMANCE_OPTIMIZED_PROMPTS['high_confidence_reasoning']
    
    def test_select_reasoning_template_conversation(self):
        """Test template selection for conversation tasks."""
        template = select_reasoning_template('conversation', {})
        assert template == ENHANCED_CONVERSATION_PROMPT
    
    def test_select_reasoning_template_error_recovery(self):
        """Test template selection for error recovery."""
        template = select_reasoning_template('error_recovery', {})
        assert template in ERROR_RECOVERY_STRATEGIES.values()


class TestMemoryContextInjection:
    """Test memory context injection functionality."""
    
    def test_inject_memory_context_full(self):
        """Test injecting complete memory context."""
        template = "Memory context: {memory_context}"
        memory_data = {
            'reasoning_chains': [
                {'summary': 'Previous brainstorming decision'},
                {'summary': 'Outline generation reasoning'}
            ],
            'tool_executions': [
                {'success': True, 'tool': 'brainstorm'},
                {'success': True, 'tool': 'outline'},
                {'success': False, 'tool': 'draft'}
            ],
            'usage_patterns': [
                {'description': 'User prefers detailed outlines'},
                {'description': 'Strong revision cycle pattern'}
            ]
        }
        
        result = inject_memory_context(template, memory_data)
        
        assert "RECENT REASONING PATTERNS:" in result
        assert "USAGE PATTERNS:" in result
        assert "PERFORMANCE:" in result
        assert "67% success rate" in result  # 2/3 successes
    
    def test_inject_memory_context_empty(self):
        """Test injecting empty memory context."""
        template = "Memory: {memory_context}"
        result = inject_memory_context(template, {})
        assert "No memory context available." in result
    
    def test_get_performance_context_full(self):
        """Test getting performance context."""
        performance_data = {
            'successful_patterns': ['brainstorm->outline->draft', 'quick_iteration'],
            'recent_metrics': {
                'success_rate': 0.85,
                'avg_response_time': 2.3
            },
            'preferred_tools': ['brainstorm', 'revise', 'polish']
        }
        
        result = get_performance_context(performance_data)
        
        assert "SUCCESSFUL PATTERNS:" in result
        assert "RECENT PERFORMANCE:" in result
        assert "Success rate: 85.0%" in result
        assert "Avg response time: 2.3s" in result
        assert "PREFERRED TOOLS: brainstorm, revise, polish" in result
    
    def test_get_performance_context_empty(self):
        """Test getting performance context with no data."""
        result = get_performance_context({})
        assert result == "No performance data available."


class TestPromptBuilder:
    """Test the PromptBuilder class."""
    
    @pytest.fixture
    def mock_memory(self):
        """Create a mock memory object."""
        memory = Mock()
        memory.get_conversation_history = Mock(return_value=[
            {'user': 'Hello', 'agent': 'Hi!'}
        ])
        memory.get_recent_memories = Mock(return_value=[
            {'summary': 'Previous essay work'}
        ])
        memory.get_performance_metrics = Mock(return_value={
            'success_rate': 0.8,
            'preferred_tools': ['brainstorm']
        })
        return memory
    
    @pytest.fixture
    def mock_tool_registry(self):
        """Create a mock tool registry."""
        mock_tool = Mock()
        mock_tool.category = 'test'
        mock_tool.description = 'Test tool'
        mock_tool.when_to_use = 'For testing'
        mock_tool.input_requirements = ['input']
        mock_tool.confidence_threshold = 0.7
        
        return {'test_tool': mock_tool}
    
    @pytest.fixture
    def prompt_builder(self, mock_memory, mock_tool_registry):
        """Create a PromptBuilder instance with mocks."""
        return PromptBuilder(mock_memory, mock_tool_registry)
    
    @pytest.mark.asyncio
    async def test_build_reasoning_prompt_basic(self, prompt_builder):
        """Test building a basic reasoning prompt."""
        user_input = "Help me brainstorm ideas"
        context = {
            'user_profile': {'experience_level': 'intermediate'},
            'conversation_history': [],
            'essay_state': {'phase': 'brainstorming'}
        }
        
        prompt = await prompt_builder.build_reasoning_prompt(user_input, context)
        
        assert len(prompt) > 100
        assert user_input in prompt
        assert "brainstorming" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_build_tool_prompt(self, prompt_builder):
        """Test building a tool-specific prompt."""
        context = {
            'user_profile': {'name': 'Test User'},
            'memory_summary': 'Previous work on essays'
        }
        
        prompt = await prompt_builder.build_tool_prompt('brainstorm', context, {'prompt': 'test'})
        
        assert 'brainstorm' in prompt.lower()
        assert 'test user' in prompt.lower() or 'Test User' in prompt
    
    @pytest.mark.asyncio
    async def test_build_error_recovery_prompt(self, prompt_builder):
        """Test building an error recovery prompt."""
        error_context = {
            'tool_name': 'brainstorm',
            'error': 'Connection timeout',
            'context': {'user_id': 'test_user'}
        }
        
        prompt = await prompt_builder.build_error_recovery_prompt(error_context)
        
        assert 'brainstorm' in prompt
        assert 'timeout' in prompt.lower()
    
    def test_optimize_for_tokens_no_truncation_needed(self, prompt_builder):
        """Test token optimization when no truncation is needed."""
        short_prompt = "This is a short prompt."
        result = prompt_builder.optimize_for_tokens(short_prompt)
        assert result == short_prompt
    
    def test_optimize_for_tokens_truncation_needed(self, prompt_builder):
        """Test token optimization when truncation is needed."""
        # Create a very long prompt
        long_prompt = "This is a very long prompt. " * 1000
        result = prompt_builder.optimize_for_tokens(long_prompt, 'default')
        
        assert len(result) < len(long_prompt)
        assert "content truncated" in result.lower()
    
    def test_determine_task_type(self, prompt_builder):
        """Test task type determination."""
        assert prompt_builder._determine_task_type("help me brainstorm", {}) == 'brainstorming'
        assert prompt_builder._determine_task_type("create an outline", {}) == 'outlining'
        assert prompt_builder._determine_task_type("write my essay", {}) == 'drafting'
        assert prompt_builder._determine_task_type("revise this paragraph", {}) == 'revision'
        assert prompt_builder._determine_task_type("polish my final draft", {}) == 'polishing'
        assert prompt_builder._determine_task_type("what do you think?", {}) == 'conversation'


class TestContextInjector:
    """Test the ContextInjector class."""
    
    @pytest.fixture
    def context_injector(self):
        """Create a ContextInjector instance."""
        return ContextInjector()
    
    def test_format_conversation_context_empty(self, context_injector):
        """Test formatting empty conversation history."""
        result = context_injector.format_conversation_context([])
        assert result == "No conversation history available."
    
    def test_format_conversation_context_full(self, context_injector):
        """Test formatting full conversation history."""
        history = [
            {'user': 'Hello', 'agent': 'Hi there!'},
            {'user': 'Help me write', 'agent': 'I can help with that.'},
            {'user': 'Generate ideas', 'agent': 'Let me brainstorm for you.'}
        ]
        
        result = context_injector.format_conversation_context(history)
        
        assert "RECENT CONVERSATION:" in result
        assert "1. User: Hello" in result
        assert "Agent: Hi there!" in result
        assert len(result.split('\n')) >= 6  # Multiple exchanges
    
    def test_format_memory_context_empty(self, context_injector):
        """Test formatting empty memory context."""
        result = context_injector.format_memory_context({})
        assert result == "No memory context available."
    
    def test_format_memory_context_full(self, context_injector):
        """Test formatting full memory context."""
        memories = {
            'recent_stories': [
                {'title': 'Overcoming challenges'},
                {'title': 'Leadership experience'}
            ],
            'writing_patterns': [
                'Prefers detailed outlines',
                'Strong revision cycles'
            ],
            'user_preferences': {
                'style': 'conversational',
                'length': 'medium'
            }
        }
        
        result = context_injector.format_memory_context(memories)
        
        assert "RECENT STORIES:" in result
        assert "WRITING PATTERNS:" in result
        assert "USER PREFERENCES:" in result
        assert "Overcoming challenges" in result
    
    def test_format_tool_context(self, context_injector):
        """Test formatting tool context."""
        tools = [
            {
                'name': 'brainstorm',
                'description': 'Generate story ideas',
                'confidence_threshold': 0.8
            },
            {
                'name': 'outline',
                'description': 'Create essay structure',
                'confidence_threshold': 0.7
            }
        ]
        
        result = context_injector.format_tool_context(tools)
        
        assert "AVAILABLE TOOLS:" in result
        assert "brainstorm:" in result
        assert "Generate story ideas" in result
        assert "confidence: 0.8" in result
    
    def test_inject_all_context_success(self, context_injector):
        """Test injecting all context successfully."""
        template = "Context: {conversation_context}, Memory: {memory_context}, User: {user_state}"
        context = {
            'conversation_history': [{'user': 'hi', 'agent': 'hello'}],
            'memory_data': {'recent_stories': [{'title': 'test'}]},
            'user_state': 'writing'
        }
        
        result = context_injector.inject_all_context(template, context)
        
        assert "RECENT CONVERSATION:" in result
        assert "RECENT STORIES:" in result
        assert "writing" in result
    
    def test_inject_all_context_error_handling(self, context_injector):
        """Test error handling in context injection."""
        template = "Bad template with {nonexistent_placeholder}"
        context = {}
        
        result = context_injector.inject_all_context(template, context)
        
        # Should not crash and should contain error message
        assert "injection failed" in result.lower() or "unavailable" in result.lower()


class TestPromptPerformanceMetrics:
    """Test the PromptPerformanceMetrics class."""
    
    def test_performance_metrics_creation(self):
        """Test creating performance metrics."""
        metrics = PromptPerformanceMetrics("test_prompt")
        
        assert metrics.prompt_id == "test_prompt"
        assert metrics.total_uses == 0
        assert metrics.successful_uses == 0
        assert metrics.success_rate == 0.0
        assert metrics.performance_score >= 0.0
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = PromptPerformanceMetrics("test")
        metrics.total_uses = 10
        metrics.successful_uses = 7
        
        assert metrics.success_rate == 0.7
    
    def test_performance_score_calculation(self):
        """Test overall performance score calculation."""
        metrics = PromptPerformanceMetrics("test")
        metrics.total_uses = 10
        metrics.successful_uses = 8
        metrics.average_response_time = 2.0
        metrics.average_confidence = 0.9
        metrics.user_satisfaction_scores = [4.0, 4.5, 4.2]
        
        score = metrics.performance_score
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be decent with good metrics


class TestPromptOptimizer:
    """Test the PromptOptimizer class."""
    
    @pytest.fixture
    def prompt_optimizer(self):
        """Create a PromptOptimizer instance."""
        return PromptOptimizer(memory=None)  # No memory for testing
    
    @pytest.mark.asyncio
    async def test_select_optimal_prompt_basic(self, prompt_optimizer):
        """Test basic prompt selection."""
        context = {'user_profile': {'experience_level': 'intermediate'}}
        
        prompt_id, confidence = await prompt_optimizer.select_optimal_prompt(
            'reasoning', context, ['prompt1', 'prompt2']
        )
        
        assert prompt_id in ['prompt1', 'prompt2']
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_select_optimal_prompt_no_candidates(self, prompt_optimizer):
        """Test prompt selection with no candidates."""
        result = await prompt_optimizer.select_optimal_prompt('reasoning', {}, [])
        
        assert result[0] == "default_reasoning"
        assert result[1] == 0.5
    
    def test_update_performance_metrics_new_prompt(self, prompt_optimizer):
        """Test updating metrics for a new prompt."""
        prompt_id = "test_prompt"
        
        prompt_optimizer.update_performance_metrics(
            prompt_id, success=True, execution_time=1.5, confidence=0.8
        )
        
        assert prompt_id in prompt_optimizer.performance_metrics
        metrics = prompt_optimizer.performance_metrics[prompt_id]
        assert metrics.total_uses == 1
        assert metrics.successful_uses == 1
        assert metrics.average_response_time == 1.5
        assert metrics.average_confidence == 0.8
    
    def test_update_performance_metrics_existing_prompt(self, prompt_optimizer):
        """Test updating metrics for an existing prompt."""
        prompt_id = "test_prompt"
        
        # First update
        prompt_optimizer.update_performance_metrics(
            prompt_id, success=True, execution_time=2.0, confidence=0.7
        )
        
        # Second update
        prompt_optimizer.update_performance_metrics(
            prompt_id, success=False, execution_time=1.0, confidence=0.6
        )
        
        metrics = prompt_optimizer.performance_metrics[prompt_id]
        assert metrics.total_uses == 2
        assert metrics.successful_uses == 1
        assert metrics.success_rate == 0.5
        assert metrics.average_response_time < 2.0  # Should be moving average
    
    @pytest.mark.asyncio
    async def test_analyze_prompt_performance_no_data(self, prompt_optimizer):
        """Test analyzing performance for unknown prompt."""
        result = await prompt_optimizer.analyze_prompt_performance("unknown_prompt")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_analyze_prompt_performance_with_data(self, prompt_optimizer):
        """Test analyzing performance for known prompt."""
        prompt_id = "test_prompt"
        
        # Add some performance data
        prompt_optimizer.update_performance_metrics(
            prompt_id, success=True, execution_time=1.0, confidence=0.8
        )
        
        result = await prompt_optimizer.analyze_prompt_performance(prompt_id)
        
        assert "prompt_id" in result
        assert "overall_performance" in result
        assert result["prompt_id"] == prompt_id
    
    def test_get_performance_recommendations(self, prompt_optimizer):
        """Test getting performance recommendations."""
        # Add some test data
        prompt_optimizer.update_performance_metrics(
            "good_prompt", success=True, execution_time=1.0, confidence=0.9
        )
        prompt_optimizer.update_performance_metrics(
            "bad_prompt", success=False, execution_time=5.0, confidence=0.3
        )
        
        recommendations = prompt_optimizer.get_performance_recommendations()
        
        assert "timestamp" in recommendations
        assert "overall_health" in recommendations
        assert "underperforming_prompts" in recommendations
    
    def test_get_context_signature(self, prompt_optimizer):
        """Test context signature generation."""
        context = {
            'user_experience': 'beginner',
            'essay_phase': 'brainstorming',
            'conversation_length': 8,
            'has_errors': True,
            'user_mood': 'frustrated'
        }
        
        signature = prompt_optimizer._get_context_signature(context)
        
        assert 'exp:beginner' in signature
        assert 'phase:brainstorming' in signature
        assert 'conv:1' in signature  # 8//5 = 1
        assert 'errors:true' in signature
        assert 'mood:frustrated' in signature


class TestPromptVariantManager:
    """Test the PromptVariantManager class."""
    
    @pytest.fixture
    def variant_manager(self):
        """Create a PromptVariantManager instance."""
        optimizer = PromptOptimizer(memory=None)
        return PromptVariantManager(optimizer)
    
    def test_register_variant(self, variant_manager):
        """Test registering a new variant."""
        variant_id = variant_manager.register_variant(
            "base_prompt",
            "Enhanced template with {context}",
            "Test variant with better context"
        )
        
        assert variant_id.startswith("base_prompt_variant_")
        assert variant_id in variant_manager.variants
        assert variant_manager.variants[variant_id].description == "Test variant with better context"
        assert "base_prompt" in variant_manager.base_prompts
        assert variant_id in variant_manager.base_prompts["base_prompt"]
    
    def test_register_variant_custom_id(self, variant_manager):
        """Test registering a variant with custom ID."""
        custom_id = "custom_variant_123"
        result_id = variant_manager.register_variant(
            "base_prompt",
            "Template",
            "Description",
            custom_id
        )
        
        assert result_id == custom_id
        assert custom_id in variant_manager.variants
    
    @pytest.mark.asyncio
    async def test_a_b_test_variants_no_variants(self, variant_manager):
        """Test A/B testing with no variants."""
        result = await variant_manager.a_b_test_variants("nonexistent_prompt", {})
        assert result == "nonexistent_prompt"
    
    @pytest.mark.asyncio
    async def test_a_b_test_variants_with_variants(self, variant_manager):
        """Test A/B testing with active variants."""
        # Register some variants
        variant1 = variant_manager.register_variant("base", "template1", "desc1")
        variant2 = variant_manager.register_variant("base", "template2", "desc2")
        
        # Run A/B test
        result = await variant_manager.a_b_test_variants("base", {"test": "context"})
        
        # Should return one of the variants or base prompt
        assert result in [variant1, variant2, "base"]
    
    def test_get_winning_variant_no_data(self, variant_manager):
        """Test getting winning variant with no performance data."""
        result = variant_manager.get_winning_variant("unknown_prompt")
        assert result is None
    
    def test_get_winning_variant_with_data(self, variant_manager):
        """Test getting winning variant with performance data."""
        # Register variants
        variant1 = variant_manager.register_variant("base", "template1", "desc1")
        variant2 = variant_manager.register_variant("base", "template2", "desc2")
        
        # Add performance data
        optimizer = variant_manager.optimizer
        
        # Make variant1 perform better
        for _ in range(10):
            optimizer.update_performance_metrics(variant1, True, 1.0, 0.9)
        
        for _ in range(10):
            optimizer.update_performance_metrics(variant2, False, 2.0, 0.5)
        
        # Add base performance
        for _ in range(10):
            optimizer.update_performance_metrics("base", True, 1.5, 0.7)
        
        winner = variant_manager.get_winning_variant("base")
        assert winner == variant1  # Should be the best performer
    
    def test_archive_underperforming_variants(self, variant_manager):
        """Test archiving underperforming variants."""
        # Register a variant
        variant_id = variant_manager.register_variant("base", "template", "desc")
        
        # Make it underperform
        optimizer = variant_manager.optimizer
        for _ in range(15):  # Enough data points
            optimizer.update_performance_metrics(variant_id, False, 5.0, 0.2)
        
        # Archive underperforming variants
        variant_manager.archive_underperforming_variants(threshold=0.6)
        
        # Variant should be archived (inactive)
        assert not variant_manager.variants[variant_id].is_active
    
    def test_get_variant_analysis(self, variant_manager):
        """Test getting variant analysis."""
        # Register some variants
        variant1 = variant_manager.register_variant("base", "template1", "desc1")
        variant2 = variant_manager.register_variant("base", "template2", "desc2")
        
        # Add some performance data
        optimizer = variant_manager.optimizer
        optimizer.update_performance_metrics(variant1, True, 1.0, 0.8)
        optimizer.update_performance_metrics(variant2, False, 2.0, 0.6)
        
        analysis = variant_manager.get_variant_analysis("base")
        
        assert analysis["base_prompt"] == "base"
        assert analysis["total_variants"] == 2
        assert analysis["active_variants"] == 2
        assert len(analysis["variants"]) == 2
        
        # Check that variants are sorted by performance
        first_variant = analysis["variants"][0]
        assert first_variant["variant_id"] == variant1  # Better performer should be first


@pytest.mark.integration
class TestPromptSystemIntegration:
    """Integration tests for the complete prompt system."""
    
    @pytest.fixture
    def full_prompt_system(self):
        """Set up a complete prompt system for integration testing."""
        mock_memory = Mock()
        mock_memory.get_conversation_history = Mock(return_value=[])
        mock_memory.get_recent_memories = Mock(return_value=[])
        mock_memory.get_performance_metrics = Mock(return_value={})
        
        builder = PromptBuilder(mock_memory, {})
        optimizer = PromptOptimizer(mock_memory)
        variant_manager = PromptVariantManager(optimizer)
        
        return {
            'builder': builder,
            'optimizer': optimizer,
            'variant_manager': variant_manager,
            'memory': mock_memory
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_prompt_optimization(self, full_prompt_system):
        """Test complete end-to-end prompt optimization workflow."""
        builder = full_prompt_system['builder']
        optimizer = full_prompt_system['optimizer']
        variant_manager = full_prompt_system['variant_manager']
        
        # 1. Build initial prompt
        context = {'user_profile': {'experience_level': 'intermediate'}}
        prompt = await builder.build_reasoning_prompt("Help me brainstorm", context)
        assert len(prompt) > 100
        
        # 2. Simulate usage and performance tracking
        optimizer.update_performance_metrics("base_reasoning", True, 2.0, 0.8)
        optimizer.update_performance_metrics("base_reasoning", True, 1.5, 0.9)
        optimizer.update_performance_metrics("base_reasoning", False, 3.0, 0.6)
        
        # 3. Register and test variants
        variant_id = variant_manager.register_variant(
            "base_reasoning",
            "Improved reasoning template",
            "Enhanced with better context"
        )
        
        # 4. A/B test variants
        selected = await variant_manager.a_b_test_variants("base_reasoning", context)
        assert selected in ["base_reasoning", variant_id]
        
        # 5. Get optimization recommendations
        recommendations = optimizer.get_performance_recommendations()
        assert "overall_health" in recommendations
        
        # 6. Analyze performance
        analysis = await optimizer.analyze_prompt_performance("base_reasoning")
        assert "overall_performance" in analysis
    
    @pytest.mark.asyncio 
    async def test_prompt_system_error_resilience(self, full_prompt_system):
        """Test that the prompt system handles errors gracefully."""
        builder = full_prompt_system['builder']
        optimizer = full_prompt_system['optimizer']
        
        # Test with malformed context
        malformed_context = {'bad_key': object()}  # Non-serializable object
        
        # Should not crash
        prompt = await builder.build_reasoning_prompt("test", malformed_context)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        
        # Test with None values
        optimizer.update_performance_metrics("test", None, None, None)
        
        # Should handle gracefully
        metrics = optimizer.performance_metrics.get("test")
        assert metrics is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 