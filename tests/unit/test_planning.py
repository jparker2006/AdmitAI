"""Unit tests for the conversational planning system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from essay_agent.planning import (
    ConversationalPlanner, 
    PlanningContext, 
    PlanningConstraints, 
    PlanQuality
)
from essay_agent.planner import EssayPlan, Phase
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, DefiningMoment


class TestPlanningConstraints:
    """Test suite for PlanningConstraints dataclass."""

    def test_constraints_initialization(self):
        """Test constraints can be initialized with default values."""
        constraints = PlanningConstraints()
        
        assert constraints.deadlines == {}
        assert constraints.word_count_targets == {}
        assert constraints.college_preferences == []
        assert constraints.available_stories == []
        assert constraints.used_stories == {}
        assert constraints.current_workload == 0
        assert constraints.time_available is None

    def test_constraints_to_dict(self):
        """Test constraints can be converted to dictionary."""
        deadline = datetime(2024, 1, 15, 23, 59)
        constraints = PlanningConstraints(
            deadlines={"common_app": deadline},
            word_count_targets={"common_app": 650},
            college_preferences=["Stanford", "MIT"],
            available_stories=["leadership", "research"],
            used_stories={"uc_essays": ["leadership"]},
            current_workload=3,
            time_available=120
        )
        
        result = constraints.to_dict()
        
        assert result["deadlines"]["common_app"] == deadline.isoformat()
        assert result["word_count_targets"]["common_app"] == 650
        assert result["college_preferences"] == ["Stanford", "MIT"]
        assert result["available_stories"] == ["leadership", "research"]
        assert result["used_stories"]["uc_essays"] == ["leadership"]
        assert result["current_workload"] == 3
        assert result["time_available"] == 120


class TestPlanQuality:
    """Test suite for PlanQuality dataclass."""

    def test_plan_quality_initialization(self):
        """Test plan quality can be initialized."""
        quality = PlanQuality(
            feasibility_score=8.5,
            efficiency_score=7.2,
            constraint_satisfaction=9.0,
            story_diversity_score=6.8,
            overall_score=7.9,
            improvement_suggestions=["Improve efficiency"]
        )
        
        assert quality.feasibility_score == 8.5
        assert quality.efficiency_score == 7.2
        assert quality.constraint_satisfaction == 9.0
        assert quality.story_diversity_score == 6.8
        assert quality.overall_score == 7.9
        assert quality.improvement_suggestions == ["Improve efficiency"]

    def test_plan_quality_is_acceptable(self):
        """Test plan quality acceptance threshold."""
        high_quality = PlanQuality(
            feasibility_score=8.0,
            efficiency_score=8.0,
            constraint_satisfaction=8.0,
            story_diversity_score=8.0,
            overall_score=8.0
        )
        
        low_quality = PlanQuality(
            feasibility_score=6.0,
            efficiency_score=6.0,
            constraint_satisfaction=6.0,
            story_diversity_score=6.0,
            overall_score=6.0
        )
        
        assert high_quality.is_acceptable() is True
        assert low_quality.is_acceptable() is False
        assert low_quality.is_acceptable(threshold=5.0) is True


class TestConversationalPlanner:
    """Test suite for ConversationalPlanner class."""

    def create_test_profile(self):
        """Create a test user profile."""
        user_info = UserInfo(
            name="Test User",
            grade=12,
            intended_major="Computer Science",
            college_list=["Stanford", "MIT", "CalTech"],
            platforms=["Common App", "UC Application"]
        )
        
        defining_moments = [
            DefiningMoment(
                title="Leadership Experience",
                description="Led school robotics team",
                emotional_impact="Gained confidence",
                lessons_learned="Teamwork is crucial",
                used_in_essays=["mit_essay_1"],
                themes=["leadership", "technology"]
            ),
            DefiningMoment(
                title="Research Project",
                description="Conducted AI research",
                emotional_impact="Discovered passion",
                lessons_learned="Research requires patience",
                used_in_essays=[],
                themes=["research", "technology"]
            )
        ]
        
        profile = Mock(spec=UserProfile)
        profile.user_info = user_info
        profile.defining_moments = defining_moments
        profile.model_dump = Mock(return_value={"user_info": user_info.__dict__})
        
        return profile

    def test_conversational_planner_initialization(self):
        """Test conversational planner can be initialized."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        assert planner.user_id == "test_user"
        assert planner.profile == profile
        assert planner.planning_history == []
        assert planner.smart_planner is not None
        assert planner.query_rewriter is not None

    @patch('essay_agent.planning.debug_print')
    def test_create_conversational_plan_basic(self, mock_debug):
        """Test basic conversational plan creation."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Mock the smart planner
        mock_plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={"next_tool": "brainstorm", "args": {"prompt": "test"}},
            metadata={}
        )
        
        with patch.object(planner.smart_planner, 'decide_next_action', return_value=mock_plan):
            with patch.object(planner.query_rewriter, 'rewrite_query', return_value="processed request"):
                plan = planner.create_conversational_plan(
                    "Help me brainstorm ideas", 
                    PlanningContext.CONVERSATION
                )
        
        assert plan.phase == Phase.BRAINSTORMING
        assert plan.data["next_tool"] == "brainstorm"
        assert "planning_context" in plan.metadata
        assert plan.metadata["planning_context"] == "conversation"
        assert "quality_metrics" in plan.metadata
        assert len(planner.planning_history) == 1

    @patch('essay_agent.planning.debug_print')
    def test_create_conversational_plan_with_constraints(self, mock_debug):
        """Test conversational plan creation with constraints."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Mock the smart planner
        mock_plan = EssayPlan(
            phase=Phase.DRAFTING,
            data={"next_tool": "draft", "args": {"word_count": 650}},
            metadata={}
        )
        
        additional_context = {
            "deadline": datetime.now() + timedelta(days=3),
            "word_count_target": 650
        }
        
        with patch.object(planner.smart_planner, 'decide_next_action', return_value=mock_plan):
            with patch.object(planner.query_rewriter, 'rewrite_query', return_value="processed request"):
                plan = planner.create_conversational_plan(
                    "Write my essay draft", 
                    PlanningContext.CONSTRAINT_DRIVEN,
                    additional_context
                )
        
        assert plan.phase == Phase.DRAFTING
        assert plan.data["next_tool"] == "draft"
        assert "constraints_applied" in plan.metadata
        assert plan.metadata["planning_context"] == "constraint_driven"

    @patch('essay_agent.planning.debug_print')
    def test_create_conversational_plan_error_handling(self, mock_debug):
        """Test error handling in conversational plan creation."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Mock the smart planner to raise an exception
        with patch.object(planner.smart_planner, 'decide_next_action', side_effect=Exception("Test error")):
            plan = planner.create_conversational_plan(
                "Help me brainstorm", 
                PlanningContext.CONVERSATION
            )
        
        assert plan.phase == Phase.BRAINSTORMING
        assert len(plan.errors) == 1
        assert "Planning error" in plan.errors[0]
        assert plan.metadata["fallback_plan"] is True

    def test_evaluate_plan_quality_basic(self):
        """Test basic plan quality evaluation."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={"next_tool": "brainstorm", "args": {"prompt": "test"}},
            metadata={}
        )
        
        quality = planner.evaluate_plan_quality(plan)
        
        assert isinstance(quality, PlanQuality)
        assert 0.0 <= quality.feasibility_score <= 10.0
        assert 0.0 <= quality.efficiency_score <= 10.0
        assert 0.0 <= quality.constraint_satisfaction <= 10.0
        assert 0.0 <= quality.story_diversity_score <= 10.0
        assert 0.0 <= quality.overall_score <= 10.0
        assert isinstance(quality.improvement_suggestions, list)

    def test_evaluate_plan_quality_with_constraints(self):
        """Test plan quality evaluation with specific constraints."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={"next_tool": "brainstorm", "args": {"prompt": "test"}},
            metadata={}
        )
        
        # Create constraints with tight deadline
        constraints = PlanningConstraints(
            deadlines={"common_app": datetime.now() + timedelta(days=1)},
            current_workload=5,
            available_stories=[]
        )
        
        quality = planner.evaluate_plan_quality(plan, constraints)
        
        # Should have lower feasibility score due to tight deadline and high workload
        assert quality.feasibility_score < 8.0
        assert len(quality.improvement_suggestions) > 0

    @patch('essay_agent.planning.debug_print')
    def test_replan_on_constraint_change(self, mock_debug):
        """Test re-planning when constraints change."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Create initial plan
        current_plan = EssayPlan(
            phase=Phase.DRAFTING,
            data={"next_tool": "draft", "args": {"word_count": 650}},
            metadata={}
        )
        
        # Create new constraints with changed deadline
        new_constraints = PlanningConstraints(
            deadlines={"common_app": datetime.now() + timedelta(days=1)},
            word_count_targets={"common_app": 500}  # Reduced word count
        )
        
        # Mock the conversational plan creation
        mock_new_plan = EssayPlan(
            phase=Phase.DRAFTING,
            data={"next_tool": "draft", "args": {"word_count": 500}},
            metadata={}
        )
        
        with patch.object(planner, 'create_conversational_plan', return_value=mock_new_plan):
            revised_plan = planner.replan_on_constraint_change(current_plan, new_constraints)
        
        assert revised_plan.metadata["replanned"] is True
        assert revised_plan.metadata["previous_plan_phase"] == "DRAFTING"
        assert "constraint_changes" in revised_plan.metadata

    def test_get_next_steps_suggestion_brainstorming(self):
        """Test next steps suggestions for brainstorming phase."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        current_state = {
            "phase": Phase.BRAINSTORMING,
            "tool_outputs": {},
            "errors": []
        }
        
        suggestions = planner.get_next_steps_suggestion(current_state)
        
        assert len(suggestions) > 0
        assert any("brainstorm" in suggestion.lower() for suggestion in suggestions)

    def test_get_next_steps_suggestion_with_output(self):
        """Test next steps suggestions when brainstorm output exists."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        current_state = {
            "phase": Phase.BRAINSTORMING,
            "tool_outputs": {"brainstorm": "some stories"},
            "errors": []
        }
        
        suggestions = planner.get_next_steps_suggestion(current_state)
        
        assert len(suggestions) > 0
        assert any("outline" in suggestion.lower() for suggestion in suggestions)

    def test_get_next_steps_suggestion_with_errors(self):
        """Test next steps suggestions when there are errors."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        current_state = {
            "phase": Phase.DRAFTING,
            "tool_outputs": {"brainstorm": "stories", "outline": "outline"},
            "errors": ["Some error occurred"]
        }
        
        suggestions = planner.get_next_steps_suggestion(current_state)
        
        assert len(suggestions) > 0
        assert any("error" in suggestion.lower() for suggestion in suggestions)

    def test_get_next_steps_suggestion_urgent_deadline(self):
        """Test next steps suggestions with urgent deadlines."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Mock the constraint extraction to return urgent deadlines
        with patch.object(planner, '_extract_constraints_from_profile') as mock_extract:
            mock_constraints = PlanningConstraints(
                deadlines={"stanford": datetime.now() + timedelta(days=2)}
            )
            mock_extract.return_value = mock_constraints
            
            current_state = {
                "phase": Phase.DRAFTING,
                "tool_outputs": {},
                "errors": []
            }
            
            suggestions = planner.get_next_steps_suggestion(current_state)
            
            assert len(suggestions) > 0
            assert any("urgent" in suggestion.lower() for suggestion in suggestions)

    @patch('essay_agent.planning.debug_print')
    def test_handle_deadline_pressure(self, mock_debug):
        """Test handling of deadline pressure."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Create constraints with urgent deadline
        constraints = PlanningConstraints(
            deadlines={"stanford": datetime.now() + timedelta(days=1)}
        )
        
        # Mock the create_conversational_plan method
        mock_plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={"next_tool": "brainstorm", "args": {"urgent": True}},
            metadata={}
        )
        
        with patch.object(planner, 'create_conversational_plan', return_value=mock_plan):
            plan = planner.handle_deadline_pressure(constraints)
        
        assert plan.metadata["time_pressure_mode"] is True
        assert plan.metadata["target_college"] == "stanford"
        assert "urgent_deadline" in plan.metadata

    def test_handle_deadline_pressure_no_urgent(self):
        """Test deadline pressure handling when no urgent deadlines."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Create constraints with no urgent deadlines
        constraints = PlanningConstraints(
            deadlines={"stanford": datetime.now() + timedelta(days=10)}
        )
        
        # Mock the create_conversational_plan method
        mock_plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={"next_tool": "brainstorm", "args": {}},
            metadata={}
        )
        
        with patch.object(planner, 'create_conversational_plan', return_value=mock_plan):
            plan = planner.handle_deadline_pressure(constraints)
        
        # Should not have time pressure metadata
        assert "time_pressure_mode" not in plan.metadata

    def test_extract_constraints_from_profile(self):
        """Test extraction of constraints from user profile."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        constraints = planner._extract_constraints_from_profile()
        
        assert "Stanford" in constraints.college_preferences
        assert "MIT" in constraints.college_preferences
        assert "CalTech" in constraints.college_preferences
        assert "Leadership Experience" in constraints.available_stories
        assert "Research Project" in constraints.available_stories
        assert "common_app" in constraints.word_count_targets
        assert constraints.word_count_targets["common_app"] == 650

    def test_extract_constraints_from_profile_used_stories(self):
        """Test extraction of used stories from profile."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        constraints = planner._extract_constraints_from_profile()
        
        # Should track that Leadership Experience was used in mit_essay_1
        assert "mit_essay_1" in constraints.used_stories
        assert "Leadership Experience" in constraints.used_stories["mit_essay_1"]

    def test_process_user_request(self):
        """Test processing of user request through query rewriter."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        with patch.object(planner.query_rewriter, 'rewrite_query', return_value="processed request"):
            result = planner._process_user_request("help me write")
        
        assert result == "processed request"

    def test_process_user_request_error_handling(self):
        """Test error handling in user request processing."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        with patch.object(planner.query_rewriter, 'rewrite_query', side_effect=Exception("Error")):
            result = planner._process_user_request("help me write")
        
        # Should return original request on error
        assert result == "help me write"

    def test_calculate_feasibility_score_normal(self):
        """Test feasibility score calculation under normal conditions."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        plan = EssayPlan(phase=Phase.BRAINSTORMING, data={}, metadata={})
        constraints = PlanningConstraints(
            deadlines={"common_app": datetime.now() + timedelta(days=10)},
            current_workload=2,
            available_stories=["story1", "story2"]
        )
        
        score = planner._calculate_feasibility_score(plan, constraints)
        
        assert score >= 7.0  # Should be high under normal conditions

    def test_calculate_feasibility_score_tight_deadline(self):
        """Test feasibility score calculation with tight deadline."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        plan = EssayPlan(phase=Phase.BRAINSTORMING, data={}, metadata={})
        constraints = PlanningConstraints(
            deadlines={"common_app": datetime.now() + timedelta(days=1)},
            current_workload=2,
            available_stories=["story1", "story2"]
        )
        
        score = planner._calculate_feasibility_score(plan, constraints)
        
        assert score < 6.0  # Should be low with tight deadline

    def test_calculate_efficiency_score_good_plan(self):
        """Test efficiency score calculation for good plan."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={"next_tool": "brainstorm", "args": {"prompt": "test"}},
            metadata={},
            errors=[]
        )
        
        score = planner._calculate_efficiency_score(plan)
        
        assert score >= 7.0  # Should be high for good plan

    def test_calculate_efficiency_score_bad_plan(self):
        """Test efficiency score calculation for bad plan."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        plan = EssayPlan(
            phase=Phase.BRAINSTORMING,
            data={},  # No next_tool or args
            metadata={},
            errors=["Error 1", "Error 2"]
        )
        
        score = planner._calculate_efficiency_score(plan)
        
        assert score < 6.0  # Should be low for bad plan

    def test_generate_improvement_suggestions(self):
        """Test generation of improvement suggestions."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        plan = EssayPlan(phase=Phase.BRAINSTORMING, data={}, metadata={})
        constraints = PlanningConstraints()
        
        suggestions = planner._generate_improvement_suggestions(
            plan, constraints, 
            feasibility=5.0, efficiency=6.0, 
            constraint_satisfaction=8.0, story_diversity=9.0
        )
        
        assert len(suggestions) > 0
        assert any("feasibility" in suggestion.lower() or "deadline" in suggestion.lower() 
                  for suggestion in suggestions)

    def test_generate_improvement_suggestions_good_quality(self):
        """Test improvement suggestions for good quality plan."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        plan = EssayPlan(phase=Phase.BRAINSTORMING, data={}, metadata={})
        constraints = PlanningConstraints()
        
        suggestions = planner._generate_improvement_suggestions(
            plan, constraints, 
            feasibility=8.0, efficiency=8.0, 
            constraint_satisfaction=8.0, story_diversity=8.0
        )
        
        assert len(suggestions) == 1
        assert "good" in suggestions[0].lower()


if __name__ == "__main__":
    pytest.main([__file__]) 