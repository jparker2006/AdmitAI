from langgraph.graph import StateGraph, END
import asyncio
import pytest

from essay_agent.agents.base import AgentState, BaseLangGraphAgent
from essay_agent.agents.communication import (
    ensure_queue,
    MessageEnvelope,
    push_message,
    pop_messages,
)


@pytest.mark.asyncio
async def test_message_flow():  # noqa: D401
    """AgentA broadcasts, AgentB receives & responds directly."""

    sg: StateGraph[dict] = StateGraph(dict)

    async def agent_a(state: dict):  # noqa: D401
        q = ensure_queue(state)
        push_message(q, MessageEnvelope(sender="A", broadcast=True, content="ping"))
        return state

    async def agent_b(state: dict):  # noqa: D401
        q = ensure_queue(state)
        msgs = pop_messages(q, "B")
        assert msgs and msgs[0].content == "ping"
        # respond directly
        push_message(q, MessageEnvelope(sender="B", receivers=["A"], content="pong"))
        return state

    async def agent_a_receive(state: dict):  # noqa: D401
        q = ensure_queue(state)
        msgs = pop_messages(q, "A")
        # ensure pong received
        assert any(m.content == "pong" for m in msgs)
        return state

    sg.add_node("A_send", agent_a)
    sg.add_node("B_recv", agent_b)
    sg.add_node("A_recv", agent_a_receive)

    sg.set_entry_point("A_send")
    sg.add_edge("A_send", "B_recv")
    sg.add_edge("B_recv", "A_recv")
    sg.add_edge("A_recv", END)

    graph = sg.compile()

    final_state = await graph.ainvoke({})
    assert "errors" not in final_state or not final_state["errors"] 