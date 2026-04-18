"""
Document Processing Pipeline for Phase 1.2
Handles PDF processing, web scraping, and text normalization
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes documents from various sources into normalized text"""
    
    def __init__(self, raw_documents_dir: str = "raw_documents"):
        self.raw_documents_dir = Path(raw_documents_dir)
        self.raw_documents_dir.mkdir(exist_ok=True)
        
        # Scheme name mapping for normalization
        self.scheme_name_mapping = {
            "ICICI Pru Dynamic Plan": "ICICI Prudential Dynamic Plan Direct Growth",
            "ICICI Pru Large Cap Fund": "ICICI Prudential Large Cap Fund Direct Growth",
            "ICICI Pru Nifty Next 50": "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
            "ICICI Pru Top 100 Fund": "ICICI Prudential Top 100 Fund Direct Growth",
            "ICICI Prudential Multi Asset Fund": "ICICI Prudential Dynamic Plan Direct Growth",
            "ICICI Prudential Large & Mid Cap Fund": "ICICI Prudential Top 100 Fund Direct Growth"
        }
        
        # Target schemes
        self.target_schemes = [
            "ICICI Prudential Dynamic Plan Direct Growth",
            "ICICI Prudential Large Cap Fund Direct Growth", 
            "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
            "ICICI Prudential Top 100 Fund Direct Growth"
        ]
    
    def process_pdf_document(self, pdf_path: str, scheme_name: str, doc_type: str) -> Dict[str, Any]:
        """Process PDF document and extract normalized text"""
        try:
            doc = fitz.open(pdf_path)
            extracted_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Clean text
                cleaned_text = self._clean_pdf_text(text)
                if cleaned_text.strip():
                    extracted_text.append({
                        "page": page_num + 1,
                        "text": cleaned_text,
                        "doc_type": doc_type,
                        "scheme": scheme_name
                    })
            
            doc.close()
            
            return {
                "success": True,
                "content": extracted_text,
                "total_pages": len(extracted_text)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _clean_pdf_text(self, text: str) -> str:
        """Clean extracted PDF text"""
        # Remove common headers/footers
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Skip common headers/footers
            skip_patterns = [
                r'ICICI Prudential.*AMC',
                r'Page \d+ of \d+',
                r'\|.*\|',
                r'^\d+$',
                r'www\..*',
                r'Confidential',
                r'For Internal Use Only'
            ]
            
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    should_skip = True
                    break
            
            if not should_skip:
                cleaned_lines.append(line)
        
        # Rejoin with proper spacing
        return ' '.join(cleaned_lines)
    
    def scrape_web_page(self, url: str, content_type: str = "general") -> Dict[str, Any]:
        """Scrape web page and extract content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Extract main content
            main_content = self._extract_main_content(soup, content_type)
            
            return {
                "success": True,
                "url": url,
                "content": main_content,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _extract_main_content(self, soup: BeautifulSoup, content_type: str) -> List[Dict]:
        """Extract main content from BeautifulSoup object"""
        content = []
        
        # Try different content selectors
        content_selectors = [
            'main', 'article', '.content', '#content', 
            '.main-content', '.post-content', '.entry-content'
        ]
        
        main_element = None
        for selector in content_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                break
        
        if not main_element:
            main_element = soup.find('body')
        
        if main_element:
            text = main_element.get_text(separator=' ', strip=True)
            text = self._normalize_text(text)
            
            content.append({
                "text": text,
                "content_type": content_type,
                "source_url": soup.get('base_url', ''),
                "extracted_at": datetime.now().isoformat()
            })
        
        return content
    
    def normalize_text(self, text: str) -> str:
        """Apply text normalization rules"""
        return self._normalize_text(text)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text according to Phase 1.2.3 requirements"""
        
        # 1. Standardize scheme names
        for short_name, full_name in self.scheme_name_mapping.items():
            text = re.sub(rf'\b{re.escape(short_name)}\b', full_name, text, flags=re.IGNORECASE)
        
        # 2. Normalize numerical formats
        # Currency: ₹5,000 → 5000
        text = re.sub(r'₹\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', lambda m: m.group(1).replace(',', ''), text)
        
        # Percentages: 0.42% → 0.42
        text = re.sub(r'(\d+\.?\d*)\s?%', r'\1', text)
        
        # 3. Convert dates to ISO format
        # March 2024 → 2024-03
        month_mapping = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        
        for month, month_num in month_mapping.items():
            text = re.sub(rf'\b{month}\s+(\d{4})\b', r'\1-{month_num}', text, flags=re.IGNORECASE)
        
        # 4. Fix spacing and formatting
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Preserve paragraph breaks
        
        return text.strip()
    
    def save_document(self, content: List[Dict], filename: str) -> str:
        """Save processed document to file"""
        filepath = self.raw_documents_dir / filename
        
        document_data = {
            "filename": filename,
            "processed_at": datetime.now().isoformat(),
            "content": content,
            "total_sections": len(content)
        }
        
        # Save as JSON
        json_filepath = filepath.with_suffix('.json')
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(document_data, f, indent=2, ensure_ascii=False)
        
        # Also save as plain text for easy reading
        txt_filepath = filepath.with_suffix('.txt')
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            for section in content:
                f.write(f"=== {section.get('content_type', 'Content')} ===\n")
                f.write(f"{section['text']}\n\n")
        
        logger.info(f"Saved document: {filename}")
        return str(json_filepath)
    
    def create_sample_documents(self):
        """Create sample documents for testing when real ones aren't available"""
        
        # Sample factsheet content
        sample_factsheet = {
            "text": """
            ICICI Prudential Large Cap Fund Direct Growth - Factsheet
            
            Fund Objective: To generate long-term capital appreciation by investing in a diversified portfolio of large-cap companies.
            
            Expense Ratio: 0.42% (as of March 2024)
            
            Exit Load: 1% if redeemed within 365 days, Nil thereafter
            
            Minimum Investment: SIP - ₹5000, Lumpsum - ₹5000
            
            Benchmark: Nifty 50 TRI
            
            Riskometer: High Risk
            
            Assets Under Management: ₹15,234.56 Cr (as of March 2024)
            
            Portfolio Allocation:
            - Equity: 95.23%
            - Debt & Money Market: 4.77%
            
            Top Holdings:
            1. Reliance Industries Ltd. - 8.45%
            2. HDFC Bank Ltd. - 7.23%
            3. ICICI Bank Ltd. - 6.89%
            4. Infosys Ltd. - 5.67%
            5. TCS Ltd. - 5.34%
            
            Performance:
            1 Year: 12.34%
            3 Year: 15.67%
            5 Year: 14.89%
            
            Since Inception: 16.23%
            
            Fund Manager: Mr. S Naren
            
            Launch Date: January 1999
            
            Last Updated: March 31, 2024
            """,
            "content_type": "factsheet",
            "scheme": "ICICI Prudential Large Cap Fund Direct Growth",
            "source_url": "https://www.icicipruamc.com/factsheet"
        }
        
        # Sample KIM content
        sample_kim = {
            "text": """
            Key Information Memorandum - ICICI Prudential Large Cap Fund Direct Growth
            
            Type of Fund: Open-ended Equity Scheme - Large Cap
            
            Investment Objective: To provide long-term capital appreciation/income through investments in large-cap companies.
            
            Option: Direct Plan - Growth Option
            
            Face Value: ₹10 per unit
            
            Minimum Application Amount:
            - ₹5000 and in multiples of ₹1 thereafter
            
            Minimum Additional Investment: ₹1000 and in multiples of ₹1 thereafter
            
            Minimum Redemption Amount: ₹5000 or all units, whichever is lower
            
            Exit Load:
            - 1% if units are redeemed/switched out within 365 days from the date of allotment
            - Nil if units are redeemed/switched out after 365 days from the date of allotment
            
            Load Applicable: On Applicable NAV
            
            Risk Factors: 
            - Market Risk: The NAV of the scheme may be affected by movements in the stock market
            - Liquidity Risk: The fund may face difficulties in selling securities at desired prices
            - Concentration Risk: Investments concentrated in large-cap companies
            
            Taxation: 
            - Long-term capital gains (holding period > 1 year) taxed at 10% above ₹1 lakh
            - Short-term capital gains (holding period ≤ 1 year) taxed at 15%
            
            Last Updated: March 31, 2024
            """,
            "content_type": "kim",
            "scheme": "ICICI Prudential Large Cap Fund Direct Growth",
            "source_url": "https://www.icicipruamc.com/kim"
        }
        
        # Sample investor services content
        sample_investor_services = {
            "text": """
            ICICI Prudential Mutual Fund - Investor Services Guide
            
            How to Download Account Statement:
            
            1. Visit the ICICI Prudential Mutual Fund website (www.icicipruamc.com)
            2. Click on 'Investor Services' or 'Login'
            3. Enter your Folio Number and PAN
            4. Click on 'Statement Download'
            5. Select the period for which you need the statement
            6. Choose the format (PDF or Excel)
            7. Download the statement
            
            How to Download Capital Gains Statement (CAS):
            
            1. Log in to your account on the ICICI Prudential website
            2. Go to 'Tax Documents' section
            3. Select 'Capital Gains Statement'
            4. Choose the financial year
            5. Download the Consolidated Account Statement (CAS)
            
            For assistance, contact:
            - Customer Care: 1860 266 7766
            - Email: investor@icicipruamc.com
            - Website: www.icicipruamc.com
            
            Last Updated: April 2024
            """,
            "content_type": "investor_services",
            "scheme": "General",
            "source_url": "https://www.icicipruamc.com/investor-services"
        }
        
        # Save sample documents
        for scheme in self.target_schemes:
            # Create scheme-specific documents
            scheme_name_short = scheme.replace("ICICI Prudential ", "").replace(" Direct Growth", "").lower().replace(" ", "_")
            
            factsheet_content = [sample_factsheet.copy()]
            factsheet_content[0]["scheme"] = scheme
            self.save_document(factsheet_content, f"{scheme_name_short}_factsheet")
            
            kim_content = [sample_kim.copy()]
            kim_content[0]["scheme"] = scheme
            self.save_document(kim_content, f"{scheme_name_short}_kim")
        
        # Save general documents
        self.save_document([sample_investor_services], "investor_services")
        
        logger.info("Sample documents created successfully")

if __name__ == "__main__":
    processor = DocumentProcessor()
    processor.create_sample_documents()
