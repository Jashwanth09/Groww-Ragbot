#!/usr/bin/env python3
"""
Manual data collection script
"""

from phase1.scheduler_service.scheduler_service import FundDataScheduler

def main():
    print("Running manual data collection...")
    scheduler = FundDataScheduler()
    result = scheduler.run_manual_collection()
    
    print(f"Status: {result['status']}")
    print(f"Schemes Processed: {result['schemes_processed']}")
    print(f"Schemes Failed: {result['schemes_failed']}")
    
    if result.get('data_file'):
        print(f"Data saved to: {result['data_file']}")
    
    if result.get('errors'):
        print("Errors:")
        for error in result['errors']:
            print(f"  - {error}")

if __name__ == "__main__":
    main()
