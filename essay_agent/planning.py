"""
Dynamic conversational planning system for essay writing workflows.

This module provides context-aware planning that integrates with the existing
smart planner while adding conversational capabilities, constraint handling,
and plan quality evaluation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json

from .planner import EssayReActPlanner, EssayPlan, Phase
from .memory.user_profile_schema import UserProfile
from .query_rewriter import QueryRewriter
from .utils.logging import debug_print


class PlanningContext(Enum):
    """Context types for planning decisions"""
    CONVERSATION = "conversation"
    WORKFLOW = "workflow"
    CONSTRAINT_DRIVEN = "constraint_driven"
    RE_PLANNING = "re_planning"


@dataclass
class PlanningConstraints:
    """Constraints that influence planning decisions"""
    deadlines: Dict[str, datetime] = field(default_factory=dict)
    word_count_targets: Dict[str, int] = field(default_factory=dict)
    college_preferences: List[str] = field(default_factory=list)
    available_stories: List[str] = field(default_factory=list)
    used_stories: Dict[str, List[str]] = field(default_factory=dict)
    current_workload: int = 0
    time_available: Optional[int] = None  # minutes available
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for context passing"""
        return {
            "deadlines": {k: v.isoformat() for k, v in self.deadlines.items()},
            "word_count_targets": self.word_count_targets,
            "college_preferences": self.college_preferences,
            "available_stories": self.available_stories,
            "used_stories": self.used_stories,
            "current_workload": self.current_workload,
            "time_available": self.time_available
        }


@dataclass
class PlanQuality:
    """Quality metrics for plan evaluation"""
    feasibility_score: float
    efficiency_score: float
    constraint_satisfaction: float
    story_diversity_score: float
    overall_score: float
    improvement_suggestions: List[str] = field(default_factory=list)
    
    def is_acceptable(self, threshold: float = 7.0) -> bool:
        """Check if plan quality meets acceptance threshold"""
        return self.overall_score >= threshold


