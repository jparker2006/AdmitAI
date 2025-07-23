"""essay_agent.intelligence.context_engine

ContextEngine – aggregates working, semantic and episodic memory plus school
context into a single Pydantic snapshot.  Used by AutonomousEssayAgent to gain
context awareness (Section 2.1).
"""
from __future__ import annotations

import time
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from essay_agent.memory.hierarchical import HierarchicalMemory
from essay_agent.memory.user_profile_schema import EssayRecord
try:
    from essay_agent.eval.college_prompts import get_prompt_by_id  # type: ignore
except ImportError:
    def get_prompt_by_id(prompt_id):  # fallback stub
        return None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic model
# ---------------------------------------------------------------------------

class ContextSnapshot(BaseModel):
    user_id: str
    user_profile: Dict[str, Any]
    recent_messages: List[str] = Field(default_factory=list)
    essay_state: Dict[str, Any] = Field(default_factory=dict)
    college_context: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    tool_stats: Dict[str, Any] = Field(default_factory=dict)
    session_info: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ContextEngine:
    """High-level helper that returns a cached ContextSnapshot per user."""

    _TTL = 30  # seconds

    def __init__(self, user_id: str, *, k: int = 4):
        self.user_id = user_id
        self._mem = HierarchicalMemory(user_id, k=k)
        self._cached: Optional[ContextSnapshot] = None
        self._cache_ts: float = 0.0

    async def snapshot(self, user_input: str = "") -> ContextSnapshot:  # noqa: D401
        now = time.time()
        if self._cached and now - self._cache_ts < self._TTL:
            return self._cached

        # Refresh hierarchical memory from disk
        self._mem.load()

        # Recent chat (working memory)
        recent = self._mem.get_recent_chat(k=4)

        # Essay state: pick latest record matching current prompt when possible
        essay_state: Dict[str, Any] = {}
        if self._mem.profile.essay_history:
            last_rec: EssayRecord = self._mem.profile.essay_history[-1]
            essay_state = {
                "prompt_text": last_rec.prompt_text,
                "status": last_rec.status,
            }
            if last_rec.versions:
                last_ver = last_rec.versions[-1]
                essay_state.update({
                    "outline": getattr(last_ver, "outline", None),
                    "draft": getattr(last_ver, "draft", None),
                })

        # College context – derived from prompt lookup OR persisted onboarding
        college_ctx: Dict[str, Any] = {}
        try:
            prompt_id = essay_state.get("prompt_text", "")
            if prompt_id:
                prompt_obj = get_prompt_by_id(prompt_id)  # type: ignore[arg-type]
                if prompt_obj:
                    college_ctx = {
                        "school": prompt_obj.school,
                        "word_limit": prompt_obj.word_limit,
                        "essay_prompt": prompt_obj.prompt,
                    }
        except Exception:
            pass

        # Fallback: use persisted onboarding data --------------------------
        try:
            # Merge extras from both Pydantic v2 (__pydantic_extra__) and legacy
            extra = {}
            extra_v2 = getattr(self._mem.profile, "__pydantic_extra__", None)
            if isinstance(extra_v2, dict):
                extra.update(extra_v2)

            extra_legacy = getattr(self._mem.profile, "model_extra", None)
            if isinstance(extra_legacy, dict):
                extra.update(extra_legacy)

            college_extra = extra.get("college")
            if college_extra and "school" not in college_ctx:
                college_ctx["school"] = college_extra
            prompt_extra = extra.get("essay_prompt")
            if prompt_extra and "essay_prompt" not in college_ctx:
                college_ctx["essay_prompt"] = prompt_extra
        except Exception:
            pass

        snap = ContextSnapshot(
            user_id=self.user_id,
            user_profile=self._mem.profile.model_dump() if hasattr(self._mem.profile, "model_dump") else {},
            recent_messages=recent,
            essay_state=essay_state,
            college_context=college_ctx,
            preferences=getattr(self._mem, "preferences", {}),
            tool_stats=getattr(self._mem, "tool_stats", {}),
            session_info={},  # agent fills in live
            timestamp=datetime.utcnow(),
        )

        self._cached = snap
        self._cache_ts = now
        return snap 