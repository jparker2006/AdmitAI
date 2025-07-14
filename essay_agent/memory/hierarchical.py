"""essay_agent.memory.hierarchical

HierarchicalMemory unifies three memory tiers for the essay agent:

1. Working memory  – short-term conversation context handled by
   ``JSONConversationMemory``.
2. Semantic memory – long-term facts about the user such as core values or
   defining moments stored in ``UserProfile``.
3. Episodic memory – essay history stored in ``UserProfile.essay_history``.

The class offers a single interface for agents while delegating persistence to
existing helpers (SimpleMemory + JSONConversationMemory).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from filelock import FileLock
from pydantic import ValidationError

from .conversation import JSONConversationMemory
from .simple_memory import SimpleMemory
from .user_profile_schema import (
    CoreValue,
    DefiningMoment,
    EssayRecord,
    EssayVersion,
    UserProfile,
)
from . import _profile_path  # re-exported helper for profile path

__all__ = ["HierarchicalMemory"]

# ---------------------------------------------------------------------------
# Helper typing ----------------------------------------------------------------
SemanticItem = Union[CoreValue, DefiningMoment]


class HierarchicalMemory:  # pylint: disable=too-few-public-methods
    """Three-tier hierarchical memory abstraction.

    Parameters
    ----------
    user_id: str
        Unique identifier for the user (filename stem).
    k: int, default=6
        Number of recent messages to include in summaries for working memory.
    """

    # ------------------------------------------------------------------
    # Construction & internal helpers
    # ------------------------------------------------------------------

    def __init__(self, user_id: str, k: int = 6):
        self.user_id: str = user_id

        # Working memory ------------------------------------------------------
        self.working: JSONConversationMemory = JSONConversationMemory(user_id=user_id, k=k)

        # Semantic & episodic memory ------------------------------------------
        self.profile: UserProfile = SimpleMemory.load(user_id)

        # File lock pointing to main profile JSON (not conv file) -------------
        self._path: Path = _profile_path(user_id)
        self._lock: FileLock = FileLock(str(self._path) + ".lock")

    # ------------------------------------------------------------------
    # General helpers
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Reload semantic + episodic profile from disk, replacing in-memory copy."""

        try:
            self.profile = SimpleMemory.load(self.user_id)
        except ValidationError as exc:  # pragma: no cover – unlikely but safe
            raise ValueError("Corrupt user profile JSON") from exc

    def save(self) -> None:  # noqa: D401 (short-description justification)
        """Persist semantic + episodic tiers to disk (conversation saved separately)."""

        SimpleMemory.save(self.user_id, self.profile)

    # ------------------------------------------------------------------
    # WORKING MEMORY (conversation context)
    # ------------------------------------------------------------------

    def add_chat_turn(self, inputs: Dict[str, str], outputs: Dict[str, str]) -> None:
        """Append a conversation turn to working memory and save to disk."""

        self.working.save_context(inputs, outputs)

    def get_recent_chat(self, k: Optional[int] = None) -> List[str]:
        """Return the *content* of the last *k* messages (human + AI)."""

        messages = self.working.buffer_memory.chat_memory.messages  # type: ignore[attr-defined]
        if k is None or k <= 0:
            return [m.content for m in messages]
        return [m.content for m in messages[-k:]]

    # ------------------------------------------------------------------
    # SEMANTIC MEMORY (core values, defining moments)
    # ------------------------------------------------------------------

    def add_semantic_item(self, item: SemanticItem) -> None:  # noqa: D401
        """Insert a new semantic item, avoiding duplicates."""

        if isinstance(item, CoreValue):
            if not any(cv.value == item.value for cv in self.profile.core_values):
                self.profile.core_values.append(item)
        elif isinstance(item, DefiningMoment):
            if not any(dm.title == item.title for dm in self.profile.defining_moments):
                self.profile.defining_moments.append(item)
        else:  # pragma: no cover
            raise ValueError("Unsupported semantic item type")

    # ----------------------- internal keyword helper -----------------------
    def _keyword_search(self, query: str, top_k: int = 5):  # noqa: D401
        """Fallback keyword search (existing regex implementation)."""

        import re as _re  # local import to avoid polluting module namespace

        pattern = _re.compile(_re.escape(query), _re.IGNORECASE)
        scored: List[Tuple[int, SemanticItem]] = []

        for item in list(self.profile.core_values) + list(self.profile.defining_moments):
            haystack = " ".join(str(getattr(item, fld, "")) for fld in item.model_fields)
            if (match := pattern.search(haystack)):
                scored.append((match.start(), item))

        scored.sort(key=lambda t: (t[0], getattr(t[1], "value", getattr(t[1], "title", ""))))
        return [item for _, item in scored[:top_k]]

    def semantic_search(self, query: str, top_k: int = 5) -> List[SemanticItem]:  # noqa: D401
        """Return semantic items most relevant to *query*.

        Prefers vector-based retrieval via :class:`SemanticSearchIndex` when
        available, falling back to keyword matching to ensure robustness when
        FAISS or embeddings are unavailable (e.g., during initial install).
        """

        try:
            from .semantic_search import SemanticSearchIndex  # local import to avoid heavy deps at module load

            index = SemanticSearchIndex.load_or_build(self.user_id, self.profile)
            results = index.search(query, k=top_k)

            # If vector search returns no results, fall back to keyword search
            if results:
                return results[:top_k]

        except Exception:  # pylint: disable=broad-except  # pragmatic: any failure → keyword fallback
            # Could be missing faiss, embeddings failure, etc.
            pass

        return self._keyword_search(query, top_k)

    # ------------------------------------------------------------------
    # EPISODIC MEMORY (essay history)
    # ------------------------------------------------------------------

    def add_essay_record(self, record: EssayRecord) -> None:  # noqa: D401
        self.profile.essay_history.append(record)

    def get_essay_history(self, status: Optional[str] = None) -> List[EssayRecord]:
        if status is None:
            return list(self.profile.essay_history)
        return [rec for rec in self.profile.essay_history if rec.status == status]

    # ------------------------------------------------------------------
    # Consolidation helpers
    # ------------------------------------------------------------------

    def consolidate_session(self, *, stories_used: Sequence[str], essay_record: EssayRecord) -> None:
        """Flush current session artefacts into long-term memory.

        1. Marks *stories_used* inside the latest EssayVersion of *essay_record*.
        2. Appends *essay_record* to episodic memory.
        3. Ensures *stories_used* are referenced in semantic tier (adds stub
           DefiningMoment objects if not already present).
        4. Saves profile to disk.
        """

        # Update record's latest version used_stories field ---------------------
        if essay_record.versions:
            essay_record.versions[-1].used_stories = list(stories_used)
        else:
            # Should not happen, but guard just in case
            raise ValueError("EssayRecord must contain at least one EssayVersion")

        # Append episodic memory ----------------------------------------------
        self.add_essay_record(essay_record)

        # Ensure semantic linkage ---------------------------------------------
        for story in stories_used:
            if not any(dm.title == story for dm in self.profile.defining_moments):
                self.profile.defining_moments.append(
                    DefiningMoment(
                        title=story,
                        description="",  # can be enriched later
                        emotional_impact="",
                        lessons_learned="",
                        used_in_essays=[essay_record.prompt_id],
                        themes=[],
                    )
                )

        # Persist to disk ------------------------------------------------------
        self.save()

    # ------------------------------------------------------------------
    # Representation helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # noqa: D401
        return f"<HierarchicalMemory user_id={self.user_id!r} essays={len(self.profile.essay_history)}>" 