class ConversationalPlanner:
    """Dynamic planning system for conversational essay writing"""
    
    def __init__(self, user_id: str, profile: UserProfile):
        self.user_id = user_id
        self.profile = profile
        self.smart_planner = EssayReActPlanner()
        self.query_rewriter = QueryRewriter()
        self.planning_history: List[EssayPlan] = []
        
    def create_conversational_plan(self, user_request: str, context: PlanningContext, 
                                 additional_context: Dict[str, Any] = None) -> EssayPlan:
        """Create a plan based on conversational context and user constraints"""
        
        debug_print(True, f"Creating conversational plan for context: {context.value}")
        
        try:
            # Step 1: Process user request through query rewriter
            processed_request = self._process_user_request(user_request)
            
            # Step 2: Extract planning constraints from user profile
            constraints = self._extract_constraints_from_profile()
            
            # Step 3: Build enhanced context for smart planner
            enhanced_context = self._build_enhanced_context(
                processed_request, context, constraints, additional_context or {}
            )
            
            # Step 4: Use smart planner with enhanced context
            plan = self.smart_planner.decide_next_action(processed_request, enhanced_context)
            
            # Step 5: Evaluate plan quality
            quality = self.evaluate_plan_quality(plan, constraints)
            
            # Step 6: Store quality metrics in plan metadata
            plan.metadata.update({
                "planning_context": context.value,
                "quality_metrics": {
                    "feasibility_score": quality.feasibility_score,
                    "efficiency_score": quality.efficiency_score,
                    "constraint_satisfaction": quality.constraint_satisfaction,
                    "story_diversity_score": quality.story_diversity_score,
                    "overall_score": quality.overall_score,
                    "acceptable": quality.is_acceptable()
                },
                "improvement_suggestions": quality.improvement_suggestions,
                "constraints_applied": constraints.to_dict()
            })
            
            # Step 7: Store in planning history
            self.planning_history.append(plan)
            
            debug_print(True, f"Plan created with quality score: {quality.overall_score}")
            
            return plan
            
        except Exception as e:
            debug_print(True, f"Error creating conversational plan: {e}")
            # Return fallback plan
            return EssayPlan(
                phase=Phase.BRAINSTORMING,
                errors=[f"Planning error: {str(e)}"],
                metadata={"fallback_plan": True, "error": str(e)}
            )
    
    def evaluate_plan_quality(self, plan: EssayPlan, constraints: PlanningConstraints = None) -> PlanQuality:
        """Evaluate plan quality against constraints and feasibility"""
        
        if constraints is None:
            constraints = self._extract_constraints_from_profile()
            
        # Calculate individual quality scores
        feasibility_score = self._calculate_feasibility_score(plan, constraints)
        efficiency_score = self._calculate_efficiency_score(plan)
        constraint_satisfaction = self._calculate_constraint_satisfaction(plan, constraints)
        story_diversity_score = self._calculate_story_diversity_score(plan, constraints)
        
        # Calculate overall score (weighted average)
        overall_score = (
            feasibility_score * 0.3 +
            efficiency_score * 0.25 +
            constraint_satisfaction * 0.25 +
            story_diversity_score * 0.2
        )
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            plan, constraints, feasibility_score, efficiency_score, 
            constraint_satisfaction, story_diversity_score
        )
        
        return PlanQuality(
            feasibility_score=feasibility_score,
            efficiency_score=efficiency_score,
            constraint_satisfaction=constraint_satisfaction,
            story_diversity_score=story_diversity_score,
            overall_score=overall_score,
            improvement_suggestions=improvement_suggestions
        )
    
    def replan_on_constraint_change(self, current_plan: EssayPlan, 
                                   new_constraints: PlanningConstraints) -> EssayPlan:
        """Adapt existing plan when constraints change"""
        
        debug_print(True, "Re-planning due to constraint changes")
        
        try:
            # Analyze what changed
            old_constraints = self._extract_constraints_from_profile()
            constraint_changes = self._analyze_constraint_changes(old_constraints, new_constraints)
            
            # Update profile with new constraints (if applicable)
            self._update_profile_with_constraints(new_constraints)
            
            # Create new plan with preserved context
            preserved_context = {
                "previous_plan": current_plan.data,
                "constraint_changes": constraint_changes,
                "preserve_completed_work": True
            }
            
            # Generate user request for re-planning
            replan_request = self._generate_replan_request(constraint_changes)
            
            # Create new plan
            new_plan = self.create_conversational_plan(
                replan_request, 
                PlanningContext.RE_PLANNING,
                preserved_context
            )
            
            # Mark as re-planned
            new_plan.metadata.update({
                "replanned": True,
                "previous_plan_phase": current_plan.phase.name,
                "constraint_changes": constraint_changes
            })
            
            return new_plan
            
        except Exception as e:
            debug_print(True, f"Error during re-planning: {e}")
            # Return current plan with error
            current_plan.errors.append(f"Re-planning failed: {str(e)}")
            return current_plan
    
    def get_next_steps_suggestion(self, current_state: Dict[str, Any]) -> List[str]:
        """Suggest next steps based on current essay state"""
        
        suggestions = []
        
        try:
            # Analyze current state
            phase = current_state.get("phase", Phase.BRAINSTORMING)
            tool_outputs = current_state.get("tool_outputs", {})
            errors = current_state.get("errors", [])
            
            # Phase-specific suggestions
            if phase == Phase.BRAINSTORMING:
                if "brainstorm" not in tool_outputs:
                    suggestions.append("Generate story ideas using the brainstorm tool")
                else:
                    suggestions.append("Review your stories and create an outline")
                    
            elif phase == Phase.OUTLINING:
                if "outline" not in tool_outputs:
                    suggestions.append("Create an essay outline from your chosen story")
                else:
                    suggestions.append("Review your outline and start drafting")
                    
            elif phase == Phase.DRAFTING:
                if "draft" not in tool_outputs:
                    suggestions.append("Write your first draft based on the outline")
                else:
                    suggestions.append("Review your draft and consider revisions")
                    
            elif phase == Phase.REVISING:
                suggestions.append("Use evaluation tools to identify areas for improvement")
                suggestions.append("Apply targeted revisions to weak sections")
                
            elif phase == Phase.POLISHING:
                suggestions.append("Perform final grammar and style checks")
                suggestions.append("Ensure word count requirements are met")
            
            # Error-specific suggestions
            if errors:
                suggestions.append("Address any errors before proceeding")
                
            # Constraint-based suggestions
            constraints = self._extract_constraints_from_profile()
            if constraints.deadlines:
                urgent_deadlines = [
                    college for college, deadline in constraints.deadlines.items()
                    if (deadline - datetime.now()).days <= 7
                ]
                if urgent_deadlines:
                    suggestions.append(f"Prioritize essays for urgent deadlines: {', '.join(urgent_deadlines)}")
                    
            return suggestions[:5]  # Limit to top 5 suggestions
            
        except Exception as e:
            debug_print(True, f"Error generating next steps: {e}")
            return ["Continue with your current essay workflow"]
    
    def handle_deadline_pressure(self, constraints: PlanningConstraints) -> EssayPlan:
        """Create time-optimized plan when deadlines are tight"""
        
        debug_print(True, "Creating deadline-optimized plan")
        
        # Find most urgent deadline
        now = datetime.now()
        urgent_essays = [
            (college, deadline) for college, deadline in constraints.deadlines.items()
            if (deadline - now).days <= 3
        ]
        
        if not urgent_essays:
            # No urgent deadlines, use normal planning
            return self.create_conversational_plan(
                "Create an efficient essay plan", 
                PlanningContext.WORKFLOW
            )
        
        # Sort by urgency
        urgent_essays.sort(key=lambda x: x[1])
        most_urgent = urgent_essays[0]
        
        # Create time-pressured request
        time_pressure_request = f"I need to complete my essay for {most_urgent[0]} by {most_urgent[1].strftime('%Y-%m-%d')}. Focus on efficiency and core requirements."
        
        # Create plan with time pressure context
        time_pressure_context = {
            "time_pressure": True,
            "urgent_deadline": most_urgent[1].isoformat(),
            "target_college": most_urgent[0],
            "optimization_mode": "speed"
        }
        
        plan = self.create_conversational_plan(
            time_pressure_request,
            PlanningContext.CONSTRAINT_DRIVEN,
            time_pressure_context
        )
        
        # Add time pressure metadata
        plan.metadata.update({
            "time_pressure_mode": True,
            "urgent_deadline": most_urgent[1].isoformat(),
            "target_college": most_urgent[0]
        })
        
        return plan
    
    # Private helper methods
    
    def _process_user_request(self, user_request: str) -> str:
        """Process user request through query rewriter"""
        try:
            return self.query_rewriter.rewrite_query(user_request)
        except Exception as e:
            debug_print(True, f"Query rewriter failed: {e}")
            return user_request
    
    def _extract_constraints_from_profile(self) -> PlanningConstraints:
        """Extract planning constraints from user profile"""
        constraints = PlanningConstraints()
        
        try:
            # Extract basic info
            if hasattr(self.profile, 'user_info'):
                constraints.college_preferences = getattr(self.profile.user_info, 'college_list', [])
            
            # Extract story information
            if hasattr(self.profile, 'defining_moments'):
                constraints.available_stories = [
                    moment.title for moment in self.profile.defining_moments
                ]
                
                # Track used stories
                for moment in self.profile.defining_moments:
                    if hasattr(moment, 'used_in_essays') and moment.used_in_essays:
                        for essay in moment.used_in_essays:
                            if essay not in constraints.used_stories:
                                constraints.used_stories[essay] = []
                            constraints.used_stories[essay].append(moment.title)
            
            # Default word count targets (can be overridden)
            constraints.word_count_targets = {
                "common_app": 650,
                "supplemental": 350,
                "uc_essays": 350
            }
            
        except Exception as e:
            debug_print(True, f"Error extracting constraints: {e}")
            
        return constraints
    
    def _build_enhanced_context(self, processed_request: str, context: PlanningContext, 
                               constraints: PlanningConstraints, additional_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build enhanced context for smart planner"""
        
        enhanced_context = {
            "user_id": self.user_id,
            "user_profile": self.profile.model_dump() if hasattr(self.profile, 'model_dump') else {},
            "planning_context": context.value,
            "planning_constraints": constraints.to_dict(),
            "processed_request": processed_request,
            **additional_context
        }
        
        return enhanced_context
    
    def _calculate_feasibility_score(self, plan: EssayPlan, constraints: PlanningConstraints) -> float:
        """Calculate feasibility score based on time and resource constraints"""
        
        # Base feasibility score
        score = 8.0
        
        # Check deadline feasibility
        if constraints.deadlines:
            now = datetime.now()
            for college, deadline in constraints.deadlines.items():
                days_remaining = (deadline - now).days
                if days_remaining <= 1:
                    score -= 3.0  # Very tight deadline
                elif days_remaining <= 3:
                    score -= 1.5  # Tight deadline
                elif days_remaining <= 7:
                    score -= 0.5  # Moderately tight
        
        # Check workload feasibility
        if constraints.current_workload > 5:
            score -= 2.0  # High workload
        elif constraints.current_workload > 3:
            score -= 1.0  # Moderate workload
        
        # Check story availability
        if not constraints.available_stories:
            score -= 2.0  # No stories available
        
        return max(0.0, min(10.0, score))
    
    def _calculate_efficiency_score(self, plan: EssayPlan) -> float:
        """Calculate efficiency score based on plan structure"""
        
        # Base efficiency score
        score = 8.0
        
        # Check if plan has clear next action
        if not plan.data.get("next_tool"):
            score -= 2.0
        
        # Check if plan has appropriate args
        if not plan.data.get("args"):
            score -= 1.0
        
        # Check for errors in plan
        if plan.errors:
            score -= 1.0 * len(plan.errors)
        
        return max(0.0, min(10.0, score))
    
    def _calculate_constraint_satisfaction(self, plan: EssayPlan, constraints: PlanningConstraints) -> float:
        """Calculate constraint satisfaction score"""
        
        # Base constraint satisfaction score
        score = 8.0
        
        # Check word count consideration
        if constraints.word_count_targets and "word_count" not in str(plan.data):
            score -= 1.0
        
        # Check college preference consideration
        if constraints.college_preferences and "college" not in str(plan.data):
            score -= 0.5
        
        return max(0.0, min(10.0, score))
    
    def _calculate_story_diversity_score(self, plan: EssayPlan, constraints: PlanningConstraints) -> float:
        """Calculate story diversity score"""
        
        # Base story diversity score
        score = 8.0
        
        # Check for story reuse issues
        if constraints.used_stories:
            # This is a simplified check - in reality we'd need to analyze the plan more deeply
            total_used = sum(len(stories) for stories in constraints.used_stories.values())
            if total_used > len(constraints.available_stories):
                score -= 2.0  # Likely reuse issues
        
        return max(0.0, min(10.0, score))
    
    def _generate_improvement_suggestions(self, plan: EssayPlan, constraints: PlanningConstraints,
                                        feasibility: float, efficiency: float, 
                                        constraint_satisfaction: float, story_diversity: float) -> List[str]:
        """Generate improvement suggestions based on quality scores"""
        
        suggestions = []
        
        if feasibility < 7.0:
            suggestions.append("Consider extending deadlines or simplifying approach")
        
        if efficiency < 7.0:
            suggestions.append("Streamline workflow by focusing on essential steps")
        
        if constraint_satisfaction < 7.0:
            suggestions.append("Better incorporate user constraints and preferences")
        
        if story_diversity < 7.0:
            suggestions.append("Ensure story diversity across essays to avoid repetition")
        
        if not suggestions:
            suggestions.append("Plan quality is good - proceed with execution")
        
        return suggestions
    
    def _analyze_constraint_changes(self, old_constraints: PlanningConstraints, 
                                  new_constraints: PlanningConstraints) -> Dict[str, Any]:
        """Analyze what changed between constraint sets"""
        
        changes = {}
        
        # Check deadline changes
        if old_constraints.deadlines != new_constraints.deadlines:
            changes["deadlines"] = {
                "old": old_constraints.deadlines,
                "new": new_constraints.deadlines
            }
        
        # Check word count changes
        if old_constraints.word_count_targets != new_constraints.word_count_targets:
            changes["word_count_targets"] = {
                "old": old_constraints.word_count_targets,
                "new": new_constraints.word_count_targets
            }
        
        # Check workload changes
        if old_constraints.current_workload != new_constraints.current_workload:
            changes["workload"] = {
                "old": old_constraints.current_workload,
                "new": new_constraints.current_workload
            }
        
        return changes
    
    def _update_profile_with_constraints(self, new_constraints: PlanningConstraints):
        """Update user profile with new constraints if applicable"""
        # This is a placeholder - in reality we'd update the profile storage
        pass
    
    def _generate_replan_request(self, constraint_changes: Dict[str, Any]) -> str:
        """Generate user request for re-planning based on changes"""
        
        if "deadlines" in constraint_changes:
            return "My deadlines have changed - please adjust my essay plan accordingly"
        elif "word_count_targets" in constraint_changes:
            return "My word count requirements have changed - please update my plan"
        elif "workload" in constraint_changes:
            return "My workload has changed - please adjust my essay timeline"
        else:
            return "My constraints have changed - please update my essay plan" 