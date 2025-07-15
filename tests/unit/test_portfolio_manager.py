"""Tests for the portfolio manager and related functionality."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import shutil

from essay_agent.portfolio.manager import PortfolioManager
from essay_agent.portfolio.models import EssayTask, StoryUsage, PortfolioStatus
from essay_agent.models import EssayPrompt, UserProfile, EssayDraft
from essay_agent.memory.user_profile_schema import (
    DefiningMoment, UserInfo, AcademicProfile, CoreValue, Activity
)


@pytest.fixture
def test_user_profile():
    """Create a test user profile with defining moments."""
    return UserProfile(
        user_info=UserInfo(
            name="Test User",
            grade=12,
            intended_major="Computer Science",
            college_list=["Harvard", "MIT", "Stanford"],
            platforms=["Common App", "UC Application"]
        ),
        academic_profile=AcademicProfile(
            gpa=3.8,
            test_scores={"SAT": 1500, "ACT": 34},
            courses=["AP Calculus", "AP Computer Science", "AP Physics"],
            activities=[
                Activity(
                    name="Math Team",
                    role="Captain",
                    duration="4 years",
                    description="Led school math team",
                    impact="Won state competition"
                )
            ]
        ),
        core_values=[
            CoreValue(
                value="Perseverance",
                description="Never giving up in face of challenges",
                evidence=["Math competition recovery", "Programming struggles"],
                used_in_essays=[]
            )
        ],
        defining_moments=[
            DefiningMoment(
                title="Math Competition Victory",
                description="Won state math competition",
                emotional_impact="High confidence boost",
                lessons_learned="Persistence pays off"
            ),
            DefiningMoment(
                title="Family Immigration Story",
                description="Moved to US at age 10",
                emotional_impact="Culture shock and adaptation",
                lessons_learned="Embracing change"
            )
        ]
    )


@pytest.fixture
def portfolio_manager():
    """Create a test portfolio manager."""
    user_id = "test_portfolio_user"
    # Clean up any existing test data
    storage_dir = Path("memory_store")
    test_files = [
        storage_dir / f"{user_id}.portfolio.tasks.json",
        storage_dir / f"{user_id}.portfolio.tasks.json.lock",
        storage_dir / f"{user_id}.portfolio.stories.json",
        storage_dir / f"{user_id}.portfolio.stories.json.lock"
    ]
    for file_path in test_files:
        if file_path.exists():
            file_path.unlink()
    
    return PortfolioManager(user_id)


def test_portfolio_manager_initialization(portfolio_manager):
    """Test portfolio manager initialization."""
    assert portfolio_manager.user_id == "test_portfolio_user"
    assert portfolio_manager.task_tracker is not None
    assert isinstance(portfolio_manager.story_usage, dict)
    assert len(portfolio_manager.story_usage) == 0


def test_submit_essay_task(portfolio_manager, test_user_profile):
    """Test submitting an essay task."""
    prompt = "Describe a challenge you overcame and how it shaped you."
    college_id = "harvard"
    deadline = datetime.utcnow() + timedelta(days=14)
    
    task_id = portfolio_manager.submit_essay_task(
        prompt=prompt,
        profile=test_user_profile,
        college_id=college_id,
        deadline=deadline
    )
    
    assert task_id is not None
    assert len(task_id) == 12  # MD5 hash truncated to 12 chars
    
    # Verify task was created
    task = portfolio_manager.get_task(task_id)
    assert task is not None
    assert task.prompt.text == prompt
    assert task.college_id == college_id
    assert task.status == "pending"
    assert task.priority_score > 0


def test_get_portfolio_status(portfolio_manager, test_user_profile):
    """Test getting portfolio status."""
    # Initially empty portfolio
    status = portfolio_manager.get_portfolio_status()
    assert status.total_essays == 0
    assert status.completed == 0
    assert status.completion_rate == 0.0
    
    # Add a task
    task_id = portfolio_manager.submit_essay_task(
        prompt="Test prompt",
        profile=test_user_profile,
        college_id="mit",
        deadline=datetime.utcnow() + timedelta(days=7)
    )
    
    # Check updated status
    status = portfolio_manager.get_portfolio_status()
    assert status.total_essays == 1
    assert status.pending == 1
    assert status.completion_rate == 0.0


def test_get_next_tasks(portfolio_manager, test_user_profile):
    """Test getting next prioritized tasks."""
    # Add multiple tasks with different deadlines
    task1_id = portfolio_manager.submit_essay_task(
        prompt="Task 1 - due in 3 days",
        profile=test_user_profile,
        college_id="harvard",
        deadline=datetime.utcnow() + timedelta(days=3)
    )
    
    task2_id = portfolio_manager.submit_essay_task(
        prompt="Task 2 - due in 14 days",
        profile=test_user_profile,
        college_id="mit",
        deadline=datetime.utcnow() + timedelta(days=14)
    )
    
    task3_id = portfolio_manager.submit_essay_task(
        prompt="Task 3 - due in 7 days",
        profile=test_user_profile,
        college_id="stanford",
        deadline=datetime.utcnow() + timedelta(days=7)
    )
    
    # Get next tasks (should be ordered by priority)
    next_tasks = portfolio_manager.get_next_tasks(limit=3)
    assert len(next_tasks) == 3
    
    # First task should have highest priority (closest deadline)
    assert next_tasks[0].id == task1_id
    assert next_tasks[0].priority_score > next_tasks[1].priority_score


def test_update_task_progress(portfolio_manager, test_user_profile):
    """Test updating task progress."""
    task_id = portfolio_manager.submit_essay_task(
        prompt="Test prompt",
        profile=test_user_profile,
        college_id="yale",
        deadline=datetime.utcnow() + timedelta(days=10)
    )
    
    # Update to in_progress
    portfolio_manager.update_task_progress(task_id, "in_progress")
    
    task = portfolio_manager.get_task(task_id)
    assert task.status == "in_progress"
    assert task.updated_at is not None
    
    # Update to completed
    portfolio_manager.update_task_progress(task_id, "completed")
    
    task = portfolio_manager.get_task(task_id)
    assert task.status == "completed"


def test_story_reuse_checking(portfolio_manager, test_user_profile):
    """Test story reuse checking functionality."""
    # Submit task for Harvard
    task1_id = portfolio_manager.submit_essay_task(
        prompt="Describe a challenge",
        profile=test_user_profile,
        college_id="harvard",
        deadline=datetime.utcnow() + timedelta(days=14)
    )
    
    # Check story reuse before using any stories
    can_use = portfolio_manager.check_story_reuse(task1_id, ["Math Competition Victory"])
    assert can_use["Math Competition Victory"] is True
    
    # Update task with used story
    portfolio_manager._update_story_usage(task1_id, ["Math Competition Victory"])
    
    # Complete the task to finalize story usage
    portfolio_manager.update_task_progress(task1_id, "completed")
    portfolio_manager._finalize_story_usage(task1_id, "harvard", ["Math Competition Victory"])
    
    # Submit task for same college (Harvard)
    task2_id = portfolio_manager.submit_essay_task(
        prompt="Another Harvard essay",
        profile=test_user_profile,
        college_id="harvard",
        deadline=datetime.utcnow() + timedelta(days=21)
    )
    
    # Should not be able to reuse the same story for the same college
    can_use = portfolio_manager.check_story_reuse(task2_id, ["Math Competition Victory"])
    assert can_use["Math Competition Victory"] is False
    
    # Submit task for different college (MIT)
    task3_id = portfolio_manager.submit_essay_task(
        prompt="MIT essay",
        profile=test_user_profile,
        college_id="mit",
        deadline=datetime.utcnow() + timedelta(days=28)
    )
    
    # Should be able to reuse story for different college
    can_use = portfolio_manager.check_story_reuse(task3_id, ["Math Competition Victory"])
    assert can_use["Math Competition Victory"] is True


def test_story_usage_report(portfolio_manager, test_user_profile):
    """Test story usage reporting."""
    # Submit task and use a story
    task_id = portfolio_manager.submit_essay_task(
        prompt="Test prompt",
        profile=test_user_profile,
        college_id="princeton",
        deadline=datetime.utcnow() + timedelta(days=14)
    )
    
    portfolio_manager._update_story_usage(task_id, ["Family Immigration Story"])
    portfolio_manager.update_task_progress(task_id, "completed")
    portfolio_manager._finalize_story_usage(task_id, "princeton", ["Family Immigration Story"])
    
    # Get usage report
    report = portfolio_manager.get_story_usage_report()
    assert "Family Immigration Story" in report
    assert report["Family Immigration Story"]["used_in_tasks"] == 1
    assert "princeton" in report["Family Immigration Story"]["colleges"]
    assert report["Family Immigration Story"]["can_reuse"] is False


def test_priority_score_calculation(portfolio_manager, test_user_profile):
    """Test priority score calculation based on deadlines."""
    # Task due in 1 day (should have very high priority)
    task1_id = portfolio_manager.submit_essay_task(
        prompt="Urgent task",
        profile=test_user_profile,
        college_id="urgent_college",
        deadline=datetime.utcnow() + timedelta(days=1)
    )
    
    # Task due in 30 days (should have lower priority)
    task2_id = portfolio_manager.submit_essay_task(
        prompt="Distant task",
        profile=test_user_profile,
        college_id="distant_college",
        deadline=datetime.utcnow() + timedelta(days=30)
    )
    
    task1 = portfolio_manager.get_task(task1_id)
    task2 = portfolio_manager.get_task(task2_id)
    
    # Urgent task should have higher priority score
    assert task1.priority_score > task2.priority_score


def test_task_not_found_error(portfolio_manager):
    """Test error handling for non-existent tasks."""
    with pytest.raises(ValueError, match="Task nonexistent not found"):
        portfolio_manager.update_task_progress("nonexistent", "completed")
    
    with pytest.raises(ValueError, match="Task nonexistent not found"):
        portfolio_manager.check_story_reuse("nonexistent", ["Some Story"])


# Clean up test files after all tests
def teardown_module(module):
    """Clean up test files."""
    storage_dir = Path("memory_store")
    test_files = storage_dir.glob("test_portfolio_user.*")
    for file_path in test_files:
        if file_path.exists():
            file_path.unlink() 