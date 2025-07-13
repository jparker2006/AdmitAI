"""essay_agent.query_rewriter

LLMChain-powered helpers for rewriting user queries, compressing conversation
context, and clarifying vague questions.  The class centralises three chains
backed by GPT-4 via the shared ``get_chat_llm`` factory.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms.base import BaseLLM  # type: ignore

from essay_agent.llm_client import get_chat_llm
from essay_agent.prompts.query_rewrite import (
    REWRITE_PROMPT,
    COMPRESS_PROMPT,
    CLARIFY_PROMPT,
)

__all__ = ["QueryRewriter"]


@dataclass
class _LazyChain:
    """Descriptor to lazily build a cached :class:`LLMChain`."""

    prompt: PromptTemplate
    chain: Optional[LLMChain] = field(default=None, init=False, repr=False)

    def __get__(self, instance, owner):  # noqa: D401
        if instance is None:
            return self  # accessing on class
        if self.chain is None:
            llm: BaseLLM = get_chat_llm()
            self.chain = LLMChain(llm=llm, prompt=self.prompt)
        return self.chain


class QueryRewriter:  # pylint: disable=too-few-public-methods
    """Utility class wrapping three query-optimisation chains."""

    _rewrite_chain: _LazyChain = _LazyChain(REWRITE_PROMPT)  # type: ignore
    _compress_chain: _LazyChain = _LazyChain(COMPRESS_PROMPT)  # type: ignore
    _clarify_chain: _LazyChain = _LazyChain(CLARIFY_PROMPT)  # type: ignore

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rewrite_query(self, query: str, **llm_overrides: Any) -> str:  # noqa: D401
        """Return clearer version of *query*."""

        raw = self._rewrite_chain.invoke({"query": query}, **llm_overrides)
        return _extract_result(raw)

    def compress_context(self, context: str, max_tokens: int = 400, **llm_overrides: Any) -> str:  # noqa: D401
        """Compress *context* aiming for ``max_tokens`` tokens."""

        raw = self._compress_chain.invoke(
            {"context": context, "max_tokens": max_tokens}, **llm_overrides
        )
        return _extract_result(raw)

    def clarify_question(self, question: str, **llm_overrides: Any) -> str:  # noqa: D401
        """Return clarified version of *question*."""

        raw = self._clarify_chain.invoke({"query": question}, **llm_overrides)
        return _extract_result(raw)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _extract_result(raw: Any) -> str:  # noqa: D401
    """Parse JSON ``raw`` from LLM and return ``result`` field.

    LangChain ``LLMChain`` returns a dict ``{"text": <str>, ...input_vars}``.
    Accept either a plain string or that dict.
    """

    if isinstance(raw, dict) and "text" in raw:
        raw = raw["text"]

    try:
        data: Dict[str, Any] = json.loads(str(raw).strip())
        return data["result"].strip()
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid LLM output; expected JSON with 'result' key") from exc 