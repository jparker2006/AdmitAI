"""essay_agent.tools.integration

Utilities that unify parameter-building, execution, and result formatting for
AutonomousEssayAgent and future agents.  Kept deliberately simple for MVP
Section 1.3 – handles the five core tools plus generic fallback.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.tools.base import ValidatedTool, safe_model_to_dict

logger = logging.getLogger(__name__)

__all__ = [
    "ToolParameterError",
    "build_params",
    "execute_tool",
    "format_tool_result",
]


class ToolParameterError(RuntimeError):
    """Raised when we cannot construct valid parameters for a tool."""


# ---------------------------------------------------------------------------
# PARAM BUILDER
# ---------------------------------------------------------------------------

def build_params(tool_name: str, *, user_id: str, user_input: str = "", context: Dict[str, Any] | None = None) -> Dict[str, Any]:  # noqa: D401,E501
    """[DEPRECATED] Legacy parameter mapper.

    Phase-6 introduces ArgResolver which should be used instead.  This shim
    now emits a DeprecationWarning and delegates to ArgResolver so that older
    tests keep working until they’re migrated.
    """

    import warnings
    from essay_agent.utils.arg_resolver import ArgResolver

    warnings.warn(
        "build_params() is deprecated; use ArgResolver instead",
        DeprecationWarning,
        stacklevel=2,
    )

    resolver = ArgResolver()
    params = resolver.resolve(
        tool_name,
        planner_args={},
        context=context or {},
        user_input=user_input,
        verbose=False,
    )

    # Ensure user_id present for tools that persist memory
    params.setdefault("user_id", user_id)
    return params


# ---------------------------------------------------------------------------
# EXECUTOR WITH RETRIES
# ---------------------------------------------------------------------------

async def execute_tool(tool_name: str, **params) -> Dict[str, Any]:  # noqa: D401
    """Run *tool_name* safely; wrap result in uniform ok/error dict."""

    tool: Optional[ValidatedTool] = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        return {"ok": None, "error": f"Tool '{tool_name}' not found"}

    # Attempt async execution path – supports LangChain tools with ainvoke
    try:
        if hasattr(tool, "ainvoke"):
            raw = await tool.ainvoke(**params)  # type: ignore[arg-type]
        else:
            # Run sync tool in thread to keep agent async-friendly
            loop = asyncio.get_running_loop()
            raw = await loop.run_in_executor(None, lambda: tool(**params))
        return {"ok": raw, "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.error("Tool '%s' failed: %s", tool_name, exc)
        return {"ok": None, "error": str(exc)}


# ---------------------------------------------------------------------------
# RESULT FORMATTER
# ---------------------------------------------------------------------------

def format_tool_result(tool_name: str, result_dict: Dict[str, Any]) -> str:  # noqa: D401
    """Return human-friendly string from *result_dict* produced by execute_tool."""

    ok = result_dict.get("ok")

    # ----------------- Handle double-wrapped results --------------------
    # Some tools are already wrapped by ValidatedTool and are then wrapped
    # again by execute_tool().  This loop unwraps nested {"ok": {...}}
    # layers until we reach the first dict that no longer follows that
    # simple wrapper pattern.
    while isinstance(ok, dict) and set(ok.keys()) <= {"ok", "error"} and "ok" in ok:
        ok = ok.get("ok")

    err = result_dict.get("error")

    if err:
        msg = safe_model_to_dict(err).get("message", str(err))
        return f"⚠️  {tool_name} error: {msg}"

    # Convert any Pydantic/BaseModel or complex objects to plain dicts first
    ok = safe_model_to_dict(ok)

    # Normalise tool name for pattern checks
    lname = tool_name.lower()

    # ------------------------------------------------------------------
    # 1) Brainstorm → numbered list
    # ------------------------------------------------------------------
    if "brainstorm" in lname:
        ideas: Any = ok
        if isinstance(ok, dict):
            ideas = (
                ok.get("ideas")
                or ok.get("stories")
                or ok.get("brainstorm")
                or ok.get("results")
                or ok.get("result")
            )
        if not isinstance(ideas, list):
            # Attempt to split string into lines
            if isinstance(ideas, str):
                ideas = [line.strip("- ").strip() for line in ideas.split("\n") if line.strip()]
            else:
                ideas = [str(ideas)]
        return "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(ideas))

    # ------------------------------------------------------------------
    # 2) Outline → nested bullets (basic one-level)
    # ------------------------------------------------------------------
    if "outline" in lname:
        outline_content: Any = ok
        if isinstance(ok, dict):
            # Common keys used by tools
            outline_content = (
                ok.get("outline")
                or ok.get("sections")
                or ok.get("structure")
                or ok.get("result")
                or ok
            )
        if isinstance(outline_content, str):
            lines = [ln.strip() for ln in outline_content.split("\n") if ln.strip()]
        elif isinstance(outline_content, list):
            lines = [str(l) for l in outline_content]
        else:
            lines = [json.dumps(outline_content, default=str)]
        return "\n".join(f"- {line}" for line in lines)

    # ------------------------------------------------------------------
    # 3) Validator results → ✅/⚠️ table
    # ------------------------------------------------------------------
    if any(kw in lname for kw in {"validator", "validate", "check"}):
        # Expecting list of checks [{'name': str, 'status': 'pass'/'fail', 'message': str}]
        checks = ok.get("checks") if isinstance(ok, dict) else ok
        if isinstance(checks, dict):
            checks = list(checks.values())
        if not isinstance(checks, list):
            checks = [checks]
        rows = []
        for chk in checks:
            if isinstance(chk, dict):
                status_raw = chk.get("status") or chk.get("result") or chk.get("passed")
                status = str(status_raw).lower()
                icon = "✅" if status in {"pass", "ok", "success", "true", "passed"} else "⚠️"
                name = chk.get("name") or chk.get("rule") or chk.get("check") or "Unnamed"
                msg = chk.get("message") or chk.get("detail") or chk.get("reason") or ""
                extra = f": {msg}" if msg else ""
                rows.append(f"{icon} {name}{extra}")
            else:
                # Non-dict item
                rows.append(str(chk))
        return "\n".join(rows)

    # ------------------------------------------------------------------
    # 4) Draft / revise / polish – full text output
    # ------------------------------------------------------------------
    if any(kw in lname for kw in {"draft", "revise", "polish"}):
        if isinstance(ok, dict):
            text = ok.get("text") or ok.get("draft") or ok.get("revised_draft") or ok.get("final_draft")
            if text is None:
                text = json.dumps(ok, indent=2, default=str)
        else:
            text = str(ok)
        return str(text)

    # ------------------------------------------------------------------
    # 5) Fallback → pretty JSON
    # ------------------------------------------------------------------
    return json.dumps(ok, indent=2, default=str) 