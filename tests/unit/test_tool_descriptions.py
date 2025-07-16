"""Unit tests for tool descriptions system.

Tests cover ToolDescription data models, EnhancedToolRegistry functionality,
and ToolAnalyzer intent/recommendation logic.
"""
import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from essay_agent.agent.tools import (
    ToolDescription,
    TOOL_DESCRIPTIONS,
    TOOL_CATEGORIES,
    get_tool_description,
    get_tools_by_category,
    format_tools_for_llm,
    EnhancedToolRegistry,
    ToolAnalyzer,
    UserIntent,
    ToolRecommendation,
    ContextAnalysis,
    create_tool_analyzer
)


class TestToolDescription:
    """Test ToolDescription data model."""
    
    def test_tool_description_creation(self):
        """Test creating a ToolDescription with all fields."""
        desc = ToolDescription(
            name="test_tool",
            category="testing",
            description="A tool for testing",
            purpose="Test tool functionality",
            input_requirements=["test_input"],
            output_format="Test output",
            when_to_use="When testing",
            example_usage="Use test_tool for testing",
            dependencies=["dependency_tool"],
            estimated_tokens=100,
            confidence_threshold=0.8
        )
        
        assert desc.name == "test_tool"
        assert desc.category == "testing"
        assert desc.estimated_tokens == 100
        assert desc.confidence_threshold == 0.8
        assert "dependency_tool" in desc.dependencies
    
    def test_tool_description_defaults(self):
        """Test ToolDescription with default values."""
        desc = ToolDescription(
            name="minimal_tool",
            category="minimal",
            description="Minimal tool",
            purpose="Test",
            input_requirements=["input"],
            output_format="output",
            when_to_use="when needed",
            example_usage="use it",
            dependencies=[],
            estimated_tokens=50
        )
        
        assert desc.confidence_threshold == 0.7  # Default value


class TestToolDescriptionsCatalog:
    """Test the tool descriptions catalog."""
    
    def test_catalog_completeness(self):
        """Test that catalog has expected tools."""
        # Core workflow tools
        core_tools = ["brainstorm", "outline", "draft", "revise", "polish"]
        for tool in core_tools:
            assert tool in TOOL_DESCRIPTIONS
            
        # At least one tool from each category
        for category in TOOL_CATEGORIES:
            category_tools = TOOL_CATEGORIES[category]
            assert len(category_tools) > 0
            # Check that at least one tool from category is in descriptions
            assert any(tool in TOOL_DESCRIPTIONS for tool in category_tools)
    
    def test_get_tool_description(self):
        """Test get_tool_description function."""
        # Test existing tool
        desc = get_tool_description("brainstorm")
        assert desc.name == "brainstorm"
        assert desc.category == "core_workflow"
        
        # Test non-existent tool
        with pytest.raises(KeyError):
            get_tool_description("non_existent_tool")
    
    def test_get_tools_by_category(self):
        """Test get_tools_by_category function."""
        # Test existing category
        core_tools = get_tools_by_category("core_workflow")
        assert len(core_tools) > 0
        assert all(tool.category == "core_workflow" for tool in core_tools)
        
        # Test non-existent category
        empty_tools = get_tools_by_category("non_existent_category")
        assert len(empty_tools) == 0
    
    def test_format_tools_for_llm(self):
        """Test format_tools_for_llm function."""
        # Test with specific tools
        core_tools = get_tools_by_category("core_workflow")
        formatted = format_tools_for_llm(core_tools[:2])
        
        assert "brainstorm" in formatted
        assert "Description:" in formatted
        assert "When to use:" in formatted
        
        # Test with all tools (should not crash)
        all_formatted = format_tools_for_llm()
        assert len(all_formatted) > 0


