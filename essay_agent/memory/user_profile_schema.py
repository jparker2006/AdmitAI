"""
Pydantic schema for user profile structure.

NOTE: Spec is truncated for brevity in MVP. Complete all fields as per
``docs/essay_writing_agent.md`` when implementing full functionality.
"""

from typing import List, Dict, Optional

from pydantic import BaseModel


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


class UserProfile(BaseModel):
    user_info: UserInfo
    academic_profile: AcademicProfile
    core_values: List[CoreValue]
    # TODO: add defining_moments, writing_voice, essay_history, etc. 