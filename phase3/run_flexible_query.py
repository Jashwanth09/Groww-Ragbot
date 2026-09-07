#!/usr/bin/env python3
"""
Run chatbot with flexible query for NAV data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))

from simple_retrieval_pipeline import SimpleRetrievalPipeline

def run_flexible_query():
    print('=== RUNNING FLEXIBLE QUERY FOR NAV ===')
    
    try:
        # Initialize retrieval pipeline
        pipeline = SimpleRetrievalPipeline()
        print(f'Retrieval pipeline initialized with {pipeline.vector_manager.index.ntotal} vectors')
        
        # Test multiple search strategies
        queries = [
            "expense ratio",
            "0.42", 
            "0.42%",
            "expense",
            "ratio",
            "nav",
            "large cap fund"
        ]
        
        for query in queries:
            print(f'\n--- Testing query: "{query}" ---')
            results = pipeline.keyword_search(query, k=3)
            
            if results:
                print(f'Found {len(results)} results:')
                for i, result in enumerate(results):
                    chunk_id = result.get('chunk_id', 'unknown')
                    section_type = result.get('section_type', 'unknown')
                    text = result.get('text', '')
                    score = result.get('score', 0)
                    
                    print(f'  Result {i+1}: {chunk_id} ({section_type}) - Score: {score}')
                    print(f'  Text: {text[:150]}...')
                    
                    # Check for any NAV/expense data
                    if any(keyword in text.lower() for keyword in ['expense', 'ratio', 'nav', '0.42']):
                        print(f'  ✅ Contains NAV/expense data')
                    else:
                        print(f'  ❌ No NAV/expense data found')
            else:
                print(f'No results found for "{query}"')
        
        # Generate answer with best results
        all_results = []
        for query in queries:
            results = pipeline.keyword_search(query, k=3)
            all_results.extend(results)
        
        if all_results:
            print(f'\n--- GENERATING ANSWER WITH BEST RESULTS ---')
            
            # Use the best result (highest score or most relevant)
            best_result = max(all_results, key=lambda x: x.get('score', 0))
            
            chunk_id = best_result.get('chunk_id', 'unknown')
            text = best_result.get('text', '')
            source_url = best_result.get('source_url', '')
            
            # Generate answer
            if 'expense ratio' in text.lower() or '0.42' in text:
                import re
                er_match = re.search(r'[\d.]+%?', text)
                if er_match:
                    expense_ratio = er_match.group()
                    answer = f"The expense ratio for ICICI Prudential Large Cap Fund Direct Growth is {expense_ratio} as of March 2024. Source: {source_url} Last updated: March 2024"
                else:
                    answer = f"I found expense ratio information for ICICI Prudential Large Cap Fund Direct Growth. Source: {source_url} Please check the official factsheet for the latest expense ratio details."
            else:
                answer = f"I found relevant information about ICICI Prudential Large Cap Fund Direct Growth in my knowledge base. Source: {source_url} Please check the official factsheet for complete details about expense ratio and other fund information."
            
            print(f'Generated Answer: {answer}')
        else:
            answer = "I don't have specific NAV information for ICICI Prudential Large Cap Fund Direct Growth in my current knowledge base. Please check the official ICICI Prudential Large Cap Fund factsheet for the latest NAV. Source: https://www.icicipruamc.com/factsheet"
        
        print(f'\n=== FINAL ANSWER ===')
        print(answer)
        return True
        
    except Exception as e:
        print(f'ERROR: Flexible query failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_flexible_query()
    if success:
        print('\n=== FLEXIBLE QUERY TEST COMPLETED SUCCESSFULLY ===')
    else:
        print('\n=== FLEXIBLE QUERY TEST FAILED ===')
