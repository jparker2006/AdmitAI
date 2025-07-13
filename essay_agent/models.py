from __future__ import annotations

"""essay_agent.models

Central data models shared across the Essay Agent code-base.

This module intentionally holds only *structure* – no heavy business
logic – so the models can be imported by any layer (CLI, memory,
LangGraph, FastAPI, etc.) without triggering extra dependencies.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator, conint

# ---------------------------------------------------------------------------
# Re-export existing UserProfile schema to provide a single canonical import
# ---------------------------------------------------------------------------
from essay_agent.memory.user_profile_schema import (
    UserProfile as _UserProfile,  # noqa: F401 – keep alias clear
)

# Simple alias works; subclassing would duplicate schema metadata.
UserProfile = _UserProfile  # type: ignore[assignment]

__all__ = [
    "EssayPrompt",
    "EssayDraft",
    "EssayFeedback",
    "UserProfile",
]


class EssayPrompt(BaseModel):
    """User-provided essay prompt metadata."""

    text: str = Field(..., description="The actual essay prompt text.")
    word_limit: int = Field(
        650,
        ge=10,
        le=1000,
        description="Maximum word count allowed by the prompt.",
    )
    college: Optional[str] = Field(
        default=None, description="College or organization issuing the prompt."
    )
    additional_instructions: Optional[str] = Field(
        default=None, description="Any extra instructions supplied by the user."
    )

    # Validators -------------------------------------------------------------

    @field_validator("text")
    @classmethod
    def _strip_and_validate_text(cls, v: str) -> str:  # noqa: D401 – imperative style
        v = v.strip()
        if not v:
            raise ValueError("Prompt text must not be empty or whitespace only.")
        return v


class EssayFeedback(BaseModel):
    """Structured feedback for an essay draft."""

    reviewer: str = Field(
        default="system", description="Who provided the feedback (system/peer/etc.)."
    )
    comments: str = Field(..., min_length=5)
    score: Optional[Dict[str, conint(ge=0, le=10)]] = Field(  # type: ignore[type-arg]
        default=None,
        description="Rubric scores, each 0–10 (e.g., {'clarity': 8, 'voice': 7}).",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EssayDraft(BaseModel):
    """A versioned essay draft with optional feedback list."""

    prompt: EssayPrompt
    draft_text: str = Field(..., min_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    version: int = Field(1, ge=1)
    feedback: List[EssayFeedback] = Field(default_factory=list)

    # Example for schema docs -------------------------------------------------
    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt": {
                    "text": "Describe a challenge you overcame.",
                    "word_limit": 650,
                    "college": "Generic University",
                },
                "draft_text": "When I first moved to the U.S., I struggled to...",
                "version": 1,
            }
        }
    }

    # Validators -------------------------------------------------------------

    @field_validator("updated_at")
    @classmethod
    def _validate_updated_at(cls, v: Optional[datetime], info):  # noqa: D401
        if v and v < info.data.get("created_at"):
            raise ValueError("updated_at cannot be earlier than created_at.")
        return v 