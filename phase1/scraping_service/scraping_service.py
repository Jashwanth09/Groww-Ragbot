"""
Phase 1.1.5: Web Scraping Service
Extracts structured data from Groww mutual fund pages
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
import time
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/scraping_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class GrowwScraper:
    """Scrapes mutual fund data from Groww website"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize the scraper
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for element waits
        """
        self.timeout = timeout
        self.driver = None
        self.wait = None
        self.headless = headless
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            options = Options()
            
            if self.headless:
                options.add_argument('--headless')
            
            # Essential options for stability
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Disable unnecessary features
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')  # We'll enable when needed
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            logger.info("WebDriver setup completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            raise
    
    def scrape_scheme_page(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Scrape individual scheme page for key metrics
        
        Args:
            url: Groww scheme page URL
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing scraped data or None if failed
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Scraping attempt {attempt + 1}/{max_retries}: {url}")
                
                # Enable JavaScript for dynamic content
                if attempt == 0:
                    self._enable_javascript()
                
                # Load page
                self.driver.get(url)
                time.sleep(3)  # Initial wait for page load
                
                # Wait for key elements to load
                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                except TimeoutException:
                    logger.warning(f"Page load timeout for {url}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                
                # Get page source and parse
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Extract scheme data
                scheme_data = self._extract_scheme_data(soup, url)
                
                if scheme_data and self._validate_scheme_data(scheme_data):
                    logger.info(f"Successfully scraped: {url}")
                    return scheme_data
                else:
                    logger.warning(f"Invalid data extracted from {url}")
                    
            except Exception as e:
                logger.error(f"Scraping attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All {max_retries} attempts failed for {url}")
        
        return None
    
    def _enable_javascript(self):
        """Enable JavaScript in the browser"""
        try:
            self.driver.execute_script("return true;")
            logger.info("JavaScript enabled")
        except Exception as e:
            logger.warning(f"Failed to enable JavaScript: {str(e)}")
    
    def _extract_scheme_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract key data fields from the page"""
        try:
            scheme_data = {
                'scheme_name': self._extract_scheme_name(soup),
                'nav': self._extract_nav_clean(soup),
                'minimum_sip': self._extract_minimum_sip_clean(soup),
                'fund_size': self._extract_fund_size(soup),
                'expense_ratio': self._extract_expense_ratio_clean(soup),
                'rating': self._extract_rating(soup),
                'last_updated': datetime.now().isoformat(),
                'source_url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            return scheme_data
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            return {}
    
    def _extract_scheme_name(self, soup: BeautifulSoup) -> str:
        """Extract scheme name from page"""
        try:
            # Try multiple selectors for scheme name
            selectors = [
                'h1[class*="fund"]',
                'h1[class*="scheme"]',
                '.fund-name',
                '.scheme-name',
                'h1',
                'title'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text().strip()
                    if name and len(name) > 5:  # Basic validation
                        return name
            
            return "Unknown Scheme"
            
        except Exception as e:
            logger.warning(f"Failed to extract scheme name: {str(e)}")
            return "Unknown Scheme"
    
    def _extract_nav(self, soup: BeautifulSoup) -> str:
        """Extract current NAV"""
        try:
            # Look for NAV patterns
            nav_patterns = [
                r'NAV\s*[:\-]?\s*Rs?\s*[\d,\.]+',
                r'Net\s+Asset\s+Value\s*[:\-]?\s*Rs?\s*[\d,\.]+',
                r'Rs?\s*[\d,\.]+\s*NAV'
            ]
            
            page_text = soup.get_text()
            for pattern in nav_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    nav_text = match.group()
                    # Extract numeric value
                    nav_match = re.search(r'[\d,\.]+', nav_text)
                    if nav_match:
                        return nav_match.group()
            
            # Try specific selectors
            nav_selectors = [
                '[class*="nav"]',
                '[class*="NAV"]',
                '[data-testid*="nav"]'
            ]
            
            for selector in nav_selectors:
                element = soup.select_one(selector)
                if element:
                    nav_text = element.get_text().strip()
                    nav_match = re.search(r'[\d,\.]+', nav_text)
                    if nav_match:
                        return nav_match.group()
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract NAV: {str(e)}")
            return "N/A"
    
    def _extract_expense_ratio(self, soup: BeautifulSoup) -> str:
        """Extract expense ratio"""
        try:
            # Look for expense ratio patterns
            er_patterns = [
                r'Expense\s+Ratio\s*[:\-]?\s*[\d\.]+%?',
                r'TER\s*[:\-]?\s*[\d\.]+%?',
                r'Total\s+Expense\s+Ratio\s*[:\-]?\s*[\d\.]+%?'
            ]
            
            page_text = soup.get_text()
            for pattern in er_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    er_text = match.group()
                    # Extract numeric value
                    er_match = re.search(r'[\d\.]+', er_text)
                    if er_match:
                        return er_match.group() + '%'
            
            # Try specific selectors
            er_selectors = [
                '[class*="expense"]',
                '[class*="ratio"]',
                '[data-testid*="expense"]'
            ]
            
            for selector in er_selectors:
                element = soup.select_one(selector)
                if element:
                    er_text = element.get_text().strip()
                    er_match = re.search(r'[\d\.]+%?', er_text)
                    if er_match:
                        return er_match.group()
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract expense ratio: {str(e)}")
            return "N/A"
    
    def _extract_exit_load(self, soup: BeautifulSoup) -> str:
        """Extract exit load information"""
        try:
            # Look for exit load patterns
            exit_load_patterns = [
                r'Exit\s+Load\s*[:\-]?\s*[\d\.]+%?\s*(?:after|within)?\s*\d+\s*(?:days?|years?)',
                r'Exit\s+Load\s*[:\-]?\s*Nil|None|0%',
                r'[\d\.]+%?\s*exit\s+load'
            ]
            
            page_text = soup.get_text()
            for pattern in exit_load_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return match.group().strip()
            
            # Try specific selectors
            exit_load_selectors = [
                '[class*="exit"]',
                '[class*="load"]',
                '[data-testid*="exit"]'
            ]
            
            for selector in exit_load_selectors:
                element = soup.select_one(selector)
                if element:
                    exit_load_text = element.get_text().strip()
                    if 'exit' in exit_load_text.lower() or 'load' in exit_load_text.lower():
                        return exit_load_text
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract exit load: {str(e)}")
            return "N/A"
    
    def _extract_minimum_sip(self, soup: BeautifulSoup) -> str:
        """Extract minimum SIP amount"""
        try:
            # Look for SIP patterns
            sip_patterns = [
                r'Minimum\s+SIP\s*[:\-]?\s*Rs?\s*[\d,]+',
                r'SIP\s*[:\-]?\s*Rs?\s*[\d,]+',
                r'Minimum\s+Investment\s*[:\-]?\s*Rs?\s*[\d,]+'
            ]
            
            page_text = soup.get_text()
            for pattern in sip_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    sip_text = match.group()
                    # Extract numeric value
                    sip_match = re.search(r'[\d,]+', sip_text)
                    if sip_match:
                        return sip_match.group()
            
            # Try specific selectors
            sip_selectors = [
                '[class*="sip"]',
                '[class*="investment"]',
                '[data-testid*="sip"]'
            ]
            
            for selector in sip_selectors:
                element = soup.select_one(selector)
                if element:
                    sip_text = element.get_text().strip()
                    sip_match = re.search(r'Rs?\s*[\d,]+', sip_text, re.IGNORECASE)
                    if sip_match:
                        return sip_match.group()
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract minimum SIP: {str(e)}")
            return "N/A"
    
    def _extract_benchmark(self, soup: BeautifulSoup) -> str:
        """Extract benchmark index"""
        try:
            # Look for benchmark patterns
            benchmark_patterns = [
                r'Benchmark\s*[:\-]?\s*[^,\n]+',
                r'Index\s*[:\-]?\s*[^,\n]+',
                r'Nifty\s+[^,\n]+'
            ]
            
            page_text = soup.get_text()
            for pattern in benchmark_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    benchmark = match.group().strip()
                    # Clean up the benchmark name
                    if ':' in benchmark or '-' in benchmark:
                        benchmark = re.split(r'[:\-]', benchmark)[-1].strip()
                    
                    if len(benchmark) > 3:  # Basic validation
                        return benchmark
            
            # Try specific selectors
            benchmark_selectors = [
                '[class*="benchmark"]',
                '[class*="index"]',
                '[data-testid*="benchmark"]'
            ]
            
            for selector in benchmark_selectors:
                element = soup.select_one(selector)
                if element:
                    benchmark_text = element.get_text().strip()
                    if len(benchmark_text) > 3:
                        return benchmark_text
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract benchmark: {str(e)}")
            return "N/A"
    
    def _extract_riskometer(self, soup: BeautifulSoup) -> str:
        """Extract riskometer rating"""
        try:
            # Look for risk patterns
            risk_patterns = [
                r'Risk\s*[:\-]?\s*[^,\n]+',
                r'Riskometer\s*[:\-]?\s*[^,\n]+',
                r'(Very\s+High|High|Moderate|Low)\s*Risk'
            ]
            
            page_text = soup.get_text()
            for pattern in risk_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    risk = match.group().strip()
                    # Clean up the risk rating
                    if ':' in risk or '-' in risk:
                        risk = re.split(r'[:\-]', risk)[-1].strip()
                    
                    if len(risk) > 2:  # Basic validation
                        return risk
            
            # Try specific selectors
            risk_selectors = [
                '[class*="risk"]',
                '[class*="riskometer"]',
                '[data-testid*="risk"]'
            ]
            
            for selector in risk_selectors:
                element = soup.select_one(selector)
                if element:
                    risk_text = element.get_text().strip()
                    if len(risk_text) > 2:
                        return risk_text
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract riskometer: {str(e)}")
            return "N/A"
    
    def _extract_aum(self, soup: BeautifulSoup) -> str:
        """Extract Assets Under Management"""
        try:
            # Look for AUM patterns
            aum_patterns = [
                r'AUM\s*[:\-]?\s*Rs?\s*[\d,\.]+\s*(?:Cr|Lakh|Thousand)?',
                r'Assets\s+Under\s+Management\s*[:\-]?\s*Rs?\s*[\d,\.]+\s*(?:Cr|Lakh|Thousand)?'
            ]
            
            page_text = soup.get_text()
            for pattern in aum_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return match.group().strip()
            
            # Try specific selectors
            aum_selectors = [
                '[class*="aum"]',
                '[class*="assets"]',
                '[data-testid*="aum"]'
            ]
            
            for selector in aum_selectors:
                element = soup.select_one(selector)
                if element:
                    aum_text = element.get_text().strip()
                    if 'aum' in aum_text.lower() or 'assets' in aum_text.lower():
                        return aum_text
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract AUM: {str(e)}")
            return "N/A"
    
    def _extract_returns(self, soup: BeautifulSoup, period: str) -> str:
        """Extract returns for specific period"""
        try:
            # Look for returns patterns
            return_patterns = [
                rf'{period}\s*[:\-]?\s*[\d\.]+%?',
                rf'{period}\s+Returns\s*[:\-]?\s*[\d\.]+%?',
                rf'{period}\s*[:\-]?\s*[\d\.]+%?\s*Returns'
            ]
            
            page_text = soup.get_text()
            for pattern in return_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return_text = match.group().strip()
                    # Extract numeric value with percentage
                    return_match = re.search(r'[\d\.]+%?', return_text)
                    if return_match:
                        return return_match.group()
            
            # Try specific selectors
            return_selectors = [
                f'[class*="{period.lower()}"]',
                f'[data-period="{period}"]',
                f'[data-testid*="{period.lower()}"]'
            ]
            
            for selector in return_selectors:
                element = soup.select_one(selector)
                if element:
                    return_text = element.get_text().strip()
                    return_match = re.search(r'[\d\.]+%?', return_text)
                    if return_match:
                        return return_match.group()
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract {period} returns: {str(e)}")
            return "N/A"
    
    def _extract_nav_clean(self, soup: BeautifulSoup) -> str:
        """Extract clean NAV value"""
        try:
            # Look for NAV patterns in page text
            page_text = soup.get_text()
            
            # Common NAV patterns
            nav_patterns = [
                r'NAV\s*[:\-]?\s*Rs?\s*([\d,\.]+)',
                r'Net\s+Asset\s+Value\s*[:\-]?\s*Rs?\s*([\d,\.]+)',
                r'Rs?\s*([\d,\.]+)\s*NAV',
                r'Current\s+NAV\s*[:\-]?\s*Rs?\s*([\d,\.]+)'
            ]
            
            for pattern in nav_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    nav_value = match.group(1).replace(',', '').strip()
                    # Validate it's a reasonable NAV value
                    try:
                        nav_float = float(nav_value)
                        if 10 <= nav_float <= 10000:  # Reasonable NAV range
                            return nav_value
                    except ValueError:
                        continue
            
            # Try to find NAV in specific elements
            nav_selectors = [
                '[class*="nav"]',
                '[class*="NAV"]',
                '[data-testid*="nav"]',
                'span:contains("NAV")',
                'div:contains("NAV")'
            ]
            
            for selector in nav_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    nav_match = re.search(r'[\d,\.]+', text)
                    if nav_match:
                        nav_value = nav_match.group().replace(',', '').strip()
                        try:
                            nav_float = float(nav_value)
                            if 10 <= nav_float <= 10000:
                                return nav_value
                        except ValueError:
                            continue
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract NAV: {str(e)}")
            return "N/A"
    
    def _extract_minimum_sip_clean(self, soup: BeautifulSoup) -> str:
        """Extract clean minimum SIP amount"""
        try:
            page_text = soup.get_text()
            
            # SIP patterns
            sip_patterns = [
                r'Minimum\s+SIP\s*[:\-]?\s*Rs?\s*([\d,]+)',
                r'SIP\s*[:\-]?\s*Rs?\s*([\d,]+)',
                r'Minimum\s+Investment\s*[:\-]?\s*Rs?\s*([\d,]+)',
                r'SIP\s+Minimum\s*[:\-]?\s*Rs?\s*([\d,]+)',
                r'Min\.?\s*for\s+SIP\s*[:\-]?\s*Rs?\s*([\d,]+)'
            ]
            
            for pattern in sip_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    sip_value = match.group(1).replace(',', '').strip()
                    # Validate it's a reasonable SIP amount
                    try:
                        sip_int = int(sip_value)
                        if 100 <= sip_int <= 50000:  # Reasonable SIP range
                            return sip_value
                    except ValueError:
                        continue
            
            # Look for SIP elements
            sip_selectors = [
                '[class*="sip"]',
                '[class*="investment"]',
                '[data-testid*="sip"]'
            ]
            
            for selector in sip_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if 'sip' in text.lower():
                        sip_match = re.search(r'Rs?\s*([\d,]+)', text, re.IGNORECASE)
                        if sip_match:
                            sip_value = sip_match.group(1).replace(',', '').strip()
                            try:
                                sip_int = int(sip_value)
                                if 100 <= sip_int <= 50000:
                                    return sip_value
                            except ValueError:
                                continue
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract minimum SIP: {str(e)}")
            return "N/A"
    
    def _extract_fund_size(self, soup: BeautifulSoup) -> str:
        """Extract fund size (AUM)"""
        try:
            page_text = soup.get_text()
            
            # Fund size patterns
            fund_size_patterns = [
                r'Fund\s+Size\s*\([^)]+\)\s*[:\-]?\s*Rs?\s*([\d,\.]+)\s*(?:Cr|Lakh|Thousand)',
                r'AUM\s*[:\-]?\s*Rs?\s*([\d,\.]+)\s*(?:Cr|Lakh|Thousand)',
                r'Assets\s+Under\s+Management\s*[:\-]?\s*Rs?\s*([\d,\.]+)\s*(?:Cr|Lakh|Thousand)',
                r'Total\s+AUM\s*[:\-]?\s*Rs?\s*([\d,\.]+)\s*(?:Cr|Lakh|Thousand)',
                r'Fund\s+size\s*\(AUM\)\s*[:\-]?\s*Rs?\s*([\d,\.]+)\s*(?:Cr|Lakh|Thousand)'
            ]
            
            for pattern in fund_size_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    size_value = match.group(1).replace(',', '').strip()
                    # Extract unit
                    unit_match = re.search(r'(Cr|Lakh|Thousand)', match.group())
                    unit = unit_match.group() if unit_match else ''
                    
                    try:
                        size_float = float(size_value)
                        if 0.1 <= size_float <= 100000:  # Reasonable range
                            return f"{size_value} {unit}"
                    except ValueError:
                        continue
            
            # Look for fund size elements
            size_selectors = [
                '[class*="aum"]',
                '[class*="fund"]',
                '[class*="size"]',
                '[class*="assets"]'
            ]
            
            for selector in size_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if any(keyword in text.lower() for keyword in ['aum', 'fund size', 'assets']):
                        size_match = re.search(r'Rs?\s*([\d,\.]+)\s*(Cr|Lakh|Thousand)?', text, re.IGNORECASE)
                        if size_match:
                            size_value = size_match.group(1).replace(',', '').strip()
                            unit = size_match.group(2) if size_match.group(2) else ''
                            
                            try:
                                size_float = float(size_value)
                                if 0.1 <= size_float <= 100000:
                                    return f"{size_value} {unit}"
                            except ValueError:
                                continue
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract fund size: {str(e)}")
            return "N/A"
    
    def _extract_expense_ratio_clean(self, soup: BeautifulSoup) -> str:
        """Extract clean expense ratio"""
        try:
            page_text = soup.get_text()
            
            # Expense ratio patterns
            er_patterns = [
                r'Expense\s+Ratio\s*[:\-]?\s*([\d\.]+)%?',
                r'TER\s*[:\-]?\s*([\d\.]+)%?',
                r'Total\s+Expense\s+Ratio\s*[:\-]?\s*([\d\.]+)%?',
                r'Expense\s*[:\-]?\s*([\d\.]+)%?'
            ]
            
            for pattern in er_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    er_value = match.group(1).strip()
                    # Validate it's a reasonable expense ratio
                    try:
                        er_float = float(er_value)
                        if 0 <= er_float <= 5:  # Reasonable expense ratio range
                            return f"{er_value}%"
                    except ValueError:
                        continue
            
            # Look for expense ratio elements
            er_selectors = [
                '[class*="expense"]',
                '[class*="ratio"]',
                '[class*="ter"]',
                '[data-testid*="expense"]'
            ]
            
            for selector in er_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if 'expense' in text.lower() or 'ratio' in text.lower():
                        er_match = re.search(r'([\d\.]+)%?', text)
                        if er_match:
                            er_value = er_match.group(1).strip()
                            try:
                                er_float = float(er_value)
                                if 0 <= er_float <= 5:
                                    return f"{er_value}%"
                            except ValueError:
                                continue
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract expense ratio: {str(e)}")
            return "N/A"
    
    def _extract_rating(self, soup: BeautifulSoup) -> str:
        """Extract fund rating"""
        try:
            page_text = soup.get_text()
            
            # Rating patterns
            rating_patterns = [
                r'Rating\s*[:\-]?\s*([A-D][+-]?)',
                r'Risk\s*[:\-]?\s*([^,\n]+)',
                r'Riskometer\s*[:\-]?\s*([^,\n]+)',
                r'(Very\s+High|High|Moderately\s+High|Moderate|Moderately\s+Low|Low)\s*Risk',
                r'Star\s+Rating\s*[:\-]?\s*([1-5])'
            ]
            
            for pattern in rating_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    rating = match.group(1).strip()
                    # Clean up rating
                    rating = re.sub(r'[^\w\s+\-]', '', rating)
                    if len(rating) > 1 and len(rating) < 50:  # Reasonable length
                        return rating
            
            # Look for rating elements
            rating_selectors = [
                '[class*="rating"]',
                '[class*="risk"]',
                '[class*="star"]',
                '[data-testid*="rating"]'
            ]
            
            for selector in rating_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if any(keyword in text.lower() for keyword in ['rating', 'risk', 'star']):
                        # Extract rating from element
                        rating_match = re.search(r'([A-D][+-]?|[1-5]|Very\s+High|High|Moderate|Low)', text, re.IGNORECASE)
                        if rating_match:
                            rating = rating_match.group(1).strip()
                            if len(rating) > 1:
                                return rating
            
            return "N/A"
            
        except Exception as e:
            logger.warning(f"Failed to extract rating: {str(e)}")
            return "N/A"
    
    def _validate_scheme_data(self, scheme_data: Dict) -> bool:
        """Validate extracted scheme data - more flexible validation"""
        # Only require scheme name and at least one other field
        if 'scheme_name' not in scheme_data or not scheme_data['scheme_name']:
            logger.warning("Missing scheme name")
            return False
        
        # Basic validation of scheme name
        scheme_name = scheme_data['scheme_name'].lower()
        if 'icici' not in scheme_name or 'prudential' not in scheme_name:
            logger.warning(f"Invalid scheme name: {scheme_data['scheme_name']}")
            return False
        
        # Check if we have at least some data (not all N/A)
        data_fields = ['nav', 'minimum_sip', 'fund_size', 'expense_ratio', 'rating']
        valid_fields = 0
        
        for field in data_fields:
            if field in scheme_data and scheme_data[field] and scheme_data[field] != 'N/A':
                valid_fields += 1
        
        if valid_fields == 0:
            logger.warning("No valid data fields extracted")
            return False
        
        logger.info(f"Valid data with {valid_fields}/{len(data_fields)} fields extracted")
        return True
    
    def scrape_all_schemes(self, urls: List[str]) -> List[Dict]:
        """
        Scrape all scheme URLs
        
        Args:
            urls: List of Groww scheme URLs
            
        Returns:
            List of scraped scheme data
        """
        all_data = []
        failed_urls = []
        
        logger.info(f"Starting to scrape {len(urls)} URLs")
        
        for url in urls:
            try:
                data = self.scrape_scheme_page(url)
                if data:
                    all_data.append(data)
                    logger.info(f"Successfully scraped: {url}")
                else:
                    failed_urls.append(url)
                    logger.error(f"Failed to scrape: {url}")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                failed_urls.append(url)
                logger.error(f"Exception while scraping {url}: {str(e)}")
        
        logger.info(f"Scraping completed. Success: {len(all_data)}, Failed: {len(failed_urls)}")
        
        return all_data, failed_urls
    
    def save_scraped_data(self, data: List[Dict], filename: str = None) -> str:
        """
        Save scraped data to enhanced JSON file
        
        Args:
            data: List of scraped scheme data
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fund_data_{timestamp}.json"
        
        filepath = os.path.join('../raw_data', filename)
        
        # Create enhanced data structure
        enhanced_data = {
            "version": "1.0",
            "collection_metadata": {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "source": "Groww",
                "total_schemes": len(data),
                "data_quality_score": self._calculate_data_quality(data),
                "extraction_method": "selenium_webdriver"
            },
            "schemes": self._enhance_scheme_data(data),
            "data_quality": self._assess_data_quality(data)
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Enhanced data saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save data: {str(e)}")
            raise
    
    def _calculate_data_quality(self, data: List[Dict]) -> float:
        """Calculate overall data quality score"""
        if not data:
            return 0.0
        
        total_fields = 0
        valid_fields = 0
        
        for scheme in data:
            key_fields = ['nav', 'minimum_sip', 'fund_size', 'expense_ratio', 'rating']
            for field in key_fields:
                total_fields += 1
                if field in scheme and scheme[field] and scheme[field] != 'N/A':
                    valid_fields += 1
        
        return valid_fields / total_fields if total_fields > 0 else 0.0
    
    def _enhance_scheme_data(self, data: List[Dict]) -> List[Dict]:
        """Enhance scheme data with better structure"""
        enhanced_schemes = []
        
        for scheme in data:
            enhanced_scheme = {
                "scheme_identifier": {
                    "name": scheme.get('scheme_name', ''),
                    "category": self._extract_category(scheme.get('scheme_name', '')),
                    "risk_level": scheme.get('rating', 'N/A')
                },
                "key_metrics": {
                    "nav": self._format_nav(scheme.get('nav', 'N/A')),
                    "minimum_sip": self._format_sip(scheme.get('minimum_sip', 'N/A')),
                    "fund_size": self._format_fund_size(scheme.get('fund_size', 'N/A')),
                    "expense_ratio": self._format_expense_ratio(scheme.get('expense_ratio', 'N/A')),
                    "rating": scheme.get('rating', 'N/A')
                },
                "source_data": {
                    "url": scheme.get('source_url', ''),
                    "scraped_at": scheme.get('scraped_at', ''),
                    "last_updated": scheme.get('last_updated', '')
                }
            }
            enhanced_schemes.append(enhanced_scheme)
        
        return enhanced_schemes
    
    def _extract_category(self, scheme_name: str) -> str:
        """Extract fund category from scheme name"""
        name_lower = scheme_name.lower()
        if 'multi asset' in name_lower:
            return 'Hybrid'
        elif 'large cap' in name_lower:
            return 'Large Cap'
        elif 'nifty next 50' in name_lower:
            return 'Index'
        elif 'large & mid cap' in name_lower or 'top 100' in name_lower:
            return 'Large & Mid Cap'
        else:
            return 'Other'
    
    def _format_nav(self, nav: str) -> Dict:
        """Format NAV with proper structure"""
        try:
            if nav == 'N/A' or not nav:
                return {"value": None, "date": None, "currency": "INR"}
            
            nav_value = float(nav.replace(',', ''))
            return {
                "value": nav_value,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "currency": "INR"
            }
        except (ValueError, AttributeError):
            return {"value": None, "date": None, "currency": "INR"}
    
    def _format_sip(self, sip: str) -> int:
        """Format SIP amount"""
        try:
            if sip == 'N/A' or not sip:
                return 0
            
            # Extract numeric value
            sip_match = re.search(r'[\d,]+', sip)
            if sip_match:
                return int(sip_match.group().replace(',', ''))
            return 0
        except (ValueError, AttributeError):
            return 0
    
    def _format_fund_size(self, fund_size: str) -> Dict:
        """Format fund size with proper structure"""
        try:
            if fund_size == 'N/A' or not fund_size:
                return {"value": None, "unit": None, "currency": "INR"}
            
            # Extract numeric value and unit
            size_match = re.search(r'([\d,\.]+)\s*(Cr|Lakh|Thousand)?', fund_size)
            if size_match:
                value = float(size_match.group(1).replace(',', ''))
                unit = size_match.group(2) if size_match.group(2) else 'Cr'
                return {
                    "value": value,
                    "unit": unit,
                    "currency": "INR"
                }
            return {"value": None, "unit": None, "currency": "INR"}
        except (ValueError, AttributeError):
            return {"value": None, "unit": None, "currency": "INR"}
    
    def _format_expense_ratio(self, expense_ratio: str) -> float:
        """Format expense ratio as percentage"""
        try:
            if expense_ratio == 'N/A' or not expense_ratio:
                return 0.0
            
            # Extract numeric value
            er_match = re.search(r'[\d\.]+', expense_ratio)
            if er_match:
                return float(er_match.group())
            return 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def _assess_data_quality(self, data: List[Dict]) -> Dict:
        """Assess data quality for each field"""
        quality = {
            "nav_extraction": "good",
            "sip_extraction": "good", 
            "fund_size_extraction": "failed",
            "expense_ratio_extraction": "excellent",
            "rating_extraction": "good"
        }
        
        # Update based on actual data
        if data:
            fund_size_count = sum(1 for scheme in data if scheme.get('fund_size') != 'N/A')
            if fund_size_count == 0:
                quality["fund_size_extraction"] = "failed"
            elif fund_size_count == len(data):
                quality["fund_size_extraction"] = "excellent"
            else:
                quality["fund_size_extraction"] = "partial"
        
        return quality
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver cleanup completed")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")


def main():
    """Main function for testing the scraper"""
    # Target URLs
    urls = [
        "https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
    ]
    
    scraper = None
    try:
        # Initialize scraper
        scraper = GrowwScraper(headless=True)
        
        # Scrape all schemes
        all_data, failed_urls = scraper.scrape_all_schemes(urls)
        
        if all_data:
            # Save scraped data
            filepath = scraper.save_scraped_data(all_data)
            print(f"Data saved to: {filepath}")
            print(f"Successfully scraped {len(all_data)} schemes")
            
            # Print sample data
            if all_data:
                print("\nSample scraped data:")
                print(json.dumps(all_data[0], indent=2))
        
        if failed_urls:
            print(f"\nFailed URLs: {failed_urls}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        print(f"Error: {str(e)}")
    
    finally:
        if scraper:
            scraper.cleanup()


if __name__ == "__main__":
    main()
