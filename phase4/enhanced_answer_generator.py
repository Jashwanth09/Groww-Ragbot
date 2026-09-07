"""
Phase 4.4: Integration with Phase 3
Enhanced Answer Generator with Safety Layer Integration
"""

import os
import sys
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase3'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from retrieval_pipeline import SimpleRetrievalPipeline
from safety import SafetyLayer, QueryType
from answer_generator import AnswerGenerator

class EnhancedAnswerGenerator:
    """Enhanced Answer Generator with Phase 4 Safety Layer Integration"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize enhanced answer generator"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize Phase 3 components
        self.phase3_generator = AnswerGenerator(config)
        self.safety_layer = SafetyLayer()
        
        self.logger.info("Enhanced Answer Generator initialized with Phase 3 + Phase 4 integration")
    
    def generate_answer(self, query: str) -> Dict[str, Any]:
        """
        Generate answer with safety layer integration
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with answer, classification, and safety status
        """
        try:
            self.logger.info(f"Processing query: {query}")
            
            # Step 1: Query Classification (Phase 4.1)
            query_type = self.safety_layer.classify_query(query)
            self.logger.info(f"Query classified as: {query_type.value}")
            
            # Step 2: PII Detection (Phase 4.3)
            pii_detected = self.safety_layer.detect_pii(query)
            if pii_detected:
                self.logger.warning(f"PII detected in query: {pii_detected}")
                return {
                    "answer": self.safety_layer.get_refusal_response("pii_detected"),
                    "query_type": QueryType.PII_DETECTED.value,
                    "safety_blocked": True,
                    "confidence": 0.0
                }
            
            # Step 3: Safety Check (Phase 4.3)
            should_block = self.safety_layer.should_block_query(query, query_type)
            if should_block:
                self.logger.info(f"Query blocked by safety layer: {query_type.value}")
                return {
                    "answer": self.safety_layer.get_refusal_response(query_type),
                    "query_type": query_type.value,
                    "safety_blocked": True,
                    "confidence": 0.0
                }
            
            # Step 4: Safe Query Processing (Phase 4.3)
            safe_query = self.safety_layer.get_safe_query_for_llm(query)
            
            # Step 5: Generate Answer (Phase 3)
            if query_type == QueryType.FACTUAL:
                # Use Phase 3 answer generation
                phase3_answer = self.phase3_generator.generate_answer(safe_query)
                
                # Step 6: Answer Validation (Phase 4.3)
                validated_answer = self.safety_layer.validate_response_quality(phase3_answer.get("answer", ""))
                
                return {
                    "answer": validated_answer,
                    "query_type": query_type.value,
                    "safety_blocked": False,
                    "confidence": 0.8,
                    "phase3_integration": True,
                    "phase4_safety": True,
                    "retrieval_count": len(phase3_answer.get("retrieved_chunks", [])),
                    "citations": phase3_answer.get("citations", [])
                }
            
            elif query_type == QueryType.ADVICE:
                # Return advice refusal (Phase 4.2)
                return {
                    "answer": self.safety_layer.get_refusal_response(QueryType.ADVICE),
                    "query_type": QueryType.ADVICE.value,
                    "safety_blocked": False,
                    "confidence": 0.9,
                    "phase4_safety": True,
                    "refusal_type": "advice"
                }
            
            elif query_type == QueryType.OUT_OF_SCOPE:
                # Return out-of-scope refusal (Phase 4.2)
                return {
                    "answer": self.safety_layer.get_refusal_response(QueryType.OUT_OF_SCOPE),
                    "query_type": QueryType.OUT_OF_SCOPE.value,
                    "safety_blocked": False,
                    "confidence": 0.9,
                    "phase4_safety": True,
                    "refusal_type": "out_of_scope"
                }
            
            else:
                # Fallback response
                return {
                    "answer": "I apologize, but I can only provide factual information about the 4 ICICI Prudential Direct Growth schemes. Please check the official factsheet for complete details.",
                    "query_type": "unknown",
                    "safety_blocked": False,
                    "confidence": 0.3
                }
        
        except Exception as e:
            self.logger.error(f"Answer generation failed: {str(e)}")
            return {
                "answer": "I encountered an error processing your query. Please try again later.",
                "query_type": "error",
                "safety_blocked": False,
                "confidence": 0.0
            }
    
    def log_query_classification(self, query: str, query_type: str, confidence: float):
        """Log query classification for monitoring"""
        self.logger.info(f"Query Classification: '{query}' -> {query_type} (confidence: {confidence})")
    
    def log_safety_check(self, query: str, blocked: bool, reason: str = ""):
        """Log safety check results"""
        if blocked:
            self.logger.warning(f"Safety Layer Blocked: '{query}' - Reason: {reason}")
        else:
            self.logger.info(f"Safety Layer Passed: '{query}' - Query allowed for processing")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status for monitoring"""
        return {
            "phase3_generator": "operational",
            "safety_layer": "operational",
            "integration_status": "active",
            "last_updated": datetime.now().isoformat(),
            "version": "1.0.0"
        }
