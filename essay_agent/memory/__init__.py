"""
Memory Subsystem (MVP)

Phase 1: JSON-file store on local disk (one file per user).
Future Roadmap: migrate to SQLite or a vector DB for semantic search.

Public API:
- ``load_user_profile(user_id)``
- ``save_user_profile(user_id, profile_dict)``
"""

import json
from pathlib import Path
from typing import Dict, Any

# Directory where JSON profiles will be stored *must* exist before others import
_MEMORY_ROOT = Path("memory_store")
_MEMORY_ROOT.mkdir(exist_ok=True)


def _profile_path(user_id: str) -> Path:
    """Compute filesystem path for a given user id."""
    return _MEMORY_ROOT / f"{user_id}.json"


# Import modules that rely on helpers *after* they are defined to avoid circular deps
from .conversation import JSONConversationMemory  # noqa: E402  (import after defs)


def load_user_profile(user_id: str) -> Dict[str, Any]:
    """Load user profile. Returns empty dict if not existing."""
    path = _profile_path(user_id)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_user_profile(user_id: str, profile: Dict[str, Any]) -> None:
    """Persist user profile to disk with pretty JSON formatting."""
    path = _profile_path(user_id)
    path.write_text(json.dumps(profile, indent=2))

__all__ = [
    "load_user_profile",
    "save_user_profile",
    "JSONConversationMemory",
] 