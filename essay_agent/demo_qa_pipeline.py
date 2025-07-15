#!/usr/bin/env python3
"""
Demo script for the QA validation pipeline.

This script demonstrates the comprehensive QA validation pipeline with different essay types
and shows how the system identifies issues and provides actionable recommendations.
"""

import asyncio
import time
from typing import Dict, List, Any

from essay_agent.workflows.qa_pipeline import QAValidationPipeline
from essay_agent.tools.validation_tools import (
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    ComprehensiveValidationResult,
    PlagiarismValidator,
    ClicheDetectionValidator,
    OutlineAlignmentValidator,
    FinalPolishValidator,
)


def run_qa_validation(essay: str, context: dict) -> ComprehensiveValidationResult:
    """Run QA validation on essay."""
    pipeline = QAValidationPipeline()
    return pipeline.run_validation(essay, context)


def display_validation_results(result: ComprehensiveValidationResult) -> None:
    """Display validation results in a formatted way."""
    print(f"🎯 Overall Status: {result.overall_status.upper()}")
    print(f"📊 Overall Score: {result.overall_score:.2f}")
    print(f"⏱️ Execution Time: {result.execution_time:.2f}s")
    print(f"🔍 Validators Run: {result.validators_run}")
    
    # Show stage results
    print("\n📋 Stage Results:")
    for i, (validator_name, stage_result) in enumerate(result.validator_results.items(), 1):
        status_icon = "✅" if stage_result.passed else "❌"
        print(f"  {i}. {status_icon} {validator_name}: {stage_result.score:.2f}")
        
        if stage_result.issues:
            print(f"     Issues found: {len(stage_result.issues)}")
            for issue in stage_result.issues[:3]:  # Show first 3 issues
                severity_icon = {
                    ValidationSeverity.LOW: "🟡",
                    ValidationSeverity.MEDIUM: "🟠",
                    ValidationSeverity.HIGH: "🔴",
                    ValidationSeverity.CRITICAL: "🚫"
                }.get(issue.severity, "🟠")
                print(f"       {severity_icon} {issue.message}")
                if issue.suggestion:
                    print(f"         Suggestion: {issue.suggestion}")
    
    # Show recommendations
    if result.recommendations:
        print(f"\n💡 Recommendations ({len(result.recommendations)}):")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
    
    print("=" * 60)


