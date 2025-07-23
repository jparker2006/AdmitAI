"""Rich tool descriptions for LLM reasoning.

This module contains comprehensive descriptions of all available tools
that enable the LLM to make intelligent decisions about which tools
to use based on user context and intent.
"""
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ToolDescription:
    """Comprehensive tool description for LLM reasoning."""
    name: str
    category: str
    description: str
    purpose: str
    input_requirements: List[str]
    output_format: str
    when_to_use: str
    example_usage: str
    dependencies: List[str]
    estimated_tokens: int
    confidence_threshold: float = 0.7


# Comprehensive tool descriptions for all registered tools
TOOL_DESCRIPTIONS: Dict[str, ToolDescription] = {
    # ====================================================================
    # CORE WORKFLOW TOOLS - Main essay writing pipeline
    # ====================================================================
    "brainstorm": ToolDescription(
        name="brainstorm",
        category="core_workflow",
        description="Generate three authentic personal story ideas based on user's profile and essay prompt",
        purpose="Help users discover meaningful personal experiences that address the essay prompt",
        input_requirements=["essay_prompt", "profile"],
        output_format="List of Story objects with title, description, prompt_fit, insights, and themes",
        when_to_use="At the beginning of essay writing when user needs story ideas or is stuck on what to write about",
        example_usage="I need help brainstorming ideas for my challenge essay",
        dependencies=[],
        estimated_tokens=800,
        confidence_threshold=0.9
    ),
    
    "outline": ToolDescription(
        name="outline",
        category="core_workflow", 
        description="Create a structured five-part outline (hook, context, conflict, growth, reflection) for a chosen story",
        purpose="Transform a story idea into a clear, organized essay structure",
        input_requirements=["chosen_story", "essay_prompt", "word_count"],
        output_format="Dictionary with outline sections and estimated word count",
        when_to_use="After brainstorming when user has selected a story and needs to structure it",
        example_usage="Create an outline for my leadership story",
        dependencies=["brainstorm"],
        estimated_tokens=600,
        confidence_threshold=0.8
    ),
    
    "draft": ToolDescription(
        name="draft",
        category="core_workflow",
        description="Write a complete first draft based on the structured outline",
        purpose="Convert outline into full essay paragraphs with narrative flow",
        input_requirements=["outline", "story_details", "target_word_count"],
        output_format="Complete essay draft as formatted text",
        when_to_use="After outline creation when ready to write full essay content",
        example_usage="Write a first draft based on my outline",
        dependencies=["outline"],
        estimated_tokens=1200,
        confidence_threshold=0.8
    ),
    
    "revise": ToolDescription(
        name="revise",
        category="core_workflow",
        description="Improve essay content, structure, and clarity through targeted revisions",
        purpose="Enhance essay quality by addressing specific weaknesses and feedback",
        input_requirements=["essay_draft", "revision_focus"],
        output_format="Revised essay with change explanations",
        when_to_use="After drafting when essay needs improvement in content or structure",
        example_usage="Revise my essay to strengthen the conclusion",
        dependencies=["draft"],
        estimated_tokens=1000,
        confidence_threshold=0.7
    ),
    
    "polish": ToolDescription(
        name="polish",
        category="core_workflow",
        description="Final refinement focusing on style, flow, and language precision",
        purpose="Perfect the essay's language and ensure professional presentation",
        input_requirements=["revised_essay"],
        output_format="Polished essay with style improvements",
        when_to_use="Final stage when content is solid but needs language refinement",
        example_usage="Polish my essay for final submission",
        dependencies=["revise"],
        estimated_tokens=800,
        confidence_threshold=0.6
    ),

    # ====================================================================
    # WRITING TOOLS - Content generation and improvement
    # ====================================================================
    "expand_outline_section": ToolDescription(
        name="expand_outline_section",
        category="writing",
        description="Convert a specific outline section into a full, detailed paragraph",
        purpose="Transform outline points into rich, narrative content",
        input_requirements=["outline_section", "context", "target_length"],
        output_format="Expanded paragraph with narrative details",
        when_to_use="During drafting when specific outline sections need detailed expansion",
        example_usage="Expand the 'conflict' section of my outline into a full paragraph",
        dependencies=["outline"],
        estimated_tokens=500,
        confidence_threshold=0.8
    ),
    
    "rewrite_paragraph": ToolDescription(
        name="rewrite_paragraph",
        category="writing",
        description="Rewrite a paragraph to be more compelling, concise, emotional, or match a specific style",
        purpose="Improve specific paragraphs with targeted enhancements",
        input_requirements=["paragraph_text", "improvement_target"],
        output_format="Rewritten paragraph with explanation of changes",
        when_to_use="When specific paragraphs need targeted improvement for style or impact",
        example_usage="Make this paragraph more emotionally compelling",
        dependencies=["draft"],
        estimated_tokens=400,
        confidence_threshold=0.7
    ),
    
    "improve_opening": ToolDescription(
        name="improve_opening",
        category="writing",
        description="Enhance the opening sentence or paragraph to create a stronger hook",
        purpose="Capture reader attention from the first sentence",
        input_requirements=["current_opening", "essay_theme"],
        output_format="Improved opening with hook explanation",
        when_to_use="When the essay opening lacks impact or doesn't draw readers in",
        example_usage="Create a stronger hook for my essay opening",
        dependencies=["draft"],
        estimated_tokens=300,
        confidence_threshold=0.8
    ),
    
    "strengthen_voice": ToolDescription(
        name="strengthen_voice",
        category="writing",
        description="Adjust paragraph content to match user's authentic voice and personality",
        purpose="Ensure essay sounds genuinely like the student who wrote it",
        input_requirements=["paragraph_text", "voice_profile"],
        output_format="Voice-adjusted paragraph maintaining authenticity",
        when_to_use="When writing sounds generic or doesn't reflect student's personality",
        example_usage="Make this paragraph sound more like my natural voice",
        dependencies=["draft"],
        estimated_tokens=400,
        confidence_threshold=0.7
    ),

    # ====================================================================
    # EVALUATION TOOLS - Assessment and feedback
    # ====================================================================
    "essay_scoring": ToolDescription(
        name="essay_scoring",
        category="evaluation",
        description="Score essay on key criteria: clarity, insight, structure, voice, and prompt fit (0-10 each)",
        purpose="Provide objective assessment of essay quality across multiple dimensions",
        input_requirements=["complete_essay", "essay_prompt"],
        output_format="Detailed scores with explanations for each criterion",
        when_to_use="After drafting to assess overall essay quality and identify improvement areas",
        example_usage="Score my essay and tell me what needs improvement",
        dependencies=["draft"],
        estimated_tokens=600,
        confidence_threshold=0.8
    ),
    
    "weakness_highlight": ToolDescription(
        name="weakness_highlight",
        category="evaluation",
        description="Identify specific weak sentences, paragraphs, and structural issues with explanations",
        purpose="Pinpoint exactly what needs improvement in the essay",
        input_requirements=["essay_text"],
        output_format="List of specific weaknesses with locations and improvement suggestions",
        when_to_use="When needing detailed feedback on what specifically to fix",
        example_usage="Show me the weakest parts of my essay",
        dependencies=["draft"],
        estimated_tokens=500,
        confidence_threshold=0.7
    ),
    
    "cliche_detection": ToolDescription(
        name="cliche_detection",
        category="evaluation",
        description="Flag overused phrases, tropes, and generic college essay language",
        purpose="Ensure essay avoids common clichés that make it sound generic",
        input_requirements=["essay_text"],
        output_format="List of clichéd phrases with suggested alternatives",
        when_to_use="During revision to eliminate generic language and improve originality",
        example_usage="Check my essay for clichés and overused phrases",
        dependencies=["draft"],
        estimated_tokens=500,
        confidence_threshold=0.7
    ),

    # ----------------------------------------------------------------
    # CURSOR-STYLE TEXT SELECTION & REAL-TIME TOOLS (generic stubs)
    # ----------------------------------------------------------------
    # These tools rely on the unified prompt helper introduced in Section 3.2.
    # They share similar input/output patterns, so a concise description is
    # sufficient for reasoning and avoids noisy registry warnings.

    **{
        name: ToolDescription(
            name=name,
            category="cursor_tools",
            description=f"{name.replace('_', ' ').title()} – lightweight editor assistance for selected text.",
            purpose="Provide real-time improvements or insights on highlighted text inside the essay editor.",
            input_requirements=["selection", "instruction"],
            output_format="Dictionary with key specific to each tool (e.g., improved_text)",
            when_to_use="While the user is actively editing text and requests this specific assistance.",
            example_usage=f"{name} selection='I love CS' instruction='make formal'",
            dependencies=[],
            estimated_tokens=150,
            confidence_threshold=0.6,
        ) for name in [
            "modify_selection",
            "explain_selection",
            "improve_selection",
            "rewrite_selection",
            "expand_selection",
            "condense_selection",
            "replace_selection",
            "smart_autocomplete",
            "transition_helper",
            "voice_matcher",
            "live_feedback",
            "word_choice_optimizer",
            "authenticity_checker",
            "goal_tracker",
            "strategy_advisor",
        ]
    },

    # ----------------------------------------------------------------
    # Supplemental brainstorming helpers referenced in some workflows
    # ----------------------------------------------------------------
    "brainstorm_specific": ToolDescription(
        name="brainstorm_specific",
        category="brainstorming",
        description="Generate targeted story ideas tailored to a specific essay prompt or theme.",
        purpose="Help users quickly surface stories that match nuanced prompt requirements (e.g., diversity, community).",
        input_requirements=["essay_prompt", "profile"],
        output_format="List of Story objects with prompt_fit annotations",
        when_to_use="When the user requests brainstorming focused on a particular prompt angle.",
        example_usage="brainstorm_specific prompt='Stanford AI + entrepreneurship'",
        dependencies=[],
        estimated_tokens=700,
        confidence_threshold=0.75,
    ),

    "story_development": ToolDescription(
        name="story_development",
        category="brainstorming",
        description="Expand a chosen story idea into richer narrative details and key moments.",
        purpose="Fill out context, conflict, and resolution elements before outlining.",
        input_requirements=["story_title", "current_details"],
        output_format="Enhanced story object with vivid scenes and emotional beats",
        when_to_use="After selecting a brainstormed idea that needs more depth before outlining.",
        example_usage="story_development story_title='Robotics Club setback'",
        dependencies=["brainstorm"],
        estimated_tokens=600,
        confidence_threshold=0.7,
    ),

    "story_themes": ToolDescription(
        name="story_themes",
        category="brainstorming",
        description="Extract and list central themes present in a story idea or draft paragraph.",
        purpose="Help align story with essay prompt and personal values.",
        input_requirements=["story_text"],
        output_format="List of thematic keywords with short explanations",
        when_to_use="When evaluating which story best matches a prompt’s required themes.",
        example_usage="story_themes story_text='Building an AI project for the blind'",
        dependencies=["brainstorm"],
        estimated_tokens=300,
        confidence_threshold=0.65,
    ),
    
    "alignment_check": ToolDescription(
        name="alignment_check",
        category="evaluation",
        description="Verify that essay directly addresses all prompt requirements",
        purpose="Ensure essay fully responds to what the prompt is asking",
        input_requirements=["essay_text", "essay_prompt"],
        output_format="Analysis of prompt alignment with specific gaps identified",
        when_to_use="Before finalizing to ensure essay answers the prompt completely",
        example_usage="Check if my essay fully addresses the prompt requirements",
        dependencies=["draft"],
        estimated_tokens=400,
        confidence_threshold=0.8
    ),

    # ====================================================================
    # STRUCTURE TOOLS - Organization and flow
    # ====================================================================
    "outline_generator": ToolDescription(
        name="outline_generator",
        category="structure",
        description="Generate alternative outline structures based on essay type and story",
        purpose="Explore different ways to organize essay content effectively",
        input_requirements=["story_summary", "essay_type", "word_count"],
        output_format="Multiple outline options with pros/cons for each",
        when_to_use="When exploring different structural approaches for the same story",
        example_usage="Generate different outline structures for my leadership story",
        dependencies=["brainstorm"],
        estimated_tokens=500,
        confidence_threshold=0.7
    ),
    
    "structure_validator": ToolDescription(
        name="structure_validator",
        category="structure",
        description="Analyze outline's logical flow and emotional arc for effectiveness",
        purpose="Ensure story structure creates proper narrative progression",
        input_requirements=["outline"],
        output_format="Structural analysis with flow improvement suggestions",
        when_to_use="After outline creation to validate narrative progression",
        example_usage="Check if my outline has good logical flow",
        dependencies=["outline"],
        estimated_tokens=300,
        confidence_threshold=0.7
    ),
    
    "transition_suggestion": ToolDescription(
        name="transition_suggestion",
        category="structure",
        description="Generate smooth transitions between outline sections or paragraphs",
        purpose="Improve essay flow by connecting sections seamlessly",
        input_requirements=["section_1", "section_2", "context"],
        output_format="Transition sentences or phrases with explanations",
        when_to_use="During drafting when sections feel disconnected or choppy",
        example_usage="Create a smooth transition between these two paragraphs",
        dependencies=["outline"],
        estimated_tokens=200,
        confidence_threshold=0.6
    ),
    
    "length_optimizer": ToolDescription(
        name="length_optimizer",
        category="structure",
        description="Adjust outline proportions to fit specific word count requirements",
        purpose="Balance section lengths to meet word limits effectively",
        input_requirements=["outline", "target_word_count", "current_word_count"],
        output_format="Revised outline with adjusted section lengths",
        when_to_use="When essay is too long/short and needs structural rebalancing",
        example_usage="Adjust my outline to fit the 650 word limit",
        dependencies=["outline"],
        estimated_tokens=300,
        confidence_threshold=0.7
    ),

    # ====================================================================
    # BRAINSTORMING TOOLS - Story development and ideation
    # ====================================================================
    "suggest_stories": ToolDescription(
        name="suggest_stories",
        category="brainstorming",
        description="Generate additional story ideas based on user profile and specific themes",
        purpose="Expand story options when initial brainstorming needs more ideas",
        input_requirements=["user_profile", "theme_focus", "prompt_type"],
        output_format="Additional story suggestions with relevance explanations",
        when_to_use="When initial brainstorming didn't generate enough viable options",
        example_usage="Suggest more stories about overcoming challenges",
        dependencies=[],
        estimated_tokens=400,
        confidence_threshold=0.8
    ),
    
    "match_story": ToolDescription(
        name="match_story",
        category="brainstorming",
        description="Match existing user stories to specific essay prompts for best fit",
        purpose="Help select the most appropriate story for a particular prompt",
        input_requirements=["user_stories", "essay_prompt"],
        output_format="Story-prompt matches with fit scores and explanations",
        when_to_use="When user has multiple stories and needs to choose the best fit",
        example_usage="Which of my stories works best for this leadership prompt?",
        dependencies=["suggest_stories"],
        estimated_tokens=350,
        confidence_threshold=0.8
    ),
    
    "expand_story": ToolDescription(
        name="expand_story",
        category="brainstorming",
        description="Develop a story idea with more details, context, and potential insights",
        purpose="Transform basic story concepts into rich, detailed narratives",
        input_requirements=["story_concept", "essay_prompt"],
        output_format="Expanded story with details, context, and insight opportunities",
        when_to_use="After story selection when more detail is needed for outlining",
        example_usage="Help me develop more details for my volunteer story",
        dependencies=["suggest_stories"],
        estimated_tokens=500,
        confidence_threshold=0.7
    ),
    
    "validate_uniqueness": ToolDescription(
        name="validate_uniqueness",
        category="brainstorming",
        description="Check if story idea is distinctive and avoid common essay topics",
        purpose="Ensure chosen story stands out from typical college essay themes",
        input_requirements=["story_idea", "essay_type"],
        output_format="Uniqueness assessment with suggestions for differentiation",
        when_to_use="After story selection to ensure it's distinctive and memorable",
        example_usage="Is my volunteer story too common for college essays?",
        dependencies=["expand_story"],
        estimated_tokens=300,
        confidence_threshold=0.6
    ),

    # ====================================================================
    # PROMPT TOOLS - Prompt analysis and strategy
    # ====================================================================
    "classify_prompt": ToolDescription(
        name="classify_prompt",
        category="prompt_analysis",
        description="Categorize essay prompt type (challenge, growth, identity, etc.) and identify key requirements",
        purpose="Understand exactly what the prompt is asking for",
        input_requirements=["essay_prompt"],
        output_format="Prompt classification with key requirements and success criteria",
        when_to_use="At the start when analyzing a new essay prompt",
        example_usage="What type of prompt is this and what should I focus on?",
        dependencies=[],
        estimated_tokens=250,
        confidence_threshold=0.9
    ),
    
    "extract_requirements": ToolDescription(
        name="extract_requirements",
        category="prompt_analysis",
        description="Identify specific requirements, word limits, and evaluation criteria from prompt",
        purpose="Ensure all prompt requirements are understood and addressed",
        input_requirements=["essay_prompt", "application_context"],
        output_format="Detailed list of requirements with importance rankings",
        when_to_use="When analyzing complex prompts with multiple requirements",
        example_usage="What are all the requirements I need to address in this prompt?",
        dependencies=["classify_prompt"],
        estimated_tokens=200,
        confidence_threshold=0.8
    ),
    
    "suggest_strategy": ToolDescription(
        name="suggest_strategy",
        category="prompt_analysis",
        description="Recommend approach strategies based on prompt type and user profile",
        purpose="Provide strategic guidance for tackling specific prompt types",
        input_requirements=["prompt_type", "user_profile", "prompt_requirements"],
        output_format="Strategic recommendations with approach explanations",
        when_to_use="After prompt analysis when planning essay approach",
        example_usage="What's the best strategy for answering this leadership prompt?",
        dependencies=["classify_prompt"],
        estimated_tokens=300,
        confidence_threshold=0.7
    ),
    
    "detect_overlap": ToolDescription(
        name="detect_overlap",
        category="prompt_analysis",
        description="Identify overlap between multiple essay prompts to avoid repetition",
        purpose="Ensure diverse essay portfolio when applying to multiple schools",
        input_requirements=["multiple_prompts", "existing_essays"],
        output_format="Overlap analysis with differentiation suggestions",
        when_to_use="When working on multiple essays that might be too similar",
        example_usage="Are my essays for different schools too similar?",
        dependencies=["classify_prompt"],
        estimated_tokens=400,
        confidence_threshold=0.6
    ),

    # ====================================================================
    # POLISH TOOLS - Language and style refinement
    # ====================================================================
    "fix_grammar": ToolDescription(
        name="fix_grammar",
        category="polish",
        description="Correct grammar, spelling, punctuation, and basic style errors",
        purpose="Ensure essay is error-free and professionally written",
        input_requirements=["essay_text"],
        output_format="Corrected text with explanations for major changes",
        when_to_use="During final polishing to eliminate all language errors",
        example_usage="Fix any grammar and spelling errors in my essay",
        dependencies=["draft"],
        estimated_tokens=300,
        confidence_threshold=0.5
    ),
    
    "enhance_vocabulary": ToolDescription(
        name="enhance_vocabulary",
        category="polish",
        description="Suggest stronger, more precise vocabulary while maintaining authentic voice",
        purpose="Improve word choice without making language sound artificial",
        input_requirements=["text_section", "voice_profile"],
        output_format="Vocabulary suggestions with authenticity considerations",
        when_to_use="When language feels imprecise or needs more sophisticated expression",
        example_usage="Suggest better word choices for this paragraph",
        dependencies=["draft"],
        estimated_tokens=250,
        confidence_threshold=0.6
    ),
    
    "check_consistency": ToolDescription(
        name="check_consistency",
        category="polish",
        description="Verify tense, voice, style, and tone consistency throughout essay",
        purpose="Ensure essay maintains consistent writing style and voice",
        input_requirements=["complete_essay"],
        output_format="Consistency analysis with specific inconsistencies highlighted",
        when_to_use="During final review to ensure stylistic coherence",
        example_usage="Check my essay for tense and style consistency",
        dependencies=["draft"],
        estimated_tokens=300,
        confidence_threshold=0.6
    ),
    
    "optimize_word_count": ToolDescription(
        name="optimize_word_count",
        category="polish",
        description="Intelligently trim or expand text to meet exact word count requirements",
        purpose="Meet word limits while preserving essay quality and meaning",
        input_requirements=["essay_text", "target_word_count", "current_word_count"],
        output_format="Revised text meeting word count with change explanations",
        when_to_use="When essay is over/under word limit and needs precise adjustment",
        example_usage="Trim my essay to exactly 650 words",
        dependencies=["draft"],
        estimated_tokens=400,
        confidence_threshold=0.7
    ),

    # ====================================================================
    # VALIDATION TOOLS - Quality assurance and final checks
    # ====================================================================
    "plagiarism_check": ToolDescription(
        name="plagiarism_check",
        category="validation",
        description="Check for potential plagiarism and ensure content originality",
        purpose="Verify essay content is original and properly attributed",
        input_requirements=["essay_text"],
        output_format="Originality assessment with any concerns flagged",
        when_to_use="Before final submission to ensure content originality",
        example_usage="Check if my essay has any plagiarism issues",
        dependencies=["polish"],
        estimated_tokens=200,
        confidence_threshold=0.5
    ),
    
    "outline_alignment": ToolDescription(
        name="outline_alignment",
        category="validation",
        description="Verify final essay matches the planned outline structure",
        purpose="Ensure essay followed the intended structural plan",
        input_requirements=["final_essay", "original_outline"],
        output_format="Alignment analysis with deviations noted",
        when_to_use="After drafting to ensure structural integrity",
        example_usage="Does my final essay match the outline I created?",
        dependencies=["draft"],
        estimated_tokens=250,
        confidence_threshold=0.6
    ),
    
    "final_polish": ToolDescription(
        name="final_polish",
        category="validation",
        description="Comprehensive final review combining multiple quality checks",
        purpose="Final quality assurance before essay submission",
        input_requirements=["complete_essay", "essay_prompt"],
        output_format="Comprehensive quality report with final recommendations",
        when_to_use="As absolute final step before submitting essay",
        example_usage="Give my essay a final comprehensive review",
        dependencies=["polish"],
        estimated_tokens=500,
        confidence_threshold=0.5
    ),
    
    "comprehensive_validation": ToolDescription(
        name="comprehensive_validation",
        category="validation",
        description="Complete validation including prompt fit, structure, style, and technical quality",
        purpose="Thorough quality assessment across all essay dimensions",
        input_requirements=["essay_text", "essay_prompt", "requirements"],
        output_format="Detailed validation report with quality scores and recommendations",
        when_to_use="For thorough quality assurance of completed essays",
        example_usage="Run a complete quality check on my finished essay",
        dependencies=["final_polish"],
        estimated_tokens=600,
        confidence_threshold=0.6
    ),

    # ====================================================================
    # UTILITY TOOLS - Helper functions and diagnostics
    # ====================================================================
    "echo": ToolDescription(
        name="echo",
        category="utility",
        description="Simple echo tool for testing and debugging tool infrastructure",
        purpose="Verify tool system is working and test tool calling mechanisms",
        input_requirements=["message"],
        output_format="Echo of input message with system status",
        when_to_use="For system testing and debugging tool connectivity",
        example_usage="Echo hello world",
        dependencies=[],
        estimated_tokens=50,
        confidence_threshold=0.9
    ),
    
    "word_count": ToolDescription(
        name="word_count",
        category="utility",
        description="Count words, characters, and analyze text length statistics",
        purpose="Track essay length and ensure word count compliance",
        input_requirements=["text_content"],
        output_format="Detailed length statistics including word/character counts",
        when_to_use="When tracking essay length during writing process",
        example_usage="Count the words in my essay",
        dependencies=[],
        estimated_tokens=100,
        confidence_threshold=0.9
    ),
    
    "clarify": ToolDescription(
        name="clarify",
        category="utility",
        description="Ask clarifying questions when user request is ambiguous",
        purpose="Gather more specific information to provide better assistance",
        input_requirements=["unclear_request", "context"],
        output_format="Clarifying questions to better understand user needs",
        when_to_use="When user request is vague or could be interpreted multiple ways",
        example_usage="Help me improve my essay (needs clarification)",
        dependencies=[],
        estimated_tokens=150,
        confidence_threshold=0.8
    )
}


