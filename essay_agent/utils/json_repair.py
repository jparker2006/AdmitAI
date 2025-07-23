from __future__ import annotations

"""essay_agent.utils.json_repair

Schema-aware repair helper that converts malformed LLM output into JSON that
conforms (as best-effort) to a target schema.  During offline tests (when the
``ESSAY_AGENT_OFFLINE_TEST`` env-var is "1") the repair relies purely on
heuristics and never calls the network.  In online mode it falls back to a
single GPT-3.5 pass if heuristics are insufficient.
"""

from typing import Any, Dict
import json
import os
import re

# ---------------------------------------------------------------------------
# Helper – strip ``` fences (duplicated to avoid circular import with tools)
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"^```(?:[a-zA-Z0-9]+)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_fences(text: str) -> str:  # noqa: D401
    """Return *text* without outer ``` fences if present."""
    if not isinstance(text, str):
        text = str(text)
    stripped = text.strip()
    match = _FENCE_RE.match(stripped)
    if match:
        return match.group(1).strip()
    return stripped


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fix(raw_text: str, schema_text: str = "") -> str:  # noqa: D401
    """Attempt to *repair* *raw_text* so it parses as JSON matching *schema_text*.

    The function is intentionally **best-effort** – it never raises and will
    always return a *string* (which might still be the original raw text if all
    repair attempts fail).
    """

    cleaned = _strip_fences(raw_text)

    # ------------------------------------------------------------------
    # 1. Fast path – does it already parse as JSON?
    # ------------------------------------------------------------------
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return cleaned  # Already good
        # If the schema appears to expect a dict with a specific key and we
        # received a *list*, wrap it accordingly (common brainstorm failure).
        if isinstance(parsed, list):
            wrapper_key = None
            if schema_text:
                top_key_match = re.search(r'"(\w+)"\s*:', schema_text)
                if top_key_match:
                    wrapper_key = top_key_match.group(1)
            # Fallback to common wrapper key names
            if wrapper_key is None:
                wrapper_key = "stories" if all(isinstance(i, dict) for i in parsed) else "data"
            wrapped = {wrapper_key: parsed}
            return json.dumps(wrapped, ensure_ascii=False)
    except Exception:
        pass  # Continue with heuristics

    # ------------------------------------------------------------------
    # 2. Heuristic clean-ups (commas, stray text, trailing chars)
    # ------------------------------------------------------------------
    heuristics = cleaned
    heuristics = re.sub(r",\s*}\s*$", "}", heuristics)  # trailing comma obj
    heuristics = re.sub(r",\s*]\s*$", "]", heuristics)  # trailing comma arr
    heuristics = heuristics.strip()

    # ------------------------------------------------------------------
    # 2b. Key alias mapping for known patterns (e.g., brainstorm drift)
    # ------------------------------------------------------------------
    try:
        obj = json.loads(heuristics)
        # If we received a list, wrap earlier code will handle; focus on dict
        if isinstance(obj, dict):
            target = obj.get("stories", obj)
            # target can be list of story dicts
            if isinstance(target, list):
                alias = {
                    "story_title": "title",
                    "story_summary": "description",
                    "key_lessons": "insights",
                    "impact": "prompt_fit",
                }
                for item in target:
                    if isinstance(item, dict):
                        for a, canonical in alias.items():
                            if a in item and canonical not in item:
                                item[canonical] = item.pop(a)
                heuristics = json.dumps(obj, ensure_ascii=False)
    except Exception:
        pass

    try:
        json.loads(heuristics)
        return heuristics
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 3. Offline deterministic fallback – never call network -------------
    # ------------------------------------------------------------------
    if os.getenv("ESSAY_AGENT_OFFLINE_TEST", "0") == "1":
        # If schema expects a specific wrapper key, fabricate a minimal stub.
        key_match = re.search(r'"(\w+)"\s*:', schema_text)
        if key_match:
            key = key_match.group(1)
            stub = {key: []}
            return json.dumps(stub, ensure_ascii=False)
        # Generic stub
        return "{}"

    # ------------------------------------------------------------------
    # 4. Online – delegate to GPT repair pass ---------------------------
    # ------------------------------------------------------------------
    try:
        from essay_agent.llm_client import get_chat_llm, call_llm

        system_msg = (
            "You are a JSON repair assistant. Convert the user's previous answer "
            "into valid JSON that matches the schema below. Return ONLY the JSON object."
        )
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "assistant", "content": cleaned[:4000]},
        ]
        if schema_text:
            messages.append({"role": "assistant", "content": f"SCHEMA:\n{schema_text}"})

        llm = get_chat_llm(model_name="gpt-3.5-turbo-0125", temperature=0.0)
        repaired = call_llm(llm, messages)  # type: ignore[arg-type]
        repaired = _strip_fences(repaired)

        # Debug output when requested -----------------------------------
        if os.getenv("SHOW_REPAIR_RAW", "0") == "1":
            preview = repaired.replace("\n", " ")[:500]
            print(f"🔧 Repaired JSON preview: {preview}…")

        # Sanity parse – if parse fails we fallthrough to returning original
        json.loads(repaired)
        return repaired
    except Exception:
        # Any failure -> return original cleaned text to avoid raising
        return cleaned


__all__ = ["fix"] 