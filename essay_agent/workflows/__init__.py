"""Workflow infrastructure for advanced LangGraph patterns.

This package provides foundational classes for branching, conditional logic, 
loops, and quality gates in essay workflows.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import warnings
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Workflow Registry implementation
# ---------------------------------------------------------------------------

class WorkflowRegistry(dict):
    """Dictionary-like container for WorkflowNode instances."""

    def register(self, node: Any, *, overwrite: bool = False) -> None:
        """Register a workflow node instance."""
        node_name = node.get_name()
        if node_name in self and not overwrite:
            warnings.warn(f"Workflow node '{node_name}' already registered; skipping.")
            return
        self[node_name] = node

    def get_node(self, name: str) -> Any:
        """Get a workflow node by name."""
        return self.get(name)

    async def execute_node(self, name: str, state: Any) -> Dict[str, Any]:
        """Execute a workflow node by name."""
        node = self.get_node(name)
        if node is None:
            raise KeyError(f"Workflow node '{name}' not found")
        return await node.execute(state)

# ---------------------------------------------------------------------------
# Global registry instance
# ---------------------------------------------------------------------------

WORKFLOW_REGISTRY = WorkflowRegistry()

# ---------------------------------------------------------------------------
# Orchestrator imports
# ---------------------------------------------------------------------------

from .orchestrator import (
    WorkflowOrchestrator,
    WorkflowConfig,
    WorkflowResult,
    ResourceUnavailableError,
    MonitoringError,
    OrchestrationError
)

# ---------------------------------------------------------------------------
# Decorator helper for workflow node registration
# ---------------------------------------------------------------------------

def register_workflow_node(name: str):
    """Decorator to register a workflow node class under `name`."""
    
    def decorator(cls):
        if not inspect.isclass(cls):
            raise TypeError("register_workflow_node requires a class")
        
        # Import WorkflowNode dynamically to avoid circular import
        from essay_agent.workflows.base import WorkflowNode
        
        if not issubclass(cls, WorkflowNode):
            raise TypeError("register_workflow_node requires WorkflowNode subclass")
        
        # Create instance and register it
        instance = cls()
        instance._name = name  # Set internal name
        WORKFLOW_REGISTRY.register(instance, overwrite=True)
        return cls
    
    return decorator

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "WorkflowRegistry",
    "WORKFLOW_REGISTRY", 
    "register_workflow_node",
]

# ---------------------------------------------------------------------------
# Dynamic module loading (import all siblings to auto-register nodes)
# ---------------------------------------------------------------------------

_current_pkg = Path(__file__).parent
for mod_info in pkgutil.iter_modules([str(_current_pkg)]):
    if mod_info.name == "__init__":
        continue
    try:
        importlib.import_module(f"{__name__}.{mod_info.name}")
    except ImportError as e:
        warnings.warn(f"Failed to import workflow module {mod_info.name}: {e}") 