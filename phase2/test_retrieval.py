#!/usr/bin/env python3
"""
Test script for Phase 2.3 Retrieval Pipeline
"""

from simple_retrieval_pipeline import SimpleRetrievalPipeline
import json

def test_retrieval_pipeline():
    print('=== PHASE 2.3 TEST: Retrieval Pipeline Functionality ===')
    
    try:
        # Initialize the retrieval pipeline
        pipeline = SimpleRetrievalPipeline()
        print(f'SUCCESS: Retrieval pipeline initialized')
        
        # Test semantic search with a relevant query
        test_query = 'expense ratio'
        print(f'Testing query: "{test_query}"')
        
        # Use the keyword search (now chunked_documents.json is in current directory)
        results = pipeline.keyword_search(test_query, k=3)
        
        if results:
            print(f'SUCCESS: Found {len(results)} results')
            for i, result in enumerate(results):
                chunk_id = result.get('chunk_id', 'unknown')
                section_type = result.get('section_type', 'unknown')
                score = result.get('score', 0)
                text_preview = result.get('text', '')[:100]
                
                print(f'Result {i+1}:')
                print(f'  Chunk ID: {chunk_id}')
                print(f'  Section: {section_type}')
                print(f'  Score: {score:.4f}')
                print(f'  Preview: {text_preview}...')
                print()
            
            print('=== PHASE 2.3 TEST PASSED ===')
            return True
        else:
            print('WARNING: No results found for query')
            return False
            
    except Exception as e:
        print(f'ERROR: Retrieval pipeline failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_retrieval_pipeline()
