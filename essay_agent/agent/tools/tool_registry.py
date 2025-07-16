"""Enhanced tool registry with categorization and context analysis.

This module provides an advanced tool registry that can categorize tools,
analyze context, and recommend relevant tools based on user intent.
"""
from __future__ import annotations

import warnings
from typing import Any, Dict, List, Set, Tuple, Optional

from langchain.tools import BaseTool

from essay_agent.tools import REGISTRY as BASE_REGISTRY
from essay_agent.agent.tools.tool_descriptions import (
    ToolDescription, 
    TOOL_DESCRIPTIONS, 
    TOOL_CATEGORIES,
    get_tools_by_category,
    get_tool_description
)


class EnhancedToolRegistry:
    """Advanced tool registry with categorization and context analysis."""
    
    def __init__(self):
        """Initialize enhanced registry."""
        self.tools: Dict[str, BaseTool] = {}
        self.descriptions: Dict[str, ToolDescription] = {}
        self.categories: Dict[str, Set[str]] = {}
        self._populate_from_base_registry()
    
    def _populate_from_base_registry(self):
        """Load tools from existing base registry."""
        for name, tool in BASE_REGISTRY.items():
            self.register_tool(tool)
    
    def register_tool(self, tool: BaseTool, description: Optional[ToolDescription] = None) -> None:
        """Register a tool with optional description.
        
        Args:
            tool: LangChain BaseTool instance
            description: Optional tool description (will auto-lookup if not provided)
        """
        self.tools[tool.name] = tool
        
        # Get description from catalog or use provided one
        if description is None:
            try:
                description = get_tool_description(tool.name)
            except KeyError:
                warnings.warn(f"No description found for tool '{tool.name}' - creating minimal description")
                description = ToolDescription(
                    name=tool.name,
                    category="unknown",
                    description=tool.description or "No description available",
                    purpose="Unknown purpose",
                    input_requirements=["unknown"],
                    output_format="Unknown format",
                    when_to_use="Unknown usage",
                    example_usage=f"Use {tool.name}",
                    dependencies=[],
                    estimated_tokens=100,
                    confidence_threshold=0.5
                )
        
        self.descriptions[tool.name] = description
        self._update_categories(description)
    
    def _update_categories(self, description: ToolDescription):
        """Update category mappings."""
        category = description.category
        if category not in self.categories:
            self.categories[category] = set()
        self.categories[category].add(description.name)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        return self.tools.get(name)
    
    def has_tool(self, name: str) -> bool:
        """Check if tool exists in registry."""
        return name in self.tools
    
    def get_description(self, name: str) -> Optional[ToolDescription]:
        """Get tool description by name."""
        return self.descriptions.get(name)
    
    def get_tool_description(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool description as dictionary for action executor compatibility."""
        desc = self.get_description(name)
        if not desc:
            return None
        
        # Convert ToolDescription to dictionary format expected by action executor
        return {
            "name": desc.name,
            "category": desc.category,
            "description": desc.description,
            "purpose": desc.purpose,
            "required_args": desc.input_requirements,  # Map input_requirements to required_args
            "output_format": desc.output_format,
            "when_to_use": desc.when_to_use,
            "example_usage": desc.example_usage,
            "dependencies": desc.dependencies,
            "estimated_tokens": desc.estimated_tokens,
            "confidence_threshold": desc.confidence_threshold,
            "arg_types": {}  # Default empty dict for arg_types (could be enhanced later)
        }
    
    def get_tools_by_category(self, category: str) -> List[ToolDescription]:
        """Get all tool descriptions in a specific category."""
        if category not in self.categories:
            return []
        
        return [self.descriptions[name] for name in self.categories[category] 
                if name in self.descriptions]
    
    def get_category_list(self) -> List[str]:
        """Get list of all categories."""
        return list(self.categories.keys())
    
    def get_all_descriptions(self) -> List[ToolDescription]:
        """Get all tool descriptions."""
        return list(self.descriptions.values())
    
    def find_tools_by_keywords(self, keywords: List[str]) -> List[ToolDescription]:
        """Find tools by keyword matching in descriptions.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of matching tool descriptions
        """
        keywords_lower = [kw.lower() for kw in keywords]
        matches = []
        
        for desc in self.descriptions.values():
            # Search in description, purpose, and when_to_use fields
            search_text = f"{desc.description} {desc.purpose} {desc.when_to_use}".lower()
            
            if any(keyword in search_text for keyword in keywords_lower):
                matches.append(desc)
        
        return matches
    
    def get_tools_with_dependencies_satisfied(self, available_data: Set[str]) -> List[ToolDescription]:
        """Get tools whose dependencies are satisfied by available data.
        
        Args:
            available_data: Set of available data types (e.g., {'user_profile', 'essay_prompt'})
            
        Returns:
            List of tools that can be executed with current data
        """
        executable_tools = []
        
        for desc in self.descriptions.values():
            # Check if all input requirements are met
            requirements_met = all(
                req in available_data for req in desc.input_requirements
            )
            
            if requirements_met:
                executable_tools.append(desc)
        
        return executable_tools
    
    def get_workflow_tools(self) -> List[ToolDescription]:
        """Get core workflow tools in order."""
        workflow_names = ["brainstorm", "outline", "draft", "revise", "polish"]
        return [self.descriptions[name] for name in workflow_names 
                if name in self.descriptions]
    
    def suggest_next_tools(self, completed_tools: List[str]) -> List[ToolDescription]:
        """Suggest next logical tools based on completed tools.
        
        Args:
            completed_tools: List of tool names that have been completed
            
        Returns:
            List of suggested next tools
        """
        completed_set = set(completed_tools)
        suggestions = []
        
        for desc in self.descriptions.values():
            # Check if dependencies are satisfied
            dependencies_met = all(dep in completed_set for dep in desc.dependencies)
            
            # Don't suggest tools already completed
            if dependencies_met and desc.name not in completed_set:
                suggestions.append(desc)
        
        # Sort by confidence threshold (higher first)
        suggestions.sort(key=lambda x: x.confidence_threshold, reverse=True)
        
        return suggestions
    
    def get_tools_for_phase(self, phase: str) -> List[ToolDescription]:
        """Get tools appropriate for a specific essay writing phase.
        
        Args:
            phase: Essay writing phase (brainstorming, structuring, drafting, revising, polishing)
            
        Returns:
            List of relevant tools for that phase
        """
        phase_mapping = {
            "brainstorming": ["brainstorming", "prompt_analysis"],
            "structuring": ["structure", "prompt_analysis"],
            "drafting": ["writing", "core_workflow"],
            "revising": ["evaluation", "writing"],
            "polishing": ["polish", "validation"]
        }
        
        relevant_categories = phase_mapping.get(phase.lower(), [])
        tools = []
        
        for category in relevant_categories:
            tools.extend(self.get_tools_by_category(category))
        
        return tools
    
    def validate_tool_sequence(self, tool_names: List[str]) -> Tuple[bool, List[str]]:
        """Validate that a sequence of tools has satisfied dependencies.
        
        Args:
            tool_names: Ordered list of tool names to validate
            
        Returns:
            Tuple of (is_valid, list_of_missing_dependencies)
        """
        completed = set()
        missing_deps = []
        
        for tool_name in tool_names:
            if tool_name not in self.descriptions:
                missing_deps.append(f"Unknown tool: {tool_name}")
                continue
            
            desc = self.descriptions[tool_name]
            
            # Check if dependencies are satisfied
            for dep in desc.dependencies:
                if dep not in completed:
                    missing_deps.append(f"{tool_name} requires {dep}")
            
            completed.add(tool_name)
        
        return len(missing_deps) == 0, missing_deps
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about registered tools."""
        total_tools = len(self.tools)
        categories_count = len(self.categories)
        
        category_breakdown = {
            cat: len(tools) for cat, tools in self.categories.items()
        }
        
        avg_tokens = sum(desc.estimated_tokens for desc in self.descriptions.values()) / total_tools
        
        return {
            "total_tools": total_tools,
            "categories_count": categories_count,
            "category_breakdown": category_breakdown,
            "average_estimated_tokens": avg_tokens,
            "tools_with_dependencies": len([
                desc for desc in self.descriptions.values() 
                if desc.dependencies
            ])
        }
    
    def call_tool(self, name: str, **kwargs: Any) -> Any:
        """Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            KeyError: If tool not found
        """
        tool = self.get_tool(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")
        
        return tool(**kwargs)
    
    async def acall_tool(self, name: str, **kwargs: Any) -> Any:
        """Execute a tool asynchronously by name.
        
        Args:
            name: Tool name
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            KeyError: If tool not found
        """
        tool = self.get_tool(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")
        
        # Use LangChain's async interface if available
        if hasattr(tool, "ainvoke"):
            return await tool.ainvoke(kwargs)
        
        # Fallback to sync execution
        return tool(**kwargs)


# Global enhanced registry instance
ENHANCED_REGISTRY = EnhancedToolRegistry() 