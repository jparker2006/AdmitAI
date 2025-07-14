"""essay_agent.eval.sample_prompts

Collection of diverse essay prompts for evaluation harness testing.
Covers different Common App archetypes with varying word limits (250-800 words).
"""

from essay_agent.models import EssayPrompt
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile, CoreValue, DefiningMoment, Activity

# Sample prompts covering different essay archetypes
SAMPLE_PROMPTS = {
    "challenge": EssayPrompt(
        text="Describe a problem you've solved or would like to solve. It can be an intellectual challenge, a research query, an ethical dilemma—anything that is of personal importance, no matter the scale. Explain its significance to you and what steps you took or could be taken to identify a solution.",
        word_limit=650,
        college="Stanford University",
        additional_instructions="Focus on your problem-solving process and personal growth."
    ),
    
    "identity": EssayPrompt(
        text="Some students have a background, identity, interest, or talent that is so meaningful they believe their application would be incomplete without it. If this sounds like you, then please share your story.",
        word_limit=800,
        college="Harvard University", 
        additional_instructions="Show how this aspect of your identity shapes your perspective and goals."
    ),
    
    "passion": EssayPrompt(
        text="Describe a topic, idea, or concept you find so engaging that it makes you lose all track of time. Why does it captivate you? What or who do you turn to when you want to learn more?",
        word_limit=500,
        college="MIT",
        additional_instructions="Demonstrate intellectual curiosity and depth of engagement."
    ),
    
    "achievement": EssayPrompt(
        text="Describe an accomplishment, event, or realization that sparked a period of personal growth and a new understanding of yourself or others.",
        word_limit=400,
        college="Yale University",
        additional_instructions="Focus on the transformation and self-reflection."
    ),
    
    "community": EssayPrompt(
        text="Discuss an accomplishment, event, or realization that made you feel proud and relates to your cultural background, community, or family traditions.",
        word_limit=250,
        college="UC Berkeley",
        additional_instructions="Connect personal experience to broader community impact."
    )
}

