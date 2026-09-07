#!/usr/bin/env python3
"""
Direct test to find SIP information in chunks
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))

from simple_retrieval_pipeline import SimpleRetrievalPipeline

def test_sip_retrieval():
    print('=== TESTING SIP RETRIEVAL ===')
    
    try:
        # Initialize retrieval pipeline
        pipeline = SimpleRetrievalPipeline()
        print(f'Retrieval pipeline initialized with {pipeline.vector_manager.index.ntotal} vectors')
        
        # Search for SIP-related terms
        sip_queries = [
            "minimum sip",
            "sip", 
            "minimum investment",
            "5000",
            "investment"
        ]
        
        found_sip_data = False
        
        for query in sip_queries:
            print(f'\n--- Testing query: "{query}" ---')
            results = pipeline.keyword_search(query, k=5)
            
            if results:
                print(f'Found {len(results)} results:')
                
                for i, result in enumerate(results):
                    chunk_id = result.get('chunk_id', 'unknown')
                    section_type = result.get('section_type', 'unknown')
                    text = result.get('text', '')
                    score = result.get('score', 0)
                    
                    print(f'  Result {i+1}: {chunk_id} ({section_type}) - Score: {score}')
                    print(f'  Text: {text[:200]}...')
                    
                    # Check for SIP data specifically
                    text_lower = text.lower()
                    if any(sip_term in text_lower for sip_term in ["minimum sip", "sip", "minimum investment", "5000", "investment"]):
                        found_sip_data = True
                        print(f'    ✅ FOUND SIP DATA in chunk!')
                        
                        # Extract SIP amount if possible
                        sip_patterns = [
                            r'sip\s*[:\-]?\s*[\d,]+',
                            r'minimum\s+investment\s*[:\-]?\s*[\d,]+',
                            r'[\d,]+'
                        ]
                        
                        for pattern in sip_patterns:
                            match = re.search(pattern, text_lower)
                            if match:
                                sip_value = match.group()
                                print(f'    SIP Amount: {sip_value}')
                                break
        
        print(f'\n=== SIP RETRIEVAL RESULTS ===')
        print(f'SIP data found: {found_sip_data}')
        
        # Test with direct query for the actual SIP value
        print('\n--- TESTING DIRECT SIP QUERY ---')
        direct_results = pipeline.keyword_search('5000', k=3)
        
        if direct_results:
            print(f'Found {len(direct_results)} results for "5000":')
            for i, result in enumerate(direct_results):
                chunk_id = result.get('chunk_id', 'unknown')
                text = result.get('text', '')
                print(f'  Result {i+1}: {chunk_id}')
                print(f'  Text: {text[:150]}...')
        
        print('\n=== SIP RETRIEVAL TEST COMPLETED ===')
        return found_sip_data
        
    except Exception as e:
        print(f'ERROR: SIP retrieval test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sip_retrieval()
    if success:
        print('\n=== SUCCESS: SIP DATA IS RETRIEVABLE ===')
    else:
        print('\n=== FAILED: SIP DATA NOT RETRIEVABLE ===')
