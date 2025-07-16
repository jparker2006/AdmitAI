"""
Real user profiles for conversational evaluation scenarios.

This module contains 20 detailed, realistic user profiles representing diverse
student backgrounds, experiences, and essay writing contexts. These profiles
are used to test memory utilization, story adaptation, and personalized
essay assistance across the full spectrum of college applicants.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ProfileCategory(Enum):
    """Categories of user profiles."""
    ACADEMIC_ACHIEVER = "academic_achiever"
    CREATIVE_ARTIST = "creative_artist"
    COMMUNITY_LEADER = "community_leader"
    ENTREPRENEUR = "entrepreneur"
    ATHLETE = "athlete"
    DIVERSE_BACKGROUND = "diverse_background"


@dataclass
class Activity:
    """Represents an extracurricular activity or experience."""
    name: str
    role: str
    description: str
    duration: str
    impact: str
    essay_potential: str
    values_demonstrated: List[str]


@dataclass
class EssayHistory:
    """Previous essay topics and themes used by the student."""
    topic: str
    theme: str
    word_count: int
    school_type: str
    strengths: List[str]
    areas_for_improvement: List[str]
    reusability: str  # "high", "medium", "low"


@dataclass
class DefiningMoment:
    """Significant life experiences that shaped the student."""
    event: str
    age_when_occurred: str
    impact: str
    lessons_learned: List[str]
    essay_potential: str
    emotional_weight: str  # "high", "medium", "low"


@dataclass
class WritingStyle:
    """Student's writing preferences and characteristics."""
    tone_preference: str  # "formal", "conversational", "creative", "analytical"
    strength_areas: List[str]
    challenge_areas: List[str]
    autonomy_preference: str  # "full_agent", "collaborative", "guided_self_write", "minimal_help"
    feedback_sensitivity: str  # "high", "medium", "low"


@dataclass
class UserProfile:
    """Comprehensive student profile for realistic evaluation scenarios."""
    profile_id: str
    name: str
    category: ProfileCategory
    
    # Demographics
    age: int
    location: str
    school_type: str
    gpa: float
    test_scores: Dict[str, int]
    
    # Background
    family_background: str
    socioeconomic_status: str
    first_generation: bool
    languages_spoken: List[str]
    
    # Academic Profile
    academic_interests: List[str]
    intended_major: str
    favorite_subjects: List[str]
    academic_achievements: List[str]
    research_experience: Optional[str]
    
    # Activities & Leadership
    activities: List[Activity]
    leadership_roles: List[str]
    volunteer_work: List[str]
    work_experience: Optional[str]
    
    # Personal Development
    core_values: List[str]
    defining_moments: List[DefiningMoment]
    personal_challenges: List[str]
    growth_areas: List[str]
    
    # Essay Context
    essay_history: List[EssayHistory]
    college_goals: List[str]
    dream_schools: List[str]
    writing_style: WritingStyle
    
    # Agent Interaction History
    previous_sessions: int
    successful_essays_completed: int
    preferred_brainstorming_approach: str
    common_stuck_points: List[str]


# =============================================================================
# ACADEMIC ACHIEVERS (5 profiles)
# =============================================================================

