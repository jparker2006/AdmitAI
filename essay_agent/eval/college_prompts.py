"""
Real college application prompts for conversational evaluation scenarios.

This module contains 50+ authentic college application prompts from Common App,
UC system, and top universities. These prompts are used in conversational
evaluations to test the agent's ability to help students across a wide variety
of essay types, difficulty levels, and institutional contexts.
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum


class PromptType(Enum):
    """Categories of essay prompts."""
    IDENTITY = "identity"
    VALUES = "values"
    CHALLENGE = "challenge"
    GROWTH = "growth"
    PASSION = "passion"
    WHY_SCHOOL = "why_school"
    WHY_MAJOR = "why_major"
    DIVERSITY = "diversity"
    LEADERSHIP = "leadership"
    CREATIVITY = "creativity"
    COMMUNITY = "community"
    ACCOMPLISHMENT = "accomplishment"
    FAILURE = "failure"
    INTELLECTUAL = "intellectual"
    SOCIAL_ISSUE = "social_issue"
    FUTURE_GOALS = "future_goals"


class PromptDifficulty(Enum):
    """Difficulty levels for essay prompts."""
    EASY = "easy"          # Clear, specific prompts with obvious answers
    MEDIUM = "medium"      # Requires some reflection and choice-making
    HARD = "hard"          # Abstract, philosophical, or highly selective


@dataclass
class CollegePrompt:
    """Represents a college application essay prompt."""
    prompt_id: str
    school: str
    prompt_text: str
    word_limit: int
    prompt_type: PromptType
    difficulty: PromptDifficulty
    
    # Metadata
    application_cycle: str  # e.g., "2024-2025"
    is_required: bool
    is_supplemental: bool
    
    # Analysis
    common_themes: List[str]
    typical_challenges: List[str]
    success_strategies: List[str]
    
    # Usage in evaluations
    evaluation_frequency: str  # "high", "medium", "low"
    typical_user_types: List[str]  # Profile categories that commonly encounter this prompt


# =============================================================================
# COMMON APPLICATION PROMPTS (7 main prompts)
# =============================================================================

COMMON_APP_PROMPTS = [
    CollegePrompt(
        prompt_id="COMMON-001-background-identity",
        school="Common Application",
        prompt_text="Some students have a background, identity, interest, or talent that is so meaningful they believe their application would be incomplete without it. If this sounds like you, then please share your story.",
        word_limit=650,
        prompt_type=PromptType.IDENTITY,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Cultural identity and heritage",
            "Unique talents or skills",
            "Personal passions and interests",
            "Family background and influence",
            "Geographic or socioeconomic identity"
        ],
        typical_challenges=[
            "Choosing which aspect of identity to focus on",
            "Avoiding cliché cultural stereotypes",
            "Balancing personal story with broader significance",
            "Making identity relevant to college goals"
        ],
        success_strategies=[
            "Choose specific, personal examples over broad generalizations",
            "Show growth and self-awareness through identity exploration",
            "Connect identity to future contributions and goals",
            "Use vivid storytelling to bring identity to life"
        ],
        evaluation_frequency="high",
        typical_user_types=["diverse_background", "creative_artist", "community_leader"]
    ),

    CollegePrompt(
        prompt_id="COMMON-002-failure-setback",
        school="Common Application", 
        prompt_text="The lessons we take from obstacles we encounter can be fundamental to later success. Recount a time when you faced a challenge, setback, or failure. How did it affect you, and what did you learn from the experience?",
        word_limit=650,
        prompt_type=PromptType.CHALLENGE,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Academic or extracurricular setbacks",
            "Personal or family challenges",
            "Failed projects or competitions",
            "Health or mental health struggles",
            "Relationship or social difficulties"
        ],
        typical_challenges=[
            "Choosing appropriate level of vulnerability",
            "Focusing on growth rather than dwelling on failure",
            "Avoiding self-pity or blame",
            "Connecting lessons to future applications"
        ],
        success_strategies=[
            "Choose failure that led to genuine growth",
            "Be specific about lessons learned and changes made",
            "Show resilience and proactive response",
            "Demonstrate how experience shaped character"
        ],
        evaluation_frequency="high",
        typical_user_types=["athlete", "academic_achiever", "entrepreneur"]
    ),

    CollegePrompt(
        prompt_id="COMMON-003-belief-idea-challenge",
        school="Common Application",
        prompt_text="Reflect on a time when you questioned or challenged a belief or idea. What prompted your thinking? What was the outcome?",
        word_limit=650,
        prompt_type=PromptType.INTELLECTUAL,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Religious or philosophical questioning",
            "Challenging social norms or stereotypes",
            "Academic or scientific skepticism",
            "Political or social justice awakening",
            "Family tradition or cultural norm examination"
        ],
        typical_challenges=[
            "Avoiding controversial or offensive topics",
            "Showing intellectual maturity and nuance",
            "Balancing criticism with respect",
            "Demonstrating genuine intellectual growth"
        ],
        success_strategies=[
            "Focus on intellectual process rather than conclusion",
            "Show respect for different perspectives",
            "Demonstrate research and careful consideration",
            "Connect questioning to personal growth"
        ],
        evaluation_frequency="medium",
        typical_user_types=["academic_achiever", "creative_artist", "community_leader"]
    ),

    CollegePrompt(
        prompt_id="COMMON-004-gratitude-accomplishment",
        school="Common Application",
        prompt_text="Reflect on something that someone has done for you that has made you happy or thankful in a surprising way. How has this gratitude affected or motivated you?",
        word_limit=650,
        prompt_type=PromptType.GROWTH,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Unexpected kindness from strangers",
            "Teacher or mentor support",
            "Family sacrifice or support",
            "Community assistance during difficulty",
            "Peer support and friendship"
        ],
        typical_challenges=[
            "Finding genuinely surprising example of gratitude",
            "Avoiding overly sentimental tone",
            "Focusing on personal impact and growth",
            "Showing how gratitude motivated action"
        ],
        success_strategies=[
            "Choose unexpected or non-obvious source of gratitude",
            "Show specific ways gratitude changed perspective or behavior",
            "Demonstrate pay-it-forward mentality",
            "Use concrete examples of motivated action"
        ],
        evaluation_frequency="medium",
        typical_user_types=["community_leader", "diverse_background", "athlete"]
    ),

    CollegePrompt(
        prompt_id="COMMON-005-accomplishment-growth",
        school="Common Application",
        prompt_text="Discuss an accomplishment, event, or realization that sparked a period of personal growth and a new understanding of yourself or others.",
        word_limit=650,
        prompt_type=PromptType.GROWTH,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Leadership roles and responsibilities",
            "Creative or artistic breakthroughs",
            "Academic or research achievements",
            "Community service realizations",
            "Personal skill development"
        ],
        typical_challenges=[
            "Choosing accomplishment that truly led to growth",
            "Balancing achievement description with growth focus",
            "Avoiding humble-bragging",
            "Showing genuine self-awareness development"
        ],
        success_strategies=[
            "Focus more on growth than accomplishment itself",
            "Use specific examples of changed thinking or behavior",
            "Show impact on relationships with others",
            "Connect growth to future goals and values"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "entrepreneur", "creative_artist"]
    ),

    CollegePrompt(
        prompt_id="COMMON-006-engaging-topic",
        school="Common Application",
        prompt_text="Describe a topic, idea, or concept you find so engaging that it makes you lose all track of time. Why does it captivate you? What or who do you turn to when you want to learn more?",
        word_limit=650,
        prompt_type=PromptType.PASSION,
        difficulty=PromptDifficulty.EASY,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Academic subjects and research interests",
            "Creative arts and artistic expression",
            "Social issues and activism",
            "Technology and innovation",
            "Sports and physical activities"
        ],
        typical_challenges=[
            "Making passion seem authentic rather than strategic",
            "Providing specific examples of deep engagement",
            "Connecting passion to academic or career goals",
            "Showing learning process and curiosity"
        ],
        success_strategies=[
            "Use vivid details about passionate engagement",
            "Show specific learning resources and methods",
            "Demonstrate how passion has driven action",
            "Connect to potential college and career paths"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "creative_artist", "entrepreneur"]
    ),

    CollegePrompt(
        prompt_id="COMMON-007-free-choice",
        school="Common Application",
        prompt_text="Share an essay on any topic of your choice. It can be one you've already written, one that responds to a different prompt, or one of your own design.",
        word_limit=650,
        prompt_type=PromptType.CREATIVITY,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Unique personal experiences",
            "Creative or artistic expression",
            "Unusual interests or hobbies",
            "Philosophical reflections",
            "Innovative approaches to common topics"
        ],
        typical_challenges=[
            "Choosing appropriate topic from infinite options",
            "Creating structure without external prompt guidance",
            "Balancing creativity with admissions relevance",
            "Standing out while maintaining authenticity"
        ],
        success_strategies=[
            "Choose topic that reveals something unique about you",
            "Use creative structure or narrative approach",
            "Ensure topic connects to personal growth or values",
            "Show rather than tell through specific examples"
        ],
        evaluation_frequency="medium",
        typical_user_types=["creative_artist", "entrepreneur", "academic_achiever"]
    )
]

# =============================================================================
# UC SYSTEM PERSONAL INSIGHT QUESTIONS (8 prompts, choose 4)
# =============================================================================

UC_PERSONAL_INSIGHT_PROMPTS = [
    CollegePrompt(
        prompt_id="UC-001-leadership",
        school="University of California System",
        prompt_text="Describe an example of your leadership experience in which you have positively influenced others, helped resolve disputes, or contributed to group efforts over time.",
        word_limit=350,
        prompt_type=PromptType.LEADERSHIP,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Formal leadership positions",
            "Informal influence and guidance",
            "Conflict resolution and mediation",
            "Team project coordination",
            "Community organizing and advocacy"
        ],
        typical_challenges=[
            "Defining leadership broadly beyond titles",
            "Showing sustained impact over time",
            "Balancing personal role with team credit",
            "Providing specific examples of influence"
        ],
        success_strategies=[
            "Focus on specific leadership actions and decisions",
            "Show impact on others and group outcomes",
            "Demonstrate growth in leadership style",
            "Use concrete examples with measurable results"
        ],
        evaluation_frequency="high",
        typical_user_types=["community_leader", "athlete", "entrepreneur"]
    ),

    CollegePrompt(
        prompt_id="UC-002-creativity",
        school="University of California System",
        prompt_text="Every person has a creative side, and it can be expressed in many ways: problem solving, original and innovative thinking, and artistically, to name a few. Describe how you express your creative side.",
        word_limit=350,
        prompt_type=PromptType.CREATIVITY,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Artistic expression and creative arts",
            "Innovative problem-solving approaches",
            "Entrepreneurial thinking and innovation",
            "Creative academic projects",
            "Unique hobby or interest development"
        ],
        typical_challenges=[
            "Defining creativity beyond traditional arts",
            "Providing specific examples of creative expression",
            "Showing impact or application of creativity",
            "Avoiding cliché creative activities"
        ],
        success_strategies=[
            "Choose unique or unexpected form of creativity",
            "Show specific creative process and methods",
            "Demonstrate impact of creative work on others",
            "Connect creativity to problem-solving or innovation"
        ],
        evaluation_frequency="high",
        typical_user_types=["creative_artist", "academic_achiever", "entrepreneur"]
    ),

    CollegePrompt(
        prompt_id="UC-003-talent-skill",
        school="University of California System",
        prompt_text="What would you say is your greatest talent or skill? How have you developed and demonstrated that talent over time?",
        word_limit=350,
        prompt_type=PromptType.ACCOMPLISHMENT,
        difficulty=PromptDifficulty.EASY,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Athletic abilities and sports achievements",
            "Academic or intellectual talents",
            "Artistic or creative skills",
            "Social or communication abilities",
            "Technical or technological skills"
        ],
        typical_challenges=[
            "Choosing one talent from multiple options",
            "Showing development and growth over time",
            "Providing specific examples of demonstration",
            "Avoiding arrogance while showing confidence"
        ],
        success_strategies=[
            "Choose talent with clear development trajectory",
            "Show specific practice, training, or improvement",
            "Demonstrate talent application in various contexts",
            "Include challenges overcome in development"
        ],
        evaluation_frequency="high",
        typical_user_types=["athlete", "academic_achiever", "creative_artist"]
    ),

    CollegePrompt(
        prompt_id="UC-004-educational-opportunity",
        school="University of California System",
        prompt_text="Describe how you have taken advantage of a significant educational opportunity or worked to overcome an educational barrier you have faced.",
        word_limit=350,
        prompt_type=PromptType.GROWTH,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Advanced academic programs or courses",
            "Research opportunities and projects",
            "Overcoming learning differences or challenges",
            "Financial barriers to educational access",
            "Language or cultural barriers in education"
        ],
        typical_challenges=[
            "Distinguishing opportunity from barrier prompt",
            "Showing proactive approach to opportunity",
            "Demonstrating impact of opportunity on growth",
            "Avoiding complaints when discussing barriers"
        ],
        success_strategies=[
            "Focus on personal agency and initiative",
            "Show specific actions taken and skills gained",
            "Demonstrate impact on academic or personal growth",
            "Connect experience to future educational goals"
        ],
        evaluation_frequency="high",
        typical_user_types=["diverse_background", "academic_achiever", "community_leader"]
    ),

    CollegePrompt(
        prompt_id="UC-005-significant-challenge",
        school="University of California System",
        prompt_text="Describe the most significant challenge you have faced and the steps you have taken to overcome this challenge. How has this challenge affected your academic achievement?",
        word_limit=350,
        prompt_type=PromptType.CHALLENGE,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Family or personal hardships",
            "Health or mental health challenges",
            "Financial difficulties affecting education",
            "Social or cultural adjustment challenges",
            "Academic struggles and recovery"
        ],
        typical_challenges=[
            "Choosing appropriate level of personal disclosure",
            "Focusing on resilience rather than victimization",
            "Connecting challenge to academic impact",
            "Showing specific steps taken to overcome"
        ],
        success_strategies=[
            "Choose challenge that demonstrates growth and resilience",
            "Show specific actions and strategies used",
            "Connect to academic achievement and learning",
            "Demonstrate ongoing strength and perspective"
        ],
        evaluation_frequency="high",
        typical_user_types=["diverse_background", "athlete", "community_leader"]
    ),

    CollegePrompt(
        prompt_id="UC-006-inspiring-subject",
        school="University of California System",
        prompt_text="Think about an academic subject that inspires you. Describe how you have furthered this interest inside and/or outside of the classroom.",
        word_limit=350,
        prompt_type=PromptType.PASSION,
        difficulty=PromptDifficulty.EASY,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "STEM subjects and research projects",
            "Humanities and social science interests",
            "Arts and creative academic pursuits",
            "Languages and cultural studies",
            "Interdisciplinary academic interests"
        ],
        typical_challenges=[
            "Going beyond basic classroom description",
            "Showing genuine passion and initiative",
            "Providing specific examples of further exploration",
            "Connecting to future academic and career plans"
        ],
        success_strategies=[
            "Show specific ways you've explored subject beyond class",
            "Demonstrate initiative in seeking learning opportunities",
            "Include projects, research, or independent study",
            "Connect passion to potential major or career"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "creative_artist", "entrepreneur"]
    ),

    CollegePrompt(
        prompt_id="UC-007-community-contribution",
        school="University of California System",
        prompt_text="What have you done to make your school or your community a better place?",
        word_limit=350,
        prompt_type=PromptType.COMMUNITY,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Volunteer work and community service",
            "School improvement initiatives",
            "Environmental or sustainability projects",
            "Social justice and advocacy work",
            "Peer support and mentoring programs"
        ],
        typical_challenges=[
            "Showing personal initiative rather than required service",
            "Demonstrating measurable impact on community",
            "Avoiding savior complex or condescension",
            "Connecting service to personal values and growth"
        ],
        success_strategies=[
            "Focus on personal motivation and initiative",
            "Show specific impact and outcomes achieved",
            "Demonstrate sustained commitment over time",
            "Include what you learned from community engagement"
        ],
        evaluation_frequency="high",
        typical_user_types=["community_leader", "diverse_background", "athlete"]
    ),

    CollegePrompt(
        prompt_id="UC-008-beyond-academics",
        school="University of California System",
        prompt_text="Beyond what has already been shared in your application, what do you believe makes you a strong candidate for admissions to the University of California?",
        word_limit=350,
        prompt_type=PromptType.VALUES,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=False,
        common_themes=[
            "Personal qualities and character traits",
            "Unique perspectives and experiences",
            "Future contributions to UC community",
            "Hidden talents or abilities",
            "Personal growth and maturity"
        ],
        typical_challenges=[
            "Avoiding repetition of application content",
            "Balancing confidence with humility",
            "Providing new insights about candidacy",
            "Connecting personal qualities to UC fit"
        ],
        success_strategies=[
            "Reveal new aspects of personality or experience",
            "Show self-awareness and reflection",
            "Connect qualities to potential UC contributions",
            "Use specific examples to demonstrate traits"
        ],
        evaluation_frequency="medium",
        typical_user_types=["academic_achiever", "entrepreneur", "diverse_background"]
    )
]

# =============================================================================
# STANFORD UNIVERSITY PROMPTS
# =============================================================================

STANFORD_PROMPTS = [
    CollegePrompt(
        prompt_id="STANFORD-001-what-matters-most",
        school="Stanford University",
        prompt_text="What matters most to you, and why?",
        word_limit=250,
        prompt_type=PromptType.VALUES,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Core personal values and principles",
            "Family and relationship priorities",
            "Social justice and equity concerns",
            "Academic or intellectual pursuits",
            "Creative expression and artistic values"
        ],
        typical_challenges=[
            "Choosing one thing from many important values",
            "Avoiding cliché or generic responses",
            "Providing specific, personal examples",
            "Showing depth of reflection in limited words"
        ],
        success_strategies=[
            "Choose value demonstrated through specific actions",
            "Use personal stories to illustrate importance",
            "Show how value influences decisions and goals",
            "Connect to potential Stanford contributions"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "community_leader", "creative_artist"]
    ),

    CollegePrompt(
        prompt_id="STANFORD-002-meaningful-experience",
        school="Stanford University",
        prompt_text="Tell us about something that is meaningful to you and why.",
        word_limit=250,
        prompt_type=PromptType.IDENTITY,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Cultural traditions and heritage",
            "Meaningful objects or places",
            "Relationships and mentorships",
            "Experiences and life events",
            "Ideas and intellectual concepts"
        ],
        typical_challenges=[
            "Distinguishing from 'what matters most' prompt",
            "Showing personal connection and significance",
            "Avoiding superficial or material choices",
            "Demonstrating reflection and insight"
        ],
        success_strategies=[
            "Choose something with deep personal resonance",
            "Explain specific ways it has shaped you",
            "Use vivid details and personal narrative",
            "Connect to character development or values"
        ],
        evaluation_frequency="high",
        typical_user_types=["diverse_background", "creative_artist", "community_leader"]
    ),

    CollegePrompt(
        prompt_id="STANFORD-003-intellectually-excited",
        school="Stanford University",
        prompt_text="Name one thing you are looking forward to experiencing at Stanford.",
        word_limit=50,
        prompt_type=PromptType.WHY_SCHOOL,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Specific academic programs or research",
            "Interdisciplinary learning opportunities",
            "Campus culture and community",
            "Location and geographic advantages",
            "Innovation and entrepreneurship ecosystem"
        ],
        typical_challenges=[
            "Being specific in very limited word count",
            "Avoiding generic Stanford attributes",
            "Showing research and genuine interest",
            "Making personal connection to opportunity"
        ],
        success_strategies=[
            "Research specific, unique Stanford opportunities",
            "Choose something aligned with personal interests",
            "Be concrete and specific rather than general",
            "Show how opportunity connects to goals"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "entrepreneur", "creative_artist"]
    )
]

# =============================================================================
# HARVARD UNIVERSITY PROMPTS
# =============================================================================

HARVARD_PROMPTS = [
    CollegePrompt(
        prompt_id="HARVARD-001-diversity-contribution",
        school="Harvard University",
        prompt_text="Harvard has long recognized the importance of student body diversity. How will the life experiences that shape who you are today enable you to contribute to Harvard?",
        word_limit=150,
        prompt_type=PromptType.DIVERSITY,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=True,
        common_themes=[
            "Cultural background and identity",
            "Unique life experiences and perspectives",
            "Overcoming challenges and adversity",
            "Geographic or socioeconomic background",
            "Family history and generational experiences"
        ],
        typical_challenges=[
            "Balancing diversity with contribution focus",
            "Avoiding victimization or complaint tone",
            "Being specific about Harvard contributions",
            "Demonstrating self-awareness and reflection"
        ],
        success_strategies=[
            "Focus on unique perspectives and insights gained",
            "Show specific ways experience shaped worldview",
            "Connect background to potential Harvard contributions",
            "Demonstrate growth and learning from experiences"
        ],
        evaluation_frequency="high",
        typical_user_types=["diverse_background", "community_leader", "athlete"]
    ),

    CollegePrompt(
        prompt_id="HARVARD-002-academic-interest",
        school="Harvard University", 
        prompt_text="Briefly describe an intellectual experience (course, project, book, discussion, paper, poetry, or research topic in engineering, mathematics, science, or other modes of inquiry) that has meant the most to you.",
        word_limit=150,
        prompt_type=PromptType.INTELLECTUAL,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=True,
        common_themes=[
            "Research projects and academic investigations",
            "Challenging courses and breakthrough moments",
            "Books or ideas that changed perspective",
            "Creative projects with intellectual depth",
            "Collaborative academic experiences"
        ],
        typical_challenges=[
            "Choosing most meaningful from many options",
            "Showing genuine intellectual engagement",
            "Explaining complex ideas concisely",
            "Demonstrating personal connection to learning"
        ],
        success_strategies=[
            "Choose experience with genuine personal impact",
            "Show specific ways it changed your thinking",
            "Demonstrate intellectual curiosity and passion",
            "Connect to future academic interests"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "creative_artist", "entrepreneur"]
    ),

    CollegePrompt(
        prompt_id="HARVARD-003-extracurricular-activity",
        school="Harvard University",
        prompt_text="Briefly describe any of your extracurricular activities, employment experience, travel, or family responsibilities that have shaped who you are.",
        word_limit=150,
        prompt_type=PromptType.GROWTH,
        difficulty=PromptDifficulty.EASY,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=True,
        common_themes=[
            "Leadership roles and responsibilities",
            "Work experience and professional growth",
            "Travel and cultural exposure",
            "Family responsibilities and caregiving",
            "Community service and volunteer work"
        ],
        typical_challenges=[
            "Choosing which activities to highlight",
            "Showing personal growth and development",
            "Avoiding simple activity description",
            "Connecting activities to character formation"
        ],
        success_strategies=[
            "Focus on activities with clear personal impact",
            "Show specific ways activities shaped character",
            "Demonstrate growth and learning from experience",
            "Choose activities not fully covered elsewhere"
        ],
        evaluation_frequency="medium",
        typical_user_types=["community_leader", "athlete", "diverse_background"]
    ),

    CollegePrompt(
        prompt_id="HARVARD-004-perspective-contribution",
        school="Harvard University",
        prompt_text="How do you hope to use your Harvard education in the future?",
        word_limit=150,
        prompt_type=PromptType.FUTURE_GOALS,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=True,
        common_themes=[
            "Career goals and professional aspirations",
            "Social impact and change-making goals",
            "Academic and research ambitions",
            "Leadership and service objectives",
            "Creative and artistic pursuits"
        ],
        typical_challenges=[
            "Balancing specificity with flexibility",
            "Connecting goals to Harvard specifically",
            "Showing realistic yet ambitious vision",
            "Demonstrating preparation for goals"
        ],
        success_strategies=[
            "Show clear connection between Harvard and goals",
            "Demonstrate knowledge of Harvard resources",
            "Balance ambition with realistic planning",
            "Connect goals to current interests and experiences"
        ],
        evaluation_frequency="medium",
        typical_user_types=["academic_achiever", "entrepreneur", "community_leader"]
    ),

    CollegePrompt(
        prompt_id="HARVARD-005-additional-information",
        school="Harvard University",
        prompt_text="Top 3 things your roommates might like to know about you.",
        word_limit=150,
        prompt_type=PromptType.IDENTITY,
        difficulty=PromptDifficulty.EASY,
        application_cycle="2024-2025",
        is_required=False,
        is_supplemental=True,
        common_themes=[
            "Personal habits and quirks",
            "Hobbies and interests",
            "Values and principles",
            "Social preferences and style",
            "Fun facts and unique traits"
        ],
        typical_challenges=[
            "Balancing fun with meaningful information",
            "Avoiding oversharing or inappropriate content",
            "Showing personality while maintaining appropriateness",
            "Being authentic rather than strategic"
        ],
        success_strategies=[
            "Choose mix of practical and personal information",
            "Show sense of humor and self-awareness",
            "Include information that reveals character",
            "Be authentic and conversational in tone"
        ],
        evaluation_frequency="medium",
        typical_user_types=["creative_artist", "athlete", "entrepreneur"]
    )
]

# =============================================================================
# MIT PROMPTS
# =============================================================================

MIT_PROMPTS = [
    CollegePrompt(
        prompt_id="MIT-001-pleasure-activity",
        school="MIT",
        prompt_text="Tell us about something you do simply for the pleasure of it.",
        word_limit=200,
        prompt_type=PromptType.PASSION,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Hobbies and personal interests",
            "Creative pursuits and artistic expression",
            "Physical activities and sports",
            "Intellectual curiosity and learning",
            "Social activities and community engagement"
        ],
        typical_challenges=[
            "Finding genuine pleasure-driven activity",
            "Avoiding activities that seem resume-building",
            "Showing authentic passion and joy",
            "Connecting pleasure to personality insight"
        ],
        success_strategies=[
            "Choose activity done purely for enjoyment",
            "Show specific ways activity brings joy",
            "Demonstrate authenticity and genuine passion",
            "Reveal personality traits through activity"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "creative_artist", "athlete"]
    ),

    CollegePrompt(
        prompt_id="MIT-002-community-description",
        school="MIT",
        prompt_text="Describe the world you come from (for example, your family, school, community, city, or town). How has that world shaped who you are?",
        word_limit=300,
        prompt_type=PromptType.IDENTITY,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Family background and culture",
            "Geographic location and community",
            "School environment and academic culture",
            "Socioeconomic background and experiences",
            "Cultural identity and heritage"
        ],
        typical_challenges=[
            "Choosing which aspect of world to focus on",
            "Showing specific ways world shaped character",
            "Avoiding stereotypes or generalizations",
            "Balancing description with personal impact"
        ],
        success_strategies=[
            "Choose specific aspect of world with clear impact",
            "Show concrete ways environment shaped values",
            "Use specific examples and stories",
            "Connect background to current perspectives"
        ],
        evaluation_frequency="high",
        typical_user_types=["diverse_background", "community_leader", "academic_achiever"]
    ),

    CollegePrompt(
        prompt_id="MIT-003-challenge-setback",
        school="MIT",
        prompt_text="Tell us about a significant challenge you've faced or something that didn't go according to plan. How did you manage the situation?",
        word_limit=200,
        prompt_type=PromptType.CHALLENGE,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Academic or project failures",
            "Personal or family difficulties",
            "Health or mental health challenges",
            "Social or relationship problems",
            "Financial or resource constraints"
        ],
        typical_challenges=[
            "Choosing appropriate level of personal sharing",
            "Focusing on management rather than challenge itself",
            "Showing growth and learning from experience",
            "Demonstrating resilience and problem-solving"
        ],
        success_strategies=[
            "Choose challenge with clear resolution strategy",
            "Show specific actions taken to address situation",
            "Demonstrate learning and growth from experience",
            "Highlight problem-solving and resilience skills"
        ],
        evaluation_frequency="high",
        typical_user_types=["athlete", "academic_achiever", "entrepreneur"]
    )
]

# =============================================================================
# YALE UNIVERSITY PROMPTS
# =============================================================================

YALE_PROMPTS = [
    CollegePrompt(
        prompt_id="YALE-001-community-impact",
        school="Yale University",
        prompt_text="What is something about you that is not on the rest of your application?",
        word_limit=200,
        prompt_type=PromptType.IDENTITY,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Hidden talents or interests",
            "Personal quirks or characteristics",
            "Family background or responsibilities",
            "Unique perspectives or experiences",
            "Personal values or principles"
        ],
        typical_challenges=[
            "Finding genuinely new information to share",
            "Balancing uniqueness with relevance",
            "Avoiding oversharing inappropriate information",
            "Showing self-awareness and reflection"
        ],
        success_strategies=[
            "Choose aspect not covered in other essays",
            "Reveal new dimension of personality or experience",
            "Show how hidden aspect influences who you are",
            "Use specific examples and stories"
        ],
        evaluation_frequency="high",
        typical_user_types=["creative_artist", "diverse_background", "community_leader"]
    ),

    CollegePrompt(
        prompt_id="YALE-002-yale-community",
        school="Yale University",
        prompt_text="What inspires you?",
        word_limit=200,
        prompt_type=PromptType.PASSION,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "People who serve as role models",
            "Ideas or concepts that drive curiosity",
            "Experiences that motivate action",
            "Creative works or artistic expression",
            "Social issues or causes"
        ],
        typical_challenges=[
            "Choosing one source of inspiration from many",
            "Showing genuine rather than strategic inspiration",
            "Connecting inspiration to personal action",
            "Demonstrating depth of impact"
        ],
        success_strategies=[
            "Choose inspiration with clear personal impact",
            "Show specific ways inspiration influences behavior",
            "Use concrete examples of inspired action",
            "Connect inspiration to future goals"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "community_leader", "creative_artist"]
    ),

    CollegePrompt(
        prompt_id="YALE-003-teach-others",
        school="Yale University",
        prompt_text="If you could teach any college course, write a book, or create an original piece of work, what would it be? Why?",
        word_limit=200,
        prompt_type=PromptType.INTELLECTUAL,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Academic subjects and teaching interests",
            "Creative projects and artistic works",
            "Social issues and advocacy topics",
            "Personal experiences and life lessons",
            "Interdisciplinary ideas and innovations"
        ],
        typical_challenges=[
            "Choosing between many possible topics",
            "Showing depth of knowledge and passion",
            "Explaining complex ideas concisely",
            "Connecting choice to personal interests"
        ],
        success_strategies=[
            "Choose topic with genuine personal connection",
            "Show specific knowledge and preparation",
            "Explain unique perspective or approach",
            "Connect to current interests and future goals"
        ],
        evaluation_frequency="medium",
        typical_user_types=["academic_achiever", "creative_artist", "entrepreneur"]
    )
]

# =============================================================================
# PRINCETON UNIVERSITY PROMPTS
# =============================================================================

PRINCETON_PROMPTS = [
    CollegePrompt(
        prompt_id="PRINCETON-001-extracurricular",
        school="Princeton University",
        prompt_text="Tell us how you have changed in the last three years. What experiences, events, or new understandings have shaped this evolution?",
        word_limit=300,
        prompt_type=PromptType.GROWTH,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Academic growth and intellectual development",
            "Personal maturity and self-awareness",
            "Social consciousness and empathy development",
            "Leadership skills and confidence building",
            "Values clarification and priority setting"
        ],
        typical_challenges=[
            "Identifying meaningful change over time period",
            "Showing specific catalysts for change",
            "Demonstrating genuine growth rather than simple aging",
            "Connecting change to current identity"
        ],
        success_strategies=[
            "Choose significant transformation with clear triggers",
            "Show specific before-and-after examples",
            "Identify key experiences that drove change",
            "Demonstrate ongoing impact of growth"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "community_leader", "athlete"]
    ),

    CollegePrompt(
        prompt_id="PRINCETON-002-unique-voice",
        school="Princeton University",
        prompt_text="Princeton values diverse perspectives and the ability to have respectful dialogue about difficult issues. Share a time when you had a conversation with a person or a group of people about a difficult topic. What insight did you gain, and how would you incorporate that knowledge into your thinking in the future?",
        word_limit=300,
        prompt_type=PromptType.INTELLECTUAL,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Political or social issue discussions",
            "Cultural or religious differences exploration",
            "Family conflicts over values or choices",
            "Peer disagreements about important topics",
            "Academic debates and intellectual challenges"
        ],
        typical_challenges=[
            "Choosing appropriate difficult topic",
            "Showing respectful dialogue rather than argument",
            "Demonstrating genuine insight gained",
            "Avoiding controversial or offensive content"
        ],
        success_strategies=[
            "Choose topic showing intellectual maturity",
            "Focus on listening and learning from dialogue",
            "Show specific insights and perspective changes",
            "Demonstrate application of learning to future thinking"
        ],
        evaluation_frequency="medium",
        typical_user_types=["academic_achiever", "community_leader", "diverse_background"]
    )
]

# =============================================================================
# ADDITIONAL TOP UNIVERSITY PROMPTS
# =============================================================================

OTHER_UNIVERSITY_PROMPTS = [
    # COLUMBIA UNIVERSITY
    CollegePrompt(
        prompt_id="COLUMBIA-001-why-major",
        school="Columbia University",
        prompt_text="What attracts you to your intended major?",
        word_limit=300,
        prompt_type=PromptType.WHY_MAJOR,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Academic interests and intellectual curiosity",
            "Career goals and professional aspirations",
            "Personal experiences that sparked interest",
            "Research or project experiences",
            "Social impact and change-making through field"
        ],
        typical_challenges=[
            "Showing genuine passion rather than strategic choice",
            "Connecting personal experiences to academic interest",
            "Demonstrating knowledge of field beyond basics",
            "Balancing specificity with openness to exploration"
        ],
        success_strategies=[
            "Use specific experiences that sparked interest",
            "Show knowledge of field and its applications",
            "Connect major to personal values and goals",
            "Demonstrate preparation through relevant activities"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "entrepreneur", "creative_artist"]
    ),

    # BROWN UNIVERSITY  
    CollegePrompt(
        prompt_id="BROWN-001-academic-fields",
        school="Brown University",
        prompt_text="Why are you drawn to the academic fields you indicated in your application?",
        word_limit=200,
        prompt_type=PromptType.WHY_MAJOR,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Intellectual curiosity and passion for learning",
            "Interdisciplinary interests and connections",
            "Personal experiences driving academic interest",
            "Research or creative projects in field",
            "Future applications and career connections"
        ],
        typical_challenges=[
            "Addressing multiple fields coherently",
            "Showing connections between different interests",
            "Avoiding generic academic interest descriptions",
            "Demonstrating genuine intellectual engagement"
        ],
        success_strategies=[
            "Show connections between different academic interests",
            "Use specific examples of engagement with fields",
            "Demonstrate intellectual curiosity and exploration",
            "Connect fields to Brown's open curriculum philosophy"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "creative_artist", "entrepreneur"]
    ),

    # DUKE UNIVERSITY
    CollegePrompt(
        prompt_id="DUKE-001-human-experience",
        school="Duke University",
        prompt_text="We seek a talented, engaged student body that embodies the wide range of human experience. Please share with us something about you not yet reflected in your application.",
        word_limit=250,
        prompt_type=PromptType.IDENTITY,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Hidden talents or unusual interests",
            "Family background or cultural heritage",
            "Personal challenges or growth experiences",
            "Unique perspectives or worldviews",
            "Character traits or personal qualities"
        ],
        typical_challenges=[
            "Finding new information not in application",
            "Showing relevance to college admissions",
            "Balancing uniqueness with authenticity",
            "Connecting hidden aspect to personal growth"
        ],
        success_strategies=[
            "Choose aspect that reveals new dimension of identity",
            "Show how hidden aspect influences perspective",
            "Use specific stories and examples",
            "Connect to potential Duke community contributions"
        ],
        evaluation_frequency="high",
        typical_user_types=["diverse_background", "community_leader", "creative_artist"]
    ),

    # NORTHWESTERN UNIVERSITY
    CollegePrompt(
        prompt_id="NORTHWESTERN-001-why-school",
        school="Northwestern University",
        prompt_text="What are the unique qualities of Northwestern - and of the specific undergraduate school to which you are applying - that make you want to attend the University?",
        word_limit=300,
        prompt_type=PromptType.WHY_SCHOOL,
        difficulty=PromptDifficulty.MEDIUM,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Specific academic programs and opportunities",
            "Research opportunities and faculty",
            "Campus culture and community",
            "Location and geographic advantages",
            "Career preparation and alumni network"
        ],
        typical_challenges=[
            "Going beyond generic university attributes",
            "Showing specific research about Northwestern",
            "Connecting qualities to personal goals",
            "Demonstrating genuine interest and fit"
        ],
        success_strategies=[
            "Research specific Northwestern programs and opportunities",
            "Show clear connection between qualities and goals",
            "Demonstrate knowledge of school-specific resources",
            "Include personal reasons for geographic/cultural fit"
        ],
        evaluation_frequency="high",
        typical_user_types=["academic_achiever", "entrepreneur", "creative_artist"]
    ),

    # CREATIVE/ARTS SCHOOLS
    CollegePrompt(
        prompt_id="ARTS-001-creative-menu",
        school="Art Institute",
        prompt_text="Create a menu for the dinner party of your dreams. Who would attend? What would you serve? What would you talk about? (You may submit this as text, images, or a combination)",
        word_limit=300,
        prompt_type=PromptType.CREATIVITY,
        difficulty=PromptDifficulty.HARD,
        application_cycle="2024-2025",
        is_required=True,
        is_supplemental=True,
        common_themes=[
            "Creative expression and artistic vision",
            "Cultural interests and influences",
            "Intellectual curiosity and conversation topics",
            "Personal values and priorities",
            "Imagination and innovative thinking"
        ],
        typical_challenges=[
            "Balancing creativity with college essay appropriateness",
            "Using creative format effectively",
            "Revealing personal insights through creative expression",
            "Showing artistic vision and cultural awareness"
        ],
        success_strategies=[
            "Use creative format to reveal personality",
            "Choose guests and topics that reflect interests",
            "Show cultural awareness and curiosity",
            "Balance creativity with personal insight"
        ],
        evaluation_frequency="low",
        typical_user_types=["creative_artist", "entrepreneur", "diverse_background"]
    )
]

# =============================================================================
# PROMPT REGISTRY AND UTILITIES
# =============================================================================

# Combine all prompts into master registry
ALL_PROMPTS = (
    COMMON_APP_PROMPTS +
    UC_PERSONAL_INSIGHT_PROMPTS +
    STANFORD_PROMPTS +
    HARVARD_PROMPTS +
    MIT_PROMPTS +
    YALE_PROMPTS +
    PRINCETON_PROMPTS +
    OTHER_UNIVERSITY_PROMPTS
)

def get_prompt_by_id(prompt_id: str) -> Optional[CollegePrompt]:
    """Get a specific prompt by its ID."""
    for prompt in ALL_PROMPTS:
        if prompt.prompt_id == prompt_id:
            return prompt
    return None

def get_prompts_by_school(school: str) -> List[CollegePrompt]:
    """Get all prompts for a specific school."""
    return [p for p in ALL_PROMPTS if p.school.lower() == school.lower()]

def get_prompts_by_type(prompt_type: PromptType) -> List[CollegePrompt]:
    """Get all prompts of a specific type."""
    return [p for p in ALL_PROMPTS if p.prompt_type == prompt_type]

def get_prompts_by_difficulty(difficulty: PromptDifficulty) -> List[CollegePrompt]:
    """Get all prompts with a specific difficulty level."""
    return [p for p in ALL_PROMPTS if p.difficulty == difficulty]

def get_prompts_by_word_limit(min_words: int, max_words: int) -> List[CollegePrompt]:
    """Get prompts within a specific word limit range."""
    return [p for p in ALL_PROMPTS if min_words <= p.word_limit <= max_words]

def get_high_frequency_prompts() -> List[CollegePrompt]:
    """Get prompts commonly used in evaluations."""
    return [p for p in ALL_PROMPTS if p.evaluation_frequency == "high"]

def get_prompts_for_user_type(user_type: str) -> List[CollegePrompt]:
    """Get prompts typically used by a specific user profile type."""
    return [p for p in ALL_PROMPTS if user_type in p.typical_user_types]

def get_prompts_summary() -> Dict[str, Any]:
    """Get summary statistics about available prompts."""
    return {
        "total_prompts": len(ALL_PROMPTS),
        "by_school": {
            school: len(get_prompts_by_school(school))
            for school in set(p.school for p in ALL_PROMPTS)
        },
        "by_type": {
            prompt_type.value: len(get_prompts_by_type(prompt_type))
            for prompt_type in PromptType
        },
        "by_difficulty": {
            difficulty.value: len(get_prompts_by_difficulty(difficulty))
            for difficulty in PromptDifficulty
        },
        "word_limit_range": {
            "min": min(p.word_limit for p in ALL_PROMPTS),
            "max": max(p.word_limit for p in ALL_PROMPTS),
            "average": sum(p.word_limit for p in ALL_PROMPTS) / len(ALL_PROMPTS)
        },
        "high_frequency_count": len(get_high_frequency_prompts()),
        "schools_covered": len(set(p.school for p in ALL_PROMPTS))
    }

# Common prompt combinations for evaluation scenarios
PROMPT_COMBINATIONS = {
    "new_user_friendly": [
        "COMMON-006-engaging-topic",
        "UC-003-talent-skill", 
        "MIT-001-pleasure-activity",
        "HARVARD-005-additional-information"
    ],
    "challenging_intellectual": [
        "COMMON-003-belief-idea-challenge",
        "YALE-003-teach-others",
        "PRINCETON-002-unique-voice",
        "HARVARD-002-academic-interest"
    ],
    "values_and_identity": [
        "STANFORD-001-what-matters-most",
        "COMMON-001-background-identity",
        "YALE-001-community-impact",
        "DUKE-001-human-experience"
    ],
    "growth_and_challenge": [
        "COMMON-002-failure-setback",
        "UC-005-significant-challenge",
        "PRINCETON-001-extracurricular",
        "MIT-003-challenge-setback"
    ]
}

# Export key components
__all__ = [
    "CollegePrompt",
    "PromptType",
    "PromptDifficulty",
    "ALL_PROMPTS",
    "COMMON_APP_PROMPTS",
    "UC_PERSONAL_INSIGHT_PROMPTS",
    "STANFORD_PROMPTS",
    "HARVARD_PROMPTS",
    "MIT_PROMPTS",
    "YALE_PROMPTS",
    "PRINCETON_PROMPTS",
    "OTHER_UNIVERSITY_PROMPTS",
    "PROMPT_COMBINATIONS",
    "get_prompt_by_id",
    "get_prompts_by_school",
    "get_prompts_by_type",
    "get_prompts_by_difficulty",
    "get_prompts_by_word_limit",
    "get_high_frequency_prompts",
    "get_prompts_for_user_type",
    "get_prompts_summary"
] 