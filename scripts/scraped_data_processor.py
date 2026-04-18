"""
Scraped Data Processor - Converts scraped fund data into document format for chunking
Phase 1 -> Phase 2 Integration Component

This module processes raw scraped JSON data from Phase 1 and converts it into
document format suitable for the chunking pipeline in Phase 2.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class ScrapedDataProcessor:
    """Processes scraped fund data into document format"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_scraped_data(self, data_file: Path) -> List[Dict[str, Any]]:
        """Load scraped data from JSON file"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            schemes = data.get('schemes', [])
            self.logger.info(f"Loaded {len(schemes)} schemes from {data_file}")
            return schemes
            
        except Exception as e:
            self.logger.error(f"Failed to load scraped data from {data_file}: {e}")
            raise
    
    def scheme_to_document(self, scheme: Dict[str, Any]) -> Dict[str, Any]:
        """Convert single scheme data to document format"""
        # Create comprehensive text content
        document_text = f"""
Scheme Information
================

Scheme Name: {scheme.get('scheme_name', 'Unknown Scheme')}
Category: Direct Growth
AMC: ICICI Prudential

Current Data
============

NAV (Net Asset Value): {scheme.get('nav', 'N/A')}
Expense Ratio (TER): {scheme.get('expense_ratio', 'N/A')}
Exit Load: {scheme.get('exit_load', 'N/A')}
Minimum SIP Amount: {scheme.get('minimum_sip', 'N/A')}
Minimum Lumpsum: {scheme.get('minimum_lumpsum', 'N/A')}

Performance & Risk
=================

Benchmark Index: {scheme.get('benchmark', 'N/A')}
Riskometer Rating: {scheme.get('riskometer', 'N/A')}
Assets Under Management (AUM): {scheme.get('aum', 'N/A')}

Returns
=======

1 Year Return: {scheme.get('returns_1yr', 'N/A')}
3 Year Return: {scheme.get('returns_3yr', 'N/A')}
5 Year Return: {scheme.get('returns_5yr', 'N/A')}

Additional Information
====================

Fund Type: {scheme.get('fund_type', 'N/A')}
Launch Date: {scheme.get('launch_date', 'N/A')}
Fund Manager: {scheme.get('fund_manager', 'N/A')}

Investment Details
================-

Minimum Investment: SIP {scheme.get('minimum_sip', 'N/A')}, Lumpsum {scheme.get('minimum_lumpsum', 'N/A')}
Additional Purchase: {scheme.get('additional_purchase', 'N/A')}
Switching: {scheme.get('switching', 'N/A')}

Source Information
=================

Source URL: {scheme.get('source_url', 'N/A')}
Data Scraped: {scheme.get('scraped_at', 'N/A')}
Last Updated: {scheme.get('last_updated', 'N/A')}
        """.strip()
        
        # Create metadata
        metadata = {
            'document_type': 'scraped_fund_data',
            'scheme_name': scheme.get('scheme_name'),
            'amc': 'ICICI Prudential',
            'category': 'Direct Growth',
            'source_url': scheme.get('source_url'),
            'scraped_at': scheme.get('scraped_at'),
            'last_updated': scheme.get('last_updated'),
            'nav': scheme.get('nav'),
            'expense_ratio': scheme.get('expense_ratio'),
            'exit_load': scheme.get('exit_load'),
            'minimum_sip': scheme.get('minimum_sip'),
            'benchmark': scheme.get('benchmark'),
            'riskometer': scheme.get('riskometer'),
            'aum': scheme.get('aum'),
            'returns_1yr': scheme.get('returns_1yr'),
            'returns_3yr': scheme.get('returns_3yr'),
            'returns_5yr': scheme.get('returns_5yr'),
            'fund_type': scheme.get('fund_type'),
            'launch_date': scheme.get('launch_date'),
            'fund_manager': scheme.get('fund_manager'),
            'raw_scheme_data': scheme  # Keep original data for reference
        }
        
        return {
            'text': document_text,
            'metadata': metadata
        }
    
    def process_scraped_file(self, data_file: Path) -> List[Dict[str, Any]]:
        """Process entire scraped data file into documents"""
        self.logger.info(f"Processing scraped data file: {data_file}")
        
        # Load scraped data
        schemes = self.load_scraped_data(data_file)
        
        # Convert each scheme to document format
        documents = []
        for i, scheme in enumerate(schemes):
            try:
                document = self.scheme_to_document(scheme)
                documents.append(document)
                self.logger.debug(f"Processed scheme {i+1}/{len(schemes)}: {scheme.get('scheme_name', 'Unknown')}")
            except Exception as e:
                self.logger.error(f"Failed to process scheme {scheme.get('scheme_name', 'Unknown')}: {e}")
                continue
        
        self.logger.info(f"Successfully processed {len(documents)} documents from {len(schemes)} schemes")
        return documents
    
    def save_processed_documents(self, documents: List[Dict[str, Any]], output_file: Path):
        """Save processed documents to JSON file"""
        try:
            output_data = {
                'processed_at': datetime.now().isoformat(),
                'total_documents': len(documents),
                'documents': documents
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(documents)} processed documents to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save processed documents: {e}")
            raise
    
    def process_latest_scraped_data(self, raw_data_dir: Path, processed_data_dir: Path) -> Path:
        """Process the latest scraped data file"""
        # Find latest scraped data file
        scraped_files = list(raw_data_dir.glob('fund_data_*.json'))
        if not scraped_files:
            raise FileNotFoundError("No scraped data files found")
        
        latest_file = max(scraped_files, key=lambda x: x.stat().st_mtime)
        self.logger.info(f"Processing latest scraped file: {latest_file}")
        
        # Process scraped data
        documents = self.process_scraped_file(latest_file)
        
        # Save processed documents
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = processed_data_dir / f'processed_documents_{timestamp}.json'
        self.save_processed_documents(documents, output_file)
        
        return output_file

def main():
    """Test the scraped data processor"""
    logging.basicConfig(level=logging.INFO)
    
    processor = ScrapedDataProcessor()
    
    # Test with sample data
    raw_data_dir = Path('raw_data')
    processed_data_dir = Path('processed_data')
    
    if not raw_data_dir.exists():
        print("No raw_data directory found")
        return
    
    processed_data_dir.mkdir(exist_ok=True)
    
    try:
        output_file = processor.process_latest_scraped_data(raw_data_dir, processed_data_dir)
        print(f"✅ Processing completed: {output_file}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")

if __name__ == "__main__":
    main()
