from __future__ import annotations

"""LangChain-compatible JSON conversation memory.

Combines an in-memory ``ConversationBufferMemory`` with a lightweight
summary mechanism and persists both the chat history and summary to disk
as JSON. This avoids network calls so tests can run offline.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from filelock import FileLock
from pydantic import PrivateAttr
# LangChain 0.1+ imports -----------------------------------------------------
# BaseChatMemory is still valid, but ChatMessageHistory moved to core chat history.
from langchain.memory.chat_memory import BaseChatMemory
from langchain.memory import ConversationBufferMemory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain.schema import BaseMessage

from . import _profile_path  # reuse helper & storage dir

__all__ = ["JSONConversationMemory"]


class JSONConversationMemory(BaseChatMemory):
    """Custom memory class persisting buffer + summary for each user.

    Private attributes are excluded from pydantic's public schema to avoid
    accidental serialization of large chat histories.
    """

    # ------------------------------------------------------------------
    # Pydantic public fields
    # ------------------------------------------------------------------

    memory_key: str = "chat_history"

    # ------------------------------------------------------------------
    # Private runtime attributes (excluded from .dict(), .json(), etc.)
    # ------------------------------------------------------------------

    _user_id: str = PrivateAttr()
    _k: int = PrivateAttr()
    _buffer_memory: ConversationBufferMemory = PrivateAttr()
    summary: str = PrivateAttr(default="")
    _path: Path = PrivateAttr()
    _lock: FileLock = PrivateAttr()

    def __init__(self, user_id: str, k: int = 6, **kwargs):
        """Create a new JSONConversationMemory instance.

        Args:
            user_id: Unique identifier for the user (used as filename stem).
            k: Number of recent messages to include in naive summary fallback.
        """

        super().__init__(**kwargs)

        # Store private attributes -------------------------------------------------
        object.__setattr__(self, "_user_id", user_id)
        object.__setattr__(self, "_k", k)
        object.__setattr__(self, "_buffer_memory", ConversationBufferMemory(return_messages=True))

        # Simple scalar summary (updated on each save_context call)
        object.__setattr__(self, "summary", "")

        # Persistence helpers ------------------------------------------------------
        path = _profile_path(user_id).with_suffix(".conv.json")
        lock = FileLock(str(path) + ".lock")
        object.__setattr__(self, "_path", path)
        object.__setattr__(self, "_lock", lock)

        # Attempt to load existing conversation state -----------------------------
        if self._path.exists():
            self._load()

    # ---------------------------------------------------------------------
    # BaseMemory protocol implementation
    # ---------------------------------------------------------------------

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key, "summary"]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Return chat history & summary for prompt formatting."""
        history = self._buffer_memory.chat_memory.messages  # type: ignore[attr-defined]
        return {
            self.memory_key: history,
            "summary": self.summary,
        }

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Add a new turn to memory and persist to disk.

        To be safe under concurrent writes we *first* reload the latest state
        from disk (under the same file lock) before appending the new user/AI
        messages. This guarantees that no turns are accidentally clobbered when
        multiple threads or processes write at nearly the same time.
        """

        # Refresh in-memory state ---------------------------------------------------
        if self._path.exists():
            self._load()

        # Append the new turn -------------------------------------------------------
        self._buffer_memory.save_context(inputs, outputs)
        # Naive summary: join last _k human/ai messages as plain text
        recent = self._buffer_memory.chat_memory.messages[-self._k :]
        object.__setattr__(self, "summary", " \n".join([m.content for m in recent]))
        self._save()

    def clear(self) -> None:
        self._buffer_memory.clear()
        object.__setattr__(self, "summary", "")

        # Overwrite file with empty state ----------------------------------------
        self._path.parent.mkdir(exist_ok=True)
        with self._lock:
            self._path.write_text(json.dumps({"chat_history": [], "summary": ""}, indent=2))

    # ------------------------------------------------------------------
    # Backwards-compatibility accessors
    # ------------------------------------------------------------------

    @property
    def buffer_memory(self) -> ConversationBufferMemory:  # noqa: D401
        """Expose the internal :class:`ConversationBufferMemory` instance.

        Older code (and some tests) expect a public ``buffer_memory`` attribute.
        Keeping this as a read-only property avoids breaking changes while still
        treating the actual object as a private attribute for pydantic.
        """

        return self._buffer_memory

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _to_dict(self) -> Dict[str, Any]:
        return {
            "chat_history": [m.dict() for m in self._buffer_memory.chat_memory.messages],  # type: ignore[attr-defined]
            "summary": self.summary,
        }

    def _load(self) -> None:
        with self._lock:
            data = json.loads(self._path.read_text())
        # restore history
        messages = [BaseMessage(**m) for m in data.get("chat_history", [])]
        # Recreate chat history ----------------------------------------------------
        chat_history = InMemoryChatMessageHistory(messages=messages)
        self._buffer_memory.chat_memory = chat_history  # type: ignore[attr-defined]
        object.__setattr__(self, "summary", data.get("summary", ""))

    def _save(self) -> None:
        self._path.parent.mkdir(exist_ok=True)

        with self._lock:
            if self._path.exists():
                existing = json.loads(self._path.read_text())
                existing_history = existing.get("chat_history", [])
            else:
                existing_history = []

            # Convert current messages to dicts -----------------------------------
            current_history = [m.dict() for m in self._buffer_memory.chat_memory.messages]  # type: ignore[attr-defined]

            # Append any messages not yet on disk ---------------------------------
            merged_history = list(existing_history)
            for msg in current_history:
                if msg not in existing_history:
                    merged_history.append(msg)

            payload = {"chat_history": merged_history, "summary": self.summary}
            self._path.write_text(json.dumps(payload, indent=2, default=str)) 