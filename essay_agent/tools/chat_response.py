from __future__ import annotations

"""essay_agent.tools.chat_response

Conversation-as-Tool implementation (U4-03).
Wraps a simple LLM call so that the planner/orchestrator can always fall back
on a plain chat response when no other tool is appropriate.

The tool complies with the `ValidatedTool` interface and returns a JSON-serialisable
structure of the form `{"ok": str, "error": None}`.  In **offline** mode (when
`ESSAY_AGENT_OFFLINE_TEST=1`) it returns a deterministic stub response so unit
and CI tests remain stable without network access.
"""

import os
from typing import Any

from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.llm_client import chat as _chat


@register_tool("chat_response")
class ChatResponseTool(ValidatedTool):
    """Fallback conversational response tool.

    This tool simply returns an LLM-generated reply to the provided *prompt*.
    It enables the *conversation-as-tool* paradigm so that **every** agent turn
    executes at least one tool (even if that tool is just free-form chat).
    """

    name = "chat_response"
    description = (
        "Generate a direct conversational response using the underlying LLM. "
        "Used when the planner decides that no specialised tool is required."
    )

    # Return the dict directly so downstream executors don't attempt re-encoding
    return_direct = True

    # ------------------------------------------------------------------
    # Core execution (sync path) – async will delegate to _run via wrapper
    # ------------------------------------------------------------------

    def _run(self, prompt: str, **kwargs: Any):  # noqa: D401
        """Generate a reply to *prompt*.

        In offline test mode we return a deterministic canned response to keep
        the test suite fully deterministic and network-free.
        """
        prompt = str(prompt).strip()
        if not prompt:
            raise ValueError("prompt must not be empty")

        offline = os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1"
        if offline:
            # Deterministic stub keeps CI stable
            reply = "(stub) Thanks for sharing – how can I assist further with your essay?"
        else:
            # Live LLM call via shared helper (handles retries & caching)
            reply = _chat(prompt)

        return {
            "reply": reply,
        }

    # Optional async override – rely on ValidatedTool's default _arun_wrapper 