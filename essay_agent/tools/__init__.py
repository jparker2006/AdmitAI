"""Tool registry and dynamic loader for Essay Agent.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import warnings
from pathlib import Path
from typing import Any, Dict

from langchain.tools import BaseTool
from essay_agent.tools.base import ValidatedTool

# ---------------------------------------------------------------------------
# Registry implementation
# ---------------------------------------------------------------------------


class ToolRegistry(dict):
    """Dictionary-like container for LangChain `BaseTool` instances."""

    def register(self, tool: BaseTool, *, overwrite: bool = False) -> None:
        if tool.name in self and not overwrite:
            warnings.warn(f"Tool '{tool.name}' already registered; skipping.")
            return
        self[tool.name] = tool

    # Synchronous call ------------------------------------------------------
    def call(self, name: str, **kwargs: Any):  # noqa: D401
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")
        return tool(**kwargs)

    # Async call ------------------------------------------------------------
    async def acall(self, name: str, **kwargs: Any):  # noqa: D401
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")

        # If the tool exposes LangChain's async interface --------------------
        if hasattr(tool, "ainvoke") and callable(getattr(tool, "ainvoke")):
            return await tool.ainvoke(**kwargs)  # type: ignore[arg-type]

        # If the tool itself is an async coroutine function ------------------
        import asyncio

        if asyncio.iscoroutinefunction(tool):  # type: ignore[arg-type]
            return await tool(**kwargs)  # type: ignore[misc]

        # Fallback to synchronous execution ----------------------------------
        return tool(**kwargs)  # type: ignore[call-arg]


REGISTRY = ToolRegistry()

# Backwards compatibility alias
TOOL_REGISTRY = REGISTRY

# ---------------------------------------------------------------------------
# Decorator helper (works for subclasses or callables returning BaseTool)
# ---------------------------------------------------------------------------

def register_tool(name: str):
    """Decorator to register a tool class or factory under `name`."""

    def decorator(obj):
        if inspect.isclass(obj) and issubclass(obj, BaseTool):
            instance = obj()
        elif isinstance(obj, BaseTool):
            instance = obj
        elif callable(obj):
            # Wrap plain callable in a ValidatedTool subclass ----------------
            func = obj
            tool_name = name

            class _FuncTool(ValidatedTool):
                name = tool_name  # type: ignore
                description = func.__doc__ or "Wrapped function tool"

                def _run(self, *args, **kwargs):  # type: ignore
                    return func(*args, **kwargs)

            instance = _FuncTool()
        else:
            raise TypeError("register_tool requires BaseTool subclass/instance or callable")
        instance.name = name  # ensure name matches registry key
        REGISTRY.register(instance, overwrite=True)
        return obj

    return decorator


# ---------------------------------------------------------------------------
# Dynamic module loading (import all siblings to auto-register tools)
# ---------------------------------------------------------------------------

_current_pkg = Path(__file__).parent
for mod_info in pkgutil.iter_modules([str(_current_pkg)]):
    if mod_info.name == "__init__":
        continue
    importlib.import_module(f"{__name__}.{mod_info.name}")

# Explicit import of text_selection ensures registration even if module name
# is added after initial package creation (e.g., during runtime tests).
try:
    importlib.import_module(f"{__name__}.text_selection")
except ModuleNotFoundError:
    # During early installations the file may not yet exist
    pass

# ---------------------------------------------------------------------------
# U4-10A – Increase default timeout to 60 s for all tools --------------------
# ---------------------------------------------------------------------------

for _tool in REGISTRY.values():
    if hasattr(_tool, "timeout") and _tool.timeout is not None and _tool.timeout < 60:  # type: ignore[attr-defined]
        _tool.timeout = 60.0

# ---------------------------------------------------------------------------
# Tool access functions
# ---------------------------------------------------------------------------

def get_available_tools() -> Dict[str, BaseTool]:
    """Get all registered tools.
    
    Returns:
        Dictionary mapping tool names to tool instances
    """
    return dict(REGISTRY) 

# ---------------------------------------------------------------------------
# Export argument specification catalogue (Phase-6)
# ---------------------------------------------------------------------------
try:
    from essay_agent.tools.tool_introspection import TOOL_ARG_SPEC, get_required_args, get_optional_args  # noqa: F401
except Exception:  # pragma: no cover
    # Introspection may fail during partial installations; fallback to empty mapping
    TOOL_ARG_SPEC = {}
    def get_required_args(name):  # type: ignore
        return []
    def get_optional_args(name):  # type: ignore
        return [] 