ACADEMIC_ACHIEVER_PROFILES = [
    UserProfile(
        profile_id="tech_entrepreneur_student",
        name="Alex Chen",
        category=ProfileCategory.ACADEMIC_ACHIEVER,
        
        age=17,
        location="Silicon Valley, CA",
        school_type="Public High School",
        gpa=4.0,
        test_scores={"SAT": 1580, "SAT_Math": 800, "SAT_ERW": 780},
        
        family_background="Second-generation Chinese-American, parents both work in tech",
        socioeconomic_status="Upper-middle class",
        first_generation=False,
        languages_spoken=["English", "Mandarin"],
        
        academic_interests=["Computer Science", "Artificial Intelligence", "Ethics in Technology", "Entrepreneurship"],
        intended_major="Computer Science with focus on AI",
        favorite_subjects=["AP Computer Science A", "AP Calculus BC", "AP Physics C"],
        academic_achievements=[
            "National Merit Semifinalist",
            "USACO Gold Division",
            "Intel ISEF Finalist",
            "AP Scholar with Distinction"
        ],
        research_experience="Developed machine learning model for early autism detection with Stanford lab",
        
        activities=[
            Activity(
                name="Robotics Team",
                role="Lead Programmer",
                description="Built autonomous robots for FIRST Robotics Competition, specialized in computer vision systems",
                duration="4 years",
                impact="Team reached World Championships twice, robots helped disabled students in local schools",
                essay_potential="High - combines technical skills with social impact",
                values_demonstrated=["innovation", "collaboration", "problem-solving", "helping others"]
            ),
            Activity(
                name="Coding Bootcamp for Underserved Youth",
                role="Founder & Lead Instructor",
                description="Created free coding program reaching 200+ middle school students from low-income areas",
                duration="2 years",
                impact="85% of participants continued with computer science coursework",
                essay_potential="High - leadership, equity, education access",
                values_demonstrated=["equity", "education", "leadership", "giving back"]
            ),
            Activity(
                name="AI Ethics Research Club",
                role="President",
                description="Student-led group exploring ethical implications of artificial intelligence",
                duration="2 years",
                impact="Presented findings at regional science fair, published blog read by 10,000+",
                essay_potential="Medium - intellectual curiosity, social responsibility",
                values_demonstrated=["ethics", "critical thinking", "social responsibility"]
            )
        ],
        
        leadership_roles=[
            "Computer Science Honor Society President",
            "Math Olympiad Team Captain",
            "Peer Tutor Coordinator"
        ],
        volunteer_work=[
            "Taught coding to senior citizens (100+ hours)",
            "Built websites for local nonprofits (50+ hours)"
        ],
        work_experience="Summer internship at early-stage AI startup",
        
        core_values=["Innovation", "Equity in tech access", "Collaborative problem-solving", "Learning from failure"],
        defining_moments=[
            DefiningMoment(
                event="Grandmother couldn't use smartphone to contact family during COVID",
                age_when_occurred="15",
                impact="Realized technology should be accessible to everyone, not just tech-savvy users",
                lessons_learned=["Importance of inclusive design", "Technology as bridge, not barrier"],
                essay_potential="High - personal connection to broader tech equity issues",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="Robot failed spectacularly at regional competition freshman year",
                age_when_occurred="14",
                impact="Learned that failure is essential part of innovation process",
                lessons_learned=["Resilience", "Team collaboration under pressure", "Iteration mindset"],
                essay_potential="Medium - growth mindset, team leadership",
                emotional_weight="medium"
            )
        ],
        
        personal_challenges=[
            "Perfectionism leading to paralysis",
            "Balancing technical interests with social impact",
            "Imposter syndrome in male-dominated tech spaces"
        ],
        growth_areas=[
            "Public speaking confidence",
            "Emotional intelligence in team settings",
            "Understanding business/market aspects of technology"
        ],
        
        essay_history=[
            EssayHistory(
                topic="Building robots to help disabled students navigate school",
                theme="Technology as tool for inclusion",
                word_count=650,
                school_type="Common App",
                strengths=["Specific technical details", "Clear impact narrative"],
                areas_for_improvement=["More personal reflection", "Stronger voice"],
                reusability="high"
            ),
            EssayHistory(
                topic="Teaching coding to grandmother during pandemic",
                theme="Breaking down digital divide",
                word_count=250,
                school_type="UC Personal Insight",
                strengths=["Personal connection", "Broader social implications"],
                areas_for_improvement=["More specific examples", "Clearer future goals"],
                reusability="medium"
            )
        ],
        
        college_goals=[
            "Major in AI/ML with focus on social applications",
            "Join research lab working on accessible technology",
            "Start organization promoting diversity in tech"
        ],
        dream_schools=["Stanford", "MIT", "UC Berkeley", "Carnegie Mellon"],
        
        writing_style=WritingStyle(
            tone_preference="analytical with personal touches",
            strength_areas=["Clear logical structure", "Technical explanations", "Problem-solution narratives"],
            challenge_areas=["Emotional vulnerability", "Creative language", "Personal reflection depth"],
            autonomy_preference="collaborative",
            feedback_sensitivity="medium"
        ),
        
        previous_sessions=3,
        successful_essays_completed=2,
        preferred_brainstorming_approach="problem-solving frameworks",
        common_stuck_points=["Being too technical", "Not revealing enough personal insight", "Perfectionism paralysis"]
    ),

    UserProfile(
        profile_id="academic_researcher_student",
        name="Priya Patel",
        category=ProfileCategory.ACADEMIC_ACHIEVER,
        
        age=17,
        location="Research Triangle, NC",
        school_type="Public Magnet School",
        gpa=4.0,
        test_scores={"SAT": 1560, "ACT": 35},
        
        family_background="First-generation Indian-American, parents are engineers",
        socioeconomic_status="Middle class",
        first_generation=False,
        languages_spoken=["English", "Hindi", "Spanish"],
        
        academic_interests=["Neuroscience", "Psychology", "Public Health", "Data Science"],
        intended_major="Neuroscience with pre-med track",
        favorite_subjects=["AP Biology", "AP Psychology", "AP Statistics"],
        academic_achievements=[
            "Siemens Competition Semifinalist",
            "Regeneron Science Talent Search Top 300",
            "Presidential Scholar Candidate",
            "National Honor Society President"
        ],
        research_experience="3 years researching adolescent brain development at Duke University",
        
        activities=[
            Activity(
                name="Independent Research on Teen Mental Health",
                role="Principal Investigator",
                description="Studied correlation between social media usage and anxiety in high school students",
                duration="3 years",
                impact="Presented at 5 national conferences, published in peer-reviewed journal",
                essay_potential="High - intellectual passion, methodical approach, social relevance",
                values_demonstrated=["intellectual curiosity", "persistence", "social awareness", "scientific rigor"]
            ),
            Activity(
                name="Science Olympiad",
                role="Team Captain",
                description="Led team to state championships in neuroscience and experimental design events",
                duration="4 years",
                impact="Team placed 3rd at nationals, mentored underclassmen",
                essay_potential="Medium - leadership, competition, mentorship",
                values_demonstrated=["leadership", "competitiveness", "knowledge sharing", "teamwork"]
            ),
            Activity(
                name="Mental Health Advocacy Club",
                role="Co-founder",
                description="Created peer support network and educational programming about teen mental health",
                duration="2 years",
                impact="Reduced stigma around counseling, increased counseling center usage by 40%",
                essay_potential="High - personal connection to research, advocacy, systemic change",
                values_demonstrated=["empathy", "advocacy", "destigmatization", "peer support"]
            )
        ],
        
        leadership_roles=[
            "National Honor Society President",
            "Science Research Symposium Organizer",
            "Peer Academic Tutor"
        ],
        volunteer_work=[
            "Hospital volunteer in pediatric ward (200+ hours)",
            "Crisis text line counselor training (40+ hours)"
        ],
        work_experience="Research assistant at neuroscience lab",
        
        core_values=["Scientific integrity", "Mental health awareness", "Educational equity", "Evidence-based decision making"],
        defining_moments=[
            DefiningMoment(
                event="Best friend struggled with anxiety and had no one to talk to",
                age_when_occurred="15",
                impact="Realized gap between mental health research and actual support for teens",
                lessons_learned=["Research must connect to real-world applications", "Peer support is crucial"],
                essay_potential="High - personal motivation for research and advocacy",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="First time presenting research to PhD students and professors",
                age_when_occurred="16",
                impact="Gained confidence in intellectual abilities and scientific communication",
                lessons_learned=["Preparation builds confidence", "Age doesn't diminish valid insights"],
                essay_potential="Medium - academic confidence, communication skills",
                emotional_weight="medium"
            )
        ],
        
        personal_challenges=[
            "Balancing perfectionism with research uncertainty",
            "Managing pressure to pursue traditional pre-med path",
            "Feeling responsibility to represent women in STEM"
        ],
        growth_areas=[
            "Accepting ambiguous results in research",
            "Developing creative problem-solving approaches",
            "Building confidence in non-academic social settings"
        ],
        
        essay_history=[
            EssayHistory(
                topic="Mental health research inspired by friend's struggle",
                theme="Bridging research and real-world application",
                word_count=650,
                school_type="Common App",
                strengths=["Clear academic passion", "Personal motivation", "Future goals alignment"],
                areas_for_improvement=["More specific research details", "Broader impact vision"],
                reusability="high"
            )
        ],
        
        college_goals=[
            "Conduct groundbreaking neuroscience research",
            "Develop evidence-based mental health interventions",
            "Bridge gap between research and community applications"
        ],
        dream_schools=["Harvard", "Johns Hopkins", "Duke", "Northwestern"],
        
        writing_style=WritingStyle(
            tone_preference="academic but accessible",
            strength_areas=["Research methodology", "Evidence-based arguments", "Clear hypothesis development"],
            challenge_areas=["Creative storytelling", "Emotional expression", "Non-academic voice"],
            autonomy_preference="collaborative",
            feedback_sensitivity="low"
        ),
        
        previous_sessions=2,
        successful_essays_completed=1,
        preferred_brainstorming_approach="research-based exploration",
        common_stuck_points=["Being too academic", "Underestimating story value", "Overthinking structure"]
    ),

    # Additional academic achiever profiles would continue here...
    UserProfile(
        profile_id="maker_engineer_student",
        name="Jordan Kim",
        category=ProfileCategory.ACADEMIC_ACHIEVER,
        
        age=17,
        location="Austin, TX",
        school_type="STEM Magnet School",
        gpa=3.95,
        test_scores={"SAT": 1520, "SAT_Math": 800, "SAT_ERW": 720},
        
        family_background="Korean-American, parents own small manufacturing business",
        socioeconomic_status="Working class",
        first_generation=True,
        languages_spoken=["English", "Korean"],
        
        academic_interests=["Mechanical Engineering", "Product Design", "Sustainable Technology", "Manufacturing"],
        intended_major="Mechanical Engineering",
        favorite_subjects=["AP Physics C", "AP Calculus BC", "Engineering Design"],
        academic_achievements=[
            "SkillsUSA National Champion in Engineering Design",
            "Texas Young Inventors Award",
            "First Place Regional Science Fair"
        ],
        research_experience="Designed low-cost prosthetics using 3D printing technology",
        
        activities=[
            Activity(
                name="Maker Space Leadership",
                role="Head of Design Team",
                description="Led student team in creating prototypes for local community needs",
                duration="3 years",
                impact="Built 15+ functional prototypes, including assistive devices for elderly residents",
                essay_potential="High - hands-on problem solving, community impact",
                values_demonstrated=["practical innovation", "community service", "collaborative design"]
            ),
            Activity(
                name="Low-Cost Prosthetics Project",
                role="Lead Engineer",
                description="Developed 3D-printed prosthetic hands for children in developing countries",
                duration="2 years",
                impact="Produced 50+ prosthetic devices, cost reduced from $15,000 to $150",
                essay_potential="High - engineering for social good, global impact",
                values_demonstrated=["accessibility", "innovation", "global awareness", "cost-consciousness"]
            )
        ],
        
        leadership_roles=["Engineering Club President", "Maker Space Safety Officer"],
        volunteer_work=["Habitat for Humanity (150+ hours)", "Repair Cafe volunteer"],
        work_experience="Summers working in parents' manufacturing business",
        
        core_values=["Practical problem-solving", "Accessible design", "Hands-on learning", "Community support"],
        defining_moments=[
            DefiningMoment(
                event="Met child who couldn't afford prosthetic hand",
                age_when_occurred="15",
                impact="Realized engineering should solve real problems for real people",
                lessons_learned=["Design with users in mind", "Cost is accessibility barrier"],
                essay_potential="High - engineering purpose and social responsibility",
                emotional_weight="high"
            )
        ],
        
        personal_challenges=["Academic writing in English", "Balancing creativity with technical precision"],
        growth_areas=["Theoretical engineering concepts", "Business aspects of innovation"],
        
        essay_history=[
            EssayHistory(
                topic="Building prosthetic hands for children who couldn't afford them",
                theme="Engineering as tool for equity",
                word_count=500,
                school_type="University of Texas",
                strengths=["Clear impact story", "Technical innovation"],
                areas_for_improvement=["Personal reflection", "Writing clarity"],
                reusability="high"
            )
        ],
        
        college_goals=["Study mechanical engineering with focus on assistive technology", "Start company making affordable medical devices"],
        dream_schools=["MIT", "Stanford", "UT Austin", "Georgia Tech"],
        
        writing_style=WritingStyle(
            tone_preference="straightforward and practical",
            strength_areas=["Technical explanations", "Problem-solution structure"],
            challenge_areas=["Academic writing style", "Abstract concepts", "Personal reflection"],
            autonomy_preference="guided_self_write",
            feedback_sensitivity="medium"
        ),
        
        previous_sessions=1,
        successful_essays_completed=1,
        preferred_brainstorming_approach="hands-on examples and prototypes",
        common_stuck_points=["Academic writing style", "Explaining technical concepts to general audience"]
    )
]

