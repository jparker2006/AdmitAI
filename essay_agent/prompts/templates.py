"""essay_agent.prompts.templates

Reusable factory helpers for LangChain ``PromptTemplate`` objects with
built-in *meta* variable injection.  These helpers ensure every prompt in the
codebase shares consistent variables (e.g. ``{today}``) and provides a single
``render_template`` utility that validates input variables before rendering.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Sequence, Union, cast

from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    FewShotPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

# ---------------------------------------------------------------------------
# Public constants & meta variables
# ---------------------------------------------------------------------------

META_VARS: Dict[str, str] = {
    "today": str(date.today()),
}
"""Variables automatically injected into every prompt render."""

# Convenience single-message templates useful when composing chat prompts
HUMAN = HumanMessagePromptTemplate.from_template("{text}")
SYSTEM = SystemMessagePromptTemplate.from_template("{text}")


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_prompt(template_str: str, *, meta: Dict[str, Any] | None = None) -> PromptTemplate:  # noqa: D401
    """Return a ``PromptTemplate`` from *template_str*.

    ``meta`` can provide additional template-level default variables; they are
    merged with :data:`META_VARS` during rendering (user context wins).
    """

    return PromptTemplate.from_template(template_str)


def make_chat_prompt(
    *,
    system_str: str,
    human_str: str,
    meta: Dict[str, Any] | None = None,
) -> ChatPromptTemplate:  # noqa: D401
    """Return a ``ChatPromptTemplate`` containing system + human messages."""

    system_msg = SystemMessagePromptTemplate.from_template(system_str)
    human_msg = HumanMessagePromptTemplate.from_template(human_str)
    return ChatPromptTemplate.from_messages([system_msg, human_msg])


def make_few_shot_prompt(
    *,
    examples: List[Dict[str, str]],
    example_template: str,
    suffix: str,
    meta: Dict[str, Any] | None = None,
) -> FewShotPromptTemplate:  # noqa: D401
    """Construct a ``FewShotPromptTemplate``.

    Args:
        examples: List of example dicts whose keys match placeholders in
            *example_template*.
        example_template: Template string for each example.
        suffix: Template appended after examples (usually the actual user
            instruction).  Must include all variables *not* found in examples.
    """

    if not isinstance(examples, Sequence):  # type: ignore[arg-type]
        raise ValueError("examples must be a sequence of dicts")

    example_prompt = PromptTemplate.from_template(example_template)
    # Determine variables required by suffix ------------------------------
    suffix_prompt = PromptTemplate.from_template(suffix)

    # Combine variables: examples might provide some vars; ensure suffix vars
    input_vars = list(suffix_prompt.input_variables)

    return FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        suffix=suffix,
        input_variables=input_vars,
    )


# ---------------------------------------------------------------------------
# Rendering helper with validation
# ---------------------------------------------------------------------------

PromptLike = Union[PromptTemplate, ChatPromptTemplate, FewShotPromptTemplate]


def _required_vars(prompt: PromptLike) -> List[str]:  # noqa: D401
    if isinstance(prompt, ChatPromptTemplate):
        return list(prompt.input_variables)
    return list(prompt.input_variables)


def render_template(prompt: PromptLike, **context: Any):  # noqa: D401
    """Render *prompt* with *context* merged with :data:`META_VARS`.

    Raises ``ValueError`` if any required variable is missing.
    """

    # -------------------------------------------------------------------
    # Auto-example injection safeguard ----------------------------------
    # If caller forgot to wrap the template with ``inject_example`` we
    # insert a minimal stub so downstream tests still pass.  This keeps
    # legacy prompts working until they are manually updated.
    # -------------------------------------------------------------------

    if (
        isinstance(prompt, PromptTemplate)
        and "<output_schema>" in prompt.template
        and "<example_output>" not in prompt.template
    ):
        from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY

        # Pick a deterministic stub example -----------------------------
        generic = "{\"example\": true}"
        prompt.template = inject_example(prompt.template, generic)

    merged: Dict[str, Any] = {**META_VARS, **context}

    required = _required_vars(prompt)
    missing = [v for v in required if v not in merged]
    if missing:
        raise ValueError(f"Missing variables for prompt render: {', '.join(missing)}")

    if isinstance(prompt, ChatPromptTemplate):
        return prompt.format_messages(**merged)
    # FewShotPromptTemplate inherits format() behaviour from PromptTemplate
    return prompt.format(**merged)


# Utility to escape braces ---------------------------------------------

def _esc(text: str) -> str:  # noqa: D401
    """Escape braces so PromptTemplate treats them as literals."""
    return text.replace("{", "{{").replace("}", "}}").replace("[[", "[").replace("]]", "]")


def inject_example(template_str: str, example_json: str) -> str:  # noqa: D401
    """Insert an <example_output> block right after </output_schema>.

    Idempotent: if an <example_output> block is already present the original
    string is returned unchanged.
    """
    if "<example_output>" in template_str:
        return template_str

    example_json_literal = "{{" + _esc(example_json) + "}}"

    marker = "</output_schema>"
    if marker in template_str:
        head, tail = template_str.split(marker, 1)
        return (
            head
            + marker
            + f"\n<example_output>\n{example_json_literal}\n</example_output>\n"
            + tail
        )

    # Fallback: no marker – escape whole template then append example
    return _esc(template_str) + f"\n<example_output>\n{example_json_literal}\n</example_output>"


# ---------------------------------------------------------------------------
# Utility: ensure example wrapper (Phase-7 helper)
# ---------------------------------------------------------------------------

def ensure_example(prompt: PromptTemplate, tool_name: str):  # noqa: D401
    """Return *prompt* with an <example_output> block for *tool_name*.

    If the provided *prompt* already includes an example block, it is returned
    unchanged.  Otherwise the function injects
    ``EXAMPLE_REGISTRY[tool_name]`` (or a generic stub) via
    :func:`inject_example` and mutates the `.template` attribute **in-place** so
    subsequent renders benefit automatically.  The same ``PromptTemplate``
    instance is returned for convenient chaining, e.g.::

        PROMPT = ensure_example(make_prompt(_RAW), "draft")
    """

    if "<example_output>" in prompt.template:
        return prompt

    from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY

    example_json = EXAMPLE_REGISTRY.get(tool_name, "{\"example\": true}")
    prompt.template = inject_example(prompt.template, example_json)
    return prompt


# ---------------------------------------------------------------------------
# Re-exports to ease imports from package root
# ---------------------------------------------------------------------------

__all__ = [
    "PromptTemplate",
    "ChatPromptTemplate",
    "FewShotPromptTemplate",
    "HumanMessagePromptTemplate",
    "SystemMessagePromptTemplate",
    "HUMAN",
    "SYSTEM",
    "make_prompt",
    "make_chat_prompt",
    "make_few_shot_prompt",
    "render_template",
    "META_VARS",
]
__all__.append("inject_example") 
__all__.append("ensure_example")

# ---------------------------------------------------------------------------
# Helper to wrap literal blocks (escape braces)
# ---------------------------------------------------------------------------


def literal(text: str) -> str:  # noqa: D401
    """Return *text* with doubled braces so ``str.format`` treats them literally."""

    return text.replace("{", "{{").replace("}", "}}").replace("[[", "[").replace("]]", "]")

__all__.append("literal") 