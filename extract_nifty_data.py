#!/usr/bin/env python3
"""
Extract correct Nifty Next 50 data from multiple sources
"""

import json
import re

def extract_from_raw_documents():
    """Extract data from raw_documents JSON files"""
    try:
        # Check factsheet
        with open('raw_documents/nifty_next_50_index_fund_factsheet.json', 'r') as f:
            factsheet_data = json.load(f)
        
        factsheet_text = factsheet_data['content'][0]['text']
        print("=== From Factsheet ===")
        print(factsheet_text)
        
        # Extract metrics from factsheet
        nav_match = re.search(r'NAV[:\s-]*₹?([\d.]+)', factsheet_text, re.IGNORECASE)
        sip_match = re.search(r'Minimum Investment.*?SIP.*?₹?([\d,]+)', factsheet_text, re.IGNORECASE)
        size_match = re.search(r'Assets Under Management.*?₹?([\d,.]+)\s*([A-Za-z]+)', factsheet_text, re.IGNORECASE)
        expense_match = re.search(r'Expense Ratio[:\s-]*([\d.]+)%', factsheet_text, re.IGNORECASE)
        
        print("\n=== Extracted from Factsheet ===")
        print(f"NAV: ₹{nav_match.group(1) if nav_match else 'N/A'}")
        print(f"SIP: ₹{sip_match.group(1) if sip_match else 'N/A'}")
        print(f"Fund Size: ₹{size_match.group(1) if size_match else 'N/A'} {size_match.group(2) if size_match else ''}")
        print(f"Expense Ratio: {expense_match.group(1) if expense_match else 'N/A'}%")
        
    except Exception as e:
        print(f"Error: {e}")

def extract_from_scraped_data():
    """Extract from latest scraped data"""
    try:
        with open('raw_data/fund_data_20260428_142719.json', 'r') as f:
            data = json.load(f)
        
        for scheme in data['schemes']:
            if 'Nifty Next 50' in scheme['scheme_identifier']['name']:
                print("\n=== From Scraped Data ===")
                metrics = scheme.get('key_metrics', {})
                
                nav_data = metrics.get('nav', {})
                print(f"NAV: {nav_data}")
                
                sip = metrics.get('minimum_sip', 'N/A')
                print(f"Minimum SIP: {sip}")
                
                fund_size = metrics.get('fund_size', {})
                print(f"Fund Size: {fund_size}")
                
                expense = metrics.get('expense_ratio', 'N/A')
                print(f"Expense Ratio: {expense}%")
                
                rating = metrics.get('rating', 'N/A')
                print(f"Rating: {rating}")
                break
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_from_raw_documents()
    extract_from_scraped_data()
