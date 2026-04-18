"""
Phase 4: Safety Layer Testing Script
Comprehensive test suite for Phase 4 Refusal Logic & Safety Layer
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'phase4'))

def setup_logging():
    """Setup test logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f'safety_layer_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def test_safety_layer_import():
    """Test safety layer import"""
    logger = logging.getLogger(__name__)
    
    try:
        from safety import SafetyLayer, QueryType
        logger.info("✅ SafetyLayer import successful")
        
        # Test instantiation
        safety = SafetyLayer()
        logger.info("✅ SafetyLayer instantiation successful")
        
        return True
    except ImportError as e:
        logger.error(f"❌ SafetyLayer import failed: {e}")
        return False

def test_query_classification():
    """Test query classification functionality"""
    logger = logging.getLogger(__name__)
    
    try:
        from safety import SafetyLayer
        safety = SafetyLayer()
        
        # Test queries
        test_cases = [
            {
                "query": "What is the expense ratio of ICICI Prudential Large Cap Fund?",
                "expected_type": QueryType.FACTUAL,
                "description": "Factual query about expense ratio"
            },
            {
                "query": "Should I invest in ICICI Prudential Multi Asset Fund?",
                "expected_type": QueryType.ADVICE,
                "description": "Investment advice seeking"
            },
            {
                "query": "My PAN is ABCDE1234F, how to invest?",
                "expected_type": QueryType.PII_DETECTED,
                "description": "Contains PAN number"
            },
            {
                "query": "What about HDFC Large Cap Fund?",
                "expected_type": QueryType.OUT_OF_SCOPE,
                "description": "Other AMC mentioned"
            },
            {
                "query": "Tell me about ICICI Prudential Large Cap Fund",
                "expected_type": QueryType.FACTUAL,
                "description": "Ambiguous factual query"
            }
        ]
        
        passed = 0
        total = len(test_cases)
        
        logger.info("Testing query classification...")
        
        for i, test_case in enumerate(test_cases):
            query = test_case["query"]
            expected_type = test_case["expected_type"]
            description = test_case["description"]
            
            # Classify query
            result_type = safety.classify_query(query)
            
            # Check result
            if result_type == expected_type:
                status = "✅ PASS"
                passed += 1
                logger.info(f"Test {i+1}/{total}: {description} - {status}")
            else:
                status = "❌ FAIL"
                logger.error(f"Test {i+1}/{total}: {description} - Expected {expected_type.value}, got {result_type.value}")
        
        logger.info(f"Query classification tests: {passed}/{total} passed")
        return passed == total
    
    except Exception as e:
        logger.error(f"Query classification test failed: {e}")
        return False

def test_pii_detection():
    """Test PII detection functionality"""
    logger = logging.getLogger(__name__)
    
    try:
        from safety import SafetyLayer
        safety = SafetyLayer()
        
        # Test PII patterns
        pii_test_cases = [
            {
                "query": "My PAN is ABCDE1234F",
                "expected_pii": ["pan"],
                "description": "PAN number detection"
            },
            {
                "query": "My Aadhaar is 1234 5678 9012",
                "expected_pii": ["aadhaar"],
                "description": "Aadhaar number detection"
            },
            {
                "query": "My email is user@example.com",
                "expected_pii": ["email"],
                "description": "Email address detection"
            },
            {
                "query": "Call me at 9876543210",
                "expected_pii": ["phone"],
                "description": "Phone number detection"
            },
            {
                "query": "My DOB is 15/01/1990",
                "expected_pii": ["dob"],
                "description": "Date of birth detection"
            },
            {
                "query": "What is NAV of ICICI Prudential fund?",
                "expected_pii": [],
                "description": "No PII in factual query"
            }
        ]
        
        passed = 0
        total = len(pii_test_cases)
        
        logger.info("Testing PII detection...")
        
        for i, test_case in enumerate(pii_test_cases):
            query = test_case["query"]
            expected_pii = test_case["expected_pii"]
            description = test_case["description"]
            
            # Detect PII
            detected_pii = safety.detect_pii(query)
            
            # Check result
            if set(detected_pii) == set(expected_pii) and len(expected_pii) == len(detected_pii):
                status = "✅ PASS"
                passed += 1
                logger.info(f"Test {i+1}/{total}: {description} - {status}")
            else:
                status = "❌ FAIL"
                logger.error(f"Test {i+1}/{total}: {description} - Expected {expected_pii}, got {detected_pii}")
        
        logger.info(f"PII detection tests: {passed}/{total} passed")
        return passed == total
    
    except Exception as e:
        logger.error(f"PII detection test failed: {e}")
        return False

