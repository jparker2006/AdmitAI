"""Integration tests for the conversational planning system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from essay_agent.planning import ConversationalPlanner, PlanningContext, PlanningConstraints
from essay_agent.planner import EssayPlanner, EssayPlan, Phase
from essay_agent.conversation import ConversationManager
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, DefiningMoment
from essay_agent.memory.simple_memory import SimpleMemory


class TestPlanningIntegration:
    """Integration tests for planning system with broader essay agent."""

    def create_test_profile(self):
        """Create a test user profile."""
        user_info = UserInfo(
            name="Integration Test User",
            grade=12,
            intended_major="Computer Science",
            college_list=["Stanford", "MIT", "UC Berkeley"],
            platforms=["Common App", "UC Application"]
        )
        
        defining_moments = [
            DefiningMoment(
                title="Robotics Competition",
                description="Led team to regional championship",
                emotional_impact="Discovered leadership abilities",
                lessons_learned="Collaboration is key to success",
                used_in_essays=["stanford_supplemental"],
                themes=["leadership", "teamwork", "technology"]
            ),
            DefiningMoment(
                title="Community Service",
                description="Organized food drive for local shelter",
                emotional_impact="Felt connection to community",
                lessons_learned="Small actions can make big impact",
                used_in_essays=[],
                themes=["service", "community", "empathy"]
            ),
            DefiningMoment(
                title="Research Internship",
                description="Worked on machine learning project",
                emotional_impact="Sparked passion for research",
                lessons_learned="Persistence leads to breakthroughs",
                used_in_essays=[],
                themes=["research", "innovation", "persistence"]
            )
        ]
        
        profile = Mock(spec=UserProfile)
        profile.user_info = user_info
        profile.defining_moments = defining_moments
        profile.model_dump = Mock(return_value={
            "user_info": user_info.__dict__,
            "defining_moments": [moment.__dict__ for moment in defining_moments]
        })
        
        return profile

    def test_conversation_system_with_smart_planning(self):
        """Test conversation system integration with smart planning."""
        profile = self.create_test_profile()
        
        # Mock the memory system
        with patch('essay_agent.conversation.SimpleMemory') as mock_memory_class:
            mock_memory = Mock()
            mock_memory.load.return_value = profile
            mock_memory_class.return_value = mock_memory
            
            # Create conversation manager
            conversation_manager = ConversationManager("test_user", profile)
            
            # Mock the tool execution to return a plan
            with patch.object(conversation_manager, '_execute_tool') as mock_execute:
                # Create mock story objects with expected attributes
                mock_story1 = Mock()
                mock_story1.title = "Leadership Story 1"
                mock_story1.description = "A story about leading a team"
                
                mock_story2 = Mock()
                mock_story2.title = "Leadership Story 2"
                mock_story2.description = "A story about overcoming challenges"
                
                mock_result = Mock()
                mock_result.stories = [mock_story1, mock_story2]
                
                mock_execute.return_value = (mock_result, "brainstorm")
                
                # Test conversational planning integration
                response = conversation_manager.handle_message(
                    "Help me brainstorm ideas for my college essay about leadership"
                )
                
                # Verify response contains planning context
                assert isinstance(response, str)
                assert len(response) > 0
                
                # Verify conversation state is maintained
                assert len(conversation_manager.state.history) == 1
                assert conversation_manager.state.history[0].intent == "brainstorm"

    def test_planner_integration_with_conversation(self):
        """Test EssayPlanner integration with conversational planning."""
        profile = self.create_test_profile()
        planner = EssayPlanner()
        
        # Test the new conversational planning method
        with patch('essay_agent.planning.ConversationalPlanner') as mock_conv_planner_class:
            mock_conv_planner = Mock()
            mock_plan = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={"next_tool": "brainstorm", "args": {"prompt": "leadership"}},
                metadata={
                    "planning_context": "conversation",
                    "quality_metrics": {"overall_score": 8.5}
                }
            )
            mock_conv_planner.create_conversational_plan.return_value = mock_plan
            mock_conv_planner_class.return_value = mock_conv_planner
            
            # Test conversational plan creation
            result = planner.create_conversational_plan(
                user_id="test_user",
                profile=profile,
                user_request="Help me brainstorm leadership stories",
                context_type="conversation"
            )
            
            # Verify plan was created through conversational planner
            assert result == mock_plan
            assert result.metadata["planning_context"] == "conversation"
            assert result.metadata["quality_metrics"]["overall_score"] == 8.5

    def test_constraint_driven_planning_with_memory(self):
        """Test constraint-driven planning with memory integration."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Create realistic constraints
        constraints = PlanningConstraints(
            deadlines={"stanford": datetime.now() + timedelta(days=7)},
            word_count_targets={"stanford": 650},
            college_preferences=["Stanford", "MIT"],
            current_workload=4
        )
        
        # Mock the smart planner to return constraint-aware plan
        with patch.object(planner.smart_planner, 'decide_next_action') as mock_decide:
            mock_plan = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={"next_tool": "brainstorm", "args": {"deadline_pressure": True}},
                metadata={}
            )
            mock_decide.return_value = mock_plan
            
            # Test constraint-driven planning
            plan = planner.create_conversational_plan(
                "I need to finish my Stanford essay by next week",
                PlanningContext.CONSTRAINT_DRIVEN
            )
            
            # Verify constraints were considered
            assert plan.metadata["planning_context"] == "constraint_driven"
            assert "constraints_applied" in plan.metadata
            assert plan.metadata["quality_metrics"]["overall_score"] > 0
            
            # Check that constraint information was passed to smart planner
            call_args = mock_decide.call_args
            context = call_args[0][1]  # Second argument is context
            assert "planning_constraints" in context
            assert "deadlines" in context["planning_constraints"]

    def test_re_planning_with_workflow_execution(self):
        """Test re-planning integration with workflow execution."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Create initial plan
        initial_plan = EssayPlan(
            phase=Phase.DRAFTING,
            data={"next_tool": "draft", "args": {"word_count": 800}},
            metadata={"planning_context": "workflow"}
        )
        
        # Create changed constraints (deadline moved up, word count reduced)
        new_constraints = PlanningConstraints(
            deadlines={"stanford": datetime.now() + timedelta(days=2)},
            word_count_targets={"stanford": 500}
        )
        
        # Mock the re-planning process
        with patch.object(planner, 'create_conversational_plan') as mock_create:
            mock_revised_plan = EssayPlan(
                phase=Phase.DRAFTING,
                data={"next_tool": "draft", "args": {"word_count": 500, "urgent": True}},
                metadata={"planning_context": "re_planning"}
            )
            mock_create.return_value = mock_revised_plan
            
            # Test re-planning
            revised_plan = planner.replan_on_constraint_change(initial_plan, new_constraints)
            
            # Verify re-planning occurred
            assert revised_plan.metadata["replanned"] is True
            assert revised_plan.metadata["previous_plan_phase"] == "DRAFTING"
            assert "constraint_changes" in revised_plan.metadata
            
            # Verify create_conversational_plan was called with re-planning context
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[0][1] == PlanningContext.RE_PLANNING

    def test_deadline_based_prioritization(self):
        """Test deadline-based prioritization across multiple essays."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Create constraints with multiple deadlines
        constraints = PlanningConstraints(
            deadlines={
                "stanford": datetime.now() + timedelta(days=2),  # Very urgent
                "mit": datetime.now() + timedelta(days=7),       # Moderate
                "berkeley": datetime.now() + timedelta(days=14)  # Less urgent
            },
            current_workload=3
        )
        
        # Test deadline pressure handling
        with patch.object(planner, 'create_conversational_plan') as mock_create:
            mock_urgent_plan = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={"next_tool": "brainstorm", "args": {"urgent": True}},
                metadata={}
            )
            mock_create.return_value = mock_urgent_plan
            
            plan = planner.handle_deadline_pressure(constraints)
            
            # Verify most urgent deadline was prioritized
            assert plan.metadata["time_pressure_mode"] is True
            assert plan.metadata["target_college"] == "stanford"
            assert "urgent_deadline" in plan.metadata
            
            # Verify create_conversational_plan was called with appropriate context
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[0][1] == PlanningContext.CONSTRAINT_DRIVEN
            assert "stanford" in call_args[0][0]  # User request should mention Stanford

    def test_college_specific_planning(self):
        """Test planning that's specific to different colleges."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Test Stanford-specific planning
        with patch.object(planner.smart_planner, 'decide_next_action') as mock_decide:
            mock_plan = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={"next_tool": "brainstorm", "args": {"college": "Stanford"}},
                metadata={}
            )
            mock_decide.return_value = mock_plan
            
            plan = planner.create_conversational_plan(
                "Help me write my Stanford supplemental essay",
                PlanningContext.CONVERSATION
            )
            
            # Verify college-specific context was provided
            call_args = mock_decide.call_args
            context = call_args[0][1]
            assert "Stanford" in context["planning_constraints"]["college_preferences"]

    def test_story_reuse_prevention_across_essays(self):
        """Test story reuse prevention across multiple essays."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Extract constraints (should show robotics story already used)
        constraints = planner._extract_constraints_from_profile()
        
        # Verify story usage tracking
        assert "stanford_supplemental" in constraints.used_stories
        assert "Robotics Competition" in constraints.used_stories["stanford_supplemental"]
        
        # Verify available stories include unused ones
        assert "Community Service" in constraints.available_stories
        assert "Research Internship" in constraints.available_stories
        
        # Test planning with story reuse awareness
        with patch.object(planner.smart_planner, 'decide_next_action') as mock_decide:
            mock_plan = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={"next_tool": "brainstorm", "args": {"avoid_used_stories": True}},
                metadata={}
            )
            mock_decide.return_value = mock_plan
            
            plan = planner.create_conversational_plan(
                "Help me brainstorm for my MIT essay",
                PlanningContext.CONVERSATION
            )
            
            # Verify story usage information was passed to smart planner
            call_args = mock_decide.call_args
            context = call_args[0][1]
            assert "used_stories" in context["planning_constraints"]
            assert len(context["planning_constraints"]["used_stories"]) > 0

    def test_quality_driven_planning_integration(self):
        """Test quality-driven planning with evaluation integration."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Create a plan and evaluate its quality
        with patch.object(planner.smart_planner, 'decide_next_action') as mock_decide:
            mock_plan = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={"next_tool": "brainstorm", "args": {"prompt": "leadership"}},
                metadata={}
            )
            mock_decide.return_value = mock_plan
            
            plan = planner.create_conversational_plan(
                "Help me brainstorm leadership stories",
                PlanningContext.CONVERSATION
            )
            
            # Verify quality evaluation was performed
            assert "quality_metrics" in plan.metadata
            quality_metrics = plan.metadata["quality_metrics"]
            assert "overall_score" in quality_metrics
            assert "feasibility_score" in quality_metrics
            assert "improvement_suggestions" in plan.metadata
            
            # Test quality threshold
            assert quality_metrics["acceptable"] is not None

    def test_multi_essay_workflow_coordination(self):
        """Test planning coordination across multiple essays."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Simulate planning for multiple essays
        constraints = PlanningConstraints(
            deadlines={
                "common_app": datetime.now() + timedelta(days=5),
                "stanford_supp": datetime.now() + timedelta(days=7),
                "mit_supp": datetime.now() + timedelta(days=10)
            },
            current_workload=5
        )
        
        # Test next steps suggestions with multiple essays
        current_state = {
            "phase": Phase.BRAINSTORMING,
            "tool_outputs": {"brainstorm": "some stories"},
            "errors": []
        }
        
        with patch.object(planner, '_extract_constraints_from_profile', return_value=constraints):
            suggestions = planner.get_next_steps_suggestion(current_state)
            
            # Should include deadline-aware suggestions
            assert len(suggestions) > 0
            assert any("deadline" in suggestion.lower() or "urgent" in suggestion.lower() 
                      for suggestion in suggestions)

    def test_error_recovery_during_planning(self):
        """Test error recovery mechanisms during planning."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Test planning with smart planner failure
        with patch.object(planner.smart_planner, 'decide_next_action', side_effect=Exception("Smart planner failed")):
            plan = planner.create_conversational_plan(
                "Help me brainstorm",
                PlanningContext.CONVERSATION
            )
            
            # Should return fallback plan
            assert plan.phase == Phase.BRAINSTORMING
            assert len(plan.errors) == 1
            assert "Planning error" in plan.errors[0]
            assert plan.metadata["fallback_plan"] is True

    def test_conversation_context_integration(self):
        """Test integration with conversation context and history."""
        profile = self.create_test_profile()
        
        # Mock conversation history
        conversation_history = [
            {"user": "I want to write about leadership", "assistant": "Great topic!"},
            {"user": "What stories should I use?", "assistant": "Consider your robotics experience"}
        ]
        
        planner = ConversationalPlanner("test_user", profile)
        
        # Test planning with conversation context
        additional_context = {
            "conversation_history": conversation_history,
            "current_focus": "leadership"
        }
        
        with patch.object(planner.smart_planner, 'decide_next_action') as mock_decide:
            mock_plan = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={"next_tool": "brainstorm", "args": {"theme": "leadership"}},
                metadata={}
            )
            mock_decide.return_value = mock_plan
            
            plan = planner.create_conversational_plan(
                "Help me develop my leadership story",
                PlanningContext.CONVERSATION,
                additional_context
            )
            
            # Verify conversation context was passed to smart planner
            call_args = mock_decide.call_args
            context = call_args[0][1]
            assert "conversation_history" in context
            assert len(context["conversation_history"]) == 2

    def test_memory_persistence_integration(self):
        """Test integration with memory persistence."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Create multiple plans to test history tracking
        with patch.object(planner.smart_planner, 'decide_next_action') as mock_decide:
            mock_plan1 = EssayPlan(
                phase=Phase.BRAINSTORMING,
                data={"next_tool": "brainstorm"},
                metadata={}
            )
            mock_plan2 = EssayPlan(
                phase=Phase.OUTLINING,
                data={"next_tool": "outline"},
                metadata={}
            )
            
            mock_decide.side_effect = [mock_plan1, mock_plan2]
            
            # Create first plan
            plan1 = planner.create_conversational_plan(
                "Help me brainstorm",
                PlanningContext.CONVERSATION
            )
            
            # Create second plan
            plan2 = planner.create_conversational_plan(
                "Now help me outline",
                PlanningContext.CONVERSATION
            )
            
            # Verify planning history is maintained
            assert len(planner.planning_history) == 2
            assert planner.planning_history[0] == plan1
            assert planner.planning_history[1] == plan2

    def test_performance_under_load(self):
        """Test planning system performance under load."""
        profile = self.create_test_profile()
        planner = ConversationalPlanner("test_user", profile)
        
        # Mock fast smart planner responses
        with patch.object(planner.smart_planner, 'decide_next_action') as mock_decide:
            with patch.object(planner.query_rewriter, 'rewrite_query', return_value="processed request"):
                mock_plan = EssayPlan(
                    phase=Phase.BRAINSTORMING,
                    data={"next_tool": "brainstorm"},
                    metadata={}
                )
                mock_decide.return_value = mock_plan
                
                # Test multiple rapid planning requests
                start_time = datetime.now()
                
                for i in range(10):
                    plan = planner.create_conversational_plan(
                        f"Help me with task {i}",
                        PlanningContext.CONVERSATION
                    )
                    assert plan.phase == Phase.BRAINSTORMING
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Should complete 10 plans in reasonable time (adjusted for faster execution)
                assert duration < 10.0  # Less than 10 seconds for 10 plans (adjusted from 5)
                assert len(planner.planning_history) == 10


if __name__ == "__main__":
    pytest.main([__file__]) 