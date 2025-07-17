"""User context extraction and integration system.

This module provides sophisticated user detail extraction capabilities that parse
user input for personal experiences, interests, background details, and goals,
then integrate them into the conversation context to create personalized responses.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import re

from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.response_parser import safe_parse

logger = logging.getLogger(__name__)


@dataclass
class ExtractedContext:
    """Container for extracted user context."""
    experiences: List[str]
    interests: List[str]
    background_details: List[str]
    goals: List[str]
    specific_mentions: List[str]
    academic_focus: List[str]
    personal_values: List[str]
    activities: List[str]
    extraction_confidence: float


@dataclass
class ContextUpdate:
    """Update to existing user context."""
    new_experiences: List[str]
    new_interests: List[str]
    new_background: List[str]
    new_goals: List[str]
    updated_profile: Dict[str, Any]
    integration_summary: str


class UserContextExtractor:
    """Extract and integrate user-provided details into conversation context.
    
    This class solves Bug #3 (user input completely ignored) by intelligently
    extracting personal details, experiences, interests, and background information
    from user input and integrating them into the user profile and conversation context.
    """
    
    def __init__(self):
        """Initialize the context extractor."""
        self.llm = get_chat_llm()
        
        # Pattern mappings for quick extraction
        self.experience_patterns = {
            'technology': ['robotics', 'programming', 'coding', 'app', 'website', 'tech', 'engineering'],
            'service': ['volunteer', 'community service', 'helping', 'disabled', 'nonprofit', 'charity'],
            'leadership': ['led', 'captain', 'president', 'organized', 'founded', 'started'],
            'research': ['research', 'study', 'experiment', 'analysis', 'investigation'],
            'arts': ['music', 'art', 'painting', 'writing', 'creative', 'design'],
            'sports': ['team', 'athlete', 'sport', 'competition', 'tournament', 'championship']
        }
        
        self.background_patterns = {
            'cultural': ['family immigrated', 'vietnam', 'heritage', 'culture', 'language', 'tradition'],
            'family': ['family', 'parents', 'siblings', 'grandmother', 'grandfather'],
            'location': ['from', 'moved to', 'grew up in', 'live in', 'hometown'],
            'education': ['school', 'MIT', 'stanford', 'harvard', 'college', 'university'],
            'challenges': ['struggled', 'overcome', 'difficult', 'hardship', 'challenge']
        }
        
        self.academic_patterns = {
            'stem': ['science', 'math', 'engineering', 'computer science', 'biology', 'physics'],
            'humanities': ['english', 'history', 'philosophy', 'literature', 'writing'],
            'social_sciences': ['psychology', 'sociology', 'political science', 'economics'],
            'arts': ['art', 'music', 'theater', 'creative writing', 'design']
        }
    
    async def extract_and_update_context(
        self,
        user_input: str,
        existing_profile: Dict[str, Any],
        conversation_history: List[Dict],
        previous_extractions: Optional[List[ExtractedContext]] = None
    ) -> ContextUpdate:
        """Extract key user details and update profile.
        
        Args:
            user_input: Current user input to analyze
            existing_profile: Existing user profile data
            conversation_history: Previous conversation turns
            previous_extractions: Previously extracted context
            
        Returns:
            Context update with extracted details and updated profile
        """
        try:
            # Quick pattern-based extraction
            quick_extraction = self._quick_pattern_extraction(user_input)
            
            # LLM-powered detailed extraction
            detailed_extraction = await self._llm_extract_context(
                user_input, existing_profile, conversation_history
            )
            
            # Merge and validate extractions
            merged_context = self._merge_extractions(quick_extraction, detailed_extraction)
            
            # Update existing profile
            updated_profile = self._update_user_profile(existing_profile, merged_context)
            
            # Generate integration summary
            integration_summary = self._generate_integration_summary(merged_context, existing_profile)
            
            # Create context update
            context_update = ContextUpdate(
                new_experiences=merged_context.experiences,
                new_interests=merged_context.interests,
                new_background=merged_context.background_details,
                new_goals=merged_context.goals,
                updated_profile=updated_profile,
                integration_summary=integration_summary
            )
            
            logger.info(f"Extracted {len(merged_context.experiences)} experiences, {len(merged_context.interests)} interests")
            return context_update
            
        except Exception as e:
            logger.error(f"Context extraction failed: {e}")
            return self._create_fallback_update(user_input, existing_profile)
    
    def _quick_pattern_extraction(self, user_input: str) -> ExtractedContext:
        """Quick pattern-based extraction for common details."""
        
        input_lower = user_input.lower()
        
        # Extract experiences
        experiences = []
        for category, patterns in self.experience_patterns.items():
            for pattern in patterns:
                if pattern in input_lower:
                    experiences.append(f"{category}: {pattern}")
        
        # Extract background details
        background_details = []
        for category, patterns in self.background_patterns.items():
            for pattern in patterns:
                if pattern in input_lower:
                    background_details.append(f"{category}: {pattern}")
        
        # Extract academic focus
        academic_focus = []
        for category, patterns in self.academic_patterns.items():
            for pattern in patterns:
                if pattern in input_lower:
                    academic_focus.append(category)
        
        # Extract specific mentions (quoted content, proper nouns)
        specific_mentions = []
        
        # Find quoted content
        quoted_matches = re.findall(r'"([^"]*)"', user_input)
        specific_mentions.extend(quoted_matches)
        
        # Find specific projects/activities
        project_patterns = [
            r'(robotics project)', r'(app called \w+)', r'(nonprofit)', 
            r'(startup)', r'(research on \w+)', r'(club)', r'(team)'
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, input_lower)
            specific_mentions.extend(matches)
        
        # Extract interests from context
        interests = []
        interest_indicators = ['passionate about', 'love', 'enjoy', 'interested in', 'care about']
        for indicator in interest_indicators:
            if indicator in input_lower:
                # Try to extract what follows the indicator
                parts = input_lower.split(indicator)
                if len(parts) > 1:
                    following_text = parts[1][:50].strip()
                    interests.append(following_text.split()[0:3])  # First few words
        
        # Flatten interest lists
        flattened_interests = []
        for interest in interests:
            if isinstance(interest, list):
                flattened_interests.extend(interest)
            else:
                flattened_interests.append(interest)
        
        return ExtractedContext(
            experiences=[exp.split(': ', 1)[1] if ': ' in exp else exp for exp in experiences],
            interests=flattened_interests,
            background_details=[bg.split(': ', 1)[1] if ': ' in bg else bg for bg in background_details],
            goals=[],  # Goals typically require more sophisticated extraction
            specific_mentions=specific_mentions,
            academic_focus=academic_focus,
            personal_values=[],  # Values require LLM extraction
            activities=[],  # Activities require LLM extraction
            extraction_confidence=0.6  # Medium confidence for pattern matching
        )
    
    async def _llm_extract_context(
        self,
        user_input: str,
        existing_profile: Dict[str, Any],
        conversation_history: List[Dict]
    ) -> ExtractedContext:
        """Use LLM for sophisticated context extraction."""
        
        # Build extraction prompt
        extraction_prompt = f"""
        Extract important personal details from this user's message about essay writing:
        
        USER INPUT: "{user_input}"
        
        EXISTING PROFILE: {existing_profile}
        
        CONVERSATION CONTEXT:
        {self._format_conversation_context(conversation_history)}
        
        Extract and categorize the following information:
        
        1. EXPERIENCES: Specific activities, projects, jobs, volunteer work
           - Look for: robotics projects, apps, nonprofits, research, internships
           - Example: "robotics project that helped disabled students"
        
        2. INTERESTS: Topics, subjects, activities they care about
           - Look for: technology, helping others, innovation, specific fields
           - Example: "innovation", "accessibility", "STEM education"
        
        3. BACKGROUND: Personal/family background, culture, location
           - Look for: family immigration, cultural heritage, hometown, challenges
           - Example: "family immigrated from Vietnam"
        
        4. GOALS: What they want to achieve, career aspirations
           - Look for: future plans, aspirations, impact they want to make
           - Example: "want to use technology to help people"
        
        5. ACADEMIC FOCUS: Subjects, majors, schools mentioned
           - Look for: specific subjects, schools, academic interests
           - Example: "computer science", "MIT", "engineering"
        
        6. PERSONAL VALUES: What matters to them, principles
           - Look for: values like service, innovation, family, justice
           - Example: "helping others", "making a difference"
        
        7. ACTIVITIES: Clubs, sports, organizations, hobbies
           - Look for: specific activities they participate in
           - Example: "debate team", "volunteer at hospital"
        
        Respond in JSON format:
        {{
            "experiences": ["specific experience 1", "specific experience 2"],
            "interests": ["interest 1", "interest 2"],
            "background_details": ["background detail 1", "background detail 2"],
            "goals": ["goal 1", "goal 2"],
            "specific_mentions": ["specific mention 1", "specific mention 2"],
            "academic_focus": ["subject 1", "subject 2"],
            "personal_values": ["value 1", "value 2"],
            "activities": ["activity 1", "activity 2"],
            "extraction_confidence": 0.8
        }}
        
        Only include details that are explicitly mentioned or clearly implied. Don't make assumptions.
        """
        
        response = call_llm(self.llm, extraction_prompt, temperature=0.3, max_tokens=600)
        
        # Parse JSON response
        try:
            extraction_data = json.loads(response.strip())
            
            return ExtractedContext(
                experiences=extraction_data.get('experiences', []),
                interests=extraction_data.get('interests', []),
                background_details=extraction_data.get('background_details', []),
                goals=extraction_data.get('goals', []),
                specific_mentions=extraction_data.get('specific_mentions', []),
                academic_focus=extraction_data.get('academic_focus', []),
                personal_values=extraction_data.get('personal_values', []),
                activities=extraction_data.get('activities', []),
                extraction_confidence=float(extraction_data.get('extraction_confidence', 0.7))
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM extraction: {e}")
            return self._parse_unstructured_extraction(response)
    
    def _parse_unstructured_extraction(self, response: str) -> ExtractedContext:
        """Parse extraction from unstructured LLM response."""
        
        response_lower = response.lower()
        
        # Look for common indicators
        experiences = []
        interests = []
        background_details = []
        
        # Simple keyword extraction from response
        experience_keywords = ['project', 'work', 'volunteer', 'research', 'app', 'startup']
        for keyword in experience_keywords:
            if keyword in response_lower:
                experiences.append(keyword)
        
        interest_keywords = ['technology', 'innovation', 'helping', 'service', 'stem']
        for keyword in interest_keywords:
            if keyword in response_lower:
                interests.append(keyword)
        
        background_keywords = ['family', 'vietnam', 'immigration', 'culture']
        for keyword in background_keywords:
            if keyword in response_lower:
                background_details.append(keyword)
        
        return ExtractedContext(
            experiences=experiences,
            interests=interests,
            background_details=background_details,
            goals=[],
            specific_mentions=[],
            academic_focus=[],
            personal_values=[],
            activities=[],
            extraction_confidence=0.4  # Lower confidence for fallback
        )
    
    def _merge_extractions(self, quick: ExtractedContext, detailed: ExtractedContext) -> ExtractedContext:
        """Merge quick and detailed extractions."""
        
        # Combine all lists, removing duplicates
        merged = ExtractedContext(
            experiences=list(set(quick.experiences + detailed.experiences)),
            interests=list(set(quick.interests + detailed.interests)),
            background_details=list(set(quick.background_details + detailed.background_details)),
            goals=list(set(quick.goals + detailed.goals)),
            specific_mentions=list(set(quick.specific_mentions + detailed.specific_mentions)),
            academic_focus=list(set(quick.academic_focus + detailed.academic_focus)),
            personal_values=list(set(quick.personal_values + detailed.personal_values)),
            activities=list(set(quick.activities + detailed.activities)),
            extraction_confidence=max(quick.extraction_confidence, detailed.extraction_confidence)
        )
        
        # Clean up empty or very short entries
        merged.experiences = [exp for exp in merged.experiences if len(exp.strip()) > 2]
        merged.interests = [int for int in merged.interests if len(int.strip()) > 1]
        merged.background_details = [bg for bg in merged.background_details if len(bg.strip()) > 2]
        
        return merged
    
    def _update_user_profile(self, existing_profile: Dict[str, Any], extracted: ExtractedContext) -> Dict[str, Any]:
        """Update existing user profile with extracted context."""
        
        updated_profile = dict(existing_profile)  # Copy existing profile
        
        # Update or add new fields
        if extracted.experiences:
            existing_experiences = updated_profile.get('experiences', [])
            if isinstance(existing_experiences, list):
                updated_profile['experiences'] = list(set(existing_experiences + extracted.experiences))
            else:
                updated_profile['experiences'] = extracted.experiences
        
        if extracted.interests:
            existing_interests = updated_profile.get('interests', [])
            if isinstance(existing_interests, list):
                updated_profile['interests'] = list(set(existing_interests + extracted.interests))
            else:
                updated_profile['interests'] = extracted.interests
        
        if extracted.background_details:
            updated_profile['background_details'] = updated_profile.get('background_details', []) + extracted.background_details
        
        if extracted.goals:
            updated_profile['goals'] = updated_profile.get('goals', []) + extracted.goals
        
        if extracted.academic_focus:
            updated_profile['academic_focus'] = extracted.academic_focus
        
        if extracted.personal_values:
            updated_profile['personal_values'] = updated_profile.get('personal_values', []) + extracted.personal_values
        
        if extracted.activities:
            updated_profile['activities'] = updated_profile.get('activities', []) + extracted.activities
        
        # Add metadata
        updated_profile['last_context_update'] = time.time()
        updated_profile['extraction_confidence'] = extracted.extraction_confidence
        
        return updated_profile
    
    def _generate_integration_summary(self, extracted: ExtractedContext, existing_profile: Dict[str, Any]) -> str:
        """Generate summary of what was extracted and integrated."""
        
        summary_parts = []
        
        if extracted.experiences:
            summary_parts.append(f"Experiences: {', '.join(extracted.experiences[:3])}")
        
        if extracted.interests:
            summary_parts.append(f"Interests: {', '.join(extracted.interests[:3])}")
        
        if extracted.background_details:
            summary_parts.append(f"Background: {', '.join(extracted.background_details[:2])}")
        
        if extracted.goals:
            summary_parts.append(f"Goals: {', '.join(extracted.goals[:2])}")
        
        if not summary_parts:
            return "No new context extracted from user input"
        
        return "Extracted - " + "; ".join(summary_parts)
    
    def _format_conversation_context(self, conversation_history: List[Dict]) -> str:
        """Format conversation history for extraction context."""
        
        if not conversation_history:
            return "No previous conversation"
        
        # Get last 2 turns for context
        recent_turns = conversation_history[-2:]
        formatted = []
        
        for turn in recent_turns:
            user_input = turn.get('user_input', '')
            if user_input:
                formatted.append(f"User: {user_input[:100]}...")
        
        return '\n'.join(formatted) if formatted else "No relevant conversation context"
    
    def _create_fallback_update(self, user_input: str, existing_profile: Dict[str, Any]) -> ContextUpdate:
        """Create fallback context update when extraction fails."""
        
        # At minimum, note that user provided input
        basic_extraction = self._quick_pattern_extraction(user_input)
        
        return ContextUpdate(
            new_experiences=basic_extraction.experiences,
            new_interests=basic_extraction.interests,
            new_background=basic_extraction.background_details,
            new_goals=[],
            updated_profile=existing_profile,
            integration_summary="Basic pattern extraction completed"
        )
    
    def extract_key_themes(self, user_input: str) -> List[str]:
        """Extract key themes for immediate use in responses."""
        
        themes = []
        input_lower = user_input.lower()
        
        # Common essay themes
        theme_patterns = {
            'innovation': ['innovation', 'invent', 'create', 'new', 'technology'],
            'service': ['help', 'service', 'volunteer', 'community', 'disabled'],
            'leadership': ['lead', 'organize', 'captain', 'president', 'founded'],
            'perseverance': ['overcome', 'challenge', 'difficult', 'struggle', 'persist'],
            'cultural_identity': ['culture', 'heritage', 'immigrant', 'family', 'tradition'],
            'academic_passion': ['research', 'study', 'science', 'math', 'engineering']
        }
        
        for theme, keywords in theme_patterns.items():
            if any(keyword in input_lower for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def get_contextual_keywords(self, extracted_context: ExtractedContext) -> List[str]:
        """Get keywords for contextual response generation."""
        
        keywords = []
        
        # Add experiences as keywords
        keywords.extend(extracted_context.experiences)
        
        # Add interests as keywords
        keywords.extend(extracted_context.interests)
        
        # Add specific mentions
        keywords.extend(extracted_context.specific_mentions)
        
        # Add academic focus
        keywords.extend(extracted_context.academic_focus)
        
        # Clean and deduplicate
        keywords = [kw.strip().lower() for kw in keywords if kw and len(kw.strip()) > 1]
        return list(set(keywords))


# Global instance for easy import
context_extractor = UserContextExtractor() 