"""Test essay prompts for comprehensive testing

Provides standardized prompts covering different essay types and colleges.
"""

from typing import Dict, List, Any, Optional

ESSAY_PROMPTS = {
    # Stanford prompts
    "stanford_learning": {
        "id": "stanford_learning",
        "college": "Stanford",
        "type": "learning",
        "word_limit": 250,
        "prompt": "The Stanford community is deeply curious and driven to learn in and out of the classroom. Reflect on an idea or experience that makes you genuinely excited about learning.",
        "keywords": ["learning", "curiosity", "excited", "Stanford community", "classroom"],
        "themes": ["intellectual curiosity", "passion for learning", "community"]
    },
    
    "stanford_experience": {
        "id": "stanford_experience", 
        "college": "Stanford",
        "type": "experience",
        "word_limit": 250,
        "prompt": "Tell us about something that is meaningful to you and why.",
        "keywords": ["meaningful", "important", "significance", "value", "personal"],
        "themes": ["personal values", "meaning", "significance"]
    },

    # MIT prompts
    "mit_community": {
        "id": "mit_community",
        "college": "MIT",
        "type": "community",
        "word_limit": 300,
        "prompt": "MIT students work to improve their communities in different ways, from tackling the world's biggest challenges to being a good friend to someone in need. Describe one way you have contributed to your community, whether in your family, the classroom, your neighborhood, etc.",
        "keywords": ["community", "contributed", "improve", "challenges", "help"],
        "themes": ["service", "community impact", "contribution"]
    },

    "mit_challenge": {
        "id": "mit_challenge",
        "college": "MIT", 
        "type": "challenge",
        "word_limit": 300,
        "prompt": "Describe a time when you overcame a significant challenge. Focus on what you learned from this experience.",
        "keywords": ["challenge", "overcome", "learned", "experience", "growth"],
        "themes": ["resilience", "growth", "learning from adversity"]
    },

    # Harvard prompts
    "harvard_identity": {
        "id": "harvard_identity",
        "college": "Harvard",
        "type": "identity",
        "word_limit": 650,
        "prompt": "Harvard has long recognized the importance of student body diversity of all kinds. We welcome you to write about distinctive aspects of your background, personal development, or the perspective you bring.",
        "keywords": ["diversity", "background", "perspective", "development", "distinctive"],
        "themes": ["identity", "diversity", "perspective", "personal growth"]
    },

    "harvard_intellectual": {
        "id": "harvard_intellectual",
        "college": "Harvard",
        "type": "intellectual",
        "word_limit": 650,
        "prompt": "Describe an intellectual experience (course, project, book, discussion, paper, poetry, or research topic in engineering, mathematics, science or other modes of inquiry) that has meant the most to you.",
        "keywords": ["intellectual", "course", "project", "research", "inquiry"],
        "themes": ["intellectual curiosity", "academic passion", "learning"]
    },

    # Yale prompts  
    "yale_passion": {
        "id": "yale_passion",
        "college": "Yale",
        "type": "passion",
        "word_limit": 400,
        "prompt": "What is something about you that is not on the rest of your application?",
        "keywords": ["something about you", "not on application", "unique", "personal"],
        "themes": ["uniqueness", "hidden talents", "personal interests"]
    },

    "yale_community": {
        "id": "yale_community",
        "college": "Yale", 
        "type": "community",
        "word_limit": 400,
        "prompt": "Yale's extensive course offerings and vibrant conversations beyond the classroom encourage students to follow their developing intellectual interests wherever they lead. Tell us about your engagement with a topic or idea that excites you. Why are you drawn to it?",
        "keywords": ["intellectual interests", "topic", "idea", "excites", "drawn"],
        "themes": ["intellectual passion", "curiosity", "engagement"]
    },

    # UC Berkeley prompts
    "ucb_achievement": {
        "id": "ucb_achievement",
        "college": "UC Berkeley",
        "type": "achievement", 
        "word_limit": 350,
        "prompt": "Describe an example of your leadership experience in which you have positively influenced others, helped resolve disputes or contributed to group efforts over time.",
        "keywords": ["leadership", "influenced", "resolve disputes", "group efforts"],
        "themes": ["leadership", "teamwork", "conflict resolution"]
    },

    "ucb_creative": {
        "id": "ucb_creative",
        "college": "UC Berkeley",
        "type": "creative",
        "word_limit": 350, 
        "prompt": "Every person has a creative side, and it can be expressed in many ways: problem solving, original and innovative thinking, and artistically, to name a few. Describe how you express your creative side.",
        "keywords": ["creative", "express", "problem solving", "innovative", "artistic"],
        "themes": ["creativity", "innovation", "self-expression"]
    },

    # Common App prompts
    "common_background": {
        "id": "common_background",
        "college": "Common App",
        "type": "identity",
        "word_limit": 650,
        "prompt": "Some students have a background, identity, interest, or talent that is so meaningful their application would be incomplete without it. If this sounds like you, then please share your story.",
        "keywords": ["background", "identity", "interest", "talent", "meaningful", "story"],
        "themes": ["identity", "personal story", "uniqueness"]
    },

    "common_challenge": {
        "id": "common_challenge", 
        "college": "Common App",
        "type": "challenge",
        "word_limit": 650,
        "prompt": "The lessons we take from obstacles we encounter can be fundamental to later success. Recount a time when you faced a challenge, setback, or failure. How did it affect you, and what did you learn from the experience?",
        "keywords": ["obstacles", "challenge", "setback", "failure", "learn", "success"],
        "themes": ["resilience", "growth mindset", "learning from failure"]
    },

    "common_accomplishment": {
        "id": "common_accomplishment",
        "college": "Common App", 
        "type": "achievement",
        "word_limit": 650,
        "prompt": "Reflect on a time when you questioned or challenged a belief or idea. What prompted your thinking? What was the outcome?",
        "keywords": ["questioned", "challenged", "belief", "idea", "thinking", "outcome"],
        "themes": ["critical thinking", "intellectual courage", "growth"]
    },

    # Test-specific prompts for edge cases
    "test_short": {
        "id": "test_short",
        "college": "Test College",
        "type": "test",
        "word_limit": 100,
        "prompt": "In 100 words, tell us about yourself.",
        "keywords": ["yourself", "personal"],
        "themes": ["identity", "conciseness"]
    },

    "test_long": {
        "id": "test_long", 
        "college": "Test College",
        "type": "test",
        "word_limit": 1000,
        "prompt": "Write a comprehensive essay about your goals, experiences, and aspirations. You have 1000 words to paint a complete picture of who you are.",
        "keywords": ["goals", "experiences", "aspirations", "complete picture"],
        "themes": ["comprehensive", "life story", "future goals"]
    }
}

