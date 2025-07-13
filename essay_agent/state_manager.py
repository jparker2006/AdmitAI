from __future__ import annotations

"""essay_agent.state_manager

ConversationStateManager maintains per-user conversation context using LangChain
ConversationBufferWindowMemory while enforcing a maximum token budget.

Key responsibilities
--------------------
1. Append / retrieve conversation messages (user & AI)
2. Persist state to disk so sessions survive restarts
3. Truncate history intelligently to keep within ``max_tokens``
4. Provide helpers to generate LangChain-compatible ``ConversationChain``
   instances and plain-dict snapshots for LangGraph state propagation.

Note
----
For the MVP we assume synchronous file I/O and local disk persistence. In
future phases this module can be upgraded to leverage a database or vector
store without changing the public API.
"""

from pathlib import Path
import json
import logging
from typing import Any, Dict, List, Sequence

import tiktoken
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import AIMessage, HumanMessage, BaseMessage
from pydantic import BaseModel, Field, field_validator

__all__ = [
    "ConversationStateError",
    "ConversationState",
    "ConversationStateManager",
]

logger = logging.getLogger(__name__)
DEFAULT_STORAGE_DIR = Path("memory_store")
DEFAULT_STORAGE_DIR.mkdir(exist_ok=True)


class ConversationStateError(RuntimeError):
    """Raised for serialization / persistence errors in ConversationStateManager."""


class ConversationState(BaseModel):
    """Pydantic model representing serialisable conversation state."""

    messages: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("messages")
    @classmethod
    def _validate_messages(cls, v: Sequence[Dict[str, str]]):  # noqa: D401, N805
        for msg in v:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each message must have 'role' and 'content'")
        return list(v)


class ConversationStateManager:  # pylint: disable=too-many-instance-attributes
    """High-level wrapper around :class:`ConversationState` with utility methods.

    Parameters
    ----------
    user_id
        Identifier under which state will be persisted. File path:
        ``<storage_dir>/<user_id>.conv.json``.
    model_name
        Name of the OpenAI model used for counting tokens. Defaults to GPT-4-o.
    max_tokens
        Soft cap on number of tokens kept in memory. Oldest messages are dropped
        once this budget is exceeded.
    window_size
        Number of recent messages that LangChain's ``ConversationBufferWindowMemory``
        should retain when generating replies.
    storage_dir
        Directory for JSON persistence. Created if missing.
    """

    _ENCODING_FALLBACK = "cl100k_base"

    def __init__(
        self,
        user_id: str,
        *,
        model_name: str = "gpt-4o",
        max_tokens: int = 3000,
        window_size: int = 12,
        storage_dir: Path | str = DEFAULT_STORAGE_DIR,
    ) -> None:
        self.user_id = user_id
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.window_size = window_size
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        # Attempt to load existing state from disk; else start empty.
        self.state: ConversationState = ConversationState()
        try:
            self.state = self._load_state()
        except ConversationStateError:
            # Log & start fresh but do not crash caller
            logger.exception("Failed to load state for user '%s' – starting new session", user_id)

        # Pre-compute tiktoken encoding (with fallback)
        try:
            self._encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self._encoding = tiktoken.get_encoding(self._ENCODING_FALLBACK)
            logger.warning("Model encoding for '%s' not found; falling back to %s", model_name, self._ENCODING_FALLBACK)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def messages(self) -> List[Dict[str, str]]:  # noqa: D401
        """Return list of message dicts in chronological order."""

        return self.state.messages

    @property
    def token_count(self) -> int:  # noqa: D401
        """Total tokens across all stored messages."""

        return sum(self._count_tokens(m["content"]) for m in self.state.messages)

    # -------------------------- add messages --------------------------

    def add_user(self, message: str) -> None:
        """Append a human message and persist state."""

        self._add_message("user", message)

    def add_ai(self, message: str) -> None:
        """Append an AI message and persist state."""

        self._add_message("ai", message)

    # -------------------------- retrieval -----------------------------

    def context_messages(self) -> List[BaseMessage]:  # noqa: D401
        """Return messages converted to LangChain ``BaseMessage`` objects."""

        lc_messages: List[BaseMessage] = []
        for m in self.state.messages:
            role = m["role"]
            content = m["content"]
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            else:
                lc_messages.append(AIMessage(content=content))
        return lc_messages

    def context_dict(self) -> Dict[str, Any]:  # noqa: D401
        """Serialisable snapshot for LangGraph state propagation."""

        return self.state.model_dump(mode="json")

    # -------------------------- LangChain helpers ---------------------

    def as_chain(self, llm, **chain_kwargs):  # noqa: D401, ANN001
        """Return initialised :class:`ConversationChain` using internal state."""

        memory = ConversationBufferWindowMemory(k=self.window_size, return_messages=True)
        memory.chat_memory.messages = self.context_messages()  # type: ignore[attr-defined]
        return ConversationChain(llm=llm, memory=memory, **chain_kwargs)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, user_id: str, **kwargs):  # noqa: D401, ANN001
        """Return manager populated from disk (or empty if file missing)."""

        return cls(user_id, **kwargs)

    def reset(self) -> None:  # noqa: D401
        """Remove all messages and overwrite persisted file."""

        self.state = ConversationState()
        self._save_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_message(self, role: str, content: str) -> None:
        content = str(content).strip()
        if not content:
            raise ValueError("Message must not be empty or whitespace.")

        self.state.messages.append({"role": role, "content": content})
        self._ensure_limit()
        self._save_state()

    def _ensure_limit(self) -> None:  # noqa: D401
        """Drop oldest messages until total tokens <= ``max_tokens``."""

        while self.token_count > self.max_tokens and self.state.messages:
            # Remove first (oldest) message
            self.state.messages.pop(0)

    # -------------------------- persistence ---------------------------

    def _file_path(self) -> Path:
        return self.storage_dir / f"{self.user_id}.conv.json"

    def _load_state(self) -> ConversationState:
        path = self._file_path()
        if not path.exists():
            return ConversationState()
        try:
            raw = json.loads(path.read_text())
            return ConversationState(**raw)
        except Exception as exc:  # noqa: BLE001
            raise ConversationStateError(str(exc)) from exc

    def _save_state(self) -> None:
        path = self._file_path()
        try:
            path.write_text(json.dumps(self.state.model_dump(mode="json"), indent=2))
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to save conversation state for user '%s': %s", self.user_id, exc)
            raise ConversationStateError(str(exc)) from exc

    # -------------------------- token counting ------------------------

    def _count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text)) 