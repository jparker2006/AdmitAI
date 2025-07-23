"""essay_agent.memory.smart_memory

Foundation layer for Section 2.2 – wraps HierarchicalMemory and adds
place-holders for preference learning, story reuse, and tool statistics.
Current chunk provides persistence scaffolding only (no advanced learning).
"""
from __future__ import annotations

from typing import Any, Dict, List
import logging

from essay_agent.memory.hierarchical import HierarchicalMemory
from essay_agent.memory.user_profile_schema import UserProfile
from essay_agent.memory.simple_memory import SimpleMemory

logger = logging.getLogger(__name__)


class SmartMemory(HierarchicalMemory):
    """HierarchicalMemory + lightweight preference & stats persistence.

    Later chunks will implement real learning; for now we just expose
    dictionaries and make sure they are stored / loaded safely.
    """

    _PREF_KEY = "preferences"
    _STATS_KEY = "tool_stats"

    def __init__(self, user_id: str, k: int = 6):
        super().__init__(user_id, k=k)
        # Ensure preference / stats keys exist --------------------------------
        self._ensure_extra_fields()

    # ------------------------------------------------------------------
    # Public getters ----------------------------------------------------
    # ------------------------------------------------------------------
    @property
    def preferences(self) -> Dict[str, Any]:  # noqa: D401
        # Store preferences on the memory instance to avoid mutating dataclass
        return self.__dict__.setdefault(self._PREF_KEY, {})  # type: ignore[index]

    @property
    def tool_stats(self) -> Dict[str, Any]:  # noqa: D401
        return self.__dict__.setdefault(self._STATS_KEY, {})  # type: ignore[index]

    # ------------------------------------------------------------------
    # Learning stubs (will be expanded in next chunk) -------------------
    # ------------------------------------------------------------------
    def learn(self, turn: Dict[str, Any]) -> None:  # noqa: D401
        """Lightweight learning on each conversation turn.

        Extracts user preference cues and tracks tool usage / success.
        Expected ``turn`` keys:
          - user_input: str
          - agent_response: str
          - tool_result: {type, tool_name, error?}
        """
        user_inp = str(turn.get("user_input", "")).lower()

        # ----------------- Preference detection -------------------------
        prefs_changed = False
        if any(word in user_inp for word in ["casual tone", "friendly tone", "casual voice"]):
            self.preferences["tone"] = "casual"
            prefs_changed = True
        elif any(word in user_inp for word in ["formal tone", "academic tone", "professional tone"]):
            self.preferences["tone"] = "formal"
            prefs_changed = True

        # Word-count hint e.g. "~650 words" or "in 500 words"
        import re

        match = re.search(r"(\d{3})\s*words", user_inp)
        if match:
            self.preferences["preferred_word_count"] = int(match.group(1))
            prefs_changed = True

        # Target school mention (very naive)
        for school in ["stanford", "harvard", "mit", "berkeley"]:
            if school in user_inp:
                ts = self.preferences.setdefault("target_schools", set())  # type: ignore[var-annotated]
                # If the stored value is a list (after JSON reload), cast to set first
                if isinstance(ts, list):
                    ts = set(ts)
                ts.add(school.title())
                self.preferences["target_schools"] = ts
                prefs_changed = True

        # ----------------- Tool statistics -----------------------------
        tool_res = turn.get("tool_result", {}) or {}
        tool_name = tool_res.get("tool_name")
        if tool_name:
            stats = self.tool_stats.setdefault(tool_name, {"usage_count": 0, "success_count": 0})
            stats["usage_count"] += 1  # type: ignore[index]
            if not tool_res.get("error"):
                stats["success_count"] += 1  # type: ignore[index]
            prefs_changed = True

        if prefs_changed:
            # Convert any set→list for JSON
            if isinstance(self.preferences.get("target_schools"), set):
                self.preferences["target_schools"] = list(self.preferences["target_schools"])  # type: ignore[index]
            self._save_extra()

    # ------------------------------------------------------------------
    # Convenience accessor (used by AutonomousEssayAgent) --------------
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any | None = None) -> Any:  # noqa: D401
        """Return a value from stored profile extras or preferences.

        Implements the minimal mapping interface expected by agent code
        (e.g. ``self.memory.get("college")``). It checks, in order:

        1. ``UserProfile.model_extra`` – where onboarding stores *college*
           and *essay_prompt* fields.
        2. ``preferences`` – dynamic prefs learned during conversation.
        3. Fallback *default* value.
        """

        # Pydantic v2 stores unknown fields in "__pydantic_extra__" whereas
        # earlier versions (or our legacy JSON) use "model_extra".  Support
        # both so that callers do not need to know the underlying version.

        extra: Dict[str, Any] = {}

        # v2 attribute ---------------------------------------------------
        extra_v2 = getattr(self.profile, "__pydantic_extra__", None)
        if isinstance(extra_v2, dict):
            extra.update(extra_v2)

        # Legacy attribute ----------------------------------------------
        extra_legacy = getattr(self.profile, "model_extra", None)
        if isinstance(extra_legacy, dict):
            extra.update(extra_legacy)

        if key in extra:
            return extra[key]
        if key in self.preferences:
            return self.preferences[key]
        return default

    # ------------------------------------------------------------------
    # Helper to _store_ extras (shared by set) -------------------------
    # ------------------------------------------------------------------
    def _update_extras(self, **kwargs):  # noqa: D401
        """Merge *kwargs* into both possible extra containers."""

        # Merge for v2
        extra_v2 = getattr(self.profile, "__pydantic_extra__", None) or {}
        extra_v2.update(kwargs)
        try:
            object.__setattr__(self.profile, "__pydantic_extra__", extra_v2)
        except Exception:
            pass  # ignore if attribute not present

        # Merge for legacy
        extra_legacy = getattr(self.profile, "model_extra", None) or {}
        extra_legacy.update(kwargs)
        try:
            object.__setattr__(self.profile, "model_extra", extra_legacy)  # type: ignore[attr-defined]
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internal helpers --------------------------------------------------
    # ------------------------------------------------------------------
    def _ensure_extra_fields(self) -> None:  # noqa: D401
        # No-op now; preferences/tool_stats stored on SmartMemory instance
        pass

    def _save_extra(self) -> None:  # noqa: D401
        try:
            self.save()
        except Exception as exc:  # noqa: BLE001
            logger.warning("SmartMemory save failed: %s", exc)

    # ------------------------------------------------------------------
    # Mutator helper ----------------------------------------------------
    # ------------------------------------------------------------------
    def set(self, key: str, value: Any) -> None:  # noqa: D401
        """Persist *key* → *value* inside profile extras and save."""

        self._update_extras(**{key: value})
        # Persist update
        self.save() 

    def add_message(self, role: str, content: str) -> None:
        """Adds a message to the working conversation memory."""
        if role == "user":
            self.working.chat_memory.add_user_message(content)
        elif role == "assistant":
            self.working.chat_memory.add_ai_message(content)
        else:
            logger.warning(f"Unknown role '{role}' for memory message.")
        # Manually trigger the save method of JSONConversationMemory
        self.working._save()

    def get_recent_chat(self, k: int = 3) -> List[Dict[str, str]]:
        """Retrieves the last k messages from the working memory, formatted for the planner."""
        from langchain_core.messages import HumanMessage, AIMessage

        messages = self.working.chat_memory.messages[-k:]
        formatted_messages = []
        for msg in messages:
            role = "unknown"
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            formatted_messages.append({"role": role, "content": msg.content})
        return formatted_messages 