# Tool categories for organization
TOOL_CATEGORIES = {
    "core_workflow": ["brainstorm", "outline", "draft", "revise", "polish"],
    "writing": ["expand_outline_section", "rewrite_paragraph", "improve_opening", "strengthen_voice"],
    "evaluation": ["essay_scoring", "weakness_highlight", "cliche_detection", "alignment_check"],
    "structure": ["outline_generator", "structure_validator", "transition_suggestion", "length_optimizer"],
    "brainstorming": ["suggest_stories", "match_story", "expand_story", "validate_uniqueness"],
    "prompt_analysis": ["classify_prompt", "extract_requirements", "suggest_strategy", "detect_overlap"],
    "polish": ["fix_grammar", "enhance_vocabulary", "check_consistency", "optimize_word_count"],
    "validation": ["plagiarism_check", "outline_alignment", "final_polish", "comprehensive_validation"],
    "utility": ["echo", "word_count", "clarify"]
}


def get_tool_description(tool_name: str) -> ToolDescription:
    """Get description for a specific tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool description object
        
    Raises:
        KeyError: If tool not found
    """
    if tool_name not in TOOL_DESCRIPTIONS:
        raise KeyError(f"Tool '{tool_name}' not found in descriptions")
    return TOOL_DESCRIPTIONS[tool_name]


