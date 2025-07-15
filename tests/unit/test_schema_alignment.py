"""
Unit tests for schema alignment between user profile and brainstorm tool.

Tests ensure that story categories are consistent across all components
and that migration from old to new schema works correctly.
"""

import pytest
from essay_agent.memory.user_profile_schema import (
    DefiningMoment, 
    UserProfile, 
    UserInfo, 
    AcademicProfile, 
    migrate_story_categories
)
from essay_agent.tools.brainstorm import BrainstormTool


class TestStoryCategories:
    """Test story category consistency between user profile and brainstorm tool."""
    
    def test_story_category_migration_old_to_new(self):
        """Test old categories are properly mapped to new ones."""
        # Test individual mappings
        test_cases = [
            ("identity", "heritage"),
            ("passion", "creative"),
            ("challenge", "obstacle"),
            ("achievement", "accomplishment"),
            ("community", "service"),
            ("general", "defining_moment")
        ]
        
        for old_category, expected_new_category in test_cases:
            moment = DefiningMoment(
                title="Test Story",
                description="Test description",
                emotional_impact="Test impact",
                lessons_learned="Test lessons",
                story_category=old_category
            )
            
            assert moment.story_category == expected_new_category, \
                f"Category '{old_category}' should map to '{expected_new_category}', got '{moment.story_category}'"
    
    def test_story_category_new_categories_preserved(self):
        """Test that new categories are preserved as-is."""
        new_categories = [
            'heritage', 'family', 'cultural', 'personal_defining',
            'creative', 'academic', 'intellectual', 'hobby',
            'obstacle', 'failure', 'conflict', 'problem_solving',
            'accomplishment', 'leadership', 'growth', 'skill',
            'service', 'cultural_involvement', 'social_impact', 'tradition',
            'defining_moment', 'values', 'experiences'
        ]
        
        for category in new_categories:
            moment = DefiningMoment(
                title="Test Story",
                description="Test description",
                emotional_impact="Test impact",
                lessons_learned="Test lessons",
                story_category=category
            )
            
            assert moment.story_category == category, \
                f"New category '{category}' should be preserved, got '{moment.story_category}'"
    
    def test_unknown_category_preserved(self):
        """Test that unknown categories are preserved as-is."""
        unknown_category = "unknown_category"
        moment = DefiningMoment(
            title="Test Story",
            description="Test description",
            emotional_impact="Test impact",
            lessons_learned="Test lessons",
            story_category=unknown_category
        )
        
        assert moment.story_category == unknown_category, \
            f"Unknown category '{unknown_category}' should be preserved"
    
    def test_category_consistency_with_brainstorm_tool(self):
        """Test brainstorm tool categories match user profile expectations."""
        brainstorm_tool = BrainstormTool()
        
        # Test that recommended categories exist in valid categories
        prompt_types = ['identity', 'passion', 'challenge', 'achievement', 'community', 'general']
        
        for prompt_type in prompt_types:
            recommended_categories = brainstorm_tool._get_recommended_story_categories(prompt_type)
            
            # All recommended categories should be valid
            for category in recommended_categories:
                # Create a moment with this category - should not raise validation error
                moment = DefiningMoment(
                    title="Test Story",
                    description="Test description",
                    emotional_impact="Test impact",
                    lessons_learned="Test lessons",
                    story_category=category
                )
                
                # If the category is valid, it should be one of the accepted values
                assert moment.story_category in [
                    'heritage', 'family', 'cultural', 'personal_defining',
                    'creative', 'academic', 'intellectual', 'hobby',
                    'obstacle', 'failure', 'conflict', 'problem_solving',
                    'accomplishment', 'leadership', 'growth', 'skill',
                    'service', 'cultural_involvement', 'social_impact', 'tradition',
                    'defining_moment', 'values', 'experiences'
                ], f"Category '{category}' from brainstorm tool not in valid categories"


class TestProfileMigration:
    """Test profile migration functionality."""
    
    def test_migrate_story_categories_success(self):
        """Test successful migration of story categories."""
        # Create profile with old categories
        profile = UserProfile(
            user_info=UserInfo(
                name="Test User",
                grade=12,
                intended_major="Computer Science",
                college_list=["Stanford"],
                platforms=["Common App"]
            ),
            academic_profile=AcademicProfile(
                gpa=3.8,
                test_scores={"SAT": 1450},
                courses=["AP Computer Science"],
                activities=[]
            ),
            core_values=[],
            defining_moments=[
                DefiningMoment(
                    title="Identity Story",
                    description="Test description",
                    emotional_impact="Test impact",
                    lessons_learned="Test lessons",
                    story_category="identity"  # Old category
                ),
                DefiningMoment(
                    title="Passion Story",
                    description="Test description",
                    emotional_impact="Test impact",
                    lessons_learned="Test lessons",
                    story_category="passion"  # Old category
                )
            ]
        )
        
        # Migrate the profile
        migrated_profile = migrate_story_categories(profile)
        
        # Check that categories were migrated
        assert migrated_profile.defining_moments[0].story_category == "heritage"
        assert migrated_profile.defining_moments[1].story_category == "creative"
    
    def test_migrate_story_categories_already_new(self):
        """Test migration with profiles that already have new categories."""
        profile = UserProfile(
            user_info=UserInfo(
                name="Test User",
                grade=12,
                intended_major="Computer Science",
                college_list=["Stanford"],
                platforms=["Common App"]
            ),
            academic_profile=AcademicProfile(
                gpa=3.8,
                test_scores={"SAT": 1450},
                courses=["AP Computer Science"],
                activities=[]
            ),
            core_values=[],
            defining_moments=[
                DefiningMoment(
                    title="Heritage Story",
                    description="Test description",
                    emotional_impact="Test impact",
                    lessons_learned="Test lessons",
                    story_category="heritage"  # Already new category
                )
            ]
        )
        
        # Migrate the profile
        migrated_profile = migrate_story_categories(profile)
        
        # Check that category was preserved
        assert migrated_profile.defining_moments[0].story_category == "heritage"
    
    def test_migrate_story_categories_error_handling(self):
        """Test migration error handling."""
        # This test would need to be implemented if we can create a scenario
        # where migration fails. For now, we'll just ensure it doesn't crash.
        
        profile = UserProfile(
            user_info=UserInfo(
                name="Test User",
                grade=12,
                intended_major="Computer Science",
                college_list=["Stanford"],
                platforms=["Common App"]
            ),
            academic_profile=AcademicProfile(
                gpa=3.8,
                test_scores={"SAT": 1450},
                courses=["AP Computer Science"],
                activities=[]
            ),
            core_values=[],
            defining_moments=[]
        )
        
        # Migration should not fail even with empty profile
        migrated_profile = migrate_story_categories(profile)
        assert migrated_profile is not None
        assert len(migrated_profile.defining_moments) == 0


class TestDefiningMomentValidation:
    """Test DefiningMoment field validation."""
    
    def test_default_story_category(self):
        """Test that default story category is correct."""
        moment = DefiningMoment(
            title="Test Story",
            description="Test description",
            emotional_impact="Test impact",
            lessons_learned="Test lessons"
        )
        
        assert moment.story_category == "defining_moment"
    
    def test_story_category_validation_runs(self):
        """Test that story category validation is actually called."""
        # Create a moment with an old category
        moment = DefiningMoment(
            title="Test Story",
            description="Test description",
            emotional_impact="Test impact",
            lessons_learned="Test lessons",
            story_category="identity"  # Old category
        )
        
        # Should be automatically converted to new category
        assert moment.story_category == "heritage" 