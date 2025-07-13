import pytest

from essay_agent.tools.echo import EchoTool


def test_echo_default():
    tool = EchoTool()
    assert tool() == {"echo": "Hello, Essay Agent!"}


def test_echo_custom_message():
    tool = EchoTool()
    assert tool(message="Hi") == {"echo": "Hi"}


def test_echo_invalid_message():
    tool = EchoTool()
    with pytest.raises(ValueError):
        tool(message="   ") 