"""essay_agent.portfolio.task_tracker

Task-based essay workflow tracking with deadline management.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from filelock import FileLock

from .models import EssayTask, PortfolioStatus, StoryUsage
from essay_agent.memory.simple_memory import SimpleMemory


class TaskTracker:
    """Manages essay task scheduling and progress tracking."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tasks: Dict[str, EssayTask] = {}
        self.storage_dir = Path("memory_store")
        self.storage_dir.mkdir(exist_ok=True)
        self.tasks_file = self.storage_dir / f"{user_id}.portfolio.tasks.json"
        self.lock_file = self.storage_dir / f"{user_id}.portfolio.tasks.json.lock"
        self._load_tasks()
    
    def add_task(self, task: EssayTask) -> None:
        """Add new task and calculate priority score."""
        task.priority_score = self._calculate_priority_score(task)
        self.tasks[task.id] = task
        self._save_tasks()
    
    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status and timestamp."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        task.status = status  # type: ignore[assignment]
        task.updated_at = datetime.utcnow()
        
        # Recalculate priority score for active tasks
        if status in ["pending", "in_progress"]:
            task.priority_score = self._calculate_priority_score(task)
        
        self._save_tasks()
    
    def get_task(self, task_id: str) -> Optional[EssayTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def get_next_tasks(self, limit: int = 3) -> List[EssayTask]:
        """Get next tasks sorted by priority (deadline + complexity)."""
        active_tasks = [
            task for task in self.tasks.values()
            if task.status in ["pending", "in_progress"]
        ]
        
        # Sort by priority score (higher = more urgent)
        active_tasks.sort(key=lambda t: t.priority_score, reverse=True)
        
        return active_tasks[:limit]
    
    def get_tasks_by_status(self, status: str) -> List[EssayTask]:
        """Get all tasks with specific status."""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_portfolio_status(self) -> PortfolioStatus:
        """Generate comprehensive portfolio status report."""
        tasks_by_status = {}
        for status in ["pending", "in_progress", "completed", "failed"]:
            tasks_by_status[status] = len(self.get_tasks_by_status(status))
        
        # Find next deadline
        next_deadline = None
        active_tasks = [t for t in self.tasks.values() if t.status in ["pending", "in_progress"]]
        if active_tasks:
            next_deadline = min(task.deadline for task in active_tasks)
        
        # Calculate completion rate
        total_tasks = len(self.tasks)
        completed_tasks = tasks_by_status["completed"]
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # Estimate completion time based on average task duration
        estimated_completion = None
        if active_tasks:
            avg_days_per_task = 7.0  # Estimate based on typical essay writing time
            remaining_tasks = len(active_tasks)
            estimated_completion = datetime.utcnow() + timedelta(days=avg_days_per_task * remaining_tasks)
        
        return PortfolioStatus(
            user_id=self.user_id,
            total_essays=total_tasks,
            completed=completed_tasks,
            in_progress=tasks_by_status["in_progress"],
            pending=tasks_by_status["pending"],
            failed=tasks_by_status["failed"],
            next_deadline=next_deadline,
            story_usage={},  # Will be populated by PortfolioManager
            completion_rate=completion_rate,
            estimated_completion=estimated_completion
        )
    
    def _calculate_priority_score(self, task: EssayTask) -> float:
        """Calculate priority score based on deadline and complexity."""
        now = datetime.utcnow()
        
        # Deadline weight (60%) - higher score for closer deadlines
        days_until_deadline = (task.deadline - now).days
        if days_until_deadline <= 0:
            deadline_score = 100.0  # Overdue tasks get maximum priority
        elif days_until_deadline <= 3:
            deadline_score = 90.0
        elif days_until_deadline <= 7:
            deadline_score = 70.0
        elif days_until_deadline <= 14:
            deadline_score = 50.0
        else:
            deadline_score = max(10.0, 100.0 - (days_until_deadline * 2))
        
        # Complexity weight (25%) - higher score for more complex essays
        word_limit = task.prompt.word_limit
        if word_limit >= 650:
            complexity_score = 80.0
        elif word_limit >= 500:
            complexity_score = 60.0
        elif word_limit >= 300:
            complexity_score = 40.0
        else:
            complexity_score = 20.0
        
        # Dependency weight (10%) - lower score if many stories already used
        dependency_score = max(0.0, 100.0 - (len(task.used_stories) * 10))
        
        # User preference weight (5%) - could be enhanced with user preferences
        preference_score = 50.0
        
        # Calculate weighted score
        priority_score = (
            deadline_score * 0.6 +
            complexity_score * 0.25 +
            dependency_score * 0.10 +
            preference_score * 0.05
        )
        
        return priority_score
    
    def _load_tasks(self) -> None:
        """Load tasks from persistent storage."""
        if not self.tasks_file.exists():
            return
        
        try:
            with FileLock(self.lock_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Deserialize tasks
                for task_id, task_data in data.items():
                    try:
                        task = EssayTask.model_validate(task_data)
                        self.tasks[task_id] = task
                    except Exception as e:
                        print(f"Warning: Failed to load task {task_id}: {e}")
        except Exception as e:
            print(f"Warning: Failed to load tasks from {self.tasks_file}: {e}")
    
    def _save_tasks(self) -> None:
        """Save tasks to persistent storage."""
        try:
            with FileLock(self.lock_file):
                # Serialize tasks
                data = {}
                for task_id, task in self.tasks.items():
                    data[task_id] = task.model_dump()
                
                with open(self.tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to save tasks to {self.tasks_file}: {e}") 