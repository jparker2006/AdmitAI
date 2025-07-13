"""
Tool Registry

Each tool must expose a callable returning JSON-serializable output.
Register tools in ``TOOL_REGISTRY`` to allow the Executor to discover them.

Design Note:
Using a simple dict for now; migrate to entry-point discovery or Pluggy plugin
manager later for extensibility.
"""

from typing import Callable, Dict

TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(name: str):
    """Decorator to register a tool function in the global registry."""

    def decorator(func: Callable):
        TOOL_REGISTRY[name] = func
        return func

    return decorator


# ----- LangChain EchoTool registration ---------------------------------------

# The full-featured EchoTool lives in ``echo.py``.  We import and register a
# singleton instance here so existing Planner/Executor logic can discover it
# via the global ``TOOL_REGISTRY``.

from .echo import EchoTool

# Register instance (callable thanks to BaseTool.__call__)
TOOL_REGISTRY["echo"] = EchoTool() 