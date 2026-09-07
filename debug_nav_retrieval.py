#!/usr/bin/env python3
"""
Debug NAV retrieval to find actual NAV values
"""

import sys
import os
import json
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'phase2'))

from simple_retrieval_pipeline import SimpleRetrievalPipeline

def debug_nav_retrieval():
    print('=== DEBUGGING NAV RETRIEVAL ===')
    
    try:
        # Load chunked documents to see what we actually have
        with open('../processed_data/chunked_documents.json', 'r') as f:
            chunked_data = json.load(f)
        
        print(f'Total chunks available: {len(chunked_data.get("chunks", []))}')
        
        # Search for NAV-related chunks
        nav_chunks = []
        expense_chunks = []
        
        for chunk in chunked_data.get("chunks", []):
            text = chunk.get('text', '').lower()
            
            if 'nav' in text or 'net asset value' in text:
                nav_chunks.append(chunk)
                print(f'NAV Chunk Found: {chunk["chunk_id"]}')
                print(f'Text: {text[:200]}...')
                
            if 'expense ratio' in text:
                expense_chunks.append(chunk)
                print(f'Expense Ratio Chunk Found: {chunk["chunk_id"]}')
                print(f'Text: {text[:200]}...')
        
        print(f'\nTotal NAV chunks: {len(nav_chunks)}')
        print(f'Total Expense Ratio chunks: {len(expense_chunks)}')
        
        # Test direct search for expense ratio
        pipeline = SimpleRetrievalPipeline()
        
        print('\n=== TESTING RETRIEVAL PIPELINE ===')
        
        # Test 1: Search for "expense ratio"
        results1 = pipeline.keyword_search("expense ratio", k=10)
        print(f'Query "expense ratio": Found {len(results1)} results')
        
        # Test 2: Search for "0.42" (specific value)
        results2 = pipeline.keyword_search("0.42", k=10)
        print(f'Query "0.42": Found {len(results2)} results')
        
        # Test 3: Search for "expense" 
        results3 = pipeline.keyword_search("expense", k=10)
        print(f'Query "expense": Found {len(results3)} results')
        
        # Check if any expense ratio chunks are actually retrieved
        expense_found = False
        for result in results1:
            text = result.get('text', '').lower()
            if 'expense ratio' in text and '0.42' in text:
                expense_found = True
                print(f'FOUND EXPENSE RATIO CHUNK: {result["chunk_id"]}')
                print(f'Text: {text[:300]}')
                break
        
        if not expense_found:
            print('ERROR: No expense ratio chunks with actual values found!')
            print('Available chunks contain:')
            for i, chunk in enumerate(expense_chunks[:3]):
                print(f'  {i+1}. {chunk["chunk_id"]}: {chunk.get("text", "")[:100]}...')
        
        print('\n=== DEBUG COMPLETE ===')
        return expense_found
        
    except Exception as e:
        print(f'ERROR: Debug failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_nav_retrieval()
    if success:
        print('\n=== SUCCESS: FOUND ACTUAL EXPENSE RATIO DATA ===')
    else:
        print('\n=== FAILED: NO EXPENSE RATIO DATA FOUND ===')
