"""essay_agent.tools.echo

LangChain-compatible Echo tool used for debugging and plumbing tests.

The tool simply returns the provided message wrapped in a dict.  It is
registered in ``essay_agent.tools.__init__`` so that the Executor can
invoke it via the standard ``TOOL_REGISTRY``.
"""

from __future__ import annotations

from typing import Any, Dict

from langchain.tools import BaseTool


class EchoTool(BaseTool):
    """Return whatever message is passed in.

    This is primarily useful for smoke-testing the tool registry and
    executor pipeline while heavier tools are still under construction.
    """

    name: str = "echo"
    description: str = (
        "Debugging / smoke-test tool that echoes a message back in a wrapper dict."
    )

    # We return the value directly so LangChain does not attempt additional parsing
    return_direct: bool = True

    # ------------------------------------------------------------------
    # LangChain sync execution
    # ------------------------------------------------------------------
    def _run(self, message: str = "Hello, Essay Agent!", **kwargs: Any) -> Dict[str, str]:
        """Synchronous run method required by ``BaseTool``.

        Args:
            message: The text to echo back. If empty or whitespace only, a
                ``ValueError`` is raised.
            **kwargs: Ignored – allows executor to pass extra params.
        Returns:
            dict: ``{"echo": <message>}``
        """
        message = str(message).strip()
        if not message:
            raise ValueError("Message must not be empty.")
        return {"echo": message}

    # ------------------------------------------------------------------
    # LangChain async execution – not needed for MVP
    # ------------------------------------------------------------------
    async def _arun(self, *args: Any, **kwargs: Any) -> Dict[str, str]:  # noqa: D401
        """Async placeholder – raises until async support is implemented."""
        raise NotImplementedError("EchoTool does not support async execution yet.")

    # ------------------------------------------------------------------
    # Provide ergonomic call signatures for MVP convenience
    # ------------------------------------------------------------------
    def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        """Invoke the tool.

        Supports three invocation styles:

        1. ``tool()`` – uses the default greeting.
        2. ``tool(message="Hi")`` – explicit keyword.
        3. ``tool("Hi")`` or ``tool(tool_input="Hi")`` – standard BaseTool.
        """

        # Allow explicit "message" keyword -------------------------------------------------
        if "message" in kwargs:
            if args:
                raise ValueError("Provide either positional 'tool_input' or 'message', not both.")
            return self._run(kwargs.pop("message"))

        # No input provided – fall back to default -----------------------------------------
        if not args and not kwargs:
            return self._run("Hello, Essay Agent!")

        # Delegate to BaseTool's __call__ implementation -----------------------------------
        return super().__call__(*args, **kwargs) 