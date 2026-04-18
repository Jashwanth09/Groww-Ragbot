"""
Phase 1.1.4: Automated Scheduler Service
Schedules daily data collection at 9:15 AM for latest fund information
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
import logging
import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import scraping service
try:
    from scraping_service.scraping_service import GrowwScraper
except ImportError:
    print("Warning: Could not import scraping_service. Make sure it's in the correct path.")
    GrowwScraper = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/scheduler_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FundDataScheduler:
    """Scheduler for automated fund data collection"""
    
    def __init__(self, config_path: str = '../config/scheduler_config.json'):
        """
        Initialize the scheduler
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.scheduler = None
        self.urls = self.config.get('urls', [])
        self.email_config = self.config.get('email', {})
        self.retry_config = self.config.get('retry', {})
        self.is_running = False
        
        # Default URLs if not in config
        if not self.urls:
            self.urls = [
                "https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth",
                "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
                "https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth",
                "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
            ]
        
        self._setup_scheduler()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load scheduler configuration"""
        default_config = {
            "schedule": {
                "hour": 9,
                "minute": 15,
                "timezone": "Asia/Kolkata"
            },
            "urls": [],
            "retry": {
                "max_attempts": 3,
                "backoff_factor": 2,
                "delay": 60
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_emails": []
            },
            "monitoring": {
                "health_check_interval": 3600,
                "max_consecutive_failures": 3
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                default_config.update(config)
                logger.info(f"Configuration loaded from {config_path}")
            else:
                # Create default config file
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default config at {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
        
        return default_config
    
    def _setup_scheduler(self):
        """Setup APScheduler with event listeners"""
        try:
            self.scheduler = BackgroundScheduler()
            
            # Add event listeners
            self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
            self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
            
            logger.info("Scheduler setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup scheduler: {str(e)}")
            raise
    
    def _job_executed(self, event):
        """Handle successful job execution"""
        logger.info(f"Job {event.job_id} executed successfully")
        self._log_job_result(event.job_id, "success", event.retval)
    
    def _job_error(self, event):
        """Handle job execution error"""
        logger.error(f"Job {event.job_id} failed: {str(event.exception)}")
        self._log_job_result(event.job_id, "error", str(event.exception))
        self._handle_job_failure(event.job_id, str(event.exception))
    
    def _job_missed(self, event):
        """Handle missed job execution"""
        logger.warning(f"Job {event.job_id} was missed")
        self._log_job_result(event.job_id, "missed", "Job execution was missed")
    
    def _log_job_result(self, job_id: str, status: str, result: Any):
        """Log job execution result"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "job_id": job_id,
            "status": status,
            "result": str(result) if result else None
        }
        
        try:
            log_file = '../logs/job_execution.log'
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to log job result: {str(e)}")
    
    def _handle_job_failure(self, job_id: str, error: str):
        """Handle job failure with alerting"""
        consecutive_failures = self._get_consecutive_failures(job_id)
        
        max_failures = self.config['monitoring']['max_consecutive_failures']
        
        if consecutive_failures >= max_failures:
            logger.critical(f"Job {job_id} failed {consecutive_failures} times consecutively")
            self._send_failure_alert(job_id, error, consecutive_failures)
    
    def _get_consecutive_failures(self, job_id: str) -> int:
        """Get count of consecutive failures for a job"""
        try:
            log_file = '../logs/job_execution.log'
            if not os.path.exists(log_file):
                return 0
            
            consecutive_failures = 0
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Read lines in reverse order
            for line in reversed(lines[-100:]):  # Check last 100 entries
                try:
                    entry = json.loads(line.strip())
                    if entry['job_id'] == job_id:
                        if entry['status'] == 'error':
                            consecutive_failures += 1
                        else:
                            break  # Reset on success
                except json.JSONDecodeError:
                    continue
            
            return consecutive_failures
            
        except Exception as e:
            logger.error(f"Failed to get consecutive failures: {str(e)}")
            return 0
    
    def setup_daily_job(self):
        """Setup daily job for fund data collection"""
        try:
            schedule_config = self.config['schedule']
            
            # Schedule daily job at specified time
            self.scheduler.add_job(
                func=self.daily_data_collection,
                trigger=CronTrigger(
                    hour=schedule_config['hour'],
                    minute=schedule_config['minute'],
                    timezone=schedule_config['timezone']
                ),
                id='daily_fund_data_update',
                name='Daily ICICI Prudential Fund Data Update',
                replace_existing=True,
                max_instances=1,  # Prevent overlapping jobs
                misfire_grace_time=300  # 5 minutes grace period
            )
            
            next_run = self.scheduler.get_job('daily_fund_data_update').next_run_time
            logger.info(f"Daily job scheduled. Next run: {next_run}")
            
        except Exception as e:
            logger.error(f"Failed to setup daily job: {str(e)}")
            raise
    
    def daily_data_collection(self):
        """Main function called by scheduler for daily data collection"""
        logger.info("Starting daily fund data collection")
        
        if not GrowwScraper:
            logger.error("GrowwScraper not available. Cannot proceed with data collection.")
            return {"status": "error", "message": "GrowwScraper not available"}
        
        scraper = None
        collection_result = {
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "schemes_processed": 0,
            "schemes_failed": 0,
            "failed_urls": [],
            "errors": []
        }
        
        try:
            # Initialize scraper
            scraper = GrowwScraper(headless=True)
            
            # Scrape all schemes with retry logic
            all_data, failed_urls = self._scrape_with_retry(scraper, self.urls)
            
            collection_result["schemes_processed"] = len(all_data)
            collection_result["schemes_failed"] = len(failed_urls)
            collection_result["failed_urls"] = failed_urls
            
            # Save collected data
            if all_data:
                try:
                    filepath = scraper.save_scraped_data(all_data)
                    collection_result["data_file"] = filepath
                    logger.info(f"Data saved to: {filepath}")
                    
                    # Trigger reprocessing pipeline (placeholder)
                    self._trigger_reprocessing_pipeline(filepath)
                    
                except Exception as e:
                    collection_result["errors"].append(f"Failed to save data: {str(e)}")
                    logger.error(f"Failed to save data: {str(e)}")
            
            # Determine final status
            if len(failed_urls) == 0:
                collection_result["status"] = "success"
            elif len(all_data) > 0:
                collection_result["status"] = "partial_success"
            else:
                collection_result["status"] = "failed"
            
            logger.info(f"Data collection completed. Success: {len(all_data)}, Failed: {len(failed_urls)}")
            
        except Exception as e:
            collection_result["status"] = "error"
            collection_result["errors"].append(str(e))
            logger.error(f"Data collection failed: {str(e)}")
        
        finally:
            if scraper:
                scraper.cleanup()
        
        # Log collection result
        self._log_collection_result(collection_result)
        
        return collection_result
    
    def _scrape_with_retry(self, scraper: GrowwScraper, urls: List[str]) -> tuple:
        """Scrape URLs with retry logic"""
        max_attempts = self.retry_config['max_attempts']
        backoff_factor = self.retry_config['backoff_factor']
        delay = self.retry_config['delay']
        
        all_data = []
        failed_urls = []
        
        for url in urls:
            attempt = 0
            while attempt < max_attempts:
                try:
                    logger.info(f"Scraping {url} (attempt {attempt + 1}/{max_attempts})")
                    data = scraper.scrape_scheme_page(url, max_retries=1)  # Single retry per attempt
                    
                    if data:
                        all_data.append(data)
                        logger.info(f"Successfully scraped: {url}")
                        break
                    else:
                        attempt += 1
                        if attempt < max_attempts:
                            wait_time = delay * (backoff_factor ** (attempt - 1))
                            logger.warning(f"Failed to scrape {url}, retrying in {wait_time}s...")
                            time.sleep(wait_time)
                        
                except Exception as e:
                    logger.error(f"Exception scraping {url}: {str(e)}")
                    attempt += 1
                    if attempt < max_attempts:
                        wait_time = delay * (backoff_factor ** (attempt - 1))
                        time.sleep(wait_time)
            
            if attempt >= max_attempts:
                failed_urls.append(url)
                logger.error(f"Failed to scrape {url} after {max_attempts} attempts")
        
        return all_data, failed_urls
    
    def _trigger_reprocessing_pipeline(self, data_file: str):
        """Trigger the chunking and embedding pipeline"""
        try:
            logger.info(f"Triggering reprocessing pipeline for {data_file}")
            
            # This is a placeholder for the actual pipeline trigger
            # In the full implementation, this would:
            # 1. Call the chunking pipeline
            # 2. Generate embeddings
            # 3. Update vector database
            
            # For now, just log that pipeline was triggered
            pipeline_log = {
                "timestamp": datetime.now().isoformat(),
                "data_file": data_file,
                "pipeline_status": "triggered",
                "pipeline_type": "chunking_embedding"
            }
            
            with open('../logs/pipeline_trigger.log', 'a') as f:
                f.write(json.dumps(pipeline_log) + '\n')
            
            logger.info("Reprocessing pipeline triggered successfully")
            
        except Exception as e:
            logger.error(f"Failed to trigger reprocessing pipeline: {str(e)}")
    
    def _log_collection_result(self, result: Dict):
        """Log collection result"""
        try:
            log_file = '../logs/collection_results.log'
            with open(log_file, 'a') as f:
                f.write(json.dumps(result) + '\n')
        except Exception as e:
            logger.error(f"Failed to log collection result: {str(e)}")
    
    def _send_failure_alert(self, job_id: str, error: str, consecutive_failures: int):
        """Send failure alert via email"""
        if not self.email_config.get('enabled', False):
            logger.warning("Email alerts not enabled")
            return
        
        try:
            subject = f"ALERT: Job {job_id} Failed {consecutive_failures} Times"
            body = f"""
            Job Failure Alert
            
            Job ID: {job_id}
            Consecutive Failures: {consecutive_failures}
            Error: {error}
            Timestamp: {datetime.now().isoformat()}
            
            Please check the scheduler logs for more details.
            """
            
            self._send_email(subject, body)
            logger.info(f"Failure alert sent for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to send failure alert: {str(e)}")
    
    def _send_email(self, subject: str, body: str):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(self.email_config['recipient_emails'])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise
    
    def start(self):
        """Start the scheduler"""
        try:
            if not self.is_running:
                self.setup_daily_job()
                self.scheduler.start()
                self.is_running = True
                logger.info("Scheduler started successfully")
            else:
                logger.warning("Scheduler is already running")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        try:
            if self.is_running and self.scheduler:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Scheduler stopped successfully")
            else:
                logger.warning("Scheduler is not running")
                
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {str(e)}")
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        status = {
            "is_running": self.is_running,
            "next_run_time": None,
            "jobs": [],
            "timestamp": datetime.now().isoformat()
        }
        
        if self.scheduler and self.is_running:
            try:
                jobs = self.scheduler.get_jobs()
                for job in jobs:
                    job_info = {
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                        "trigger": str(job.trigger)
                    }
                    status["jobs"].append(job_info)
                
                # Get next run time for daily job
                daily_job = self.scheduler.get_job('daily_fund_data_update')
                if daily_job:
                    status["next_run_time"] = daily_job.next_run_time.isoformat()
                    
            except Exception as e:
                logger.error(f"Failed to get job status: {str(e)}")
        
        return status
    
    def run_manual_collection(self) -> Dict:
        """Run manual data collection"""
        logger.info("Starting manual data collection")
        return self.daily_data_collection()
    
    def get_collection_history(self, days: int = 7) -> List[Dict]:
        """Get collection history for specified number of days"""
        try:
            log_file = '../logs/collection_results.log'
            if not os.path.exists(log_file):
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            history = []
            
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time >= cutoff_date:
                            history.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get collection history: {str(e)}")
            return []


def main():
    """Main function for testing the scheduler"""
    scheduler = None
    
    try:
        # Initialize scheduler
        scheduler = FundDataScheduler()
        
        # Print scheduler status
        status = scheduler.get_status()
        print("Scheduler Status:")
        print(json.dumps(status, indent=2))
        
        # Run manual collection for testing
        print("\nRunning manual data collection...")
        result = scheduler.run_manual_collection()
        print("Collection Result:")
        print(json.dumps(result, indent=2))
        
        # Get collection history
        history = scheduler.get_collection_history(days=1)
        if history:
            print(f"\nRecent Collection History ({len(history)} entries):")
            for entry in history[-3:]:  # Show last 3 entries
                print(f"- {entry['timestamp']}: {entry['status']} ({entry['schemes_processed']}/{entry['schemes_processed'] + entry['schemes_failed']})")
        
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")
        print(f"Error: {str(e)}")
    finally:
        if scheduler:
            scheduler.stop()


if __name__ == "__main__":
    main()
