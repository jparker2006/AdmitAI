"""
Essay Agent package initialization.

Exposes convenience factories for quickly instantiating the Planner → Executor loop.
Nothing heavy should happen at import time – keep side-effects minimal.
"""

from .planner import EssayPlanner  # noqa: F401
from .executor import EssayExecutor  # noqa: F401

__all__ = ["EssayPlanner", "EssayExecutor"] 