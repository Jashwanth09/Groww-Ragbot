from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

def scrape_live_fund_data():
    """Scrape live fund data from Groww website with better selectors"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    # Fund URLs
    funds = {
        'Large Cap': 'https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth',
        'Nifty Next 50': 'https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth',
        'Multi Asset': 'https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth',
        'Top 100': 'https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth'
    }

    results = {}

    for fund_name, url in funds.items():
        try:
            print(f'Scraping {fund_name}...')
            driver.get(url)
            time.sleep(5)
            
            # Try multiple selectors for NAV
            nav_text = None
            selectors = [
                '//span[contains(text(), "NAV")]',
                '//div[contains(@class, "nav")]//span',
                '//div[contains(text(), "NAV")]',
                '//*[contains(text(), "NAV")]',
                '//span[contains(text(), "₹")]',
                '//*[contains(text(), "₹")]'
            ]
            
            for selector in selectors:
                try:
                    nav_element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    nav_text = nav_element.text
                    print(f'Found NAV text with selector {selector}: {nav_text[:100]}...')
                    break
                except:
                    continue
            
            if nav_text:
                # Extract NAV value and date
                nav_match = re.search(r'₹\s*([\d,\.]+)', nav_text)
                date_match = re.search(r'(\d{2}-\d{2}-\d{4})', nav_text)
                
                nav_value = nav_match.group(1) if nav_match else 'N/A'
                nav_date = date_match.group(1) if date_match else '05-05-2026'
                
                results[fund_name] = {
                    'nav': f'₹{nav_value}',
                    'date': nav_date,
                    'full_text': nav_text[:200]
                }
                print(f'{fund_name} NAV: ₹{nav_value} (as of {nav_date})')
            else:
                print(f'Could not find NAV for {fund_name}')
                results[fund_name] = {'nav': 'N/A', 'date': '05-05-2026', 'full_text': 'Not found'}
            
        except Exception as e:
            print(f'Error scraping {fund_name}: {e}')
            results[fund_name] = {'nav': 'N/A', 'date': '05-05-2026', 'full_text': str(e)}

    driver.quit()
    return results

if __name__ == "__main__":
    results = scrape_live_fund_data()
    print('\n=== FINAL RESULTS ===')
    for fund, data in results.items():
        print(f'{fund}: {data}')
