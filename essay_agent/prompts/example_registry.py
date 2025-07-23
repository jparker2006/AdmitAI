EXAMPLE_REGISTRY = {
    "brainstorm": '{"stories":[{"title":"Fair Fail","description":"Project failed; adapted.","prompt_fit":"Shows resilience.","insights":["Resilience"],"themes":["challenge"]}]}',
    "outline": '{"outline":{"hook":"Hook line","context":"Context line","conflict":"Conflict line","growth":"Growth line","reflection":"Reflection line"},"estimated_word_count":650}',
    "match_story": '{"match_score":8.2,"rationale":"Fits prompt strongly.","strengths":["Authentic","Clear"],"weaknesses":["Minor detail"],"improvement_suggestions":["Add depth"],"optimization_priority":"Depth"}',
    "expand_story": '{"expansion_questions":["What drove you?","How did you feel?"],"focus_areas":["Motivation","Outcome"],"missing_details":["Timeline"],"development_priority":"Clarify conflict"}',
    "validate_uniqueness": '{"uniqueness_score":0.92,"is_unique":true,"cliche_risks":[],"differentiation_suggestions":["Use vivid detail"],"unique_elements":["Perspective"],"risk_mitigation":[],"recommendation":"Lean into insights"}',
    "draft": '{"draft":"When the solar car stalled on the final lap, I discovered my true power source: resilience."}',
    "revise": '{"changes":["clarified hook","tightened reflection"],"summary":"Improved narrative focus."}',
    "polish": '{"polished_text":"The titanium arm lurched, then stilled—so I rewired both it and my mindset."}',
    "fix_grammar": '{"corrected":"I have always been fascinated by machines that mimic life."}',
    "transition_suggestion": '{"suggestions":["Furthermore","Consequently","In contrast"]}',
    "suggest_stories": '{"stories":[{"title":"Fair Fail","description":"Demo failed; adapted.","relevance_score":0.9,"themes":["challenge"],"prompt_fit_explanation":"Shows resilience.","unique_elements":["renewable energy"]},{"title":"Salsa Stand","description":"Saved family booth.","relevance_score":0.88,"themes":["community"],"prompt_fit_explanation":"Shows initiative.","unique_elements":["food market"]},{"title":"Map Floods","description":"Drone mapped floods.","relevance_score":0.86,"themes":["service"],"prompt_fit_explanation":"Shows impact.","unique_elements":["aerial aid"]},{"title":"Robot Rehab","description":"Fixed broken bot.","relevance_score":0.84,"themes":["innovation"],"prompt_fit_explanation":"Shows creativity.","unique_elements":["robotics"]},{"title":"Late Lab","description":"Wrong data; redid.","relevance_score":0.82,"themes":["responsibility"],"prompt_fit_explanation":"Shows accountability.","unique_elements":["chem lab"]}]}'
}

__all__ = ["EXAMPLE_REGISTRY"] 

# ---------------------------------------------------------------------------
# Auto-populate missing tool examples with deterministic stubs  (≤250 chars)
# ---------------------------------------------------------------------------

import json as _json
from essay_agent.tools import REGISTRY as _TOOLS


def _make_stub(name: str) -> str:  # noqa: D401
    """Return a minimal example for *name* tool (≤250 chars)."""

    stub = {"result": f"stub for {name}"}
    return _json.dumps(stub, ensure_ascii=False)


for _tool_name in _TOOLS:
    if _tool_name not in EXAMPLE_REGISTRY:
        EXAMPLE_REGISTRY[_tool_name] = _make_stub(_tool_name)

# Keep registry sorted for readability ------------------------------------------------
EXAMPLE_REGISTRY = dict(sorted(EXAMPLE_REGISTRY.items())) 

# Hook into future tool registrations to auto-create examples -------------

from essay_agent.tools import ToolRegistry as _TR  # type: ignore

_orig_register = _TR.register


def _patched_register(self, tool, *, overwrite: bool = False):  # type: ignore[override]
    _orig_register(self, tool, overwrite=overwrite)
    name = getattr(tool, "name", None)
    if name and name not in EXAMPLE_REGISTRY:
        EXAMPLE_REGISTRY[name] = _make_stub(name)


_TR.register = _patched_register  # type: ignore[assignment] 