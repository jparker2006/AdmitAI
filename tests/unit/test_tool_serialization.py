import json, os, asyncio

import pytest

os.environ["ESSAY_AGENT_OFFLINE_TEST"] = "1"

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.tools.integration import build_params, execute_tool

@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", list(TOOL_REGISTRY.keys()))
async def test_tool_result_serializable(tool_name, monkeypatch):
    # Dummy SimpleMemory profile
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})

    params = build_params(tool_name, user_id="pytest", user_input="sample text", context={"selection": "text"})

    result = await execute_tool(tool_name, **params)
    # Ensure json serializable
    json.dumps(result) 


@pytest.mark.asyncio
async def test_plagiarism_check_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json

    result = await execute_tool(
        "plagiarism_check",
        essay="Sample essay text",
        context={},
        user_id="pytest",
    )
    json.dumps(result)


@pytest.mark.asyncio
async def test_expand_outline_section_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json

    result = await execute_tool(
        "expand_outline_section",
        outline_section="Hook",
        section_name="Introduction",
        voice_profile="authentic",
        target_words=50,
        user_id="pytest",
        context={},
    )
    json.dumps(result) 


@pytest.mark.asyncio
async def test_improve_opening_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "improve_opening",
        opening_sentence="It was dawn when the challenge began.",
        essay_context="Story about overcoming obstacles.",
        voice_profile="authentic",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_strengthen_voice_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "strengthen_voice",
        paragraph="I have always enjoyed science.",
        voice_profile="authentic",
        target_voice_traits="curious, reflective",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_weakness_highlight_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "weakness_highlight",
        essay_text="I learned a lot from this experience and became stronger.",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_cliche_detection_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "cliche_detection",
        essay_text="This experience changed my life and taught me to never give up.",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_alignment_check_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "alignment_check",
        essay_text="My background shaped my identity.",
        essay_prompt="Describe your identity.",
        user_id="pytest",
        context={},
    )
    json.dumps(res) 


@pytest.mark.asyncio
async def test_draft_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "draft",
        outline={"hook": "abc", "context": "def"},
        voice_profile="authentic",
        word_count=100,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_polish_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "polish",
        draft="This is my essay draft.",
        word_count=50,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_word_count_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "word_count",
        text="one two three four five",
        target=5,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_revise_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "revise",
        draft="This is my essay draft.",
        revision_focus="clarity",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_outline_generator_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "outline_generator",
        story="Story about perseverance",
        essay_prompt="Describe a challenge you faced.",
        word_count=650,
        user_id="pytest",
        context={},
    )
    json.dumps(res) 


@pytest.mark.asyncio
async def test_structure_validator_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    outline = {"hook": "Start", "context": "Background", "growth_moment": "Challenge", "reflection": "Lesson"}
    res = await execute_tool(
        "structure_validator",
        outline=outline,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_transition_suggestion_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    outline = {"hook": "Start", "context": "Background", "growth_moment": "Challenge", "reflection": "Lesson"}
    res = await execute_tool(
        "transition_suggestion",
        outline=outline,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_length_optimizer_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    outline = {"hook": "Start", "context": "Background", "growth_moment": "Challenge", "reflection": "Lesson"}
    res = await execute_tool(
        "length_optimizer",
        outline=outline,
        target_word_count=650,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_classify_prompt_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "classify_prompt",
        essay_prompt="Describe a challenge you overcame.",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_extract_requirements_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "extract_requirements",
        essay_prompt="Tell a story in under 250 words.",
        user_id="pytest",
        context={},
    )
    json.dumps(res) 


@pytest.mark.asyncio
async def test_suggest_strategy_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "suggest_strategy",
        essay_prompt="Describe an obstacle you overcame.",
        profile="student profile",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_detect_overlap_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    prev = ["Essay about sports", "Essay about music"]
    res = await execute_tool(
        "detect_overlap",
        story="Story about sports challenges",
        previous_essays=prev,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_suggest_stories_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "suggest_stories",
        essay_prompt="Describe your passion.",
        profile="student profile",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_match_story_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "match_story",
        story="Story about innovation",
        essay_prompt="Describe an innovative project.",
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_expand_story_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "expand_story",
        story_seed="When I built a robot in 10th grade science fair,",
        user_id="pytest",
        context={},
    )
    json.dumps(res) 


@pytest.mark.asyncio
async def test_validate_uniqueness_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "validate_uniqueness",
        story_angle="Unique perspective on robotics",
        previous_essays=["Generic robotics essay"],
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_fix_grammar_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    text = "This are bad grammar sentence."
    res = await execute_tool(
        "fix_grammar",
        essay_text=text,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_enhance_vocabulary_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    text = "I am happy."
    res = await execute_tool(
        "enhance_vocabulary",
        essay_text=text*10,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_check_consistency_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    text = "He runs. They were running."
    res = await execute_tool(
        "check_consistency",
        essay_text=text*10,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_optimize_word_count_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    text = "word "*150
    res = await execute_tool(
        "optimize_word_count",
        essay_text=text,
        target_words=100,
        user_id="pytest",
        context={},
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_outline_alignment_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "outline_alignment",
        essay="This is my essay.",
        context={},
        user_id="pytest",
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_final_polish_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "final_polish",
        essay="Draft essay",
        context={},
        user_id="pytest",
    )
    json.dumps(res)


@pytest.mark.asyncio
async def test_comprehensive_validation_serializable(monkeypatch):
    monkeypatch.setattr("essay_agent.tools.integration.SimpleMemory.load", lambda uid: {})
    from essay_agent.tools.integration import execute_tool
    import json
    res = await execute_tool(
        "comprehensive_validation",
        essay="This is my essay.",
        context={},
        user_id="pytest",
    )
    json.dumps(res) 