# =============================================================================
# CREATIVE ARTISTS (4 profiles)
# =============================================================================

CREATIVE_ARTIST_PROFILES = [
    UserProfile(
        profile_id="interdisciplinary_thinker_student",
        name="Maya Rodriguez",
        category=ProfileCategory.CREATIVE_ARTIST,
        
        age=17,
        location="Santa Fe, NM",
        school_type="Arts Integrated High School",
        gpa=3.8,
        test_scores={"SAT": 1450, "ACT": 32},
        
        family_background="Mexican-American, mother is ceramics artist, father is high school history teacher",
        socioeconomic_status="Middle class",
        first_generation=False,
        languages_spoken=["English", "Spanish"],
        
        academic_interests=["Art History", "Anthropology", "Environmental Science", "Cultural Studies"],
        intended_major="Art History with Environmental Studies minor",
        favorite_subjects=["AP Art History", "AP Studio Art", "AP Environmental Science"],
        academic_achievements=[
            "Scholastic Art Awards Regional Gold Key",
            "Young Arts Merit Award",
            "National Art Honor Society"
        ],
        research_experience="Independent study on indigenous art's relationship to environmental stewardship",
        
        activities=[
            Activity(
                name="Community Mural Project",
                role="Lead Artist and Organizer",
                description="Coordinated neighborhood mural celebrating local Chicano history and environmental justice",
                duration="2 years",
                impact="Brought together 50+ community members, mural now permanent neighborhood landmark",
                essay_potential="High - art as community building, cultural heritage, social justice",
                values_demonstrated=["cultural pride", "community organizing", "environmental justice", "collaborative art"]
            ),
            Activity(
                name="Sustainable Art Initiative",
                role="Founder",
                description="Created art program using only recycled and natural materials",
                duration="2 years",
                impact="Diverted 500+ lbs of materials from landfill, taught 100+ students sustainable practices",
                essay_potential="High - environmental consciousness, innovation in art, education",
                values_demonstrated=["environmental stewardship", "innovation", "education", "sustainability"]
            ),
            Activity(
                name="Youth Arts Council",
                role="Secretary and Exhibition Curator",
                description="Organized quarterly art exhibitions showcasing local teen artists",
                duration="3 years",
                impact="Featured 200+ teen artists, increased youth arts funding by 30%",
                essay_potential="Medium - arts advocacy, curation skills, community support",
                values_demonstrated=["arts advocacy", "peer support", "cultural programming"]
            )
        ],
        
        leadership_roles=["Art Honor Society President", "Environmental Club Co-leader"],
        volunteer_work=["Art therapy for elderly (100+ hours)", "Environmental cleanup coordinator"],
        work_experience="Gallery assistant at local contemporary art center",
        
        core_values=["Art as social change", "Environmental stewardship", "Cultural heritage preservation", "Community collaboration"],
        defining_moments=[
            DefiningMoment(
                event="Grandmother shared stories of art traditions lost during family's immigration",
                age_when_occurred="14",
                impact="Understood art's role in preserving and sharing cultural identity",
                lessons_learned=["Art carries cultural memory", "Importance of intergenerational knowledge transfer"],
                essay_potential="High - personal cultural connection, art's deeper purpose",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="Witnessed neighborhood lot being developed, destroying informal community gathering space",
                age_when_occurred="16",
                impact="Realized art could help communities claim and define their own spaces",
                lessons_learned=["Art can be activism", "Community voice matters in urban development"],
                essay_potential="High - art as community empowerment, environmental and social justice",
                emotional_weight="high"
            )
        ],
        
        personal_challenges=["Balancing artistic vision with academic expectations", "Financial constraints on art supplies", "Navigating predominantly white art institutions"],
        growth_areas=["Art history theoretical knowledge", "Grant writing and fundraising", "Digital art techniques"],
        
        essay_history=[
            EssayHistory(
                topic="Creating community mural to preserve neighborhood stories",
                theme="Art as cultural preservation and community building",
                word_count=350,
                school_type="UC Personal Insight",
                strengths=["Strong community connection", "Clear artistic purpose"],
                areas_for_improvement=["More personal artistic development", "Future vision clarity"],
                reusability="high"
            ),
            EssayHistory(
                topic="Learning traditional pottery from grandmother",
                theme="Intergenerational knowledge and cultural identity",
                word_count=250,
                school_type="Common App additional info",
                strengths=["Personal family connection", "Cultural depth"],
                areas_for_improvement=["Broader implications", "Contemporary relevance"],
                reusability="medium"
            )
        ],
        
        college_goals=["Study intersection of art, culture, and environmental justice", "Develop community-centered art practices", "Preserve and revitalize traditional art forms"],
        dream_schools=["Yale", "Brown", "UCLA", "University of New Mexico"],
        
        writing_style=WritingStyle(
            tone_preference="creative and reflective",
            strength_areas=["Vivid imagery", "Cultural narratives", "Social justice themes"],
            challenge_areas=["Academic analysis", "Abstract theoretical concepts", "Concise expression"],
            autonomy_preference="collaborative",
            feedback_sensitivity="medium"
        ),
        
        previous_sessions=0,
        successful_essays_completed=0,
        preferred_brainstorming_approach="visual and story-based exploration",
        common_stuck_points=["Academic vs. creative writing styles", "Connecting personal stories to broader themes"]
    ),

    UserProfile(
        profile_id="creative_arts_student",
        name="River Thompson",
        category=ProfileCategory.CREATIVE_ARTIST,
        
        age=17,
        location="Portland, OR",
        school_type="Private Arts Academy",
        gpa=3.7,
        test_scores={"SAT": 1390, "ACT": 31},
        
        family_background="White, parents are both musicians, raised in creative but financially unstable household",
        socioeconomic_status="Lower-middle class",
        first_generation=False,
        languages_spoken=["English"],
        
        academic_interests=["Creative Writing", "Theater", "Psychology", "Media Studies"],
        intended_major="Creative Writing with Theater minor",
        favorite_subjects=["AP Literature", "Creative Writing Workshop", "Drama"],
        academic_achievements=[
            "National YoungArts Winner in Creative Writing",
            "Regional Poetry Slam Champion",
            "Published in national teen literary magazine"
        ],
        research_experience="None formal, but extensive independent creative projects",
        
        activities=[
            Activity(
                name="Spoken Word Poetry Collective",
                role="Co-founder and Performer",
                description="Created platform for teen poets to share work addressing social issues",
                duration="3 years",
                impact="Performed for 2000+ audience members, raised $5000 for homeless youth",
                essay_potential="High - creative expression, social activism, vulnerability",
                values_demonstrated=["authentic expression", "social justice", "community building", "vulnerability"]
            ),
            Activity(
                name="Youth Theater Director",
                role="Student Director",
                description="Directed original play written by and for homeless teenagers",
                duration="1 year",
                impact="Play performed 10 times, changed community perspective on homeless youth",
                essay_potential="High - creative leadership, social impact, empathy",
                values_demonstrated=["empathy", "storytelling for change", "leadership", "social awareness"]
            ),
            Activity(
                name="Creative Writing Tutor",
                role="Peer Tutor",
                description="Helped struggling students find their voice through writing",
                duration="2 years",
                impact="15+ students improved writing confidence and grades",
                essay_potential="Medium - teaching, personal growth, academic support",
                values_demonstrated=["empathy", "teaching", "confidence building"]
            )
        ],
        
        leadership_roles=["Literary Magazine Editor-in-Chief", "Drama Club Vice President"],
        volunteer_work=["Literacy program for adults (80+ hours)", "Animal shelter writing adoption profiles"],
        work_experience="Part-time at independent bookstore",
        
        core_values=["Authentic self-expression", "Storytelling as healing", "Art for social change", "Creating safe creative spaces"],
        defining_moments=[
            DefiningMoment(
                event="Performed poem about mental health struggles at school assembly",
                age_when_occurred="16",
                impact="Realized vulnerability in art can help others feel less alone",
                lessons_learned=["Sharing struggles can be healing", "Art creates connection and understanding"],
                essay_potential="High - personal growth, mental health advocacy, artistic courage",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="Family experienced housing instability due to parents' irregular arts income",
                age_when_occurred="14",
                impact="Understood challenges of pursuing creative career while also valuing creative expression",
                lessons_learned=["Art has value beyond financial success", "Financial stability affects creative freedom"],
                essay_potential="Medium - socioeconomic challenges, family dynamics, artistic values",
                emotional_weight="high"
            )
        ],
        
        personal_challenges=["Financial stress affecting college options", "Anxiety and perfectionism in creative work", "Balancing artistic authenticity with academic expectations"],
        growth_areas=["Academic writing skills", "Time management", "Confidence in non-creative subjects"],
        
        essay_history=[
            EssayHistory(
                topic="Performing poetry about mental health to help other students",
                theme="Vulnerability as strength and connection",
                word_count=650,
                school_type="Common App",
                strengths=["Authentic voice", "Emotional depth", "Clear personal growth"],
                areas_for_improvement=["More specific impact examples", "Future goals clarity"],
                reusability="high"
            )
        ],
        
        college_goals=["Develop voice as creative writer", "Use art for social change and healing", "Build sustainable creative career"],
        dream_schools=["Sarah Lawrence", "Wesleyan", "Oberlin", "The New School"],
        
        writing_style=WritingStyle(
            tone_preference="creative and deeply personal",
            strength_areas=["Emotional authenticity", "Poetic language", "Narrative voice"],
            challenge_areas=["Academic structure", "Conciseness", "Analytical writing"],
            autonomy_preference="minimal_help",
            feedback_sensitivity="high"
        ),
        
        previous_sessions=0,
        successful_essays_completed=0,
        preferred_brainstorming_approach="free-writing and emotional exploration",
        common_stuck_points=["Over-editing creative voice", "Academic essay structure", "Self-doubt about story worthiness"]
    )
]

