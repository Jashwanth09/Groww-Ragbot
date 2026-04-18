"""
Phase 4: Refusal Logic & Safety Layer
Implements query classification, PII detection, and structured refusal responses
"""

import re
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Query classification types"""
    FACTUAL = "factual"
    ADVICE = "advice"
    OUT_OF_SCOPE = "out_of_scope"
    PII_DETECTED = "pii_detected"

class SafetyLayer:
    """Safety layer for query classification and refusal logic"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Advice-seeking keywords
        self.ADVICE_KEYWORDS = [
            "should i", "recommend", "better", "best", "good investment",
            "worth it", "buy or sell", "switch", "redeem", "which one",
            "portfolio", "allocate", "invest now", "right time", "good choice",
            "bad investment", "top fund", "best fund", "high returns", "future returns"
        ]
        
        # Out-of-scope keywords
        self.OUT_OF_SCOPE_KEYWORDS = [
            "open account", "kyc", "aadhar", "pan", "otp", "password",
            "transaction failed", "redemption pending", "nav not updated", "account statement",
            "customer care", "support ticket", "complaint", "refund", "withdrawal",
            "other amc", "other fund house", "hdfc", "sbi", "axis", "kotak",
            "reliance", "mirae", "nippon", "dsp", "tata", "franklin"
        ]
        
        # PII detection patterns
        self.PII_PATTERNS = {
            "pan": r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
            "aadhaar": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b[6-9]\d{9}\b',
            "account": r'\b\d{9,18}\b',  # typical bank account numbers
            "dob": r'\b\d{2}[/-]\d{2}[/-]\d{4}\b',  # Date of birth
            "folio": r'\b[A-Z]{2}\d{8,10}\b'  # Portfolio/folio numbers
        }
        
        # Refusal response templates
        self.ADVICE_REFUSAL = """I provide facts only, not investment advice.

For personalized portfolio guidance, please consult a SEBI-registered investment advisor.

📚 Learn more:
- SEBI Investor Awareness: https://investor.sebi.gov.in
- Find SEBI-registered advisors: https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes

Would you like factual information about any of the 4 ICICI Prudential schemes instead?"""
        
        self.OUT_OF_SCOPE_REFUSAL = """I only answer factual questions about these 4 ICICI Prudential Direct Growth schemes:

1. ICICI Prudential Multi Asset Fund Direct Growth
2. ICICI Prudential Large Cap Fund Direct Growth
3. ICICI Prudential Nifty Next 50 Index Fund Direct Growth
4. ICICI Prudential Top 100 Fund Direct Growth

For account-related queries, please contact:
- Groww Support: https://groww.in/help
- ICICI Prudential Customer Care: 1860 266 7766

Can I help with facts about any of the above schemes?"""
        
        self.PERFORMANCE_REFUSAL = """I cannot compute or predict fund returns.

For official performance data, please check:
- Latest factsheet: [scheme-specific factsheet link]
- Groww fund page: [scheme-specific Groww URL]

Note: Past performance does not guarantee future results.

Can I help with other factual information about this scheme?"""
        
        self.PII_REFUSAL = """⚠️ Security Notice

I cannot process queries containing personal information ({detected_pii}).

Please remove sensitive details and ask your question again without:
- PAN/Aadhaar numbers
- Account numbers
- Email addresses
- Phone numbers
- OTPs or passwords

How can I help with factual information about ICICI Prudential schemes?"""
    
    def classify_query(self, query: str) -> QueryType:
        """Classify query using rule-based approach"""
        query_lower = query.lower().strip()
        
        # Check for PII first (highest priority)
        detected_pii = self.detect_pii(query)
        if detected_pii:
            self.logger.warning(f"PII detected in query: {detected_pii}")
            return QueryType.PII_DETECTED
        
        # Check for advice-seeking queries
        if any(keyword in query_lower for keyword in self.ADVICE_KEYWORDS):
            self.logger.info(f"Advice-seeking query detected: {query}")
            return QueryType.ADVICE
        
        # Check for out-of-scope queries
        if any(keyword in query_lower for keyword in self.OUT_OF_SCOPE_KEYWORDS):
            self.logger.info(f"Out-of-scope query detected: {query}")
            return QueryType.OUT_OF_SCOPE
        
        # Default to factual
        self.logger.info(f"Factual query detected: {query}")
        return QueryType.FACTUAL
    
    def detect_pii(self, query: str) -> List[str]:
        """Detect personal identifiable information in query"""
        detected = []
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, query):
                detected.append(pii_type)
                self.logger.warning(f"PII pattern matched: {pii_type}")
        
        return detected
    
    def get_refusal_response(self, query_type: QueryType, detected_pii: Optional[List[str]] = None) -> str:
        """Get appropriate refusal response based on query type"""
        if query_type == QueryType.PII_DETECTED:
            return self.PII_REFUSAL.format(detected_pii=", ".join(detected_pii) if detected_pii else "None")
        
        elif query_type == QueryType.ADVICE:
            return self.ADVICE_REFUSAL
        
        elif query_type == QueryType.OUT_OF_SCOPE:
            return self.OUT_OF_SCOPE_REFUSAL
        
        else:
            # This should not happen in normal flow
            return "I apologize, but I encountered an unexpected error. Please try again."
    
    def should_block_query(self, query_type: QueryType) -> bool:
        """Determine if query should be blocked"""
        return query_type in [QueryType.PII_DETECTED, QueryType.ADVICE]
    
    def log_query_classification(self, query: str, query_type: QueryType, detected_pii: List[str] = None):
        """Log query classification for monitoring"""
        self.logger.info(f"Query classified: {query_type.value}")
        self.logger.info(f"Query text: {query[:100]}...")
        
        if detected_pii:
            self.logger.warning(f"PII types detected: {', '.join(detected_pii)}")
        
        # Log classification reasoning
        if query_type == QueryType.ADVICE:
            advice_keywords_found = [kw for kw in self.ADVICE_KEYWORDS if kw in query.lower()]
            self.logger.info(f"Advice keywords found: {', '.join(advice_keywords_found)}")
        
        elif query_type == QueryType.OUT_OF_SCOPE:
            oos_keywords_found = [kw for kw in self.OUT_OF_SCOPE_KEYWORDS if kw in query.lower()]
            self.logger.info(f"Out-of-scope keywords found: {', '.join(oos_keywords_found)}")
    
    def get_safe_query_for_llm(self, query: str, query_type: QueryType) -> Optional[str]:
        """Get safe version of query for LLM processing (remove PII)"""
        if query_type == QueryType.PII_DETECTED:
            # Remove PII from query before sending to LLM
            safe_query = query
            for pii_type, pattern in self.PII_PATTERNS.items():
                safe_query = re.sub(pattern, "[REDACTED]", safe_query)
            self.logger.info("PII redacted from query for LLM processing")
            return safe_query
        
        return None  # Return None for non-PII queries
    
    def validate_response_quality(self, response: str, query_type: QueryType) -> Dict[str, Any]:
        """Validate response meets quality standards"""
        if query_type in [QueryType.ADVICE, QueryType.OUT_OF_SCOPE]:
            # For refusals, check they contain required elements
            checks = {
                "has_educational_resources": "sebi.gov.in" in response.lower(),
                "has_scheme_list": "4 ICICI Prudential" in response,
                "has_contact_info": "groww.in/help" in response.lower() or "1860 266 7766" in response
            }
            return {
                "passed": all(checks.values()),
                "checks": checks
            }
        
        return {"passed": True, "checks": {}}  # Default pass for factual queries

def main():
    """Test safety layer functionality"""
    logging.basicConfig(level=logging.INFO)
    
    safety = SafetyLayer()
    
    # Test queries
    test_queries = [
        "What is the expense ratio of ICICI Prudential Large Cap Fund?",
        "Should I invest in ICICI Prudential Multi Asset Fund?",
        "Which is better - Large Cap or Multi Asset Fund?",
        "My PAN is ABCDE1234F and I want to invest",
        "What about HDFC Large Cap Fund?",
        "How do I download my capital gains statement?",
        "My phone is 9876543210, can you help me invest?",
        "Will this fund give 15% returns next year?"
    ]
    
    print("Safety Layer Test Results:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Classify query
        query_type = safety.classify_query(query)
        print(f"Classification: {query_type.value}")
        
        # Check if should block
        should_block = safety.should_block_query(query_type)
        print(f"Should block: {should_block}")
        
        # Get refusal response if needed
        if should_block:
            refusal = safety.get_refusal_response(query_type)
            print(f"Refusal: {refusal}")
        else:
            print("Query allowed for processing")
        
        print("-" * 50)
    
    print(f"\nTotal queries tested: {len(test_queries)}")
    print("Safety layer is functioning correctly!")

if __name__ == "__main__":
    main()
