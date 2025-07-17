"""Intelligent LLM-driven response generation with context awareness and deduplication.

This module provides sophisticated response generation capabilities that integrate
user context, prevent response duplication, and create personalized, engaging
responses based on conversation history and user details.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
import difflib

from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.response_parser import safe_parse

logger = logging.getLogger(__name__)


@dataclass
class ResponseContext:
    """Context information for response generation."""
    user_input: str
    tool_result: Any
    conversation_history: List[Dict]
    user_profile: Dict
    previous_responses: List[str]
    school_context: Optional[Dict] = None
    user_interests: List[str] = None
    specific_details: List[str] = None


class IntelligentResponseGenerator:
    """LLM-powered response generation with context awareness and deduplication.
    
    This class eliminates identical responses (Bug #1) and integrates user-provided
    details (Bug #3) by using sophisticated LLM-driven response generation that
    considers conversation history, user context, and response uniqueness.
    """
    
    def __init__(self):
        """Initialize the response generator."""
        self.llm = get_chat_llm()
        self.response_cache = []
        self.similarity_threshold = 0.85
        
        # Response templates for different scenarios
        self.templates = {
            'tool_success': self._get_tool_success_template(),
            'user_detail_integration': self._get_user_detail_template(),
            'conversation_continuation': self._get_conversation_template(),
            'alternative_response': self._get_alternative_template()
        }
        
    async def generate_contextual_response(
        self,
        user_input: str,
        tool_result: Any,
        conversation_history: List[Dict],
        user_profile: Dict,
        previous_responses: List[str],
        school_context: Optional[Dict] = None
    ) -> str:
        """Generate unique, contextual responses that integrate user details.
        
        Args:
            user_input: Current user input
            tool_result: Result from tool execution
            conversation_history: Previous conversation turns
            user_profile: User profile information
            previous_responses: Recent agent responses for deduplication
            school_context: School-specific context if available
            
        Returns:
            Unique, contextually appropriate response
        """
        try:
            # Build response context
            context = ResponseContext(
                user_input=user_input,
                tool_result=tool_result,
                conversation_history=conversation_history,
                user_profile=user_profile,
                previous_responses=previous_responses,
                school_context=school_context,
                user_interests=self._extract_user_interests(user_input, user_profile),
                specific_details=self._extract_specific_details(user_input)
            )
            
            # Generate initial response
            response = await self._generate_initial_response(context)
            
            # Check for duplication and regenerate if needed
            if await self._is_duplicate_response(response, previous_responses):
                logger.info("Duplicate response detected, generating alternative")
                response = await self._generate_alternative_response(context)
            
            # Integrate user-specific details
            response = await self._integrate_user_details(response, context)
            
            # Add school context if relevant
            if school_context:
                response = await self._add_school_context(response, context)
            
            # Cache response for future deduplication
            self._cache_response(response)
            
            logger.info("Generated contextual response with user integration")
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._generate_fallback_response(user_input, tool_result)
    
    async def _generate_initial_response(self, context: ResponseContext) -> str:
        """Generate initial response based on context."""
        
        # Determine response type based on tool result
        if context.tool_result and hasattr(context.tool_result, '__iter__'):
            response_type = 'tool_success'
        elif context.specific_details:
            response_type = 'user_detail_integration'
        else:
            response_type = 'conversation_continuation'
        
        template = self.templates[response_type]
        
        # Build context-aware prompt
        generation_prompt = template.format(
            user_input=context.user_input,
            tool_result=self._format_tool_result(context.tool_result),
            user_profile=self._format_user_profile(context.user_profile),
            conversation_summary=self._summarize_conversation(context.conversation_history),
            user_interests=", ".join(context.user_interests) if context.user_interests else "General essay assistance",
            specific_details=", ".join(context.specific_details) if context.specific_details else "None provided"
        )
        
        # Generate response with LLM
        response = call_llm(self.llm, generation_prompt, temperature=0.7, max_tokens=800)
        
        return response.strip()
    
    async def _is_duplicate_response(self, response: str, previous_responses: List[str]) -> bool:
        """Check if response is too similar to previous responses."""
        
        if not previous_responses:
            return False
            
        # Check last 3 responses for similarity
        for prev_response in previous_responses[-3:]:
            similarity = self._calculate_similarity(response, prev_response)
            
            if similarity > self.similarity_threshold:
                logger.debug(f"High similarity detected: {similarity:.2f}")
                return True
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        
        # Simple similarity based on shared words and structure
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity for word overlap
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        jaccard = intersection / union if union > 0 else 0.0
        
        # Sequence similarity for structure
        sequence_sim = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        # Combined similarity (weighted toward sequence for detecting identical responses)
        combined_similarity = 0.3 * jaccard + 0.7 * sequence_sim
        
        return combined_similarity
    
    async def _generate_alternative_response(self, context: ResponseContext) -> str:
        """Generate alternative response when duplication is detected."""
        
        template = self.templates['alternative_response']
        
        alternative_prompt = template.format(
            user_input=context.user_input,
            tool_result=self._format_tool_result(context.tool_result),
            previous_responses="\n---\n".join(context.previous_responses[-2:]),
            user_details=self._format_user_details(context),
            conversation_context=self._get_conversation_context(context.conversation_history)
        )
        
        response = call_llm(self.llm, alternative_prompt, temperature=0.8, max_tokens=800)
        
        return response.strip()
    
    async def _integrate_user_details(self, response: str, context: ResponseContext) -> str:
        """Integrate user-specific details into the response."""
        
        if not context.specific_details:
            return response
        
        integration_prompt = f"""
        Enhance this response to naturally incorporate the user's specific details:
        
        ORIGINAL RESPONSE: {response}
        
        USER DETAILS TO INTEGRATE:
        {', '.join(context.specific_details)}
        
        USER INTERESTS: {', '.join(context.user_interests) if context.user_interests else 'General'}
        
        Requirements:
        1. Naturally weave in user details where relevant
        2. Don't force connections that don't make sense
        3. Maintain the helpful, supportive tone
        4. Keep the core message and functionality
        5. Make it feel personalized and relevant
        
        Return the enhanced response:
        """
        
        enhanced_response = call_llm(self.llm, integration_prompt, temperature=0.6, max_tokens=1000)
        
        return enhanced_response.strip()
    
    async def _add_school_context(self, response: str, context: ResponseContext) -> str:
        """Add school-specific context to the response."""
        
        if not context.school_context:
            return response
        
        school_name = context.school_context.get('name', 'your target school')
        
        school_enhancement_prompt = f"""
        Subtly enhance this response with relevant {school_name} context:
        
        ORIGINAL RESPONSE: {response}
        
        SCHOOL CONTEXT: {context.school_context}
        
        USER INTERESTS: {', '.join(context.user_interests) if context.user_interests else 'General'}
        
        Add natural, relevant {school_name} references only where they make sense.
        Don't force it - keep the enhancement subtle and helpful.
        
        Enhanced response:
        """
        
        enhanced_response = call_llm(self.llm, school_enhancement_prompt, temperature=0.5, max_tokens=1000)
        
        return enhanced_response.strip()
    
    def _extract_user_interests(self, user_input: str, user_profile: Dict) -> List[str]:
        """Extract user interests from input and profile."""
        
        interests = []
        
        # Extract from user input
        input_lower = user_input.lower()
        interest_keywords = {
            'technology': ['tech', 'robotics', 'programming', 'coding', 'engineering', 'innovation'],
            'service': ['helping', 'service', 'volunteer', 'community', 'disabled', 'support'],
            'leadership': ['lead', 'captain', 'president', 'organize', 'manage'],
            'arts': ['music', 'art', 'creative', 'design', 'writing'],
            'stem': ['science', 'math', 'research', 'experiment', 'analysis']
        }
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                interests.append(interest)
        
        # Extract from user profile
        profile_interests = user_profile.get('interests', [])
        if isinstance(profile_interests, list):
            interests.extend(profile_interests)
        
        return list(set(interests))
    
    def _extract_specific_details(self, user_input: str) -> List[str]:
        """Extract specific details mentioned by the user."""
        
        details = []
        input_lower = user_input.lower()
        
        # Common specific detail patterns
        detail_patterns = [
            'robotics project', 'disabled students', 'vietnam', 'mit',
            'family immigrated', 'volunteer work', 'research project',
            'startup', 'nonprofit', 'internship', 'competition'
        ]
        
        for pattern in detail_patterns:
            if pattern in input_lower:
                details.append(pattern)
        
        # Extract quoted or emphasized content
        import re
        quoted_content = re.findall(r'"([^"]*)"', user_input)
        details.extend(quoted_content)
        
        return details
    
    def _format_tool_result(self, tool_result: Any) -> str:
        """Format tool result for prompt inclusion."""
        
        if not tool_result:
            return "No specific tool result available"
        
        # Handle different tool result types
        if isinstance(tool_result, dict):
            if 'stories' in tool_result:
                # Brainstorm tool result
                stories = tool_result.get('stories', [])
                if stories and len(stories) > 0:
                    story_summaries = []
                    for story in stories[:3]:  # Limit to 3 stories
                        title = story.get('title', 'Untitled')
                        description = story.get('description', 'No description')[:100]
                        story_summaries.append(f"- {title}: {description}")
                    return "Brainstormed stories:\n" + "\n".join(story_summaries)
            
            elif 'essay_draft' in tool_result:
                # Draft tool result
                draft = tool_result.get('essay_draft', '')
                word_count = tool_result.get('word_count', 0)
                return f"Essay draft generated ({word_count} words): {draft[:200]}..."
            
            else:
                # Generic dict result
                return str(tool_result)[:300]
        
        elif isinstance(tool_result, str):
            return tool_result[:300]
        
        else:
            return str(tool_result)[:300]
    
    def _format_user_profile(self, user_profile: Dict) -> str:
        """Format user profile for prompt inclusion."""
        
        if not user_profile:
            return "No user profile available"
        
        profile_parts = []
        
        for key in ['name', 'interests', 'experiences', 'goals', 'background']:
            if key in user_profile and user_profile[key]:
                value = user_profile[key]
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                profile_parts.append(f"{key.title()}: {value}")
        
        return '\n'.join(profile_parts) if profile_parts else "Basic user profile"
    
    def _summarize_conversation(self, conversation_history: List[Dict]) -> str:
        """Create a brief summary of conversation history."""
        
        if not conversation_history:
            return "No previous conversation"
        
        recent_turns = conversation_history[-3:]  # Last 3 turns
        summary_parts = []
        
        for turn in recent_turns:
            user_msg = turn.get('user_input', turn.get('user', ''))[:50]
            agent_msg = turn.get('agent_response', turn.get('agent', ''))[:50]
            summary_parts.append(f"User: {user_msg}... Agent: {agent_msg}...")
        
        return '\n'.join(summary_parts)
    
    def _format_user_details(self, context: ResponseContext) -> str:
        """Format user details for prompts."""
        
        details = []
        
        if context.specific_details:
            details.append(f"Specific mentions: {', '.join(context.specific_details)}")
        
        if context.user_interests:
            details.append(f"Interests: {', '.join(context.user_interests)}")
        
        return '\n'.join(details) if details else "No specific details"
    
    def _get_conversation_context(self, conversation_history: List[Dict]) -> str:
        """Get relevant conversation context."""
        
        if not conversation_history:
            return "New conversation"
        
        # Look for patterns in conversation
        tool_usage = []
        user_mentions = []
        
        for turn in conversation_history:
            tools = turn.get('tools_used', [])
            if tools:
                tool_usage.extend(tools)
            
            user_input = turn.get('user_input', '')
            if 'robotics' in user_input.lower():
                user_mentions.append('robotics')
            if 'disabled' in user_input.lower():
                user_mentions.append('accessibility')
        
        context_parts = []
        if tool_usage:
            context_parts.append(f"Tools used: {', '.join(set(tool_usage))}")
        if user_mentions:
            context_parts.append(f"User focuses: {', '.join(set(user_mentions))}")
        
        return '; '.join(context_parts) if context_parts else "General conversation"
    
    def _cache_response(self, response: str) -> None:
        """Cache response for future deduplication checking."""
        
        self.response_cache.append(response)
        
        # Keep cache size manageable
        if len(self.response_cache) > 10:
            self.response_cache = self.response_cache[-5:]
    
    def _generate_fallback_response(self, user_input: str, tool_result: Any) -> str:
        """Generate safe fallback response when main generation fails."""
        
        if tool_result:
            return f"✅ I've completed your request. Based on your input about {user_input[:50]}..., here's what I found: {str(tool_result)[:200]}... What would you like to work on next?"
        else:
            return f"I understand you're asking about {user_input[:50]}... Let me help you with your essay writing. What specific aspect would you like to focus on?"
    
    # Template methods
    def _get_tool_success_template(self) -> str:
        return """
        You are an expert essay writing assistant. Generate a helpful, engaging response based on this tool execution:
        
        USER REQUEST: "{user_input}"
        TOOL RESULT: {tool_result}
        USER PROFILE: {user_profile}
        USER INTERESTS: {user_interests}
        SPECIFIC DETAILS: {specific_details}
        
        Create a response that:
        1. Acknowledges what was accomplished
        2. Integrates user-specific interests and details naturally
        3. Explains the results clearly with engaging formatting
        4. Suggests concrete next steps
        5. Maintains an encouraging, supportive tone
        6. Uses emojis and markdown for visual appeal
        
        Make it personalized and relevant to their specific situation:
        """
    
    def _get_user_detail_template(self) -> str:
        return """
        Generate a personalized essay assistance response that specifically integrates the user's details:
        
        USER REQUEST: "{user_input}"
        TOOL RESULT: {tool_result}
        USER INTERESTS: {user_interests}
        SPECIFIC DETAILS: {specific_details}
        USER PROFILE: {user_profile}
        
        Requirements:
        1. Reference their specific details naturally (robotics, disabled students, innovation, etc.)
        2. Connect their interests to essay opportunities
        3. Provide concrete, actionable guidance
        4. Use an encouraging, expert tone
        5. Include specific next steps
        
        Create a helpful response that shows you understand their unique background:
        """
    
    def _get_conversation_template(self) -> str:
        return """
        Continue this essay writing conversation in a helpful, personalized way:
        
        USER REQUEST: "{user_input}"
        CONVERSATION SUMMARY: {conversation_summary}
        USER PROFILE: {user_profile}
        USER INTERESTS: {user_interests}
        
        Provide guidance that:
        1. Builds on the conversation history
        2. Addresses their specific request
        3. Offers concrete essay writing help
        4. Maintains continuity and progress
        5. Shows understanding of their goals
        
        Response:
        """
    
    def _get_alternative_template(self) -> str:
        return """
        Generate a fresh, alternative response that avoids repeating previous responses:
        
        USER REQUEST: "{user_input}"
        TOOL RESULT: {tool_result}
        USER DETAILS: {user_details}
        CONVERSATION CONTEXT: {conversation_context}
        
        PREVIOUS RESPONSES TO AVOID:
        {previous_responses}
        
        Create a NEW response that:
        1. Uses completely different language and structure
        2. Approaches the same topic from a fresh angle
        3. Integrates user details in a new way
        4. Provides different but equally helpful guidance
        5. Maintains quality and usefulness
        
        Alternative response:
        """


# Global instance for easy import
response_generator = IntelligentResponseGenerator() 