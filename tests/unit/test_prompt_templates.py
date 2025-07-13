import re
from essay_agent.prompts import (
    make_prompt,
    make_chat_prompt,
    make_few_shot_prompt,
    render_template,
    META_VARS,
)


def test_render_basic_prompt():
    tpl = make_prompt("Hello {name}, today is {today}.")
    rendered = render_template(tpl, name="Alice")
    assert "Alice" in rendered
    assert META_VARS["today"] in rendered


def test_chat_prompt_messages():
    chat_tpl = make_chat_prompt(
        system_str="System date {today}",
        human_str="Hi {name}!",
    )
    messages = render_template(chat_tpl, name="Bob")
    assert len(messages) == 2
    assert META_VARS["today"] in messages[0].content
    assert "Bob" in messages[1].content


def test_few_shot_prompt():
    examples = [
        {"question": "2+2", "answer": "4"},
        {"question": "3+3", "answer": "6"},
    ]
    example_template = "Q: {question}\nA: {answer}"
    suffix = "Q: {query}\nA:"
    fs_tpl = make_few_shot_prompt(
        examples=examples,
        example_template=example_template,
        suffix=suffix,
    )
    rendered = render_template(fs_tpl, query="5+5")
    # Should contain both examples and the new query
    assert "2+2" in rendered and "3+3" in rendered and "5+5" in rendered


def test_missing_variable_raises():
    tpl = make_prompt("Hello {missing_var}")
    import pytest

    with pytest.raises(ValueError):
        _ = render_template(tpl) 