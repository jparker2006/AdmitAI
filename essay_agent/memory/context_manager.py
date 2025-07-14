from __future__ import annotations

"""essay_agent.memory.context_manager

Advanced conversation context window management that combines a running
summary with a token-bounded message buffer, and supports multiple essay
sessions per user.
"""

from pathlib import Path
import json
import logging
from typing import Any, Dict, List, Tuple

import tiktoken
from filelock import FileLock
from pydantic import BaseModel, Field, field_validator

from langchain.memory import ConversationTokenBufferMemory

__all__ = ["ContextManagerError", "ContextWindowManager"]

logger = logging.getLogger(__name__)
DEFAULT_DIR = Path("memory_store")
DEFAULT_DIR.mkdir(exist_ok=True)


class ContextManagerError(RuntimeError):
    """Raised on persistence / serialization failures."""


class _SessionState(BaseModel):
    """Persisted representation of a single essay session."""

    summary: str = ""
    messages: List[Dict[str, str]] = Field(default_factory=list)

    @field_validator("messages")
    @classmethod
    def _validate_msgs(cls, v):  # noqa: D401
        for m in v:
            if not {"role", "content"}.issubset(m):
                raise ValueError("Each message must have 'role' and 'content'")
        return list(v)


class ContextWindowManager:  # pylint: disable=too-many-instance-attributes
    """Manage conversation context with token budget & per-essay sessions."""

    _ENCODING_FALLBACK = "cl100k_base"

    def __init__(
        self,
        user_id: str,
        essay_id: str,
        *,
        max_tokens: int = 3000,
        summary_max_tokens: int = 400,
        model_name: str = "gpt-4o",
        storage_dir: Path | str = DEFAULT_DIR,
    ) -> None:
        self.user_id = user_id
        self.essay_id = essay_id
        self.max_tokens = max_tokens
        self.summary_max_tokens = summary_max_tokens
        self.model_name = model_name
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        # tiktoken encoding ---------------------------------------------------
        try:
            self._enc = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self._enc = tiktoken.get_encoding(self._ENCODING_FALLBACK)
            logger.warning("Encoding for %s not found; using %s", model_name, self._ENCODING_FALLBACK)

        # Load state -----------------------------------------------------------
        self._state: _SessionState = self._load_state()

    # ---------------------------------------------------------------------
    # Public properties
    # ---------------------------------------------------------------------

    @property
    def summary(self) -> str:  # noqa: D401
        return self._state.summary

    @property
    def messages(self) -> List[Dict[str, str]]:  # noqa: D401
        return self._state.messages

    @property
    def token_count(self) -> int:  # noqa: D401
        msgs_tokens = sum(self._count_tokens(m["content"]) for m in self._state.messages)
        return msgs_tokens + self._count_tokens(self._state.summary)

    # ---------------------------------------------------------------------
    # Message helpers
    # ---------------------------------------------------------------------

    def add_user(self, content: str) -> None:
        self._add("user", content)

    def add_ai(self, content: str) -> None:
        self._add("ai", content)

    # ---------------------------------------------------------------------
    # Session management
    # ---------------------------------------------------------------------

    def switch_session(self, essay_id: str) -> None:  # noqa: D401
        """Persist current session and load *essay_id* session."""

        self._save_state()
        self.essay_id = essay_id
        self._state = self._load_state()

    # ---------------------------------------------------------------------
    # LangChain compatibility
    # ---------------------------------------------------------------------

    def lc_memory(self) -> ConversationTokenBufferMemory:  # noqa: D401
        """Return LangChain memory primed with summary + recent messages."""

        mem = ConversationTokenBufferMemory(max_token_limit=self.max_tokens, return_messages=True)
        # inject summary at beginning (system message style)
        if self.summary:
            mem.chat_memory.add_ai_message(f"SUMMARY: {self.summary}")
        for m in self._state.messages:
            if m["role"] == "user":
                mem.chat_memory.add_user_message(m["content"])
            else:
                mem.chat_memory.add_ai_message(m["content"])
        return mem

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _add(self, role: str, content: str) -> None:
        content = str(content).strip()
        if not content:
            raise ValueError("Message content must be non-empty")

        self._state.messages.append({"role": role, "content": content})
        self._enforce_budget()
        self._save_state()

    def _enforce_budget(self) -> None:
        """Summarise & trim until token budget satisfied."""

        while self.token_count > self.max_tokens and self._state.messages:
            # Pop oldest message
            popped = self._state.messages.pop(0)
            # Append to summary (naive concatenation w/ delimiter)
            add_text = f"[{popped['role']}] {popped['content']}"
            self._state.summary = (self._state.summary + " \n" + add_text).strip()
            # Truncate summary itself if it grows beyond summary_max_tokens
            while self._count_tokens(self._state.summary) > self.summary_max_tokens:
                # Drop earliest sentences – simplest: drop first 20 tokens
                toks = self._enc.encode(self._state.summary)
                toks = toks[20:]
                self._state.summary = self._enc.decode(toks)

    # --------------------- persistence ---------------------------

    def _file_path(self) -> Path:
        stem = f"{self.user_id}.{self.essay_id}.ctx.json"
        return self.storage_dir / stem

    def _load_state(self) -> _SessionState:
        path = self._file_path()
        if not path.exists():
            return _SessionState()
        try:
            with FileLock(str(path) + ".lock"):
                raw = json.loads(path.read_text())
            return _SessionState(**raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load context state: %s", exc)
            return _SessionState()

    def _save_state(self) -> None:
        path = self._file_path()
        data = self._state.model_dump(mode="json")
        try:
            with FileLock(str(path) + ".lock"):
                path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to save context state: %s", exc)
            raise ContextManagerError(str(exc)) from exc

    # --------------------- token helper --------------------------

    def _count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text)) 