"""
Test script to verify metrics data loading and search functionality
"""

from pathlib import Path
import json

# Test loading metrics data
data_storage_path = Path('d:/M2/data_storage_example.json')
metrics_data = {}

try:
    if data_storage_path.exists():
        with open(data_storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'schemes' in data:
                for scheme_data in data['schemes']:
                    scheme_name = scheme_data.get('scheme_identifier', {}).get('name', 'Unknown')
                    metrics_data[scheme_name] = scheme_data
except Exception as e:
    print(f'Error loading metrics data: {e}')

print(f'Loaded {len(metrics_data)} schemes with metrics data')
for scheme_name in metrics_data.keys():
    print(f'  - {scheme_name}')
    metrics = metrics_data[scheme_name].get('key_metrics', {})
    print(f'    NAV: {metrics.get("nav", {}).get("value", "N/A")}')
    print(f'    Minimum SIP: {metrics.get("minimum_sip", "N/A")}')
    print(f'    Fund Size: {metrics.get("fund_size", {}).get("value", "N/A")} {metrics.get("fund_size", {}).get("unit", "")}')
    print(f'    Rating: {metrics.get("rating", "N/A")}')

# Test search function
def search_metrics_data(query, metrics_data):
    """Search metrics data (SIP, NAV, fund size, rating) based on user query"""
    query_lower = query.lower()
    results = []
    
    # Check which specific metric is being requested
    requested_metric = None
    if "nav" in query_lower:
        requested_metric = "nav"
    elif "sip" in query_lower:
        requested_metric = "sip"
    elif "fund size" in query_lower:
        requested_metric = "fund_size"
    elif "size" in query_lower:
        requested_metric = "fund_size"
    elif "rating" in query_lower:
        requested_metric = "rating"
    elif "expense" in query_lower:
        requested_metric = "expense_ratio"
    
    for scheme_name, scheme_data in metrics_data.items():
        scheme_lower = scheme_name.lower()
        
        # Check if query matches scheme name
        if any(keyword in scheme_lower for keyword in query_lower.split()):
            metrics = scheme_data.get('key_metrics', {})
            
            # Only return the requested metric
            if requested_metric == "nav":
                nav_data = metrics.get('nav', {})
                nav_value = nav_data.get('value', 'N/A')
                nav_date = nav_data.get('date', 'N/A')
                result = f"**{scheme_name} - NAV:** ₹{nav_value} (as of {nav_date})"
                results.append(result)
            elif requested_metric == "sip":
                min_sip = metrics.get('minimum_sip', 'N/A')
                result = f"**{scheme_name} - Minimum SIP:** ₹{min_sip}"
                results.append(result)
            elif requested_metric == "fund_size":
                fund_size_data = metrics.get('fund_size', {})
                fund_size_value = fund_size_data.get('value', 'N/A')
                fund_size_unit = fund_size_data.get('unit', '')
                result = f"**{scheme_name} - Fund Size:** ₹{fund_size_value} {fund_size_unit}"
                results.append(result)
            elif requested_metric == "rating":
                rating = metrics.get('rating', 'N/A')
                result = f"**{scheme_name} - Risk Rating:** {rating}"
                results.append(result)
            elif requested_metric == "expense_ratio":
                expense_ratio = metrics.get('expense_ratio', 'N/A')
                result = f"**{scheme_name} - Expense Ratio:** {expense_ratio}%"
                results.append(result)
            else:
                # If no specific metric requested, show all metrics
                nav_data = metrics.get('nav', {})
                nav_value = nav_data.get('value', 'N/A')
                nav_date = nav_data.get('date', 'N/A')
                
                fund_size_data = metrics.get('fund_size', {})
                fund_size_value = fund_size_data.get('value', 'N/A')
                fund_size_unit = fund_size_data.get('unit', '')
                
                min_sip = metrics.get('minimum_sip', 'N/A')
                expense_ratio = metrics.get('expense_ratio', 'N/A')
                rating = metrics.get('rating', 'N/A')
                
                result = f"""
**{scheme_name} - Key Metrics:**

• **NAV:** ₹{nav_value} (as of {nav_date})
• **Minimum SIP:** ₹{min_sip}
• **Fund Size:** ₹{fund_size_value} {fund_size_unit}
• **Expense Ratio:** {expense_ratio}%
• **Risk Rating:** {rating}
"""
                results.append(result)
    
    return results if results else None

# Test queries
test_queries = ['multi asset nav', 'multi asset sip', 'multi asset fund size', 'multi asset rating', 'multi asset']
for query in test_queries:
    print(f'\n--- Testing query: "{query}" ---')
    results = search_metrics_data(query, metrics_data)
    if results:
        print(f'Found {len(results)} results')
        for result in results:
            print(result)
    else:
        print('No results found')
