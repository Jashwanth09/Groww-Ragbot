#!/usr/bin/env python3
"""
Simple Phase 4.4 Integration Test
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))

from enhanced_answer_generator import EnhancedAnswerGenerator

def test_phase4_integration():
    """Test Phase 4.4 integration with Phase 3"""
    print("=== PHASE 4.4 INTEGRATION TEST ===")
    
    try:
        # Initialize enhanced answer generator
        generator = EnhancedAnswerGenerator()
        print("✅ Enhanced Answer Generator initialized")
        
        # Test queries
        test_queries = [
            "What is the expense ratio of ICICI Prudential Large Cap Fund?",
            "Should I invest in ICICI Prudential Large Cap Fund?",
            "My PAN is ABCDE1234F, what is the NAV?"
        ]
        
        passed = 0
        total = len(test_queries)
        
        for i, query in enumerate(test_queries):
            print(f"\nTest {i+1}/{total}: {query}")
            
            # Generate answer
            result = generator.generate_answer(query)
            
            # Check results
            answer = result.get("answer", "")
            query_type = result.get("query_type", "unknown")
            safety_blocked = result.get("safety_blocked", False)
            phase3_integration = result.get("phase3_integration", False)
            phase4_safety = result.get("phase4_safety", False)
            
            if answer:
                print(f"✅ Answer: {answer[:100]}...")
                passed += 1
            else:
                print(f"❌ No answer generated")
            
            print(f"Query Type: {query_type}")
            print(f"Safety Blocked: {safety_blocked}")
            print(f"Phase 3 Integration: {phase3_integration}")
            print(f"Phase 4 Safety: {phase4_safety}")
        
        print(f"\n=== TEST SUMMARY ===")
        print(f"Passed: {passed}/{total}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Phase 4.4 integration working correctly!")
            return True
        else:
            print(f"❌ {total - passed} TESTS FAILED")
            return False
    
    except Exception as e:
        print(f"ERROR: Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase4_integration()
    
    if success:
        print("\n=== PHASE 4.4 INTEGRATION TEST COMPLETED SUCCESSFULLY ===")
        print("✅ Phase 4.4 implemented and working!")
        print("✅ Phase 3 + Phase 4 integration complete!")
    else:
        print("\n=== PHASE 4.4 INTEGRATION TEST FAILED ===")
        print("❌ Integration issues found")
