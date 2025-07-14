#!/usr/bin/env python3
"""
Real GPT Evaluation Runner

Run essay agent evaluations with actual GPT API calls.
Usage: python -m essay_agent.eval.run_real_eval [options]
"""

import argparse
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import essay_agent
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from essay_agent.eval import run_real_evaluation


def main():
    parser = argparse.ArgumentParser(description="Run essay agent evaluation with real GPT calls")
    parser.add_argument(
        "--user-id", 
        default="real_eval_user",
        help="User ID for the evaluation (default: real_eval_user)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose output"
    )
    parser.add_argument(
        "--check-api-key",
        action="store_true",
        help="Check if OpenAI API key is set and exit"
    )
    
    args = parser.parse_args()
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    if args.check_api_key:
        print("✅ OpenAI API key is set")
        sys.exit(0)
    
    print("🔑 OpenAI API key found")
    
    try:
        results = run_real_evaluation(user_id=args.user_id, debug=args.debug)
        
        # Print summary stats
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        pass_rate = passed_count / total_count if total_count > 0 else 0.0
        
        print(f"\n🎯 Summary:")
        print(f"   Total prompts: {total_count}")
        print(f"   Passed: {passed_count}")
        print(f"   Failed: {total_count - passed_count}")
        print(f"   Pass rate: {pass_rate:.1%}")
        
        # Exit with appropriate code
        if pass_rate < 0.8:  # 80% pass rate threshold
            print("⚠️  Warning: Pass rate below 80%")
            sys.exit(1)
        else:
            print("✅ All evaluations completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n🛑 Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 