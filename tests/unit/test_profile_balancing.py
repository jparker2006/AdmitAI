"""
Test suite for Section 7.3 · Profile Balancing & Enhancement

Tests that story_weight field exists, profiles are balanced, and diversity is achieved.
"""

import pytest
from essay_agent.memory.user_profile_schema import DefiningMoment
from essay_agent.eval.sample_prompts import (
    create_test_profile,
    create_test_profile_arts,
    create_test_profile_community
)


class TestStoryWeightField:
    """Test that story_weight field exists and has correct default."""
    
    def test_story_weight_field_exists(self):
        """Test that story_weight field exists with correct default."""
        moment = DefiningMoment(
            title="Test Story",
            description="A test story",
            emotional_impact="Some impact",
            lessons_learned="Some lessons"
        )
        assert hasattr(moment, 'story_weight')
        assert moment.story_weight == 1.0
        
    def test_story_weight_can_be_set(self):
        """Test that story_weight can be set to custom values."""
        moment = DefiningMoment(
            title="Test Story",
            description="A test story",
            emotional_impact="Some impact",
            lessons_learned="Some lessons",
            story_weight=2.5
        )
        assert moment.story_weight == 2.5


class TestBalancedProfiles:
    """Test that all profiles have equal weights and proper categorization."""
    
    @pytest.mark.parametrize("profile_func,profile_name", [
        (create_test_profile, "Tech"),
        (create_test_profile_arts, "Arts"),
        (create_test_profile_community, "Community")
    ])
    def test_equal_story_weights(self, profile_func, profile_name):
        """Test that all stories have equal weight."""
        profile = profile_func()
        weights = [moment.story_weight for moment in profile.defining_moments]
        assert all(weight == 1.0 for weight in weights), f"{profile_name} profile has unequal weights: {weights}"
    
    @pytest.mark.parametrize("profile_func,profile_name", [
        (create_test_profile, "Tech"),
        (create_test_profile_arts, "Arts"),
        (create_test_profile_community, "Community")
    ])
    def test_story_categorization(self, profile_func, profile_name):
        """Test that stories are properly categorized."""
        profile = profile_func()
        valid_categories = {'identity', 'passion', 'challenge', 'achievement', 'community', 'general'}
        
        for moment in profile.defining_moments:
            assert moment.story_category in valid_categories, f"{profile_name} has invalid category: {moment.story_category}"
    
    def test_profile_diversity(self):
        """Test that profiles have different dominant themes."""
        tech_profile = create_test_profile()
        arts_profile = create_test_profile_arts()
        community_profile = create_test_profile_community()
        
        # Different intended majors
        assert tech_profile.user_info.intended_major == "Computer Science"
        assert arts_profile.user_info.intended_major == "Theatre Arts"
        assert community_profile.user_info.intended_major == "Public Policy"
        
        # Different names
        assert tech_profile.user_info.name == "Alex Johnson"
        assert arts_profile.user_info.name == "Maya Chen"
        assert community_profile.user_info.name == "Jordan Williams"
    
    def test_no_robotics_dominance(self):
        """Test that robotics doesn't dominate any profile."""
        profiles = [
            ("Tech", create_test_profile()),
            ("Arts", create_test_profile_arts()),
            ("Community", create_test_profile_community())
        ]
        
        for profile_name, profile in profiles:
            robotics_count = sum(1 for moment in profile.defining_moments 
                               if 'robotics' in moment.title.lower() or 'robotics' in moment.description.lower())
            assert robotics_count <= 1, f"{profile_name} profile has {robotics_count} robotics stories (should be ≤1)"


class TestProfileBalance:
    """Test that no single story dominates any profile."""
    
    def test_max_stories_per_category(self):
        """Test that no more than 2 stories per category."""
        profiles = [
            ("Tech", create_test_profile()),
            ("Arts", create_test_profile_arts()),
            ("Community", create_test_profile_community())
        ]
        
        for profile_name, profile in profiles:
            categories = [moment.story_category for moment in profile.defining_moments]
            category_counts = {cat: categories.count(cat) for cat in set(categories)}
            
            for category, count in category_counts.items():
                assert count <= 2, f"{profile_name} has {count} stories in {category} category (should be ≤2)"
    
    def test_all_categories_represented(self):
        """Test that key categories are represented across all profiles."""
        profiles = [
            create_test_profile(),
            create_test_profile_arts(),
            create_test_profile_community()
        ]
        
        all_categories = set()
        for profile in profiles:
            profile_categories = {moment.story_category for moment in profile.defining_moments}
            all_categories.update(profile_categories)
        
        # Should have at least these key categories across all profiles
        required_categories = {'identity', 'passion', 'challenge', 'achievement'}
        assert required_categories.issubset(all_categories), f"Missing categories: {required_categories - all_categories}"


class TestEvaluationIntegration:
    """Test that all profiles can be used in evaluation system."""
    
    def test_profile_creation_success(self):
        """Test that all three profiles can be created without errors."""
        profiles = [
            create_test_profile(),
            create_test_profile_arts(),
            create_test_profile_community()
        ]
        
        for profile in profiles:
            assert len(profile.defining_moments) > 0
            assert profile.user_info.name
            assert profile.user_info.intended_major
            assert len(profile.core_values) > 0
    
    def test_backwards_compatibility(self):
        """Test that existing code continues to work."""
        # Test that original create_test_profile still works
        profile = create_test_profile()
        assert profile.user_info.name == "Alex Johnson"
        assert len(profile.defining_moments) == 5
        
        # Test that all moments have the new field
        for moment in profile.defining_moments:
            assert hasattr(moment, 'story_weight')
            assert moment.story_weight == 1.0 