"""Conversation Quality Evaluator for Essay Agent Memory Integration Testing.

This module provides comprehensive conversation quality assessment including:
- Response completeness detection (missing AI responses)
- Profile utilization evaluation
- Memory integration testing
- Tool diversity analysis
- Real-time bug detection during evaluations
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path

from .conversation_runner import ConversationResult, ConversationTurn
from .real_profiles import UserProfile
from .conversational_scenarios import ConversationScenario
from ..agent.core.react_agent import EssayReActAgent

logger = logging.getLogger(__name__)


class ConversationQualityEvaluator:
    """Comprehensive conversation quality evaluation and bug detection."""
    
    def __init__(self):
        """Initialize conversation quality evaluator."""
        self.logger = logging.getLogger(__name__)
    
    def evaluate_conversation_completeness(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Check for missing responses, response quality, logical flow.
        
        Args:
            conversation_history: List of conversation turns with type and content
            
        Returns:
            Dictionary with completeness metrics and detected issues
        """
        user_messages = [msg for msg in conversation_history if msg.get('type') == 'human']
        ai_messages = [msg for msg in conversation_history if msg.get('type') == 'ai']
        
        # Calculate response coverage
        expected_responses = len(user_messages)
        actual_responses = len(ai_messages)
        response_coverage = actual_responses / expected_responses if expected_responses > 0 else 0
        
        # Calculate average response length
        avg_response_length = 0
        if ai_messages:
            total_length = sum(len(msg.get('content', '')) for msg in ai_messages)
            avg_response_length = total_length / len(ai_messages)
        
        # Extract tools used
        tools_used = set()
        for msg in ai_messages:
            tool_calls = msg.get('tool_calls', [])
            for tool_call in tool_calls:
                if isinstance(tool_call, dict) and 'function' in tool_call:
                    tools_used.add(tool_call['function'].get('name', 'unknown'))
        
        # Evaluate conversation coherence
        coherence_score = self._evaluate_logical_flow(conversation_history)
        
        return {
            'response_coverage': response_coverage,
            'missing_responses': expected_responses - actual_responses,
            'expected_responses': expected_responses,
            'actual_responses': actual_responses,
            'avg_response_length': avg_response_length,
            'tool_diversity': len(tools_used),
            'tools_used': list(tools_used),
            'conversation_coherence': coherence_score,
            'critical_issues': self._detect_critical_issues(conversation_history, response_coverage)
        }
    
    def evaluate_profile_utilization(self, conversation_history: List[Dict], user_profile: Dict) -> Dict[str, Any]:
        """Check if agent properly uses user background information.
        
        Args:
            conversation_history: List of conversation turns
            user_profile: User profile data
            
        Returns:
            Dictionary with profile utilization metrics
        """
        profile_keywords = self._extract_profile_keywords(user_profile)
        ai_responses = [msg.get('content', '') for msg in conversation_history if msg.get('type') == 'ai']
        
        # Count profile references
        profile_references = 0
        for response in ai_responses:
            response_lower = response.lower()
            for keyword in profile_keywords:
                if keyword.lower() in response_lower:
                    profile_references += 1
                    break  # Count only once per response
        
        # Calculate personalization score
        total_responses = len(ai_responses)
        personalization_score = profile_references / total_responses if total_responses > 0 else 0
        
        # Evaluate context awareness
        context_awareness = self._evaluate_context_usage(conversation_history, user_profile)
        
        return {
            'profile_references': profile_references,
            'total_responses': total_responses,
            'personalization_score': personalization_score,
            'context_awareness': context_awareness,
            'profile_keywords_found': self._find_profile_keywords_in_responses(ai_responses, profile_keywords),
            'generic_response_count': self._count_generic_responses(ai_responses)
        }
    
    def test_memory_integration(self, user_id: str, test_message: str = "Can you remind me what we discussed about my essay?") -> Dict[str, Any]:
        """Test if manual chat can access evaluation conversation history.
        
        Args:
            user_id: User ID to test (should be evaluation user ID)
            test_message: Test message to send to manual chat
            
        Returns:
            Dictionary with memory integration test results
        """
        try:
            # Create agent instance for manual chat mode
            agent = EssayReActAgent(user_id=user_id)
            
            # Check if agent has access to conversation history
            if hasattr(agent, 'memory') and agent.memory:
                # Get recent conversation history
                recent_history = agent.memory.get_recent_history(5)
                
                if recent_history:
                    return {
                        'memory_integration_success': True,
                        'conversation_turns_found': len(recent_history),
                        'memory_content_preview': str(recent_history)[:200] + "..." if len(str(recent_history)) > 200 else str(recent_history),
                        'test_status': 'pass'
                    }
                else:
                    return {
                        'memory_integration_success': False,
                        'conversation_turns_found': 0,
                        'error': 'No conversation history found in memory',
                        'test_status': 'fail'
                    }
            else:
                return {
                    'memory_integration_success': False,
                    'error': 'Agent memory system not available',
                    'test_status': 'fail'
                }
                
        except Exception as e:
            self.logger.error(f"Memory integration test failed: {e}")
            return {
                'memory_integration_success': False,
                'error': str(e),
                'test_status': 'error'
            }
    
    def generate_evaluation_report(self, 
                                  completeness_results: Dict[str, Any],
                                  profile_results: Dict[str, Any], 
                                  memory_results: Dict[str, Any]) -> str:
        """Generate detailed evaluation report with bug detection.
        
        Args:
            completeness_results: Results from conversation completeness evaluation
            profile_results: Results from profile utilization evaluation  
            memory_results: Results from memory integration test
            
        Returns:
            Formatted evaluation report string
        """
        memory_integration_status = "✅ PASS" if memory_results.get('memory_integration_success', False) else "❌ FAIL"
        
        critical_issues = []
        critical_issues.extend(completeness_results.get('critical_issues', []))
        
        if profile_results.get('personalization_score', 0) < 0.3:
            critical_issues.append("Low profile utilization - agent not using user background")
            
        if not memory_results.get('memory_integration_success', False):
            critical_issues.append("Memory integration broken - manual chat cannot access evaluation history")
        
        report = f"""
🔍 CONVERSATION QUALITY ANALYSIS
================================
Response Coverage: {completeness_results.get('response_coverage', 0):.2%}
Missing Responses: {completeness_results.get('missing_responses', 0)}/{completeness_results.get('expected_responses', 0)}
Profile Utilization: {profile_results.get('personalization_score', 0):.2%}
Tool Diversity: {completeness_results.get('tool_diversity', 0)} unique tools
Memory Integration: {memory_integration_status}
Conversation Coherence: {completeness_results.get('conversation_coherence', 0):.2f}

🛠️ TOOL USAGE:
{', '.join(completeness_results.get('tools_used', [])) or 'No tools detected'}

🚨 CRITICAL ISSUES DETECTED:
{chr(10).join(f'- {issue}' for issue in critical_issues) if critical_issues else 'None detected'}

📊 DETAILED METRICS:
- Average Response Length: {completeness_results.get('avg_response_length', 0):.0f} characters
- Generic Responses: {profile_results.get('generic_response_count', 0)}
- Profile Keywords Found: {len(profile_results.get('profile_keywords_found', []))}
- Memory Access: {memory_results.get('conversation_turns_found', 0)} turns found

💡 RECOMMENDATIONS:
{self._generate_recommendations(completeness_results, profile_results, memory_results)}
        """
        
        return report.strip()
    
    def _evaluate_logical_flow(self, conversation_history: List[Dict]) -> float:
        """Evaluate logical flow and coherence of conversation."""
        if len(conversation_history) < 2:
            return 1.0
        
        coherence_score = 1.0
        
        # Check for abrupt topic changes
        # Check for repeated questions
        # Check for contextual continuity
        
        # Simple heuristic: penalize if responses are too similar
        ai_responses = [msg.get('content', '') for msg in conversation_history if msg.get('type') == 'ai']
        if len(ai_responses) > 1:
            similarity_penalties = 0
            for i in range(1, len(ai_responses)):
                # Simple similarity check
                if ai_responses[i] == ai_responses[i-1]:
                    similarity_penalties += 0.2
            coherence_score = max(0.0, 1.0 - similarity_penalties)
        
        return coherence_score
    
    def _detect_critical_issues(self, conversation_history: List[Dict], response_coverage: float) -> List[str]:
        """Detect critical issues in conversation quality."""
        issues = []
        
        # Missing responses issue
        if response_coverage < 0.5:
            issues.append(f"CRITICAL: Missing {(1-response_coverage)*100:.0f}% of expected AI responses")
        elif response_coverage < 0.8:
            issues.append(f"WARNING: Missing {(1-response_coverage)*100:.0f}% of expected AI responses")
        
        # Short response issue
        ai_messages = [msg for msg in conversation_history if msg.get('type') == 'ai']
        short_responses = sum(1 for msg in ai_messages if len(msg.get('content', '')) < 50)
        if short_responses > 0:
            issues.append(f"WARNING: {short_responses} extremely short AI responses (<50 chars)")
        
        # Error detection
        for msg in ai_messages:
            content = msg.get('content', '').lower()
            if 'error' in content or 'failed' in content or 'apologize' in content:
                issues.append("ERROR: Agent response contains error or failure message")
                break
        
        return issues
    
    def _extract_profile_keywords(self, user_profile: Dict) -> List[str]:
        """Extract keywords from user profile for reference detection."""
        keywords = []
        
        # Extract from various profile fields
        if isinstance(user_profile, dict):
            # Basic info
            keywords.extend([
                user_profile.get('name', ''),
                user_profile.get('intended_major', ''),
                user_profile.get('school_type', '')
            ])
            
            # Core values
            core_values = user_profile.get('core_values', [])
            for value in core_values:
                if isinstance(value, dict):
                    keywords.append(value.get('value', ''))
                elif isinstance(value, str):
                    keywords.append(value)
            
            # Activities
            activities = user_profile.get('activities', [])
            for activity in activities:
                if isinstance(activity, dict):
                    keywords.extend([
                        activity.get('name', ''),
                        activity.get('role', '')
                    ])
            
            # Academic interests
            academic_interests = user_profile.get('academic_interests', [])
            keywords.extend(academic_interests)
        
        # Filter out empty strings and short words
        return [kw.strip() for kw in keywords if kw and len(kw.strip()) > 2]
    
    def _find_profile_keywords_in_responses(self, ai_responses: List[str], profile_keywords: List[str]) -> List[str]:
        """Find which profile keywords appear in AI responses."""
        found_keywords = []
        
        for response in ai_responses:
            response_lower = response.lower()
            for keyword in profile_keywords:
                if keyword.lower() in response_lower and keyword not in found_keywords:
                    found_keywords.append(keyword)
        
        return found_keywords
    
    def _count_generic_responses(self, ai_responses: List[str]) -> int:
        """Count generic responses that don't seem personalized."""
        generic_patterns = [
            r"i'd be happy to help",
            r"let's work together",
            r"here are some ideas",
            r"let me help you",
            r"i'm here to assist"
        ]
        
        generic_count = 0
        for response in ai_responses:
            response_lower = response.lower()
            for pattern in generic_patterns:
                if re.search(pattern, response_lower):
                    generic_count += 1
                    break  # Count once per response
        
        return generic_count
    
    def _evaluate_context_usage(self, conversation_history: List[Dict], user_profile: Dict) -> float:
        """Evaluate how well the agent uses conversation and profile context."""
        # Simple heuristic: check if agent references previous conversation
        ai_responses = [msg.get('content', '') for msg in conversation_history if msg.get('type') == 'ai']
        
        context_indicators = [
            "as we discussed",
            "building on our",
            "based on your",
            "you mentioned",
            "from your profile",
            "your background",
            "as you said"
        ]
        
        context_usage_count = 0
        for response in ai_responses:
            response_lower = response.lower()
            for indicator in context_indicators:
                if indicator in response_lower:
                    context_usage_count += 1
                    break
        
        return context_usage_count / len(ai_responses) if ai_responses else 0.0
    
    def _generate_recommendations(self, 
                                completeness_results: Dict[str, Any],
                                profile_results: Dict[str, Any],
                                memory_results: Dict[str, Any]) -> str:
        """Generate recommendations based on evaluation results."""
        recommendations = []
        
        # Response completeness recommendations
        if completeness_results.get('response_coverage', 1) < 0.9:
            recommendations.append("Fix conversation recording system to ensure all AI responses are saved")
        
        # Profile utilization recommendations  
        if profile_results.get('personalization_score', 1) < 0.5:
            recommendations.append("Improve profile data loading and context injection in agent prompts")
        
        # Tool diversity recommendations
        if completeness_results.get('tool_diversity', 0) < 2:
            recommendations.append("Enhance tool selection logic to use diverse, context-appropriate tools")
        
        # Memory integration recommendations
        if not memory_results.get('memory_integration_success', True):
            recommendations.append("Fix memory integration between evaluation and manual chat modes")
        
        if not recommendations:
            recommendations.append("No critical issues detected - system functioning well")
        
        return '\n'.join(f'- {rec}' for rec in recommendations)


def extract_tools_used(ai_messages: List[Dict]) -> List[str]:
    """Extract list of tools used from AI messages."""
    tools = []
    
    for msg in ai_messages:
        tool_calls = msg.get('tool_calls', [])
        for tool_call in tool_calls:
            if isinstance(tool_call, dict) and 'function' in tool_call:
                tool_name = tool_call['function'].get('name')
                if tool_name:
                    tools.append(tool_name)
    
    return tools


def analyze_conversation_file(file_path: str) -> Dict[str, Any]:
    """Analyze a conversation file for quality issues.
    
    Args:
        file_path: Path to conversation JSON file
        
    Returns:
        Analysis results dictionary
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        conversation_history = data.get('chat_history', [])
        
        evaluator = ConversationQualityEvaluator()
        completeness_results = evaluator.evaluate_conversation_completeness(conversation_history)
        
        return {
            'file_path': file_path,
            'conversation_turns': len(conversation_history),
            'analysis_results': completeness_results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing conversation file {file_path}: {e}")
        return {
            'file_path': file_path,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        } 