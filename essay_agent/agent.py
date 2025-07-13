"""essay_agent.agent

High-level `EssayAgent` orchestrates the full essay workflow – from brainstorming
through polishing – in a single call, integrating planner/executor, tool
registry and JSON memory.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from essay_agent.llm_client import track_cost
from essay_agent.memory.simple_memory import SimpleMemory, is_story_reused
from essay_agent.models import EssayPrompt, EssayDraft  # noqa: F401 – used for typing
from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.memory.user_profile_schema import EssayRecord, EssayVersion
from essay_agent.planner import Phase


class EssayAgent:  # pylint: disable=too-few-public-methods
    """User-facing API wrapping planner, executor & memory helpers."""

    MAX_BRAINSTORM_RETRY = 2

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.mem = SimpleMemory()
        self.profile = self.mem.load(user_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_essay(self, prompt: EssayPrompt) -> Dict[str, Any]:  # noqa: D401
        """Run the end-to-end workflow and return final draft + metadata."""

        if not prompt.text.strip():
            raise ValueError("Prompt text must not be empty")

        start_time = time.time()
        workflow: Dict[str, Any] = {}

        # ------------------------------------------------------------------
        # Phase 1: Brainstorm
        # ------------------------------------------------------------------
        brainstorm_tool = TOOL_REGISTRY["brainstorm"]
        retry = 0
        stories: List[Dict[str, Any]] | None = None
        while retry <= self.MAX_BRAINSTORM_RETRY:
            out = brainstorm_tool(essay_prompt=prompt.text, profile=self.profile.model_dump_json())
            workflow["brainstorm"] = out
            if out.get("error"):
                raise RuntimeError(out["error"])
            stories = out["ok"]["stories"]
            # Choose first story not yet reused for this college
            chosen = None
            for s in stories:
                if not is_story_reused(self.user_id, story_title=s["title"], college=prompt.college or ""):  # type: ignore[arg-type]
                    chosen = s
                    break
            if chosen:
                story = chosen["title"]
                break
            retry += 1
        else:
            raise RuntimeError("Brainstorm produced only reused stories")

        # ------------------------------------------------------------------
        # Phase 2: Outline
        outline_tool = TOOL_REGISTRY["outline"]
        outline_out = outline_tool(story=story, prompt=prompt.text, word_count=prompt.word_limit)
        workflow["outline"] = outline_out
        if outline_out.get("error"):
            raise RuntimeError(outline_out["error"])
        outline = outline_out["outline"] if isinstance(outline_out, dict) else outline_out["ok"]["outline"]

        # ------------------------------------------------------------------
        # Phase 3: Draft
        draft_tool = TOOL_REGISTRY["draft"]
        # Extract voice profile from user profile or use default
        voice_profile = "authentic, personal, reflective"
        if self.profile.writing_voice:
            voice_profile = ", ".join(self.profile.writing_voice.tone_preferences) or voice_profile
        draft_out = draft_tool(outline=outline, voice_profile=voice_profile, word_count=prompt.word_limit)
        workflow["draft"] = draft_out
        if draft_out.get("error"):
            raise RuntimeError(draft_out["error"])
        draft_text = draft_out["ok"]["draft"] if "ok" in draft_out else draft_out["draft"]

        # ------------------------------------------------------------------
        # Phase 4: Revise (simple generic focus)
        revise_tool = TOOL_REGISTRY["revise"]
        rev_out = revise_tool(draft=draft_text, revision_focus="improve flow", word_count=prompt.word_limit)
        workflow["revise"] = rev_out
        if rev_out.get("error"):
            raise RuntimeError(rev_out["error"])
        revised_text = rev_out["ok"]["revised_draft"] if "ok" in rev_out else rev_out["revised_draft"]

        # ------------------------------------------------------------------
        # Phase 5: Polish
        polish_tool = TOOL_REGISTRY["polish"]
        with track_cost() as (llm, cb):
            pol_out = polish_tool(draft=revised_text, word_count=prompt.word_limit)
            cost = cb.total_cost
        workflow["polish"] = pol_out
        if pol_out.get("error"):
            raise RuntimeError(pol_out["error"])
        final_text = pol_out["ok"]["final_draft"] if "ok" in pol_out else pol_out["final_draft"]

        duration = time.time() - start_time

        # ------------------------------------------------------------------
        # Persist essay record ----------------------------------------------------
        record = EssayRecord(
            prompt_id="N/A",  # can be extended later
            prompt_text=prompt.text,
            platform=prompt.college or "generic",
            status="complete",
            versions=[
                EssayVersion(
                    version=1,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    content=final_text,
                    word_count=prompt.word_limit,
                    used_stories=[story],
                )
            ],
        )
        SimpleMemory.add_essay_record(self.user_id, record)

        # Flatten the workflow results into the top-level dictionary
        final_result = {
            "final_draft": final_text,
            "cost": cost,
            "duration_sec": duration,
        }
        # Add all intermediate step outputs to the final result
        for step_name, step_output in workflow.items():
            # Use the 'ok' sub-dictionary if it exists, otherwise the raw output
            if isinstance(step_output, dict) and "ok" in step_output:
                final_result[step_name] = step_output["ok"]
            else:
                final_result[step_name] = step_output

        # Backward-compatibility: keep nested workflow key for older tests
        final_result["workflow"] = workflow

        return final_result

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @staticmethod
    def is_story_reused(user_id: str, story_title: str, college: str) -> bool:  # noqa: D401
        return is_story_reused(user_id, story_title=story_title, college=college) 