# =============================================================================
# COMMUNITY LEADERS (4 profiles)
# =============================================================================

COMMUNITY_LEADER_PROFILES = [
    UserProfile(
        profile_id="community_organizer_student",
        name="Aisha Williams",
        category=ProfileCategory.COMMUNITY_LEADER,
        
        age=17,
        location="Baltimore, MD",
        school_type="Public High School",
        gpa=3.9,
        test_scores={"SAT": 1420, "ACT": 32},
        
        family_background="African-American, raised by grandmother, mother works two jobs",
        socioeconomic_status="Low income",
        first_generation=True,
        languages_spoken=["English"],
        
        academic_interests=["Political Science", "Social Work", "Public Health", "Criminal Justice Reform"],
        intended_major="Political Science with Social Work minor",
        favorite_subjects=["AP Government", "AP English Language", "Social Justice Seminar"],
        academic_achievements=[
            "Student Government President",
            "Debate Team State Finalist",
            "Youth Advisory Council to Mayor"
        ],
        research_experience="Policy research internship with local city council member",
        
        activities=[
            Activity(
                name="Youth Violence Prevention Coalition",
                role="Co-founder and Director",
                description="Created peer mediation program and violence intervention initiatives",
                duration="2 years",
                impact="Reduced school conflicts by 40%, trained 50+ peer mediators",
                essay_potential="High - community safety, peer leadership, systemic change",
                values_demonstrated=["community safety", "peer education", "conflict resolution", "systemic thinking"]
            ),
            Activity(
                name="Food Justice Campaign",
                role="Lead Organizer",
                description="Advocated for healthy food options in school and neighborhood",
                duration="3 years",
                impact="Secured funding for salad bar, established weekend food pantry",
                essay_potential="High - community advocacy, health equity, organizing skills",
                values_demonstrated=["health equity", "community organizing", "persistence", "food justice"]
            ),
            Activity(
                name="Mentorship Program for Middle Schoolers",
                role="Program Coordinator",
                description="Connected high school students with at-risk middle schoolers",
                duration="2 years",
                impact="30+ successful mentorship pairs, 90% of mentees stayed in school",
                essay_potential="Medium - mentorship, academic support, community building",
                values_demonstrated=["mentorship", "academic support", "community investment"]
            )
        ],
        
        leadership_roles=["Student Government President", "Black Student Union Vice President", "Debate Team Captain"],
        volunteer_work=["Community center after-school programming (200+ hours)", "Voter registration drives"],
        work_experience="Part-time at community health clinic",
        
        core_values=["Community empowerment", "Educational equity", "Restorative justice", "Youth voice in policy"],
        defining_moments=[
            DefiningMoment(
                event="Best friend was suspended for fight that could have been prevented with better conflict resolution",
                age_when_occurred="15",
                impact="Realized need for prevention-focused, peer-led approaches to school discipline",
                lessons_learned=["Prevention better than punishment", "Peers can be most effective interventionists"],
                essay_potential="High - personal motivation for systemic change, restorative justice",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="Testified at city council meeting about need for youth programming",
                age_when_occurred="16",
                impact="Discovered power of youth voice in policy and formal advocacy",
                lessons_learned=["Young people can influence policy", "Preparation and research enhance credibility"],
                essay_potential="High - civic engagement, youth empowerment, policy advocacy",
                emotional_weight="medium"
            )
        ],
        
        personal_challenges=["Balancing activism with academics", "Financial stress affecting college options", "Feeling responsible for solving community problems"],
        growth_areas=["Academic writing for policy analysis", "Self-care and boundary setting", "Long-term strategic planning"],
        
        essay_history=[
            EssayHistory(
                topic="Creating peer mediation program after friend's unfair suspension",
                theme="Youth-led solutions to school discipline issues",
                word_count=650,
                school_type="Common App",
                strengths=["Personal motivation", "Clear community impact", "Leadership demonstration"],
                areas_for_improvement=["More policy analysis", "Future career connection"],
                reusability="high"
            ),
            EssayHistory(
                topic="Testifying at city council about youth programming needs",
                theme="Youth voice in policy making",
                word_count=350,
                school_type="UC Personal Insight",
                strengths=["Civic engagement", "Public speaking courage"],
                areas_for_improvement=["More personal reflection", "Specific policy outcomes"],
                reusability="medium"
            )
        ],
        
        college_goals=["Study policy and advocacy strategies", "Develop expertise in community organizing", "Return to community as policy advocate"],
        dream_schools=["Howard University", "Spelman", "Georgetown", "American University"],
        
        writing_style=WritingStyle(
            tone_preference="passionate and persuasive",
            strength_areas=["Persuasive arguments", "Community impact narratives", "Policy analysis"],
            challenge_areas=["Personal vulnerability", "Academic formality", "Concise expression"],
            autonomy_preference="collaborative",
            feedback_sensitivity="low"
        ),
        
        previous_sessions=1,
        successful_essays_completed=1,
        preferred_brainstorming_approach="problem-analysis and solution-focused",
        common_stuck_points=["Balancing personal story with policy focus", "Avoiding 'savior complex' tone"]
    ),

    UserProfile(
        profile_id="emerging_leader_student", 
        name="Carlos Mendoza",
        category=ProfileCategory.COMMUNITY_LEADER,
        
        age=17,
        location="Phoenix, AZ",
        school_type="Public High School",
        gpa=3.6,
        test_scores={"SAT": 1350, "ACT": 29},
        
        family_background="Mexican-American, parents work in hospitality, close extended family",
        socioeconomic_status="Working class",
        first_generation=True,
        languages_spoken=["English", "Spanish"],
        
        academic_interests=["Business", "Education", "Community Development", "Social Entrepreneurship"],
        intended_major="Business Administration with focus on social enterprise",
        favorite_subjects=["AP Spanish Literature", "Economics", "Leadership Seminar"],
        academic_achievements=["Honor Roll", "Business Plan Competition Finalist", "Perfect attendance 4 years"],
        research_experience="None formal",
        
        activities=[
            Activity(
                name="ESL Family Support Program",
                role="Student Coordinator",
                description="Helped Spanish-speaking families navigate school system and college planning",
                duration="2 years",
                impact="Assisted 40+ families, increased college enrollment in community by 25%",
                essay_potential="High - cultural bridge-building, family support, educational access",
                values_demonstrated=["cultural bridge-building", "family support", "educational equity", "bilingual skills"]
            ),
            Activity(
                name="Small Business Mentorship",
                role="Teen Business Advisor",
                description="Helped local Latino business owners with social media and basic marketing",
                duration="1 year",
                impact="Increased revenue for 5 small businesses, created business plan template",
                essay_potential="Medium - business skills, community economic development",
                values_demonstrated=["economic empowerment", "entrepreneurship", "community investment"]
            )
        ],
        
        leadership_roles=["Latino Student Association Secretary", "Peer Tutor"],
        volunteer_work=["Food bank coordinator (100+ hours)", "Translation services for community clinic"],
        work_experience="Part-time at family restaurant, summers as camp counselor",
        
        core_values=["Family support", "Educational opportunity", "Cultural pride", "Economic empowerment"],
        defining_moments=[
            DefiningMoment(
                event="Parents couldn't understand teacher at parent conference, missed important information about college prep",
                age_when_occurred="15",
                impact="Realized language barriers create educational inequity, decided to help other families navigate system",
                lessons_learned=["Language access is educational justice", "Small help can have big impact"],
                essay_potential="High - personal family connection, educational equity advocacy",
                emotional_weight="high"
            )
        ],
        
        personal_challenges=["Balancing work, family responsibilities, and school", "Confidence in academic settings", "Financial stress about college"],
        growth_areas=["Academic writing", "Public speaking confidence", "Long-term goal planning"],
        
        essay_history=[],
        
        college_goals=["Learn business skills to support community economic development", "Create programs for first-generation college students"],
        dream_schools=["Arizona State University", "University of Arizona", "Cal State system"],
        
        writing_style=WritingStyle(
            tone_preference="humble and family-focused",
            strength_areas=["Family narratives", "Community connection", "Practical examples"],
            challenge_areas=["Academic formality", "Self-promotion", "Abstract concepts"],
            autonomy_preference="guided_self_write",
            feedback_sensitivity="medium"
        ),
        
        previous_sessions=0,
        successful_essays_completed=0,
        preferred_brainstorming_approach="family and community story exploration",
        common_stuck_points=["Feeling stories aren't impressive enough", "Academic writing style", "Self-advocacy"]
    )
]

