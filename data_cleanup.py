#!/usr/bin/env python3
"""
Data Cleanup Script
Checks data dates and deletes non-current day's data files
"""

import os
import json
import glob
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleanupManager:
    """Manages cleanup of outdated data files"""
    
    def __init__(self, raw_data_dir: str = "raw_data", logs_dir: str = "logs"):
        """
        Initialize cleanup manager
        
        Args:
            raw_data_dir: Directory containing raw data files
            logs_dir: Directory for cleanup logs
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.logs_dir = Path(logs_dir)
        self.cleanup_log_file = self.logs_dir / "data_cleanup.log"
        
        # Ensure directories exist
        self.raw_data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def get_file_date(self, file_path: Path) -> datetime:
        """
        Extract date from filename or file creation date
        
        Args:
            file_path: Path to the data file
            
        Returns:
            datetime object representing the file date
        """
        filename = file_path.name
        
        # Try to extract date from filename (format: fund_data_YYYYMMDD_HHMMSS.json)
        if filename.startswith("fund_data_") and filename.endswith(".json"):
            try:
                date_part = filename.replace("fund_data_", "").replace(".json", "")
                date_str = date_part.split("_")[0]  # Get YYYYMMDD part
                return datetime.strptime(date_str, "%Y%m%d")
            except (ValueError, IndexError):
                pass
        
        # Fallback to file modification time
        try:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            return mod_time
        except Exception:
            return datetime.min
    
    def is_current_day_data(self, file_path: Path) -> bool:
        """
        Check if file contains current day's data
        
        Args:
            file_path: Path to the data file
            
        Returns:
            True if file is from current day, False otherwise
        """
        file_date = self.get_file_date(file_path)
        today = datetime.now().date()
        return file_date.date() == today
    
    def cleanup_outdated_data(self, dry_run: bool = False) -> dict:
        """
        Clean up outdated data files (keep only current day's data)
        
        Args:
            dry_run: If True, only report what would be deleted without actually deleting
            
        Returns:
            Dictionary with cleanup results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "total_files": 0,
            "current_day_files": 0,
            "outdated_files": 0,
            "deleted_files": [],
            "failed_deletions": [],
            "errors": []
        }
        
        try:
            # Get all JSON files in raw_data directory
            data_files = list(self.raw_data_dir.glob("fund_data_*.json"))
            results["total_files"] = len(data_files)
            
            logger.info(f"Found {len(data_files)} data files to check")
            
            for file_path in data_files:
                try:
                    if self.is_current_day_data(file_path):
                        results["current_day_files"] += 1
                        logger.info(f"Keeping current day file: {file_path.name}")
                    else:
                        results["outdated_files"] += 1
                        logger.info(f"Outdated file found: {file_path.name}")
                        
                        if not dry_run:
                            try:
                                file_path.unlink()
                                results["deleted_files"].append(str(file_path.name))
                                logger.info(f"Deleted outdated file: {file_path.name}")
                            except Exception as e:
                                results["failed_deletions"].append({
                                    "file": str(file_path.name),
                                    "error": str(e)
                                })
                                logger.error(f"Failed to delete {file_path.name}: {e}")
                        else:
                            results["deleted_files"].append(str(file_path.name) + " (dry run)")
                
                except Exception as e:
                    results["errors"].append({
                        "file": str(file_path.name),
                        "error": str(e)
                    })
                    logger.error(f"Error processing {file_path.name}: {e}")
            
            # Log cleanup results
            self._log_cleanup_results(results)
            
        except Exception as e:
            results["errors"].append({"general_error": str(e)})
            logger.error(f"Cleanup failed: {e}")
        
        return results
    
    def _log_cleanup_results(self, results: dict):
        """Log cleanup results to file"""
        try:
            with open(self.cleanup_log_file, 'a') as f:
                f.write(json.dumps(results, indent=2) + '\n')
        except Exception as e:
            logger.error(f"Failed to log cleanup results: {e}")
    
    def get_cleanup_history(self, days: int = 7) -> list:
        """
        Get cleanup history for specified number of days
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of cleanup results
        """
        try:
            if not self.cleanup_log_file.exists():
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            history = []
            
            with open(self.cleanup_log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time >= cutoff_date:
                            history.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get cleanup history: {e}")
            return []
    
    def cleanup_logs(self, days_to_keep: int = 30):
        """
        Clean up old log files
        
        Args:
            days_to_keep: Number of days to keep log files
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for log_file in self.logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.info(f"Deleted old log file: {log_file.name}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup logs: {e}")

def main():
    """Main function for testing and manual cleanup"""
    cleanup_manager = DataCleanupManager()
    
    print("=== Data Cleanup Manager ===")
    print(f"Raw data directory: {cleanup_manager.raw_data_dir}")
    print(f"Logs directory: {cleanup_manager.logs_dir}")
    print()
    
    # Show current files
    current_files = list(cleanup_manager.raw_data_dir.glob("fund_data_*.json"))
    print(f"Current data files: {len(current_files)}")
    for file in sorted(current_files, key=lambda x: x.stat().st_mtime, reverse=True):
        file_date = cleanup_manager.get_file_date(file)
        is_current = cleanup_manager.is_current_day_data(file)
        status = "✓ CURRENT" if is_current else "✗ OUTDATED"
        print(f"  {file.name} ({file_date.strftime('%Y-%m-%d')}) {status}")
    
    print()
    
    # Dry run cleanup
    print("=== Dry Run Cleanup ===")
    dry_run_results = cleanup_manager.cleanup_outdated_data(dry_run=True)
    print(f"Total files: {dry_run_results['total_files']}")
    print(f"Current day files: {dry_run_results['current_day_files']}")
    print(f"Outdated files: {dry_run_results['outdated_files']}")
    
    if dry_run_results['deleted_files']:
        print("Files to be deleted:")
        for file in dry_run_results['deleted_files']:
            print(f"  - {file}")
    
    print()
    
    # Ask for confirmation
    if dry_run_results['outdated_files'] > 0:
        response = input("Delete outdated files? (y/N): ").lower().strip()
        if response == 'y':
            print("=== Actual Cleanup ===")
            actual_results = cleanup_manager.cleanup_outdated_data(dry_run=False)
            print(f"Deleted {len(actual_results['deleted_files'])} files")
            
            if actual_results['failed_deletions']:
                print("Failed deletions:")
                for failure in actual_results['failed_deletions']:
                    print(f"  - {failure['file']}: {failure['error']}")
        else:
            print("Cleanup cancelled")
    else:
        print("No outdated files to cleanup")

if __name__ == "__main__":
    main()
