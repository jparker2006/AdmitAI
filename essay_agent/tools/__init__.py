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


# ----- Example stub tool: echo ------------------------------------------------

@register_tool("echo")
def echo_tool(message: str = "Hello, Essay Agent!") -> dict:
    """Simple debugging tool that echoes a message.

    Args:
        message: text to echo back
    Returns:
        dict: wrapper around the provided message
    """

    return {"echo": message} 