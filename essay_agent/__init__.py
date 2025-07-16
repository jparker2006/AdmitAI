"""
Essay Agent package initialization.

Modern ReAct agent system for intelligent essay writing assistance.
Exposes the core EssayReActAgent and essential utilities.
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

# Public symbols - Modern ReAct Agent System
__all__ = [
    # ReAct Agent System
    "EssayReActAgent",
    "AgentMemory",
    "TOOL_DESCRIPTIONS",
    
    # Legacy compatibility (minimal)
    "EssayExecutor", 
    "load_user_profile",
    "save_user_profile",
]

# Core ReAct Agent System imports
try:
    from .agent.core.react_agent import EssayReActAgent  # noqa: F401
    from .agent.memory.agent_memory import AgentMemory  # noqa: F401
    from .agent.tools.tool_descriptions import TOOL_DESCRIPTIONS  # noqa: F401
except ImportError as e:  # pragma: no cover
    # Graceful degradation if ReAct agent components not available
    warnings.warn(f"ReAct agent system not available: {e}")
    EssayReActAgent = None  # type: ignore
    AgentMemory = None  # type: ignore
    TOOL_DESCRIPTIONS = {}  # type: ignore

# Legacy compatibility - keep essential components
from .executor import EssayExecutor  # noqa: F401

# LLM client convenience exports
try:
    from .llm_client import get_chat_llm, track_cost  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    # llm_client may have optional heavy deps; degrade gracefully
    get_chat_llm = None  # type: ignore
    track_cost = None  # type: ignore

# Memory system utilities
try:
    from .memory import load_user_profile, save_user_profile  # noqa: F401
except ImportError:  # pragma: no cover
    # Fallback if memory system not available
    def load_user_profile(user_id: str) -> dict:
        """Fallback user profile loader."""
        return {"user_id": user_id, "preferences": {}}
    
    def save_user_profile(user_id: str, profile: dict) -> None:
        """Fallback user profile saver."""
        pass 