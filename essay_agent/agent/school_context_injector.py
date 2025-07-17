"""School-specific context injection system.

This module provides intelligent school context enhancement capabilities that add
relevant school-specific information, values, programs, and culture details to
responses when appropriate, making conversations more targeted and personalized.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

from essay_agent.llm_client import get_chat_llm, call_llm

logger = logging.getLogger(__name__)


@dataclass
class SchoolContext:
    """Container for school-specific information."""
    name: str
    values: List[str]
    programs: List[str]
    culture: List[str]
    admissions_priorities: List[str]
    notable_features: List[str]
    essay_preferences: List[str]


class SchoolContextInjector:
    """Add school-specific context to responses based on scenario and user interests.
    
    This class solves Bug #14 (school-specific context missing) by intelligently
    adding relevant school information, values, programs, and cultural details
    to responses when the conversation involves specific schools or applications.
    """
    
    def __init__(self):
        """Initialize the school context injector."""
        self.llm = get_chat_llm()
        
        # Comprehensive school context database
        self.school_contexts = {
            'stanford': SchoolContext(
                name='Stanford',
                values=['innovation', 'entrepreneurship', 'social impact', 'interdisciplinary learning'],
                programs=['Computer Science', 'Engineering', 'Human-Computer Interaction', 'Design Thinking', 'Bioengineering'],
                culture=['collaborative', 'forward-thinking', 'risk-taking', 'problem-solving'],
                admissions_priorities=['intellectual curiosity', 'impact potential', 'collaborative spirit'],
                notable_features=['Silicon Valley location', 'startup culture', 'research opportunities'],
                essay_preferences=['authenticity', 'personal growth', 'future impact']
            ),
            
            'harvard': SchoolContext(
                name='Harvard',
                values=['leadership', 'service', 'academic excellence', 'global citizenship'],
                programs=['Liberal Arts', 'Public Policy', 'Medicine', 'Business', 'Law'],
                culture=['intellectual rigor', 'tradition', 'diverse perspectives', 'debate'],
                admissions_priorities=['leadership potential', 'academic achievement', 'character'],
                notable_features=['oldest university', 'extensive alumni network', 'Cambridge location'],
                essay_preferences=['intellectual engagement', 'personal character', 'contribution to community']
            ),
            
            'mit': SchoolContext(
                name='MIT',
                values=['innovation', 'problem-solving', 'hands-on learning', 'making'],
                programs=['Engineering', 'Computer Science', 'Physics', 'Research', 'UROP'],
                culture=['maker culture', 'collaboration', 'intensity', 'creativity'],
                admissions_priorities=['technical aptitude', 'creativity', 'collaboration'],
                notable_features=['hands-on learning', 'research opportunities', 'maker spaces'],
                essay_preferences=['problem-solving stories', 'technical passion', 'collaborative projects']
            ),
            
            'yale': SchoolContext(
                name='Yale',
                values=['community', 'leadership', 'service', 'intellectual exploration'],
                programs=['Liberal Arts', 'Residential Colleges', 'Arts', 'Drama'],
                culture=['residential college system', 'tradition', 'close-knit community'],
                admissions_priorities=['community contribution', 'leadership', 'intellectual curiosity'],
                notable_features=['residential colleges', 'strong alumni network', 'Gothic architecture'],
                essay_preferences=['community involvement', 'personal growth', 'intellectual pursuits']
            ),
            
            'princeton': SchoolContext(
                name='Princeton',
                values=['service', 'leadership', 'academic excellence', 'honor'],
                programs=['Liberal Arts', 'Public Policy', 'Engineering', 'Research'],
                culture=['honor code', 'undergraduate focus', 'service ethic'],
                admissions_priorities=['character', 'leadership', 'academic excellence'],
                notable_features=['undergraduate focus', 'honor system', 'beautiful campus'],
                essay_preferences=['personal character', 'service commitment', 'intellectual growth']
            ),
            
            'columbia': SchoolContext(
                name='Columbia',
                values=['diversity', 'urban engagement', 'global perspective', 'social justice'],
                programs=['Liberal Arts', 'Journalism', 'International Affairs', 'Core Curriculum'],
                culture=['diverse', 'urban', 'intellectually rigorous', 'globally minded'],
                admissions_priorities=['diversity contribution', 'global perspective', 'urban engagement'],
                notable_features=['New York City location', 'Core Curriculum', 'diversity'],
                essay_preferences=['diverse perspectives', 'urban experiences', 'global awareness']
            ),
            
            'duke': SchoolContext(
                name='Duke',
                values=['leadership', 'service', 'excellence', 'community'],
                programs=['Engineering', 'Public Policy', 'Medicine', 'Basketball'],
                culture=['school spirit', 'leadership', 'research', 'community service'],
                admissions_priorities=['leadership potential', 'service commitment', 'academic excellence'],
                notable_features=['research university', 'strong athletics', 'beautiful campus'],
                essay_preferences=['leadership stories', 'service commitment', 'personal passion']
            ),
            
            'northwestern': SchoolContext(
                name='Northwestern',
                values=['innovation', 'collaboration', 'practical application', 'diversity'],
                programs=['Journalism', 'Engineering', 'Theatre', 'Business', 'Integrated studies'],
                culture=['collaborative', 'pre-professional', 'innovative', 'spirited'],
                admissions_priorities=['practical application', 'collaboration', 'innovation'],
                notable_features=['quarter system', 'co-op programs', 'lakefront campus'],
                essay_preferences=['practical experiences', 'collaborative projects', 'innovative thinking']
            ),
            
            'brown': SchoolContext(
                name='Brown',
                values=['academic freedom', 'open curriculum', 'creativity', 'social responsibility'],
                programs=['Open Curriculum', 'PLME', 'Liberal Arts', 'Interdisciplinary studies'],
                culture=['open-minded', 'creative', 'socially conscious', 'academic freedom'],
                admissions_priorities=['intellectual curiosity', 'creativity', 'social consciousness'],
                notable_features=['open curriculum', 'no core requirements', 'pass/fail options'],
                essay_preferences=['intellectual curiosity', 'creative pursuits', 'social responsibility']
            )
        }
        
        # Common school type patterns
        self.school_type_patterns = {
            'ivy_league': ['harvard', 'yale', 'princeton', 'columbia', 'brown', 'penn', 'dartmouth', 'cornell'],
            'tech_focused': ['mit', 'caltech', 'georgia tech', 'carnegie mellon'],
            'liberal_arts': ['williams', 'amherst', 'swarthmore', 'pomona'],
            'public_flagship': ['uc berkeley', 'ucla', 'michigan', 'virginia', 'texas']
        }
    
    async def inject_school_context(
        self,
        response: str,
        school_name: str,
        user_interests: List[str],
        user_context: Optional[Dict[str, Any]] = None,
        response_type: str = 'general'
    ) -> str:
        """Add relevant school-specific context to responses.
        
        Args:
            response: Original response text
            school_name: Name of the school to add context for
            user_interests: User's interests and background
            user_context: Additional user context
            response_type: Type of response (brainstorm, outline, draft, etc.)
            
        Returns:
            Enhanced response with school-specific context
        """
        try:
            # Normalize school name
            school_key = self._normalize_school_name(school_name)
            
            if school_key not in self.school_contexts:
                logger.info(f"No context available for school: {school_name}")
                return response
            
            school_context = self.school_contexts[school_key]
            
            # Determine enhancement approach based on response type
            if response_type == 'brainstorm':
                enhanced_response = await self._enhance_brainstorm_with_school(
                    response, school_context, user_interests
                )
            elif response_type == 'outline':
                enhanced_response = await self._enhance_outline_with_school(
                    response, school_context, user_interests
                )
            elif response_type == 'draft':
                enhanced_response = await self._enhance_draft_with_school(
                    response, school_context, user_interests
                )
            else:
                enhanced_response = await self._enhance_general_with_school(
                    response, school_context, user_interests, user_context
                )
            
            logger.info(f"Enhanced response with {school_name} context")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"School context injection failed: {e}")
            return response  # Return original response on failure
    
    async def _enhance_brainstorm_with_school(
        self,
        response: str,
        school_context: SchoolContext,
        user_interests: List[str]
    ) -> str:
        """Enhance brainstorming responses with school-specific themes."""
        
        enhancement_prompt = f"""
        Enhance this brainstorming response to include relevant {school_context.name} context:
        
        ORIGINAL RESPONSE: {response}
        
        SCHOOL CONTEXT:
        - Values: {', '.join(school_context.values)}
        - Notable Programs: {', '.join(school_context.programs[:3])}
        - Culture: {', '.join(school_context.culture[:3])}
        - Essay Preferences: {', '.join(school_context.essay_preferences)}
        
        USER INTERESTS: {', '.join(user_interests) if user_interests else 'General'}
        
        Enhancement Instructions:
        1. Subtly mention {school_context.name} where it makes sense
        2. Align story suggestions with {school_context.name}'s values
        3. Reference relevant programs or opportunities when appropriate
        4. Don't force connections - keep it natural
        5. Maintain the original response's helpful structure
        
        Enhanced response:
        """
        
        enhanced = call_llm(self.llm, enhancement_prompt, temperature=0.5, max_tokens=1000)
        return enhanced.strip()
    
    async def _enhance_outline_with_school(
        self,
        response: str,
        school_context: SchoolContext,
        user_interests: List[str]
    ) -> str:
        """Enhance outline responses with school-specific guidance."""
        
        enhancement_prompt = f"""
        Enhance this outline response with {school_context.name}-specific guidance:
        
        ORIGINAL RESPONSE: {response}
        
        {school_context.name} CONTEXT:
        - Admissions Priorities: {', '.join(school_context.admissions_priorities)}
        - Values: {', '.join(school_context.values)}
        - Essay Preferences: {', '.join(school_context.essay_preferences)}
        
        USER INTERESTS: {', '.join(user_interests) if user_interests else 'General'}
        
        Add relevant guidance about:
        1. How to align the essay with {school_context.name}'s values
        2. What {school_context.name} admissions officers look for
        3. Specific programs or opportunities to mention
        4. Keep enhancement subtle and helpful
        
        Enhanced response:
        """
        
        enhanced = call_llm(self.llm, enhancement_prompt, temperature=0.5, max_tokens=1000)
        return enhanced.strip()
    
    async def _enhance_draft_with_school(
        self,
        response: str,
        school_context: SchoolContext,
        user_interests: List[str]
    ) -> str:
        """Enhance draft responses with school-specific elements."""
        
        enhancement_prompt = f"""
        Enhance this essay draft response to better align with {school_context.name}:
        
        ORIGINAL RESPONSE: {response}
        
        {school_context.name} ALIGNMENT:
        - Values: {', '.join(school_context.values)}
        - Programs to reference: {', '.join(school_context.programs[:3])}
        - Cultural elements: {', '.join(school_context.culture)}
        - Notable features: {', '.join(school_context.notable_features)}
        
        USER INTERESTS: {', '.join(user_interests) if user_interests else 'General'}
        
        Enhancement approach:
        1. Suggest specific {school_context.name} programs that align with user interests
        2. Mention {school_context.name}'s values where relevant
        3. Reference {school_context.name} culture or opportunities naturally
        4. Keep suggestions authentic to the user's story
        
        Enhanced response:
        """
        
        enhanced = call_llm(self.llm, enhancement_prompt, temperature=0.5, max_tokens=1200)
        return enhanced.strip()
    
    async def _enhance_general_with_school(
        self,
        response: str,
        school_context: SchoolContext,
        user_interests: List[str],
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Enhance general responses with school-specific context."""
        
        # Find best alignment between user interests and school
        aligned_elements = self._find_alignment(user_interests, school_context)
        
        if not aligned_elements:
            # If no strong alignment, minimal enhancement
            return self._add_subtle_school_reference(response, school_context.name)
        
        enhancement_prompt = f"""
        Enhance this response with relevant {school_context.name} context:
        
        ORIGINAL RESPONSE: {response}
        
        ALIGNMENT OPPORTUNITIES:
        {aligned_elements}
        
        USER INTERESTS: {', '.join(user_interests) if user_interests else 'General'}
        
        Add {school_context.name} context by:
        1. Mentioning relevant programs or opportunities
        2. Referencing values that align with user interests
        3. Adding natural connections to {school_context.name} culture
        4. Keep enhancements subtle and helpful
        
        Enhanced response:
        """
        
        enhanced = call_llm(self.llm, enhancement_prompt, temperature=0.5, max_tokens=1000)
        return enhanced.strip()
    
    def _normalize_school_name(self, school_name: str) -> str:
        """Normalize school name to match context keys."""
        
        name_lower = school_name.lower().strip()
        
        # Direct matches
        if name_lower in self.school_contexts:
            return name_lower
        
        # Common variations
        name_mappings = {
            'stanford university': 'stanford',
            'harvard university': 'harvard',
            'massachusetts institute of technology': 'mit',
            'yale university': 'yale',
            'princeton university': 'princeton',
            'columbia university': 'columbia',
            'duke university': 'duke',
            'northwestern university': 'northwestern',
            'brown university': 'brown'
        }
        
        for variation, standard in name_mappings.items():
            if variation in name_lower or name_lower in variation:
                return standard
        
        # Check for partial matches
        for school_key in self.school_contexts.keys():
            if school_key in name_lower or name_lower in school_key:
                return school_key
        
        return name_lower  # Return as-is if no match found
    
    def _find_alignment(self, user_interests: List[str], school_context: SchoolContext) -> str:
        """Find alignment between user interests and school context."""
        
        if not user_interests:
            return ""
        
        alignments = []
        
        # Check alignment with programs
        for interest in user_interests:
            interest_lower = interest.lower()
            for program in school_context.programs:
                if interest_lower in program.lower() or program.lower() in interest_lower:
                    alignments.append(f"Interest in {interest} aligns with {school_context.name}'s {program} program")
        
        # Check alignment with values
        for interest in user_interests:
            interest_lower = interest.lower()
            for value in school_context.values:
                if interest_lower in value.lower() or value.lower() in interest_lower:
                    alignments.append(f"Interest in {interest} aligns with {school_context.name}'s emphasis on {value}")
        
        # Check alignment with culture
        for interest in user_interests:
            interest_lower = interest.lower()
            for culture_element in school_context.culture:
                if interest_lower in culture_element.lower() or culture_element.lower() in interest_lower:
                    alignments.append(f"Interest in {interest} fits {school_context.name}'s {culture_element} culture")
        
        return '\n'.join(alignments) if alignments else ""
    
    def _add_subtle_school_reference(self, response: str, school_name: str) -> str:
        """Add subtle school reference when no specific alignment found."""
        
        # Simple enhancement - just mention the school name where appropriate
        if school_name.lower() not in response.lower():
            # Add school reference to conclusion or next steps
            if "What's next?" in response or "next steps" in response.lower():
                response = response.replace(
                    "What's next?",
                    f"What's next for your {school_name} application?"
                )
            elif response.endswith("✨"):
                response = response[:-1] + f" for your {school_name} essay! ✨"
            else:
                response += f"\n\nThis approach will help create a compelling essay for {school_name}!"
        
        return response
    
    def extract_school_from_input(self, user_input: str) -> Optional[str]:
        """Extract school name from user input."""
        
        input_lower = user_input.lower()
        
        # Check for direct school mentions
        for school_key, context in self.school_contexts.items():
            if school_key in input_lower or context.name.lower() in input_lower:
                return context.name
        
        # Check for common school patterns
        school_patterns = [
            r'(stanford|harvard|mit|yale|princeton|columbia|duke|northwestern|brown)',
            r'(university of \w+)',
            r'(\w+ university)',
            r'(\w+ college)'
        ]
        
        for pattern in school_patterns:
            import re
            match = re.search(pattern, input_lower)
            if match:
                potential_school = match.group(1)
                normalized = self._normalize_school_name(potential_school)
                if normalized in self.school_contexts:
                    return self.school_contexts[normalized].name
        
        return None
    
    def get_school_context(self, school_name: str) -> Optional[SchoolContext]:
        """Get school context object for a given school."""
        
        normalized_name = self._normalize_school_name(school_name)
        return self.school_contexts.get(normalized_name)
    
    def get_relevant_programs(self, school_name: str, user_interests: List[str]) -> List[str]:
        """Get programs at a school that align with user interests."""
        
        school_context = self.get_school_context(school_name)
        if not school_context or not user_interests:
            return []
        
        relevant_programs = []
        
        for interest in user_interests:
            interest_lower = interest.lower()
            for program in school_context.programs:
                if interest_lower in program.lower() or program.lower() in interest_lower:
                    relevant_programs.append(program)
        
        return list(set(relevant_programs))  # Remove duplicates


# Global instance for easy import
school_injector = SchoolContextInjector() 