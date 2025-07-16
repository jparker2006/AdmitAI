"""essay_agent.agent

High-level `EssayAgent` orchestrates the full essay workflow – from brainstorming
through polishing – in a single call, integrating planner/executor, tool
registry and JSON memory.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.models import EssayPrompt
from essay_agent.memory.user_profile_schema import UserProfile
from essay_agent.models import Phase, EssayPlan, EssayPlanner
from essay_agent.executor import EssayExecutor
from dataclasses import dataclass, field
from essay_agent.utils.logging import debug_print
from datetime import datetime

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class EssayResult:
    final_draft: str
    stories: list[dict[str, Any]] | None = None
    outline: dict[str, Any] | None = None
    versions: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    debug_log: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


class EssayAgent:  # pylint: disable=too-few-public-methods
    """High-level orchestrator that drives planner & executor until completion."""

    def __init__(self, user_id: str, *, max_steps: int = 10):
        self.user_id = user_id
        self.mem = SimpleMemory()
        self.profile = self.mem.load(user_id)
        self.max_steps = max_steps
        self._planner = EssayPlanner()
        self._executor = EssayExecutor()

    # ------------------------------------------------------------------
    # Public API – new run method
    # ------------------------------------------------------------------

    def run(
        self,
        prompt: EssayPrompt,
        profile: "UserProfile",
        *,
        debug: bool = False,
        stop_phase: Phase | None = None,
    ) -> EssayResult:  # noqa: D401
        """Execute full essay workflow returning structured :class:`EssayResult`."""

        if not prompt.text.strip():
            raise ValueError("prompt.text must not be empty")

        # Merge supplied profile with persisted profile ----------------
        self.profile = profile  # in MVP simply overwrite
        SimpleMemory.save(self.user_id, profile)

        start_time = time.time()

        final_draft: str = ""

        # Initialise plan ------------------------------------------------
        plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={
                "user_input": prompt.text,
                "context": {
                    "user_id": self.user_id,
                    "essay_prompt": prompt.text,
                    "word_limit": prompt.word_limit,
                    "user_profile": profile.model_dump() if hasattr(profile, "model_dump") else {},
                },
            },
        )

        debug_log: list[dict[str, Any]] = []
        errors: list[str] = []

        for step in range(self.max_steps):
            step_start = time.time()
            debug_print(debug, f"Step {step} – phase={plan.phase.name}")

            outputs = {}
            try:
                outputs = self._executor.run_plan(plan)
            except Exception as exc:  # pragma: no cover – executor error
                errors.append(str(exc))
                debug_print(debug, f"Executor raised {exc}")
                break

            # Extract tool outputs & errors
            tool_outputs = {k: v for k, v in outputs.items() if k != "errors"}
            step_errors = outputs.get("errors", [])
            errors.extend(step_errors)

            # Update plan for next iteration ---------------------------
            plan.data.setdefault("tool_outputs", {}).update(tool_outputs)

            # Determine next phase from executor logic via returned outputs
            if "polish" in tool_outputs:
                final_draft = tool_outputs["polish"].get("final_draft") if isinstance(tool_outputs["polish"], dict) else tool_outputs["polish"]
                # Mark workflow as completed so we don't incorrectly flag errors later
                plan.phase = Phase.POLISHING
                break

            # If caller requested partial run, exit once that phase is reached
            if stop_phase and plan.phase == stop_phase:
                break

            # Let planner choose next (fallback handled inside executor) --
            plan = EssayPlan(phase=plan.phase, data=plan.data)

            debug_log.append(
                {
                    "step": step,
                    "phase": plan.phase.name,
                    "tool_outputs": list(tool_outputs.keys()),
                    "errors": step_errors,
                    "duration": round(time.time() - step_start, 3),
                }
            )

        # Extract final draft from the last successful tool ---------------
        final_draft = ""
        tool_outputs = plan.data.get("tool_outputs", {})
        
        # Helper to extract successful result from tool output
        def extract_result(tool_output):
            if isinstance(tool_output, dict):
                if "error" in tool_output and tool_output["error"] is not None:
                    return None  # Tool failed
                if "ok" in tool_output:
                    return tool_output["ok"]
            return tool_output
        
        # Try to get final draft from polish -> revise -> draft in that order
        for tool_name, content_key in [("polish", "final_draft"), ("revise", "revised_draft"), ("draft", "draft")]:
            if tool_name in tool_outputs:
                result = extract_result(tool_outputs[tool_name])
                if result and isinstance(result, dict) and content_key in result:
                    final_draft = result[content_key]
                    break
                elif result and isinstance(result, str):
                    final_draft = result
                    break

        if not final_draft:
            errors.append("No successful draft generated")

        # Only mark max_steps error if workflow did not produce a final draft
        if plan.phase != Phase.POLISHING and not final_draft:
            errors.append("max_steps reached without completion")

        duration = time.time() - start_time

        # Collate artefacts -------------------------------------------
        stories = None
        outline = None
        versions: list[dict[str, Any]] = []
        
        if "brainstorm" in tool_outputs:
            result = extract_result(tool_outputs["brainstorm"])
            if result and isinstance(result, dict) and "stories" in result:
                stories = result["stories"]
                
        if "outline" in tool_outputs:
            result = extract_result(tool_outputs["outline"])
            if result and isinstance(result, dict) and "outline" in result:
                outline = result["outline"]
                
        for name in ("draft", "revise"):
            if name in tool_outputs:
                # Always include the raw tool result for debugging, but mark errors clearly
                tool_result = tool_outputs[name]
                if isinstance(tool_result, dict) and "error" in tool_result and tool_result["error"] is not None:
                    # Include error information for debugging
                    versions.append(tool_result)
                else:
                    versions.append(tool_result)

        steps_executed = len(debug_log) if debug else (step + 1 if 'step' in locals() else 0)

        result = EssayResult(
            final_draft=final_draft or "",
            stories=stories,
            outline=outline,
            versions=versions,
            errors=errors,
            debug_log=debug_log if debug else [],
            stats={"total_time_sec": round(duration, 2), "steps": steps_executed},
        )

        # retain plan for legacy wrapper
        self._last_plan = plan

        return result

    # ------------------------------------------------------------------
    # Backward-compatibility shim – older tests expect generate_essay()
    # ------------------------------------------------------------------

    def generate_essay(self, prompt: EssayPrompt):  # noqa: D401
        """Legacy wrapper that delegates to ``run`` using persisted profile."""
        res = self.run(prompt, self.profile, debug=False)
        # Flatten to the original dict structure expected by old tests -----
        workflow = plan.data.get("tool_outputs", {}) if (plan := getattr(self, "_last_plan", None)) else {}
        flat: Dict[str, Any] = {
            "final_draft": res.final_draft,
            "stories": res.stories,
            "outline": res.outline,
            "versions": res.versions,
            "errors": res.errors,
            "workflow": workflow,
        }
        return flat 