async def demo_qa_pipeline():
    """Demonstrate QA validation pipeline with different essay types."""
    
    print("🔍 Essay Agent QA Validation Pipeline Demo")
    print("=" * 60)
    
    # Test essays with different quality levels
    test_essays = [
        {
            "name": "EXCELLENT",
            "description": "High-quality, original essay with good structure and personal voice",
            "text": """
            Growing up in a small town, I never expected to find my passion in the most unlikely place: the local library's forgotten archives. What started as a mandatory community service project transformed into a deep appreciation for historical preservation and the stories of ordinary people who shaped our community.

            My journey began when Mrs. Chen, the head librarian, assigned me to help digitize old documents in the basement. Initially, I viewed this as tedious work, but as I carefully scanned faded photographs and crumbling newspapers from the 1920s, I discovered fascinating stories about my town's founding families, their struggles during the Great Depression, and their resilience in building the community I know today.

            One particular document captured my attention: a handwritten letter from a young woman named Sarah who had moved to our town in 1925 to teach at the one-room schoolhouse. Her vivid descriptions of daily life, the challenges of rural education, and her determination to provide quality learning opportunities for farm children resonated deeply with me. Through her words, I realized that every generation faces unique challenges but shares the common thread of hoping for a better future.

            This experience taught me that history isn't just about famous figures or major events—it's about understanding how ordinary people's decisions and actions ripple through time to create the world we inherit. I spent months researching Sarah's life, tracking down her descendants, and eventually helped organize a small exhibition about early education in our county.

            The project connected me with community members I'd never met, taught me valuable research skills, and showed me how preserving local history can strengthen community bonds. It also sparked my interest in pursuing studies in public history and community development, as I realized how powerful storytelling can be in bringing people together and honoring those who came before us.

            This experience in the archives didn't just fulfill my community service requirement—it opened my eyes to the importance of preserving and sharing the stories that shape our identities and communities.
            """,
            "context": {
                "essay_prompt": "Describe a meaningful experience and its impact on you",
                "word_limit": 650,
                "user_profile": {"grade": "12", "interests": ["history", "community service"]}
            }
        },
        {
            "name": "PROBLEMATIC", 
            "description": "Essay with multiple cliches, generic language, and potential plagiarism",
            "text": """
            From a young age, I have always been passionate about making a difference in the world. This passion has driven me to pursue excellence in all areas of my life, as I believe that hard work and dedication are the keys to success.

            Growing up, I faced many challenges that tested my resolve. Like many teenagers, I struggled with finding my place in the world and understanding who I truly was. However, through perseverance and determination, I was able to overcome these obstacles and emerge stronger than ever before.

            One experience that changed my life forever was when I volunteered at a local soup kitchen during my junior year of high school. Seeing the faces of those less fortunate than myself really opened my eyes to the harsh realities of life. It was a real eye-opener that made me realize how blessed I am to have the opportunities that I do.

            At the end of the day, this experience taught me that it's not about what you have, but about what you give back to others. I learned that true happiness comes from helping others and making a positive impact in their lives. This revelation has shaped my entire worldview and influenced my decision to pursue a career in social work.

            The lessons I learned from this experience will stay with me for the rest of my life. I now understand that success isn't measured by material possessions or personal achievements, but by the positive difference you make in the lives of others. This philosophy has become the driving force behind everything I do.

            In conclusion, my volunteer experience at the soup kitchen has been instrumental in shaping who I am today. It has taught me the importance of giving back to the community and has inspired me to dedicate my life to helping others achieve their full potential.
            """,
            "context": {
                "essay_prompt": "Describe a meaningful experience and its impact on you",
                "word_limit": 650,
                "user_profile": {"grade": "12", "interests": ["social work", "volunteering"]}
            }
        }
    ]
    
    for essay_data in test_essays:
        print(f"\n📄 Testing Essay: {essay_data['name']}")
        print(f"Description: {essay_data['description']}")
        print("-" * 60)
        
        # Run validation
        validation_result = run_qa_validation(essay_data["text"], essay_data["context"])
        
        # Display results
        display_validation_results(validation_result)
        
        print("=" * 60)
    
    print("\n✅ QA Pipeline Demo Complete!")
    print("The validation pipeline successfully identified issues in problematic essays")
    print("and provided actionable recommendations for improvement.")
    
    # Additional demo: Show individual validator results
    print("\n🔧 Individual Validator Demo")
    print("-" * 40)
    
    # Test individual validators
    test_essay = test_essays[1]["text"]  # Use problematic essay
    test_context = test_essays[1]["context"]
    
    validators = [
        ("Plagiarism Detector", PlagiarismValidator()),
        ("Cliche Detector", ClicheDetectionValidator()),
        ("Outline Alignment", OutlineAlignmentValidator()),
        ("Final Polish", FinalPolishValidator())
    ]
    
    for name, validator in validators:
        print(f"\n📊 {name}:")
        result = validator.validate(test_essay, test_context)
        print(f"   Score: {result.score:.2f}")
        print(f"   Passed: {result.passed}")
        print(f"   Issues: {len(result.issues)}")
        if result.issues:
            for issue in result.issues[:2]:  # Show first 2 issues
                print(f"     • {issue.message}")
            if len(result.issues) > 2:
                print(f"     • ... and {len(result.issues) - 2} more")
    
    print("\n🎉 Demo finished! Check the validation results above.")


async def demo_plagiarism_validator():
    """Demonstrate plagiarism validation."""
    print("\n🕵️ Plagiarism Validator Demo")
    print("-" * 40)
    
    from essay_agent.tools.validation_tools import PlagiarismValidator
    
    validator = PlagiarismValidator(threshold=0.15)
    
    # Test with potentially plagiarized content
    plagiarized_text = """
    Education is the most powerful weapon which you can use to change the world. 
    Nelson Mandela once said this, and it has become one of the most quoted 
    statements about education. This quote emphasizes the transformative power 
    of education in society and its ability to create positive change.
    """
    
    context = {"essay_prompt": "Discuss the importance of education"}
    
    print("Testing potentially plagiarized content...")
    try:
        result = await validator.validate(plagiarized_text, context)
        print(f"✅ Validation completed: {'PASS' if result.passed else 'FAIL'}")
        print(f"📊 Score: {result.score:.2f}")
        print(f"🕒 Execution time: {result.execution_time:.2f}s")
        
        if result.issues:
            print(f"⚠️  Issues found: {len(result.issues)}")
            for issue in result.issues:
                print(f"  - {issue.message}")
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")


