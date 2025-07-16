"""
Comprehensive conversational evaluation scenarios for the essay agent ReAct system.

This module contains 100 detailed scenarios testing the complete user journey
from essay prompt input to polished essay across different user types,
autonomy levels, and memory utilization patterns.
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum


class ScenarioCategory(Enum):
    """Categories for conversation scenarios."""
    NEW_USER = "new_user"
    RETURNING_USER = "returning_user"
    COMPLEX = "complex"
    EDGE_CASE = "edge_case"


# AutonomyLevel removed - simplified evaluation without autonomy tracking


@dataclass
class ConversationPhase:
    """Represents a phase in the conversation flow."""
    phase_name: str
    user_input: str
    expected_agent_behavior: str
    expected_tool_use: Optional[List[str]] = None
    expected_memory_use: Optional[List[str]] = None
    autonomy_check: Optional[str] = None
    success_indicators: Optional[List[str]] = None


@dataclass
class SuccessCriteria:
    """Success criteria for evaluating conversation outcomes."""
    conversation_turns: Dict[str, int]  # min, max
    tools_used: Dict[str, Any]  # min count, expected tools
    final_word_count: Dict[str, int]  # min, max
    prompt_relevance: Dict[str, float]  # min score
    conversation_quality: Dict[str, float]  # min scores for various aspects
    memory_utilization: Optional[Dict[str, float]] = None


@dataclass
class ConversationScenario:
    """Complete conversation scenario for evaluation."""
    eval_id: str
    name: str
    category: ScenarioCategory
    description: str
    school: str
    prompt: str
    word_limit: int
    user_profile: str
    conversation_flow: List[ConversationPhase]
    success_criteria: SuccessCriteria
    difficulty: Literal["easy", "medium", "hard"]
    estimated_duration_minutes: int
    tags: List[str]


# =============================================================================
# NEW USER SCENARIOS (25 scenarios)
# =============================================================================

NEW_USER_SCENARIOS = [
    # NEW USER BRAINSTORM (10 scenarios)
    ConversationScenario(
        eval_id="CONV-001-new-user-stanford-identity",
        name="New User - Stanford Identity Discovery",
        category=ScenarioCategory.NEW_USER,
        description="First-time user discovering their core values for Stanford 'What matters most' prompt",
        school="Stanford",
        prompt="What matters most to you, and why?",
        word_limit=250,
        user_profile="tech_entrepreneur_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="initial_request",
                user_input="I need help with my Stanford essay. The prompt is 'What matters most to you, and why?' and I'm not sure where to start.",
                expected_agent_behavior="prompt_analysis_and_brainstorm_offer",
                expected_tool_use=["analyze_prompt", "brainstorm"],
                success_indicators=["prompt_breakdown", "brainstorm_invitation"]
            ),
            ConversationPhase(
                phase_name="brainstorming", 
                user_input="Help me brainstorm what matters most to me",
                expected_agent_behavior="deep_values_exploration",
                expected_tool_use=["brainstorm"],
                expected_memory_use=["core_values", "defining_moments"],
                success_indicators=["multiple_value_options", "personal_connection"]
            ),
            ConversationPhase(
                phase_name="story_selection",
                user_input="I think I want to write about innovation and helping others through technology",
                expected_agent_behavior="story_development_and_outline_offer",
                expected_tool_use=["story_development", "outline"],
                success_indicators=["specific_story_examples", "structure_preview"]
            ),
            ConversationPhase(
                phase_name="drafting",
                user_input="Help me write a draft focusing on my robotics project that helped disabled students",
                expected_agent_behavior="collaborative_drafting",
                expected_tool_use=["draft_essay"],
                autonomy_check="collaborative",
                success_indicators=["personal_voice", "prompt_alignment"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 5, "max": 12},
            tools_used={"min": 3, "expected": ["brainstorm", "outline", "draft_essay"]},
            final_word_count={"min": 225, "max": 275},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.5}
        ),
        difficulty="medium",
        estimated_duration_minutes=8,
        tags=["brainstorming", "values", "technology", "stanford"]
    ),

    ConversationScenario(
        eval_id="CONV-002-new-user-harvard-diversity",
        name="New User - Harvard Diversity Essay",
        category=ScenarioCategory.NEW_USER,
        description="New user exploring their unique background for Harvard diversity prompt",
        school="Harvard",
        prompt="Harvard has long recognized the importance of student body diversity. How will the life experiences that shape who you are today enable you to contribute to Harvard?",
        word_limit=150,
        user_profile="first_gen_immigrant_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="initial_uncertainty",
                user_input="I'm working on my Harvard diversity essay but I don't know if my background is interesting enough.",
                expected_agent_behavior="confidence_building_and_story_exploration",
                expected_tool_use=["brainstorm_specific"],
                success_indicators=["validation", "story_prompting"]
            ),
            ConversationPhase(
                phase_name="background_exploration",
                user_input="My family immigrated from Vietnam when I was 10, and I've had to translate for my parents a lot",
                expected_agent_behavior="deep_story_development",
                expected_tool_use=["story_development", "story_themes"],
                success_indicators=["unique_perspective_highlight", "contribution_connection"]
            ),
            ConversationPhase(
                phase_name="contribution_focus",
                user_input="How do I connect this to how I'll contribute to Harvard?",
                expected_agent_behavior="contribution_brainstorming",
                expected_tool_use=["brainstorm_specific"],
                success_indicators=["specific_contributions", "harvard_connection"]
            ),
            ConversationPhase(
                phase_name="concise_drafting",
                user_input="Help me write this concisely - only 150 words is tough",
                expected_agent_behavior="concise_drafting_assistance",
                expected_tool_use=["draft_essay", "check_word_count"],
                success_indicators=["word_efficiency", "impact_maximization"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 3, "expected": ["brainstorm_specific", "story_development", "draft_essay"]},
            final_word_count={"min": 135, "max": 165},
            prompt_relevance={"min": 4.5},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.5}
        ),
        difficulty="medium",
        estimated_duration_minutes=7,
        tags=["diversity", "immigration", "contribution", "harvard", "concise"]
    ),

    ConversationScenario(
        eval_id="CONV-003-new-user-common-app-challenge",
        name="New User - Common App Challenge Essay",
        category=ScenarioCategory.NEW_USER,
        description="New user identifying and developing a challenge story for Common App",
        school="Common App",
        prompt="The lessons we take from obstacles we encounter can be fundamental to later success. Recount a time when you faced a challenge, setback, or failure. How did it affect you, and what did you learn from the experience?",
        word_limit=650,
        user_profile="athlete_academic_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="challenge_identification",
                user_input="I need to write about a challenge for Common App. I've had a few setbacks but I'm not sure which one would make the best essay.",
                expected_agent_behavior="challenge_exploration_and_comparison",
                expected_tool_use=["brainstorm", "story_analysis"],
                success_indicators=["multiple_options", "story_potential_assessment"]
            ),
            ConversationPhase(
                phase_name="story_selection",
                user_input="I'm thinking about when I tore my ACL junior year and couldn't play soccer, which was my whole identity. Or maybe when I failed my first calculus test.",
                expected_agent_behavior="story_comparison_and_guidance",
                expected_tool_use=["story_analysis"],
                success_indicators=["story_strengths_analysis", "selection_guidance"]
            ),
            ConversationPhase(
                phase_name="story_development",
                user_input="Let's go with the ACL injury. It really changed how I see myself and opened up other interests.",
                expected_agent_behavior="deep_story_development",
                expected_tool_use=["story_development", "story_themes"],
                success_indicators=["specific_details", "growth_identification"]
            ),
            ConversationPhase(
                phase_name="structure_planning",
                user_input="How should I structure this essay to show the journey from injury to discovery?",
                expected_agent_behavior="structure_guidance",
                expected_tool_use=["outline", "structure_essay"],
                success_indicators=["clear_narrative_arc", "lesson_integration"]
            ),
            ConversationPhase(
                phase_name="drafting_assistance",
                user_input="Help me write a compelling opening that draws the reader in",
                expected_agent_behavior="opening_crafting",
                expected_tool_use=["strengthen_opening", "draft_essay"],
                success_indicators=["engaging_hook", "scene_setting"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 6, "max": 15},
            tools_used={"min": 4, "expected": ["brainstorm", "story_development", "outline", "draft_essay"]},
            final_word_count={"min": 600, "max": 700},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=12,
        tags=["challenge", "sports", "growth", "common_app", "narrative"]
    ),

    ConversationScenario(
        eval_id="CONV-004-new-user-mit-stem-passion",
        name="New User - MIT STEM Passion Discovery",
        category=ScenarioCategory.NEW_USER,
        description="New user exploring their passion for STEM and making for MIT",
        school="MIT",
        prompt="Tell us about something you do simply for the pleasure of it.",
        word_limit=200,
        user_profile="maker_engineer_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="passion_exploration",
                user_input="I love building things and coding, but I'm not sure how to make that sound interesting for this MIT prompt about pleasure.",
                expected_agent_behavior="passion_deepening_and_specificity",
                expected_tool_use=["brainstorm", "story_development"],
                success_indicators=["specific_examples", "joy_identification"]
            ),
            ConversationPhase(
                phase_name="story_selection",
                user_input="I guess what I really love is the moment when code finally works, or when I figure out why a circuit isn't working. Like last week I spent 6 hours debugging a robot and when it finally moved, I literally jumped up and cheered.",
                expected_agent_behavior="moment_amplification",
                expected_tool_use=["story_development"],
                success_indicators=["emotional_connection", "specific_details"]
            ),
            ConversationPhase(
                phase_name="mit_connection",
                user_input="How do I connect this to MIT without being too obvious?",
                expected_agent_behavior="authentic_connection_guidance",
                expected_tool_use=["enhance_voice"],
                success_indicators=["natural_fit", "authenticity_maintenance"]
            ),
            ConversationPhase(
                phase_name="concise_drafting",
                user_input="Help me capture that debugging joy in 200 words",
                expected_agent_behavior="concise_vivid_writing",
                expected_tool_use=["draft_essay", "check_word_count"],
                success_indicators=["vivid_imagery", "emotion_conveyance"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 3, "expected": ["brainstorm", "story_development", "draft_essay"]},
            final_word_count={"min": 180, "max": 220},
            prompt_relevance={"min": 4.5},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.5}
        ),
        difficulty="medium",
        estimated_duration_minutes=8,
        tags=["passion", "stem", "making", "mit", "joy"]
    ),

    ConversationScenario(
        eval_id="CONV-005-new-user-yale-community",
        name="New User - Yale Community Impact Essay",
        category=ScenarioCategory.NEW_USER,
        description="New user developing community service story for Yale",
        school="Yale",
        prompt="What is something about you that is not on the rest of your application?",
        word_limit=200,
        user_profile="community_organizer_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="hidden_story_search",
                user_input="I'm struggling with this Yale prompt. Most of my community work is already in my activities list. What else could I write about?",
                expected_agent_behavior="hidden_story_exploration",
                expected_tool_use=["brainstorm", "story_development"],
                success_indicators=["unique_angle_discovery", "personal_side_exploration"]
            ),
            ConversationPhase(
                phase_name="personal_discovery",
                user_input="Well, I started organizing because I was actually really shy in middle school. Most people don't know that about me.",
                expected_agent_behavior="transformation_story_development",
                expected_tool_use=["story_development", "story_themes"],
                success_indicators=["transformation_highlight", "vulnerability_exploration"]
            ),
            ConversationPhase(
                phase_name="story_refinement",
                user_input="How do I show this transformation without making it sound like a before/after story?",
                expected_agent_behavior="nuanced_storytelling_guidance",
                expected_tool_use=["enhance_voice", "story_development"],
                success_indicators=["complexity_maintenance", "authentic_voice"]
            ),
            ConversationPhase(
                phase_name="yale_alignment",
                user_input="Help me write this in a way that shows how this hidden part of me would contribute to Yale",
                expected_agent_behavior="contribution_integration",
                expected_tool_use=["draft_essay"],
                success_indicators=["yale_connection", "contribution_clarity"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 3, "expected": ["brainstorm", "story_development", "draft_essay"]},
            final_word_count={"min": 180, "max": 220},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=8,
        tags=["hidden_story", "transformation", "community", "yale", "vulnerability"]
    ),

    ConversationScenario(
        eval_id="CONV-006-new-user-princeton-growth",
        name="New User - Princeton Growth Mindset Essay",
        category=ScenarioCategory.NEW_USER,
        description="New user exploring intellectual growth for Princeton",
        school="Princeton",
        prompt="Tell us how you have changed in the last three years.",
        word_limit=300,
        user_profile="academic_researcher_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="change_identification",
                user_input="I'm working on Princeton's essay about how I've changed. I feel like I've grown a lot intellectually but I'm not sure how to show that.",
                expected_agent_behavior="growth_exploration",
                expected_tool_use=["brainstorm", "story_development"],
                success_indicators=["specific_changes", "evidence_gathering"]
            ),
            ConversationPhase(
                phase_name="concrete_examples",
                user_input="I used to just accept what teachers told me, but now I question everything and do my own research. Like in AP Bio, I didn't just memorize - I designed my own experiments.",
                expected_agent_behavior="example_development",
                expected_tool_use=["story_development"],
                success_indicators=["specific_evidence", "growth_demonstration"]
            ),
            ConversationPhase(
                phase_name="pattern_recognition",
                user_input="This questioning approach has carried over to other areas too - debate, volunteering, even friendships.",
                expected_agent_behavior="pattern_amplification",
                expected_tool_use=["story_themes"],
                success_indicators=["growth_pattern", "holistic_development"]
            ),
            ConversationPhase(
                phase_name="future_implications",
                user_input="How do I connect this growth to what I want to do at Princeton?",
                expected_agent_behavior="future_vision_integration",
                expected_tool_use=["draft_essay"],
                success_indicators=["princeton_alignment", "future_trajectory"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 12},
            tools_used={"min": 3, "expected": ["brainstorm", "story_development", "draft_essay"]},
            final_word_count={"min": 270, "max": 330},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=10,
        tags=["growth", "intellectual_development", "research", "princeton", "change"]
    ),

    ConversationScenario(
        eval_id="CONV-007-new-user-columbia-diversity",
        name="New User - Columbia Diversity of Thought",
        category=ScenarioCategory.NEW_USER,
        description="New user exploring unique perspective for Columbia",
        school="Columbia",
        prompt="What attracts you to your intended major?",
        word_limit=300,
        user_profile="interdisciplinary_thinker_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="major_uncertainty",
                user_input="I'm interested in economics but also psychology and computer science. How do I write about a major when I'm not 100% sure?",
                expected_agent_behavior="interdisciplinary_exploration",
                expected_tool_use=["brainstorm"],
                success_indicators=["connection_finding", "interdisciplinary_value"]
            ),
            ConversationPhase(
                phase_name="connection_discovery",
                user_input="I guess what I really love is understanding human behavior, especially in markets and online spaces.",
                expected_agent_behavior="theme_development",
                expected_tool_use=["story_development", "story_themes"],
                success_indicators=["theme_clarity", "passion_identification"]
            ),
            ConversationPhase(
                phase_name="columbia_fit",
                user_input="How do I show that Columbia is the right place for this interdisciplinary interest?",
                expected_agent_behavior="school_fit_exploration",
                expected_tool_use=["brainstorm_specific"],
                success_indicators=["columbia_resources", "fit_demonstration"]
            ),
            ConversationPhase(
                phase_name="cohesive_narrative",
                user_input="Help me write this so it sounds focused even though I'm combining multiple interests",
                expected_agent_behavior="narrative_coherence",
                expected_tool_use=["draft_essay", "structure_essay"],
                success_indicators=["coherent_vision", "focused_passion"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 3, "expected": ["brainstorm", "story_development", "draft_essay"]},
            final_word_count={"min": 270, "max": 330},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=9,
        tags=["major_selection", "interdisciplinary", "economics", "columbia", "passion"]
    ),

    ConversationScenario(
        eval_id="CONV-008-new-user-duke-leadership",
        name="New User - Duke Leadership Development",
        category=ScenarioCategory.NEW_USER,
        description="New user exploring leadership growth for Duke",
        school="Duke",
        prompt="We seek a talented, engaged student body that embodies the wide range of human experience. Please share with us something about you not yet reflected in your application.",
        word_limit=250,
        user_profile="emerging_leader_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="hidden_leadership",
                user_input="I don't have traditional leadership titles, so I'm not sure what to share for this Duke prompt about something not in my application.",
                expected_agent_behavior="leadership_redefinition",
                expected_tool_use=["brainstorm"],
                success_indicators=["broader_leadership_view", "hidden_story_discovery"]
            ),
            ConversationPhase(
                phase_name="informal_leadership",
                user_input="I guess I'm the person my friends always come to for advice, and I helped organize our grade's response to the cafeteria food quality issue.",
                expected_agent_behavior="informal_leadership_validation",
                expected_tool_use=["story_development"],
                success_indicators=["leadership_recognition", "impact_identification"]
            ),
            ConversationPhase(
                phase_name="leadership_style",
                user_input="I don't like being in the spotlight, but I'm good at bringing people together and finding solutions everyone can agree on.",
                expected_agent_behavior="leadership_style_exploration",
                expected_tool_use=["story_themes", "enhance_voice"],
                success_indicators=["style_clarity", "strength_identification"]
            ),
            ConversationPhase(
                phase_name="duke_contribution",
                user_input="How do I show Duke that this behind-the-scenes leadership style would be valuable?",
                expected_agent_behavior="contribution_articulation",
                expected_tool_use=["draft_essay"],
                success_indicators=["value_demonstration", "duke_alignment"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 3, "expected": ["brainstorm", "story_development", "draft_essay"]},
            final_word_count={"min": 225, "max": 275},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=8,
        tags=["leadership", "informal_leadership", "collaboration", "duke", "hidden_strength"]
    ),

    ConversationScenario(
        eval_id="CONV-009-new-user-northwestern-why",
        name="New User - Northwestern Why School Essay",
        category=ScenarioCategory.NEW_USER,
        description="New user developing specific reasons for choosing Northwestern",
        school="Northwestern",
        prompt="What are the unique qualities of Northwestern - and of the specific undergraduate school to which you are applying - that make you want to attend the University?",
        word_limit=300,
        user_profile="journalism_communications_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="generic_reasons",
                user_input="I want to apply to Northwestern for journalism, but I'm struggling to go beyond the obvious reasons like 'great journalism program' and 'near Chicago.'",
                expected_agent_behavior="specificity_guidance",
                expected_tool_use=["brainstorm_specific"],
                success_indicators=["specific_research_needed", "uniqueness_emphasis"]
            ),
            ConversationPhase(
                phase_name="specific_research",
                user_input="I did some research and I'm really interested in the Knight Lab and their work on media innovation. Also the Medill-DC program.",
                expected_agent_behavior="connection_deepening",
                expected_tool_use=["story_development"],
                success_indicators=["personal_connection", "specific_goals"]
            ),
            ConversationPhase(
                phase_name="personal_goals",
                user_input="I want to work on making news more accessible to young people through technology, and Northwestern seems perfect for combining journalism and innovation.",
                expected_agent_behavior="goal_alignment_amplification",
                expected_tool_use=["story_themes"],
                success_indicators=["clear_vision", "northwestern_fit"]
            ),
            ConversationPhase(
                phase_name="authentic_enthusiasm",
                user_input="How do I show genuine excitement without sounding like I'm just repeating their website?",
                expected_agent_behavior="authentic_voice_development",
                expected_tool_use=["draft_essay", "enhance_voice"],
                success_indicators=["personal_voice", "authentic_enthusiasm"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 3, "expected": ["brainstorm_specific", "story_development", "draft_essay"]},
            final_word_count={"min": 270, "max": 330},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=9,
        tags=["why_school", "journalism", "research", "northwestern", "specificity"]
    ),

    ConversationScenario(
        eval_id="CONV-010-new-user-brown-open",
        name="New User - Brown Open Curriculum Essay",
        category=ScenarioCategory.NEW_USER,
        description="New user exploring intellectual curiosity for Brown's open curriculum",
        school="Brown",
        prompt="Why are you drawn to the academic fields you indicated in your application?",
        word_limit=200,
        user_profile="curious_learner_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="curiosity_exploration",
                user_input="I listed several different fields on my Brown application because I'm genuinely curious about so many things. How do I explain this without seeming unfocused?",
                expected_agent_behavior="curiosity_validation",
                expected_tool_use=["brainstorm"],
                success_indicators=["curiosity_value", "connection_seeking"]
            ),
            ConversationPhase(
                phase_name="connection_finding",
                user_input="I'm interested in neuroscience, philosophy, and creative writing. They seem unrelated but to me they're all about understanding consciousness and human experience.",
                expected_agent_behavior="connection_amplification",
                expected_tool_use=["story_themes"],
                success_indicators=["theme_identification", "intellectual_coherence"]
            ),
            ConversationPhase(
                phase_name="brown_fit",
                user_input="This is exactly why I love Brown's open curriculum - I can explore all these connections.",
                expected_agent_behavior="brown_alignment",
                expected_tool_use=["story_development"],
                success_indicators=["brown_understanding", "curriculum_appreciation"]
            ),
            ConversationPhase(
                phase_name="concise_synthesis",
                user_input="Help me synthesize this into 200 words that shows my intellectual curiosity without rambling",
                expected_agent_behavior="concise_synthesis",
                expected_tool_use=["draft_essay", "check_word_count"],
                success_indicators=["coherent_curiosity", "brown_alignment"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 3, "expected": ["brainstorm", "story_themes", "draft_essay"]},
            final_word_count={"min": 180, "max": 220},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=8,
        tags=["intellectual_curiosity", "open_curriculum", "interdisciplinary", "brown", "synthesis"]
    ),

    # NEW USER GUIDED (8 scenarios)
    ConversationScenario(
        eval_id="CONV-011-new-user-step-by-step",
        name="New User - Complete Step-by-Step Guidance",
        category=ScenarioCategory.NEW_USER,
        description="Completely new user needing guidance through every step of essay writing",
        school="UC System",
        prompt="Describe how you have taken advantage of a significant educational opportunity or worked to overcome an educational barrier you have faced.",
        word_limit=350,
        user_profile="first_gen_college_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="overwhelmed_start",
                user_input="I have no idea how to write a college essay. Can you help me with this UC prompt? I don't even know where to start.",
                expected_agent_behavior="comprehensive_guidance_offer",
                expected_tool_use=["analyze_prompt"],
                success_indicators=["step_by_step_plan", "reassurance", "prompt_breakdown"]
            ),
            ConversationPhase(
                phase_name="prompt_understanding",
                user_input="Ok, so I need to write about an educational opportunity or barrier. What counts as each of those?",
                expected_agent_behavior="concept_clarification",
                expected_tool_use=["clarify"],
                success_indicators=["clear_definitions", "examples_provided"]
            ),
            ConversationPhase(
                phase_name="experience_identification",
                user_input="I started a tutoring program at my school because a lot of kids were struggling like I was. Does that count?",
                expected_agent_behavior="validation_and_development",
                expected_tool_use=["story_development"],
                success_indicators=["story_validation", "development_questions"]
            ),
            ConversationPhase(
                phase_name="structure_learning",
                user_input="How should I organize this essay? I've never written anything this important before.",
                expected_agent_behavior="structure_teaching",
                expected_tool_use=["outline", "structure_essay"],
                success_indicators=["clear_structure", "writing_confidence"]
            ),
            ConversationPhase(
                phase_name="drafting_support",
                user_input="Can you help me start writing? I'm nervous about getting the tone right.",
                expected_agent_behavior="drafting_guidance",
                expected_tool_use=["write_introduction", "enhance_voice"],
                success_indicators=["writing_start", "tone_guidance"]
            ),
            ConversationPhase(
                phase_name="revision_learning",
                user_input="I wrote a draft but I don't know if it's good. How do I make it better?",
                expected_agent_behavior="revision_teaching",
                expected_tool_use=["provide_feedback", "suggest_improvements"],
                success_indicators=["constructive_feedback", "revision_strategies"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 8, "max": 18},
            tools_used={"min": 5, "expected": ["analyze_prompt", "story_development", "outline", "write_introduction", "provide_feedback"]},
            final_word_count={"min": 320, "max": 380},
            prompt_relevance={"min": 3.5},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.5, "educational_value": 4.5}
        ),
        difficulty="easy",
        estimated_duration_minutes=15,
        tags=["beginner", "step_by_step", "educational", "uc_system", "tutoring"]
    ),

    ConversationScenario(
        eval_id="CONV-012-new-user-process-learning",
        name="New User - Learning Essay Writing Process",
        category=ScenarioCategory.NEW_USER,
        description="New user learning the essay writing process through guided practice",
        school="State University",
        prompt="Tell us about a person who has influenced you in a significant way.",
        word_limit=500,
        user_profile="rural_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="process_question",
                user_input="I need to write about someone who influenced me. Should I just start writing or is there a process I should follow?",
                expected_agent_behavior="process_education",
                expected_tool_use=["plan_essay"],
                success_indicators=["process_explanation", "planning_emphasis"]
            ),
            ConversationPhase(
                phase_name="brainstorming_practice",
                user_input="Ok, let's brainstorm. I'm thinking about my high school librarian who helped me discover my love of reading.",
                expected_agent_behavior="brainstorming_facilitation",
                expected_tool_use=["brainstorm", "story_development"],
                success_indicators=["story_expansion", "detail_gathering"]
            ),
            ConversationPhase(
                phase_name="organization_learning",
                user_input="I have lots of ideas about Mrs. Chen but I don't know how to organize them into an essay.",
                expected_agent_behavior="organization_teaching",
                expected_tool_use=["organize_content", "outline"],
                success_indicators=["organization_strategies", "clear_outline"]
            ),
            ConversationPhase(
                phase_name="writing_practice",
                user_input="Can you give me tips on how to start writing from this outline?",
                expected_agent_behavior="writing_strategy_teaching",
                expected_tool_use=["write_introduction"],
                success_indicators=["writing_strategies", "confidence_building"]
            ),
            ConversationPhase(
                phase_name="self_evaluation",
                user_input="I wrote a paragraph but I don't know if it's good. How can I tell?",
                expected_agent_behavior="self_evaluation_teaching",
                expected_tool_use=["provide_feedback"],
                success_indicators=["evaluation_criteria", "self_assessment_skills"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 6, "max": 15},
            tools_used={"min": 4, "expected": ["plan_essay", "brainstorm", "outline", "write_introduction"]},
            final_word_count={"min": 450, "max": 550},
            prompt_relevance={"min": 3.5},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.0, "educational_value": 4.5}
        ),
        difficulty="easy",
        estimated_duration_minutes=12,
        tags=["process_learning", "guidance", "influence", "state_university", "mentorship"]
    ),

    # Continue with more NEW USER scenarios...
    # [Additional scenarios CONV-013 through CONV-025 would follow similar patterns]

    # NEW USER AUTONOMY (7 scenarios)
    ConversationScenario(
        eval_id="CONV-018-new-user-full-agent",
        name="New User - Full Agent Autonomy",
        category=ScenarioCategory.NEW_USER,
        description="New user preferring agent to handle most of the writing process",
        school="Liberal Arts College",
        prompt="What work of art, music, science, mathematics, or literature has surprised, unsettled, or challenged you, and in what way?",
        word_limit=200,
        user_profile="busy_achiever_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="delegation_request",
                user_input="I'm really swamped with AP exams and need help with this essay. Can you mostly write it for me if I give you the basic idea?",
                expected_agent_behavior="autonomy_clarification_and_collaboration_setup",
                expected_tool_use=["clarify"],
                success_indicators=["autonomy_understanding", "collaboration_framework"]
            ),
            ConversationPhase(
                phase_name="content_gathering",
                user_input="I want to write about how reading 'The Handmaid's Tale' in English class really disturbed me and made me think about women's rights in new ways.",
                expected_agent_behavior="detailed_content_extraction",
                expected_tool_use=["story_development", "story_themes"],
                success_indicators=["rich_content_gathering", "personal_connection_identification"]
            ),
            ConversationPhase(
                phase_name="agent_drafting",
                user_input="Great, can you write a draft using that information? I trust your judgment on structure and style.",
                expected_agent_behavior="comprehensive_drafting",
                expected_tool_use=["draft_essay", "structure_essay"],
                success_indicators=["complete_draft", "personal_voice_maintenance"]
            ),
            ConversationPhase(
                phase_name="approval_and_refinement",
                user_input="This is really good! Can you just adjust the ending to be a bit more personal?",
                expected_agent_behavior="targeted_refinement",
                expected_tool_use=["write_conclusion", "enhance_voice"],
                success_indicators=["personalization", "user_satisfaction"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 8},
            tools_used={"min": 4, "expected": ["story_development", "draft_essay", "structure_essay", "enhance_voice"]},
            final_word_count={"min": 180, "max": 220},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.5}
        ),
        difficulty="easy",
        estimated_duration_minutes=6,
        tags=["full_agent", "literature", "autonomy", "liberal_arts", "efficiency"]
    )
]

# =============================================================================
# RETURNING USER SCENARIOS (25 scenarios)
# =============================================================================

RETURNING_USER_SCENARIOS = [
    # MEMORY REUSE (10 scenarios)
    ConversationScenario(
        eval_id="CONV-026-returning-user-memory-leverage",
        name="Returning User - Leveraging Rich Profile",
        category=ScenarioCategory.RETURNING_USER,
        description="Returning user with extensive profile wanting to write new essay using previous content",
        school="Ivy League",
        prompt="Describe a topic, idea, or concept you find so engaging that it makes you lose all track of time.",
        word_limit=650,
        user_profile="returning_stem_researcher_with_rich_history",
        conversation_flow=[
            ConversationPhase(
                phase_name="memory_recognition",
                user_input="Hey! I'm back to work on my Ivy League essays. I remember we worked on my robotics stories before - can we use some of that for this new prompt about engaging topics?",
                expected_agent_behavior="memory_retrieval_and_connection",
                expected_tool_use=["story_development"],
                expected_memory_use=["previous_essays", "robotics_experiences", "core_interests"],
                success_indicators=["memory_recognition", "connection_identification"]
            ),
            ConversationPhase(
                phase_name="story_adaptation",
                user_input="I want to focus on how I get lost in coding for hours, but I don't want to repeat what I wrote for my Common App essay.",
                expected_agent_behavior="differentiation_strategy",
                expected_tool_use=["story_analysis", "generate_alternatives"],
                expected_memory_use=["previous_essay_content"],
                success_indicators=["unique_angle", "story_differentiation"]
            ),
            ConversationPhase(
                phase_name="deep_exploration",
                user_input="Let's explore the psychological aspect - why coding makes me lose track of time compared to other activities.",
                expected_agent_behavior="psychological_exploration",
                expected_tool_use=["story_themes", "story_development"],
                success_indicators=["deeper_insight", "psychological_analysis"]
            ),
            ConversationPhase(
                phase_name="integration_drafting",
                user_input="Help me write this incorporating insights from our previous conversations but making it fresh.",
                expected_agent_behavior="integrated_drafting",
                expected_tool_use=["draft_essay"],
                expected_memory_use=["writing_style_preferences", "voice_patterns"],
                success_indicators=["memory_integration", "fresh_perspective"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 4, "expected": ["story_development", "story_analysis", "story_themes", "draft_essay"]},
            final_word_count={"min": 600, "max": 700},
            prompt_relevance={"min": 4.5},
            conversation_quality={"naturalness": 4.5, "goal_achievement": 4.5},
            memory_utilization={"profile_usage": 4.0, "story_adaptation": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=10,
        tags=["memory_reuse", "story_adaptation", "coding", "psychology", "returning_user"]
    ),

    ConversationScenario(
        eval_id="CONV-027-returning-user-activity-leverage",
        name="Returning User - Activity Database Utilization",
        category=ScenarioCategory.RETURNING_USER,
        description="Returning user leveraging stored activities for new essay angle",
        school="Stanford",
        prompt="What matters most to you, and why?",
        word_limit=250,
        user_profile="returning_community_leader_with_activities",
        conversation_flow=[
            ConversationPhase(
                phase_name="activity_exploration",
                user_input="I'm working on Stanford's 'what matters most' prompt. Can you remind me what activities we've discussed before? I want to find a new angle.",
                expected_agent_behavior="activity_database_review",
                expected_tool_use=["brainstorm"],
                expected_memory_use=["activities_list", "defining_moments"],
                success_indicators=["activity_recall", "new_angle_seeking"]
            ),
            ConversationPhase(
                phase_name="value_extraction",
                user_input="Looking at my tutoring work and environmental club leadership, I think what really matters to me is creating spaces where people can grow.",
                expected_agent_behavior="value_theme_development",
                expected_tool_use=["story_themes", "story_development"],
                expected_memory_use=["leadership_experiences"],
                success_indicators=["value_identification", "theme_connection"]
            ),
            ConversationPhase(
                phase_name="story_selection",
                user_input="I want to focus on how I transformed our school's environmental club from a small group to a real force for change.",
                expected_agent_behavior="story_development_with_memory",
                expected_tool_use=["story_development"],
                expected_memory_use=["environmental_club_details", "leadership_growth"],
                success_indicators=["specific_story_development", "growth_demonstration"]
            ),
            ConversationPhase(
                phase_name="stanford_connection",
                user_input="How do I connect this value of 'creating growth spaces' to Stanford specifically?",
                expected_agent_behavior="stanford_alignment",
                expected_tool_use=["draft_essay"],
                success_indicators=["stanford_connection", "value_integration"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 10},
            tools_used={"min": 3, "expected": ["brainstorm", "story_themes", "draft_essay"]},
            final_word_count={"min": 225, "max": 275},
            prompt_relevance={"min": 4.5},
            conversation_quality={"naturalness": 4.5, "goal_achievement": 4.5},
            memory_utilization={"activity_usage": 4.5, "theme_development": 4.0}
        ),
        difficulty="medium",
        estimated_duration_minutes=8,
        tags=["activity_leverage", "values", "leadership", "stanford", "growth"]
    ),

    # Continue with additional RETURNING USER scenarios...
    # [Scenarios CONV-028 through CONV-050 would follow similar patterns]
]

# =============================================================================
# COMPLEX SCENARIOS (25 scenarios)
# =============================================================================

COMPLEX_SCENARIOS = [
    # MULTI-TOOL WORKFLOWS (10 scenarios)
    ConversationScenario(
        eval_id="CONV-051-complex-iterative-refinement",
        name="Complex - Iterative Essay Refinement",
        category=ScenarioCategory.COMPLEX,
        description="Complex iterative refinement process using multiple tools and feedback cycles",
        school="Harvard",
        prompt="Harvard has long recognized the importance of student body diversity. How will the life experiences that shape who you are today enable you to contribute to Harvard?",
        word_limit=150,
        user_profile="perfectionist_with_complex_background",
        conversation_flow=[
            ConversationPhase(
                phase_name="initial_draft_analysis",
                user_input="I have a draft for my Harvard diversity essay but I feel like it's not capturing the depth of my experience. Can you help me analyze what's missing?",
                expected_agent_behavior="comprehensive_analysis",
                expected_tool_use=["analyze_essay", "provide_feedback"],
                success_indicators=["detailed_analysis", "improvement_areas"]
            ),
            ConversationPhase(
                phase_name="structural_reimagining",
                user_input="You're right, the structure doesn't highlight my unique perspective effectively. Let's completely restructure this.",
                expected_agent_behavior="structural_overhaul",
                expected_tool_use=["assess_narrative_structure", "structure_essay", "outline"],
                success_indicators=["structural_innovation", "perspective_clarity"]
            ),
            ConversationPhase(
                phase_name="voice_enhancement",
                user_input="The new structure is better but my voice still doesn't feel authentic. How can I make it more personal?",
                expected_agent_behavior="voice_development",
                expected_tool_use=["enhance_voice", "refine_word_choice"],
                success_indicators=["authentic_voice", "personal_tone"]
            ),
            ConversationPhase(
                phase_name="precision_editing",
                user_input="I love the voice now but I'm 20 words over the 150 limit. Help me cut without losing impact.",
                expected_agent_behavior="precision_editing",
                expected_tool_use=["check_word_count", "polish_language", "final_edit"],
                success_indicators=["word_efficiency", "impact_maintenance"]
            ),
            ConversationPhase(
                phase_name="final_validation",
                user_input="Let's do one final check - does this essay truly answer Harvard's question about contribution?",
                expected_agent_behavior="comprehensive_validation",
                expected_tool_use=["evaluate_prompt_response", "score_essay"],
                success_indicators=["prompt_alignment", "contribution_clarity"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 6, "max": 15},
            tools_used={"min": 7, "expected": ["analyze_essay", "structure_essay", "enhance_voice", "check_word_count", "evaluate_prompt_response"]},
            final_word_count={"min": 145, "max": 155},
            prompt_relevance={"min": 4.5},
            conversation_quality={"naturalness": 4.5, "goal_achievement": 4.5, "iterative_improvement": 4.5}
        ),
        difficulty="hard",
        estimated_duration_minutes=18,
        tags=["iterative_refinement", "perfectionist", "harvard", "diversity", "precision"]
    ),

    # Continue with additional COMPLEX scenarios...
    # [Scenarios CONV-052 through CONV-075 would follow similar patterns]
]

# =============================================================================
# EDGE CASE & STRESS TEST SCENARIOS (25 scenarios)
# =============================================================================

EDGE_CASE_SCENARIOS = [
    # UNUSUAL PROMPTS (10 scenarios)
    ConversationScenario(
        eval_id="CONV-076-edge-case-creative-prompt",
        name="Edge Case - Creative Multimedia Prompt",
        category=ScenarioCategory.EDGE_CASE,
        description="Handling unusual creative prompt requiring multimedia thinking",
        school="Art Institute",
        prompt="Create a menu for the dinner party of your dreams. Who would attend? What would you serve? What would you talk about? (You may submit this as text, images, or a combination)",
        word_limit=300,
        user_profile="creative_arts_student",
        conversation_flow=[
            ConversationPhase(
                phase_name="format_confusion",
                user_input="This prompt is so different from normal college essays. It's asking for a menu but also seems like it wants to know about me. How do I approach this?",
                expected_agent_behavior="creative_prompt_interpretation",
                expected_tool_use=["analyze_prompt", "clarify"],
                success_indicators=["creative_understanding", "approach_clarification"]
            ),
            ConversationPhase(
                phase_name="concept_development",
                user_input="I'm thinking of a dinner party where artists from different time periods could meet. Is that too weird?",
                expected_agent_behavior="creative_encouragement",
                expected_tool_use=["brainstorm", "story_development"],
                success_indicators=["creativity_validation", "concept_expansion"]
            ),
            ConversationPhase(
                phase_name="structure_innovation",
                user_input="How do I structure this as both a menu and an essay that shows who I am?",
                expected_agent_behavior="innovative_structure_guidance",
                expected_tool_use=["structure_essay", "enhance_voice"],
                success_indicators=["creative_structure", "personal_revelation"]
            ),
            ConversationPhase(
                phase_name="multimedia_integration",
                user_input="Should I describe visual elements even though I'm submitting text only?",
                expected_agent_behavior="multimedia_adaptation",
                expected_tool_use=["draft_essay"],
                success_indicators=["visual_description", "multimedia_thinking"]
            )
        ],
        success_criteria=SuccessCriteria(
            conversation_turns={"min": 4, "max": 12},
            tools_used={"min": 4, "expected": ["analyze_prompt", "brainstorm", "structure_essay", "draft_essay"]},
            final_word_count={"min": 270, "max": 330},
            prompt_relevance={"min": 4.0},
            conversation_quality={"naturalness": 4.0, "goal_achievement": 4.5, "creativity_support": 4.5}
        ),
        difficulty="hard",
        estimated_duration_minutes=12,
        tags=["creative_prompt", "multimedia", "artistic", "innovative", "unusual_format"]
    ),

    # Continue with additional EDGE CASE scenarios...
    # [Scenarios CONV-077 through CONV-100 would follow similar patterns]
]

# =============================================================================
# SCENARIO REGISTRY AND UTILITIES
# =============================================================================

# Combine all scenarios into master registry
ALL_SCENARIOS = (
    NEW_USER_SCENARIOS + 
    RETURNING_USER_SCENARIOS + 
    COMPLEX_SCENARIOS + 
    EDGE_CASE_SCENARIOS
)

def get_scenario_by_id(eval_id: str) -> Optional[ConversationScenario]:
    """Get a specific scenario by its evaluation ID."""
    for scenario in ALL_SCENARIOS:
        if scenario.eval_id == eval_id:
            return scenario
    return None

def get_scenarios_by_category(category: ScenarioCategory) -> List[ConversationScenario]:
    """Get all scenarios in a specific category."""
    return [s for s in ALL_SCENARIOS if s.category == category]

def get_scenarios_by_difficulty(difficulty: str) -> List[ConversationScenario]:
    """Get all scenarios with a specific difficulty level."""
    return [s for s in ALL_SCENARIOS if s.difficulty == difficulty]

def get_scenarios_by_school(school: str) -> List[ConversationScenario]:
    """Get all scenarios for a specific school."""
    return [s for s in ALL_SCENARIOS if s.school.lower() == school.lower()]

# get_scenarios_by_autonomy removed - no longer needed without autonomy system

def get_scenario_summary() -> Dict[str, Any]:
    """Get summary statistics about available scenarios."""
    return {
        "total_scenarios": len(ALL_SCENARIOS),
        "by_category": {
            category.value: len(get_scenarios_by_category(category))
            for category in ScenarioCategory
        },
        "by_difficulty": {
            difficulty: len(get_scenarios_by_difficulty(difficulty))
            for difficulty in ["easy", "medium", "hard"]
        },
        # "by_autonomy" removed - no longer tracking autonomy levels
        "schools_covered": len(set(s.school for s in ALL_SCENARIOS)),
        "avg_duration_minutes": sum(s.estimated_duration_minutes for s in ALL_SCENARIOS) / len(ALL_SCENARIOS)
    }

# Export key components
__all__ = [
    "ConversationScenario",
    "ConversationPhase", 
    "SuccessCriteria",
    "ScenarioCategory",
    "ALL_SCENARIOS",
    "NEW_USER_SCENARIOS",
    "RETURNING_USER_SCENARIOS", 
    "COMPLEX_SCENARIOS",
    "EDGE_CASE_SCENARIOS",
    "get_scenario_by_id",
    "get_scenarios_by_category",
    "get_scenarios_by_difficulty",
    "get_scenarios_by_school",
    "get_scenario_summary"
] 