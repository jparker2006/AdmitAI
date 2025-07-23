import os, asyncio
from pathlib import Path

import pytest

from essay_agent.onboard import main as onboard_main
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.agent_autonomous import AutonomousEssayAgent


@pytest.mark.integration
def test_offline_bootstrap_generates_outline(tmp_path, monkeypatch):
    """End-to-end offline flow: onboarding → bootstrap brainstorm/outline."""

    # Isolation -------------------------------------------------------------
    user_id = "pytest_flow"
    memory_file = Path("memory_store") / f"{user_id}.json"
    if memory_file.exists():
        memory_file.unlink()

    # Offline environment variables ----------------------------------------
    monkeypatch.setenv("ESSAY_AGENT_OFFLINE_TEST", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")  # not used in offline mode

    # ----------------------------------------------------------------------
    # 1) Onboard user
    # ----------------------------------------------------------------------
    onboard_args = [
        "--user", user_id,
        "--college", "Stanford",
        "--essay-prompt", "Tell us about your identity.",
    ]
    onboard_main(onboard_args)

    # Basic sanity check
    profile = SimpleMemory.load(user_id)
    assert getattr(profile, "model_extra", {}).get("college") == "Stanford"

    # ----------------------------------------------------------------------
    # 2) Create agent & run bootstrap
    # ----------------------------------------------------------------------
    agent = AutonomousEssayAgent(user_id=user_id)
    ran = asyncio.run(agent.orchestrator.bootstrap_if_needed())
    assert ran is True

    # ----------------------------------------------------------------------
    # 3) Verify outline exists in memory
    # ----------------------------------------------------------------------
    profile_after = SimpleMemory.load(user_id)
    assert profile_after.essay_history, "Essay history should not be empty after bootstrap"
    first_rec = profile_after.essay_history[0]
    assert first_rec.status == "outline"
    # At least one tool step should have produced content – we check brainstorm result stored in context maybe versions
    # Versions may be empty in offline stub; we just ensure bootstrap ran. 