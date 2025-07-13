from essay_agent.prompts.brainstorm import BRAINSTORM_PROMPT
from essay_agent.tools.brainstorm import BrainstormTool
from essay_agent.tools import REGISTRY
from langchain.llms.fake import FakeListLLM
import json, pytest

def test_prompt_variables():
    required = {"essay_prompt", "profile", "today"}
    assert required.issubset(set(BRAINSTORM_PROMPT.input_variables))

def test_brainstorm_tool_offline(monkeypatch):
    fake_output = {
        "stories": [
            {"title": "Debate Leap", "description": "Desc1", "prompt_fit": "fit", "insights": ["Res"]},
            {"title": "Market", "description": "Desc2", "prompt_fit": "fit", "insights": ["Lead"]},
            {"title": "Science Fair", "description": "Desc3", "prompt_fit": "fit", "insights": ["Curiosity"]},
        ]
    }
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.brainstorm.get_chat_llm", lambda **_: fake_llm)

    tool = BrainstormTool()
    result = tool(essay_prompt="Describe a challenge you overcame.", profile="Immigrant student")

    assert result["ok"]["stories"][0]["title"] == "Debate Leap"
    # Ensure registry wired
    registry_result = REGISTRY.call(
        "brainstorm", essay_prompt="Describe a challenge", profile="Immigrant"
    )
    assert "stories" in registry_result["ok"] 