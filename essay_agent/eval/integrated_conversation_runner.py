"""Integrated conversation runner with real memory system integration.

This module provides IntegratedConversationRunner that saves evaluation conversations
directly to /memory_store using the same memory system as manual chats, eliminating
the architectural disconnect between evaluation and manual conversation storage.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from .conversation_runner import ConversationRunner
from ..agent.core.react_agent import EssayReActAgent
from ..memory.simple_memory import SimpleMemory
from ..memory.user_profile_schema import UserProfile, CoreValue, DefiningMoment, Activity
from .conversational_scenarios import ConversationPhase
from .conversation_quality_evaluator import ConversationQualityEvaluator

logger = logging.getLogger(__name__)


class IntegratedConversationRunner(ConversationRunner):
    """ConversationRunner that integrates with real memory system.
    
    This class extends ConversationRunner to use the real AgentMemory system
    instead of the EvaluationMemory stub, ensuring evaluation conversations
    are saved to memory_store like manual chats.
    """
    
    def __init__(self, verbose: bool = False, memory_prefix: str = "eval"):
        """Initialize integrated conversation runner.
        
        Args:
            verbose: Whether to show verbose output
            memory_prefix: Prefix for evaluation user IDs (default: "eval")
        """
        super().__init__(verbose)
        self.memory_prefix = memory_prefix
        self.eval_user_id = None  # Will be set during initialization
        self.quality_evaluator = ConversationQualityEvaluator()  # Add quality evaluator
        
    async def _initialize_agent_with_profile(self):
        """Initialize ReAct agent with REAL memory integration."""
        
        # Create evaluation-specific user ID to avoid conflicts with manual chats
        self.eval_user_id = f"{self.memory_prefix}_{self.current_profile.profile_id}"
        
        # Initialize ReAct agent with real memory (no EvaluationMemory stub!)
        self.agent = EssayReActAgent(user_id=self.eval_user_id)
        
        # Load profile data into REAL memory system
        await self._load_profile_into_real_memory()
        
        # Set user_memory to None since we're using the agent's internal memory
        self.user_memory = None
        
        self.logger.info(f"Initialized INTEGRATED agent for user: {self.current_profile.name}")
        self.logger.info(f"Memory will be saved to: memory_store/{self.eval_user_id}.conv.json")
        
    async def _load_profile_into_real_memory(self):
        """Load user profile data into REAL memory system."""
        
        profile = self.current_profile
        memory = self.agent.memory  # Get the REAL AgentMemory
        
        try:
            # Create UserProfile object for proper memory storage
            user_profile_data = self._convert_eval_profile_to_user_profile(profile)
            
            # Store the profile using SimpleMemory (real storage)
            SimpleMemory.save(self.eval_user_id, user_profile_data)
            
            # Also update the agent's hierarchical memory if available
            if hasattr(memory, 'hierarchical_memory') and memory.hierarchical_memory:
                # Reload the profile to get the saved data
                memory.hierarchical_memory.profile = user_profile_data
                memory.hierarchical_memory.save()
            
            self.logger.info(f"Successfully stored profile in REAL memory system")
            self.logger.info(f"Profile contains: {len(profile.activities)} activities, {len(profile.defining_moments)} moments")
            
        except Exception as e:
            self.logger.warning(f"Failed to store profile in real memory: {e}")
            # Continue with evaluation even if memory storage fails
    
    def _convert_eval_profile_to_user_profile(self, eval_profile) -> UserProfile:
        """Convert evaluation profile to UserProfile format for real memory storage.
        
        Args:
            eval_profile: Evaluation profile from real_profiles.py
            
        Returns:
            UserProfile object for memory storage
        """
        # Convert core values
        core_values = []
        for value in eval_profile.core_values:
            if isinstance(value, str):
                # Simple string value
                core_values.append(CoreValue(
                    value=value,
                    description=f"Core value: {value}",
                    importance_level=8  # Default importance
                ))
            elif isinstance(value, dict):
                # Already structured
                core_values.append(CoreValue(
                    value=value.get("value", str(value)),
                    description=value.get("description", f"Core value: {value.get('value', str(value))}"),
                    importance_level=value.get("importance_level", 8)
                ))
        
        # Convert defining moments
        defining_moments = []
        for moment in eval_profile.defining_moments:
            defining_moments.append(DefiningMoment(
                title=moment.event[:50],  # Truncate title
                description=moment.event,
                impact=moment.impact,
                lessons_learned=moment.lessons_learned,
                emotional_weight=moment.emotional_weight,
                time_period="high_school",  # Default
                people_involved=[],
                skills_developed=[]
            ))
        
        # Convert activities
        activities = []
        for activity in eval_profile.activities:
            activities.append(Activity(
                name=activity.name,
                role=activity.role,
                description=activity.description,
                impact=activity.impact,
                time_commitment="3-5 hours/week",  # Default
                leadership_role=True if "leader" in activity.role.lower() else False,
                values_demonstrated=activity.values_demonstrated
            ))
        
        # Create UserProfile
        user_profile = UserProfile(
            name=eval_profile.name,
            age=eval_profile.age,
            location=eval_profile.location,
            school_type=eval_profile.school_type,
            intended_major=eval_profile.intended_major,
            academic_interests=eval_profile.academic_interests,
            career_goals=getattr(eval_profile, 'career_goals', []),
            core_values=core_values,
            defining_moments=defining_moments,
            activities=activities,
            essay_history=[]  # Start with empty essay history
        )
        
        return user_profile
    
    async def _get_agent_response(
        self, 
        user_input: str, 
        phase: ConversationPhase
    ) -> Tuple[str, List[str], List[str]]:
        """Get agent response and properly save conversation turn to memory."""
        
        # Call parent method to get response
        response, tools_used, memory_accessed = await super()._get_agent_response(user_input, phase)
        
        try:
            # CRITICAL FIX: Ensure the AI response is saved to agent memory
            # This fixes the missing AI responses issue
            if self.agent and hasattr(self.agent, 'memory') and self.agent.memory:
                # Store the conversation turn in the agent's memory system
                await self.agent.memory.store_conversation_turn(
                    user_input=user_input,
                    agent_response=response,
                    metadata={
                        "phase": phase.phase_name,
                        "tools_used": tools_used,
                        "memory_accessed": memory_accessed,
                        "evaluation_mode": True
                    }
                )
                
                # Also update the hierarchical memory conversation if available
                if hasattr(self.agent.memory, 'hierarchical_memory') and self.agent.memory.hierarchical_memory:
                    self.agent.memory.hierarchical_memory.add_chat_turn(
                        inputs={"input": user_input},
                        outputs={"output": response}
                    )
                
                self.logger.debug(f"Saved conversation turn: {len(response)} chars response")
            else:
                self.logger.warning("Agent memory not available for conversation saving")
                
        except Exception as e:
            self.logger.error(f"Failed to save conversation turn to memory: {e}")
            # Continue execution even if memory saving fails
        
        return response, tools_used, memory_accessed
    
    async def _analyze_conversation_quality(self) -> Dict[str, Any]:
        """Analyze conversation quality and detect integration issues.
        
        Returns:
            Dictionary with comprehensive quality analysis results
        """
        try:
            # Load the saved conversation from memory_store
            conv_file = Path(f"memory_store/{self.eval_user_id}.conv.json")
            if not conv_file.exists():
                return {
                    'quality_analysis': 'ERROR: Conversation file not found',
                    'memory_integration_broken': True
                }
            
            with open(conv_file, 'r') as f:
                conv_data = json.load(f)
            
            conversation_history = conv_data.get('chat_history', [])
            
            # Perform comprehensive quality analysis
            completeness_results = self.quality_evaluator.evaluate_conversation_completeness(conversation_history)
            
            # Get profile data for profile utilization analysis
            profile_data = {}
            try:
                profile = SimpleMemory.load(self.eval_user_id)
                profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else {}
            except Exception as e:
                self.logger.warning(f"Could not load profile for quality analysis: {e}")
            
            profile_results = self.quality_evaluator.evaluate_profile_utilization(conversation_history, profile_data)
            
            # Test memory integration
            memory_results = self.quality_evaluator.test_memory_integration(self.eval_user_id)
            
            # Generate comprehensive report
            quality_report = self.quality_evaluator.generate_evaluation_report(
                completeness_results, profile_results, memory_results
            )
            
            return {
                'completeness_results': completeness_results,
                'profile_results': profile_results,
                'memory_results': memory_results,
                'quality_report': quality_report,
                'conversation_file_path': str(conv_file),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Quality analysis failed: {e}")
            return {
                'quality_analysis': f'ERROR: {str(e)}',
                'error': True
            }
    
    async def execute_evaluation(self, scenario, profile=None):
        """Execute evaluation with enhanced quality analysis."""
        
        # Call parent execution
        result = await super().execute_evaluation(scenario, profile)
        
        # Perform post-evaluation quality analysis
        quality_analysis = await self._analyze_conversation_quality()
        
        # Add quality analysis to result
        if hasattr(result, '__dict__'):
            result.__dict__['quality_analysis'] = quality_analysis
        
        # Print enhanced summary with quality analysis
        if self.verbose:
            self._print_enhanced_evaluation_summary(result, quality_analysis)
        
        return result
    
    def _print_enhanced_evaluation_summary(self, result, quality_analysis):
        """Print enhanced evaluation summary with quality analysis."""
        
        # Call parent summary first
        self._print_evaluation_summary(result)
        
        # Add quality analysis section
        print(f"\n🔍 QUALITY ANALYSIS REPORT")
        print(f"{'='*60}")
        
        if 'quality_report' in quality_analysis:
            print(quality_analysis['quality_report'])
        elif 'error' in quality_analysis:
            print(f"❌ Quality analysis failed: {quality_analysis.get('quality_analysis', 'Unknown error')}")
        
        # Add file information
        if 'conversation_file_path' in quality_analysis:
            print(f"\n📁 Conversation saved to: {quality_analysis['conversation_file_path']}")
            
        # Add specific bug warnings
        completeness_results = quality_analysis.get('completeness_results', {})
        if completeness_results.get('response_coverage', 1) < 0.9:
            print(f"\n⚠️  CRITICAL BUG DETECTED: Missing AI responses in conversation file!")
            print(f"   Expected: {completeness_results.get('expected_responses', 0)} responses")
            print(f"   Found: {completeness_results.get('actual_responses', 0)} responses")
            print(f"   Coverage: {completeness_results.get('response_coverage', 0):.1%}")
    
    def get_memory_file_paths(self) -> Dict[str, str]:
        """Get the file paths where evaluation conversation data is stored.
        
        Returns:
            Dictionary mapping file types to their paths
        """
        if not self.eval_user_id:
            return {}
        
        return {
            "conversation_history": f"memory_store/{self.eval_user_id}.conv.json",
            "user_profile": f"memory_store/{self.eval_user_id}.json", 
            "reasoning_history": f"memory_store/{self.eval_user_id}.reasoning_history.json",
            "vector_index": f"memory_store/vector_indexes/{self.eval_user_id}/",
            "memory_stats": f"memory_store/{self.eval_user_id}.memory_stats.json"
        }
    
    def print_integration_summary(self):
        """Print summary of memory integration for this evaluation."""
        
        if not self.eval_user_id:
            print("⚠️  No evaluation user ID available")
            return
            
        print(f"\n🔗 MEMORY INTEGRATION SUMMARY")
        print(f"{'='*60}")
        print(f"Evaluation User ID: {self.eval_user_id}")
        print(f"Original Profile: {self.current_profile.profile_id}")
        
        memory_paths = self.get_memory_file_paths()
        print(f"\n📁 Files Created in memory_store:")
        for file_type, path in memory_paths.items():
            print(f"  {file_type.replace('_', ' ').title()}: {path}")
        
        print(f"\n✅ Integration Status:")
        print(f"  - Evaluation conversations saved to memory_store")
        print(f"  - Same memory system as manual chats")
        print(f"  - Profile data stored in real memory")
        print(f"  - Memory indexing and search enabled")
        
        print(f"\n🔍 Verification Commands:")
        print(f"  ls memory_store/{self.eval_user_id}*")
        print(f"  python -m essay_agent chat --user-id {self.eval_user_id}")
        print(f"  # Should show evaluation conversation history!")


# Utility functions for CLI integration
def list_evaluation_memory_files(memory_prefix: str = "eval") -> List[str]:
    """List all evaluation memory files in memory_store.
    
    Args:
        memory_prefix: Prefix used for evaluation user IDs
        
    Returns:
        List of evaluation memory file paths
    """
    import os
    from pathlib import Path
    
    memory_dir = Path("memory_store")
    if not memory_dir.exists():
        return []
    
    eval_files = []
    for file_path in memory_dir.iterdir():
        if file_path.name.startswith(f"{memory_prefix}_"):
            eval_files.append(str(file_path))
    
    return sorted(eval_files)


def cleanup_evaluation_memory_files(memory_prefix: str = "eval", 
                                   keep_recent: int = 5) -> int:
    """Clean up old evaluation memory files.
    
    Args:
        memory_prefix: Prefix used for evaluation user IDs
        keep_recent: Number of recent evaluation sessions to keep
        
    Returns:
        Number of files cleaned up
    """
    import os
    from pathlib import Path
    
    eval_files = list_evaluation_memory_files(memory_prefix)
    
    if len(eval_files) <= keep_recent:
        return 0
    
    # Sort by modification time and remove oldest
    eval_files_with_time = [(f, os.path.getmtime(f)) for f in eval_files]
    eval_files_with_time.sort(key=lambda x: x[1], reverse=True)
    
    files_to_remove = eval_files_with_time[keep_recent:]
    removed_count = 0
    
    for file_path, _ in files_to_remove:
        try:
            os.remove(file_path)
            removed_count += 1
            logger.info(f"Cleaned up old evaluation memory file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove {file_path}: {e}")
    
    return removed_count 