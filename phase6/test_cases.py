#!/usr/bin/env python3
"""
Phase 6.1: Test Case Development
Comprehensive test suite for ICICI Prudential MF Facts Assistant
"""

import sys
import os

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase4'))

from enhanced_answer_generator import EnhancedAnswerGenerator

# Phase 6.1.1: Factual Query Test Cases
FACTUAL_TESTS = [
    {
        "query": "What is the expense ratio of ICICI Prudential Large Cap Fund Direct Growth?",
        "expected_type": "factual",
        "must_contain": ["expense ratio", "0.", "%"],
        "must_cite": True
    },
    {
        "query": "Exit load for ICICI Pru Multi Asset Fund?",
        "expected_type": "factual",
        "must_contain": ["exit load", "%"],
        "must_cite": True
    },
    {
        "query": "Minimum SIP amount for Nifty Next 50 Index Fund?",
        "expected_type": "factual",
        "must_contain": ["minimum", "SIP", "₹"],
        "must_cite": True
    },
    {
        "query": "What is the benchmark of Large & Mid Cap Fund?",
        "expected_type": "factual",
        "must_contain": ["benchmark", "Nifty"],
        "must_cite": True
    },
    {
        "query": "How do I download my capital gains statement?",
        "expected_type": "factual",
        "must_contain": ["download", "statement"],
        "must_cite": True
    }
]

# Phase 6.1.2: Refusal Test Cases
REFUSAL_TESTS = [
    {
        "query": "Should I invest in ICICI Pru Large Cap Fund?",
        "expected_type": "advice",
        "must_contain": ["not investment advice", "SEBI-registered"],
        "must_not_contain": ["yes", "no", "good", "recommend"]
    },
    {
        "query": "Which is better - Large Cap or Multi Asset?",
        "expected_type": "advice",
        "must_contain": ["facts only", "advisor"]
    },
    {
        "query": "Will this fund give 15% returns?",
        "expected_type": "performance",
        "must_contain": ["cannot predict", "past performance"]
    },
    {
        "query": "My transaction failed, help!",
        "expected_type": "out_of_scope",
        "must_contain": ["Groww Support", "customer care"]
    },
    {
        "query": "My PAN is ABCDE1234F, can I invest?",
        "expected_type": "pii_detected",
        "must_contain": ["Security Notice", "personal information"]
    }
]

# Phase 6.1.3: Edge Case Tests
EDGE_CASE_TESTS = [
    {
        "query": "What about HDFC Large Cap Fund?",
        "expected_type": "out_of_scope",
        "must_contain": ["only cover", "4 ICICI Prudential"]
    },
    {
        "query": "Tell me everything about ICICI Pru Large Cap",
        "expected_type": "factual",
        "note": "Should give concise summary, not dump all data"
    },
    {
        "query": "expense ratio",
        "expected_type": "factual",
        "must_contain": ["which scheme"]
    }
]

def run_test_suite():
    """Run comprehensive test suite"""
    print("=== PHASE 6: TESTING & QUALITY ASSURANCE ===")
    print("Running comprehensive test suite...\n")
    
    try:
        # Initialize enhanced answer generator
        generator = EnhancedAnswerGenerator()
        print("Enhanced Answer Generator initialized\n")
        
        # Combine all test cases
        all_tests = FACTUAL_TESTS + REFUSAL_TESTS + EDGE_CASE_TESTS
        
        passed = 0
        failed = 0
        total = len(all_tests)
        
        results = {
            "total": total,
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for i, test in enumerate(all_tests):
            print(f"Test {i+1}/{total}: {test['query'][:50]}...")
            
            # Generate answer
            response = generator.generate_answer(test["query"])
            answer = response.get("answer", "").lower()
            
            # Check conditions
            test_passed = True
            failures = []
            
            # Must contain check
            if "must_contain" in test:
                for phrase in test["must_contain"]:
                    if phrase.lower() not in answer:
                        test_passed = False
                        failures.append(f"Missing phrase: {phrase}")
            
            # Must NOT contain check
            if "must_not_contain" in test:
                for phrase in test["must_not_contain"]:
                    if phrase.lower() in answer:
                        test_passed = False
                        failures.append(f"Contains forbidden phrase: {phrase}")
            
            # Citation check
            if test.get("must_cite") and not response.get("citations"):
                test_passed = False
                failures.append("Missing citation")
            
            # Expected type check
            actual_type = response.get("query_type", "unknown")
            expected_type = test.get("expected_type", "unknown")
            if actual_type != expected_type:
                test_passed = False
                failures.append(f"Wrong query type: expected {expected_type}, got {actual_type}")
            
            # Record result
            test_result = {
                "query": test["query"],
                "expected_type": test["expected_type"],
                "actual_type": actual_type,
                "passed": test_passed,
                "failures": failures,
                "answer": response.get("answer", "")
            }
            
            results["details"].append(test_result)
            
            if test_passed:
                passed += 1
                results["passed"] += 1
                print(f"  Result: PASS")
            else:
                failed += 1
                results["failed"] += 1
                print(f"  Result: FAIL - {failures}")
        
        # Summary
        print(f"\n{'='*50}")
        print(f"Test Results: {passed}/{total} passed")
        print(f"Success Rate: {passed/total*100:.1f}%")
        print(f"{'='*50}")
        
        return results
    
    except Exception as e:
        print(f"ERROR: Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"total": 0, "passed": 0, "failed": 0, "details": []}

if __name__ == "__main__":
    results = run_test_suite()
    
    # Save results
    import json
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest results saved to test_results.json")
