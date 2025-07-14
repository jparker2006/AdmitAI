"""Integration tests for the smart planner with the broader essay agent system."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from essay_agent.planner import EssayReActPlanner, Phase, EssayPlan
from essay_agent.executor import EssayExecutor
from essay_agent.memory import HierarchicalMemory, SimpleMemory
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile, EssayRecord, EssayVersion, Activity
from langchain.llms.fake import FakeListLLM


class TestSmartPlannerIntegration:
    """Integration tests for smart planner with executor and memory."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a test user profile
        self.user_info = UserInfo(
            name="Test Student",
            grade=12,
            intended_major="Computer Science",
            college_list=["MIT", "Stanford"],
            platforms=["CommonApp"]
        )
        
        self.academic_profile = AcademicProfile(
            gpa=3.8,
            test_scores={"SAT": 1500},
            courses=["AP Computer Science", "AP Calculus"],
            activities=[
                Activity(
                    name="Debate Team",
                    role="Captain",
                    duration="2 years",
                    description="Led varsity debate team",
                    impact="Developed leadership and public speaking skills"
                ),
                Activity(
                    name="Robotics Club",
                    role="Lead Programmer",
                    duration="3 years",
                    description="Programmed autonomous robots",
                    impact="Enhanced technical problem-solving abilities"
                )
            ]
        )
        
        self.user_profile = UserProfile(
            user_info=self.user_info,
            academic_profile=self.academic_profile,
            core_values=[]
        )

    def test_revision_loop_workflow(self):
        """Test smart planner orchestrating revision loops based on quality metrics."""
        
        # Sequence of responses for revision loop:
        # 1. First draft creation
        # 2. Quality evaluation reveals low score
        # 3. Revision decision based on quality
        # 4. Final polish when quality improves
        
        llm_responses = [
            # 1. Initial draft request
            json.dumps({
                "tool": "draft",
                "args": {"outline": "test outline"},
                "reasoning": {
                    "context_analysis": "User has outline, needs draft",
                    "decision_type": "CONTINUE",
                    "tool_selection": "draft tool for essay writing"
                },
                "metadata": {"confidence": 0.85, "phase": "DRAFTING"}
            }),
            
            # 2. Quality evaluation after draft
            json.dumps({
                "tool": "essay_scoring",
                "args": {"essay_text": "draft text", "essay_prompt": "test prompt"},
                "reasoning": {
                    "context_analysis": "Draft completed, need quality assessment",
                    "decision_type": "RETRY",
                    "tool_selection": "essay_scoring for quality baseline"
                },
                "metadata": {"confidence": 0.9, "phase": "REVISING"}
            }),
            
            # 3. Revision based on low quality
            json.dumps({
                "tool": "revise",
                "args": {"focus": "clarity", "target_score": 7.5},
                "reasoning": {
                    "context_analysis": "Quality score 6.2 below threshold",
                    "quality_assessment": "Essay needs clarity improvements",
                    "decision_type": "LOOP",
                    "tool_selection": "revise tool for improvement"
                },
                "metadata": {"confidence": 0.8, "phase": "REVISING", "quality_score": 6.2}
            }),
            
            # 4. Final polish after improvement
            json.dumps({
                "tool": "polish",
                "args": {"word_count": 650},
                "reasoning": {
                    "context_analysis": "Revised essay quality improved",
                    "quality_assessment": "Score 7.8 meets threshold",
                    "decision_type": "CONTINUE",
                    "tool_selection": "polish for final optimization"
                },
                "metadata": {"confidence": 0.9, "phase": "POLISHING", "quality_score": 7.8}
            })
        ]
        
        fake_llm = FakeListLLM(responses=llm_responses)
        planner = EssayReActPlanner(llm=fake_llm)
        
        # Mock tool registry with realistic outputs
        mock_tools = {
            "draft": Mock(return_value={"draft_text": "Initial draft content", "word_count": 643}),
            "essay_scoring": Mock(return_value={
                "overall_score": 6.2,
                "is_strong_essay": False,
                "scores": {"clarity": 5, "insight": 7, "structure": 6, "voice": 7, "prompt_fit": 6}
            }),
            "revise": Mock(return_value={"revised_text": "Improved draft content", "changes": ["Improved clarity"]}),
            "polish": Mock(return_value={"final_draft": "Polished essay content", "word_count": 650})
        }
        
        with patch('essay_agent.planner.TOOL_REGISTRY', mock_tools):
            with patch('essay_agent.planner.SimpleMemory') as mock_memory:
                mock_memory.load.return_value = self.user_profile
                
                # Simulate revision loop workflow
                context = {"user_id": "test_user"}
                
                # 1. Draft creation
                plan1 = planner.decide_next_action("Write my essay draft", context)
                assert plan1.data["next_tool"] == "draft"
                assert plan1.phase == Phase.DRAFTING
                
                # 2. Quality evaluation
                context["tool_outputs"] = {"draft": mock_tools["draft"].return_value}
                plan2 = planner.decide_next_action("Evaluate my draft", context)
                assert plan2.data["next_tool"] == "essay_scoring"
                assert plan2.phase == Phase.REVISING
                
                # 3. Revision decision
                context["tool_outputs"]["essay_scoring"] = mock_tools["essay_scoring"].return_value
                plan3 = planner.decide_next_action("Improve my essay", context)
                assert plan3.data["next_tool"] == "revise"
                assert plan3.metadata["quality_score"] == 6.2
                assert "LOOP" in plan3.metadata["reasoning"]["decision_type"]
                
                # 4. Final polish
                context["tool_outputs"]["revise"] = mock_tools["revise"].return_value
                plan4 = planner.decide_next_action("Finalize my essay", context)
                assert plan4.data["next_tool"] == "polish"
                assert plan4.metadata["quality_score"] == 7.8
                assert plan4.phase == Phase.POLISHING

    def test_story_reuse_prevention(self):
        """Test smart planner prevents story reuse across essays."""
        
        # Create user profile with existing essay history
        from datetime import datetime
        existing_essay = EssayRecord(
            prompt_id="previous_prompt",
            prompt_text="Previous essay prompt",
            platform="CommonApp",
            status="completed",
            versions=[EssayVersion(
                version=1,
                timestamp=datetime.now(),
                content="Previous essay content",
                word_count=650,
                used_stories=["My Leadership Journey", "Overcoming Challenges"]
            )]
        )
        
        user_profile_with_history = UserProfile(
            user_info=self.user_info,
            academic_profile=self.academic_profile,
            core_values=[],
            essay_history=[existing_essay]
        )
        
        # LLM response that should detect story reuse
        llm_response = json.dumps({
            "tool": "brainstorm",
            "args": {"exclude_stories": ["My Leadership Journey", "Overcoming Challenges"]},
            "reasoning": {
                "context_analysis": "User has existing essays for CommonApp platform",
                "decision_type": "BRANCH",
                "tool_selection": "brainstorm with story exclusion for uniqueness"
            },
            "metadata": {
                "confidence": 0.85,
                "phase": "BRAINSTORMING", 
                "memory_flags": ["story_reuse_checked", "platform_awareness"]
            }
        })
        
        fake_llm = FakeListLLM(responses=[llm_response])
        planner = EssayReActPlanner(llm=fake_llm)
        
        mock_tools = {
            "brainstorm": Mock(return_value={"stories": ["New Story 1", "New Story 2", "New Story 3"]})
        }
        
        with patch('essay_agent.planner.TOOL_REGISTRY', mock_tools):
            with patch('essay_agent.planner.SimpleMemory') as mock_memory:
                mock_memory.load.return_value = user_profile_with_history
                
                context = {"user_id": "test_user"}
                plan = planner.decide_next_action("Generate new story ideas for CommonApp", context)
                
                # Verify story reuse prevention
                assert plan.data["next_tool"] == "brainstorm"
                assert "story_reuse_checked" in plan.metadata["memory_flags"]
                assert "BRANCH" in plan.metadata["reasoning"]["decision_type"]
                
                # Verify exclusion of previously used stories
                args = plan.data["args"]
                if "exclude_stories" in args:
                    assert "My Leadership Journey" in args["exclude_stories"]
                    assert "Overcoming Challenges" in args["exclude_stories"]

    def test_quality_threshold_branching(self):
        """Test smart planner branches to different approach when quality is critically low."""
        
        # Simulate critically low alignment score requiring major rework
        llm_response = json.dumps({
            "tool": "outline",
            "args": {"focus": "prompt_alignment", "rework": True},
            "reasoning": {
                "context_analysis": "Draft exists but alignment critically low",
                "quality_assessment": "Alignment score 3.5 indicates major prompt mismatch",
                "decision_type": "BRANCH",
                "tool_selection": "outline tool for structural rework"
            },
            "metadata": {
                "confidence": 0.75,
                "phase": "OUTLINING",
                "quality_score": 3.5,
                "memory_flags": ["alignment_critical"]
            }
        })
        
        fake_llm = FakeListLLM(responses=[llm_response])
        planner = EssayReActPlanner(llm=fake_llm)
        
        mock_tools = {
            "outline": Mock(return_value={"outline": "Restructured outline", "alignment_focus": True})
        }
        
        with patch('essay_agent.planner.TOOL_REGISTRY', mock_tools):
            with patch('essay_agent.planner.SimpleMemory') as mock_memory:
                mock_memory.load.return_value = self.user_profile
                
                # Context with critically low alignment
                context = {
                    "user_id": "test_user",
                    "tool_outputs": {
                        "alignment_check": {
                            "alignment_score": 3.5,
                            "is_fully_aligned": False,
                            "missing_elements": ["key requirement 1", "key requirement 2"]
                        }
                    }
                }
                
                plan = planner.decide_next_action("My essay doesn't address the prompt well", context)
                
                # Verify branching decision
                assert plan.data["next_tool"] == "outline"
                assert plan.phase == Phase.OUTLINING
                assert "BRANCH" in plan.metadata["reasoning"]["decision_type"]
                assert plan.metadata["quality_score"] == 3.5
                assert "alignment_critical" in plan.metadata["memory_flags"]

    def test_memory_driven_voice_consistency(self):
        """Test smart planner maintains voice consistency using memory."""
        
        # Create user profile with established voice characteristics
        user_profile_with_voice = UserProfile(
            user_info=self.user_info,
            academic_profile=self.academic_profile,
            core_values=[],
            voice_characteristics={
                "tone": "reflective",
                "style": "analytical",
                "preferred_structure": "narrative"
            }
        )
        
        llm_response = json.dumps({
            "tool": "draft",
            "args": {"maintain_voice": True, "tone": "reflective", "style": "analytical"},
            "reasoning": {
                "context_analysis": "User has established voice from previous essays",
                "decision_type": "CONTINUE",
                "tool_selection": "draft with voice consistency maintained"
            },
            "metadata": {
                "confidence": 0.88,
                "phase": "DRAFTING",
                "memory_flags": ["voice_consistency_maintained"]
            }
        })
        
        fake_llm = FakeListLLM(responses=[llm_response])
        planner = EssayReActPlanner(llm=fake_llm)
        
        mock_tools = {
            "draft": Mock(return_value={"draft_text": "Consistent voice draft", "voice_maintained": True})
        }
        
        with patch('essay_agent.planner.TOOL_REGISTRY', mock_tools):
            with patch('essay_agent.planner.SimpleMemory') as mock_memory:
                mock_memory.load.return_value = user_profile_with_voice
                
                context = {"user_id": "test_user"}
                plan = planner.decide_next_action("Write my essay draft", context)
                
                # Verify voice consistency
                assert plan.data["next_tool"] == "draft"
                assert "voice_consistency_maintained" in plan.metadata["memory_flags"]
                
                # Verify voice parameters in args
                args = plan.data["args"]
                assert args.get("maintain_voice") is True
                assert args.get("tone") == "reflective"
                assert args.get("style") == "analytical"

    def test_planner_executor_integration(self):
        """Test smart planner integration with executor for complete workflow."""
        
        # Create sequence for complete workflow
        llm_responses = [
            json.dumps({
                "tool": "brainstorm",
                "args": {"essay_prompt": "test prompt"},
                "reasoning": {"decision_type": "CONTINUE"},
                "metadata": {"confidence": 0.9, "phase": "BRAINSTORMING"}
            }),
            json.dumps({
                "tool": "outline",
                "args": {"selected_story": "Story 1"},
                "reasoning": {"decision_type": "CONTINUE"},
                "metadata": {"confidence": 0.85, "phase": "OUTLINING"}
            })
        ]
        
        fake_llm = FakeListLLM(responses=llm_responses)
        planner = EssayReActPlanner(llm=fake_llm)
        executor = EssayExecutor()
        
        # Mock tools for executor
        mock_tools = {
            "brainstorm": Mock(return_value={"stories": ["Story 1", "Story 2", "Story 3"]}),
            "outline": Mock(return_value={"outline": "Structured outline"})
        }
        
        with patch('essay_agent.planner.TOOL_REGISTRY', mock_tools):
            with patch('essay_agent.executor.TOOL_REGISTRY', mock_tools):
                with patch('essay_agent.planner.SimpleMemory') as mock_memory:
                    mock_memory.load.return_value = self.user_profile
                    
                    # Test planner → executor workflow
                    context = {"user_id": "test_user"}
                    
                    # Get plan from smart planner
                    plan = planner.decide_next_action("Generate story ideas", context)
                    assert plan.data["next_tool"] == "brainstorm"
                    
                    # Execute plan
                    result = executor.run_plan(plan)
                    assert "brainstorm" in result
                    assert result["brainstorm"]["stories"] == ["Story 1", "Story 2", "Story 3"]

    def test_error_recovery_in_workflow(self):
        """Test smart planner error recovery during workflow execution."""
        
        # Simulate error scenario and recovery
        llm_responses = [
            "Invalid JSON response",  # First attempt fails
            json.dumps({
                "tool": "echo",
                "args": {"message": "Fallback to simple tool"},
                "reasoning": {"decision_type": "RETRY"},
                "metadata": {"confidence": 0.6, "phase": "BRAINSTORMING"}
            })
        ]
        
        fake_llm = FakeListLLM(responses=llm_responses)
        planner = EssayReActPlanner(llm=fake_llm)
        
        mock_tools = {
            "echo": Mock(return_value={"response": "Echo response"})
        }
        
        with patch('essay_agent.planner.TOOL_REGISTRY', mock_tools):
            with patch('essay_agent.planner.SimpleMemory') as mock_memory:
                mock_memory.load.return_value = self.user_profile
                
                context = {"user_id": "test_user"}
                plan = planner.decide_next_action("Test error recovery", context)
                
                # Verify fallback mechanism worked
                assert "fallback_reason" in plan.metadata
                assert "Smart planning failed" in plan.metadata["fallback_reason"]
                assert plan.data["next_tool"] == "echo"

    def test_conversation_context_integration(self):
        """Test smart planner uses conversation context for decision making."""
        
        llm_response = json.dumps({
            "tool": "revise",
            "args": {"focus": "introduction", "user_feedback": "make it more engaging"},
            "reasoning": {
                "context_analysis": "User expressed dissatisfaction with introduction",
                "decision_type": "RETRY",
                "tool_selection": "revise tool with user feedback integration"
            },
            "metadata": {
                "confidence": 0.82,
                "phase": "REVISING",
                "memory_flags": ["user_feedback_integrated"]
            }
        })
        
        fake_llm = FakeListLLM(responses=[llm_response])
        planner = EssayReActPlanner(llm=fake_llm)
        
        mock_tools = {
            "revise": Mock(return_value={"revised_text": "More engaging introduction", "changes": ["Improved hook"]})
        }
        
        with patch('essay_agent.planner.TOOL_REGISTRY', mock_tools):
            with patch('essay_agent.planner.SimpleMemory') as mock_memory:
                mock_memory.load.return_value = self.user_profile
                
                # Context with conversation history
                context = {
                    "user_id": "test_user",
                    "conversation_history": [
                        "I don't like how my essay starts",
                        "The introduction feels boring",
                        "Can you make it more engaging?"
                    ]
                }
                
                plan = planner.decide_next_action("Improve my introduction", context)
                
                # Verify conversation context integration
                assert plan.data["next_tool"] == "revise"
                assert "user_feedback_integrated" in plan.metadata["memory_flags"]
                assert "user_feedback" in plan.data["args"]
                assert plan.data["args"]["user_feedback"] == "make it more engaging"

    def test_quality_metrics_progression(self):
        """Test smart planner tracks quality improvement over revision cycles."""
        
        # Simulate quality progression through revision cycles
        llm_responses = [
            json.dumps({
                "tool": "revise",
                "args": {"focus": "clarity"},
                "reasoning": {"quality_assessment": "Score 6.2 needs improvement"},
                "metadata": {"confidence": 0.8, "phase": "REVISING", "quality_score": 6.2, "revision_count": 1}
            }),
            json.dumps({
                "tool": "revise",
                "args": {"focus": "structure"},
                "reasoning": {"quality_assessment": "Score 6.8 improved but still below threshold"},
                "metadata": {"confidence": 0.85, "phase": "REVISING", "quality_score": 6.8, "revision_count": 2}
            }),
            json.dumps({
                "tool": "polish",
                "args": {"final_check": True},
                "reasoning": {"quality_assessment": "Score 7.3 meets threshold"},
                "metadata": {"confidence": 0.9, "phase": "POLISHING", "quality_score": 7.3, "revision_count": 2}
            })
        ]
        
        fake_llm = FakeListLLM(responses=llm_responses)
        planner = EssayReActPlanner(llm=fake_llm)
        
        mock_tools = {
            "revise": Mock(return_value={"revised_text": "Improved content"}),
            "polish": Mock(return_value={"final_draft": "Polished content"})
        }
        
        with patch('essay_agent.planner.TOOL_REGISTRY', mock_tools):
            with patch('essay_agent.planner.SimpleMemory') as mock_memory:
                mock_memory.load.return_value = self.user_profile
                
                context = {"user_id": "test_user"}
                
                # Track quality progression
                plan1 = planner.decide_next_action("Revise for clarity", context)
                assert plan1.metadata["quality_score"] == 6.2
                assert plan1.metadata["revision_count"] == 1
                
                plan2 = planner.decide_next_action("Revise structure", context)
                assert plan2.metadata["quality_score"] == 6.8
                assert plan2.metadata["revision_count"] == 2
                
                plan3 = planner.decide_next_action("Final polish", context)
                assert plan3.metadata["quality_score"] == 7.3
                assert plan3.data["next_tool"] == "polish"  # Quality threshold met 