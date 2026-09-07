#!/usr/bin/env python3
"""
Test NAV retrieval with updated chunked documents
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'phase2'))

from simple_retrieval_pipeline import SimpleRetrievalPipeline

def test_nav_retrieval():
    print('=== TESTING NAV RETRIEVAL WITH UPDATED DATA ===')
    
    try:
        # Initialize retrieval pipeline
        pipeline = SimpleRetrievalPipeline()
        print(f'Retrieval pipeline initialized with {pipeline.vector_manager.index.ntotal} vectors')
        
        # Test specific NAV query
        query = "expense ratio"
        print(f'Query: "{query}"')
        
        # Retrieve relevant chunks
        results = pipeline.keyword_search(query, k=5)
        print(f'Found {len(results)} relevant chunks')
        
        if results:
            print('\n--- RETRIEVED CHUNKS ---')
            for i, result in enumerate(results):
                chunk_id = result.get('chunk_id', 'unknown')
                section_type = result.get('section_type', 'unknown')
                text = result.get('text', '')
                score = result.get('score', 0)
                
                print(f'Chunk {i+1}: {chunk_id} ({section_type}) - Score: {score}')
                print(f'Text: {text[:200]}...')
                
                # Check for expense ratio specifically
                if 'expense ratio' in text.lower():
                    import re
                    er_match = re.search(r'expense ratio\s*[:\-]?\s*[\d.]+%?', text.lower())
                    if er_match:
                        print(f'EXPENSE RATIO FOUND: {er_match.group()}')
                
                # Check for NAV
                if 'nav' in text.lower() or 'net asset value' in text.lower():
                    nav_match = re.search(r'nav\s*[:\-]?\s*[\d,.]+', text.lower())
                    if nav_match:
                        print(f'NAV FOUND: {nav_match.group()}')
        
        # Test direct NAV query
        nav_query = "nav"
        print(f'\n--- Testing Direct NAV Query: "{nav_query}" ---')
        nav_results = pipeline.keyword_search(nav_query, k=5)
        print(f'Found {len(nav_results)} relevant chunks')
        
        if nav_results:
            print('\n--- NAV RETRIEVAL RESULTS ---')
            for i, result in enumerate(nav_results):
                chunk_id = result.get('chunk_id', 'unknown')
                section_type = result.get('section_type', 'unknown')
                text = result.get('text', '')
                score = result.get('score', 0)
                
                print(f'Chunk {i+1}: {chunk_id} ({section_type}) - Score: {score}')
                print(f'Text: {text[:200]}...')
                
                # Check for NAV specifically
                if 'nav' in text.lower() or 'net asset value' in text.lower():
                    nav_match = re.search(r'nav\s*[:\-]?\s*[\d,.]+', text.lower())
                    if nav_match:
                        print(f'NAV FOUND: {nav_match.group()}')
        
        print('\n=== NAV RETRIEVAL TEST COMPLETED ===')
        return True
        
    except Exception as e:
        print(f'ERROR: NAV retrieval test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import re
    success = test_nav_retrieval()
    if success:
        print('\n=== SUCCESS: NAV DATA IS NOW RETRIEVABLE ===')
    else:
        print('\n=== FAILED: NAV RETRIEVAL STILL NOT WORKING ===')
