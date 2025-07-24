"""
Pydantic schema for user profile structure.

NOTE: Spec is truncated for brevity in MVP. Complete all fields as per
``docs/essay_writing_agent.md`` when implementing full functionality.
"""

from typing import List, Dict, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Activity(BaseModel):
    name: str
    role: str
    duration: str = Field(default="N/A")  # Make optional with default
    description: str = Field(default="")  # Make optional with default  
    impact: str


class AcademicProfile(BaseModel):
    gpa: Optional[float] = None  # Make optional
    test_scores: Dict[str, Optional[int]] = Field(default_factory=dict)  # Make optional
    courses: List[str] = Field(default_factory=list)  # Make optional
    activities: List[Activity]


class CoreValue(BaseModel):
    value: str
    description: str
    evidence: List[str] = Field(default_factory=list)
    used_in_essays: List[str] = Field(default_factory=list)
    importance_level: int = Field(default=8, ge=1, le=10)


class UserInfo(BaseModel):
    name: str
    grade: int = Field(default=12)  # Make optional with default
    intended_major: str
    college_list: List[str] = Field(default_factory=list)  # Make optional
    platforms: List[str] = Field(default_factory=list)  # Make optional


class DefiningMoment(BaseModel):
    title: str
    description: str
    emotional_impact: str = Field(default="")  # Make optional with default
    lessons_learned: str = Field(default="")  # Make optional with default
    used_in_essays: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    story_category: str = Field(
        default="defining_moment",
        description="Story category aligned with brainstorm tool: heritage, creative, obstacle, accomplishment, service, defining_moment, etc."
    )
    story_weight: float = Field(
        default=1.0,
        description="Relative weight for story selection (1.0 = equal, >1.0 = higher priority)"
    )
    college_usage: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Maps college_id -> [prompt_ids] where story was used"
    )

    @field_validator('story_category')
    @classmethod
    def validate_story_category(cls, v: str) -> str:
        """Validate and migrate story categories to new schema.
        
        This function ensures backward compatibility by automatically converting
        old category names to new ones when loading existing profiles.
        
        Args:
            profile: UserProfile with potentially old story categories
            
        Returns:
            UserProfile with updated story categories
        """
        # Map old categories to new brainstorm tool categories
        category_mapping = {
            # Old schema -> New schema (aligned with brainstorm tool)
            'identity': 'heritage',
            'passion': 'creative', 
            'challenge': 'obstacle',
            'achievement': 'accomplishment',
            'community': 'service',
            'general': 'defining_moment'
        }
        
        # If it's already a new category, keep it
        valid_new_categories = {
            'heritage', 'family', 'cultural', 'personal_defining',
            'creative', 'academic', 'intellectual', 'hobby',
            'obstacle', 'failure', 'conflict', 'problem_solving',
            'accomplishment', 'leadership', 'growth', 'skill',
            'service', 'cultural_involvement', 'social_impact', 'tradition',
            'defining_moment', 'values', 'experiences'
        }
        
        if v in valid_new_categories:
            return v
        
        # Apply mapping for old categories
        return category_mapping.get(v, v)


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


def migrate_story_categories(profile: UserProfile) -> UserProfile:
    """Migrate existing story categories to new schema.
    
    This function ensures backward compatibility by automatically converting
    old category names to new ones when loading existing profiles.
    
    Args:
        profile: UserProfile with potentially old story categories
        
    Returns:
        UserProfile with updated story categories
    """
    # The field validator will automatically handle migration when the profile
    # is re-instantiated, so we just need to trigger validation
    try:
        # Create a new profile instance to trigger validation
        migrated_profile = UserProfile.model_validate(profile.model_dump())
        return migrated_profile
    except Exception as e:
        # If migration fails, log the error but return original profile
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to migrate story categories: {e}")
        return profile 