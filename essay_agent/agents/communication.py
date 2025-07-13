"""essay_agent.agents.communication

Light-weight message-passing primitives used by LangGraph agents.
These utilities are **independent** from any concrete agent implementation;
any node can import and use them to exchange information by mutating the
shared state dict that flows through a LangGraph `StateGraph`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from pydantic import BaseModel, Field, validator

from essay_agent.agents.base import AgentState  # circular safe (runtime)


# ---------------------------------------------------------------------------
# Core message / event models
# ---------------------------------------------------------------------------

class MessageEnvelope(BaseModel):  # noqa: D401
    """Structured message exchanged between agents.

    • *broadcast* = True  → deliver to **all** agents except the sender
      (``receivers`` list can be empty in this case).
    • If *broadcast* is False, ``receivers`` **must** be non-empty.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    broadcast: bool = False
    receivers: List[str] = Field(default_factory=list)
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @validator("receivers", always=True)
    @classmethod
    def _validate_receivers(cls, v, values):  # noqa: D401
        broadcast_flag = values.get("broadcast", False)
        if not broadcast_flag and not v:
            raise ValueError("receivers cannot be empty when broadcast is False")
        return v


class ConflictEvent(BaseModel):  # noqa: D401
    """Represents a key-collision conflict in shared state."""

    key: str
    previous_owner: str
    new_owner: str
    message: str


# ---------------------------------------------------------------------------
# Event queue
# ---------------------------------------------------------------------------

@dataclass
class EventQueue:  # noqa: D401
    """Simple FIFO queue for MessageEnvelope objects."""

    pending: List[MessageEnvelope] = field(default_factory=list)
    delivered: List[MessageEnvelope] = field(default_factory=list)

    # No custom methods here; helper functions below operate on the queue.


# ---------------------------------------------------------------------------
# Helper functions – stateless utilities operating on EventQueue
# ---------------------------------------------------------------------------


def push_message(queue: EventQueue, msg: MessageEnvelope) -> None:  # noqa: D401
    """Append *msg* to *queue.pending*."""

    queue.pending.append(msg)


def pop_messages(queue: EventQueue, receiver: str) -> List[MessageEnvelope]:  # noqa: D401
    """Remove & return messages addressed to *receiver*.

    Broadcast messages are delivered to **all** agents (except sender).
    Direct messages ({receiver} ∈ msg.receivers) are delivered exactly once.
    """

    deliver: List[MessageEnvelope] = []
    remaining: List[MessageEnvelope] = []

    for msg in queue.pending:
        should_deliver = (
            msg.broadcast and msg.sender != receiver
        ) or (
            not msg.broadcast and receiver in msg.receivers
        )

        if should_deliver:
            deliver.append(msg)
            # For direct messages, do not re-queue after delivery.
            # For broadcast, we still mark as delivered after first delivery
            # but do **not** deliver again in subsequent pop operations.
        else:
            remaining.append(msg)

    queue.pending = remaining
    queue.delivered.extend(deliver)
    return deliver


# ---------------------------------------------------------------------------
# Conflict-resolution helper
# ---------------------------------------------------------------------------


def resolve_conflicts(
    state: Dict[str, Any],
    new_data: Dict[str, Any],
    *,
    owner: str,
) -> List[ConflictEvent]:  # noqa: D401
    """Merge *new_data* into ``state["data"]`` with first-write-wins policy.

    If a key is already present, a :class:`ConflictEvent` is created and the
    incoming value is **ignored**.
    """

    conflicts: List[ConflictEvent] = []
    data_dict = state.setdefault("data", {})

    for k, v in new_data.items():
        if k in data_dict:
            conflicts.append(
                ConflictEvent(
                    key=k,
                    previous_owner=str(data_dict[k].get("_owner", "unknown"))
                    if isinstance(data_dict[k], dict)
                    else "unknown",
                    new_owner=owner,
                    message=f"Key '{k}' already set – keeping existing value",
                ),
            )
            continue

        # Store owner provenance for debugging
        if isinstance(v, dict):
            v["_owner"] = owner  # type: ignore[index]
        data_dict[k] = v

    # Dump conflict messages into state's errors list
    if conflicts:
        errs = state.setdefault("errors", [])
        errs.extend(evt.message for evt in conflicts)
    return conflicts


# ---------------------------------------------------------------------------
# Convenience: attach a fresh EventQueue to state if not present
# ---------------------------------------------------------------------------

def _state_dict(state: Dict[str, Any] | AgentState) -> Dict[str, Any]:  # noqa: D401
    """Return mutable dict representation of *state*."""

    return state.__dict__ if isinstance(state, AgentState) else state


def ensure_queue(state: Dict[str, Any] | AgentState) -> EventQueue:  # noqa: D401
    sdict = _state_dict(state)
    if "queue" not in sdict:
        sdict["queue"] = EventQueue()
    return sdict["queue"] 