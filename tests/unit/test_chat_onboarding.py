import os, types, asyncio, argparse

from essay_agent.memory.smart_memory import SmartMemory

# Monkeypatch dependencies inside test function to avoid network & interactive loop

def test_chat_onboarding(monkeypatch, tmp_path):
    """Ensure chat command asks for prompt/college and saves them (offline)."""

    # Redirect memory root to temp dir
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    # Environment – offline deterministic testing
    monkeypatch.setenv("ESSAY_AGENT_OFFLINE_TEST", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Stub AutonomousEssayAgent to bypass network calls
    class _DummyAgent:
        def __init__(self, user_id):
            self.user_id = user_id
            self.orchestrator = types.SimpleNamespace(bootstrap_if_needed=lambda *_: False)
        async def handle_message(self, msg):
            return ""
    monkeypatch.setattr("essay_agent.cli.AutonomousEssayAgent", _DummyAgent)

    # Skip real conversation loop
    async def _noop_start(agent, args):
        return None
    monkeypatch.setattr("essay_agent.cli._start_react_conversation", _noop_start)

    # Provide interactive inputs (prompt then college)
    inputs = iter(["My challenge prompt", "Dream U"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # Build args namespace mimicking CLI parser output
    args = argparse.Namespace(
        user="unit_onboard_user",
        profile=None,
        prompt=None,
        college=None,
        shortcut=None,
        shortcuts=False,
        debug=False,
        show_prompts=False,
    )

    from essay_agent.cli import _cmd_chat

    asyncio.run(_cmd_chat(args))

    mem = SmartMemory("unit_onboard_user")
    assert mem.get("essay_prompt") == "My challenge prompt"
    assert mem.get("college") == "Dream U" 