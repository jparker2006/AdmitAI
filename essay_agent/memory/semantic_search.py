from __future__ import annotations

"""essay_agent.memory.semantic_search

SemanticSearchIndex encapsulates vector-based semantic retrieval over the
user's long-term *semantic* tier (CoreValue + DefiningMoment).  It stores a
per-user FAISS index persisted under ``memory_store/vector_indexes/{user_id}``
and uses OpenAI embeddings when an API key is configured.  When running
offline or without an API key the class falls back to a deterministic local
hash-embedding implementation so unit tests do not require network access.

Public API::

    idx = SemanticSearchIndex.load_or_build(user_id, user_profile)
    results: list[SemanticItem] = idx.search("leadership", k=3)

The class purposefully does *not* expose mutating helpers; instead we rebuild
(or incrementally append) the index whenever ``load_or_build`` is called.  The
profile object passed in already contains the authoritative list of semantic
items, guaranteeing consistency between profile JSON and the FAISS index.
"""

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple, Union
import json
import os
import hashlib

from filelock import FileLock

# LangChain imports – guarded so tests do not break if optional deps missing
try:
    from langchain.vectorstores.faiss import FAISS
    from langchain.embeddings.openai import OpenAIEmbeddings
    try:
        from langchain.embeddings.base import Embeddings  # LangChain < 0.1.5
    except ImportError:  # pragma: no cover – newer split package
        from langchain_core.embeddings import Embeddings  # type: ignore
    from langchain.docstore.document import Document
except ImportError as exc:  # pragma: no cover – dev environment issue
    raise ImportError("LangChain>=0.1.0 and faiss-cpu must be installed") from exc

from . import _profile_path  # storage root helper
from .user_profile_schema import CoreValue, DefiningMoment, UserProfile

SemanticItem = Union[CoreValue, DefiningMoment]

__all__ = ["SemanticSearchIndex"]

# ---------------------------------------------------------------------------
# Deterministic offline embedding helper
# ---------------------------------------------------------------------------


