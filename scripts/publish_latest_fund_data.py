#!/usr/bin/env python3
"""Scrape Groww fund pages and publish data/latest_fund_data.json for the deployed chatbot."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "logs"
DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "latest_fund_data.json"
CONFIG_FILE = ROOT / "config" / "scheduler_config.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "phase1" / "scraping_service"))

from scraping_service import GrowwScraper  # noqa: E402


def load_urls() -> list[str]:
    if CONFIG_FILE.exists():
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        urls = config.get("urls") or []
        if urls:
            return urls
    return [
        "https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth",
    ]


def main() -> int:
    urls = load_urls()
    scraper = None
    try:
        scraper = GrowwScraper(headless=True)
        raw_schemes, failed_urls = scraper.scrape_all_schemes(urls)
        if not raw_schemes:
            print("Scrape returned no schemes; leaving existing published file unchanged.")
            if failed_urls:
                print("Failed URLs:", failed_urls)
            return 1

        payload = {
            "version": "1.0",
            "collection_metadata": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Groww",
                "total_schemes": len(raw_schemes),
                "data_quality_score": scraper._calculate_data_quality(raw_schemes),
                "extraction_method": "selenium_webdriver",
            },
            "schemes": scraper._enhance_scheme_data(raw_schemes),
            "data_quality": scraper._assess_data_quality(raw_schemes),
        }
        OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Published {len(raw_schemes)} schemes to {OUTPUT_FILE}")
        if failed_urls:
            print("Failed URLs:", failed_urls)
        return 0
    finally:
        if scraper is not None:
            scraper.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
