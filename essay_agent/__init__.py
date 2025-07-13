"""
Essay Agent package initialization.

Exposes convenience factories for quickly instantiating the Planner → Executor loop.
Nothing heavy should happen at import time – keep side-effects minimal.
"""

# Public symbols
__all__ = [
    "EssayPlanner",
    "EssayExecutor",
]

# Core imports
from .planner import EssayPlanner  # noqa: F401
from .executor import EssayExecutor  # noqa: F401

# Optional – state_manager requires heavy deps not yet installed
try:
    from .state_manager import ConversationStateManager  # noqa: F401
    __all__.append("ConversationStateManager")
except ModuleNotFoundError:  # pragma: no cover
    # Gracefully degrade until dependencies (e.g., tiktoken) are available
    ConversationStateManager = None  # type: ignore 