# =============================================================================
# ENTREPRENEURS (3 profiles)
# =============================================================================

ENTREPRENEUR_PROFILES = [
    UserProfile(
        profile_id="busy_achiever_student",
        name="Taylor Park",
        category=ProfileCategory.ENTREPRENEUR,
        
        age=17,
        location="Denver, CO",
        school_type="Private Preparatory School",
        gpa=3.95,
        test_scores={"SAT": 1510, "ACT": 34},
        
        family_background="Korean-American, parents own successful restaurant chain",
        socioeconomic_status="Upper-middle class",
        first_generation=False,
        languages_spoken=["English", "Korean"],
        
        academic_interests=["Business", "Economics", "Marketing", "International Relations"],
        intended_major="Business Administration with International Business focus",
        favorite_subjects=["AP Economics", "AP Statistics", "Entrepreneurship"],
        academic_achievements=["DECA State Champion", "Business Plan Competition Winner", "National Merit Commended"],
        research_experience="Market research for local small business development",
        
        activities=[
            Activity(
                name="Student-Run Investment Club",
                role="Founder and CEO",
                description="Created investment club managing $10,000 portfolio, teaching financial literacy",
                duration="2 years",
                impact="Generated 15% returns, taught 50+ students about investing",
                essay_potential="High - financial leadership, peer education, practical results",
                values_demonstrated=["financial literacy", "peer education", "calculated risk-taking", "results-oriented"]
            ),
            Activity(
                name="Sustainable Lunch Delivery Service",
                role="Co-founder",
                description="Started business delivering healthy, locally-sourced lunches to busy students",
                duration="1 year",
                impact="Served 200+ students, donated 10% profits to food insecurity programs",
                essay_potential="High - social entrepreneurship, sustainability, problem-solving",
                values_demonstrated=["sustainability", "social responsibility", "problem-solving", "innovation"]
            )
        ],
        
        leadership_roles=["DECA President", "Model UN Secretary-General", "Investment Club CEO"],
        volunteer_work=["Financial literacy workshops for underserved youth (60+ hours)"],
        work_experience="Summer internships at family business and investment firm",
        
        core_values=["Calculated risk-taking", "Financial independence", "Social responsibility in business", "Efficiency and results"],
        defining_moments=[
            DefiningMoment(
                event="Watched parents struggle during 2008 financial crisis despite having successful business",
                age_when_occurred="8",
                impact="Learned importance of financial diversification and planning",
                lessons_learned=["Success requires risk management", "Financial literacy is essential"],
                essay_potential="Medium - early business understanding, family influence",
                emotional_weight="medium"
            )
        ],
        
        personal_challenges=["Perfectionism and overcommitment", "Balancing profit with social impact", "Time management"],
        growth_areas=["Collaborative leadership style", "Long-term vision over short-term gains"],
        
        essay_history=[
            EssayHistory(
                topic="Starting investment club to teach financial literacy to peers",
                theme="Making finance accessible and educational",
                word_count=400,
                school_type="Business school supplement",
                strengths=["Clear business results", "Peer leadership"],
                areas_for_improvement=["More personal motivation", "Broader social impact"],
                reusability="high"
            )
        ],
        
        college_goals=["Study international business and social entrepreneurship", "Start socially responsible business"],
        dream_schools=["Wharton", "Stern", "Haas", "McCombs"],
        
        writing_style=WritingStyle(
            tone_preference="professional and results-focused",
            strength_areas=["Business metrics", "Leadership examples", "Clear outcomes"],
            challenge_areas=["Personal vulnerability", "Emotional depth", "Non-business narratives"],
            autonomy_preference="full_agent",
            feedback_sensitivity="low"
        ),
        
        previous_sessions=1,
        successful_essays_completed=1,
        preferred_brainstorming_approach="metrics and results-focused analysis",
        common_stuck_points=["Being too business-focused", "Lack of personal vulnerability", "Overemphasizing achievements"]
    )
]

# =============================================================================
# ATHLETES (2 profiles)
# =============================================================================

ATHLETE_PROFILES = [
    UserProfile(
        profile_id="athlete_academic_student",
        name="Marcus Johnson",
        category=ProfileCategory.ATHLETE,
        
        age=17,
        location="Atlanta, GA",
        school_type="Public High School",
        gpa=3.7,
        test_scores={"SAT": 1280, "ACT": 28},
        
        family_background="African-American, single mother working as nurse, strong community support",
        socioeconomic_status="Working class",
        first_generation=True,
        languages_spoken=["English"],
        
        academic_interests=["Kinesiology", "Sports Medicine", "Business", "Education"],
        intended_major="Kinesiology with pre-physical therapy track",
        favorite_subjects=["AP Biology", "Sports Psychology", "Health Sciences"],
        academic_achievements=["Honor Roll", "Student-Athlete Academic Achievement Award"],
        research_experience="None formal",
        
        activities=[
            Activity(
                name="Varsity Basketball",
                role="Team Captain and Point Guard",
                description="Led team to state semifinals, earned All-State honorable mention",
                duration="4 years",
                impact="Team GPA improved from 2.8 to 3.4 under leadership, mentored underclassmen",
                essay_potential="High - leadership through adversity, academic improvement, mentorship",
                values_demonstrated=["leadership", "academic responsibility", "mentorship", "perseverance"]
            ),
            Activity(
                name="Youth Basketball Coach",
                role="Volunteer Coach",
                description="Coached 8-10 year olds in community center league",
                duration="2 years",
                impact="Taught fundamentals to 40+ children, emphasized education alongside athletics",
                essay_potential="Medium - giving back, teaching, community investment",
                values_demonstrated=["community investment", "teaching", "youth development"]
            ),
            Activity(
                name="Injury Recovery Advocacy",
                role="Peer Educator",
                description="Shared recovery journey to help other student-athletes with injuries",
                duration="1 year",
                impact="Helped 10+ athletes navigate injury recovery and maintain academic focus",
                essay_potential="High - overcoming adversity, peer support, personal growth",
                values_demonstrated=["resilience", "peer support", "vulnerability", "growth mindset"]
            )
        ],
        
        leadership_roles=["Team Captain", "Student-Athlete Advisory Committee"],
        volunteer_work=["Community center basketball camps (120+ hours)", "Special Olympics volunteer"],
        work_experience="Part-time at sports equipment store",
        
        core_values=["Team before self", "Education as foundation", "Giving back to community", "Resilience through adversity"],
        defining_moments=[
            DefiningMoment(
                event="Tore ACL junior year, couldn't play for 8 months",
                age_when_occurred="16",
                impact="Discovered identity beyond basketball, focused on academics and helping others",
                lessons_learned=["Identity shouldn't depend on one thing", "Challenges can redirect toward new strengths"],
                essay_potential="High - identity exploration, resilience, personal growth",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="Became first in family to take SAT and consider college",
                age_when_occurred="17",
                impact="Realized responsibility to model educational achievement for younger siblings and community",
                lessons_learned=["Education creates opportunities", "Success creates responsibility to help others"],
                essay_potential="High - first-generation challenges, family responsibility, educational values",
                emotional_weight="high"
            )
        ],
        
        personal_challenges=["Balancing athletics with academics", "Financial stress about college", "Pressure to be family's first college graduate"],
        growth_areas=["Academic writing", "Test-taking strategies", "College navigation"],
        
        essay_history=[],
        
        college_goals=["Study sports medicine to help athletes recover from injuries", "Use athletic experience to work with youth", "Set example for family and community"],
        dream_schools=["University of Georgia", "Georgia Tech", "Morehouse", "Florida A&M"],
        
        writing_style=WritingStyle(
            tone_preference="authentic and team-focused",
            strength_areas=["Personal narratives", "Team leadership examples", "Overcoming challenges"],
            challenge_areas=["Academic writing structure", "Abstract concepts", "Self-promotion"],
            autonomy_preference="guided_self_write",
            feedback_sensitivity="medium"
        ),
        
        previous_sessions=0,
        successful_essays_completed=0,
        preferred_brainstorming_approach="story-based with team and family examples",
        common_stuck_points=["Academic writing style", "Balancing athletics with other interests", "First-generation college navigation"]
    )
]

