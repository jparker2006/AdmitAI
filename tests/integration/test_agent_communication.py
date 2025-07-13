import asyncio

from essay_agent.agents.base import BaseLangGraphAgent, AgentState, AgentMessage
from langgraph.graph import StateGraph, END


class EchoAgent(BaseLangGraphAgent):
    def _build_graph(self):  # noqa: D401
        sg: StateGraph[dict] = StateGraph(dict)

        async def echo(state: dict):
            msg = state.get("last_message")
            if msg:
                state.setdefault("data", {})["echo"] = msg.content
            return state

        sg.add_node("echo", echo)
        sg.set_entry_point("echo")
        sg.add_edge("echo", END)
        return sg.compile()


class UpperAgent(BaseLangGraphAgent):
    def _build_graph(self):  # noqa: D401
        sg: StateGraph[dict] = StateGraph(dict)

        async def reverse(state: dict):
            txt = state.get("data", {}).get("echo", "")
            state.setdefault("data", {})["reversed"] = txt[::-1]
            return state

        async def upper(state: dict):
            txt = state.get("data", {}).get("reversed", "")
            state.setdefault("data", {})["upper"] = txt.upper()
            return state

        sg.add_node("reverse", reverse)
        sg.add_node("upper", upper)
        sg.set_entry_point("reverse")
        sg.add_edge("reverse", "upper")
        sg.add_edge("upper", END)
        return sg.compile()


def test_agent_chain_communication():
    init_state = AgentState(last_message=AgentMessage(sender="test", receiver="echo", content="hello"))

    echo_agent = EchoAgent()
    upper_agent = UpperAgent()

    # run echo
    state_after_echo = echo_agent.invoke(init_state)

    # pass to upper
    state_after_upper = upper_agent.invoke(state_after_echo)

    assert state_after_upper.data["upper"] == "OLLEH"
    assert not state_after_upper.errors 