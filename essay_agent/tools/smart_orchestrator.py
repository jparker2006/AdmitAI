"""essay_agent.tools.smart_orchestrator

Section 3.1 – Smart Tool Orchestrator
-------------------------------------------------
Centralised component that converts BulletproofReasoning output + contextual
information into an *ordered* tool-execution plan and executes that plan with
robust retries, fall-backs, and quality-score hooks.

It purposely avoids any hard-coded chains. Instead, it consults the existing
`BulletproofReasoning` engine after each tool run to decide whether a follow-up
execution is needed.  This allows fully LLM-driven orchestration while keeping
strict guard-rails on JSON structure and retries.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional
import os

from essay_agent.reasoning.bulletproof_reasoning import BulletproofReasoning, ReasoningResult
# Phase-6: replace manual param builder with ArgResolver
from essay_agent.tools.integration import execute_tool
from essay_agent.utils.arg_resolver import ArgResolver, MissingRequiredArgError
from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.intelligence.quality_engine import QualityEngine

logger = logging.getLogger(__name__)

__all__ = ["SmartOrchestrator"]


class SmartOrchestrator:  # pylint: disable=too-few-public-methods
    """Intelligent, LLM-guided tool orchestrator.

    A *plan* is a list of step-dicts::

        {
          "tool_name": "outline",
          "tool_args": { ... },
          "reasoning": "why we chose it",
          "confidence": 0.82,
        }

    For each step we attempt execution, append result to *history*, update
    *context*, and then ask the LLM (via :class:`BulletproofReasoning`) if we
    should continue.  The process terminates when the LLM returns
    ``action = conversation`` or when ``MAX_STEPS`` is reached.
    """

    MAX_STEPS = 5
    MAX_RETRIES = 2

    def __init__(
        self,
        user_id: str,
        memory: Any,  # SmartMemory instance – kept generic to avoid circular import
        context_engine: Any,  # ContextEngine instance
        reasoner: Optional[BulletproofReasoning] = None,
        tool_registry: Dict[str, Any] | None = None,
    ) -> None:
        self.user_id = user_id
        self.memory = memory
        self.context_engine = context_engine
        self.reasoner = reasoner or BulletproofReasoning()
        self.tools = tool_registry or TOOL_REGISTRY

        # Phase-6: shared arg resolver instance
        self._arg_resolver = ArgResolver()

        # Quality scoring --------------------------------------------------
        self.quality_engine = QualityEngine()
        self.min_quality = float(os.getenv("MIN_QUALITY_SCORE", "8.5"))
        self.max_quality_steps = int(os.getenv("MAX_QUALITY_STEPS", "3"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def select_tools(self, reasoning: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:  # noqa: D401,E501
        """Transform *reasoning* into an initial execution plan.

        The agent's first *BulletproofReasoning* call has already decided on the
        *first* tool to run.  We simply wrap that into plan-format so that the
        executor can iterate.  Additional tools (if any) are appended
        dynamically at runtime after we observe each tool's output.
        """
        action = reasoning.get("action")

        if action == "tool_execution":
            tools = [reasoning.get("tool_name")]
        elif action == "tool_sequence":
            tools = reasoning.get("sequence") or []
        else:
            return []

        # Optional dependency validation if registry exposes helper
        if hasattr(self.tools, "validate_tool_sequence") and tools:
            valid, missing = self.tools.validate_tool_sequence(tools)
            if not valid:
                logger.warning("Invalid tool sequence – %s", ", ".join(missing))
                # Drop invalid tools to avoid runtime failure
                tools = [t for t in tools if all(t not in m for m in missing)]

        plan: List[Dict[str, Any]] = []
        for tname in tools:
            if not tname:
                continue
            plan.append({
                "tool_name": tname,
                "tool_args": reasoning.get("tool_args", {}),
                "reasoning": reasoning.get("reasoning", ""),
                "confidence": reasoning.get("confidence", 0.0),
            })

        return plan

    async def execute_plan(
        self,
        plan: List[Dict[str, Any]],
        *,
        user_input: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:  # noqa: D401,E501
        """Run *plan* sequentially, expanding it on-the-fly with LLM guidance.

        Returns a dict::
            {
              "steps": [ {"tool": str, "params": dict, "result": dict}, ... ]
            }
        """
        import os, json

        # ------------------------------------------------------------------
        # DEBUG / Observability: show prompts & tool outputs when enabled
        # ------------------------------------------------------------------
        show_prompts = os.getenv("ESSAY_AGENT_SHOW_PROMPTS") == "1"

        # ------------------------------------------------------------------
        # Fallback: if planner returned an empty list switch to chat_response
        # ------------------------------------------------------------------
        if not plan:
            logger.info("Plan is empty, defaulting to conversation-as-tool")
            plan = [
                {
                    "tool_name": "chat_response",
                    "tool_args": {"prompt": user_input},
                    "reasoning": "Fallback to conversation-as-tool when plan is empty",
                    "confidence": 0.0,
                }
            ]

        history: List[Dict[str, Any]] = []
        executed_tools: set[str] = set()
        current_context: Dict[str, Any] = dict(context)
        steps_executed = 0
        clarify_inserted = False  # guard against infinite clarify loop

        while plan and steps_executed < self.MAX_STEPS:
            step_raw = plan.pop(0)

            # Autofill missing args --------------------------------------------------
            # U4-02: Autofill missing arguments
            try:
                from essay_agent.utils.default_args import autofill_args

                autofilled_args = autofill_args(
                    step_raw,
                    context=context,
                    memory=self.memory,
                    user_input=user_input
                )
                step_raw["args"] = autofilled_args

            except ImportError:
                # dev-mode: default_args may not exist yet
                pass

            tool_name: str = step_raw.get("tool_name") or step_raw.get("tool")
            tool_args_ctx: Dict[str, Any] = step_raw.get("tool_args", step_raw.get("args", {}))

            # Merge original planner-provided args so aliases (e.g. 'prompt') survive
            planner_args = {**tool_args_ctx}

            # ------------------------------------------------------------------
            # Parameter construction
            # ------------------------------------------------------------------
            try:
                params = self._arg_resolver.resolve(
                    tool_name,
                    planner_args=planner_args,
                    context={**current_context},
                    user_input=user_input,
                )
                # Always include user_id for memory persistence if expected
                params.setdefault("user_id", self.user_id)
                # Merge resolved params into current context for downstream steps
                current_context.update(params)
            except MissingRequiredArgError as exc:
                logger.warning("ArgResolver failed: %s", exc)
                if clarify_inserted:
                    # Prevent infinite loop – return error result gracefully
                    history.append({
                        "tool": tool_name,
                        "params": {},
                        "result": {"ok": None, "error": str(exc)},
                    })
                    break

                clarification_q = str(exc).replace("Missing required args for", "I need these details for")
                plan.insert(0, {
                    "tool_name": "clarify",
                    "tool_args": {
                        "question": clarification_q,
                        "user_input": user_input,
                    },
                    "reasoning": "Ask user to provide missing parameters",
                    "confidence": 0.0,
                })
                clarify_inserted = True
                # Skip executing the current step
                continue

            if show_prompts:
                print("\n=== TOOL »", tool_name, "===")
                try:
                    print("ARGS:")
                    print(json.dumps(params, indent=2, default=str))
                except Exception:
                    print("[args not JSON-serialisable]")

            # ------------------------------------------------------------------
            # Tool execution with basic retry / fallback
            # ------------------------------------------------------------------
            result_dict: Dict[str, Any] | None = None
            error: Optional[str] = None
            for attempt in range(1, self.MAX_RETRIES + 2):
                result_dict = await execute_tool(tool_name, **params)
                error = result_dict.get("error")
                if not error:
                    break  # success!
                logger.warning("Tool %s failed (attempt %s/%s): %s", tool_name, attempt, self.MAX_RETRIES + 1, error)
            # After retries, proceed regardless – error information is valuable

            history.append({
                "tool": tool_name,
                "params": params,
                "result": result_dict,
            })

            if show_prompts:
                from essay_agent.tools.integration import format_tool_result
                print("RESULT:")
                try:
                    print(format_tool_result(tool_name, result_dict))
                except Exception:
                    # Fallback to raw JSON if formatter fails
                    try:
                        print(json.dumps(result_dict, indent=2, default=str))
                    except Exception:
                        print("[result not JSON-serialisable]")

            # Update context with output to help next reasoning step
            current_context[tool_name] = result_dict.get("ok")

            # ------------------------------------------------------------------
            # Quality check – if we produced a draft-like text, score it
            # ------------------------------------------------------------------
            draft_text = _extract_draft_text(result_dict.get("ok"))
            if draft_text:
                quality = await self.quality_engine.async_score_draft(draft_text, user_id=self.user_id)
                current_context["quality_score"] = quality
                if quality < self.min_quality and steps_executed < self.max_quality_steps:
                    # Ask reasoning engine for improvement tool, fallback default
                    try:
                        follow = await self.reasoner.decide_action("Improve quality", current_context)
                        next_tool = follow.tool_name or "revise_for_clarity"
                    except Exception:
                        next_tool = "revise_for_clarity"

                    plan.append({
                        "tool_name": next_tool,
                        "tool_args": {"target_quality": self.min_quality},
                        "reasoning": "auto quality improvement",
                        "confidence": 0.9,
                    })

            # Track executed tool to avoid duplicates in this turn
            executed_tools.add(tool_name)

            steps_executed += 1

            # ------------------------------------------------------------------
            # Ask LLM if we need another tool – avoids hard-coded chains
            # ------------------------------------------------------------------
            reasoning_follow: ReasoningResult = await self.reasoner.decide_action(
                user_input,
                current_context,
            )
            # If follow-up suggests another tool
            if reasoning_follow.action == "tool_execution":
                next_tool_name = reasoning_follow.tool_name

                # Skip if we've already executed this tool in the current turn
                if next_tool_name in executed_tools:
                    break

                plan.append({
                    "tool_name": next_tool_name,
                    "tool_args": getattr(reasoning_follow, "tool_args", {}),
                    "reasoning": getattr(reasoning_follow, "reasoning", ""),
                    "confidence": getattr(reasoning_follow, "confidence", 0.0),
                })
            else:
                # LLM indicated we're done; exit loop
                break

        return {"steps": history}

    # ------------------------------------------------------------------
    # Bootstrap helper (EF-93) – run brainstorm → outline on first session
    # ------------------------------------------------------------------

    async def bootstrap_if_needed(self) -> bool:  # noqa: D401
        """Run an initial brainstorm→outline sequence if not yet generated.

        Returns *True* when the bootstrap plan was executed, *False* when it
        was skipped because an outline already exists or required context is
        missing.
        """

        # Lazy import to avoid heavy deps on startup
        from essay_agent.memory.simple_memory import SimpleMemory, ensure_essay_record  # pylint: disable=import-outside-toplevel

        profile = SimpleMemory.load(self.user_id)
        extra = getattr(profile, "model_extra", {}) or {}
        essay_prompt: str | None = extra.get("essay_prompt")

        if not essay_prompt:
            return False  # onboarding not completed

        # Ensure we have a record; status may already be "outline" for new ones
        record = ensure_essay_record(self.user_id, essay_prompt)

        # Skip bootstrap when the user already progressed beyond the initial outline
        # i.e. when *any* versions exist OR the status is anything other than plain "outline".
        # This change (EF-97) also means an unfinished workflow (status != "complete") will be
        # picked up by *resume_workflow* instead of re-running the brainstorm/outline pair.
        if record.versions or record.status != "outline":
            return False

        plan: List[Dict[str, Any]] = [
            {
                "tool_name": "brainstorm_specific",
                "tool_args": {"prompt": essay_prompt},
                "reasoning": "phase-3 bootstrap",
                "confidence": 0.95,
            },
            {
                "tool_name": "outline",
                "tool_args": {},
                "reasoning": "phase-3 bootstrap",
                "confidence": 0.95,
            },
        ]

        # Empty context for first run; more could be added later
        await self.execute_plan(plan, user_input=essay_prompt, context={})
        return True

    # ------------------------------------------------------------------
    # Resume helper (EF-97) – continue an unfinished workflow
    # ------------------------------------------------------------------

    async def resume_workflow(self) -> str:  # noqa: D401
        """Resume the next step of an unfinished essay workflow.

        Determines the *current* :pyattr:`EssayRecord.status` and executes the
        appropriate next tool once. The mapping is::

            outline   → draft   (runs ``draft`` tool)
            draft     → revision (runs ``revise`` tool)
            revision  → complete (runs ``polish`` tool)

        The function persists the updated status in :class:`SimpleMemory` and
        returns the *new* status string. When the essay is already complete,
        the function is a no-op and simply returns "complete".
        """

        # Lazy import to avoid circular dependencies at module import time
        from essay_agent.memory.simple_memory import SimpleMemory, ensure_essay_record  # pylint: disable=import-outside-toplevel

        profile = SimpleMemory.load(self.user_id)
        extra = getattr(profile, "model_extra", {}) or {}
        essay_prompt: str | None = extra.get("essay_prompt")

        if not essay_prompt:
            return "no_prompt"  # Onboarding not complete – nothing to resume

        record = ensure_essay_record(self.user_id, essay_prompt)

        current_status = record.status or "outline"

        # Nothing to do when the essay is already finished ----------------
        if current_status == "complete":
            return "complete"

        # Map current status → (next_status, tool_name)
        transition_map: dict[str, tuple[str, str]] = {
            "outline": ("draft", "draft"),
            "draft": ("revision", "revise"),
            "revision": ("complete", "polish"),
        }

        if current_status not in transition_map:
            # Unexpected status – bail out gracefully
            return current_status

        next_status, next_tool = transition_map[current_status]

        plan = [{
            "tool_name": next_tool,
            "tool_args": {},
            "reasoning": "resume_workflow_auto",
            "confidence": 0.90,
        }]

        # Execute the single step. We intentionally ignore errors here to
        # avoid crashing the CLI – failure details are captured in memory.
        essay_prompt_text = essay_prompt or "Resume workflow"
        try:
            await self.execute_plan(plan, user_input=essay_prompt_text, context={})
        except Exception:  # pragma: no cover – resume should never raise
            pass

        # Update record status and persist --------------------------------
        record.status = next_status
        SimpleMemory.save(self.user_id, profile)

        return next_status


# ---------------------------------------------------------------------------
# Helper: attempt to extract draft text from tool result
# ---------------------------------------------------------------------------


def _extract_draft_text(ok_obj):
    if not ok_obj:
        return ""
    if isinstance(ok_obj, str):
        return ok_obj
    if isinstance(ok_obj, dict):
        for key in ("draft", "revised_draft", "final_draft", "text"):
            if key in ok_obj and isinstance(ok_obj[key], str):
                return ok_obj[key]
    return "" 