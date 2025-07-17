"""essay_agent.llm_client

Reusable LangChain-OpenAI client with cost tracking, caching and retry logic.

This module centralises configuration for GPT-4-based ChatOpenAI / OpenAI models
so the rest of the codebase can import a pre-configured client instead of
instantiating LLMs ad-hoc.  Key features:

* Automatic SQLite or in-memory cache using ``langchain.cache``.
* Cost & token accounting via ``get_openai_callback`` context manager.
* Exponential back-off retry decorator (via *tenacity*) wrapping common helpers.
* Rate limiting to prevent API quota exhaustion.
* Graceful degradation: when ``OPENAI_API_KEY`` is absent, falls back to
  ``FakeListLLM`` to allow offline / CI execution without hitting the network.

Example
-------
>>> from essay_agent.llm_client import track_cost
>>> with track_cost() as (llm, cb):
...     answer = llm.predict("Say hello!")
...     print(cb.total_cost)
"""
from __future__ import annotations

import contextlib
import functools
import os
import time
import threading
from typing import Any, Generator, Union, cast
import tiktoken  # Add tiktoken for token counting

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# LangChain cache -----------------------------------------------------------------
from langchain.cache import InMemoryCache, SQLiteCache
from langchain.globals import set_llm_cache

# Callback helper for cost tracking ------------------------------------------------
# New import path (LangChain >= 0.1.17)
try:
    from langchain_community.callbacks.manager import get_openai_callback  # type: ignore
except ImportError:  # pragma: no cover – fallback for older versions
    from langchain.callbacks import get_openai_callback  # type: ignore

# Fake LLM used when no API key is available ---------------------------------------
from langchain.llms.fake import FakeListLLM

# Import OpenAI implementations.  ``langchain_openai`` is preferred as of
# LangChain >=0.1.  Fall back to legacy modules if not available so the package
# can still import in minimal environments.
try:
    from langchain_openai import ChatOpenAI, OpenAI  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – legacy fallback
    from langchain.chat_models import ChatOpenAI  # type: ignore
    from langchain.llms.openai import OpenAI  # type: ignore


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_MODEL = os.getenv("ESSAY_AGENT_MODEL", "gpt-4o")
_CACHE_PATH = os.getenv("ESSAY_AGENT_CACHE_PATH", ".essay_agent_cache.sqlite")
_USE_CACHE = os.getenv("ESSAY_AGENT_CACHE", "1") == "1"

# BUGFIX: Add evaluation mode to disable caching during conversations
_EVALUATION_MODE = os.getenv("ESSAY_AGENT_EVALUATION_MODE", "0") == "1"

# Rate limiting configuration
_MIN_REQUEST_INTERVAL = float(os.getenv("ESSAY_AGENT_MIN_REQUEST_INTERVAL", "1.0"))  # seconds between requests
_last_request_time = 0.0
_request_lock = threading.Lock()

# Initialise global cache exactly once at import time.  SQLite is persistent,
# while the in-memory cache avoids disk I/O when disabled.
# BUGFIX: Disable caching in evaluation mode to prevent identical responses
if _USE_CACHE and not _EVALUATION_MODE:
    set_llm_cache(SQLiteCache(_CACHE_PATH))
else:  # pragma: no cover
    set_llm_cache(InMemoryCache())


def _rate_limit():
    """Enforce minimum interval between API requests to prevent rate limiting."""
    global _last_request_time
    
    with _request_lock:
        current_time = time.time()
        time_since_last = current_time - _last_request_time
        
        if time_since_last < _MIN_REQUEST_INTERVAL:
            sleep_time = _MIN_REQUEST_INTERVAL - time_since_last
            time.sleep(sleep_time)
        
        _last_request_time = time.time()


# ---------------------------------------------------------------------------
# Retry wrapper – applies to helper functions (not to the LLM instance itself)
# ---------------------------------------------------------------------------

