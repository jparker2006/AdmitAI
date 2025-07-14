"""
Pydantic schema for user profile structure.

NOTE: Spec is truncated for brevity in MVP. Complete all fields as per
``docs/essay_writing_agent.md`` when implementing full functionality.
"""

from typing import List, Dict, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class Activity(BaseModel):
    name: str
    role: str
    duration: str
    description: str
    impact: str


class AcademicProfile(BaseModel):
    gpa: Optional[float]
    test_scores: Dict[str, Optional[int]]
    courses: List[str]
    activities: List[Activity]


class CoreValue(BaseModel):
    value: str
    description: str
    evidence: List[str]
    used_in_essays: List[str]


class UserInfo(BaseModel):
    name: str
    grade: int
    intended_major: str
    college_list: List[str]
    platforms: List[str]


class DefiningMoment(BaseModel):
    title: str
    description: str
    emotional_impact: str
    lessons_learned: str
    used_in_essays: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    story_category: str = Field(
        default="general",
        description="Category: identity, passion, challenge, achievement, community, general"
    )
    story_weight: float = Field(
        default=1.0,
        description="Relative weight for story selection (1.0 = equal, >1.0 = higher priority)"
    )
    college_usage: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Maps college_id -> [prompt_ids] where story was used"
    )


class WritingVoice(BaseModel):
    tone_preferences: List[str] = Field(default_factory=list)
    vocabulary_level: str
    sentence_patterns: List[str] = Field(default_factory=list)
    stylistic_traits: List[str] = Field(default_factory=list)


class EssayVersion(BaseModel):
    version: int
    timestamp: datetime
    content: str
    word_count: int
    scores: Dict[str, float] = Field(default_factory=dict)
    feedback: List[str] = Field(default_factory=list)
    used_stories: List[str] = Field(default_factory=list)
    used_values: List[str] = Field(default_factory=list)


class EssayRecord(BaseModel):
    prompt_id: str
    prompt_text: str
    platform: str
    versions: List[EssayVersion] = Field(default_factory=list)
    final_version: int = 0
    status: str  # expected: "draft", "revision", "complete"


class UserProfile(BaseModel):
    user_info: UserInfo
    academic_profile: AcademicProfile
    core_values: List[CoreValue]
    defining_moments: List[DefiningMoment] = Field(default_factory=list)
    writing_voice: Optional[WritingVoice] = None
    essay_history: List[EssayRecord] = Field(default_factory=list)
    college_story_usage: Dict[str, Dict[str, List[str]]] = Field(
        default_factory=dict,
        description="Maps college_id -> prompt_type -> [story_titles] for tracking story diversification"
    ) 