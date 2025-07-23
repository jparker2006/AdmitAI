import os, sys, json, asyncio, subprocess
from pathlib import Path

import pytest

from essay_agent.onboard import main as onboard_main
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.agent_autonomous import AutonomousEssayAgent


@pytest.mark.integration
def test_resume_workflow_advances_status(tmp_path, monkeypatch):
    """Onboard → bootstrap → resume; ensure status advances and bootstrap not rerun."""

    user_id = "pytest_resume"
    memory_file = Path("memory_store") / f"{user_id}.json"
    if memory_file.exists():
        memory_file.unlink()

    # Offline mode env vars --------------------------------------------------
    monkeypatch.setenv("ESSAY_AGENT_OFFLINE_TEST", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")  # stub value

    # ----------------------------------------------------------------------
    # 1) Onboard
    # ----------------------------------------------------------------------
    onboard_args = [
        "--user", user_id,
        "--college", "Stanford",
        "--essay-prompt", "Tell us about your identity.",
    ]
    onboard_main(onboard_args)

    # ----------------------------------------------------------------------
    # 2) Run bootstrap (brainstorm → outline)
    # ----------------------------------------------------------------------
    agent = AutonomousEssayAgent(user_id=user_id)
    ran_bootstrap = asyncio.run(agent.orchestrator.bootstrap_if_needed())
    assert ran_bootstrap is True

    profile_after_bootstrap = SimpleMemory.load(user_id)
    assert profile_after_bootstrap.essay_history[0].status == "outline"

    # ----------------------------------------------------------------------
    # 3) CLI resume command (should NOT trigger bootstrap again)
    # ----------------------------------------------------------------------
    env = os.environ.copy()
    env["ESSAY_AGENT_OFFLINE_TEST"] = "1"
    env.setdefault("OPENAI_API_KEY", "sk-test")

    result = subprocess.run(
        [sys.executable, "-m", "essay_agent.cli", "resume", "--user", user_id, "--json"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    output = json.loads(result.stdout.strip())
    assert output["bootstrap_ran"] is False

    # Status should have advanced beyond outline
    profile_final = SimpleMemory.load(user_id)
    assert profile_final.essay_history[0].status in {"draft", "revision", "complete"} 