def _retryable(fn):  # noqa: D401
    """Function decorator adding exponential back-off retry behaviour with rate limiting."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # Apply rate limiting before each request
        _rate_limit()
        return fn(*args, **kwargs)

    return cast(
        Any,
        retry(
            wait=wait_exponential(multiplier=1, min=2, max=30),  # Longer waits for better stability
            stop=stop_after_attempt(8),  # More attempts for better resilience
            retry=retry_if_exception_type((
                ConnectionError,
                TimeoutError,
                # Add common OpenAI API exceptions
                Exception,  # Broad catch for API issues - we'll refine this
            )),
        )(wrapper),
    )


# ---------------------------------------------------------------------------
# Factory helpers – cached so callers share the same object & callback stats
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _chat_llm(**overrides: Any):  # noqa: D401
    """Return a singleton ChatOpenAI instance (or ``FakeListLLM`` offline)."""

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            # Pop temperature from overrides if provided to avoid duplicate keys
            temperature = overrides.pop("temperature", 0.2)
            llm = ChatOpenAI(
                model_name=_DEFAULT_MODEL,
                temperature=temperature,
                max_retries=0,  # we handle retries at helper-function level
                **overrides,
            )
            # Backward-compat alias ------------------------------------
            if not hasattr(llm, "predict"):
                llm.predict = lambda prompt, **kw: llm.invoke(prompt, **kw)  # type: ignore[assignment]
            return llm
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Failed to instantiate ChatOpenAI: {exc}") from exc

    # Offline fall-back – deterministic fake responses enable CI tests
    return FakeListLLM(responses=["FAKE_RESPONSE"])  # type: ignore[return-value]


@functools.lru_cache(maxsize=1)
def _completion_llm(**overrides: Any):  # noqa: D401
    """Return a singleton completions-style OpenAI LLM (or fake offline)."""

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            return OpenAI(max_retries=0, **overrides)  # type: ignore[return-value]
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Failed to instantiate OpenAI LLM: {exc}") from exc

    return FakeListLLM(responses=["FAKE_RESPONSE"])  # type: ignore[return-value]


# Public APIs ----------------------------------------------------------------------


def get_chat_llm(**overrides: Any):  # noqa: D401
    """Return a cached **chat** LLM instance (GPT-4 by default)."""

    return _chat_llm(**overrides)


def get_completion_llm(**overrides: Any):  # noqa: D401
    """Return a cached **completions** LLM instance (legacy OpenAI)."""

    return _completion_llm(**overrides)


def set_evaluation_mode(enabled: bool = True):
    """Enable/disable evaluation mode to control caching behavior.
    
    Args:
        enabled: If True, disables LLM caching to ensure unique responses
    """
    global _EVALUATION_MODE
    _EVALUATION_MODE = enabled
    
    # Update cache based on evaluation mode
    if enabled:
        # Use in-memory cache for evaluation (no persistence)
        set_llm_cache(InMemoryCache())
    else:
        # Restore persistent cache for normal usage
        if _USE_CACHE:
            set_llm_cache(SQLiteCache(_CACHE_PATH))
        else:
            set_llm_cache(InMemoryCache())


def get_evaluation_mode() -> bool:
    """Check if evaluation mode is currently enabled.
    
    Returns:
        True if evaluation mode is active
    """
    global _EVALUATION_MODE
    return _EVALUATION_MODE


@contextlib.contextmanager
def track_cost(llm: Any | None = None, **overrides: Any) -> Generator[tuple[Any, Any], None, None]:  # noqa: ANN401, D401
    """Yield *(llm, callback)* where *callback* tracks tokens & cost.

    Useful for instrumentation:

    >>> from essay_agent.llm_client import track_cost
    >>> with track_cost() as (llm, cb):
    ...     _ = llm.predict("Hello")
    ...     print(cb.total_tokens, cb.total_cost)
    """

    with get_openai_callback() as cb:  # pragma: no cover – works even with FakeListLLM
        yield (llm or get_chat_llm(**overrides), cb)


# Convenience wrapper – suitable for quick one-off prompts -------------------------


@_retryable
def chat(prompt: str, **kwargs: Any) -> str:  # noqa: D401
    """Synchronous helper: call :pyfunc:`ChatOpenAI.predict` with retries."""

    llm = get_chat_llm()
    try:
        return call_llm(llm, prompt, **kwargs)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Unified invoke helper ------------------------------------------------------
# ---------------------------------------------------------------------------


@_retryable
def call_llm(llm: Any, prompt: str, **kwargs: Any) -> str:  # noqa: D401, ANN401
    """Call ``llm.invoke`` and normalise the return value to *str*."""

    if hasattr(llm, "invoke"):
        result = llm.invoke(prompt, **kwargs)
    elif hasattr(llm, "predict"):
        result = llm.predict(prompt, **kwargs)  # type: ignore[attr-defined]
    else:
        raise AttributeError("LLM instance has neither invoke nor predict method")

    # ChatOpenAI returns an AIMessage; FakeListLLM returns str
    if hasattr(result, "content"):
        return result.content  # type: ignore[attr-defined]
    return str(result)


# Internal re-export for typing convenience ----------------------------------------
ChatLLM_T = Union["ChatOpenAI", FakeListLLM]  # type: ignore[name-defined]
CompletionLLM_T = Union["OpenAI", FakeListLLM]  # type: ignore[name-defined] 

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4

def truncate_context(context: str, max_tokens: int = 25000, model: str = "gpt-4") -> str:
    """Truncate context to fit within token limit, preserving important parts."""
    current_tokens = count_tokens(context, model)
    
    if current_tokens <= max_tokens:
        return context
    
    # If it's JSON, try to truncate essay history first
    try:
        import json
        data = json.loads(context)
        
        # If it has essay_history, truncate it
        if isinstance(data, dict) and "essay_history" in data:
            essay_history = data["essay_history"]
            if isinstance(essay_history, list) and len(essay_history) > 3:
                # Keep only the 3 most recent essays
                data["essay_history"] = essay_history[-3:]
                truncated = json.dumps(data, indent=2)
                
                if count_tokens(truncated, model) <= max_tokens:
                    return truncated
        
        # If still too long, truncate more aggressively
        if isinstance(data, dict) and "essay_history" in data:
            data["essay_history"] = data["essay_history"][-1:] if data["essay_history"] else []
            truncated = json.dumps(data, indent=2)
            
            if count_tokens(truncated, model) <= max_tokens:
                return truncated
    
    except (json.JSONDecodeError, KeyError):
        pass
    
    # Fallback: simple character-based truncation
    target_chars = int(max_tokens * 3.5)  # Rough estimate
    if len(context) > target_chars:
        return context[:target_chars] + "\n... [truncated for length]"
    
    return context 