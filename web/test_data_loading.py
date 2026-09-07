"""
Test script to verify data loading and search functionality
"""

from pathlib import Path
import json

# Test loading fund data
raw_docs_path = Path('d:/M2/raw_documents')
fund_data = {}

if raw_docs_path.exists():
    for json_file in raw_docs_path.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'content' in data and data['content']:
                    for item in data['content']:
                        scheme = item.get('scheme', 'Unknown')
                        content_type = item.get('content_type', 'unknown')
                        text = item.get('text', '')
                        
                        if scheme not in fund_data:
                            fund_data[scheme] = {}
                        
                        fund_data[scheme][content_type] = text
        except Exception as e:
            print(f'Error loading {json_file}: {e}')

print(f'Loaded {len(fund_data)} schemes')
for scheme in fund_data.keys():
    print(f'  - {scheme}')
    print(f'    Content types: {list(fund_data[scheme].keys())}')

# Test search function
def search_fund_data(query, fund_data):
    query_lower = query.lower()
    results = []
    
    for scheme, data in fund_data.items():
        scheme_lower = scheme.lower()
        
        # Check if query matches scheme name
        if any(keyword in scheme_lower for keyword in query_lower.split()):
            # Return all content types for this scheme
            if 'kim' in data:
                results.append(f'**{scheme} - Key Information Memorandum:**\n\n{data["kim"]}')
            if 'factsheet' in data:
                results.append(f'**{scheme} - Factsheet:**\n\n{data["factsheet"]}')
            continue
        
        # Search within content text
        for content_type, text in data.items():
            if any(keyword in text.lower() for keyword in query_lower.split() if len(keyword) > 3):
                results.append(f'**{scheme} - {content_type.upper()}:**\n\n{text}')
    
    return results if results else None

# Test queries
test_queries = ['large cap', 'dynamic plan', 'nifty next', 'top 100']
for query in test_queries:
    print(f'\n--- Testing query: "{query}" ---')
    results = search_fund_data(query, fund_data)
    if results:
        print(f'Found {len(results)} results')
        for result in results[:1]:  # Show first result only
            print(result[:200] + '...')
    else:
        print('No results found')