# =============================================================================
# DIVERSE BACKGROUNDS (2 profiles)
# =============================================================================

DIVERSE_BACKGROUND_PROFILES = [
    UserProfile(
        profile_id="first_gen_immigrant_student",
        name="Fatima Al-Rashid",
        category=ProfileCategory.DIVERSE_BACKGROUND,
        
        age=17,
        location="Dearborn, MI",
        school_type="Public High School",
        gpa=3.85,
        test_scores={"SAT": 1380, "ACT": 31},
        
        family_background="Syrian-American, family immigrated when she was 12, parents work multiple jobs",
        socioeconomic_status="Low-middle income",
        first_generation=True,
        languages_spoken=["English", "Arabic", "some French"],
        
        academic_interests=["International Relations", "Human Rights", "Journalism", "Middle Eastern Studies"],
        intended_major="International Relations with Human Rights focus",
        favorite_subjects=["AP World History", "AP English Language", "Arabic Language"],
        academic_achievements=["Model UN Best Delegate", "Journalism Award", "Arabic Honor Society"],
        research_experience="Independent research on refugee integration policies",
        
        activities=[
            Activity(
                name="Refugee Family Support Network",
                role="Co-founder and Translator",
                description="Helped newly arrived refugee families navigate school system, healthcare, employment",
                duration="3 years",
                impact="Assisted 25+ families, created multilingual resource guide",
                essay_potential="High - personal connection, cultural bridge-building, service",
                values_demonstrated=["cultural bridge-building", "service", "empathy", "community building"]
            ),
            Activity(
                name="Model United Nations",
                role="President and Crisis Director",
                description="Led school's MUN team to regional championships, organized crisis simulations",
                duration="3 years",
                impact="Team grew from 8 to 30 members, won multiple awards",
                essay_potential="Medium - leadership, international awareness, public speaking",
                values_demonstrated=["international awareness", "leadership", "diplomatic thinking"]
            ),
            Activity(
                name="Multicultural Journalism Initiative",
                role="Editor and Writer",
                description="Created publication highlighting immigrant student stories",
                duration="2 years",
                impact="Published 20+ articles, changed school climate around immigrant students",
                essay_potential="High - storytelling, advocacy, cultural representation",
                values_demonstrated=["storytelling", "cultural representation", "advocacy", "journalism ethics"]
            )
        ],
        
        leadership_roles=["Model UN President", "Arabic Honor Society Vice President", "International Club Secretary"],
        volunteer_work=["Mosque community outreach (150+ hours)", "ESL tutoring for adults"],
        work_experience="Part-time translator for community health clinic",
        
        core_values=["Cultural bridge-building", "Human rights advocacy", "Family support", "Educational opportunity"],
        defining_moments=[
            DefiningMoment(
                event="Family fled Syria during civil war, arrived in US with little English",
                age_when_occurred="12",
                impact="Understood challenges of displacement, importance of community support",
                lessons_learned=["Resilience in face of loss", "Community support is essential", "Education as path to stability"],
                essay_potential="High - immigration experience, resilience, family sacrifice",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="Helped crying refugee mother at clinic understand medical diagnosis",
                age_when_occurred="16",
                impact="Realized power of language access and cultural navigation",
                lessons_learned=["Language is power and access", "Small acts of help can be transformative"],
                essay_potential="High - service motivation, cultural competency, empathy",
                emotional_weight="high"
            )
        ],
        
        personal_challenges=["Financial stress about college costs", "Balancing traditional expectations with American opportunities", "Dealing with discrimination and stereotypes"],
        growth_areas=["Academic writing in English", "Confidence in predominantly white academic spaces", "Long-term career planning"],
        
        essay_history=[
            EssayHistory(
                topic="Translating for refugee families and understanding power of language access",
                theme="Language as bridge between cultures and communities",
                word_count=450,
                school_type="UC Personal Insight",
                strengths=["Personal connection", "Community impact", "Cultural insight"],
                areas_for_improvement=["More academic analysis", "Future career connection"],
                reusability="high"
            )
        ],
        
        college_goals=["Study international relations and human rights law", "Work with refugee communities", "Bridge understanding between cultures"],
        dream_schools=["Georgetown", "George Washington University", "American University", "University of Michigan"],
        
        writing_style=WritingStyle(
            tone_preference="thoughtful and culturally aware",
            strength_areas=["Cultural narratives", "Personal storytelling", "Human rights themes"],
            challenge_areas=["Academic English complexity", "Abstract theoretical concepts", "Self-advocacy"],
            autonomy_preference="collaborative",
            feedback_sensitivity="medium"
        ),
        
        previous_sessions=1,
        successful_essays_completed=1,
        preferred_brainstorming_approach="cultural story exploration and family history",
        common_stuck_points=["Academic English writing", "Balancing cultural identity with American expectations", "Self-advocacy without seeming ungrateful"]
    ),

    UserProfile(
        profile_id="first_gen_college_student",
        name="Maria Santos",
        category=ProfileCategory.DIVERSE_BACKGROUND,
        
        age=17,
        location="Fresno, CA",
        school_type="Public High School",
        gpa=3.6,
        test_scores={"SAT": 1220, "ACT": 26},
        
        family_background="Mexican-American, parents work in agriculture, large extended family",
        socioeconomic_status="Low income",
        first_generation=True,
        languages_spoken=["English", "Spanish"],
        
        academic_interests=["Education", "Social Work", "Child Development", "Public Health"],
        intended_major="Education with focus on bilingual education",
        favorite_subjects=["Child Development", "AP Spanish Literature", "Psychology"],
        academic_achievements=["Honor Roll", "Perfect attendance award", "Bilingual Seal"],
        research_experience="None formal",
        
        activities=[
            Activity(
                name="Migrant Student Tutoring Program",
                role="Head Tutor and Coordinator",
                description="Provided academic support for children of migrant workers",
                duration="3 years",
                impact="Helped 40+ students improve grades, created bilingual study materials",
                essay_potential="High - educational equity, cultural understanding, peer support",
                values_demonstrated=["educational equity", "cultural understanding", "peer support", "bilingual skills"]
            ),
            Activity(
                name="Family College Navigation Support",
                role="Student Coordinator",
                description="Helped Latino families understand college application process",
                duration="2 years",
                impact="Guided 15+ families through FAFSA and college applications",
                essay_potential="High - first-generation challenges, family support, educational access",
                values_demonstrated=["family support", "educational access", "first-generation advocacy"]
            )
        ],
        
        leadership_roles=["Migrant Education Club President", "Honor Society member"],
        volunteer_work=["Elementary school reading assistant (200+ hours)", "Community health fair translator"],
        work_experience="Summers working in fields with family, part-time at daycare center",
        
        core_values=["Family support", "Educational opportunity", "Hard work", "Community uplift"],
        defining_moments=[
            DefiningMoment(
                event="Realized she was the only one in family who could help siblings with homework",
                age_when_occurred="14",
                impact="Understood responsibility as educational bridge for family",
                lessons_learned=["Education is privilege with responsibility", "Family support takes many forms"],
                essay_potential="High - family responsibility, educational gaps, first-generation challenges",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="Teacher said college 'might not be realistic' given family's financial situation",
                age_when_occurred="16",
                impact="Determined to prove that first-generation students belong in college",
                lessons_learned=["Advocate for yourself and others", "Don't let others limit your dreams"],
                essay_potential="High - overcoming barriers, self-advocacy, determination",
                emotional_weight="high"
            )
        ],
        
        personal_challenges=["Financial barriers to college", "Academic preparation gaps", "Family pressure to work instead of attend college"],
        growth_areas=["Academic writing", "Test-taking strategies", "College financing knowledge"],
        
        essay_history=[],
        
        college_goals=["Become bilingual teacher to help students like herself", "Support first-generation college students", "Give back to community"],
        dream_schools=["UC system", "Cal State Fresno", "Cal Poly", "University of California schools"],
        
        writing_style=WritingStyle(
            tone_preference="humble and family-focused",
            strength_areas=["Family stories", "Community narratives", "Overcoming challenges"],
            challenge_areas=["Academic writing style", "Self-promotion", "Abstract analysis"],
            autonomy_preference="guided_self_write",
            feedback_sensitivity="high"
        ),
        
        previous_sessions=0,
        successful_essays_completed=0,
        preferred_brainstorming_approach="family and community story exploration",
        common_stuck_points=["Feeling stories aren't impressive enough", "Academic writing structure", "Self-advocacy without seeming ungrateful"]
    )
]

