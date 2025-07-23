"""essay_agent.memory.simple_memory

Light-weight JSON memory helper wrapping existing ``load_user_profile`` /
``save_user_profile`` utilities.  Provides higher-level helpers for essay
history management and story-reuse checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
from typing import Any, List
from datetime import datetime

from filelock import FileLock
from pydantic import ValidationError

from .user_profile_schema import UserProfile, EssayRecord
from . import _profile_path  # reuse helper & storage dir
from . import load_user_profile, save_user_profile

__all__ = ["SimpleMemory", "is_story_reused", "ensure_essay_record"]


class SimpleMemory:  # pylint: disable=too-few-public-methods
    """Facade around JSON user profile storage with convenience helpers."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def load(user_id: str) -> UserProfile:  # noqa: D401
        """Return :class:`UserProfile` for *user_id* (create if missing)."""

        try:
            raw = load_user_profile(user_id)
        except json.JSONDecodeError:
            # File exists but is partially written – treat as empty and reset
            raw = {}

        if not raw:
            return _default_profile()

        # ------------------------------------------------------------------
        # Capture unknown top-level keys (extras).  We special-case the legacy
        # ``model_extra`` container because including it *again* inside itself
        # would create a self-referential dict that silently breaks downstream
        # look-ups and JSON serialisation.
        # ------------------------------------------------------------------

        unknown = {k: v for k, v in raw.items() if k not in UserProfile.model_fields}

        # If the legacy container itself appears at the root we merge *its*
        # contents into ``unknown`` and drop the key to avoid recursion.
        legacy_container = unknown.pop("model_extra", {}) if isinstance(unknown.get("model_extra"), dict) else {}
        if legacy_container:
            unknown.update(legacy_container)

        if unknown:
            # Ensure legacy container is a dict even if file contained null/other
            if not isinstance(raw.get("model_extra"), dict):
                raw["model_extra"] = {}
            raw["model_extra"].update(unknown)  # type: ignore[attr-defined]

        try:
            prof = UserProfile.model_validate(raw)  # type: ignore[attr-defined]
        except ValidationError as exc:  # pragma: no cover
            raise ValueError("Corrupt user profile JSON") from exc

        # ------------------------------------------------------------------
        # Keep **one** flat copy of extras on both containers so that callers
        # can safely access them regardless of the pydantic version they use.
        # ------------------------------------------------------------------

        base_extras = getattr(prof, "model_extra", None)
        if not isinstance(base_extras, dict):
            base_extras = {}

        merged_extras: dict[str, Any] = {**base_extras}  # type: ignore[var-annotated]

        # Merge any new unknown keys discovered above
        merged_extras.update(unknown)

        # Ensure legacy container exists ------------------------------------
        try:
            object.__setattr__(prof, "model_extra", merged_extras)  # type: ignore[attr-defined]
        except Exception:
            pass

        # Mirror into pydantic-v2 extras container --------------------------
        try:
            object.__setattr__(prof, "__pydantic_extra__", merged_extras)
        except Exception:
            pass
        return prof

    @staticmethod
    def save(user_id: str, profile: UserProfile) -> None:  # noqa: D401
        """Persist *profile* for *user_id* including extras."""

        # --------------------------------------------------------------
        # Persist profile *plus* any extras.  We first build a merged
        # ``extras`` dict combining both possible containers so that we can
        # write a single, authoritative copy to disk (and optionally keep a
        # flat root-level copy for backward compatibility).
        # --------------------------------------------------------------

        data = profile.model_dump()

        extra_v2 = getattr(profile, "__pydantic_extra__", {}) or {}
        extra_legacy = getattr(profile, "model_extra", {}) or {}

        merged_extras = {**extra_legacy, **extra_v2}

        # Store merged copy inside legacy container -----------------------
        if merged_extras:
            data["model_extra"] = merged_extras

        # Optionally keep a flat root-level view for existing files/tools --
        data.update(merged_extras)

        # Finally write to disk -------------------------------------------
        save_user_profile(user_id, data)

    # ------------------------------------------------------------------
    # Essay helpers
    # ------------------------------------------------------------------

    @classmethod
    def add_essay_record(cls, user_id: str, record: EssayRecord) -> None:  # noqa: D401
        profile = cls.load(user_id)
        profile.essay_history.append(record)
        cls.save(user_id, profile)


# ---------------------------------------------------------------------------
# Story-reuse helper – exported standalone for convenience
# ---------------------------------------------------------------------------

def is_story_reused(user_id: str, *, story_title: str, college: str) -> bool:  # noqa: D401
    """Return *True* if *story_title* already used for *college* essays."""

    profile = SimpleMemory.load(user_id)

    for rec in profile.essay_history:
        if rec.platform != college:
            continue
        for ver in rec.versions:
            if story_title in ver.used_stories:
                return True
    return False


# ---------------------------------------------------------------------------
# Essay-record helpers (used by memory-integrated tools)
# ---------------------------------------------------------------------------

def ensure_essay_record(user_id: str, prompt_text: str) -> EssayRecord:  # noqa: D401
    """Return existing :class:`EssayRecord` for *prompt_text* or create one.

    Created record is persisted immediately with status="outline" so that
    later tools (draft, revise, polish) can safely append versions.
    """

    profile = SimpleMemory.load(user_id)

    # Return existing record when prompt matches ---------------------------
    for rec in profile.essay_history:
        if rec.prompt_text == prompt_text:
            return rec

    # Otherwise create a skeleton record -----------------------------------
    rec = EssayRecord(
        prompt_id=f"essay_{len(profile.essay_history)+1}",
        prompt_text=prompt_text,
        platform="generic",
        status="outline",
    )
    profile.essay_history.append(rec)
    SimpleMemory.save(user_id, profile)
    return rec


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _default_profile() -> UserProfile:  # noqa: D401
    """Return minimally valid empty :class:`UserProfile`."""

    from .user_profile_schema import (
        UserInfo,
        AcademicProfile,
    )

    info = UserInfo(
        name="", grade=0, intended_major="", college_list=[], platforms=[]
    )
    acad = AcademicProfile(gpa=None, test_scores={}, courses=[], activities=[])
    return UserProfile(user_info=info, academic_profile=acad, core_values=[]) 