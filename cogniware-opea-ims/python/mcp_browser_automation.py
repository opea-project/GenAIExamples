"""
Cogniware Core - MCP Browser Automation & RPA
Chrome automation, screen capture, RPA capabilities
"""

import os
import time
import base64
from pathlib import Path
from typing import Optional, Dict, List

# Try to import selenium, install if not available
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class BrowserAutomation:
    """Chrome browser automation and RPA capabilities"""
    
    def __init__(self):
        self.driver = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
    
    def _ensure_driver(self):
        """Ensure browser driver is initialized"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not installed. Run: pip install selenium")
        
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                # Try without headless if it fails
                chrome_options = Options()
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                self.driver = webdriver.Chrome(options=chrome_options)
    
    def navigate_to(self, url: str) -> dict:
        """Navigate to URL"""
        try:
            self._ensure_driver()
            self.driver.get(url)
            time.sleep(2)  # Wait for page load
            
            return {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def take_screenshot(self, filename: str = None) -> dict:
        """Take screenshot of current page"""
        try:
            self._ensure_driver()
            
            if filename is None:
                filename = f"screenshot_{int(time.time())}.png"
            
            filepath = self.screenshots_dir / filename
            self.driver.save_screenshot(str(filepath))
            
            # Return base64 encoded image for display in browser
            with open(filepath, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "image_base64": image_data  # Full base64 for browser display
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def click_element(self, selector: str, by: str = "css") -> dict:
        """Click element by selector"""
        try:
            self._ensure_driver()
            
            by_method = By.CSS_SELECTOR if by == "css" else By.XPATH
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by_method, selector))
            )
            element.click()
            
            return {
                "success": True,
                "selector": selector,
                "action": "clicked"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fill_form(self, selector: str, value: str, by: str = "css") -> dict:
        """Fill form field"""
        try:
            self._ensure_driver()
            
            by_method = By.CSS_SELECTOR if by == "css" else By.XPATH
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((by_method, selector))
            )
            element.clear()
            element.send_keys(value)
            
            return {
                "success": True,
                "selector": selector,
                "action": "filled",
                "value_length": len(value)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_text(self, selector: str, by: str = "css") -> dict:
        """Extract text from element"""
        try:
            self._ensure_driver()
            
            by_method = By.CSS_SELECTOR if by == "css" else By.XPATH
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((by_method, selector))
            )
            text = element.text
            
            return {
                "success": True,
                "selector": selector,
                "text": text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_table(self, table_selector: str) -> dict:
        """Extract data from HTML table"""
        try:
            self._ensure_driver()
            
            table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
            )
            
            # Extract headers
            headers = []
            header_elements = table.find_elements(By.CSS_SELECTOR, "thead th, thead td")
            for header in header_elements:
                headers.append(header.text)
            
            # Extract rows
            rows = []
            row_elements = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            for row_element in row_elements:
                cells = row_element.find_elements(By.TAG_NAME, "td")
                row_data = [cell.text for cell in cells]
                rows.append(row_data)
            
            return {
                "success": True,
                "headers": headers,
                "rows": rows,
                "row_count": len(rows)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_script(self, script: str) -> dict:
        """Execute JavaScript on page"""
        try:
            self._ensure_driver()
            result = self.driver.execute_script(script)
            
            return {
                "success": True,
                "result": str(result)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def scroll_page(self, direction: str = "down", amount: int = 500) -> dict:
        """Scroll page"""
        try:
            self._ensure_driver()
            
            if direction == "down":
                self.driver.execute_script(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                self.driver.execute_script(f"window.scrollBy(0, -{amount})")
            elif direction == "bottom":
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            elif direction == "top":
                self.driver.execute_script("window.scrollTo(0, 0)")
            
            return {
                "success": True,
                "direction": direction,
                "amount": amount
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def wait_for_element(self, selector: str, timeout: int = 10) -> dict:
        """Wait for element to appear"""
        try:
            self._ensure_driver()
            
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            return {
                "success": True,
                "selector": selector,
                "found": True,
                "text": element.text[:100]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_page_source(self) -> dict:
        """Get HTML source of current page"""
        try:
            self._ensure_driver()
            source = self.driver.page_source
            
            return {
                "success": True,
                "html": source[:1000] + "...",  # Truncate for response
                "length": len(source)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_cookies(self) -> dict:
        """Get browser cookies"""
        try:
            self._ensure_driver()
            cookies = self.driver.get_cookies()
            
            return {
                "success": True,
                "cookies": cookies,
                "count": len(cookies)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_cookie(self, name: str, value: str, domain: str = None) -> dict:
        """Set browser cookie"""
        try:
            self._ensure_driver()
            
            cookie = {'name': name, 'value': value}
            if domain:
                cookie['domain'] = domain
            
            self.driver.add_cookie(cookie)
            
            return {
                "success": True,
                "cookie_name": name
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close_browser(self) -> dict:
        """Close browser"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            return {"success": True, "action": "browser_closed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # RPA WORKFLOWS
    # =========================================================================
    
    def rpa_login_workflow(self, url: str, username_selector: str, 
                           password_selector: str, submit_selector: str,
                           username: str, password: str) -> dict:
        """RPA: Automated login workflow"""
        try:
            self._ensure_driver()
            
            # Navigate to login page
            self.driver.get(url)
            time.sleep(2)
            
            # Fill username
            username_field = self.driver.find_element(By.CSS_SELECTOR, username_selector)
            username_field.send_keys(username)
            
            # Fill password
            password_field = self.driver.find_element(By.CSS_SELECTOR, password_selector)
            password_field.send_keys(password)
            
            # Submit
            submit_button = self.driver.find_element(By.CSS_SELECTOR, submit_selector)
            submit_button.click()
            
            time.sleep(3)  # Wait for login
            
            return {
                "success": True,
                "workflow": "login",
                "current_url": self.driver.current_url,
                "title": self.driver.title
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def rpa_form_fill_workflow(self, form_data: dict) -> dict:
        """RPA: Fill multiple form fields"""
        try:
            self._ensure_driver()
            
            results = []
            for selector, value in form_data.items():
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.clear()
                element.send_keys(value)
                results.append({"selector": selector, "status": "filled"})
            
            return {
                "success": True,
                "workflow": "form_fill",
                "fields_filled": len(results),
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def rpa_data_extraction_workflow(self, url: str, selectors: list) -> dict:
        """RPA: Navigate and extract multiple data points"""
        try:
            self._ensure_driver()
            
            # Navigate
            self.driver.get(url)
            time.sleep(2)
            
            # Extract data from each selector
            extracted_data = {}
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    extracted_data[selector] = element.text
                except:
                    extracted_data[selector] = None
            
            return {
                "success": True,
                "workflow": "data_extraction",
                "url": url,
                "data": extracted_data,
                "items_extracted": len([v for v in extracted_data.values() if v])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def rpa_screenshot_workflow(self, urls: list) -> dict:
        """RPA: Take screenshots of multiple pages"""
        try:
            self._ensure_driver()
            
            screenshots = []
            for url in urls:
                self.driver.get(url)
                time.sleep(2)
                
                filename = f"screenshot_{url.replace('://', '_').replace('/', '_')}_{int(time.time())}.png"
                filepath = self.screenshots_dir / filename
                self.driver.save_screenshot(str(filepath))
                
                screenshots.append({
                    "url": url,
                    "filename": filename,
                    "filepath": str(filepath)
                })
            
            return {
                "success": True,
                "workflow": "screenshot_batch",
                "screenshots": screenshots,
                "count": len(screenshots)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global browser automation instance
browser_automation = BrowserAutomation()