async def demo_cliche_validator():
    """Demonstrate cliche detection."""
    print("\n🎭 Cliche Detection Validator Demo")
    print("-" * 40)
    
    from essay_agent.tools.validation_tools import ClicheDetectionValidator
    
    validator = ClicheDetectionValidator(severity_threshold=3)
    
    # Test with cliche-heavy content
    cliche_text = """
    This experience changed my life and taught me that hard work pays off. 
    I learned to never give up on my dreams and to step out of my comfort zone. 
    Through this journey of discovery, I found my passion for helping others 
    and making a difference in the world. I believe that anything is possible 
    if you put your mind to it.
    """
    
    context = {"essay_prompt": "Describe a transformative experience"}
    
    print("Testing cliche-heavy content...")
    try:
        result = await validator.validate(cliche_text, context)
        print(f"✅ Validation completed: {'PASS' if result.passed else 'FAIL'}")
        print(f"📊 Score: {result.score:.2f}")
        print(f"🕒 Execution time: {result.execution_time:.2f}s")
        
        if result.issues:
            print(f"⚠️  Cliches found: {len(result.issues)}")
            for issue in result.issues:
                print(f"  - \"{issue.text_excerpt}\": {issue.message}")
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")


async def demo_outline_alignment_validator():
    """Demonstrate outline alignment validation."""
    print("\n📝 Outline Alignment Validator Demo")
    print("-" * 40)
    
    from essay_agent.tools.validation_tools import OutlineAlignmentValidator
    
    validator = OutlineAlignmentValidator(min_coverage=0.8)
    
    # Test with poorly aligned content
    essay_text = """
    I like science and math. They are interesting subjects that I enjoy studying. 
    I want to become an engineer someday because engineering is a good career. 
    I think I would be good at it because I am hardworking and dedicated.
    """
    
    outline = {
        "hook": "Describe a specific moment when you discovered your passion for engineering",
        "context": "Explain the circumstances that led to this discovery",
        "conflict": "Describe a challenge you faced in pursuing this interest",
        "growth": "Explain how you overcame the challenge and what you learned",
        "reflection": "Reflect on how this experience shapes your future goals"
    }
    
    context = {
        "essay_prompt": "Describe your passion for engineering",
        "outline": outline
    }
    
    print("Testing poorly aligned essay...")
    try:
        result = await validator.validate(essay_text, context)
        print(f"✅ Validation completed: {'PASS' if result.passed else 'FAIL'}")
        print(f"📊 Score: {result.score:.2f}")
        print(f"🕒 Execution time: {result.execution_time:.2f}s")
        
        if result.issues:
            print(f"⚠️  Alignment issues: {len(result.issues)}")
            for issue in result.issues:
                print(f"  - {issue.message}")
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")


async def demo_final_polish_validator():
    """Demonstrate final polish validation."""
    print("\n✨ Final Polish Validator Demo")
    print("-" * 40)
    
    from essay_agent.tools.validation_tools import FinalPolishValidator
    
    validator = FinalPolishValidator(comprehensive=True)
    
    # Test with essay that has various issues
    problematic_essay = """
    This experiance changed my life in many ways. I learned alot about myself 
    and others, and it effected how I view the world. Their were many challenges 
    that I faced, but I overcame them threw hard work and dedication. This essay 
    is very short and doesn't meet the word count requirements.
    """
    
    context = {
        "word_limit": 650,
        "essay_prompt": "Describe a transformative experience",
        "user_profile": {}
    }
    
    print("Testing essay with technical issues...")
    try:
        result = await validator.validate(problematic_essay, context)
        print(f"✅ Validation completed: {'PASS' if result.passed else 'FAIL'}")
        print(f"📊 Score: {result.score:.2f}")
        print(f"🕒 Execution time: {result.execution_time:.2f}s")
        
        if result.issues:
            print(f"⚠️  Issues found: {len(result.issues)}")
            issue_types = {}
            for issue in result.issues:
                issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
            
            for issue_type, count in issue_types.items():
                print(f"  - {issue_type}: {count} issues")
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")


if __name__ == "__main__":
    asyncio.run(demo_qa_pipeline()) 