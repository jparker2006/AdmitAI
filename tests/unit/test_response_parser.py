import json

import pytest

from essay_agent.response_parser import (
    JsonResponse,
    pydantic_parser,
    schema_parser,
    safe_parse,
    ParseError,
)


def test_pydantic_success():
    parser = pydantic_parser(JsonResponse)
    obj = safe_parse(parser, json.dumps({"result": "OK"}))
    assert obj.result == "OK"


def test_schema_success():
    schema = {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    }
    parser = schema_parser(schema)
    output = safe_parse(parser, json.dumps({"summary": "hello"}))
    assert output["summary"] == "hello"


def test_safe_parse_retry(monkeypatch):
    # First parse fails; fixing parser returns corrected JSON
    class FailingParser:
        def __init__(self):
            self.calls = 0

        def parse(self, text):  # noqa: D401
            self.calls += 1
            raise ValueError("bad")

    # Provide DummyFixer with parse method
    class DummyFixer:
        def parse(self, text):  # noqa: D401
            return json.dumps({"result": "FIXED"})

    # Ensure OutputFixingParser has from_llm attribute for this test
    import essay_agent.response_parser as rp

    monkeypatch.setattr(rp, "OutputFixingParser", type("_X", (), {"from_llm": staticmethod(lambda p, llm: DummyFixer())}))
    monkeypatch.setattr(rp, "get_chat_llm", lambda **_: object())

    # Use parser that always fails first
    class SimpleParser:
        def __init__(self):
            self.called = False

        def parse(self, text):  # noqa: D401
            if not self.called:
                self.called = True
                raise ValueError("bad")
            return JsonResponse(result="FIXED")

    sp = SimpleParser()
    result = safe_parse(sp, "garbage", retries=1)
    assert result.result == "FIXED"


def test_parse_error_raises():
    class BadParser:
        def parse(self, text):  # noqa: D401
            raise ValueError("no")

    with pytest.raises(ParseError):
        _ = safe_parse(BadParser(), "bad", retries=0) 