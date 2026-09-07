#!/usr/bin/env python3
"""
Phase 4.4: Integration Test - Phase 3 + Phase 4
Tests the complete pipeline with safety layer integration
"""

import os
import os
import os
import sys
import logging
from datetime import datetime

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from enhanced_answer_generator import EnhancedAnswerGenerator

def setup_logging():
    """Setup test logging"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, f'phase3_phase4_integration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def test_phase3_phase4_integration():
    """Test complete integration of Phase 3 + Phase 4"""
    logger = setup_logging()
    
    try:
        logger.info("=== PHASE 3 + PHASE 4 INTEGRATION TEST ===")
        
        # Initialize enhanced answer generator with Phase 4 safety
        generator = EnhancedAnswerGenerator()
        
        # Test queries covering all scenarios
        test_queries = [
            {
                "query": "What is the expense ratio of ICICI Prudential Large Cap Fund?",
                "expected_type": "factual",
                "description": "Factual query with expected answer"
            },
            {
                "query": "Should I invest in ICICI Prudential Large Cap Fund?",
                "expected_type": "advice",
                "description": "Investment advice - should be blocked"
            },
            {
                "query": "My PAN is ABCDE1234F, what is the NAV?",
                "expected_type": "pii_detected",
                "description": "Query with PII - should be blocked"
            },
            {
                "query": "What about HDFC Large Cap Fund?",
                "expected_type": "out_of_scope",
                "description": "Other AMC query - should get out-of-scope response"
            },
            {
                "query": "What is the minimum SIP amount?",
                "expected_type": "factual",
                "description": "Factual query about minimum SIP"
            },
            {
                "query": "Tell me about ICICI Prudential Large Cap Fund",
                "expected_type": "factual",
                "description": "General factual query"
            },
            {
                "query": "What are the returns of ICICI Prudential Large Cap Fund?",
                "expected_type": "factual",
                "description": "Returns query - should get performance refusal"
            }
        ]
        
        # Run tests
        passed_tests = 0
        total_tests = len(test_queries)
        
        logger.info(f"Running {total_tests} integration tests...")
        
        for i, test_case in enumerate(test_queries):
            query = test_case["query"]
            expected_type = test_case["expected_type"]
            description = test_case["description"]
            
            logger.info(f"Test {i+1}/{total_tests}: {description}")
            logger.info(f"Query: {query}")
            
            # Generate answer
            result = generator.generate_answer(query)
            
            # Check results
            actual_type = result.get("query_type", "unknown")
            safety_blocked = result.get("safety_blocked", False)
            phase3_integration = result.get("phase3_integration", False)
            phase4_safety = result.get("phase4_safety", False)
            
            # Evaluate test
            if actual_type == expected_type:
                status = "✅ PASS"
                passed_tests += 1
                logger.info(f"  Result: {status}")
                logger.info(f"  Query Type: {actual_type}")
                logger.info(f"  Safety Blocked: {safety_blocked}")
                logger.info(f"  Phase 3 Integration: {phase3_integration}")
                logger.info(f"  Phase 4 Safety: {phase4_safety}")
                
                # Check answer quality
                answer = result.get("answer", "")
                if answer and len(answer) > 10:
                    logger.info(f"  Answer: {answer[:100]}...")
            else:
                status = "❌ FAIL"
                logger.error(f"  Result: {status}")
                logger.error(f"  Expected: {expected_type}, Got: {actual_type}")
            
            logger.info(f"Test {i+1}/{total_tests}: {description} - {status}")
        
        # Summary
        logger.info(f"=== INTEGRATION TEST SUMMARY ===")
        logger.info(f"Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
            logger.info("Phase 3 + Phase 4 integration is working correctly!")
            return True
        else:
            logger.error(f"❌ {total_tests - passed_tests} TESTS FAILED")
            logger.error("Integration needs fixes before deployment!")
            return False
    
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_logging()
    success = test_phase3_phase4_integration()
    
    if success:
        print("\n=== PHASE 3 + PHASE 4 INTEGRATION TEST COMPLETED SUCCESSFULLY ===")
        print("✅ Phase 3 (Answer Generation) + Phase 4 (Safety Layer) integration working!")
        print("✅ All safety checks and query classification functioning properly!")
        print("✅ Enhanced answer generator with Phase 4 integration operational!")
    else:
        print("\n=== PHASE 3 + PHASE 4 INTEGRATION TEST FAILED ===")
        print("❌ Integration issues found - check logs for details")

def setup_logging():
    """Setup test logging"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, f'phase3_phase4_integration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def test_phase3_phase4_integration():
    """Test complete integration of Phase 3 + Phase 4"""
    logger = setup_logging()
    
    try:
        logger.info("=== PHASE 3 + PHASE 4 INTEGRATION TEST ===")
        
        # Initialize enhanced answer generator with Phase 4 safety
        generator = EnhancedAnswerGenerator()
        
        # Test queries covering all scenarios
        test_queries = [
            {
                "query": "What is the expense ratio of ICICI Prudential Large Cap Fund?",
                "expected_type": "factual",
                "description": "Factual query with expected answer"
            },
            {
                "query": "Should I invest in ICICI Prudential Large Cap Fund?",
                "expected_type": "advice",
                "description": "Investment advice query - should be blocked"
            },
            {
                "query": "My PAN is ABCDE1234F, what is the NAV?",
                "expected_type": "pii_detected",
                "description": "Query with PII - should be blocked"
            },
            {
                "query": "What about HDFC Large Cap Fund?",
                "expected_type": "out_of_scope",
                "description": "Other AMC query - should get out-of-scope response"
            },
            {
                "query": "What is the minimum SIP amount?",
                "expected_type": "factual",
                "description": "Factual query about minimum SIP"
            },
            {
                "query": "Tell me about ICICI Prudential Large Cap Fund",
                "expected_type": "factual",
                "description": "General factual query"
            },
            {
                "query": "What are the returns of ICICI Prudential Large Cap Fund?",
                "expected_type": "factual",
                "description": "Returns query - should get performance refusal"
            }
        ]
        
        # Run tests
        passed_tests = 0
        total_tests = len(test_queries)
        
        logger.info(f"Running {total_tests} integration tests...")
        
        for i, test_case in enumerate(test_queries):
            query = test_case["query"]
            expected_type = test_case["expected_type"]
            description = test_case["description"]
            
            logger.info(f"Test {i+1}/{total_tests}: {description}")
            logger.info(f"Query: {query}")
            
            # Generate answer
            result = generator.generate_answer(query)
            
            # Check results
            actual_type = result.get("query_type", "unknown")
            safety_blocked = result.get("safety_blocked", False)
            phase3_integration = result.get("phase3_integration", False)
            phase4_safety = result.get("phase4_safety", False)
            
            # Evaluate test
            if actual_type == expected_type:
                status = "✅ PASS"
                passed_tests += 1
                logger.info(f"  Result: {status}")
                logger.info(f"  Query Type: {actual_type}")
                logger.info(f"  Safety Blocked: {safety_blocked}")
                logger.info(f"  Phase 3 Integration: {phase3_integration}")
                logger.info(f"  Phase 4 Safety: {phase4_safety}")
                
                # Check answer quality
                answer = result.get("answer", "")
                if answer and len(answer) > 10:
                    logger.info(f"  Answer: {answer[:100]}...")
            else:
                status = "❌ FAIL"
                logger.error(f"  Result: {status}")
                logger.error(f"  Expected: {expected_type}, Got: {actual_type}")
            
            logger.info(f"Test {i+1}/{total_tests}: {description} - {status}")
        
        # Summary
        logger.info(f"=== INTEGRATION TEST SUMMARY ===")
        logger.info(f"Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
            logger.info("Phase 3 + Phase 4 integration is working correctly!")
            return True
        else:
            logger.error(f"❌ {total_tests - passed_tests} TESTS FAILED")
            logger.error("Integration needs fixes before deployment!")
            return False
    
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_logging()
    success = test_phase3_phase4_integration()
    
    if success:
        print("\n=== PHASE 3 + PHASE 4 INTEGRATION TEST COMPLETED SUCCESSFULLY ===")
        print("✅ Phase 3 (Answer Generation) + Phase 4 (Safety Layer) integration working!")
        print("✅ All safety checks and query classification functioning properly!")
        print("✅ Enhanced answer generator with Phase 4 integration operational!")
    else:
        print("\n=== PHASE 3 + PHASE 4 INTEGRATION TEST FAILED ===")
        print("❌ Integration issues found - check logs for details")