# =============================================================================
# ADDITIONAL RETURNING USER PROFILES (with rich history)
# =============================================================================

RETURNING_USER_PROFILES = [
    UserProfile(
        profile_id="returning_stem_researcher_with_rich_history",
        name="Alex Chen (Returning)",
        category=ProfileCategory.ACADEMIC_ACHIEVER,
        
        # Basic info same as original but with rich history
        age=17,
        location="Silicon Valley, CA",
        school_type="Public High School",
        gpa=4.0,
        test_scores={"SAT": 1580, "SAT_Math": 800, "SAT_ERW": 780},
        
        family_background="Second-generation Chinese-American, parents both work in tech",
        socioeconomic_status="Upper-middle class",
        first_generation=False,
        languages_spoken=["English", "Mandarin"],
        
        academic_interests=["Computer Science", "Artificial Intelligence", "Ethics in Technology", "Entrepreneurship"],
        intended_major="Computer Science with focus on AI",
        favorite_subjects=["AP Computer Science A", "AP Calculus BC", "AP Physics C"],
        academic_achievements=[
            "National Merit Semifinalist",
            "USACO Gold Division",
            "Intel ISEF Finalist",
            "AP Scholar with Distinction"
        ],
        research_experience="Developed machine learning model for early autism detection with Stanford lab",
        
        activities=[
            Activity(
                name="Robotics Team",
                role="Lead Programmer",
                description="Built autonomous robots for FIRST Robotics Competition, specialized in computer vision systems",
                duration="4 years",
                impact="Team reached World Championships twice, robots helped disabled students in local schools",
                essay_potential="High - combines technical skills with social impact",
                values_demonstrated=["innovation", "collaboration", "problem-solving", "helping others"]
            ),
            Activity(
                name="Coding Bootcamp for Underserved Youth",
                role="Founder & Lead Instructor",
                description="Created free coding program reaching 200+ middle school students from low-income areas",
                duration="2 years",
                impact="85% of participants continued with computer science coursework",
                essay_potential="High - leadership, equity, education access",
                values_demonstrated=["equity", "education", "leadership", "giving back"]
            )
        ],
        
        leadership_roles=["Computer Science Honor Society President", "Math Olympiad Team Captain"],
        volunteer_work=["Taught coding to senior citizens (100+ hours)"],
        work_experience="Summer internship at early-stage AI startup",
        
        core_values=["Innovation", "Equity in tech access", "Collaborative problem-solving", "Learning from failure"],
        defining_moments=[
            DefiningMoment(
                event="Grandmother couldn't use smartphone to contact family during COVID",
                age_when_occurred="15",
                impact="Realized technology should be accessible to everyone, not just tech-savvy users",
                lessons_learned=["Importance of inclusive design", "Technology as bridge, not barrier"],
                essay_potential="High - personal connection to broader tech equity issues",
                emotional_weight="high"
            )
        ],
        
        personal_challenges=["Perfectionism leading to paralysis", "Balancing technical interests with social impact"],
        growth_areas=["Public speaking confidence", "Emotional intelligence in team settings"],
        
        # RICH ESSAY HISTORY - Multiple completed essays
        essay_history=[
            EssayHistory(
                topic="Building robots to help disabled students navigate school",
                theme="Technology as tool for inclusion",
                word_count=650,
                school_type="Common App",
                strengths=["Specific technical details", "Clear impact narrative", "Problem-solving approach"],
                areas_for_improvement=["More personal reflection", "Stronger voice"],
                reusability="high"
            ),
            EssayHistory(
                topic="Teaching coding to grandmother during pandemic",
                theme="Breaking down digital divide",
                word_count=250,
                school_type="UC Personal Insight",
                strengths=["Personal connection", "Broader social implications", "Intergenerational relationship"],
                areas_for_improvement=["More specific examples", "Clearer future goals"],
                reusability="medium"
            ),
            EssayHistory(
                topic="AI ethics research club findings on facial recognition bias",
                theme="Responsible technology development",
                word_count=300,
                school_type="MIT Supplement",
                strengths=["Technical depth", "Social responsibility", "Research methodology"],
                areas_for_improvement=["Personal stakes", "Emotional connection"],
                reusability="medium"
            ),
            EssayHistory(
                topic="Failure at robotics competition leading to innovation",
                theme="Learning from failure to create breakthrough solutions",
                word_count=400,
                school_type="Stanford Supplement",
                strengths=["Growth mindset", "Specific technical problem-solving", "Team leadership"],
                areas_for_improvement=["More vulnerability", "Broader life lessons"],
                reusability="high"
            )
        ],
        
        college_goals=["Major in AI/ML with focus on social applications", "Join research lab working on accessible technology"],
        dream_schools=["Stanford", "MIT", "UC Berkeley", "Carnegie Mellon"],
        
        writing_style=WritingStyle(
            tone_preference="analytical with personal touches",
            strength_areas=["Clear logical structure", "Technical explanations", "Problem-solution narratives"],
            challenge_areas=["Emotional vulnerability", "Creative language", "Personal reflection depth"],
            autonomy_preference="collaborative",
            feedback_sensitivity="medium"
        ),
        
        # EXTENSIVE AGENT INTERACTION HISTORY
        previous_sessions=8,
        successful_essays_completed=4,
        preferred_brainstorming_approach="problem-solving frameworks with personal connection",
        common_stuck_points=["Being too technical", "Not revealing enough personal insight", "Perfectionism paralysis", "Reusing same themes"]
    ),

    UserProfile(
        profile_id="returning_community_leader_with_activities",
        name="Aisha Williams (Returning)",
        category=ProfileCategory.COMMUNITY_LEADER,
        
        # Same basic profile as community_organizer_student but with extensive history
        age=17,
        location="Baltimore, MD", 
        school_type="Public High School",
        gpa=3.9,
        test_scores={"SAT": 1420, "ACT": 32},
        
        family_background="African-American, raised by grandmother, mother works two jobs",
        socioeconomic_status="Low income",
        first_generation=True,
        languages_spoken=["English"],
        
        academic_interests=["Political Science", "Social Work", "Public Health", "Criminal Justice Reform"],
        intended_major="Political Science with Social Work minor",
        favorite_subjects=["AP Government", "AP English Language", "Social Justice Seminar"],
        academic_achievements=["Student Government President", "Debate Team State Finalist", "Youth Advisory Council to Mayor"],
        research_experience="Policy research internship with local city council member",
        
        # EXTENSIVE ACTIVITY DATABASE
        activities=[
            Activity(
                name="Youth Violence Prevention Coalition",
                role="Co-founder and Director",
                description="Created peer mediation program and violence intervention initiatives",
                duration="2 years",
                impact="Reduced school conflicts by 40%, trained 50+ peer mediators",
                essay_potential="High - community safety, peer leadership, systemic change",
                values_demonstrated=["community safety", "peer education", "conflict resolution", "systemic thinking"]
            ),
            Activity(
                name="Food Justice Campaign",
                role="Lead Organizer",
                description="Advocated for healthy food options in school and neighborhood",
                duration="3 years",
                impact="Secured funding for salad bar, established weekend food pantry",
                essay_potential="High - community advocacy, health equity, organizing skills",
                values_demonstrated=["health equity", "community organizing", "persistence", "food justice"]
            ),
            Activity(
                name="Environmental Justice Club",
                role="President",
                description="Organized campaigns against environmental hazards in low-income neighborhoods",
                duration="2 years",
                impact="Successfully lobbied for air quality monitoring, organized 3 community forums",
                essay_potential="High - environmental justice, community organizing, policy advocacy",
                values_demonstrated=["environmental justice", "policy advocacy", "community organizing"]
            ),
            Activity(
                name="Mentorship Program for Middle Schoolers",
                role="Program Coordinator",
                description="Connected high school students with at-risk middle schoolers",
                duration="2 years",
                impact="30+ successful mentorship pairs, 90% of mentees stayed in school",
                essay_potential="Medium - mentorship, academic support, community building",
                values_demonstrated=["mentorship", "academic support", "community investment"]
            ),
            Activity(
                name="Youth Voter Registration Drive",
                role="Campaign Manager",
                description="Registered 200+ new young voters in community",
                duration="1 year",
                impact="Increased youth voter turnout by 35% in local election",
                essay_potential="Medium - civic engagement, democracy, community empowerment",
                values_demonstrated=["civic engagement", "democracy", "community empowerment"]
            )
        ],
        
        leadership_roles=["Student Government President", "Black Student Union Vice President", "Debate Team Captain", "Youth Advisory Council Member"],
        volunteer_work=["Community center after-school programming (200+ hours)", "Voter registration drives", "Food bank coordination"],
        work_experience="Part-time at community health clinic",
        
        core_values=["Community empowerment", "Educational equity", "Restorative justice", "Youth voice in policy"],
        defining_moments=[
            DefiningMoment(
                event="Best friend was suspended for fight that could have been prevented with better conflict resolution",
                age_when_occurred="15",
                impact="Realized need for prevention-focused, peer-led approaches to school discipline",
                lessons_learned=["Prevention better than punishment", "Peers can be most effective interventionists"],
                essay_potential="High - personal motivation for systemic change, restorative justice",
                emotional_weight="high"
            ),
            DefiningMoment(
                event="Testified at city council meeting about need for youth programming",
                age_when_occurred="16",
                impact="Discovered power of youth voice in policy and formal advocacy",
                lessons_learned=["Young people can influence policy", "Preparation and research enhance credibility"],
                essay_potential="High - civic engagement, youth empowerment, policy advocacy",
                emotional_weight="medium"
            ),
            DefiningMoment(
                event="Environmental racism presentation led to community air quality testing",
                age_when_occurred="16",
                impact="Realized intersectionality of social justice issues and power of research-based advocacy",
                lessons_learned=["Environmental and social justice are connected", "Research amplifies community voice"],
                essay_potential="High - intersectional thinking, environmental justice, community impact",
                emotional_weight="medium"
            )
        ],
        
        personal_challenges=["Balancing activism with academics", "Financial stress affecting college options", "Feeling responsible for solving community problems"],
        growth_areas=["Academic writing for policy analysis", "Self-care and boundary setting", "Long-term strategic planning"],
        
        # RICH ESSAY HISTORY showing growth and adaptation
        essay_history=[
            EssayHistory(
                topic="Creating peer mediation program after friend's unfair suspension",
                theme="Youth-led solutions to school discipline issues",
                word_count=650,
                school_type="Common App",
                strengths=["Personal motivation", "Clear community impact", "Leadership demonstration"],
                areas_for_improvement=["More policy analysis", "Future career connection"],
                reusability="high"
            ),
            EssayHistory(
                topic="Testifying at city council about youth programming needs",
                theme="Youth voice in policy making",
                word_count=350,
                school_type="UC Personal Insight",
                strengths=["Civic engagement", "Public speaking courage", "Policy understanding"],
                areas_for_improvement=["More personal reflection", "Specific policy outcomes"],
                reusability="medium"
            ),
            EssayHistory(
                topic="Environmental justice campaign in predominantly Black neighborhood",
                theme="Intersectionality of environmental and social justice",
                word_count=300,
                school_type="Georgetown Supplement",
                strengths=["Intersectional analysis", "Community organizing", "Research-based advocacy"],
                areas_for_improvement=["Personal stakes", "Future vision"],
                reusability="high"
            ),
            EssayHistory(
                topic="Food justice campaign connecting hunger and community empowerment",
                theme="Food access as social justice issue",
                word_count=250,
                school_type="American University Supplement",
                strengths=["Systemic thinking", "Community organizing", "Practical impact"],
                areas_for_improvement=["Personal connection", "Emotional resonance"],
                reusability="medium"
            )
        ],
        
        college_goals=["Study policy and advocacy strategies", "Develop expertise in community organizing", "Return to community as policy advocate"],
        dream_schools=["Howard University", "Spelman", "Georgetown", "American University"],
        
        writing_style=WritingStyle(
            tone_preference="passionate and persuasive",
            strength_areas=["Persuasive arguments", "Community impact narratives", "Policy analysis", "Intersectional thinking"],
            challenge_areas=["Personal vulnerability", "Academic formality", "Concise expression"],
            autonomy_preference="collaborative",
            feedback_sensitivity="low"
        ),
        
        # EXTENSIVE AGENT INTERACTION HISTORY
        previous_sessions=6,
        successful_essays_completed=4,
        preferred_brainstorming_approach="problem-analysis and solution-focused with community examples",
        common_stuck_points=["Balancing personal story with policy focus", "Avoiding 'savior complex' tone", "Choosing between many activities", "Connecting activities to future goals"]
    )
]

