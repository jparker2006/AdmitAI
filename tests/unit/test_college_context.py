import os
from essay_agent.onboard import main as onboard_main
from essay_agent.intelligence.context_engine import ContextEngine
import asyncio

def test_context_engine_injects_college(monkeypatch):
    monkeypatch.setenv("ESSAY_AGENT_OFFLINE_TEST", "1")
    user_id = "pytest_college"
    # Onboard user -----------------------------------------------------------
    onboard_main(["--user", user_id, "--college", "Stanford", "--essay-prompt", "Identity prompt"])
    # Snapshot ---------------------------------------------------------------
    ctx_engine = ContextEngine(user_id)
    snap = asyncio.run(ctx_engine.snapshot())
    assert snap.college_context.get("school") == "Stanford" 