class TestEnhancedToolRegistry:
    """Test EnhancedToolRegistry functionality."""
    
    @pytest.fixture
    def mock_tool(self):
        """Create a mock LangChain tool."""
        tool = Mock()
        tool.name = "mock_tool"
        tool.description = "A mock tool for testing"
        return tool
    
    @pytest.fixture
    def registry(self):
        """Create a fresh registry for testing."""
        with patch('essay_agent.agent.tools.tool_registry.BASE_REGISTRY', {}):
            return EnhancedToolRegistry()
    
    def test_registry_initialization(self, registry):
        """Test registry initializes properly."""
        assert isinstance(registry.tools, dict)
        assert isinstance(registry.descriptions, dict)
        assert isinstance(registry.categories, dict)
    
    def test_register_tool_with_description(self, registry, mock_tool):
        """Test registering a tool with explicit description."""
        desc = ToolDescription(
            name="mock_tool",
            category="testing",
            description="Mock tool",
            purpose="Testing",
            input_requirements=["input"],
            output_format="output",
            when_to_use="when testing",
            example_usage="use mock_tool",
            dependencies=[],
            estimated_tokens=100
        )
        
        registry.register_tool(mock_tool, desc)
        
        assert "mock_tool" in registry.tools
        assert "mock_tool" in registry.descriptions
        assert "testing" in registry.categories
        assert "mock_tool" in registry.categories["testing"]
    
    def test_register_tool_auto_description(self, registry, mock_tool):
        """Test registering a tool with auto-lookup description."""
        # This would typically look up from TOOL_DESCRIPTIONS
        # but will create a minimal description if not found
        registry.register_tool(mock_tool)
        
        assert "mock_tool" in registry.tools
        assert "mock_tool" in registry.descriptions
        desc = registry.descriptions["mock_tool"]
        assert desc.name == "mock_tool"
    
    def test_get_tools_by_category(self, registry, mock_tool):
        """Test getting tools by category."""
        desc = ToolDescription(
            name="mock_tool",
            category="testing",
            description="Mock tool",
            purpose="Testing",
            input_requirements=["input"],
            output_format="output", 
            when_to_use="when testing",
            example_usage="use mock_tool",
            dependencies=[],
            estimated_tokens=100
        )
        
        registry.register_tool(mock_tool, desc)
        
        testing_tools = registry.get_tools_by_category("testing")
        assert len(testing_tools) == 1
        assert testing_tools[0].name == "mock_tool"
        
        # Test non-existent category
        empty_tools = registry.get_tools_by_category("non_existent")
        assert len(empty_tools) == 0
    
    def test_find_tools_by_keywords(self, registry, mock_tool):
        """Test keyword-based tool search."""
        desc = ToolDescription(
            name="mock_tool",
            category="testing",
            description="A tool for generating brainstorm ideas",
            purpose="Generate creative content",
            input_requirements=["input"],
            output_format="output",
            when_to_use="when brainstorming",
            example_usage="use mock_tool",
            dependencies=[],
            estimated_tokens=100
        )
        
        registry.register_tool(mock_tool, desc)
        
        # Search for brainstorm-related tools
        matches = registry.find_tools_by_keywords(["brainstorm", "ideas"])
        assert len(matches) >= 1
        assert any(tool.name == "mock_tool" for tool in matches)
    
    def test_workflow_tools(self, registry):
        """Test getting workflow tools in order."""
        # This test depends on the actual workflow tools being registered
        # We'll mock the descriptions for the test
        workflow_names = ["brainstorm", "outline", "draft", "revise", "polish"]
        
        for name in workflow_names:
            mock_tool = Mock()
            mock_tool.name = name
            desc = ToolDescription(
                name=name,
                category="core_workflow",
                description=f"{name} tool",
                purpose=f"Perform {name}",
                input_requirements=["input"],
                output_format="output",
                when_to_use=f"when {name}ing",
                example_usage=f"use {name}",
                dependencies=[],
                estimated_tokens=100
            )
            registry.register_tool(mock_tool, desc)
        
        workflow_tools = registry.get_workflow_tools()
        assert len(workflow_tools) == 5
        assert workflow_tools[0].name == "brainstorm"
        assert workflow_tools[-1].name == "polish"
    
    def test_suggest_next_tools(self, registry):
        """Test suggesting next tools based on completed ones."""
        # Register tools with dependencies
        tools_with_deps = [
            ("brainstorm", []),
            ("outline", ["brainstorm"]),
            ("draft", ["outline"]),
        ]
        
        for name, deps in tools_with_deps:
            mock_tool = Mock()
            mock_tool.name = name
            desc = ToolDescription(
                name=name,
                category="core_workflow",
                description=f"{name} tool",
                purpose=f"Perform {name}",
                input_requirements=["input"],
                output_format="output",
                when_to_use=f"when {name}ing",
                example_usage=f"use {name}",
                dependencies=deps,
                estimated_tokens=100
            )
            registry.register_tool(mock_tool, desc)
        
        # Test suggesting next after brainstorm
        suggestions = registry.suggest_next_tools(["brainstorm"])
        suggested_names = [tool.name for tool in suggestions]
        assert "outline" in suggested_names
        assert "draft" not in suggested_names  # Dependencies not met
    
    def test_validate_tool_sequence(self, registry):
        """Test validating tool execution sequence."""
        # Register tools with dependencies
        tools_with_deps = [
            ("brainstorm", []),
            ("outline", ["brainstorm"]),
            ("draft", ["outline"]),
        ]
        
        for name, deps in tools_with_deps:
            mock_tool = Mock()
            mock_tool.name = name
            desc = ToolDescription(
                name=name,
                category="core_workflow",
                description=f"{name} tool",
                purpose=f"Perform {name}",
                input_requirements=["input"],
                output_format="output",
                when_to_use=f"when {name}ing",
                example_usage=f"use {name}",
                dependencies=deps,
                estimated_tokens=100
            )
            registry.register_tool(mock_tool, desc)
        
        # Test valid sequence
        is_valid, missing = registry.validate_tool_sequence(["brainstorm", "outline", "draft"])
        assert is_valid
        assert len(missing) == 0
        
        # Test invalid sequence
        is_valid, missing = registry.validate_tool_sequence(["draft", "brainstorm"])
        assert not is_valid
        assert len(missing) > 0