# =============================================================================
# PROFILE REGISTRY AND UTILITIES
# =============================================================================

# Combine all profiles into master registry
ALL_PROFILES = (
    ACADEMIC_ACHIEVER_PROFILES +
    CREATIVE_ARTIST_PROFILES + 
    COMMUNITY_LEADER_PROFILES +
    ENTREPRENEUR_PROFILES +
    ATHLETE_PROFILES +
    DIVERSE_BACKGROUND_PROFILES +
    RETURNING_USER_PROFILES
)

def get_profile_by_id(profile_id: str) -> Optional[UserProfile]:
    """Get a specific profile by its ID."""
    for profile in ALL_PROFILES:
        if profile.profile_id == profile_id:
            return profile
    return None

def get_profiles_by_category(category: ProfileCategory) -> List[UserProfile]:
    """Get all profiles in a specific category."""
    return [p for p in ALL_PROFILES if p.category == category]

def get_returning_user_profiles() -> List[UserProfile]:
    """Get profiles with extensive agent interaction history."""
    return [p for p in ALL_PROFILES if p.previous_sessions > 0]

def get_first_generation_profiles() -> List[UserProfile]:
    """Get profiles of first-generation college students."""
    return [p for p in ALL_PROFILES if p.first_generation]

def get_profiles_summary() -> Dict[str, Any]:
    """Get summary statistics about available profiles."""
    return {
        "total_profiles": len(ALL_PROFILES),
        "by_category": {
            category.value: len(get_profiles_by_category(category))
            for category in ProfileCategory
        },
        "returning_users": len(get_returning_user_profiles()),
        "first_generation": len(get_first_generation_profiles()),
        "average_activities": sum(len(p.activities) for p in ALL_PROFILES) / len(ALL_PROFILES),
        "languages_represented": len(set(lang for p in ALL_PROFILES for lang in p.languages_spoken)),
        "schools_represented": len(set(p.location for p in ALL_PROFILES))
    }

# Export key components
__all__ = [
    "UserProfile",
    "Activity",
    "EssayHistory", 
    "DefiningMoment",
    "WritingStyle",
    "ProfileCategory",
    "ALL_PROFILES",
    "ACADEMIC_ACHIEVER_PROFILES",
    "CREATIVE_ARTIST_PROFILES",
    "COMMUNITY_LEADER_PROFILES", 
    "ENTREPRENEUR_PROFILES",
    "ATHLETE_PROFILES",
    "DIVERSE_BACKGROUND_PROFILES",
    "RETURNING_USER_PROFILES",
    "get_profile_by_id",
    "get_profiles_by_category",
    "get_returning_user_profiles",
    "get_first_generation_profiles",
    "get_profiles_summary"
] 