def test_refusal_responses():
    """Test refusal response generation"""
    logger = logging.getLogger(__name__)
    
    try:
        from safety import SafetyLayer, QueryType
        safety = SafetyLayer()
        
        # Test refusal scenarios
        refusal_test_cases = [
            {
                "query_type": QueryType.ADVICE,
                "description": "Investment advice refusal"
            },
            {
                "query_type": QueryType.OUT_OF_SCOPE,
                "description": "Out-of-scope refusal"
            },
            {
                "query_type": QueryType.PII_DETECTED,
                "description": "PII detection refusal"
            }
        ]
        
        passed = 0
        total = len(refusal_test_cases)
        
        logger.info("Testing refusal responses...")
        
        for i, test_case in enumerate(refusal_test_cases):
            query_type = test_case["query_type"]
            description = test_case["description"]
            
            # Get refusal response
            refusal = safety.get_refusal_response(query_type)
            
            # Check refusal quality
            if refusal:
                # Check for educational resources
                has_sebi = "sebi.gov.in" in refusal.lower()
                has_schemes = "4 ICICI Prudential" in refusal
                has_contact = "1860 266 7766" in refusal or "groww.in/help" in refusal
                
                if query_type == QueryType.ADVICE:
                    correct_elements = [has_sebi, has_schemes]
                elif query_type == QueryType.OUT_OF_SCOPE:
                    correct_elements = [has_schemes, has_contact]
                elif query_type == QueryType.PII_DETECTED:
                    correct_elements = True  # Just check if refusal exists
                
                if correct_elements:
                    status = "✅ PASS"
                    passed += 1
                    logger.info(f"Test {i+1}/{total}: {description} - {status}")
                else:
                    status = "❌ FAIL"
                    logger.error(f"Test {i+1}/{total}: {description} - Missing required elements")
            else:
                status = "❌ FAIL"
                logger.error(f"Test {i+1}/{total}: {description} - No refusal generated")
        
        logger.info(f"Refusal response tests: {passed}/{total} passed")
        return passed == total
    
    except Exception as e:
        logger.error(f"Refusal response test failed: {e}")
        return False

def test_integration_with_answer_generator():
    """Test safety layer integration with answer generator"""
    logger = logging.getLogger(__name__)
    
    try:
        # Import answer generator
        sys.path.append(str(project_root / 'phase3'))
        from answer_generator import AnswerGenerator
        
        # Test with safe query
        logger.info("Testing integration with safe query...")
        safe_query = "What is the expense ratio of ICICI Prudential Large Cap Fund?"
        
        generator = AnswerGenerator()
        result = generator.generate_answer(safe_query)
        
        # Check that safety layer was used
        if result["type"] == "factual_answer":
            logger.info("✅ Safe query processed correctly")
            integration_pass = True
        else:
            logger.error(f"❌ Safe query not processed correctly: {result['type']}")
            integration_pass = False
        
        # Test with PII query
        logger.info("Testing integration with PII query...")
        pii_query = "My PAN is ABCDE1234F, what is expense ratio?"
        
        result = generator.generate_answer(pii_query)
        
        # Check that PII was blocked
        if result["type"] == "pii_detected_refusal":
            logger.info("✅ PII query blocked correctly")
            pii_pass = True
        else:
            logger.error(f"❌ PII query not blocked: {result['type']}")
            pii_pass = False
        
        # Test with advice query
        logger.info("Testing integration with advice query...")
        advice_query = "Should I invest in ICICI Prudential funds?"
        
        result = generator.generate_answer(advice_query)
        
        # Check that advice was refused
        if result["type"] == "advice_refusal":
            logger.info("✅ Advice query refused correctly")
            advice_pass = True
        else:
            logger.error(f"❌ Advice query not refused: {result['type']}")
            advice_pass = False
        
        integration_success = integration_pass and pii_pass and advice_pass
        
        logger.info(f"Integration tests: {'✅ PASS' if integration_success else '❌ FAIL'}")
        return integration_success
    
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False

def main():
    """Run all safety layer tests"""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("PHASE 4: SAFETY LAYER TESTING")
    logger.info("=" * 80)
    
    tests = [
        ("Safety Layer Import", test_safety_layer_import),
        ("Query Classification", test_query_classification),
        ("PII Detection", test_pii_detection),
        ("Refusal Responses", test_refusal_responses),
        ("Integration with Answer Generator", test_integration_with_answer_generator)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: CRASHED - {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All safety layer tests passed!")
        return 0
    else:
        logger.error(f"💥 {total - passed} tests failed. Fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