class TestToolAnalyzer:
    """Test ToolAnalyzer functionality."""
    
    @pytest.fixture
    def mock_registry(self):
        """Create a mock registry with test tools."""
        registry = Mock(spec=EnhancedToolRegistry)
        
        # Mock brainstorm tool
        brainstorm_desc = ToolDescription(
            name="brainstorm",
            category="core_workflow",
            description="Generate story ideas",
            purpose="Help with brainstorming",
            input_requirements=["user_profile", "essay_prompt"],
            output_format="List of stories",
            when_to_use="when brainstorming ideas",
            example_usage="brainstorm ideas for my essay",
            dependencies=[],
            estimated_tokens=800,
            confidence_threshold=0.9
        )
        
        # Mock outline tool
        outline_desc = ToolDescription(
            name="outline",
            category="structure",
            description="Create essay outline",
            purpose="Structure essay content",
            input_requirements=["chosen_story"],
            output_format="Structured outline",
            when_to_use="when organizing content",
            example_usage="create outline for my story",
            dependencies=["brainstorm"],
            estimated_tokens=600,
            confidence_threshold=0.8
        )
        
        registry.get_tools_for_phase.return_value = [brainstorm_desc]
        registry.get_tools_by_category.return_value = [brainstorm_desc]
        registry.get_description.return_value = brainstorm_desc
        
        return registry
    
    @pytest.fixture
    def analyzer(self, mock_registry):
        """Create ToolAnalyzer with mock registry."""
        return ToolAnalyzer(mock_registry)
    
    def test_quick_intent_analysis(self, analyzer):
        """Test pattern-based intent analysis."""
        # Test brainstorming intent
        result = analyzer._quick_intent_analysis("I need help brainstorming ideas")
        assert result["primary_intent"] == "brainstorming"
        assert result["confidence"] > 0.5
        
        # Test drafting intent
        result = analyzer._quick_intent_analysis("Help me write my essay draft")
        assert result["primary_intent"] == "drafting"
    
    def test_analyze_user_intent(self, analyzer):
        """Test full intent analysis."""
        # Test with clear brainstorming message
        intent = analyzer.analyze_user_intent("I need brainstorming help")
        
        assert isinstance(intent, UserIntent)
        assert intent.primary_intent == "brainstorming"
        assert intent.essay_phase == "brainstorming"
        assert intent.confidence > 0.3
    
    def test_analyze_context(self, analyzer):
        """Test context analysis."""
        available_data = {
            "user_profile": {"name": "Test User"},
            "essay_prompt": "Write about a challenge",
            "stories": ["story1", "story2"]
        }
        
        completed_tools = ["brainstorm"]
        
        context = analyzer.analyze_context(available_data, completed_tools)
        
        assert isinstance(context, ContextAnalysis)
        assert "user_profile" in context.available_data
        assert "essay_prompt" in context.available_data
        assert "brainstorm" in context.completed_tools
        assert "20%" in context.workflow_progress  # 1/5 tools completed
    
    @patch('essay_agent.agent.tools.tool_analyzer.get_chat_llm')
    def test_recommend_tools(self, mock_llm, analyzer, mock_registry):
        """Test tool recommendation logic."""
        # Create test intent and context
        intent = UserIntent(
            primary_intent="brainstorming",
            secondary_intents=[],
            confidence=0.8,
            essay_phase="brainstorming",
            specific_request="I need brainstorming help",
            urgency="Medium"
        )
        
        context = ContextAnalysis(
            available_data=["user_profile", "essay_prompt"],
            completed_tools=[],
            missing_dependencies=[],
            workflow_progress="0% - Not started"
        )
        
        # Mock registry to return brainstorm tool
        brainstorm_desc = ToolDescription(
            name="brainstorm",
            category="core_workflow",
            description="Generate story ideas",
            purpose="Help with brainstorming",
            input_requirements=["user_profile", "essay_prompt"],
            output_format="List of stories",
            when_to_use="when brainstorming ideas",
            example_usage="brainstorm ideas for my essay",
            dependencies=[],
            estimated_tokens=800,
            confidence_threshold=0.9
        )
        
        mock_registry.get_tools_for_phase.return_value = [brainstorm_desc]
        mock_registry.get_tools_by_category.return_value = [brainstorm_desc]
        
        recommendations = analyzer.recommend_tools(intent, context)
        
        assert len(recommendations) > 0
        assert isinstance(recommendations[0], ToolRecommendation)
        assert recommendations[0].tool_name == "brainstorm"
    
    def test_explain_recommendation(self, analyzer, mock_registry):
        """Test recommendation explanation generation."""
        intent = UserIntent(
            primary_intent="brainstorming",
            secondary_intents=[],
            confidence=0.8,
            essay_phase="brainstorming",
            specific_request="I need ideas",
            urgency="Medium"
        )
        
        context = ContextAnalysis(
            available_data=["user_profile"],
            completed_tools=[],
            missing_dependencies=[],
            workflow_progress="0%"
        )
        
        explanation = analyzer.explain_recommendation("brainstorm", intent, context)
        
        assert "brainstorm" in explanation.lower()
        assert "purpose" in explanation.lower()
        assert "example usage" in explanation.lower()


class TestIntegration:
    """Integration tests for the complete tool descriptions system."""
    
    def test_factory_function(self):
        """Test create_tool_analyzer factory function."""
        analyzer = create_tool_analyzer()
        assert isinstance(analyzer, ToolAnalyzer)
        assert analyzer.registry is not None
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from intent analysis to tool recommendation."""
        # This would be a more complex integration test
        # combining all components in a realistic scenario
        analyzer = create_tool_analyzer()
        
        # Analyze intent
        intent = analyzer.analyze_user_intent("I need help brainstorming essay ideas")
        assert intent.primary_intent == "brainstorming"
        
        # Analyze context
        context = analyzer.analyze_context({
            "user_profile": {"name": "Test"},
            "essay_prompt": "Challenge essay"
        })
        assert len(context.available_data) >= 2
        
        # Get recommendations
        recommendations = analyzer.recommend_tools(intent, context, max_recommendations=3)
        assert len(recommendations) <= 3
        
        # Should recommend brainstorm-related tools
        recommended_names = [rec.tool_name for rec in recommendations]
        assert any("brainstorm" in name for name in recommended_names)


if __name__ == "__main__":
    pytest.main([__file__]) 