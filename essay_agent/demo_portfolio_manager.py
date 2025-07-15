#!/usr/bin/env python3
"""
Demo script showing the Portfolio Manager functionality.

This script demonstrates:
- Creating a portfolio manager for a user
- Submitting multiple essay tasks with different deadlines
- Checking story reuse enforcement
- Getting portfolio status and progress reports
- Task prioritization and scheduling
"""

import asyncio
from datetime import datetime, timedelta
from pprint import pprint

from essay_agent.portfolio.manager import PortfolioManager
from essay_agent.models import UserProfile
from essay_agent.memory.user_profile_schema import (
    UserInfo, AcademicProfile, CoreValue, DefiningMoment, Activity
)


def create_demo_user_profile() -> UserProfile:
    """Create a demo user profile for testing."""
    return UserProfile(
        user_info=UserInfo(
            name="Alex Johnson",
            grade=12,
            intended_major="Computer Science",
            college_list=["Harvard", "MIT", "Stanford", "Carnegie Mellon", "UC Berkeley"],
            platforms=["Common App", "UC Application"]
        ),
        academic_profile=AcademicProfile(
            gpa=3.95,
            test_scores={"SAT": 1580, "ACT": 35},
            courses=["AP Calculus BC", "AP Computer Science A", "AP Physics C", "AP English Literature"],
            activities=[
                Activity(
                    name="Programming Competition Team",
                    role="Captain",
                    duration="3 years",
                    description="Led team in USACO and local programming contests",
                    impact="Qualified for state championships, mentored 10+ students"
                ),
                Activity(
                    name="Math Tutoring Program",
                    role="Volunteer Tutor",
                    duration="2 years",
                    description="Weekly tutoring for underserved students",
                    impact="Helped 15 students improve grades by average of 1.5 letter grades"
                )
            ]
        ),
        core_values=[
            CoreValue(
                value="Intellectual Curiosity",
                description="Driven by desire to understand and solve complex problems",
                evidence=["Independent research projects", "Extra coursework", "Competition participation"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Community Service",
                description="Commitment to helping others and giving back",
                evidence=["Tutoring program", "Food bank volunteering", "Peer mentoring"],
                used_in_essays=[]
            )
        ],
        defining_moments=[
            DefiningMoment(
                title="First Programming Competition",
                description="Struggled with algorithmic thinking but persevered through practice",
                emotional_impact="Initial frustration turned into determination and eventual success",
                lessons_learned="Persistence and methodical practice can overcome initial struggles"
            ),
            DefiningMoment(
                title="Tutoring a Struggling Student",
                description="Helped Maria overcome math anxiety and improve her grades",
                emotional_impact="Profound satisfaction from seeing someone else succeed",
                lessons_learned="Teaching others deepens your own understanding"
            ),
            DefiningMoment(
                title="Family Financial Hardship",
                description="Dad lost job during pandemic, family had to make sacrifices",
                emotional_impact="Stress and worry, but also brought family closer",
                lessons_learned="Resilience and the importance of supporting each other"
            )
        ]
    )


def demo_portfolio_manager():
    """Demonstrate the portfolio manager functionality."""
    print("🎓 Essay Agent Portfolio Manager Demo")
    print("=" * 50)
    
    # Create portfolio manager
    user_id = "demo_user"
    portfolio = PortfolioManager(user_id)
    profile = create_demo_user_profile()
    
    print(f"✅ Created portfolio manager for user: {user_id}")
    print()
    
    # Submit multiple essay tasks
    print("📝 Submitting Essay Tasks")
    print("-" * 30)
    
    tasks = [
        {
            "prompt": "Describe a challenge you've overcome and how it shaped you as a person.",
            "college_id": "harvard",
            "deadline": datetime.now() + timedelta(days=7),
            "description": "Harvard supplemental essay (urgent - due in 1 week)"
        },
        {
            "prompt": "Tell us about a time you were intellectually curious about something.",
            "college_id": "mit",
            "deadline": datetime.now() + timedelta(days=14),
            "description": "MIT supplemental essay (due in 2 weeks)"
        },
        {
            "prompt": "Describe a meaningful experience you've had helping others.",
            "college_id": "stanford",
            "deadline": datetime.now() + timedelta(days=21),
            "description": "Stanford supplemental essay (due in 3 weeks)"
        },
        {
            "prompt": "Share a story about overcoming a personal challenge.",
            "college_id": "harvard",
            "deadline": datetime.now() + timedelta(days=28),
            "description": "Harvard Common App essay (due in 4 weeks)"
        },
        {
            "prompt": "Describe your intellectual interests and how you pursue them.",
            "college_id": "carnegie_mellon",
            "deadline": datetime.now() + timedelta(days=35),
            "description": "Carnegie Mellon supplemental essay (due in 5 weeks)"
        }
    ]
    
    task_ids = []
    for task in tasks:
        task_id = portfolio.submit_essay_task(
            prompt=task["prompt"],
            profile=profile,
            college_id=task["college_id"],
            deadline=task["deadline"]
        )
        task_ids.append(task_id)
        print(f"✅ Submitted: {task['description']}")
        print(f"   Task ID: {task_id}")
        print(f"   College: {task['college_id']}")
        print(f"   Deadline: {task['deadline'].strftime('%Y-%m-%d %H:%M')}")
        print()
    
    # Show portfolio status
    print("📊 Portfolio Status")
    print("-" * 20)
    status = portfolio.get_portfolio_status()
    print(f"Total Essays: {status.total_essays}")
    print(f"Completed: {status.completed}")
    print(f"In Progress: {status.in_progress}")
    print(f"Pending: {status.pending}")
    print(f"Completion Rate: {status.completion_rate:.1%}")
    if status.next_deadline:
        print(f"Next Deadline: {status.next_deadline.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Show task prioritization
    print("🎯 Task Prioritization")
    print("-" * 22)
    next_tasks = portfolio.get_next_tasks(limit=3)
    for i, task in enumerate(next_tasks, 1):
        print(f"{i}. {task.college_id.upper()} Essay")
        print(f"   Priority Score: {task.priority_score:.1f}")
        print(f"   Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Status: {task.status}")
        print(f"   Prompt: {task.prompt.text[:80]}...")
        print()
    
    # Demonstrate story reuse checking
    print("🔄 Story Reuse Checking")
    print("-" * 24)
    
    # Check story usage for Harvard task
    harvard_task_id = task_ids[0]  # First task was Harvard
    story_check = portfolio.check_story_reuse(
        harvard_task_id, 
        ["First Programming Competition", "Family Financial Hardship"]
    )
    
    print(f"For Harvard task ({harvard_task_id}):")
    for story, can_use in story_check.items():
        status_icon = "✅" if can_use else "❌"
        print(f"  {status_icon} {story}: {'Can use' if can_use else 'Cannot use'}")
    print()
    
    # Simulate completing the Harvard task with a story
    print("📝 Simulating Task Progress")
    print("-" * 27)
    
    # Update Harvard task to in progress
    portfolio.update_task_progress(harvard_task_id, "in_progress")
    print(f"✅ Updated Harvard task to 'in_progress'")
    
    # Mark story as used
    portfolio._update_story_usage(harvard_task_id, ["First Programming Competition"])
    print(f"✅ Used story: 'First Programming Competition'")
    
    # Complete the task
    portfolio.update_task_progress(harvard_task_id, "completed")
    portfolio._finalize_story_usage(harvard_task_id, "harvard", ["First Programming Competition"])
    print(f"✅ Completed Harvard task")
    print()
    
    # Check story reuse for another Harvard task
    harvard_task_2_id = task_ids[3]  # Fourth task was also Harvard
    story_check_2 = portfolio.check_story_reuse(
        harvard_task_2_id,
        ["First Programming Competition", "Tutoring a Struggling Student"]
    )
    
    print(f"For second Harvard task ({harvard_task_2_id}):")
    for story, can_use in story_check_2.items():
        status_icon = "✅" if can_use else "❌"
        status_text = "Can use" if can_use else "Cannot use (already used for Harvard)"
        print(f"  {status_icon} {story}: {status_text}")
    print()
    
    # Check story reuse for MIT task (different college)
    mit_task_id = task_ids[1]  # Second task was MIT
    story_check_3 = portfolio.check_story_reuse(
        mit_task_id,
        ["First Programming Competition", "Tutoring a Struggling Student"]
    )
    
    print(f"For MIT task ({mit_task_id}):")
    for story, can_use in story_check_3.items():
        status_icon = "✅" if can_use else "❌"
        status_text = "Can use" if can_use else "Cannot use"
        if story == "First Programming Competition" and can_use:
            status_text += " (different college - reuse allowed)"
        print(f"  {status_icon} {story}: {status_text}")
    print()
    
    # Show updated portfolio status
    print("📊 Updated Portfolio Status")
    print("-" * 28)
    updated_status = portfolio.get_portfolio_status()
    print(f"Total Essays: {updated_status.total_essays}")
    print(f"Completed: {updated_status.completed}")
    print(f"In Progress: {updated_status.in_progress}")
    print(f"Pending: {updated_status.pending}")
    print(f"Completion Rate: {updated_status.completion_rate:.1%}")
    print()
    
    # Show story usage report
    print("📚 Story Usage Report")
    print("-" * 21)
    story_report = portfolio.get_story_usage_report()
    for story_title, usage_info in story_report.items():
        print(f"📖 {story_title}")
        print(f"   Used in {usage_info['used_in_tasks']} task(s)")
        print(f"   Colleges: {', '.join(usage_info['colleges'])}")
        print(f"   Can reuse: {'Yes' if usage_info['can_reuse'] else 'No'}")
        print()
    
    print("🎉 Demo Complete!")
    print("The Portfolio Manager successfully:")
    print("  ✅ Managed multiple essay tasks")
    print("  ✅ Prioritized tasks by deadline")
    print("  ✅ Enforced story reuse rules")
    print("  ✅ Tracked progress and completion")
    print("  ✅ Generated comprehensive reports")


if __name__ == "__main__":
    demo_portfolio_manager() 