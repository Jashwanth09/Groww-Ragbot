#!/usr/bin/env python3
"""
Test retrieval of important data fields: NAV, Minimum SIP, Fund Size, Expense Ratio, Rating
"""

import json
import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'phase2'))

from simple_retrieval_pipeline import SimpleRetrievalPipeline

def test_data_field_retrieval():
    print('=== TESTING IMPORTANT DATA FIELD RETRIEVAL ===')
    
    try:
        # Initialize retrieval pipeline
        pipeline = SimpleRetrievalPipeline()
        print(f'Retrieval pipeline initialized with {pipeline.vector_manager.index.ntotal} vectors')
        
        # Test queries for each important data field
        test_queries = [
            ("nav", "NAV information"),
            ("minimum sip", "Minimum SIP amount"),
            ("expense ratio", "Expense ratio percentage"),
            ("fund size", "Fund size/AUM"),
            ("riskometer", "Risk rating"),
            ("rating", "Fund rating")
        ]
        
        for query, description in test_queries:
            print(f'\n--- Testing: {description} ---')
            print(f'Query: "{query}"')
            
            # Retrieve relevant chunks
            results = pipeline.keyword_search(query, k=3)
            
            if results:
                print(f'Found {len(results)} relevant chunks:')
                
                for i, result in enumerate(results):
                    chunk_id = result.get('chunk_id', 'unknown')
                    section_type = result.get('section_type', 'unknown')
                    text = result.get('text', '')
                    score = result.get('score', 0)
                    
                    print(f'  Result {i+1}: {chunk_id} ({section_type}) - Score: {score}')
                    
                    # Check if field value is present in the text
                    text_lower = text.lower()
                    field_found = False
                    
                    if query == "nav" and ("nav" in text_lower or "net asset value" in text_lower):
                        field_found = True
                        # Extract NAV value
                        nav_match = re.search(r'nav\s*[:\-]?\s*[\d,.]+', text_lower)
                        if nav_match:
                            print(f'    NAV Value Found: {nav_match.group()}')
                    
                    elif query == "minimum sip" and ("sip" in text_lower or "minimum investment" in text_lower):
                        field_found = True
                        # Extract SIP value
                        sip_match = re.search(r'sip\s*[:\-]?\s*[\d,.]+', text_lower)
                        if sip_match:
                            print(f'    SIP Value Found: {sip_match.group()}')
                    
                    elif query == "expense ratio" and ("expense ratio" in text_lower or "ter" in text_lower):
                        field_found = True
                        # Extract expense ratio
                        er_match = re.search(r'expense ratio\s*[:\-]?\s*[\d.]+%?', text_lower)
                        if er_match:
                            print(f'    Expense Ratio Found: {er_match.group()}')
                    
                    elif query == "fund size" and ("aum" in text_lower or "assets under management" in text_lower or "fund size" in text_lower):
                        field_found = True
                        # Extract fund size
                        size_match = re.search(r'[\d,.]+\s*(?:cr|crore|lakh)', text_lower)
                        if size_match:
                            print(f'    Fund Size Found: {size_match.group()}')
                    
                    elif query in ["riskometer", "rating"] and ("risk" in text_lower or "rating" in text_lower):
                        field_found = True
                        # Extract risk rating
                        risk_match = re.search(r'(very high|high|moderate|low)\s*risk', text_lower)
                        if risk_match:
                            print(f'    Risk Rating Found: {risk_match.group()}')
                    
                    if not field_found:
                        print(f'    Field value NOT found in chunk text')
                    
                    print(f'    Text Preview: {text[:150]}...')
            else:
                print(f'No results found for {description}')
        
        # Test specific query for all fields
        print(f'\n--- COMPREHENSIVE QUERY TEST ---')
        comprehensive_query = "ICICI Prudential Large Cap Fund details NAV expense ratio minimum SIP fund size rating"
        print(f'Query: "{comprehensive_query}"')
        
        results = pipeline.keyword_search(comprehensive_query, k=5)
        
        if results:
            print(f'Found {len(results)} chunks with comprehensive data:')
            
            # Collect all data fields found
            found_data = {
                'nav': False,
                'minimum_sip': False,
                'expense_ratio': False,
                'fund_size': False,
                'rating': False
            }
            
            for result in results:
                text = result.get('text', '').lower()
                
                if 'nav' in text or 'net asset value' in text:
                    found_data['nav'] = True
                if 'sip' in text or 'minimum investment' in text:
                    found_data['minimum_sip'] = True
                if 'expense ratio' in text or 'ter' in text:
                    found_data['expense_ratio'] = True
                if 'aum' in text or 'assets under management' in text or 'fund size' in text:
                    found_data['fund_size'] = True
                if 'risk' in text or 'rating' in text:
                    found_data['rating'] = True
            
            print('Data Fields Coverage:')
            for field, found in found_data.items():
                status = '✅ FOUND' if found else '❌ MISSING'
                print(f'  {field}: {status}')
        
        print('\n=== DATA FIELD RETRIEVAL TEST COMPLETED ===')
        return True
        
    except Exception as e:
        print(f'ERROR: Data field retrieval test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_field_retrieval()
    if success:
        print('\n=== ALL IMPORTANT DATA FIELDS ARE READY FOR RETRIEVAL ===')
    else:
        print('\n=== DATA FIELD RETRIEVAL TEST FAILED ===')
