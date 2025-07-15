"""essay_agent.portfolio.models

Portfolio-specific data models for multi-essay management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field

from essay_agent.models import EssayPrompt, UserProfile, EssayDraft


class EssayTask(BaseModel):
    """Individual essay task with metadata and progress tracking."""
    
    id: str = Field(..., description="Unique task identifier")
    prompt: EssayPrompt = Field(..., description="Essay prompt and requirements")
    profile: UserProfile = Field(..., description="User profile for personalization")
    college_id: str = Field(..., description="College/organization identifier")
    deadline: datetime = Field(..., description="Essay submission deadline")
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(
        default="pending", description="Current task status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    draft: Optional[EssayDraft] = Field(default=None, description="Current essay draft")
    used_stories: List[str] = Field(default_factory=list, description="Stories used in this essay")
    priority_score: float = Field(default=0.0, description="Calculated priority score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StoryUsage(BaseModel):
    """Track story usage across essays to prevent repetition."""
    
    story_id: str = Field(..., description="Unique story identifier")
    story_title: str = Field(..., description="Human-readable story title")
    used_in_tasks: List[str] = Field(default_factory=list, description="Task IDs using this story")
    college_ids: List[str] = Field(default_factory=list, description="Colleges where story was used")
    
    def can_use_for_college(self, college_id: str) -> bool:
        """Check if story can be used for a specific college."""
        return college_id not in self.college_ids


class PortfolioStatus(BaseModel):
    """Comprehensive portfolio status report."""
    
    user_id: str = Field(..., description="User identifier")
    total_essays: int = Field(..., description="Total number of essays in portfolio")
    completed: int = Field(..., description="Number of completed essays")
    in_progress: int = Field(..., description="Number of essays in progress")
    pending: int = Field(..., description="Number of pending essays")
    failed: int = Field(..., description="Number of failed essays")
    next_deadline: Optional[datetime] = Field(default=None, description="Next upcoming deadline")
    story_usage: Dict[str, StoryUsage] = Field(default_factory=dict, description="Story usage tracking")
    completion_rate: float = Field(..., description="Portfolio completion rate (0.0-1.0)")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def is_complete(self) -> bool:
        """Check if portfolio is fully completed."""
        return self.pending == 0 and self.in_progress == 0 and self.total_essays > 0 