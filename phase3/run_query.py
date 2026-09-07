#!/usr/bin/env python3
"""
Run a complete query through Phase 1 + Phase 2 + Phase 3 pipeline
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase1'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase2'))

from simple_retrieval_pipeline import SimpleRetrievalPipeline
import json

def run_query(query: str):
    print(f'=== RUNNING QUERY: "{query}" ===')
    
    try:
        # Initialize retrieval pipeline
        pipeline = SimpleRetrievalPipeline()
        print(f'Retrieval pipeline initialized with {pipeline.vector_manager.index.ntotal} vectors')
        
        # Retrieve relevant chunks
        results = pipeline.keyword_search(query, k=3)
        print(f'Found {len(results)} relevant chunks')
        
        if not results:
            return "I don't have that information in my current knowledge base. Please check the official ICICI Prudential factsheet or contact customer support."
        
        # Display retrieved context
        print('\n--- RETRIEVED CONTEXT ---')
        context_parts = []
        for i, result in enumerate(results):
            chunk_id = result.get('chunk_id', 'unknown')
            section_type = result.get('section_type', 'unknown')
            text = result.get('text', '')
            source_url = result.get('source_url', '')
            score = result.get('score', 0)
            
            context_parts.append(f"[Source: {source_url}]\n{text}")
            print(f'Chunk {i+1}: {chunk_id} ({section_type}) - Score: {score}')
            print(f'Text: {text[:200]}...')
            print()
        
        # Build context for answer generation
        context = "\n\n".join(context_parts)
        
        # Generate answer (mock since no LLM API keys)
        print('\n--- ANSWER GENERATION ---')
        
        # Look for NAV information in the retrieved chunks
        nav_info = ""
        for result in results:
            text = result.get('text', '').lower()
            if 'nav' in text or 'net asset value' in text:
                nav_info = result.get('text', '')
                break
        
        if nav_info:
            # Extract NAV value and date if present
            import re
            
            # Look for NAV values
            nav_pattern = r'nav\s*[:\-]?\s*[\d,.]+'
            nav_matches = re.findall(nav_pattern, nav_info.lower())
            
            # Look for dates
            date_pattern = r'\d{4}|\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}'
            date_matches = re.findall(date_pattern, nav_info)
            
            if nav_matches:
                nav_value = nav_matches[0].replace('nav', '').replace(':', '').replace('-', '').strip()
                date_str = date_matches[0] if date_matches else "recent data"
                
                answer = f"The NAV for ICICI Prudential Large Cap Fund Direct Growth is {nav_value} as of {date_str}. Source: {results[0].get('source_url', 'https://www.icicipruamc.com/factsheet')} Last updated: {date_str}"
            else:
                answer = f"NAV information for ICICI Prudential Large Cap Fund Direct Growth is available in the fund factsheet. Source: {results[0].get('source_url', 'https://www.icicipruamc.com/factsheet')} Please check the latest NAV on the official website."
        else:
            answer = "I don't have specific NAV information in my current knowledge base. Please check the official ICICI Prudential Large Cap Fund factsheet for the latest NAV. Source: https://www.icicipruamc.com/factsheet"
        
        print(f'Generated Answer: {answer}')
        return answer
        
    except Exception as e:
        print(f'Error running query: {str(e)}')
        return f"I encountered an error processing your query: {str(e)}"

if __name__ == "__main__":
    query = "what is the nav for large cap"
    answer = run_query(query)
    print(f'\n=== FINAL ANSWER ===')
    print(answer)