def get_prompt_by_type(essay_type: str) -> Optional[Dict[str, Any]]:
    """Get the first prompt matching the given type"""
    for prompt_id, prompt in ESSAY_PROMPTS.items():
        if prompt["type"] == essay_type:
            return prompt
    return None

def get_prompt_by_college(college: str) -> List[Dict[str, Any]]:
    """Get all prompts for a specific college"""
    return [prompt for prompt in ESSAY_PROMPTS.values() if prompt["college"] == college]

def get_prompt_by_id(prompt_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific prompt by ID"""
    return ESSAY_PROMPTS.get(prompt_id)

def get_prompts_by_word_limit(min_words: int = 0, max_words: int = 1000) -> List[Dict[str, Any]]:
    """Get prompts within a word limit range"""
    return [
        prompt for prompt in ESSAY_PROMPTS.values() 
        if min_words <= prompt["word_limit"] <= max_words
    ]

def get_all_prompt_types() -> List[str]:
    """Get all unique prompt types"""
    return list(set(prompt["type"] for prompt in ESSAY_PROMPTS.values()))

def get_all_colleges() -> List[str]:
    """Get all unique colleges"""
    return list(set(prompt["college"] for prompt in ESSAY_PROMPTS.values()))

# Prompt sets for different testing scenarios
PROMPT_SETS = {
    "happy_path": [
        "stanford_learning",
        "mit_community", 
        "harvard_identity",
        "yale_passion",
        "common_challenge"
    ],
    
    "edge_cases": [
        "test_short",
        "test_long"
    ],
    
    "word_count_variety": [
        "test_short",      # 100 words
        "stanford_learning", # 250 words  
        "mit_community",   # 300 words
        "yale_passion",    # 400 words
        "common_challenge" # 650 words
    ],

    "essay_types": [
        "stanford_learning",   # learning
        "mit_challenge",       # challenge  
        "harvard_identity",    # identity
        "yale_passion",        # passion
        "mit_community",       # community
        "ucb_achievement",     # achievement
        "ucb_creative"         # creative
    ]
} 