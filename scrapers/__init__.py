"""
Initialize scrapers module.
"""

from scrapers.base_scraper import BaseScraper
from scrapers.linkedin_scraper import LinkedInJobScraper, scrape_linkedin_jobs

__all__ = [
    "BaseScraper",
    "LinkedInJobScraper",
    "scrape_linkedin_jobs",
]
