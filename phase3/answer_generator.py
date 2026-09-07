"""
Answer Generation Pipeline for Phase 3
Integrates LLM with retrieval system to generate citation-backed answers
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from llm_config import LLMConfig, setup_logging
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from retrieval_pipeline import RetrievalPipeline
from safety import SafetyLayer, QueryType

logger = logging.getLogger(__name__)

class AnswerGenerator:
    """Generates answers using LLM with retrieved context"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self.retrieval_pipeline = RetrievalPipeline()
        self.safety_layer = SafetyLayer()
        self._setup_llm_client()
        
    def _setup_llm_client(self):
        """Initialize LLM client based on provider"""
        if self.config.provider == "groq":
            try:
                import groq
                self.client = groq.Groq(api_key=self.config.api_key)
                logger.info("Groq client initialized")
            except ImportError:
                raise ImportError("Groq library not installed. Run: pip install groq")
                
        elif self.config.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.config.api_key)
                logger.info("OpenAI client initialized")
            except ImportError:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
                
        elif self.config.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.config.api_key)
                logger.info("Anthropic client initialized")
            except ImportError:
                raise ImportError("Anthropic library not installed. Run: pip install anthropic")
                
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    SYSTEM_PROMPT = """You are a mutual fund FAQ assistant for Groww users researching ICICI Prudential schemes.

SCOPE:
You ONLY answer questions about these 4 ICICI Prudential Direct Growth schemes:
1. ICICI Prudential Dynamic Plan Direct Growth
2. ICICI Prudential Large Cap Fund Direct Growth
3. ICICI Prudential Nifty Next 50 Index Fund Direct Growth
4. ICICI Prudential Top 100 Fund Direct Growth

RULES:
1. Answer ONLY factual questions about expense ratios, exit loads, minimum SIP/lumpsum amounts, benchmarks, riskometer ratings, asset allocation, and how to download statements/capital gains reports
2. MANDATORY CITATION: Every answer MUST include exactly ONE source link in format "Source: [URL]"
3. ANSWER FORMAT: Maximum 3 sentences, start with direct answer, end with citation, add timestamp "Last updated: [date]"
4. REFUSE investment advice: For portfolio guidance, consult a SEBI-registered investment advisor
5. OUT-OF-SCOPE handling: If query is about other schemes/AMCs, say "I only cover the 4 ICICI Prudential schemes listed above"
"""

    OUT_OF_SCOPE_RESPONSES = {
        "other_schemes": "I only cover the 4 ICICI Prudential schemes listed above: ICICI Prudential Dynamic Plan Direct Growth, ICICI Prudential Large Cap Fund Direct Growth, ICICI Prudential Nifty Next 50 Index Fund Direct Growth, and ICICI Prudential Top 100 Fund Direct Growth.",
        "investment_advice": "For investment guidance and portfolio recommendations, please consult a SEBI-registered investment advisor. 📚 Learn more: https://investor.sebi.gov.in Find SEBI-registered advisors: https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes",
        "account_issues": "For account-related queries, transaction issues, or technical support, please contact Groww Support or ICICI Prudential customer care directly.",
        "predictions": "I cannot predict future returns or fund performance. Past performance does not guarantee future results. Please refer to the scheme information documents for historical data."
    }

    def _classify_query(self, query: str) -> str:
        """Classify query type for appropriate response"""
        query_lower = query.lower()
        
        # Check for out-of-scope schemes
        other_amcs = ["hdfc", "sbi", "axis", "kotak", "reliance", "mirae", "nippon", "dsp", "tata", "franklin"]
        if any(amc in query_lower for amc in other_amcs):
            return "other_schemes"
            
        # Check for investment advice keywords
        advice_keywords = ["should i", "recommend", "best", "good investment", "portfolio", "invest", "buy", "sell"]
        if any(keyword in query_lower for keyword in advice_keywords):
            return "investment_advice"
            
        # Check for account/transaction issues
        account_keywords = ["account", "login", "password", "kyc", "pan", "aadhar", "transaction", "redemption", "purchase"]
        if any(keyword in query_lower for keyword in account_keywords):
            return "account_issues"
            
        # Check for prediction requests
        prediction_keywords = ["predict", "future", "will", "expected", "forecast", "target"]
        if any(keyword in query_lower for keyword in prediction_keywords):
            return "predictions"
            
        return "factual"

    def _extract_urls_from_chunks(self, chunks: List[Dict]) -> List[str]:
        """Extract source URLs from retrieved chunks"""
        urls = []
        for chunk in chunks:
            if 'metadata' in chunk and 'source_url' in chunk['metadata']:
                urls.append(chunk['metadata']['source_url'])
        return list(set(urls))  # Remove duplicates

    def _generate_with_groq(self, prompt: str) -> str:
        """Generate response using Groq"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return "I apologize, but I'm unable to process your request at the moment. Please try again later."

    def _generate_with_openai(self, prompt: str) -> str:
        """Generate response using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "I apologize, but I'm unable to process your request at the moment. Please try again later."

    def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate response using Anthropic Claude"""
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return "I apologize, but I'm unable to process your request at the moment. Please try again later."

    def _format_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks into context for LLM"""
        context = "RELEVANT INFORMATION:\n\n"
        for i, chunk in enumerate(chunks, 1):
            context += f"Source {i}:\n{chunk['text']}\n"
            if 'metadata' in chunk and 'source_url' in chunk['metadata']:
                context += f"URL: {chunk['metadata']['source_url']}\n"
            context += "\n"
        return context

    def _validate_citation(self, answer: str, available_urls: List[str]) -> bool:
        """Validate that answer contains proper citation"""
        if not available_urls:
            return True  # No URLs available, skip validation
            
        # Check if answer contains any of the available URLs
        for url in available_urls:
            if url in answer:
                return True
        return False

    def generate_answer(self, query: str) -> Dict[str, Any]:
        """Generate answer for user query"""
        start_time = datetime.now()
        
        try:
            # Classify query using safety layer
            query_type = self.safety_layer.classify_query(query)
            self.safety_layer.log_query_classification(query, query_type)
            
            # Handle blocked queries
            if self.safety_layer.should_block_query(query_type):
                refusal = self.safety_layer.get_refusal_response(query_type)
                logger.info(f"Query blocked: {query_type}")
                return {
                    "query": query,
                    "answer": refusal,
                    "type": f"{query_type}_refusal",
                    "confidence": "high",
                    "retrieved_chunks": [],
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Retrieve relevant chunks
            retrieved_chunks = self.retrieval_pipeline.process_query(
                query, 
                k=self.config.top_k
            )
            # Filter by threshold if needed
            retrieved_chunks = self.retrieval_pipeline.filter_results(
                retrieved_chunks, min_similarity=self.config.similarity_threshold
            )
            
            if not retrieved_chunks:
                return {
                    "query": query,
                    "answer": "I couldn't find specific information about your query in my current knowledge base. Please check official ICICI Prudential factsheet or contact customer support.",
                    "type": "no_information",
                    "confidence": "low",
                    "retrieved_chunks": [],
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get safe query for LLM (remove PII if detected)
            safe_query = self.safety_layer.get_safe_query_for_llm(query, query_type)
            
            # Format context
            context = self._format_context(retrieved_chunks)
            
            # Create prompt
            prompt = f"""CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUESTION:
{safe_query if safe_query != query else query}

Provide a factual answer following all rules in the system prompt."""
            
            # Generate answer
            if self.config.provider == "groq":
                answer = self._generate_with_groq(prompt)
            elif self.config.provider == "openai":
                answer = self._generate_with_openai(prompt)
            elif self.config.provider == "anthropic":
                answer = self._generate_with_anthropic(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            # Validate citation and response quality
            available_urls = self._extract_urls_from_chunks(retrieved_chunks)
            citation_valid = self._validate_citation(answer, available_urls)
            
            # Additional quality validation using safety layer
            quality_check = self.safety_layer.validate_response_quality(answer, query_type)
            
            return {
                "query": query,
                "answer": answer,
                "type": "factual_answer",
                "confidence": "high" if retrieved_chunks[0].get("distance", 1.0) < 0.5 else "medium",
                "retrieved_chunks": retrieved_chunks[:3],
                "citation_valid": citation_valid,
                "quality_check": quality_check,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "query": query,
                "answer": "I apologize, but I encountered an error while processing your request. Please try again later.",
                "type": "error",
                "confidence": "low",
                "retrieved_chunks": [],
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }

def main():
    """Test the answer generator"""
    setup_logging()
    
    # Initialize
    generator = AnswerGenerator()
    
    # Test queries
    test_queries = [
        "What is the expense ratio of ICICI Prudential Large Cap Fund Direct Growth?",
        "What is the minimum SIP amount for Dynamic Plan?",
        "Should I invest in ICICI Prudential funds?",
        "What is the NAV of HDFC Top 100 Fund?",
        "How to download capital gains statement?"
    ]
    
    print("Testing Answer Generator:\n")
    for query in test_queries:
        print(f"Query: {query}")
        result = generator.generate_answer(query)
        print(f"Answer: {result['answer']}")
        print(f"Type: {result['type']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Processing time: {result['processing_time']:.2f}s")
        print("-" * 80)

if __name__ == "__main__":
    main()
