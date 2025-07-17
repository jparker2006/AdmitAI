"""Advanced LLM-driven tool selection system for comprehensive essay agent workflow.

This module provides intelligent tool selection from 40+ available tools across 8 categories:
- Brainstorming & Story Development (8 tools)
- Outline & Structure (5 tools) 
- Writing & Drafting (5 tools)
- Polish & Refinement (6 tools)
- Evaluation & Scoring (4 tools)
- Validation & QA (5 tools)
- Prompt Analysis (4 tools)
- Utility & Support (3 tools)

The system uses LLM-driven analysis to select optimal tools based on user intent,
conversation context, and workflow progression.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools import get_available_tools


class ToolCategory(Enum):
    """Categories of tools available in the essay agent."""
    BRAINSTORM = "brainstorming"
    STRUCTURE = "structure" 
    WRITING = "writing"
    POLISH = "polish"
    EVALUATION = "evaluation"
    VALIDATION = "validation"
    PROMPT_ANALYSIS = "prompt_analysis"
    UTILITY = "utility"


@dataclass
class ToolMetadata:
    """Metadata about a specific tool."""
    name: str
    category: ToolCategory
    phase: str
    purpose: str
    prerequisites: List[str]
    outputs: List[str]
    confidence_threshold: float


class ComprehensiveToolSelector:
    """Advanced tool selector with full knowledge of 40+ essay agent tools."""
    
    def __init__(self):
        self.tool_catalog = self._build_comprehensive_tool_catalog()
        self.available_tools = get_available_tools()
    
    def _build_comprehensive_tool_catalog(self) -> Dict[str, ToolMetadata]:
        """Build comprehensive catalog of all 40+ tools with metadata."""
        return {
            # Brainstorming & Story Development Tools (8)
            "brainstorm": ToolMetadata(
                name="brainstorm",
                category=ToolCategory.BRAINSTORM,
                phase="ideation",
                purpose="Generate 3 authentic personal story ideas for essay prompts",
                prerequisites=["essay_prompt", "user_profile"],
                outputs=["story_ideas", "themes", "insights"],
                confidence_threshold=0.8
            ),
            "suggest_stories": ToolMetadata(
                name="suggest_stories",
                category=ToolCategory.BRAINSTORM,
                phase="ideation",
                purpose="Generate 5 detailed story suggestions from user profile",
                prerequisites=["essay_prompt", "detailed_profile"],
                outputs=["story_suggestions", "relevance_scores"],
                confidence_threshold=0.7
            ),
            "match_story": ToolMetadata(
                name="match_story",
                category=ToolCategory.BRAINSTORM,
                phase="selection",
                purpose="Match specific user experiences to essay prompts",
                prerequisites=["multiple_experiences", "prompt_requirements"],
                outputs=["best_matches", "fit_analysis"],
                confidence_threshold=0.8
            ),
            "expand_story": ToolMetadata(
                name="expand_story",
                category=ToolCategory.BRAINSTORM,
                phase="development",
                purpose="Develop chosen story idea with vivid details",
                prerequisites=["selected_story", "initial_outline"],
                outputs=["expanded_narrative", "key_moments"],
                confidence_threshold=0.7
            ),
            "brainstorm_specific": ToolMetadata(
                name="brainstorm_specific",
                category=ToolCategory.BRAINSTORM,
                phase="targeted_ideation",
                purpose="Generate ideas for specific prompt types or themes",
                prerequisites=["prompt_theme", "user_background"],
                outputs=["targeted_ideas", "theme_alignment"],
                confidence_threshold=0.8
            ),
            "story_development": ToolMetadata(
                name="story_development",
                category=ToolCategory.BRAINSTORM,
                phase="narrative_building",
                purpose="Develop story arc with conflict, growth, reflection",
                prerequisites=["core_story", "character_development"],
                outputs=["story_arc", "narrative_elements"],
                confidence_threshold=0.7
            ),
            "story_themes": ToolMetadata(
                name="story_themes",
                category=ToolCategory.BRAINSTORM,
                phase="thematic_analysis",
                purpose="Extract and analyze themes from personal stories",
                prerequisites=["developed_stories", "prompt_context"],
                outputs=["theme_analysis", "depth_assessment"],
                confidence_threshold=0.8
            ),
            "validate_uniqueness": ToolMetadata(
                name="validate_uniqueness",
                category=ToolCategory.BRAINSTORM,
                phase="uniqueness_check",
                purpose="Ensure story originality and avoid clichés",
                prerequisites=["story_concept", "comparative_context"],
                outputs=["uniqueness_score", "differentiation_suggestions"],
                confidence_threshold=0.9
            ),
            
            # Outline & Structure Tools (5)
            "outline": ToolMetadata(
                name="outline",
                category=ToolCategory.STRUCTURE,
                phase="planning",
                purpose="Generate 5-part essay outline (hook, context, conflict, growth, reflection)",
                prerequisites=["chosen_story", "essay_prompt", "word_count"],
                outputs=["structured_outline", "section_breakdown"],
                confidence_threshold=0.8
            ),
            "outline_generator": ToolMetadata(
                name="outline_generator",
                category=ToolCategory.STRUCTURE,
                phase="advanced_planning",
                purpose="Generate sophisticated outlines with multiple approaches",
                prerequisites=["story_elements", "strategic_goals"],
                outputs=["outline_options", "strategic_recommendations"],
                confidence_threshold=0.7
            ),
            "structure_validator": ToolMetadata(
                name="structure_validator",
                category=ToolCategory.STRUCTURE,
                phase="validation",
                purpose="Validate essay structure and logical flow",
                prerequisites=["complete_outline", "essay_requirements"],
                outputs=["structure_analysis", "improvement_suggestions"],
                confidence_threshold=0.8
            ),
            "transition_suggestion": ToolMetadata(
                name="transition_suggestion",
                category=ToolCategory.STRUCTURE,
                phase="refinement",
                purpose="Suggest smooth transitions between essay sections",
                prerequisites=["outline_sections", "narrative_flow"],
                outputs=["transition_phrases", "flow_improvements"],
                confidence_threshold=0.7
            ),
            "length_optimizer": ToolMetadata(
                name="length_optimizer",
                category=ToolCategory.STRUCTURE,
                phase="optimization",
                purpose="Optimize essay length and section proportions",
                prerequisites=["draft_sections", "word_limits"],
                outputs=["length_recommendations", "section_adjustments"],
                confidence_threshold=0.8
            ),
            
            # Writing & Drafting Tools (5)
            "draft": ToolMetadata(
                name="draft",
                category=ToolCategory.WRITING,
                phase="drafting",
                purpose="Generate complete essay draft from outline with user context",
                prerequisites=["finalized_outline", "user_voice", "target_word_count"],
                outputs=["essay_draft", "actual_word_count"],
                confidence_threshold=0.8
            ),
            "expand_outline_section": ToolMetadata(
                name="expand_outline_section",
                category=ToolCategory.WRITING,
                phase="section_development",
                purpose="Expand specific outline sections into full paragraphs",
                prerequisites=["outline_section", "context", "voice_profile"],
                outputs=["expanded_paragraph", "section_content"],
                confidence_threshold=0.7
            ),
            "rewrite_paragraph": ToolMetadata(
                name="rewrite_paragraph",
                category=ToolCategory.WRITING,
                phase="revision",
                purpose="Rewrite paragraphs for clarity, impact, or voice",
                prerequisites=["existing_paragraph", "improvement_goals"],
                outputs=["rewritten_paragraph", "improvement_notes"],
                confidence_threshold=0.8
            ),
            "improve_opening": ToolMetadata(
                name="improve_opening",
                category=ToolCategory.WRITING,
                phase="hook_development",
                purpose="Enhance essay opening for maximum impact",
                prerequisites=["current_opening", "story_context"],
                outputs=["improved_opening", "engagement_analysis"],
                confidence_threshold=0.8
            ),
            "strengthen_voice": ToolMetadata(
                name="strengthen_voice",
                category=ToolCategory.WRITING,
                phase="voice_development",
                purpose="Enhance authentic voice throughout essay",
                prerequisites=["essay_content", "voice_characteristics"],
                outputs=["voice_enhanced_text", "authenticity_notes"],
                confidence_threshold=0.7
            ),
            
            # Polish & Refinement Tools (6)
            "polish": ToolMetadata(
                name="polish",
                category=ToolCategory.POLISH,
                phase="final_polish",
                purpose="Final essay polishing for submission readiness",
                prerequisites=["near_final_draft", "submission_requirements"],
                outputs=["polished_essay", "final_checks"],
                confidence_threshold=0.9
            ),
            "fix_grammar": ToolMetadata(
                name="fix_grammar",
                category=ToolCategory.POLISH,
                phase="grammar_correction",
                purpose="Correct grammar while preserving authentic voice",
                prerequisites=["draft_text", "voice_preservation_notes"],
                outputs=["corrected_text", "grammar_improvements"],
                confidence_threshold=0.9
            ),
            "enhance_vocabulary": ToolMetadata(
                name="enhance_vocabulary",
                category=ToolCategory.POLISH,
                phase="vocabulary_improvement",
                purpose="Enhance vocabulary sophistication appropriately",
                prerequisites=["text_content", "target_audience"],
                outputs=["enhanced_text", "vocabulary_improvements"],
                confidence_threshold=0.8
            ),
            "check_consistency": ToolMetadata(
                name="check_consistency",
                category=ToolCategory.POLISH,
                phase="consistency_check",
                purpose="Ensure consistency in tone, tense, and style",
                prerequisites=["complete_essay", "style_guidelines"],
                outputs=["consistency_report", "correction_suggestions"],
                confidence_threshold=0.8
            ),
            "optimize_word_count": ToolMetadata(
                name="optimize_word_count",
                category=ToolCategory.POLISH,
                phase="length_optimization",
                purpose="Optimize essay to meet exact word count requirements",
                prerequisites=["essay_draft", "word_limit", "priority_content"],
                outputs=["optimized_essay", "word_count_changes"],
                confidence_threshold=0.9
            ),
            "word_count": ToolMetadata(
                name="word_count",
                category=ToolCategory.POLISH,
                phase="measurement",
                purpose="Accurate word count analysis and breakdown",
                prerequisites=["text_content"],
                outputs=["word_count", "character_count", "paragraph_breakdown"],
                confidence_threshold=1.0
            ),
            
            # Evaluation & Scoring Tools (4)
            "essay_scoring": ToolMetadata(
                name="essay_scoring",
                category=ToolCategory.EVALUATION,
                phase="assessment",
                purpose="Score essay on 5-dimension admissions rubric",
                prerequisites=["complete_essay", "essay_prompt"],
                outputs=["rubric_scores", "detailed_feedback"],
                confidence_threshold=0.8
            ),
            "weakness_highlight": ToolMetadata(
                name="weakness_highlight",
                category=ToolCategory.EVALUATION,
                phase="weakness_analysis",
                purpose="Identify and highlight specific essay weaknesses",
                prerequisites=["essay_text", "scoring_context"],
                outputs=["weakness_analysis", "improvement_priorities"],
                confidence_threshold=0.8
            ),
            "cliche_detection": ToolMetadata(
                name="cliche_detection",
                category=ToolCategory.EVALUATION,
                phase="originality_check",
                purpose="Detect overused phrases and clichéd expressions",
                prerequisites=["essay_content"],
                outputs=["cliche_report", "originality_suggestions"],
                confidence_threshold=0.9
            ),
            "alignment_check": ToolMetadata(
                name="alignment_check",
                category=ToolCategory.EVALUATION,
                phase="prompt_alignment",
                purpose="Verify essay alignment with prompt requirements",
                prerequisites=["essay", "prompt_requirements"],
                outputs=["alignment_score", "requirement_analysis"],
                confidence_threshold=0.8
            ),
            
            # Validation & QA Tools (5)
            "plagiarism_check": ToolMetadata(
                name="plagiarism_check",
                category=ToolCategory.VALIDATION,
                phase="integrity_check",
                purpose="Check for potential plagiarism issues",
                prerequisites=["essay_text", "reference_context"],
                outputs=["plagiarism_report", "originality_verification"],
                confidence_threshold=0.9
            ),
            "outline_alignment": ToolMetadata(
                name="outline_alignment",
                category=ToolCategory.VALIDATION,
                phase="structure_verification",
                purpose="Verify essay follows planned outline structure",
                prerequisites=["essay_draft", "original_outline"],
                outputs=["alignment_analysis", "structural_adherence"],
                confidence_threshold=0.8
            ),
            "final_polish": ToolMetadata(
                name="final_polish",
                category=ToolCategory.VALIDATION,
                phase="final_validation",
                purpose="Comprehensive final validation before submission",
                prerequisites=["polished_essay", "all_requirements"],
                outputs=["validation_report", "submission_readiness"],
                confidence_threshold=0.95
            ),
            "comprehensive_validation": ToolMetadata(
                name="comprehensive_validation",
                category=ToolCategory.VALIDATION,
                phase="full_qa",
                purpose="Complete quality assurance across all dimensions",
                prerequisites=["complete_essay", "full_context"],
                outputs=["comprehensive_report", "final_recommendations"],
                confidence_threshold=0.9
            ),
            
            # Prompt Analysis Tools (4)
            "classify_prompt": ToolMetadata(
                name="classify_prompt",
                category=ToolCategory.PROMPT_ANALYSIS,
                phase="prompt_understanding",
                purpose="Classify essay prompt by theme and approach",
                prerequisites=["essay_prompt"],
                outputs=["prompt_classification", "strategic_insights"],
                confidence_threshold=0.8
            ),
            "extract_requirements": ToolMetadata(
                name="extract_requirements",
                category=ToolCategory.PROMPT_ANALYSIS,
                phase="requirement_analysis",
                purpose="Extract explicit requirements and constraints",
                prerequisites=["essay_prompt", "submission_guidelines"],
                outputs=["requirement_list", "constraint_analysis"],
                confidence_threshold=0.9
            ),
            "suggest_strategy": ToolMetadata(
                name="suggest_strategy",
                category=ToolCategory.PROMPT_ANALYSIS,
                phase="strategic_planning",
                purpose="Suggest optimal response strategy for prompt",
                prerequisites=["prompt_analysis", "user_profile"],
                outputs=["strategic_recommendations", "approach_options"],
                confidence_threshold=0.8
            ),
            "detect_overlap": ToolMetadata(
                name="detect_overlap",
                category=ToolCategory.PROMPT_ANALYSIS,
                phase="overlap_analysis",
                purpose="Detect overlap between multiple essay prompts",
                prerequisites=["multiple_prompts", "application_context"],
                outputs=["overlap_analysis", "differentiation_strategy"],
                confidence_threshold=0.8
            ),
            
            # Utility & Support Tools (3)
            "echo": ToolMetadata(
                name="echo",
                category=ToolCategory.UTILITY,
                phase="testing",
                purpose="Test system functionality and provide feedback",
                prerequisites=["message"],
                outputs=["echo_response", "system_status"],
                confidence_threshold=1.0
            ),
            "clarify": ToolMetadata(
                name="clarify",
                category=ToolCategory.UTILITY,
                phase="clarification",
                purpose="Ask clarifying questions for ambiguous requests",
                prerequisites=["user_input", "context"],
                outputs=["clarifying_questions", "guidance_suggestions"],
                confidence_threshold=0.9
            ),
            "revise": ToolMetadata(
                name="revise",
                category=ToolCategory.UTILITY,
                phase="revision",
                purpose="General revision and improvement suggestions",
                prerequisites=["content", "improvement_goals"],
                outputs=["revision_suggestions", "improvement_plan"],
                confidence_threshold=0.8
            )
        }

    async def select_tools_intelligent(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        available_tools: Optional[List[str]] = None,
        max_tools: int = 3
    ) -> List[str]:
        """Intelligent tool selection using LLM analysis and workflow progression logic.
        
        Args:
            user_input: User's message to analyze
            conversation_history: Recent conversation context
            user_profile: User profile information
            available_tools: Optional subset of tools to consider
            max_tools: Maximum number of tools to return
            
        Returns:
            List of selected tool names optimized for workflow progression
        """
        try:
            # CRITICAL FIX: Analyze conversation history for tool usage patterns
            recent_tools = self._extract_recent_tools(conversation_history)
            brainstorm_count = recent_tools.count('brainstorm')
            
            # PREVENT EXCESSIVE BRAINSTORM USAGE: If brainstorm used 2+ times recently, force progression
            if brainstorm_count >= 2:
                return self._force_workflow_progression(user_input, recent_tools, max_tools)
            
            # Build enhanced context for tool selection
            enhanced_context = await self._build_enhanced_context(
                user_input, conversation_history, user_profile, recent_tools
            )
            
            # LLM-powered tool selection with workflow awareness
            llm_response = await self._call_llm_for_tool_selection(enhanced_context)
            selected_tools = self._parse_llm_tool_selection(llm_response)
            
            # Validate and enforce workflow progression
            validated_tools = self._validate_and_enforce_progression(
                selected_tools, recent_tools, enhanced_context, max_tools
            )
            
            # Final fallback with aggressive progression enforcement
            if not validated_tools:
                validated_tools = self._get_progression_fallback(recent_tools, enhanced_context)
            
            return validated_tools[:max_tools]
            
        except Exception as e:
            logger.error(f"Error in intelligent tool selection: {e}")
            # Enhanced fallback with workflow progression
            return self._get_workflow_aware_fallback(user_input, max_tools)
    
    def _extract_recent_tools(self, conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Extract recently used tools from conversation history."""
        recent_tools = []
        
        for turn in conversation_history[-5:]:  # Last 5 turns
            # Look for tool usage indicators in agent responses
            agent_response = turn.get('agent', turn.get('output', ''))
            if isinstance(agent_response, str):
                # Common patterns that indicate tool usage
                if 'brainstormed' in agent_response.lower() or 'story ideas' in agent_response.lower():
                    recent_tools.append('brainstorm')
                elif 'outline' in agent_response.lower() and ('created' in agent_response.lower() or 'structured' in agent_response.lower()):
                    recent_tools.append('outline')
                elif 'draft' in agent_response.lower() and 'wrote' in agent_response.lower():
                    recent_tools.append('draft')
                elif 'revised' in agent_response.lower() or 'improved' in agent_response.lower():
                    recent_tools.append('revise')
                elif 'polished' in agent_response.lower() or 'refined' in agent_response.lower():
                    recent_tools.append('polish')
        
        return recent_tools
    
    def _force_workflow_progression(self, user_input: str, recent_tools: List[str], max_tools: int) -> List[str]:
        """Force progression to next workflow phase when brainstorm overused."""
        logger.info("Forcing workflow progression due to excessive brainstorm usage")
        
        user_lower = user_input.lower()
        
        # Determine current workflow state and force next step
        if 'outline' in recent_tools:
            # If outline done, force draft
            if any(word in user_lower for word in ['write', 'draft', 'essay', 'expand']):
                return ['draft']
            else:
                return ['draft', 'expand_outline_section']
        elif any(tool in recent_tools for tool in ['brainstorm', 'story']):
            # If brainstorming done, force outline
            if any(word in user_lower for word in ['outline', 'structure', 'organize']):
                return ['outline']
            else:
                return ['outline', 'structure_validator']
        else:
            # Fallback: suggest outline as next logical step
            return ['outline', 'story_analysis']
    
    def _validate_and_enforce_progression(self, selected_tools: List[str], recent_tools: List[str], 
                                        context: Dict[str, Any], max_tools: int) -> List[str]:
        """Validate tool selection and enforce logical workflow progression."""
        validated_tools = []
        
        # Check for workflow progression violations
        brainstorm_count = recent_tools.count('brainstorm')
        
        for tool in selected_tools:
            # CRITICAL: Prevent excessive brainstorm usage
            if tool == 'brainstorm' and brainstorm_count >= 2:
                logger.warning("Blocking excessive brainstorm usage, forcing progression")
                # Replace with progression tool
                if 'outline' not in recent_tools:
                    validated_tools.append('outline')
                elif 'draft' not in recent_tools:
                    validated_tools.append('draft')
                else:
                    validated_tools.append('revise')
                continue
            
            # Check if tool is appropriate for current workflow state
            if self._is_tool_appropriate_for_state(tool, recent_tools, context):
                validated_tools.append(tool)
        
        # Ensure we have at least one tool by adding progression-appropriate tool
        if not validated_tools:
            validated_tools = self._get_progression_fallback(recent_tools, context)
        
        return validated_tools
    
    def _is_tool_appropriate_for_state(self, tool: str, recent_tools: List[str], 
                                     context: Dict[str, Any]) -> bool:
        """Check if tool is appropriate for current workflow state."""
        
        # Define workflow progression rules
        workflow_rules = {
            'brainstorm': {
                'max_usage': 2,  # Allow max 2 brainstorm uses
                'required_before': [],
                'not_after': ['draft', 'revise', 'polish']
            },
            'outline': {
                'max_usage': 3,
                'required_before': [],  # Can be used without brainstorm in some cases
                'not_after': ['polish']
            },
            'draft': {
                'max_usage': 2,
                'preferred_after': ['brainstorm', 'outline'],
                'not_after': ['polish']
            },
            'revise': {
                'max_usage': 5,
                'required_before': ['draft'],
                'not_after': []
            },
            'polish': {
                'max_usage': 3,
                'required_before': ['draft'],
                'not_after': []
            }
        }
        
        if tool not in workflow_rules:
            return True  # Allow non-workflow tools
        
        rules = workflow_rules[tool]
        tool_count = recent_tools.count(tool)
        
        # Check max usage
        if tool_count >= rules['max_usage']:
            return False
        
        # Check required prerequisites
        if 'required_before' in rules:
            for required in rules['required_before']:
                if required not in recent_tools:
                    return False
        
        # Check if tool shouldn't be used after certain others
        if 'not_after' in rules:
            for blocker in rules['not_after']:
                if blocker in recent_tools:
                    return False
        
        return True
    
    def _get_progression_fallback(self, recent_tools: List[str], context: Dict[str, Any]) -> List[str]:
        """Get fallback tools that promote workflow progression."""
        
        # Determine current workflow phase
        if not recent_tools or not any(tool in recent_tools for tool in ['brainstorm', 'outline', 'draft']):
            # Early phase - promote brainstorming or outline
            return ['brainstorm', 'classify_prompt']
        elif 'brainstorm' in recent_tools and 'outline' not in recent_tools:
            # Brainstorming done, need outline
            return ['outline', 'structure_validator']
        elif 'outline' in recent_tools and 'draft' not in recent_tools:
            # Outline done, need draft
            return ['draft', 'expand_outline_section']
        elif 'draft' in recent_tools and 'revise' not in recent_tools:
            # Draft done, need revision
            return ['revise', 'essay_scoring']
        else:
            # Late phase - polish or evaluate
            return ['polish', 'comprehensive_validation']
    
    def _get_workflow_aware_fallback(self, user_input: str, max_tools: int) -> List[str]:
        """Enhanced fallback with workflow awareness."""
        user_lower = user_input.lower()
        
        # Intent-based fallback with workflow progression
        if any(word in user_lower for word in ['idea', 'story', 'brainstorm', 'help me think']):
            return ['brainstorm']
        elif any(word in user_lower for word in ['outline', 'structure', 'organize']):
            return ['outline']  
        elif any(word in user_lower for word in ['write', 'draft', 'essay']):
            return ['draft']
        elif any(word in user_lower for word in ['improve', 'revise', 'better']):
            return ['revise']
        elif any(word in user_lower for word in ['polish', 'final', 'finish']):
            return ['polish']
        else:
            # Default progression-promoting fallback
            return ['clarify', 'echo'] 

    async def _build_enhanced_context(self, user_input: str, conversation_history: List[Dict[str, Any]], 
                                    user_profile: Dict[str, Any], recent_tools: List[str]) -> Dict[str, Any]:
        """Build enhanced context for intelligent tool selection."""
        return {
            "user_input": user_input,
            "recent_tools": recent_tools,
            "conversation_length": len(conversation_history),
            "user_profile": user_profile,
            "workflow_phase": self._determine_workflow_phase(recent_tools),
            "urgency_indicators": self._detect_urgency_indicators(user_input),
            "complexity_level": self._assess_complexity(user_input, conversation_history)
        }
    
    async def _call_llm_for_tool_selection(self, context: Dict[str, Any]) -> str:
        """Call LLM for tool selection with enhanced context."""
        prompt = f"""
        You are an expert essay writing workflow advisor. Select the best tools for this situation:
        
        USER REQUEST: "{context['user_input']}"
        RECENT TOOLS USED: {context['recent_tools']}
        WORKFLOW PHASE: {context['workflow_phase']}
        
        RULES:
        1. If brainstorm was used 2+ times recently, DO NOT suggest brainstorm again
        2. Follow logical progression: brainstorm → outline → draft → revise → polish
        3. Select maximum 2 tools that advance the workflow
        
        Return JSON array of tool names: ["tool1", "tool2"]
        """
        
        llm = get_chat_llm(temperature=0.2)
        return call_llm(llm, prompt)
    
    def _parse_llm_tool_selection(self, response: str) -> List[str]:
        """Parse LLM response to extract tool names."""
        try:
            # Try to parse as JSON
            if '[' in response and ']' in response:
                import re
                match = re.search(r'\[(.*?)\]', response)
                if match:
                    tools_str = match.group(1)
                    # Extract quoted tool names
                    tools = re.findall(r'"([^"]+)"', tools_str)
                    return tools
            return []
        except Exception:
            return []
    
    def _determine_workflow_phase(self, recent_tools: List[str]) -> str:
        """Determine current workflow phase based on recent tools."""
        if 'polish' in recent_tools:
            return 'polishing'
        elif 'revise' in recent_tools or 'draft' in recent_tools:
            return 'revision'
        elif 'outline' in recent_tools:
            return 'drafting'
        elif 'brainstorm' in recent_tools:
            return 'planning'
        else:
            return 'ideation'
    
    def _detect_urgency_indicators(self, user_input: str) -> List[str]:
        """Detect urgency indicators in user input."""
        urgency_words = ['urgent', 'deadline', 'asap', 'quickly', 'fast', 'emergency', 'due']
        user_lower = user_input.lower()
        return [word for word in urgency_words if word in user_lower]
    
    def _assess_complexity(self, user_input: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Assess complexity level of user request."""
        complex_indicators = ['complex', 'difficult', 'challenging', 'multiple', 'comprehensive']
        simple_indicators = ['simple', 'basic', 'quick', 'easy', 'just']
        
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in complex_indicators):
            return 'complex'
        elif any(word in user_lower for word in simple_indicators):
            return 'simple'
        elif len(conversation_history) > 10:
            return 'complex'  # Long conversations suggest complexity
        else:
            return 'moderate'

    def get_tool_categories(self) -> Dict[str, List[str]]:
        """Get tools organized by category."""
        categories = {}
        for tool_name, metadata in self.tool_catalog.items():
            category = metadata.category.value
            if category not in categories:
                categories[category] = []
            categories[category].append(tool_name)
        return categories

    def get_tools_for_phase(self, phase: str) -> List[str]:
        """Get tools appropriate for a specific workflow phase."""
        return [
            name for name, meta in self.tool_catalog.items()
            if meta.phase == phase or phase in meta.phase
        ]


# Singleton instance for use throughout the application
comprehensive_tool_selector = ComprehensiveToolSelector()


async def select_tools_with_full_context(
    user_input: str,
    conversation_history: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    max_tools: int = 3
) -> List[str]:
    """Main entry point for intelligent tool selection using all 40+ tools."""
    return await comprehensive_tool_selector.select_tools_intelligent(
        user_input=user_input,
        conversation_history=conversation_history,
        user_profile=user_profile,
        max_tools=max_tools
    )


# Legacy compatibility function
async def select_tools(
    user_input: str,
    conversation_context: Dict[str, Any],
    available_tools: List[str],
    user_goals: List[str]
) -> List[str]:
    """Legacy compatibility wrapper for tool selection."""
    conversation_history = conversation_context.get('conversation_history', [])
    user_profile = conversation_context.get('user_profile', {})
    
    return await comprehensive_tool_selector.select_tools_intelligent(
        user_input=user_input,
        conversation_history=conversation_history,
        user_profile=user_profile,
        available_tools=available_tools,
        max_tools=3
    ) 