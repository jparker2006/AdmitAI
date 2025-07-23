from __future__ import annotations

"""essay_agent.planner_prompt

Unified planner prompt that replaces BulletproofReasoning.
Builds a concise prompt containing full context and parses the
returned JSON plan.
"""

import json
import os
from typing import Any, Dict, List


class PlannerPrompt:  # pylint: disable=too-few-public-methods
    """LLM-wrapper that produces an ordered execution *plan*.

    Example JSON expected from LLM::
        {"plan":[{"tool":"outline","args":{"story":"..."}}]}
    """

    OFFLINE_PLAN = [{"tool": "brainstorm_specific", "args": {}}]

    def __init__(self, tool_names: List[str]):
        self._tool_names = tool_names

    # ------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------
    def build_prompt(self, user_input: str, context: Dict[str, Any]) -> str:  # noqa: D401
        """Return the raw prompt string sent to GPT.

        The prompt embeds structured context followed by the user message and
        STRICT instructions to output pure JSON.
        """
        recent_chat = context.get("recent_chat", [])[-3:]
        last_tool = context.get("last_tool", "none")
        profile = context.get("profile", {})
        # Flatten profile extras we care about
        college = profile.get("college", "")
        essay_prompt = profile.get("essay_prompt", "")
        preferred_wc = profile.get("preferred_word_count", 650)
        # NEW: additional context for Phase-5 upgrades ---------------------
        tool_stats = context.get("tool_stats", "")
        failure_count = context.get("failure_count", 0)

        # Render using Jinja template -----------------------------------------
        from pathlib import Path
        try:
            from jinja2 import Template  # Optional dependency
        except ModuleNotFoundError:  # pragma: no cover – fallback rendering
            Template = None  # type: ignore[assignment]

        tmpl_path = Path(__file__).resolve().parent / "prompts" / "planner" / "100x_planner_prompt.txt"
        if not tmpl_path.exists():
            # Fallback to inline template (should not happen in prod)
            template_str = "{{ role }}\n\nContext:\n  last_tool_used: {{ last_tool }}\n  tool_stats: {{ tool_stats }}\n  failure_count: {{ failure_count }}\n  college: {{ college }}\n  essay_prompt: {{ essay_prompt }}\n  recent_chat:\n{% for line in recent_chat %}    - {{ line }}\n{% endfor %}\nAvailable tools: {{ tools }}\n\nINSTRUCTIONS: 1) decide plan 2) output JSON only.\nUser message:\n{{ user_input }}\nJSON RESPONSE ONLY:"
        else:
            template_str = tmpl_path.read_text(encoding="utf-8")

        if Template is not None:
            tmpl = Template(template_str)
            rendered = tmpl.render(
                role="You are PlannerGPT-v2, the strategic architect turning user intent into an optimal sequence of tool calls.",
                last_tool=last_tool,
                college=college,
                essay_prompt=essay_prompt,
                tool_stats=tool_stats,
                failure_count=failure_count,
                recent_chat=recent_chat,
                tools_list=self._format_tools_with_descriptions_list(),
                user_input=user_input,
            )
        else:
            # Minimal manual replacement – recent_chat concatenated
            rendered = template_str.replace("{{ last_tool }}", last_tool)
            rendered = rendered.replace("{{ college }}", college)
            rendered = rendered.replace("{{ essay_prompt }}", essay_prompt)
            rendered = rendered.replace("{{ preferred_wc }}", str(preferred_wc))  # may still exist in legacy templates
            rendered = rendered.replace("{{ tool_stats }}", tool_stats)
            rendered = rendered.replace("{{ failure_count }}", str(failure_count))
            rendered = rendered.replace("{{ tools }}", ", ".join(self._tool_names))
            rendered = rendered.replace("{{ user_input }}", user_input)
            rendered = rendered.replace("{{ role }}", "PlannerGPT")
            joined_chat = "\n".join(recent_chat)
            rendered = rendered.replace("{% for line in recent_chat %}    - {{ line }}\n{% endfor %}", joined_chat)
        return rendered

    # ------------------------------------------------------------------
    # Response parser
    # ------------------------------------------------------------------
    def parse_response(self, raw: str, *, offline: bool | None = None) -> List[Dict[str, Any]]:  # noqa: D401
        """Parse *raw* JSON from the LLM, return ordered plan list.

        Falls back to deterministic OFFLINE_PLAN when running under
        ESSAY_AGENT_OFFLINE_TEST or when JSON is invalid.
        """
        if offline is None:
            offline = os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1"

        try:
            # Strip common markdown fences if present
            raw_stripped = raw.strip()
            if raw_stripped.startswith("```"):
                # Remove opening fence (```json optional)
                raw_stripped = raw_stripped.split("\n", 1)[1] if "\n" in raw_stripped else raw_stripped
                if raw_stripped.endswith("```"):
                    raw_stripped = raw_stripped.rsplit("```", 1)[0]

            # Fallback: try to grab the first JSON object in the text
            if not raw_stripped.strip().startswith("{"):
                first_curly = raw_stripped.find("{")
                last_curly = raw_stripped.rfind("}")
                if first_curly != -1 and last_curly != -1 and last_curly > first_curly:
                    raw_stripped = raw_stripped[first_curly:last_curly + 1]

            data = json.loads(raw_stripped)
            plan = data.get("plan")
            if isinstance(plan, list):
                # basic validation: each item has tool key
                filtered = [p for p in plan if isinstance(p, dict) and p.get("tool")]
                if filtered:
                    return filtered
        except Exception:  # pragma: no cover – any json failure triggers fallback
            pass

        # Fallback deterministic plan
        return self.OFFLINE_PLAN.copy()

    def _format_tools_with_descriptions(self) -> str:
        """Return formatted string of tools with their descriptions (compressed)."""
        from essay_agent.tools import REGISTRY  # local import
        formatted = []
        for name, tool in sorted(REGISTRY.items()):
            desc = (tool.description or "(no description)").split()
            short_desc = " ".join(desc[:8])  # first 8 words max
            formatted.append(f"{name} – {short_desc}…")
        return "\n".join(formatted)

    def _format_tools_with_descriptions_list(self):  # noqa: D401
        """Return list of tool-description lines for templating."""
        return self._format_tools_with_descriptions().split("\n") 