class _DeterministicEmbeddings(Embeddings):
    """Simple hash-based embedding to avoid network calls in unit tests."""

    _dim: int = 1536

    def _hash(self, text: str) -> List[float]:  # noqa: D401
        # Create a deterministic pseudo-vector from sha256 hexdigests
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Repeat digest bytes to fill 1536 floats, normalise to 0-1 range
        raw = list(digest) * (self._dim // len(digest) + 1)
        return [b / 255.0 for b in raw[: self._dim]]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:  # noqa: D401
        return [self._hash(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:  # noqa: D401
        return self._hash(text)


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------


class SemanticSearchIndex:  # pylint: disable=too-few-public-methods
    """Vector-based semantic search helper (per user)."""

    # ------------------------ construction helpers -------------------------

    def __init__(self, user_id: str, vectorstore: "FAISS"):
        self.user_id = user_id
        self._vs: FAISS = vectorstore

    # ---------------------------------------------------------------------
    # Public factory -------------------------------------------------------
    # ---------------------------------------------------------------------

    @classmethod
    def load_or_build(
        cls,
        user_id: str,
        profile: UserProfile,
        *,
        embeddings: "Embeddings" | None = None,
    ) -> "SemanticSearchIndex":
        """Return a ready-to-use index for *user_id* – build if missing."""

        index_dir = cls._index_dir(user_id)
        index_dir.mkdir(parents=True, exist_ok=True)
        lock = FileLock(str(index_dir) + ".lock")

        # ------------------------------------------------------------------
        if embeddings is None:
            embeddings = cls._get_default_embeddings()

        with lock:
            faiss_path = index_dir / "index.faiss"
            pkl_path = index_dir / "index.pkl"

            try:
                if faiss_path.exists() and pkl_path.exists():
                    vs = FAISS.load_local(
                        str(index_dir), embeddings, allow_different_embedding=True
                    )
                    return cls(user_id, vs)

                # Build from scratch ---------------------------------------
                items: List[SemanticItem] = list(profile.core_values) + list(profile.defining_moments)
                if not items:
                    # Create an empty (dummy) vector store ------------------
                    vs = FAISS.from_texts(
                        ["__dummy__"], embeddings, metadatas=[{"_dummy": True}]
                    )
                    vs.docstore._dict.clear()
                    vs.index.reset()
                else:
                    texts, metas = cls._items_to_texts_and_metas(items)
                    vs = FAISS.from_texts(texts, embeddings, metadatas=metas)

                vs.save_local(str(index_dir))
                return cls(user_id, vs)
            except Exception:  # pragma: no cover – likely faiss import error
                # ------------------------------------------------------------------
                # FAISS unavailable – fall back to naive list index ----------------
                # ------------------------------------------------------------------

                class _ListIndex:  # pylint: disable=too-few-public-methods
                    def __init__(self, texts: List[str], metas: List[dict]):
                        self._texts = texts
                        self._metas = metas

                        # Pre-compute embeddings once
                        self._embeds = embeddings.embed_documents(texts) if texts else []

                    def similarity_search_with_score(self, query: str, k: int = 5):
                        if not self._texts:
                            return [], []

                        import numpy as np

                        q_emb = np.array(embeddings.embed_query(query))
                        scores: List[Tuple[int, float]] = []
                        for idx, emb in enumerate(self._embeds):
                            emb_vec = np.array(emb)
                            # Cosine similarity (dot for normalized vectors)
                            sim = float(np.dot(q_emb, emb_vec) / (np.linalg.norm(q_emb) * np.linalg.norm(emb_vec) + 1e-12))
                            scores.append((idx, 1 - sim))  # lower is better to mimic FAISS score

                        scores.sort(key=lambda t: t[1])
                        from langchain.docstore.document import Document

                        results = []
                        for idx, score in scores[:k]:
                            results.append(
                                (
                                    Document(page_content=self._texts[idx], metadata=self._metas[idx]),
                                    score,
                                )
                            )
                        return results

                    # alias used later ------------------------------------
                    def similarity_search(self, query: str, k: int = 5):
                        docs_scores = self.similarity_search_with_score(query, k)
                        return [doc for doc, _ in docs_scores]

                items: List[SemanticItem] = list(profile.core_values) + list(profile.defining_moments)
                texts, metas = cls._items_to_texts_and_metas(items) if items else ([], [])
                fallback_vs = _ListIndex(texts, metas)
                return cls(user_id, fallback_vs)  # type: ignore[arg-type]

    # ------------------------------ public API -----------------------------

    def search(self, query: str, k: int = 5) -> List[SemanticItem]:  # noqa: D401
        """Return *k* most similar semantic items to *query*."""

        try:
            docs_and_scores: List[Tuple[Document, float]] = self._vs.similarity_search_with_score(query, k=k)
        except Exception:  # pragma: no cover – e.g. empty index
            return []

        # Docs are already sorted by score ascending (lower == closer)
        results: List[SemanticItem] = []
        for doc, _score in docs_and_scores:
            meta = doc.metadata or {}
            if meta.get("_dummy"):
                continue
            results.append(self._meta_to_item(meta))
        return results

    # Placeholder – proper clustering can come later
    def cluster(self, num_clusters: int = 3) -> List[List[SemanticItem]]:  # noqa: D401
        """Very naive clustering: splits the index into *num_clusters* equal chunks."""

        # Fetch up to 1k docs; for MVP we assume semantic tier is small.
        all_docs = self._vs.similarity_search("", k=1000)
        chunks: List[List[SemanticItem]] = [[] for _ in range(num_clusters)]
        for idx, doc in enumerate(all_docs):
            cluster_idx = idx % num_clusters
            chunks[cluster_idx].append(self._meta_to_item(doc.metadata))
        return chunks

    # ------------------------------------------------------------------
    # Internal helpers -------------------------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _get_default_embeddings() -> "Embeddings":  # noqa: D401
        if os.getenv("OPENAI_API_KEY"):
            # Use OpenAI embeddings when API key available
            return OpenAIEmbeddings()
        return _DeterministicEmbeddings()

    @staticmethod
    def _index_dir(user_id: str) -> Path:  # noqa: D401
        return _profile_path(user_id).with_suffix("").with_name(user_id).parent / "vector_indexes" / user_id

    # Conversion helpers ---------------------------------------------------

    @staticmethod
    def _items_to_texts_and_metas(items: Sequence[SemanticItem]) -> Tuple[List[str], List[dict]]:
        texts: List[str] = []
        metas: List[dict] = []
        for item in items:
            if isinstance(item, CoreValue):
                text = f"Core Value: {item.value}. {item.description}"
                metas.append({"type": "CoreValue", "data": json.loads(item.model_dump_json())})
            elif isinstance(item, DefiningMoment):
                text = f"Defining Moment: {item.title}. {item.description} {item.lessons_learned}"
                metas.append({"type": "DefiningMoment", "data": json.loads(item.model_dump_json())})
            else:
                raise ValueError("Unsupported semantic item type")
            texts.append(text)
        return texts, metas

    @staticmethod
    def _meta_to_item(meta: dict) -> SemanticItem:  # noqa: D401
        typ = meta.get("type")
        data = meta.get("data", {})
        if typ == "CoreValue":
            return CoreValue(**data)
        if typ == "DefiningMoment":
            return DefiningMoment(**data)
        raise ValueError("Unknown metadata type: " + str(typ)) 