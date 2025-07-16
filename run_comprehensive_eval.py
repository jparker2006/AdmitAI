#!/usr/bin/env python3
"""
Quick runner for comprehensive essay agent evaluation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add essay_agent to path
sys.path.insert(0, str(Path(__file__).parent))

from essay_agent.eval.comprehensive_test import ComprehensiveTestRunner


async def main():
    """Run comprehensive evaluation"""
    print("🔬 Starting Comprehensive Essay Agent Evaluation Suite")
    print("=" * 80)
    
    # Create output directory
    output_dir = "eval_results_" + str(int(asyncio.get_event_loop().time()))
    
    try:
        runner = ComprehensiveTestRunner(output_dir=output_dir)
        summary = await runner.run_all_tests()
        
        print(f"\n🎯 EVALUATION COMPLETE!")
        print(f"📊 Results: {summary.passed_tests}/{summary.total_tests} tests passed")
        print(f"🐛 Bugs Found: {len(summary.critical_bugs + summary.high_bugs + summary.medium_bugs + summary.low_bugs)}")
        print(f"📁 Details saved to: {output_dir}")
        
        # Return non-zero exit code if critical bugs found
        if summary.critical_bugs or summary.high_bugs:
            print("\n🚨 CRITICAL ISSUES FOUND - Review bug reports!")
            return 1
        else:
            print("\n✅ SYSTEM READY - No critical issues found!")
            return 0
            
    except Exception as e:
        print(f"\n💥 EVALUATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 