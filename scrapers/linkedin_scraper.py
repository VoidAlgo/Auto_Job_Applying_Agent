"""
LinkedIn job scraper with entry-level AI/ML role filters.
"""

import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from config.config_manager import get_config
from scrapers.base_scraper import BaseScraper


class LinkedInJobScraper(BaseScraper):
    """
    Scrape LinkedIn jobs with filters for entry-level AI/ML positions.
    
    Note: LinkedIn has strict anti-bot measures. Use responsibly.
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize LinkedIn job scraper.
        
        Args:
            headless: Run browser in headless mode
        """
        super().__init__(headless=headless, use_proxy=False)
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.config = get_config()
        self.job_criteria = self.config.settings.job_criteria
        self.linkedin_config = self.config.settings.job_boards.get("linkedin", {})
    
    def scrape(self,
              keywords: Optional[List[str]] = None,
              location: Optional[str] = None,
              max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape LinkedIn jobs.
        
        Args:
            keywords: Search keywords (defaults to config target roles)
            location: Location filter
            max_results: Maximum number of jobs to scrape
            
        Returns:
            List of job dictionaries
        """
        logger.info("Starting LinkedIn job scraping...")
        
        # Default keywords from config
        if keywords is None:
            keywords = self.job_criteria["target_roles"][:3]  # Top 3 roles
        
        # Default location
        if location is None:
            location = self.config.candidate_profile.preferences.locations.get("primary", ["Remote"])[0]
        
        all_jobs = []
        
        for keyword in keywords:
            try:
                logger.info(f"Searching for: {keyword} in {location}")
                jobs = self._search_jobs(keyword, location, max_results // len(keywords))
                all_jobs.extend(jobs)
                
                # Delay between different searches
                time.sleep(self.between_pages_delay)
            
            except Exception as e:
                logger.error(f"Failed to scrape jobs for {keyword}: {e}")
                continue
        
        logger.info(f"Scraped {len(all_jobs)} jobs from LinkedIn")
        return all_jobs
    
    def _search_jobs(self, keyword: str, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Search for jobs with specific keyword and location."""
        # Build search URL
        params = {
            "keywords": keyword,
            "location": location,
            "f_E": "2",  # Entry level (1=Internship, 2=Entry level, 3=Associate)
            "f_WT": "2",  # Remote (1=On-site, 2=Remote, 3=Hybrid)
            "f_TPR": "r604800",  # Past week (r86400=24h, r604800=7days, r2592000=30days)
            "sortBy": "DD",  # Date posted (DD=Most recent, R=Most relevant)
        }
        
        search_url = f"{self.base_url}?{urlencode(params)}"
        logger.debug(f"Search URL: {search_url}")
        
        # Get page with Selenium
        driver = self.get_driver()
        driver.get(search_url)
        
        # Wait for job cards to load
        time.sleep(5)
        
        jobs = []
        page = 1
        
        while len(jobs) < max_results:
            try:
                # Extract jobs from current page
                page_jobs = self._extract_jobs_from_page()
                
                if not page_jobs:
                    logger.info("No more jobs found")
                    break
                
                jobs.extend(page_jobs)
                logger.info(f"Page {page}: Found {len(page_jobs)} jobs (Total: {len(jobs)})")
                
                # Try to load more jobs (infinite scroll)
                if not self._load_more_jobs():
                    break
                
                page += 1
                time.sleep(self.between_pages_delay)
            
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                break
        
        return jobs[:max_results]
    
    def _extract_jobs_from_page(self) -> List[Dict[str, Any]]:
        """Extract job listings from current page."""
        driver = self.get_driver()
        jobs = []
        
        try:
            # Find all job cards
            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job-search-card")
            
            for card in job_cards:
                try:
                    job_data = self._parse_job_card(card)
                    
                    # Filter by experience level and keywords
                    if self._is_relevant_job(job_data):
                        jobs.append(job_data)
                
                except Exception as e:
                    logger.debug(f"Failed to parse job card: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to extract jobs: {e}")
        
        return jobs
    
    def _parse_job_card(self, card) -> Dict[str, Any]:
        """Parse individual job card."""
        job = {
            "title": "",
            "company": "",
            "location": "",
            "description": "",
            "url": "",
            "posted_date": "",
            "job_id": "",
            "source": "linkedin",
        }
        
        try:
            # Title
            title_elem = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title")
            job["title"] = title_elem.text.strip()
            
            # Company
            company_elem = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle")
            job["company"] = company_elem.text.strip()
            
            # Location
            location_elem = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location")
            job["location"] = location_elem.text.strip()
            
            # URL and Job ID
            link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
            job["url"] = link_elem.get_attribute("href")
            
            # Extract job ID from URL
            job_id_match = re.search(r'/jobs/view/(\d+)', job["url"])
            if job_id_match:
                job["job_id"] = job_id_match.group(1)
            
            # Posted date
            try:
                date_elem = card.find_element(By.CSS_SELECTOR, "time")
                job["posted_date"] = date_elem.get_attribute("datetime")
            except:
                pass
            
            # Get detailed description by clicking on job (optional)
            # This is commented out to avoid detection, enable if needed
            # job["description"] = self._get_job_description(job["url"])
        
        except Exception as e:
            logger.debug(f"Error parsing job card: {e}")
        
        return job
    
    def _get_job_description(self, job_url: str) -> str:
        """
        Get full job description.
        
        Args:
            job_url: Job detail URL
            
        Returns:
            Job description text
        """
        driver = self.get_driver()
        
        try:
            # Open job in new tab to avoid losing search results
            original_window = driver.current_window_handle
            driver.execute_script(f"window.open('{job_url}', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            
            time.sleep(3)
            
            # Extract description
            desc_elem = driver.find_element(By.CSS_SELECTOR, "div.show-more-less-html__markup")
            description = desc_elem.text
            
            # Close tab and switch back
            driver.close()
            driver.switch_to.window(original_window)
            
            return description
        
        except Exception as e:
            logger.debug(f"Failed to get job description: {e}")
            
            # Make sure we're back to original window
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
            return ""
    
    def _load_more_jobs(self) -> bool:
        """
        Scroll down to load more jobs.
        
        Returns:
            True if more jobs loaded
        """
        driver = self.get_driver()
        
        try:
            # Get current number of job cards
            before_count = len(driver.find_elements(By.CSS_SELECTOR, "div.job-search-card"))
            
            # Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Check for "See more jobs" button
            try:
                see_more_btn = driver.find_element(By.CSS_SELECTOR, "button.infinite-scroller__show-more-button")
                self.click_with_retry(see_more_btn)
                time.sleep(3)
            except:
                pass
            
            # Get new count
            after_count = len(driver.find_elements(By.CSS_SELECTOR, "div.job-search-card"))
            
            return after_count > before_count
        
        except Exception as e:
            logger.debug(f"Failed to load more jobs: {e}")
            return False
    
    def _is_relevant_job(self, job: Dict[str, Any]) -> bool:
        """
        Check if job is relevant based on filters.
        
        Args:
            job: Job dictionary
            
        Returns:
            True if relevant
        """
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        combined = f"{title} {description}"
        
        # Check for excluded keywords (senior, lead, etc.)
        excluded_keywords = self.job_criteria.get("excluded_keywords", [])
        if any(keyword.lower() in combined for keyword in excluded_keywords):
            logger.debug(f"Excluded: {job['title']} (contains excluded keyword)")
            return False
        
        # Check for required keywords
        required_keywords = self.job_criteria.get("keywords", {}).get("required", [])
        if required_keywords:
            if not any(keyword.lower() in combined for keyword in required_keywords):
                logger.debug(f"Excluded: {job['title']} (missing required keywords)")
                return False
        
        return True
    
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific job.
        
        Args:
            job_url: LinkedIn job URL
            
        Returns:
            Detailed job information
        """
        logger.info(f"Fetching job details: {job_url}")
        
        driver = self.get_driver()
        driver.get(job_url)
        time.sleep(3)
        
        job_details = {
            "url": job_url,
            "description": "",
            "requirements": [],
            "qualifications": [],
            "responsibilities": [],
            "company_info": {},
        }
        
        try:
            # Full description
            desc_elem = driver.find_element(By.CSS_SELECTOR, "div.show-more-less-html__markup")
            job_details["description"] = desc_elem.text
            
            # Parse description into sections
            self._parse_job_description(job_details["description"], job_details)
            
            # Company information
            try:
                company_elem = driver.find_element(By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card__company-name")
                job_details["company_info"]["name"] = company_elem.text
            except:
                pass
        
        except Exception as e:
            logger.error(f"Failed to get job details: {e}")
        
        return job_details
    
    def _parse_job_description(self, description: str, job_details: Dict[str, Any]) -> None:
        """Parse job description into structured sections."""
        description_lower = description.lower()
        
        # Split by common section headers
        sections = {
            "requirements": ["requirements", "required", "must have", "qualifications"],
            "qualifications": ["qualifications", "preferred", "nice to have", "desired"],
            "responsibilities": ["responsibilities", "you will", "role", "what you'll do"],
        }
        
        for key, keywords in sections.items():
            for keyword in keywords:
                if keyword in description_lower:
                    # Extract section (simplified, can be improved)
                    start_idx = description_lower.find(keyword)
                    # Find next section or end
                    end_idx = len(description)
                    for other_keyword in sum(sections.values(), []):
                        if other_keyword != keyword:
                            next_idx = description_lower.find(other_keyword, start_idx + len(keyword))
                            if next_idx != -1 and next_idx < end_idx:
                                end_idx = next_idx
                    
                    section_text = description[start_idx:end_idx]
                    
                    # Extract bullet points
                    bullets = re.findall(r'[•\-\*]\s*(.+)', section_text)
                    if bullets:
                        job_details[key] = bullets[:10]  # Top 10 points
                    break


def scrape_linkedin_jobs(keywords: Optional[List[str]] = None,
                        location: Optional[str] = None,
                        max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Convenience function to scrape LinkedIn jobs.
    
    Args:
        keywords: Search keywords
        location: Location filter
        max_results: Maximum number of results
        
    Returns:
        List of jobs
    """
    with LinkedInJobScraper(headless=True) as scraper:
        return scraper.scrape(keywords, location, max_results)
