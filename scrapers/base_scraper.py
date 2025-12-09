"""
Base scraper with anti-detection measures, rate limiting, and error handling.
"""

import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth
from tenacity import retry, stop_after_attempt, wait_exponential

from config.config_manager import get_config


class BaseScraper(ABC):
    """
    Abstract base class for web scrapers with anti-detection features.
    """
    
    def __init__(self, headless: bool = True, use_proxy: bool = False):
        """
        Initialize base scraper.
        
        Args:
            headless: Run browser in headless mode
            use_proxy: Use proxy for requests
        """
        self.config = get_config()
        self.headless = headless
        self.use_proxy = use_proxy
        
        # User agent rotation
        self.ua = UserAgent()
        
        # Rate limiting
        self.scraping_config = self.config.settings.scraping
        self.min_delay = self.scraping_config["delays"]["min"]
        self.max_delay = self.scraping_config["delays"]["max"]
        self.between_pages_delay = self.scraping_config["delays"]["between_pages"]
        
        # Session management
        self.session = requests.Session()
        self.driver: Optional[webdriver.Chrome] = None
        
        # Proxy setup
        self.proxy = self._get_proxy() if use_proxy else None
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration from environment."""
        proxy_url = self.config.env.get("PROXY_URL")
        if not proxy_url:
            return None
        
        return {
            "http": proxy_url,
            "https": proxy_url,
        }
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent."""
        user_agents = self.scraping_config.get("user_agents", [])
        if user_agents:
            return random.choice(user_agents)
        return self.ua.random
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Selenium Chrome driver with stealth mode."""
        options = ChromeOptions()
        
        # Basic options
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance
        if self.scraping_config.get("stealth_mode", {}).get("disable_images", True):
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
        
        # Random user agent
        options.add_argument(f'user-agent={self._get_random_user_agent()}')
        
        # Proxy
        if self.proxy and self.proxy.get("http"):
            proxy_url = self.proxy["http"]
            options.add_argument(f'--proxy-server={proxy_url}')
        
        # Create driver
        driver = webdriver.Chrome(options=options)
        
        # Apply stealth
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
        )
        
        # Set timeouts
        driver.set_page_load_timeout(self.scraping_config.get("timeout", 30))
        
        return driver
    
    def get_driver(self) -> webdriver.Chrome:
        """Get or create Selenium driver."""
        if self.driver is None:
            self.driver = self._setup_driver()
        return self.driver
    
    def close_driver(self) -> None:
        """Close Selenium driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_page(self, url: str, use_selenium: bool = False) -> Optional[str]:
        """
        Get page content with retry logic.
        
        Args:
            url: URL to fetch
            use_selenium: Use Selenium instead of requests
            
        Returns:
            Page HTML content or None
        """
        logger.debug(f"Fetching: {url}")
        
        # Random delay to avoid detection
        self._random_delay()
        
        try:
            if use_selenium:
                return self._get_page_selenium(url)
            else:
                return self._get_page_requests(url)
        
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise
    
    def _get_page_requests(self, url: str) -> Optional[str]:
        """Fetch page using requests."""
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = self.session.get(
            url,
            headers=headers,
            proxies=self.proxy,
            timeout=self.scraping_config.get("timeout", 30),
        )
        
        response.raise_for_status()
        return response.text
    
    def _get_page_selenium(self, url: str) -> Optional[str]:
        """Fetch page using Selenium."""
        driver = self.get_driver()
        driver.get(url)
        
        # Random human-like delay
        time.sleep(random.uniform(1, 3))
        
        # Scroll to load dynamic content
        self._random_scroll(driver)
        
        return driver.page_source
    
    def _random_delay(self) -> None:
        """Add random delay between requests."""
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def _random_scroll(self, driver: webdriver.Chrome) -> None:
        """Perform random scrolling to mimic human behavior."""
        # Scroll down gradually
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        
        while current_position < scroll_height:
            # Random scroll amount
            scroll_amount = random.randint(300, 700)
            current_position += scroll_amount
            
            driver.execute_script(f"window.scrollTo(0, {current_position})")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Update scroll height (for dynamic pages)
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            
            # Stop after a few scrolls
            if current_position > 3000:
                break
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content.
        
        Args:
            html: HTML string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'lxml')
    
    def wait_for_element(self, 
                        by: By, 
                        value: str, 
                        timeout: int = 10) -> Any:
        """
        Wait for element to be present.
        
        Args:
            by: Selenium By locator
            value: Locator value
            timeout: Maximum wait time
            
        Returns:
            WebElement
        """
        driver = self.get_driver()
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    
    def click_with_retry(self, element, max_attempts: int = 3) -> bool:
        """
        Click element with retry logic.
        
        Args:
            element: WebElement to click
            max_attempts: Maximum number of attempts
            
        Returns:
            True if successful
        """
        for attempt in range(max_attempts):
            try:
                element.click()
                return True
            except Exception as e:
                logger.debug(f"Click attempt {attempt + 1} failed: {e}")
                time.sleep(0.5)
        
        return False
    
    def handle_captcha(self) -> None:
        """
        Handle CAPTCHA detection.
        Override in subclasses for specific CAPTCHA handling.
        """
        logger.warning("CAPTCHA detected. Manual intervention may be required.")
        
        if self.driver and "captcha" in self.driver.current_url.lower():
            logger.warning("CAPTCHA page detected. Waiting for manual resolution...")
            input("Press Enter after solving CAPTCHA...")
    
    def is_rate_limited(self, html: str) -> bool:
        """
        Check if rate limited or blocked.
        
        Args:
            html: Page HTML
            
        Returns:
            True if rate limited
        """
        rate_limit_indicators = [
            "too many requests",
            "rate limit",
            "try again later",
            "access denied",
            "blocked",
            "captcha",
        ]
        
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in rate_limit_indicators)
    
    def save_page(self, html: str, filename: str) -> None:
        """
        Save page HTML for debugging.
        
        Args:
            html: HTML content
            filename: Output filename
        """
        from pathlib import Path
        
        debug_dir = Path("debug/pages")
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = debug_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.debug(f"Saved page to {filepath}")
    
    @abstractmethod
    def scrape(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Main scraping method to be implemented by subclasses.
        
        Returns:
            List of scraped items
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_driver()
        self.session.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close_driver()
