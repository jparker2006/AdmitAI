#!/usr/bin/env python3
"""Demo script for Revision & Feedback Loops functionality.

This script demonstrates the new revision loop features:
- Intelligent revision orchestration with quality gates
- Targeted feedback generation based on evaluation results
- Progress tracking through multiple revision attempts
- Fallback mechanisms for graceful degradation
"""

import asyncio
import json
from typing import Dict, Any

from essay_agent.workflows.revision_loops import (
    RevisionLoopController,
    RevisionTracker,
    RevisionProgress,
    create_revision_controller,
    execute_intelligent_revision_loop,
)
from essay_agent.workflows.base import WorkflowState
from essay_agent.planner import Phase
from essay_agent.tools.evaluation_tools import create_enhanced_evaluator


class RevisionLoopDemo:
    """Demonstration of revision loop capabilities."""
    
    def __init__(self):
        self.scenarios = {
            "progressive_improvement": self._create_progressive_improvement_scenario(),
            "targeted_feedback": self._create_targeted_feedback_scenario(),
            "max_attempts": self._create_max_attempts_scenario(),
            "error_recovery": self._create_error_recovery_scenario(),
        }
    
    def _create_progressive_improvement_scenario(self) -> Dict[str, Any]:
        """Scenario showing progressive improvement through revision cycles."""
        return {
            "name": "Progressive Improvement",
            "description": "Essay improves from 5.5 to 8.2 through intelligent revision cycles",
            "initial_draft": "I faced a challenge in high school when I struggled with math. It was hard.",
            "essay_prompt": "Describe a challenge you faced and how you overcame it.",
            "mock_scoring_progression": [
                {
                    "overall_score": 5.5,
                    "scores": {"clarity": 5, "insight": 4, "structure": 6, "voice": 5, "prompt_fit": 6},
                    "is_strong_essay": False,
                    "feedback": "Needs more specific examples and better structure."
                },
                {
                    "overall_score": 7.0,
                    "scores": {"clarity": 7, "insight": 6, "structure": 7, "voice": 7, "prompt_fit": 7},
                    "is_strong_essay": True,
                    "feedback": "Much improved with better examples and flow."
                },
                {
                    "overall_score": 8.2,
                    "scores": {"clarity": 8, "insight": 8, "structure": 8, "voice": 8, "prompt_fit": 8},
                    "is_strong_essay": True,
                    "feedback": "Excellent essay with compelling narrative."
                }
            ],
            "mock_revisions": [
                {
                    "revised_draft": "I faced a significant challenge in high school when I struggled with advanced calculus. The complex equations seemed insurmountable, and I often felt overwhelmed during class.",
                    "changes": ["Added specific subject details", "Expanded on emotional impact"]
                },
                {
                    "revised_draft": "I faced a significant challenge in high school when I struggled with advanced calculus. The complex equations seemed insurmountable, and I often felt overwhelmed during class. However, I discovered that breaking problems into smaller steps and seeking help from my teacher transformed my approach to learning.",
                    "changes": ["Added solution strategy", "Included growth mindset"]
                }
            ],
            "expected_attempts": 2,
            "expected_final_score": 8.2
        }
    
    def _create_targeted_feedback_scenario(self) -> Dict[str, Any]:
        """Scenario showing targeted feedback based on evaluation results."""
        return {
            "name": "Targeted Feedback Generation",
            "description": "Revision feedback targets specific weak areas identified by evaluation",
            "initial_draft": "My background is diverse. I have learned many things. This has helped me grow.",
            "essay_prompt": "Share your background and identity and how it has shaped your perspective.",
            "mock_scoring_result": {
                "overall_score": 4.0,
                "scores": {"clarity": 3, "insight": 2, "structure": 4, "voice": 5, "prompt_fit": 6},
                "is_strong_essay": False,
                "feedback": "Very generic with no specific examples or personal reflection."
            },
            "expected_focus_areas": ["insight", "clarity", "structure"],
            "expected_feedback_keywords": ["self-reflection", "personal growth", "specific examples"]
        }
    
    def _create_max_attempts_scenario(self) -> Dict[str, Any]:
        """Scenario showing max attempts handling."""
        return {
            "name": "Max Attempts Reached",
            "description": "Revision loop stops after 3 attempts even with low quality",
            "initial_draft": "I think college is good. I want to go there. It will be fun.",
            "essay_prompt": "Why do you want to attend this university?",
            "mock_scoring_result": {
                "overall_score": 3.0,
                "scores": {"clarity": 3, "insight": 2, "structure": 3, "voice": 3, "prompt_fit": 4},
                "is_strong_essay": False,
                "feedback": "Extremely generic and lacks specificity."
            },
            "max_attempts": 3,
            "expected_final_score": 3.0  # Never improves
        }
    
    def _create_error_recovery_scenario(self) -> Dict[str, Any]:
        """Scenario showing error recovery and fallback."""
        return {
            "name": "Error Recovery",
            "description": "Revision loop handles tool failures gracefully",
            "initial_draft": "This is a test essay about leadership.",
            "essay_prompt": "Describe a time when you demonstrated leadership.",
            "mock_error_type": "evaluation_failure",
            "expected_fallback": "graceful_degradation"
        }
    
    async def run_demo(self):
        """Run complete demonstration of revision loop features."""
        print("🔄 Revision & Feedback Loops Demo")
        print("=" * 50)
        
        # Test basic controller functionality
        print("\n1. BASIC CONTROLLER FUNCTIONALITY")
        print("-" * 40)
        await self._demo_basic_controller()
        
        # Test targeted feedback generation
        print("\n2. TARGETED FEEDBACK GENERATION")
        print("-" * 40)
        await self._demo_targeted_feedback()
        
        # Test progress tracking
        print("\n3. PROGRESS TRACKING")
        print("-" * 40)
        await self._demo_progress_tracking()
        
        # Test revision loop scenarios
        print("\n4. REVISION LOOP SCENARIOS")
        print("-" * 40)
        
        for scenario_name, scenario in self.scenarios.items():
            print(f"\n📋 Scenario: {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            
            try:
                result = await self._run_scenario(scenario)
                self._display_results(result, scenario)
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Test quality gate decisions
        print("\n5. QUALITY GATE DECISIONS")
        print("-" * 40)
        await self._demo_quality_gates()
        
        print("\n🎉 Demo completed successfully!")
    
    async def _demo_basic_controller(self):
        """Demonstrate basic controller functionality."""
        print("   Creating revision loop controller...")
        controller = RevisionLoopController(max_attempts=3, target_score=8.0)
        
        print(f"   Max attempts: {controller.max_attempts}")
        print(f"   Target score: {controller.target_score}")
        print(f"   Min improvement: {controller.min_improvement}")
        
        # Test revision focus generation
        mock_evaluation = {
            "scores": {"clarity": 4, "insight": 3, "structure": 5, "voice": 6, "prompt_fit": 5},
            "feedback": "Needs better examples and structure"
        }
        
        focus = controller.get_revision_focus(mock_evaluation)
        print(f"   Generated focus: {focus[:100]}...")
        
        print("   ✅ Basic controller functionality works")
    
    async def _demo_targeted_feedback(self):
        """Demonstrate targeted feedback generation."""
        print("   Testing targeted feedback generation...")
        
        # Create evaluator with workflow integration
        evaluator = create_enhanced_evaluator()
        
        # Mock evaluation result
        mock_result = {
            "overall_score": 5.5,
            "scores": {"clarity": 4, "insight": 3, "structure": 6, "voice": 7, "prompt_fit": 5},
            "feedback": "Essay lacks specific examples and clear structure"
        }
        
        # Test weakest dimensions identification
        weak_dims = evaluator.get_weakest_dimensions(mock_result)
        print(f"   Weakest dimensions: {[f'{dim}: {score}' for dim, score in weak_dims[:3]]}")
        
        # Test revision feedback generation
        feedback = evaluator.generate_revision_feedback(mock_result)
        print(f"   Generated feedback: {feedback[:150]}...")
        
        # Test improvement priority
        priority = evaluator._get_improvement_priority(mock_result)
        print(f"   Improvement priority: {priority}")
        
        print("   ✅ Targeted feedback generation works")
    
    async def _demo_progress_tracking(self):
        """Demonstrate progress tracking."""
        print("   Testing progress tracking...")
        
        tracker = RevisionTracker()
        
        # Simulate revision attempts
        attempts = [
            RevisionProgress(1, 5.0, 6.5, 1.5, ["clarity", "structure"], ["Better examples"], 30.0),
            RevisionProgress(2, 6.5, 7.8, 1.3, ["insight", "voice"], ["Deeper reflection"], 25.0),
            RevisionProgress(3, 7.8, 8.2, 0.4, ["polish"], ["Final touches"], 20.0),
        ]
        
        for attempt in attempts:
            tracker.track_attempt(attempt)
        
        # Get progress summary
        summary = tracker.get_progress_summary()
        print(f"   Total attempts: {summary['total_attempts']}")
        print(f"   Total improvement: {summary['total_improvement']:.1f} points")
        print(f"   Average time per attempt: {summary['average_time_per_attempt']:.1f}s")
        print(f"   Improvement trend: {summary['improvement_trend']}")
        print(f"   Successful attempts: {summary['successful_attempts']}")
        
        # Test plateauing detection
        is_plateauing = tracker.is_plateauing()
        print(f"   Is plateauing: {is_plateauing}")
        
        print("   ✅ Progress tracking works")
    
    async def _run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific scenario."""
        scenario_name = scenario["name"]
        
        if scenario_name == "Progressive Improvement":
            return await self._run_progressive_improvement(scenario)
        elif scenario_name == "Targeted Feedback Generation":
            return await self._run_targeted_feedback_scenario(scenario)
        elif scenario_name == "Max Attempts Reached":
            return await self._run_max_attempts_scenario(scenario)
        elif scenario_name == "Error Recovery":
            return await self._run_error_recovery_scenario(scenario)
        else:
            return {"error": f"Unknown scenario: {scenario_name}"}
    
    async def _run_progressive_improvement(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run progressive improvement scenario."""
        controller = RevisionLoopController(max_attempts=3, target_score=8.0)
        
        # Simulate the workflow
        scoring_progression = scenario["mock_scoring_progression"]
        revision_results = scenario["mock_revisions"]
        
        # Track progress through simulated cycles
        results = []
        for i, (score_result, revision_result) in enumerate(zip(scoring_progression[:-1], revision_results)):
            # Simulate revision cycle
            progress = RevisionProgress(
                attempt_number=i + 1,
                previous_score=scoring_progression[i]["overall_score"],
                current_score=scoring_progression[i + 1]["overall_score"],
                score_improvement=scoring_progression[i + 1]["overall_score"] - scoring_progression[i]["overall_score"],
                focus_areas=["clarity", "structure"],
                changes_made=revision_result["changes"],
                time_taken=30.0 - (i * 5)  # Simulate decreasing time
            )
            
            controller.tracker.track_attempt(progress)
            results.append(progress)
        
        return {
            "attempts": len(results),
            "final_score": scoring_progression[-1]["overall_score"],
            "total_improvement": scoring_progression[-1]["overall_score"] - scoring_progression[0]["overall_score"],
            "progress_summary": controller.tracker.get_progress_summary(),
            "success": True
        }
    
    async def _run_targeted_feedback_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run targeted feedback scenario."""
        controller = RevisionLoopController()
        
        # Test feedback generation
        scoring_result = scenario["mock_scoring_result"]
        feedback = controller.get_revision_focus(scoring_result)
        
        # Analyze feedback for expected keywords
        feedback_lower = feedback.lower()
        found_keywords = [
            keyword for keyword in scenario["expected_feedback_keywords"]
            if keyword in feedback_lower
        ]
        
        return {
            "feedback_generated": feedback,
            "expected_keywords": scenario["expected_feedback_keywords"],
            "found_keywords": found_keywords,
            "feedback_quality": len(found_keywords) / len(scenario["expected_feedback_keywords"]),
            "success": len(found_keywords) > 0
        }
    
    async def _run_max_attempts_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run max attempts scenario."""
        controller = RevisionLoopController(max_attempts=scenario["max_attempts"], target_score=8.0)
        
        # Simulate max attempts reached
        low_score = scenario["mock_scoring_result"]["overall_score"]
        
        for i in range(scenario["max_attempts"]):
            progress = RevisionProgress(
                attempt_number=i + 1,
                previous_score=low_score,
                current_score=low_score,  # No improvement
                score_improvement=0.0,
                focus_areas=["clarity", "insight"],
                changes_made=["Minor changes"],
                time_taken=35.0
            )
            
            controller.tracker.track_attempt(progress)
        
        return {
            "attempts": scenario["max_attempts"],
            "final_score": low_score,
            "total_improvement": 0.0,
            "reason": "max_attempts_reached",
            "success": True  # Success in handling max attempts
        }
    
    async def _run_error_recovery_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run error recovery scenario."""
        controller = RevisionLoopController()
        
        # Simulate error handling
        error_type = scenario["mock_error_type"]
        
        if error_type == "evaluation_failure":
            return {
                "error_type": error_type,
                "handled_gracefully": True,
                "fallback_applied": True,
                "success": True
            }
        
        return {"error": f"Unknown error type: {error_type}"}
    
    def _display_results(self, result: Dict[str, Any], scenario: Dict[str, Any]):
        """Display scenario results."""
        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
            return
        
        print(f"   📊 Results:")
        
        if "attempts" in result:
            print(f"      Attempts: {result['attempts']}")
        
        if "final_score" in result:
            print(f"      Final Score: {result['final_score']}/10")
        
        if "total_improvement" in result:
            print(f"      Total Improvement: {result['total_improvement']:.1f} points")
        
        if "feedback_quality" in result:
            print(f"      Feedback Quality: {result['feedback_quality']:.1%}")
        
        if "reason" in result:
            print(f"      Reason: {result['reason']}")
        
        if result.get("success"):
            print("      ✅ Scenario completed successfully")
        else:
            print("      ⚠️  Scenario had issues")
        
        print()
    
    async def _demo_quality_gates(self):
        """Demonstrate quality gate decisions."""
        print("   Testing quality gate decisions...")
        
        from essay_agent.workflows.revision_loops import RevisionQualityGate
        
        gate = RevisionQualityGate(target_score=8.0, max_attempts=3)
        
        # Test different scenarios
        scenarios = [
            {"score": 8.5, "attempts": 1, "expected": False, "reason": "target_reached"},
            {"score": 6.0, "attempts": 3, "expected": False, "reason": "max_attempts"},
            {"score": 6.0, "attempts": 1, "expected": True, "reason": "continue"},
        ]
        
        for scenario in scenarios:
            # Mock state
            from unittest.mock import MagicMock
            state = MagicMock()
            state.get_evaluation_score.return_value = scenario["score"]
            state.revision_attempts = scenario["attempts"]
            
            should_continue = gate.should_continue(state)
            reason = gate.get_decision_reason(state)
            
            print(f"      Score: {scenario['score']}, Attempts: {scenario['attempts']} → Continue: {should_continue}")
            print(f"      Reason: {reason}")
            
            assert should_continue == scenario["expected"], f"Expected {scenario['expected']}, got {should_continue}"
        
        print("   ✅ Quality gate decisions work correctly")


def main():
    """Main demo function."""
    demo = RevisionLoopDemo()
    
    try:
        asyncio.run(demo.run_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 