# Phase 1: Web Scraping & Scheduler Implementation

## Overview
This phase implements the automated data collection system for ICICI Prudential mutual fund data from Groww website.

## Folder Structure
```
M2/
|-- phase1/
|   |-- scraping_service/
|   |   |-- scraping_service.py      # Main scraping service
|   |-- scheduler_service/
|   |   |-- scheduler_service.py      # Scheduler with APScheduler
|-- raw_data/                        # Scraped JSON data files
|-- processed_data/                  # Processed chunks (for Phase 2)
|-- config/
|   |-- scheduler_config.json        # Scheduler configuration
|-- logs/                            # Log files
|-- requirements.txt                 # Python dependencies
|-- README_Phase1.md               # Phase 1 documentation
```

## Components

### Phase 1.1.5: Web Scraping Service
**File:** `scraping_service/scraping_service.py`

**Features:**
- Selenium WebDriver for dynamic content extraction
- Robust error handling with retry logic
- Data validation and normalization
- Support for 4 ICICI Prudential schemes
- Comprehensive logging

**Extracted Data:**
- Scheme name
- NAV (Net Asset Value)
- Expense ratio (TER)
- Exit load
- Minimum SIP amount
- Benchmark index
- Riskometer rating
- AUM (Assets Under Management)
- Returns (1Y, 3Y, 5Y)

### Phase 1.1.4: Scheduler Service
**File:** `scheduler_service/scheduler_service.py`

**Features:**
- APScheduler for automated daily execution
- Configurable schedule (default: 9:15 AM IST)
- Event monitoring and alerting
- Email notifications on failures
- Job execution logging
- Retry logic with exponential backoff

## Installation

### Prerequisites
1. Python 3.9+
2. Chrome WebDriver (automatically managed by webdriver-manager)
3. Chrome browser

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create necessary folders (already created)
mkdir -p raw_data processed_data config logs
```

## Configuration

### Scheduler Configuration
Edit `config/scheduler_config.json`:

```json
{
  "schedule": {
    "hour": 9,
    "minute": 15,
    "timezone": "Asia/Kolkata"
  },
  "urls": [
    "https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth",
    "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth",
    "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
  ],
  "retry": {
    "max_attempts": 3,
    "backoff_factor": 2,
    "delay": 60
  },
  "email": {
    "enabled": false,
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
```

## Usage

### Manual Testing
```bash
# Test scraping service
cd phase1/scraping_service
python scraping_service.py

# Test scheduler service
cd phase1/scheduler_service
python scheduler_service.py
```

### Running the Scheduler
```python
from scheduler_service.scheduler_service import FundDataScheduler

# Initialize and start scheduler
scheduler = FundDataScheduler()
scheduler.start()

# Check status
status = scheduler.get_status()
print(status)

# Run manual collection
result = scheduler.run_manual_collection()
print(result)

# Stop scheduler
scheduler.stop()
```

## Data Output

### Scraped Data Format
```json
{
  "scheme_name": "ICICI Prudential Large Cap Fund Direct Growth",
  "nav": "15.2345",
  "expense_ratio": "0.42%",
  "exit_load": "1% after 1 year",
  "minimum_sip": "5000",
  "benchmark": "Nifty 50 TRI",
  "riskometer": "High Risk",
  "aum": "15234.56 Cr",
  "returns_1yr": "12.34%",
  "returns_3yr": "15.67%",
  "returns_5yr": "14.89%",
  "last_updated": "2024-04-17T18:00:00",
  "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
  "scraped_at": "2024-04-17T18:00:00"
}
```

### File Naming Convention
- Raw data: `fund_data_YYYYMMDD_HHMMSS.json`
- Logs: `scraping_service.log`, `scheduler_service.log`
- Job logs: `job_execution.log`, `collection_results.log`

## Monitoring

### Log Files
- `logs/scraping_service.log` - Scraping operations
- `logs/scheduler_service.log` - Scheduler operations
- `logs/job_execution.log` - Individual job results
- `logs/collection_results.log` - Daily collection summaries

### Health Checks
The scheduler monitors:
- Consecutive job failures
- Data collection success rates
- Scraping service availability

## Error Handling

### Retry Logic
- Max 3 attempts per URL
- Exponential backoff (60s, 120s, 240s)
- Graceful degradation on partial failures

### Alerting
- Email alerts after 3 consecutive failures
- Detailed error logging
- Failed URL tracking

## Next Steps

### Phase 2: Chunking & Embedding
After implementing Phase 1, the scraped data will be processed by:
1. Data validation and normalization
2. Intelligent chunking strategy
3. OpenAI embedding generation
4. FAISS vector database updates

### Integration with GitHub Actions
The scheduler will be integrated with GitHub Actions for:
- Automated daily execution
- Pipeline orchestration
- Version control of embeddings

## Troubleshooting

### Common Issues
1. **WebDriver not found**: Install Chrome and webdriver-manager will handle the rest
2. **Website changes**: Update CSS selectors in scraping service
3. **Network issues**: Check internet connection and retry settings
4. **Permission errors**: Ensure write access to logs and data folders

### Debug Mode
Set headless=False in scraping service to see browser actions:
```python
scraper = GrowwScraper(headless=False)
```

## Dependencies

### Key Libraries
- `selenium` - Web automation
- `beautifulsoup4` - HTML parsing
- `APScheduler` - Task scheduling
- `webdriver-manager` - WebDriver management

### Chrome WebDriver
Automatically managed by webdriver-manager. No manual installation required.

## Security Notes

- No sensitive data is stored in scraped files
- Email credentials should be set via environment variables
- Chrome runs in headless mode by default
- Rate limiting prevents server overload
