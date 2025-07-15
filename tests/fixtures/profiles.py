"""Test user profiles for consistent testing

Provides standardized user profiles covering different student types and backgrounds.
"""

from datetime import datetime
from typing import Dict, List, Any

# Base profile template
def create_test_profile(
    name: str,
    grade: int,
    major: str,
    colleges: List[str],
    gpa: float,
    test_scores: Dict[str, int],
    activities: List[Dict[str, Any]],
    values: List[Dict[str, Any]],
    moments: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create a standardized test profile"""
    return {
        "user_info": {
            "name": name,
            "grade": grade,
            "intended_major": major,
            "college_list": colleges,
            "platforms": ["Common App", "Coalition"]
        },
        "academic_profile": {
            "gpa": gpa,
            "test_scores": test_scores,
            "courses": [
                f"AP {major}",
                "AP Literature",
                "AP History",
                "AP Math"
            ],
            "activities": activities
        },
        "core_values": values,
        "defining_moments": moments,
        "writing_voice": None,
        "essay_history": [],
        "college_story_usage": {}
    }

# Test profile variations
TEST_PROFILES = {
    "achiever_stem": create_test_profile(
        name="Alex Chen",
        grade=12,
        major="Computer Science",
        colleges=["MIT", "Stanford", "UC Berkeley", "Caltech"],
        gpa=3.95,
        test_scores={"SAT": 1580, "ACT": None},
        activities=[
            {
                "name": "Robotics Team Captain",
                "role": "Team Captain",
                "duration": "3 years",
                "description": "Led 15-person robotics team to state championships",
                "impact": "Won regional championship, mentored 8 underclassmen"
            },
            {
                "name": "Math Tutoring",
                "role": "Volunteer Tutor",
                "duration": "2 years", 
                "description": "Tutored underperforming students in calculus",
                "impact": "Helped 20+ students improve grades by 1+ letter grade"
            }
        ],
        values=[
            {
                "value": "Innovation",
                "description": "Using technology to solve real-world problems",
                "evidence": ["Robotics projects", "Programming competitions"],
                "used_in_essays": []
            },
            {
                "value": "Teaching",
                "description": "Sharing knowledge to empower others",
                "evidence": ["Math tutoring", "Mentoring teammates"],
                "used_in_essays": []
            }
        ],
        moments=[
            {
                "title": "First Robot Competition Victory",
                "description": "Leading team to unexpected victory after months of setbacks",
                "emotional_impact": "Profound sense of accomplishment and team unity",
                "lessons_learned": "Persistence and collaboration can overcome any obstacle",
                "used_in_essays": [],
                "themes": ["leadership", "perseverance", "innovation"],
                "story_category": "accomplishment",
                "story_weight": 1.0,
                "college_usage": {}
            }
        ]
    ),
    
    "challenger_humanities": create_test_profile(
        name="Maya Rodriguez",
        grade=12,
        major="International Relations",
        colleges=["Harvard", "Yale", "Georgetown", "Princeton"],
        gpa=3.85,
        test_scores={"SAT": 1520, "ACT": 34},
        activities=[
            {
                "name": "Model UN Secretary-General",
                "role": "Secretary-General",
                "duration": "2 years",
                "description": "Organized international conferences with 200+ delegates",
                "impact": "Increased participation by 40%, established scholarship fund"
            },
            {
                "name": "Immigration Legal Aid",
                "role": "Volunteer Translator",
                "duration": "3 years",
                "description": "Provided Spanish translation for legal consultations",
                "impact": "Assisted 50+ families with asylum and citizenship applications"
            }
        ],
        values=[
            {
                "value": "Justice",
                "description": "Fighting for equality and human rights",
                "evidence": ["Legal aid work", "Model UN advocacy"],
                "used_in_essays": []
            },
            {
                "value": "Cultural Bridge-Building",
                "description": "Connecting communities across cultural divides", 
                "evidence": ["Translation work", "International conferences"],
                "used_in_essays": []
            }
        ],
        moments=[
            {
                "title": "Family Immigration Struggle",
                "description": "Helping parents navigate complex immigration system",
                "emotional_impact": "Deep understanding of systemic barriers and injustice",
                "lessons_learned": "Personal experience drives authentic advocacy",
                "used_in_essays": [],
                "themes": ["challenge", "family", "justice", "identity"],
                "story_category": "challenge",
                "story_weight": 1.0,
                "college_usage": {}
            }
        ]
    ),

    "creative_passionate": create_test_profile(
        name="Jordan Kim",
        grade=12, 
        major="Fine Arts",
        colleges=["RISD", "Parsons", "Yale", "NYU"],
        gpa=3.70,
        test_scores={"SAT": 1450, "ACT": None},
        activities=[
            {
                "name": "Art Gallery Curator",
                "role": "Student Curator",
                "duration": "2 years",
                "description": "Curated 6 exhibitions featuring local emerging artists",
                "impact": "Showcased 30+ artists, raised $5000 for art scholarships"
            },
            {
                "name": "Community Mural Project",
                "role": "Lead Artist",
                "duration": "1 year",
                "description": "Designed and painted mural reflecting neighborhood history",
                "impact": "Brought together 100+ community members in collaborative art"
            }
        ],
        values=[
            {
                "value": "Creative Expression",
                "description": "Art as a universal language for connection",
                "evidence": ["Gallery work", "Mural project"],
                "used_in_essays": []
            },
            {
                "value": "Community Building",
                "description": "Using art to strengthen community bonds",
                "evidence": ["Mural project", "Gallery exhibitions"],
                "used_in_essays": []
            }
        ],
        moments=[
            {
                "title": "Community Mural Unveiling",
                "description": "Seeing neighbors of all ages celebrate art together", 
                "emotional_impact": "Art's power to unite across differences",
                "lessons_learned": "Creativity can heal and build community",
                "used_in_essays": [],
                "themes": ["passion", "art", "community", "creativity"],
                "story_category": "passion",
                "story_weight": 1.0,
                "college_usage": {}
            }
        ]
    ),

    "service_leader": create_test_profile(
        name="Sam Johnson",
        grade=12,
        major="Social Work", 
        colleges=["Columbia", "UCLA", "University of Michigan", "Northwestern"],
        gpa=3.80,
        test_scores={"SAT": 1480, "ACT": None},
        activities=[
            {
                "name": "Homeless Shelter Coordinator",
                "role": "Volunteer Coordinator",
                "duration": "3 years",
                "description": "Organized meal service and life skills workshops",
                "impact": "Served 1000+ meals, helped 15 people find stable housing"
            },
            {
                "name": "Peer Counseling Program",
                "role": "Peer Counselor",
                "duration": "2 years",
                "description": "Provided emotional support to struggling classmates",
                "impact": "Supported 25+ students through academic and personal challenges"
            }
        ],
        values=[
            {
                "value": "Service",
                "description": "Dedicating life to helping others in need",
                "evidence": ["Shelter work", "Peer counseling"],
                "used_in_essays": []
            },
            {
                "value": "Empathy", 
                "description": "Understanding and sharing others' experiences",
                "evidence": ["Counseling work", "Homeless outreach"],
                "used_in_essays": []
            }
        ],
        moments=[
            {
                "title": "Helping Someone Find Housing",
                "description": "Supporting a homeless individual through housing application",
                "emotional_impact": "Witnessing transformation from despair to hope",
                "lessons_learned": "Small actions can create profound change",
                "used_in_essays": [],
                "themes": ["service", "community", "empathy", "impact"],
                "story_category": "service", 
                "story_weight": 1.0,
                "college_usage": {}
            }
        ]
    ),

    "identity_explorer": create_test_profile(
        name="Riley Patel",
        grade=12,
        major="Psychology",
        colleges=["Brown", "Wesleyan", "Oberlin", "Swarthmore"],
        gpa=3.75,
        test_scores={"SAT": 1510, "ACT": None},
        activities=[
            {
                "name": "Cultural Heritage Club",
                "role": "Co-Founder & President",
                "duration": "2 years",
                "description": "Created space for multicultural students to share traditions",
                "impact": "Grew from 5 to 40 members, hosted 8 cultural celebrations"
            },
            {
                "name": "Mental Health Awareness",
                "role": "Advocate & Speaker",
                "duration": "1 year",
                "description": "Spoke at assemblies about anxiety and depression",
                "impact": "Reduced stigma, increased counseling center usage by 30%"
            }
        ],
        values=[
            {
                "value": "Authenticity",
                "description": "Being true to all aspects of identity",
                "evidence": ["Cultural club", "Mental health advocacy"],
                "used_in_essays": []
            },
            {
                "value": "Acceptance",
                "description": "Creating space for all identities to thrive",
                "evidence": ["Cultural celebrations", "Mental health talks"],
                "used_in_essays": []
            }
        ],
        moments=[
            {
                "title": "Coming Out Speech at Assembly",
                "description": "Sharing personal mental health story with entire school",
                "emotional_impact": "Vulnerability leading to authentic connection",
                "lessons_learned": "Sharing struggles can empower others",
                "used_in_essays": [],
                "themes": ["identity", "vulnerability", "authenticity", "courage"],
                "story_category": "identity",
                "story_weight": 1.0,
                "college_usage": {}
            }
        ]
    )
}

def get_profile_by_type(profile_type: str) -> Dict[str, Any]:
    """Get a test profile by type"""
    return TEST_PROFILES.get(profile_type, TEST_PROFILES["achiever_stem"])

def get_all_profile_types() -> List[str]:
    """Get all available profile types"""
    return list(TEST_PROFILES.keys()) 