from __future__ import annotations

"""essay_agent.memory.rag

Factory helpers for Retrieval-Augmented Generation (RAG) over user memory.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging

from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.vectorstores.base import VectorStoreRetriever

from .hierarchical import HierarchicalMemory
from .semantic_search import SemanticSearchIndex
from ..prompts.rag import RAG_PROMPT

logger = logging.getLogger(__name__)

__all__ = ["RAGConfig", "build_rag_chain"]


@dataclass
class RAGConfig:
    top_k: int = 4
    chain_type: str = "qa"  # "qa" | "conv"
    prompt_path: Optional[Path] = None  # allow custom prompt file


class RAGError(RuntimeError):
    """Raised when building the RAG chain fails."""


def _load_prompt(config: RAGConfig) -> PromptTemplate:  # noqa: D401
    if config.prompt_path and config.prompt_path.exists():
        template = config.prompt_path.read_text()
    else:
        template = RAG_PROMPT
    return PromptTemplate.from_template(template)


def build_rag_chain(
    user_id: str,
    llm,  # any LangChain-compatible LLM
    memory: HierarchicalMemory,
    *,
    top_k: int | None = None,
    chain_type: str = "qa",
    prompt_path: Path | None = None,
):
    """Return RetrievalQA or ConversationalRetrievalChain grounded in user memory."""

    # ------------------------------------------------------------------
    config = RAGConfig(top_k=top_k or 4, chain_type=chain_type, prompt_path=prompt_path)

    # Build / load vector store ----------------------------------------
    index = SemanticSearchIndex.load_or_build(user_id, memory.profile)
    # Build retriever ----------------------------------------------------
    if hasattr(index._vs, "as_retriever"):
        retriever: VectorStoreRetriever = index._vs.as_retriever(search_kwargs={"k": config.top_k})  # type: ignore[attr-defined]
    else:
        from langchain.schema import Document
        from pydantic import PrivateAttr
        try:
            from langchain_core.retrievers import BaseRetriever  # type: ignore
        except ImportError:
            from langchain.retrievers import BaseRetriever  # type: ignore

        class _ListRetriever(BaseRetriever):
            k: int = 4  # public field for pydantic
            _idx: any = PrivateAttr()

            def __init__(self, lst_index, k: int):
                super().__init__(k=k)
                object.__setattr__(self, "_idx", lst_index)

            def get_relevant_documents(self, query: str):  # noqa: D401
                docs_scores = self._idx.similarity_search_with_score(query, k=self.k)
                return [Document(page_content=d.page_content, metadata=d.metadata) for d, _ in docs_scores]

            async def aget_relevant_documents(self, query: str):  # noqa: D401
                return self.get_relevant_documents(query)

        retriever = _ListRetriever(index._vs, config.top_k)  # type: ignore

    prompt = _load_prompt(config)

    if config.chain_type == "qa":
        try:
            qa_chain = RetrievalQA.from_chain_type(
                llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=False,
                chain_type_kwargs={"prompt": prompt},
            )
            return qa_chain
        except Exception as exc:  # noqa: BLE001
            raise RAGError(str(exc)) from exc

    if config.chain_type == "conv":
        try:
            conv_chain = ConversationalRetrievalChain.from_llm(
                llm,
                retriever,
                combine_docs_chain_kwargs={"prompt": prompt},
            )
            return conv_chain
        except Exception as exc:  # noqa: BLE001
            raise RAGError(str(exc)) from exc

    raise ValueError(f"Unsupported chain_type: {chain_type}") 