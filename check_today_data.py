import json

def check_today_data():
    """Check today's scraped data for NAV values"""
    
    data_file = 'd:/M2/raw_data/fund_data_20260505_233611.json'
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Total schemes collected: {len(data.get('schemes', []))}")
        print("\n=== TODAY'S FUND DATA ===")
        
        for scheme in data.get('schemes', []):
            fund_name = scheme.get('scheme_identifier', {}).get('name', 'Unknown')
            key_metrics = scheme.get('key_metrics', {})
            nav_data = key_metrics.get('nav', {})
            
            nav_value = nav_data.get('value', 'N/A')
            nav_date = nav_data.get('date', 'N/A')
            
            print(f"\nFund: {fund_name}")
            print(f"NAV: ₹{nav_value} (as of {nav_date})")
            
            # Also check other metrics
            sip = key_metrics.get('minimum_sip', 'N/A')
            fund_size = key_metrics.get('fund_size', {})
            expense_ratio = key_metrics.get('expense_ratio', 'N/A')
            
            print(f"SIP: ₹{sip}")
            print(f"Fund Size: {fund_size.get('value', 'N/A')} {fund_size.get('unit', '')}")
            print(f"Expense Ratio: {expense_ratio}%")
        
        return data
        
    except Exception as e:
        print(f"Error reading data: {e}")
        return None

if __name__ == "__main__":
    check_today_data()
