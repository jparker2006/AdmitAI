import pytest

from essay_agent.agents.communication import (
    MessageEnvelope,
    EventQueue,
    push_message,
    pop_messages,
    resolve_conflicts,
)


def test_message_validation():
    # broadcast False with receivers
    msg = MessageEnvelope(sender="A", receivers=["B"], content="hi")
    assert msg.broadcast is False

    # broadcast True can have empty receivers
    msg2 = MessageEnvelope(sender="A", broadcast=True, content="all")
    assert msg2.receivers == []

    # invalid: no receivers & not broadcast
    with pytest.raises(ValueError):
        MessageEnvelope(sender="A", receivers=[], content="oops")


def test_queue_push_pop_direct():
    q = EventQueue()
    m1 = MessageEnvelope(sender="A", receivers=["B"], content="hello")
    push_message(q, m1)

    # nothing for C
    assert pop_messages(q, "C") == []

    # B receives message
    got = pop_messages(q, "B")
    assert got == [m1]
    # queue empty now
    assert q.pending == []


def test_queue_broadcast():
    q = EventQueue()
    m = MessageEnvelope(sender="A", broadcast=True, content="ping")
    push_message(q, m)

    got_b = pop_messages(q, "B")
    assert got_b == [m]
    # message removed after broadcast delivery
    assert q.pending == []


def test_conflict_resolution():
    state: dict = {"data": {"x": 1}}
    conflicts = resolve_conflicts(state, {"x": 2, "y": 3}, owner="Agent1")
    assert len(conflicts) == 1
    assert state["data"]["x"] == 1  # unchanged
    assert state["data"]["y"] == 3
    assert "errors" in state 