def get_tools_by_category(category: str) -> List[ToolDescription]:
    """Get all tool descriptions in a specific category.
    
    Args:
        category: Category name
        
    Returns:
        List of tool descriptions in that category
    """
    if category not in TOOL_CATEGORIES:
        return []
    
    return [TOOL_DESCRIPTIONS[tool_name] for tool_name in TOOL_CATEGORIES[category] 
            if tool_name in TOOL_DESCRIPTIONS]


def format_tools_for_llm(tools: List[ToolDescription] = None) -> str:
    """Format tool descriptions for LLM reasoning.
    
    Args:
        tools: Specific tools to format, or None for all tools
        
    Returns:
        Formatted string of tool descriptions
    """
    if tools is None:
        tools = list(TOOL_DESCRIPTIONS.values())
    
    formatted = []
    for tool in tools:
        tool_text = f"""
**{tool.name}** ({tool.category})
- Description: {tool.description}
- When to use: {tool.when_to_use}
- Requires: {', '.join(tool.input_requirements)}
- Output: {tool.output_format}
- Example: "{tool.example_usage}"
"""
        formatted.append(tool_text)
    
    return "\n".join(formatted)


def get_all_tool_names() -> List[str]:
    """Get list of all registered tool names."""
    return list(TOOL_DESCRIPTIONS.keys())


def get_category_list() -> List[str]:
    """Get list of all tool categories."""
    return list(TOOL_CATEGORIES.keys()) 