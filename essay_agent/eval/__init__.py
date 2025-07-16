"""essay_agent.eval

Evaluation harness for testing essay agent performance and quality.
Provides comprehensive metrics and validation for essay generation workflow.
"""

from .sample_prompts import (
    SAMPLE_PROMPTS,
    create_test_profile,
    create_test_profile_arts,
    create_test_profile_community,
    get_all_prompts,
    get_prompt_by_id,
    get_prompt_keywords
)

from .metrics import (
    EvaluationReport,
    WordCountValidator,
    JSONSchemaValidator,
    KeywordSimilarityScorer,
    ErrorValidator,
    QualityMetrics,
    evaluate_essay_result
)

from .test_runs import (
    run_evaluation,
    print_evaluation_summary
)

__all__ = [
    # Sample prompts
    "SAMPLE_PROMPTS",
    "create_test_profile",
    "create_test_profile_arts",
    "create_test_profile_community",
    "get_all_prompts",
    "get_prompt_by_id",
    "get_prompt_keywords",
    
    # Metrics and validation
    "EvaluationReport",
    "WordCountValidator",
    "JSONSchemaValidator",
    "KeywordSimilarityScorer",
    "ErrorValidator",
    "QualityMetrics",
    "evaluate_essay_result",
    
    # Test execution
    "run_evaluation",
    "run_real_evaluation",
    "print_evaluation_summary"
]

# Version info
__version__ = "1.0.0"
__author__ = "Essay Agent Team"
__description__ = "Comprehensive evaluation harness for essay agent testing"


def quick_eval(user_id: str = "quick_eval_user", debug: bool = False):
    """
    Quick evaluation run for development and debugging.
    
    Args:
        user_id: User ID for the evaluation
        debug: Whether to enable debug mode
        
    Returns:
        Summary of evaluation results
    """
    results = run_evaluation(user_id=user_id, debug=debug)
    print_evaluation_summary(results)
    
    # Return summary stats
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    
    return {
        "total_tests": total_count,
        "passed": passed_count,
        "failed": total_count - passed_count,
        "pass_rate": passed_count / total_count if total_count > 0 else 0.0,
        "avg_execution_time": sum(r.execution_time for r in results) / len(results) if results else 0.0,
        "results": results
    }


def validate_single_result(result, prompt_id: str, target_word_count: int, keywords: list[str], use_legacy_metrics: bool = False):
    """
    Validate a single essay result with comprehensive metrics.
    
    Args:
        result: EssayResult to validate
        prompt_id: ID of the prompt used
        target_word_count: Target word count for validation
        keywords: Expected keywords for similarity scoring
        use_legacy_metrics: Whether to use legacy heuristic evaluation
        
    Returns:
        EvaluationReport with validation results
    """
    return evaluate_essay_result(
        result=result,
        prompt_keywords=keywords,
        target_word_count=target_word_count,
        execution_time=0.0,  # Not timed for single validation
        prompt_id=prompt_id,
        use_legacy_metrics=use_legacy_metrics
    )


def get_evaluation_config():
    """
    Get the current evaluation configuration.
    
    Returns:
        Dict with evaluation settings and thresholds
    """
    return {
        "word_count_tolerance": 0.05,  # 5% tolerance for word count
        "keyword_similarity_threshold": 0.3,  # Minimum similarity score
        "minimum_pass_rate": 0.8,  # 80% pass rate required
        "required_outline_sections": ["hook", "context", "conflict", "growth", "reflection"],
        "required_story_fields": ["title", "description"],
        "quality_metrics": {
            "readability_enabled": True,
            "sentence_variety_enabled": True,
            "vocabulary_richness_enabled": True
        }
    } 


def run_real_evaluation(user_id: str = "real_eval_user", debug: bool = False, use_legacy_metrics: bool = False):
    """
    Run evaluation with real GPT calls (no mocks).
    
    Args:
        user_id: User ID for the evaluation
        debug: Whether to enable debug mode
        use_legacy_metrics: Whether to use legacy heuristic evaluation
        
    Returns:
        List of evaluation reports
    """
    import time
    from essay_agent.agent_legacy import EssayAgent
    
    results = []
    profile = create_test_profile()
    
    print(f"🚀 Starting real GPT evaluation with {len(SAMPLE_PROMPTS)} prompts...")
    print("⚠️  This will make actual API calls and may take several minutes per prompt")
    print("=" * 60)
    
    # Run evaluation for each prompt
    for i, (prompt_id, prompt) in enumerate(SAMPLE_PROMPTS.items(), 1):
        print(f"\n[{i}/{len(SAMPLE_PROMPTS)}] Running prompt '{prompt_id}'...")
        print(f"📝 Prompt: {prompt.text[:100]}...")
        print(f"📏 Target words: {prompt.word_limit}")
        
        agent = EssayAgent(user_id=f"{user_id}_{prompt_id}")
        keywords = get_prompt_keywords(prompt_id)
        
        start_time = time.time()
        try:
            result = agent.run(prompt=prompt, profile=profile, debug=debug)
            execution_time = time.time() - start_time
            
            report = evaluate_essay_result(
                result=result,
                prompt_keywords=keywords,
                target_word_count=prompt.word_limit,
                execution_time=execution_time,
                prompt_id=prompt_id,
                use_legacy_metrics=use_legacy_metrics
            )
            results.append(report)
            
            status = "✅ PASSED" if report.passed else "❌ FAILED"
            print(f"{status} - {execution_time:.1f}s")
            
        except Exception as e:
            execution_time = time.time() - start_time
            report = EvaluationReport(
                prompt_id=prompt_id,
                passed=False,
                execution_time=execution_time
            )
            report.add_error(f"Execution failed: {str(e)}")
            results.append(report)
            
            print(f"❌ FAILED - {execution_time:.1f}s - Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 Final Results:")
    print_evaluation_summary(results)
    
    return results 