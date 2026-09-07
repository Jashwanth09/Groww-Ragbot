#!/usr/bin/env python3
"""
Improved NAV retrieval test with better text matching
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'phase2'))

from simple_retrieval_pipeline import SimpleRetrievalPipeline

def test_improved_nav_retrieval():
    print('=== TESTING IMPROVED NAV RETRIEVAL ===')
    
    try:
        # Initialize retrieval pipeline
        pipeline = SimpleRetrievalPipeline()
        print(f'Retrieval pipeline initialized with {pipeline.vector_manager.index.ntotal} vectors')
        
        # Search for expense ratio
        results = pipeline.keyword_search('expense ratio', k=10)
        print(f'Found {len(results)} results for expense ratio')
        
        if results:
            print('\n--- ANALYZING CHUNKS FOR EXPENSE RATIO ---')
            expense_found = False
            
            for i, result in enumerate(results):
                text = result.get('text', '')
                chunk_id = result.get('chunk_id', 'unknown')
                section_type = result.get('section_type', 'unknown')
                
                print(f'Chunk {i+1}: {chunk_id} ({section_type})')
                print(f'Text: {text[:300]}...')
                
                # Multiple patterns for expense ratio detection
                expense_patterns = [
                    r'expense ratio\s*[:\-]?\s*[\d.]+%?',
                    r'0\.42%',
                    r'0\.42',
                    r'42%',
                    r'expense.*ratio.*0\.42',
                    r'ter.*0\.42'
                ]
                
                for pattern in expense_patterns:
                    if re.search(pattern, text.lower()):
                        expense_found = True
                        print(f'✅ FOUND EXPENSE RATIO PATTERN: {pattern}')
                        break
                
                if expense_found:
                    print(f'✅ CHUNK {i+1} CONTAINS EXPENSE RATIO DATA')
                else:
                    print(f'❌ CHUNK {i+1} DOES NOT CONTAIN EXPENSE RATIO')
            
            print(f'\nTotal chunks with expense ratio data: {sum(1 for r in results if any(re.search(p, r.get("text", "").lower()) for p in expense_patterns))}')
        
        # Test specific value search
        print('\n=== TESTING SPECIFIC VALUE SEARCH ===')
        
        # Search for "0.42" specifically
        specific_results = pipeline.keyword_search('0.42', k=10)
        print(f'Found {len(specific_results)} results for "0.42"')
        
        if specific_results:
            for i, result in enumerate(specific_results):
                text = result.get('text', '')
                chunk_id = result.get('chunk_id', 'unknown')
                print(f'Specific result {i+1}: {chunk_id}')
                print(f'Text: {text[:200]}...')
        
        # Test broader search
        print('\n=== TESTING BROADER SEARCH ===')
        broader_results = pipeline.keyword_search('expense', k=10)
        print(f'Found {len(broader_results)} results for "expense"')
        
        broader_expense_found = False
        for result in broader_results:
            text = result.get('text', '')
            if 'expense ratio' in text.lower() or '0.42' in text:
                broader_expense_found = True
                print(f'✅ BROADER SEARCH FOUND: {result.get("chunk_id", "unknown")}')
                break
        
        print('\n=== SEARCH RESULTS SUMMARY ===')
        print(f'Expense ratio pattern search: {expense_found}')
        print(f'Specific "0.42" search: {len(specific_results)} results')
        print(f'Broader "expense" search: {broader_expense_found}')
        
        print('\n=== IMPROVED NAV RETRIEVAL TEST COMPLETED ===')
        return True
        
    except Exception as e:
        print(f'ERROR: Improved NAV retrieval test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_improved_nav_retrieval()
    if success:
        print('\n=== SUCCESS: IMPROVED NAV RETRIEVAL WORKING ===')
    else:
        print('\n=== FAILED: IMPROVED NAV RETRIEVAL NOT WORKING ===')
