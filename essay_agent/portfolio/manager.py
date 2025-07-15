"""essay_agent.portfolio.manager

Central coordinator for multi-essay portfolio management with story reuse enforcement.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from filelock import FileLock

from .models import EssayTask, StoryUsage, PortfolioStatus
from .task_tracker import TaskTracker
from essay_agent.models import EssayPrompt, UserProfile, EssayDraft
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.workflows.orchestrator import WorkflowOrchestrator, WorkflowConfig


class PortfolioManager:
    """Central coordinator for multi-essay portfolio management."""
    
    def __init__(self, user_id: str, orchestrator: Optional[WorkflowOrchestrator] = None):
        self.user_id = user_id
        self.task_tracker = TaskTracker(user_id)
        self.story_usage: Dict[str, StoryUsage] = {}
        self.storage_dir = Path("memory_store")
        self.storage_dir.mkdir(exist_ok=True)
        self.story_usage_file = self.storage_dir / f"{user_id}.portfolio.stories.json"
        self.story_lock_file = self.storage_dir / f"{user_id}.portfolio.stories.json.lock"
        self._load_story_usage()
        
        # Resource-aware orchestration
        self.orchestrator = orchestrator
        if orchestrator:
            self._resource_aware = True
        else:
            self._resource_aware = False
    
    def submit_essay_task(self, prompt: str, profile: UserProfile, 
                         college_id: str, deadline: datetime) -> str:
        """Submit new essay task and return task-id."""
        # Generate unique task ID
        task_id = self._generate_task_id()
        
        # Create essay prompt object
        essay_prompt = EssayPrompt(
            text=prompt,
            word_limit=650,  # Default, could be customized
            college=college_id
        )
        
        # Create essay task
        task = EssayTask(
            id=task_id,
            prompt=essay_prompt,
            profile=profile,
            college_id=college_id,
            deadline=deadline,
            status="pending"
        )
        
        # Enforce story reuse rules
        self._enforce_story_reuse_rules(task)
        
        # Add to task tracker
        self.task_tracker.add_task(task)
        
        # Submit to orchestrator if available
        if self.orchestrator:
            workflow_config = WorkflowConfig(
                type='essay_workflow',
                prompt=prompt,
                user_profile=profile.to_dict(),
                college_id=college_id,
                word_limit=essay_prompt.word_limit,
                priority='normal'
            )
            # This would be async in a real implementation
            # For now, we just track the configuration
            task.orchestrator_config = workflow_config
        
        return task_id
    
    def get_portfolio_status(self) -> PortfolioStatus:
        """Get comprehensive portfolio status."""
        status = self.task_tracker.get_portfolio_status()
        # Add story usage information
        status.story_usage = self.story_usage.copy()
        return status
    
    def get_next_tasks(self, limit: int = 3) -> List[EssayTask]:
        """Get next prioritized tasks for execution."""
        return self.task_tracker.get_next_tasks(limit)
    
    def get_task(self, task_id: str) -> Optional[EssayTask]:
        """Get task by ID."""
        return self.task_tracker.get_task(task_id)
    
    def update_task_progress(self, task_id: str, status: str, 
                           draft: Optional[EssayDraft] = None) -> None:
        """Update task progress and story usage."""
        task = self.task_tracker.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update task status
        self.task_tracker.update_task_status(task_id, status)
        
        # Update draft if provided
        if draft:
            task.draft = draft
            # Extract story usage from draft or used_stories
            if hasattr(draft, 'used_stories'):
                self._update_story_usage(task_id, draft.used_stories)
            elif task.used_stories:
                self._update_story_usage(task_id, task.used_stories)
        
        # If task completed, finalize story usage
        if status == "completed" and task.used_stories:
            self._finalize_story_usage(task_id, task.college_id, task.used_stories)
    
    def check_story_reuse(self, task_id: str, story_titles: List[str]) -> Dict[str, bool]:
        """Check if stories can be used without violating reuse rules."""
        task = self.task_tracker.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        result = {}
        for story_title in story_titles:
            story_id = self._get_story_id(story_title)
            story_usage = self.story_usage.get(story_id)
            
            if story_usage:
                # Check if story can be used for this college
                can_use = story_usage.can_use_for_college(task.college_id)
            else:
                # New story, can be used
                can_use = True
            
            result[story_title] = can_use
        
        return result
    
    def get_story_usage_report(self) -> Dict[str, Dict[str, any]]:
        """Get detailed story usage report."""
        report = {}
        for story_id, usage in self.story_usage.items():
            report[usage.story_title] = {
                "used_in_tasks": len(usage.used_in_tasks),
                "colleges": usage.college_ids,
                "can_reuse": len(usage.college_ids) == 0  # Can reuse if not used in any college yet
            }
        return report
    
    def _enforce_story_reuse_rules(self, task: EssayTask) -> None:
        """Enforce story reuse rules during task creation."""
        # Get user's defining moments/stories from profile
        if hasattr(task.profile, 'defining_moments'):
            for moment in task.profile.defining_moments:
                story_title = moment.title
                story_id = self._get_story_id(story_title)
                
                # Initialize story usage if new
                if story_id not in self.story_usage:
                    self.story_usage[story_id] = StoryUsage(
                        story_id=story_id,
                        story_title=story_title,
                        used_in_tasks=[],
                        college_ids=[]
                    )
    
    def _generate_task_id(self) -> str:
        """Generate unique task identifier."""
        timestamp = datetime.utcnow().isoformat()
        unique_string = f"{self.user_id}_{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def _get_story_id(self, story_title: str) -> str:
        """Generate consistent story ID from title."""
        return hashlib.md5(story_title.lower().encode()).hexdigest()[:8]
    
    def _update_story_usage(self, task_id: str, story_titles: List[str]) -> None:
        """Update story usage tracking."""
        task = self.task_tracker.get_task(task_id)
        if not task:
            return
        
        for story_title in story_titles:
            story_id = self._get_story_id(story_title)
            
            if story_id not in self.story_usage:
                self.story_usage[story_id] = StoryUsage(
                    story_id=story_id,
                    story_title=story_title,
                    used_in_tasks=[],
                    college_ids=[]
                )
            
            # Add task to usage tracking
            story_usage = self.story_usage[story_id]
            if task_id not in story_usage.used_in_tasks:
                story_usage.used_in_tasks.append(task_id)
        
        # Update task's used_stories
        task.used_stories = story_titles
        self._save_story_usage()
    
    def _finalize_story_usage(self, task_id: str, college_id: str, story_titles: List[str]) -> None:
        """Finalize story usage when task is completed."""
        for story_title in story_titles:
            story_id = self._get_story_id(story_title)
            
            if story_id in self.story_usage:
                story_usage = self.story_usage[story_id]
                if college_id not in story_usage.college_ids:
                    story_usage.college_ids.append(college_id)
        
        self._save_story_usage()
    
    def _load_story_usage(self) -> None:
        """Load story usage from persistent storage."""
        if not self.story_usage_file.exists():
            return
        
        try:
            with FileLock(self.story_lock_file):
                with open(self.story_usage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Deserialize story usage
                for story_id, usage_data in data.items():
                    try:
                        usage = StoryUsage.model_validate(usage_data)
                        self.story_usage[story_id] = usage
                    except Exception as e:
                        print(f"Warning: Failed to load story usage {story_id}: {e}")
        except Exception as e:
            print(f"Warning: Failed to load story usage from {self.story_usage_file}: {e}")
    
    def _save_story_usage(self) -> None:
        """Save story usage to persistent storage."""
        try:
            with FileLock(self.story_lock_file):
                # Serialize story usage
                data = {}
                for story_id, usage in self.story_usage.items():
                    data[story_id] = usage.model_dump()
                
                with open(self.story_usage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to save story usage to {self.story_usage_file}: {e}")


# Exception classes for portfolio management
class PortfolioError(Exception):
    """Base exception for portfolio management errors."""
    pass


class DuplicateTaskError(PortfolioError):
    """Raised when attempting to create a duplicate task."""
    pass


class InvalidDeadlineError(PortfolioError):
    """Raised when deadline is invalid (e.g., in the past)."""
    pass


class StoryReuseViolationError(PortfolioError):
    """Raised when story reuse rules are violated."""
    pass


class TaskNotFoundError(PortfolioError):
    """Raised when requested task is not found."""
    pass 