# Sample user profile for testing
def create_test_profile() -> UserProfile:
    """Create a realistic test user profile for evaluation - balanced technology focus."""
    return UserProfile(
        user_info=UserInfo(
            name="Alex Johnson",
            grade=12,
            intended_major="Computer Science",
            college_list=["Stanford", "MIT", "Harvard", "Yale", "UC Berkeley"],
            platforms=["Common App", "Coalition"]
        ),
        academic_profile=AcademicProfile(
            gpa=3.8,
            test_scores={"SAT": 1450, "ACT": None},
            courses=["AP Computer Science", "AP Calculus BC", "AP Literature"],
            activities=[
                Activity(
                    name="Robotics Club",
                    role="Lead Programmer",
                    duration="2 years",
                    description="Designed autonomous navigation systems for competitive robots",
                    impact="Led team to regional championship, mentored 8 younger students"
                ),
                Activity(
                    name="Volunteer Tutoring",
                    role="Math Tutor",
                    duration="3 years", 
                    description="Tutored underprivileged students in algebra and geometry",
                    impact="Improved student grades by average of 1.2 letter grades"
                ),
                Activity(
                    name="Cultural Heritage Club",
                    role="Vice President",
                    duration="2 years",
                    description="Organized cultural awareness events and language preservation workshops",
                    impact="Increased school cultural diversity awareness by 40%, preserved family traditions"
                ),
                Activity(
                    name="Environmental Club",
                    role="Project Leader",
                    duration="2 years",
                    description="Led campus sustainability initiatives and community clean-up events",
                    impact="Reduced school waste by 25%, organized 15 community events"
                ),
                Activity(
                    name="Peer Mentorship Program",
                    role="Mentor",
                    duration="1 year",
                    description="Guided freshman students through academic and social challenges",
                    impact="Supported 12 students with 95% retention rate"
                )
            ]
        ),
        core_values=[
            CoreValue(
                value="Innovation",
                description="Belief in using technology to solve real-world problems",
                evidence=["Created app for local food bank", "Robotics innovations"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Service",
                description="Commitment to helping others succeed",
                evidence=["Tutoring program", "Mentoring younger students"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Cultural Pride",
                description="Deep appreciation for heritage and traditions",
                evidence=["Led cultural heritage club", "Organized cultural awareness events"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Environmental Stewardship",
                description="Responsibility to protect and preserve our planet",
                evidence=["Campus sustainability initiatives", "Community clean-up events"],
                used_in_essays=[]
            )
        ],
        defining_moments=[
            DefiningMoment(
                title="First Programming Success",
                description="Creating my first working program that solved a real problem for our school's attendance system",
                emotional_impact="Overwhelming sense of accomplishment and realization that code could create meaningful change",
                lessons_learned="Technology can be a powerful tool for positive impact when applied thoughtfully",
                used_in_essays=[],
                themes=["problem-solving", "innovation", "purpose", "technology"],
                story_category="passion",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Supporting Struggling Family Member",
                description="Helping my younger sibling through a difficult learning disability diagnosis and finding new ways to support their education",
                emotional_impact="Deep sense of responsibility and protective love that reshaped my priorities",
                lessons_learned="Everyone learns differently; patience, creativity, and unconditional support can unlock potential",
                used_in_essays=[],
                themes=["family", "empathy", "perseverance", "education"],
                story_category="identity",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Cultural Identity Crisis",
                description="Struggling with feeling disconnected from my heritage and then rediscovering it through community involvement",
                emotional_impact="Initial shame and confusion transformed into deep pride and sense of belonging",
                lessons_learned="Understanding your roots strengthens your sense of self and connection to others",
                used_in_essays=[],
                themes=["identity", "culture", "belonging", "growth"],
                story_category="identity",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Failed Leadership Attempt",
                description="Trying to lead a school environmental project that completely fell apart due to my poor planning and communication",
                emotional_impact="Humiliation and disappointment that forced me to confront my limitations",
                lessons_learned="True leadership requires listening, planning, and building consensus, not just having good ideas",
                used_in_essays=[],
                themes=["failure", "leadership", "humility", "growth"],
                story_category="challenge",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Tutoring Breakthrough Moment",
                description="Helping a student who had been failing math finally understand a concept after weeks of different approaches",
                emotional_impact="Joy and validation that teaching and patience can truly transform someone's life",
                lessons_learned="Everyone has potential; the key is finding the right approach and never giving up",
                used_in_essays=[],
                themes=["teaching", "persistence", "empathy", "achievement"],
                story_category="achievement",
                story_weight=1.0
            )
        ]
    )


def create_test_profile_arts() -> UserProfile:
    """Create an arts-focused test user profile for evaluation."""
    return UserProfile(
        user_info=UserInfo(
            name="Maya Chen",
            grade=12,
            intended_major="Theatre Arts",
            college_list=["Yale", "Northwestern", "NYU", "UCLA", "Brown"],
            platforms=["Common App", "Coalition"]
        ),
        academic_profile=AcademicProfile(
            gpa=3.9,
            test_scores={"SAT": 1380, "ACT": 31},
            courses=["AP Literature", "AP Art History", "AP Psychology"],
            activities=[
                Activity(
                    name="Theatre Company",
                    role="Lead Actress",
                    duration="4 years",
                    description="Performed in 12 productions, including leading roles in Shakespeare and contemporary plays",
                    impact="Received state-level acting award, inspired 20+ students to join theatre"
                ),
                Activity(
                    name="Creative Writing Club",
                    role="President",
                    duration="3 years",
                    description="Led workshop sessions and edited school literary magazine",
                    impact="Published 3 personal essays, increased club membership by 150%"
                ),
                Activity(
                    name="Art Therapy Volunteer",
                    role="Assistant",
                    duration="2 years",
                    description="Helped facilitate art therapy sessions for children with trauma",
                    impact="Supported 25+ children, developed therapeutic art curriculum"
                ),
                Activity(
                    name="Community Mural Project",
                    role="Co-Lead",
                    duration="1 year",
                    description="Organized and painted large-scale mural celebrating cultural diversity",
                    impact="Engaged 50+ community members, now permanent city landmark"
                ),
                Activity(
                    name="Poetry Open Mic",
                    role="Founder",
                    duration="2 years",
                    description="Created monthly poetry event for students and community members",
                    impact="Hosted 20+ events, provided platform for 100+ emerging poets"
                )
            ]
        ),
        core_values=[
            CoreValue(
                value="Creative Expression",
                description="Belief in the transformative power of art and storytelling",
                evidence=["Theatre performances", "Published writing", "Community art projects"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Empathy",
                description="Deep understanding and connection to others' experiences",
                evidence=["Art therapy work", "Diverse character portrayals", "Community engagement"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Cultural Celebration",
                description="Appreciation for diverse perspectives and traditions",
                evidence=["Community mural project", "Multicultural theatre selections"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Healing",
                description="Using art to help others process emotions and experiences",
                evidence=["Art therapy volunteer work", "Poetry open mic community"],
                used_in_essays=[]
            )
        ],
        defining_moments=[
            DefiningMoment(
                title="First Stage Performance",
                description="Overcoming severe stage fright to perform in my first school play, discovering my voice and confidence",
                emotional_impact="Terrifying vulnerability transformed into exhilarating empowerment and sense of purpose",
                lessons_learned="Growth happens outside comfort zones; authentic expression connects people across differences",
                used_in_essays=[],
                themes=["courage", "self-discovery", "performance", "growth"],
                story_category="passion",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Grandmother's Stories",
                description="Spending summers listening to my grandmother's immigration stories and learning about our family's artistic traditions",
                emotional_impact="Deep connection to my heritage and understanding of resilience across generations",
                lessons_learned="Family stories shape identity; preserving culture through art honors those who came before",
                used_in_essays=[],
                themes=["heritage", "storytelling", "family", "tradition"],
                story_category="identity",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Art Therapy Breakthrough",
                description="Witnessing a young trauma survivor express their feelings through painting for the first time",
                emotional_impact="Profound realization of art's healing power and my calling to help others through creativity",
                lessons_learned="Art can reach places words cannot; everyone deserves a voice and safe space for expression",
                used_in_essays=[],
                themes=["healing", "service", "empathy", "purpose"],
                story_category="achievement",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Failed Play Production",
                description="Directing a student production that was poorly received due to my inexperience and over-ambition",
                emotional_impact="Crushing disappointment and self-doubt about my abilities and judgment",
                lessons_learned="Failure is a teacher; collaboration and humility are essential for artistic leadership",
                used_in_essays=[],
                themes=["failure", "leadership", "learning", "humility"],
                story_category="challenge",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Community Mural Completion",
                description="Seeing our neighborhood mural unveiled and watching community members find their own stories represented",
                emotional_impact="Overwhelming joy and pride in creating something lasting that brings people together",
                lessons_learned="Art can bridge divides and create shared spaces for celebration and healing",
                used_in_essays=[],
                themes=["community", "collaboration", "legacy", "unity"],
                story_category="community",
                story_weight=1.0
            )
        ]
    )


def create_test_profile_community() -> UserProfile:
    """Create a community service and athletics-focused test user profile for evaluation."""
    return UserProfile(
        user_info=UserInfo(
            name="Jordan Williams",
            grade=12,
            intended_major="Public Policy",
            college_list=["Georgetown", "Duke", "Vanderbilt", "UNC", "Emory"],
            platforms=["Common App", "Coalition"]
        ),
        academic_profile=AcademicProfile(
            gpa=3.7,
            test_scores={"SAT": 1420, "ACT": 33},
            courses=["AP Government", "AP Statistics", "AP History"],
            activities=[
                Activity(
                    name="Varsity Basketball",
                    role="Team Captain",
                    duration="4 years",
                    description="Led team to conference championship, maintained 3.7 GPA while playing 25+ hours weekly",
                    impact="Team won first championship in 10 years, received sportsmanship award"
                ),
                Activity(
                    name="Homeless Shelter Volunteer",
                    role="Coordinator",
                    duration="3 years",
                    description="Organized meal service and recreational activities for shelter residents",
                    impact="Coordinated 150+ volunteers, served 5,000+ meals annually"
                ),
                Activity(
                    name="Student Government",
                    role="President",
                    duration="2 years",
                    description="Led school policy initiatives and represented student interests to administration",
                    impact="Implemented mental health resources, increased student satisfaction by 30%"
                ),
                Activity(
                    name="Youth Basketball League",
                    role="Coach",
                    duration="3 years",
                    description="Coached elementary school basketball team in underserved community",
                    impact="Developed 40+ young athletes, 100% high school graduation rate"
                ),
                Activity(
                    name="Community Health Fair",
                    role="Organizer",
                    duration="2 years",
                    description="Coordinated annual health screenings and education for underserved populations",
                    impact="Reached 500+ community members, connected 100+ to healthcare resources"
                )
            ]
        ),
        core_values=[
            CoreValue(
                value="Service",
                description="Commitment to lifting up others and strengthening communities",
                evidence=["Homeless shelter work", "Youth coaching", "Community health initiatives"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Leadership",
                description="Inspiring others to work toward shared goals and positive change",
                evidence=["Team captain", "Student government president", "Volunteer coordination"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Perseverance",
                description="Pushing through challenges and maintaining commitment to goals",
                evidence=["Athletic achievements", "Academic balance", "Long-term community projects"],
                used_in_essays=[]
            ),
            CoreValue(
                value="Equity",
                description="Belief that everyone deserves access to opportunities and resources",
                evidence=["Youth coaching in underserved area", "Community health advocacy"],
                used_in_essays=[]
            )
        ],
        defining_moments=[
            DefiningMoment(
                title="Championship Game Victory",
                description="Leading my team to our first conference championship through a season of adversity and doubt",
                emotional_impact="Overwhelming pride and validation after years of hard work and team building",
                lessons_learned="Success requires both individual excellence and collective commitment; leadership means serving others",
                used_in_essays=[],
                themes=["achievement", "teamwork", "leadership", "perseverance"],
                story_category="achievement",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Father's Injury and Recovery",
                description="Watching my father struggle with unemployment after a work injury and our family's financial hardship",
                emotional_impact="Fear and uncertainty that matured me quickly and deepened my empathy for struggling families",
                lessons_learned="Economic insecurity affects entire families; community support systems are essential for resilience",
                used_in_essays=[],
                themes=["family", "hardship", "resilience", "empathy"],
                story_category="identity",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Homeless Shelter Regular",
                description="Building a relationship with a shelter resident who became like a grandfather to me",
                emotional_impact="Deep connection that challenged my assumptions about homelessness and human dignity",
                lessons_learned="Everyone has a story and inherent worth; privilege comes with responsibility to serve others",
                used_in_essays=[],
                themes=["service", "dignity", "connection", "privilege"],
                story_category="community",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Election Campaign Failure",
                description="Losing my first student government election due to overconfidence and poor campaigning",
                emotional_impact="Humbling defeat that forced me to examine my approach and motivations",
                lessons_learned="True leadership requires listening to others and earning trust, not just having good ideas",
                used_in_essays=[],
                themes=["failure", "humility", "leadership", "growth"],
                story_category="challenge",
                story_weight=1.0
            ),
            DefiningMoment(
                title="Young Player's Breakthrough",
                description="Helping a shy 8-year-old player find confidence and joy in basketball through patient encouragement",
                emotional_impact="Pure joy watching someone discover their potential and love for the game",
                lessons_learned="Coaching is about developing the whole person; small encouragements can transform lives",
                used_in_essays=[],
                themes=["mentorship", "growth", "patience", "impact"],
                story_category="passion",
                story_weight=1.0
            )
        ]
    )

# Keywords for similarity scoring
PROMPT_KEYWORDS = {
    "challenge": ["problem", "solve", "challenge", "solution", "steps", "significance", "difficulty", "overcome"],
    "identity": ["background", "identity", "meaningful", "story", "shapes", "perspective", "who you are"],
    "passion": ["engaging", "captivate", "lose track", "time", "learn", "curiosity", "interest"],
    "achievement": ["accomplishment", "growth", "realization", "understanding", "transformation", "change"],
    "community": ["community", "cultural", "family", "traditions", "proud", "background", "impact"]
}

def get_all_prompts():
    """Return all sample prompts as a list."""
    return list(SAMPLE_PROMPTS.values())

def get_prompt_by_id(prompt_id: str) -> EssayPrompt:
    """Get a specific prompt by ID."""
    if prompt_id not in SAMPLE_PROMPTS:
        raise ValueError(f"Unknown prompt ID: {prompt_id}")
    return SAMPLE_PROMPTS[prompt_id]

def get_prompt_keywords(prompt_id: str) -> list[str]:
    """Get expected keywords for a prompt."""
    return PROMPT_KEYWORDS.get(prompt_id, []) 