#!/usr/bin/env python3
"""
Start the scheduler service as a background process
"""

import os
import sys
import time
import signal
import logging
from phase1.scheduler_service.scheduler_service import FundDataScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, stopping scheduler...")
    if scheduler:
        scheduler.stop()
    sys.exit(0)

def main():
    global scheduler
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Starting Fund Data Scheduler Service...")
        
        # Initialize scheduler
        scheduler = FundDataScheduler()
        
        # Start the scheduler
        scheduler.start()
        
        logger.info("Scheduler started successfully!")
        logger.info("Scheduled to run daily at 9:15 AM IST")
        
        # Get and display status
        status = scheduler.get_status()
        logger.info(f"Next run time: {status.get('next_run_time', 'Not scheduled')}")
        
        # Keep the process running
        while True:
            time.sleep(60)  # Check every minute
            status = scheduler.get_status()
            if not status.get('is_running', False):
                logger.error("Scheduler stopped unexpectedly!")
                break
                
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")
    finally:
        if scheduler:
            scheduler.stop()
        logger.info("Scheduler service stopped")

if __name__ == "__main__":
    main()
