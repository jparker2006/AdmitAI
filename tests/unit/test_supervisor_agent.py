import pytest

from essay_agent.agents.supervisor import SupervisorAgent
from essay_agent.agents.base import AgentState


class DummyState(AgentState):
    """Helper subclass to bypass BaseLangGraphAgent metaclass registration in tests."""


def test_supervisor_happy_path(monkeypatch):
    # Patch sub-agent ainvoke methods ----------------------------------------
    sup = SupervisorAgent()

    async def _ok(state):  # noqa: D401
        return AgentState(data={"done": True})

    monkeypatch.setattr(sup.research, "ainvoke", _ok)
    monkeypatch.setattr(sup.structure, "ainvoke", _ok)
    monkeypatch.setattr(sup.style, "ainvoke", _ok)

    init_state = AgentState(data={"essay_prompt": "x"})
    result_state = sup.invoke(init_state)

    assert result_state.errors == []
    assert result_state.data["done"] is True


def test_supervisor_stops_on_error(monkeypatch):
    sup = SupervisorAgent()

    async def _fail(state):  # noqa: D401
        st = AgentState(errors=["boom"], data={})
        return st

    async def _should_not_run(state):  # noqa: D401
        raise AssertionError("Should not run when previous phase errored")

    monkeypatch.setattr(sup.research, "ainvoke", _fail)
    monkeypatch.setattr(sup.structure, "ainvoke", _should_not_run)

    init_state = AgentState(data={"essay_prompt": "x"})
    result_state = sup.invoke(init_state)

    assert "boom" in result_state.errors 