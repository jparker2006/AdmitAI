from essay_agent.tools.base import _strip_fences

def test_strip_fences_json():
    raw = """```json\n{\n  \"foo\": 123\n}\n```"""
    assert _strip_fences(raw) == '{\n  "foo": 123\n}'


def test_strip_fences_no_fence():
    raw = '{"foo": 123}'
    assert _strip_fences(raw) == raw 