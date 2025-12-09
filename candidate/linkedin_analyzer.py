"""
LinkedIn profile scraper to extract professional experience and network data.
Note: This uses web scraping as LinkedIn API is restricted. Use responsibly.
"""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth

from config.config_manager import get_config


class LinkedInAnalyzer:
    """
    Analyze LinkedIn profile (with ethical scraping practices).
    
    Note: LinkedIn's Terms of Service restrict automated scraping.
    This is for personal use only. Consider using LinkedIn API when available.
    """
    
    def __init__(self, profile_url: Optional[str] = None):
        """
        Initialize LinkedIn analyzer.
        
        Args:
            profile_url: LinkedIn profile URL. If None, uses config.
        """
        config = get_config()
        self.profile_url = profile_url or config.candidate_profile.links.linkedin
        
        self.driver: Optional[webdriver.Chrome] = None
        self.profile_data: Optional[Dict[str, Any]] = None
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Selenium driver with stealth mode."""
        options = webdriver.ChromeOptions()
        
        # Stealth settings
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Use headless for automation
        # options.add_argument('--headless')  # Uncomment for headless mode
        
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
        
        return driver
    
    def analyze(self, login_email: Optional[str] = None, login_password: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze LinkedIn profile.
        
        Args:
            login_email: LinkedIn login email
            login_password: LinkedIn login password
            
        Returns:
            Profile analysis data
            
        Note: For public profiles, login may not be required.
        """
        logger.info(f"Analyzing LinkedIn profile: {self.profile_url}")
        
        try:
            self.driver = self._setup_driver()
            
            # If credentials provided, login first
            if login_email and login_password:
                self._login(login_email, login_password)
                time.sleep(3)
            
            # Navigate to profile
            self.driver.get(self.profile_url)
            time.sleep(3)
            
            # Extract data
            self.profile_data = {
                "basic_info": self._extract_basic_info(),
                "experience": self._extract_experience(),
                "education": self._extract_education(),
                "skills": self._extract_skills(),
                "certifications": self._extract_certifications(),
                "recommendations": self._extract_recommendations(),
            }
            
            logger.info("LinkedIn profile analysis completed")
            return self.profile_data
        
        except Exception as e:
            logger.error(f"LinkedIn analysis failed: {e}")
            raise
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def _login(self, email: str, password: str) -> None:
        """Login to LinkedIn."""
        logger.info("Logging into LinkedIn...")
        
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        # Find and fill email
        email_field = self.driver.find_element(By.ID, "username")
        email_field.send_keys(email)
        
        # Find and fill password
        password_field = self.driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        
        # Click sign in
        sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        sign_in_button.click()
        
        time.sleep(5)
        
        # Check for CAPTCHA or 2FA (manual intervention may be needed)
        if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
            logger.warning("CAPTCHA or 2FA detected. Manual intervention required.")
            input("Press Enter after completing verification...")
    
    def _extract_basic_info(self) -> Dict[str, str]:
        """Extract basic profile information."""
        basic_info = {
            "name": "",
            "headline": "",
            "location": "",
            "connections": "",
        }
        
        try:
            # Name
            name_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge")
            basic_info["name"] = name_elem.text if name_elem else ""
            
            # Headline
            headline_elem = self.driver.find_element(By.CSS_SELECTOR, "div.text-body-medium")
            basic_info["headline"] = headline_elem.text if headline_elem else ""
            
            # Location
            location_elem = self.driver.find_element(By.CSS_SELECTOR, "span.text-body-small.inline")
            basic_info["location"] = location_elem.text if location_elem else ""
            
        except Exception as e:
            logger.warning(f"Failed to extract basic info: {e}")
        
        return basic_info
    
    def _extract_experience(self) -> List[Dict[str, Any]]:
        """Extract work experience."""
        experience = []
        
        try:
            # Scroll to experience section
            self.driver.execute_script("window.scrollTo(0, 800)")
            time.sleep(1)
            
            # Find experience section
            exp_section = self.driver.find_element(By.ID, "experience")
            
            # Find all experience items
            exp_items = exp_section.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")
            
            for item in exp_items:
                try:
                    exp_data = {
                        "title": "",
                        "company": "",
                        "duration": "",
                        "location": "",
                        "description": "",
                    }
                    
                    # Extract title
                    title_elem = item.find_element(By.CSS_SELECTOR, "div[class*='display-flex'] span[aria-hidden='true']")
                    exp_data["title"] = title_elem.text if title_elem else ""
                    
                    # Extract company
                    company_elem = item.find_element(By.CSS_SELECTOR, "span.t-14.t-normal span[aria-hidden='true']")
                    exp_data["company"] = company_elem.text if company_elem else ""
                    
                    # Extract duration
                    duration_elem = item.find_element(By.CSS_SELECTOR, "span.t-14.t-normal.t-black--light span[aria-hidden='true']")
                    exp_data["duration"] = duration_elem.text if duration_elem else ""
                    
                    experience.append(exp_data)
                
                except Exception as e:
                    logger.debug(f"Failed to extract experience item: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to extract experience: {e}")
        
        return experience
    
    def _extract_education(self) -> List[Dict[str, str]]:
        """Extract education information."""
        education = []
        
        try:
            # Scroll to education section
            self.driver.execute_script("window.scrollTo(0, 1200)")
            time.sleep(1)
            
            edu_section = self.driver.find_element(By.ID, "education")
            edu_items = edu_section.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")
            
            for item in edu_items:
                try:
                    edu_data = {
                        "school": "",
                        "degree": "",
                        "field": "",
                        "dates": "",
                    }
                    
                    # Extract school name
                    school_elem = item.find_element(By.CSS_SELECTOR, "div[class*='display-flex'] span[aria-hidden='true']")
                    edu_data["school"] = school_elem.text if school_elem else ""
                    
                    # Extract degree and field
                    degree_elem = item.find_element(By.CSS_SELECTOR, "span.t-14.t-normal span[aria-hidden='true']")
                    edu_data["degree"] = degree_elem.text if degree_elem else ""
                    
                    education.append(edu_data)
                
                except Exception as e:
                    logger.debug(f"Failed to extract education item: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to extract education: {e}")
        
        return education
    
    def _extract_skills(self) -> List[str]:
        """Extract skills."""
        skills = []
        
        try:
            # Scroll to skills section
            self.driver.execute_script("window.scrollTo(0, 1600)")
            time.sleep(1)
            
            skills_section = self.driver.find_element(By.ID, "skills")
            
            # Click "Show all skills" if available
            try:
                show_all_btn = skills_section.find_element(By.CSS_SELECTOR, "a[aria-label*='Show all']")
                show_all_btn.click()
                time.sleep(2)
            except:
                pass
            
            # Extract skill names
            skill_items = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='skill-name']")
            
            for item in skill_items:
                skill_name = item.text.strip()
                if skill_name:
                    skills.append(skill_name)
        
        except Exception as e:
            logger.warning(f"Failed to extract skills: {e}")
        
        return skills
    
    def _extract_certifications(self) -> List[Dict[str, str]]:
        """Extract certifications."""
        certifications = []
        
        try:
            # Scroll to certifications section
            self.driver.execute_script("window.scrollTo(0, 2000)")
            time.sleep(1)
            
            cert_section = self.driver.find_element(By.ID, "licenses_and_certifications")
            cert_items = cert_section.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")
            
            for item in cert_items:
                try:
                    cert_data = {
                        "name": "",
                        "issuer": "",
                        "date": "",
                    }
                    
                    # Extract certification name
                    name_elem = item.find_element(By.CSS_SELECTOR, "div[class*='display-flex'] span[aria-hidden='true']")
                    cert_data["name"] = name_elem.text if name_elem else ""
                    
                    # Extract issuer
                    issuer_elem = item.find_element(By.CSS_SELECTOR, "span.t-14.t-normal span[aria-hidden='true']")
                    cert_data["issuer"] = issuer_elem.text if issuer_elem else ""
                    
                    certifications.append(cert_data)
                
                except Exception as e:
                    logger.debug(f"Failed to extract certification item: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to extract certifications: {e}")
        
        return certifications
    
    def _extract_recommendations(self) -> List[Dict[str, str]]:
        """Extract recommendations count."""
        recommendations = {"count": 0, "samples": []}
        
        try:
            # Scroll to recommendations section
            self.driver.execute_script("window.scrollTo(0, 2400)")
            time.sleep(1)
            
            rec_section = self.driver.find_element(By.ID, "recommendations")
            rec_items = rec_section.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")
            
            recommendations["count"] = len(rec_items)
            
            # Extract first 3 recommendations
            for item in rec_items[:3]:
                try:
                    rec_text = item.find_element(By.CSS_SELECTOR, "div[class*='display-flex']").text
                    recommendations["samples"].append(rec_text)
                except:
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to extract recommendations: {e}")
        
        return recommendations
    
    def get_summary(self) -> str:
        """
        Get text summary of LinkedIn profile.
        
        Returns:
            Summary string
        """
        if not self.profile_data:
            logger.warning("Profile data not available. Call analyze() first.")
            return ""
        
        basic = self.profile_data["basic_info"]
        exp_count = len(self.profile_data["experience"])
        skills_count = len(self.profile_data["skills"])
        
        summary = (
            f"LinkedIn: {basic.get('name', 'N/A')} | "
            f"{basic.get('headline', 'N/A')} | "
            f"{exp_count} experiences | "
            f"{skills_count} skills"
        )
        
        return summary


def analyze_linkedin_profile(profile_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze LinkedIn profile.
    
    Args:
        profile_url: LinkedIn profile URL
        
    Returns:
        LinkedIn profile analysis
        
    Note: May require manual login for private profiles.
    """
    analyzer = LinkedInAnalyzer(profile_url)
    
    # Check if credentials are available
    import os
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if email and password:
        return analyzer.analyze(email, password)
    else:
        logger.warning("LinkedIn credentials not found. Attempting to access public profile...")
        return analyzer.analyze()
