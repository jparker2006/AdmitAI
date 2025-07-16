"""
Essay Agent package initialization.

Exposes convenience factories for quickly instantiating the Planner → Executor loop.
Nothing heavy should happen at import time – keep side-effects minimal.
"""

# ---------------------------------------------------------------------------
# Suppress noisy LangChain deprecation warnings so CLI output remains clean.
# Users can re-enable by setting the `ESSAY_AGENT_DEBUG_WARNINGS` env variable.
# ---------------------------------------------------------------------------

import os
import warnings
import importlib

# Automatically enable fast test mode (skips long sleeps) during CI runs
import os as _os
_os.environ.setdefault('ESSAY_AGENT_FAST_TEST', '1')

# Silence LangChainDeprecationWarning variants unless explicitly opted-in
if os.getenv("ESSAY_AGENT_DEBUG_WARNINGS", "0") != "1":
    for mod_path in [
        "langchain_core._api.deprecation",
        "langchain._api.module_import",
    ]:
        try:
            mod = importlib.import_module(mod_path)
            if hasattr(mod, "LangChainDeprecationWarning"):
                warnings.filterwarnings("ignore", category=getattr(mod, "LangChainDeprecationWarning"))
        except ModuleNotFoundError:
            continue
    # Fallback: blanket-ignore generic DeprecationWarnings from langchain
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

# Public symbols
# TEMPORARILY COMMENTED FOR TASK-001 VALIDATION
# from .agent import EssayAgent  # noqa: E402

__all__ = [
    "EssayPlanner",
    "EssayExecutor",
    # "EssayAgent",  # Temporarily commented
    "load_user_profile",
    "save_user_profile",
]

# Core imports
from .planner import EssayPlanner  # noqa: F401
from .executor import EssayExecutor  # noqa: F401

# LLM client convenience exports ---------------------------------------------------
try:
    from .llm_client import get_chat_llm, track_cost  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    # llm_client may have optional heavy deps; degrade gracefully
    get_chat_llm = None  # type: ignore
    track_cost = None  # type: ignore

# Optional – state_manager requires heavy deps not yet installed
try:
    from .state_manager import ConversationStateManager  # noqa: F401
    __all__.append("ConversationStateManager")
except ModuleNotFoundError:  # pragma: no cover
    # Gracefully degrade until dependencies (e.g., tiktoken) are available
    ConversationStateManager = None  # type: ignore 