"""essay_agent.portfolio

Multi-essay portfolio management system supporting concurrent essay tasks,
story reuse enforcement, deadline prioritization, and task coordination.

This package provides:
- PortfolioManager: Central coordinator for multi-essay workflows
- TaskTracker: Task scheduling and progress tracking
- EssayTask, StoryUsage, PortfolioStatus: Portfolio-specific data models
"""

from .manager import PortfolioManager
from .task_tracker import TaskTracker
from .models import EssayTask, StoryUsage, PortfolioStatus

__all__ = [
    "PortfolioManager",
    "TaskTracker", 
    "EssayTask",
    "StoryUsage",
    "PortfolioStatus",
] 