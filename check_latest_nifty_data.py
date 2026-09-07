#!/usr/bin/env python3
"""
Check latest Nifty Next 50 data
"""

import json

def check_latest_nifty_data():
    try:
        with open('raw_data/fund_data_20260428_142719.json', 'r') as f:
            data = json.load(f)
        
        for scheme in data['schemes']:
            if 'Nifty Next 50' in scheme['scheme_identifier']['name']:
                print(f"Fund: {scheme['scheme_identifier']['name']}")
                print(f"Category: {scheme['scheme_identifier']['category']}")
                print(f"Risk Level: {scheme['scheme_identifier']['risk_level']}")
                
                metrics = scheme.get('key_metrics', {})
                print(f"NAV: {metrics.get('nav', 'N/A')}")
                print(f"Minimum SIP: {metrics.get('minimum_sip', 'N/A')}")
                print(f"Fund Size: {metrics.get('fund_size', 'N/A')}")
                print(f"Expense Ratio: {metrics.get('expense_ratio', 'N/A')}")
                print(f"Rating: {metrics.get('rating', 'N/A')}")
                
                print(f"Data Quality: {scheme.get('data_quality', {})}")
                break
        else:
            print("Nifty Next 50 fund not found in scraped data")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_latest_nifty_data()
