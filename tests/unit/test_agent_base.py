import pytest

from essay_agent.agents.base import AgentMessage, AgentState, BaseLangGraphAgent
from langgraph.graph import StateGraph, END

# ---------------------------------------------------------------------------
# Dummy agent for tests ------------------------------------------------------
# ---------------------------------------------------------------------------

class PingAgent(BaseLangGraphAgent):
    """Agent that appends 'ping' to state.data."""

    def _build_graph(self):  # noqa: D401
        sg: StateGraph[dict] = StateGraph(dict)

        async def ping_node(state: dict):
            state.setdefault("data", {})["ping"] = True
            return state

        sg.add_node("ping", ping_node)
        sg.set_entry_point("ping")
        sg.add_edge("ping", END)
        return sg.compile()


def test_agent_message_validation():
    msg = AgentMessage(sender="a", receiver="b", content={"foo": 1})
    assert msg.sender == "a"
    assert msg.metadata == {}


def test_ping_agent_sync_vs_async():
    agent = PingAgent()
    import asyncio
    state_sync = agent.invoke()
    state_async = asyncio.run(agent.ainvoke())
    assert state_sync.data == state_async.data == {"ping": True} 