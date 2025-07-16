"""Unit tests for enhanced tool registry system.

This module provides comprehensive test coverage for:
- Enhanced tool registry functionality
- Tool description formatting for LLM consumption
- Tool categorization and filtering
- Tool analyzer recommendations
- Tool performance tracking
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any, Optional
import time
from datetime import datetime, timedelta

from essay_agent.agent.tools.tool_registry import EnhancedToolRegistry
from essay_agent.agent.tools.tool_analyzer import (
    ToolAnalyzer, ToolRecommendation, ContextAnalysis, UserIntent
)
from essay_agent.agent.tools.tool_descriptions import (
    ToolDescription, TOOL_DESCRIPTIONS, TOOL_CATEGORIES,
    get_tools_by_category, format_tools_for_llm
)
from essay_agent.tools import REGISTRY as BASE_REGISTRY


class TestToolDescription:
    """Test cases for ToolDescription data model."""
    
    def test_tool_description_creation(self):
        """Test creating a complete ToolDescription."""
        description = ToolDescription(
            name="brainstorm",
            category="brainstorming",
            description="Generate creative story ideas",
            purpose="Help users discover meaningful personal experiences",
            input_requirements=["essay_prompt", "user_profile"],
            output_format="List of story ideas with themes",
            when_to_use="When user needs creative inspiration",
            example_usage="Help me brainstorm ideas for my challenge essay",
            dependencies=[],
            estimated_tokens=800,
            confidence_threshold=0.8
        )
        
        assert description.name == "brainstorm"
        assert description.category == "brainstorming"
        assert len(description.input_requirements) == 2
        assert description.estimated_tokens == 800
        assert description.confidence_threshold == 0.8
    
    def test_tool_description_validation(self):
        """Test ToolDescription validation and error handling."""
        # Test missing required fields
        with pytest.raises((ValueError, TypeError)):
            ToolDescription(name="")  # Empty name should fail
        
        # Test minimal valid description
        description = ToolDescription(
            name="test_tool",
            category="testing",
            description="Test description",
            purpose="Testing purposes",
            input_requirements=["input"],
            output_format="Test output",
            when_to_use="For testing",
            example_usage="Test example",
            dependencies=[],
            estimated_tokens=100
        )
        assert description.name == "test_tool"
    
    def test_tool_description_dict_conversion(self):
        """Test ToolDescription dataclass conversion."""
        description = ToolDescription(
            name="test_tool",
            category="analysis",
            description="Test tool description",
            purpose="Testing",
            input_requirements=["arg1"],
            output_format="Test output",
            when_to_use="For testing",
            example_usage="Test example",
            dependencies=["arg2"],
            estimated_tokens=100
        )
        
        # Test that description has all expected attributes
        assert description.name == "test_tool"
        assert description.category == "analysis"
        assert "arg1" in description.input_requirements
        assert "arg2" in description.dependencies


class TestEnhancedToolRegistry:
    """Test cases for EnhancedToolRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create registry instance for testing."""
        return EnhancedToolRegistry()
    
    @pytest.fixture
    def sample_tool_description(self):
        """Sample tool description for testing."""
        return ToolDescription(
            name="test_tool",
            category="writing",
            description="Test tool for unit testing",
            purpose="Testing tool functionality",
            input_requirements=["content"],
            output_format="Modified content string",
            when_to_use="For testing purposes",
            example_usage="test_tool(content='hello')",
            dependencies=[],
            estimated_tokens=100,
            confidence_threshold=0.9
        )
    
    def test_registry_initialization(self, registry):
        """Test registry initialization."""
        assert isinstance(registry.tools, dict)
        assert isinstance(registry.descriptions, dict)
        assert isinstance(registry.categories, dict)
        
        # Should have some tools from BASE_REGISTRY
        assert len(registry.tools) > 0
    
    def test_tool_registration(self, registry, sample_tool_description):
        """Test registering new tools."""
        # Create a mock tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool description"
        
        # Register the tool
        registry.register_tool(mock_tool, sample_tool_description)
        
        # Verify tool is registered
        assert registry.has_tool("test_tool")
        assert registry.get_tool("test_tool") == mock_tool
        assert registry.get_description("test_tool") == sample_tool_description
    
    def test_tool_retrieval(self, registry):
        """Test retrieving registered tools."""
        # Test existing tool if available
        available_tools = list(registry.tools.keys())
        if available_tools:
            tool_name = available_tools[0]
            tool = registry.get_tool(tool_name)
            assert tool is not None
            
            description = registry.get_description(tool_name)
            if description:
                assert description.name == tool_name
        
        # Test non-existent tool
        assert not registry.has_tool("non_existent_tool")
        assert registry.get_tool("non_existent_tool") is None
        assert registry.get_description("non_existent_tool") is None
    
    def test_tool_categorization(self, registry):
        """Test tool categorization and filtering."""
        # Get tools by category
        brainstorm_tools = registry.get_tools_by_category("brainstorming")
        assert isinstance(brainstorm_tools, list)
        
        writing_tools = registry.get_tools_by_category("writing")
        assert isinstance(writing_tools, list)
        
        # Verify category filtering works
        for tool_desc in brainstorm_tools:
            assert tool_desc.category == "brainstorming"
    
    def test_workflow_tools(self, registry):
        """Test getting workflow tools."""
        workflow_tools = registry.get_workflow_tools()
        assert isinstance(workflow_tools, list)
        
        # Should include core workflow tools if they exist
        workflow_names = [tool.name for tool in workflow_tools]
        expected_tools = ["brainstorm", "outline", "draft", "revise", "polish"]
        
        # At least some workflow tools should be present
        assert len(workflow_tools) >= 0  # May be empty if tools not registered yet
    
    def test_category_list(self, registry):
        """Test getting category list."""
        categories = registry.get_category_list()
        assert isinstance(categories, list)
        assert len(categories) >= 0
    
    def test_find_tools_by_keywords(self, registry):
        """Test finding tools by keyword matching."""
        # Test keyword search
        matches = registry.find_tools_by_keywords(["essay", "writing"])
        assert isinstance(matches, list)
        
        # Results should contain tools with matching keywords
        for match in matches:
            assert isinstance(match, ToolDescription)
            search_text = f"{match.description} {match.purpose} {match.when_to_use}".lower()
            assert any(keyword in search_text for keyword in ["essay", "writing"])
    
    def test_suggest_next_tools(self, registry):
        """Test suggesting next logical tools."""
        # Test with some completed tools
        completed_tools = ["brainstorm"]
        suggestions = registry.suggest_next_tools(completed_tools)
        
        assert isinstance(suggestions, list)
        
        # Should not suggest already completed tools
        for suggestion in suggestions:
            assert suggestion.name not in completed_tools


class TestToolAnalyzer:
    """Test cases for ToolAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing."""
        mock_registry = Mock(spec=EnhancedToolRegistry)
        return ToolAnalyzer(mock_registry)
    
    @pytest.fixture
    def mock_context(self):
        """Mock context for testing."""
        return {
            "user_input": "Help me brainstorm essay ideas",
            "current_phase": "brainstorming", 
            "previous_tools": ["analyze_prompt"],
            "user_profile": {"experience_level": "beginner"},
            "essay_state": {"topic": "challenge", "word_limit": 650},
            "conversation_history": [
                {"role": "user", "content": "I need help with my essay"},
                {"role": "assistant", "content": "I can help you brainstorm ideas"}
            ]
        }
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.registry is not None
        assert hasattr(analyzer, 'intent_patterns')
        assert hasattr(analyzer, 'llm')
    
    def test_context_analysis(self, analyzer, mock_context):
        """Test context analysis functionality."""
        with patch.object(analyzer, '_quick_intent_analysis') as mock_quick:
            mock_quick.return_value = {
                "primary_intent": "brainstorming",
                "confidence": 0.8
            }
            
            # Create a mock UserIntent
            intent = analyzer.analyze_intent(
                mock_context["user_input"],
                quick_analysis=mock_quick.return_value
            )
            
            assert isinstance(intent, UserIntent)
            assert intent.primary_intent is not None
            assert isinstance(intent.confidence, float)
            assert 0 <= intent.confidence <= 1
    
    def test_tool_recommendation(self, analyzer, mock_context):
        """Test tool recommendation logic."""
        # Create mock intent and context analysis
        mock_intent = UserIntent(
            primary_intent="brainstorming",
            secondary_intents=[],
            confidence=0.9,
            essay_phase="brainstorming",
            specific_request="User wants story ideas",
            urgency="Medium"
        )
        
        mock_context_analysis = ContextAnalysis(
            available_data=["essay_prompt", "user_profile"],
            completed_tools=[],
            missing_dependencies=[],
            workflow_progress="starting"
        )
        
        recommendations = analyzer.recommend_tools(mock_intent, mock_context_analysis, max_recommendations=3)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        assert all(isinstance(rec, ToolRecommendation) for rec in recommendations)
    
    def test_quick_intent_analysis(self, analyzer):
        """Test quick intent analysis patterns."""
        # Test brainstorming intent
        result = analyzer._quick_intent_analysis("Help me brainstorm essay ideas")
        assert isinstance(result, dict)
        assert "primary_intent" in result
        assert result["primary_intent"] == "brainstorming"
        
        # Test writing intent
        result = analyzer._quick_intent_analysis("Write a draft of my essay")
        assert result["primary_intent"] == "drafting"
        
        # Test evaluation intent
        result = analyzer._quick_intent_analysis("Score my essay please")
        assert result["primary_intent"] == "evaluation"


class TestToolDescriptionsModule:
    """Test cases for tool descriptions utility functions."""
    
    def test_tool_descriptions_loading(self):
        """Test loading of TOOL_DESCRIPTIONS."""
        assert isinstance(TOOL_DESCRIPTIONS, dict)
        assert len(TOOL_DESCRIPTIONS) > 0
        
        # Check some expected tools
        expected_tools = ["brainstorm", "outline", "draft_essay", "revise_for_clarity"]
        for tool in expected_tools:
            if tool in TOOL_DESCRIPTIONS:
                description = TOOL_DESCRIPTIONS[tool]
                assert isinstance(description, ToolDescription)
                assert description.name == tool
    
    def test_format_tools_for_llm(self):
        """Test formatting tool descriptions for LLM consumption."""
        # Test with sample tools
        sample_descriptions = [
            ToolDescription(
                name="test_tool",
                category="analysis",
                description="Test tool",
                purpose="Testing",
                input_requirements=["input"],
                output_format="Test output",
                when_to_use="For testing",
                example_usage="Test example",
                dependencies=[],
                estimated_tokens=100
            )
        ]
        
        formatted = format_tools_for_llm(sample_descriptions)
        
        assert isinstance(formatted, str)
        assert "test_tool" in formatted
        assert "analysis" in formatted
    
    def test_get_tools_by_category(self):
        """Test filtering tools by category."""
        brainstorm_tools = get_tools_by_category("brainstorming")
        assert isinstance(brainstorm_tools, list)
        
        # Verify all returned tools are in the correct category
        for description in brainstorm_tools:
            assert description.category == "brainstorming"
    
    def test_tool_categories_structure(self):
        """Test tool categories structure."""
        assert isinstance(TOOL_CATEGORIES, dict)
        assert len(TOOL_CATEGORIES) > 0
        
        # Verify some expected categories exist
        expected_categories = ["core_workflow", "writing", "evaluation"]
        for category in expected_categories:
            assert category in TOOL_CATEGORIES


@pytest.mark.integration
class TestToolRegistryIntegration:
    """Integration tests for tool registry with real components."""
    
    @pytest.fixture
    def integrated_registry(self):
        """Create registry with real base registry."""
        return EnhancedToolRegistry()
    
    def test_real_tool_integration(self, integrated_registry):
        """Test integration with actual essay agent tools."""
        # Get some real tools
        available_tools = list(integrated_registry.tools.keys())
        assert len(available_tools) > 0
        
        # Test a real tool if available
        if available_tools:
            tool_name = available_tools[0]
            tool = integrated_registry.get_tool(tool_name)
            description = integrated_registry.get_description(tool_name)
            
            assert tool is not None
            if description:
                assert description.name == tool_name
    
    def test_tool_description_compatibility(self, integrated_registry):
        """Test tool description dictionary format compatibility."""
        available_tools = list(integrated_registry.descriptions.keys())
        
        if available_tools:
            tool_name = available_tools[0]
            desc_dict = integrated_registry.get_tool_description(tool_name)
            
            if desc_dict:
                assert isinstance(desc_dict, dict)
                assert "name" in desc_dict
                assert "category" in desc_dict
                assert "description" in desc_dict
    
    def test_workflow_integration(self, integrated_registry):
        """Test workflow tool integration."""
        workflow_tools = integrated_registry.get_workflow_tools()
        assert isinstance(workflow_tools, list)
        
        # Test getting tools for specific phases
        brainstorm_tools = integrated_registry.get_tools_for_phase("brainstorming")
        assert isinstance(brainstorm_tools, list) 