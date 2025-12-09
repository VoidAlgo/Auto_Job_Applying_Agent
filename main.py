"""
Main orchestration pipeline for automated job application system.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from candidate.profile_builder import CandidateProfileBuilder
from config.config_manager import get_config
from scrapers.linkedin_scraper import LinkedInJobScraper
from matching.job_matcher import JobMatcher
from matching.ranker import JobRanker
from customization.cover_letter_agent import CoverLetterAgent
from utils.logger import setup_logging


class JobApplicationAgent:
    """Main orchestrator for the automated job application system."""
    
    def __init__(self):
        """Initialize the job application agent."""
        # Setup logging
        setup_logging()
        logger.info("=" * 80)
        logger.info("Automated Job Application Agent - Starting")
        logger.info("=" * 80)
        
        # Load configuration
        self.config = get_config()
        
        # Validate configuration
        try:
            self.config.validate()
            logger.info("✓ Configuration validated")
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            sys.exit(1)
        
        # Initialize components
        self.profile_builder: Optional[CandidateProfileBuilder] = None
        self.candidate_profile: Optional[dict] = None
        self.job_matcher: Optional[JobMatcher] = None
        self.job_ranker: Optional[JobRanker] = None
        self.cover_letter_agent: Optional[CoverLetterAgent] = None
    
    def build_candidate_profile(self, force_rebuild: bool = False) -> dict:
        """
        Build or load candidate profile.
        
        Args:
            force_rebuild: Force rebuild even if cached profile exists
            
        Returns:
            Candidate profile dictionary
        """
        profile_path = Path("data/candidate_profile.json")
        
        # Check if cached profile exists
        if profile_path.exists() and not force_rebuild:
            logger.info("Loading cached candidate profile...")
            self.profile_builder = CandidateProfileBuilder()
            self.candidate_profile = self.profile_builder.load(str(profile_path))
            logger.info("✓ Profile loaded from cache")
        
        else:
            logger.info("Building candidate profile from sources...")
            self.profile_builder = CandidateProfileBuilder()
            
            # Build profile from all sources
            self.candidate_profile = self.profile_builder.build(
                include_resume=True,
                include_github=True,
                include_linkedin=False,  # Set to True if credentials available
                include_projects=True,
            )
            
            # Save profile
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            self.profile_builder.save(str(profile_path))
            
            logger.info("✓ Profile built and saved")
        
        # Print profile summary
        summary = self.profile_builder.get_summary()
        logger.info(f"\nProfile Summary:\n{summary}\n")
        
        return self.candidate_profile
    
    def discover_jobs(self, max_jobs: int = 50) -> list:
        """
        Discover relevant jobs from various job boards.
        
        Args:
            max_jobs: Maximum number of jobs to discover
            
        Returns:
            List of discovered jobs
        """
        logger.info(f"Discovering jobs (max: {max_jobs})...")
        
        all_jobs = []
        
        # LinkedIn scraping
        if self.config.settings.job_boards.get("linkedin", {}).get("enabled", True):
            try:
                logger.info("Scraping LinkedIn jobs...")
                
                with LinkedInJobScraper(headless=True) as scraper:
                    jobs = scraper.scrape(max_results=max_jobs)
                    all_jobs.extend(jobs)
                    logger.info(f"✓ Found {len(jobs)} jobs from LinkedIn")
            
            except Exception as e:
                logger.error(f"LinkedIn scraping failed: {e}")
        
        # TODO: Add Indeed, Glassdoor, AngelList scrapers
        
        logger.info(f"✓ Total jobs discovered: {len(all_jobs)}")
        return all_jobs
    
    def match_and_rank_jobs(self, jobs: list) -> list:
        """
        Match and rank jobs based on candidate profile.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Ranked list of jobs with match scores
        """
        logger.info(f"Matching and ranking {len(jobs)} jobs...")
        
        if not self.candidate_profile:
            logger.error("Candidate profile not built. Cannot match jobs.")
            return []
        
        # Initialize matcher and ranker
        if not self.job_matcher:
            self.job_matcher = JobMatcher()
            logger.info("✓ JobMatcher initialized")
        
        if not self.job_ranker:
            self.job_ranker = JobRanker(job_matcher=self.job_matcher)
            logger.info("✓ JobRanker initialized")
        
        # Rank jobs
        ranked_jobs = self.job_ranker.rank_jobs(
            jobs=jobs,
            profile=self.candidate_profile,
            top_n=None  # Rank all jobs
        )
        
        # Save ranked jobs
        ranked_jobs_path = Path("data/ranked_jobs.json")
        self.job_ranker.save_ranked_jobs(ranked_jobs, ranked_jobs_path)
        
        logger.info(f"✓ Ranked {len(ranked_jobs)} jobs")
        logger.info(f"  - High Priority: {sum(1 for j in ranked_jobs if j.priority == 'High')}")
        logger.info(f"  - Medium Priority: {sum(1 for j in ranked_jobs if j.priority == 'Medium')}")
        logger.info(f"  - Low Priority: {sum(1 for j in ranked_jobs if j.priority == 'Low')}")
        
        return ranked_jobs
    
    def review_and_apply(self, jobs: list, auto_apply: bool = False) -> dict:
        """
        Review jobs and apply to selected positions.
        
        Args:
            jobs: List of ranked jobs
            auto_apply: Automatically apply without review (dangerous!)
            
        Returns:
            Application statistics
        """
        logger.info(f"Reviewing {len(jobs)} jobs for application...")
        
        stats = {
            "total_jobs": len(jobs),
            "reviewed": 0,
            "applied": 0,
            "skipped": 0,
            "failed": 0,
        }
        
        if auto_apply:
            logger.warning("Auto-apply mode enabled - applications will be submitted automatically!")
        
        # Filter to high priority jobs
        high_priority_jobs = [j for j in jobs if j.priority == "High"]
        logger.info(f"Found {len(high_priority_jobs)} high priority jobs")
        
        # Initialize cover letter agent
        if not self.cover_letter_agent:
            try:
                self.cover_letter_agent = CoverLetterAgent()
                logger.info("✓ CoverLetterAgent initialized")
            except ValueError as e:
                logger.warning(f"Cannot initialize CoverLetterAgent: {e}")
                logger.warning("Cover letters will not be generated")
        
        # Process each job
        for i, job in enumerate(high_priority_jobs[:10], 1):  # Process top 10
            try:
                logger.info(f"\n[{i}/{min(10, len(high_priority_jobs))}] {job.title} at {job.company}")
                logger.info(f"  Match Score: {job.match_score.overall_score:.1f}/100")
                logger.info(f"  Priority: {job.priority}")
                logger.info(f"  Recommendation: {job.recommendation}")
                
                # Generate cover letter
                if self.cover_letter_agent:
                    logger.info("  Generating cover letter...")
                    
                    # Convert RankedJob to dict for cover letter generation
                    job_dict = {
                        'title': job.title,
                        'company': job.company,
                        'description': job.description,
                        'url': job.url,
                        'location': job.location,
                    }
                    
                    cover_letter = self.cover_letter_agent.generate(
                        job=job_dict,
                        profile=self.candidate_profile,
                        match_score=job.match_score
                    )
                    
                    # Save cover letter
                    cover_letter_path = Path(f"data/cover_letters/{job.company}_{job.title}.txt")
                    cover_letter.save(cover_letter_path)
                    logger.info(f"  ✓ Cover letter saved ({cover_letter.word_count} words)")
                
                stats["reviewed"] += 1
                
                # TODO: Implement automated form filling
                logger.info("  ⚠ Automated submission not yet implemented")
                logger.info(f"  URL: {job.url}")
                
            except Exception as e:
                logger.error(f"  ✗ Error processing job: {e}")
                stats["failed"] += 1
                continue
        
        logger.info(f"\n✓ Review completed: {stats['reviewed']} jobs processed")
        
        return stats
    
    def run(self, 
            max_jobs: int = 50,
            force_profile_rebuild: bool = False,
            auto_apply: bool = False):
        """
        Run the complete job application pipeline.
        
        Args:
            max_jobs: Maximum number of jobs to process
            force_profile_rebuild: Force rebuild candidate profile
            auto_apply: Automatically apply to jobs (not recommended initially)
        """
        try:
            # Step 1: Build candidate profile
            logger.info("\n" + "=" * 80)
            logger.info("STEP 1: Building Candidate Profile")
            logger.info("=" * 80)
            self.build_candidate_profile(force_rebuild=force_profile_rebuild)
            
            # Step 2: Discover jobs
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: Discovering Jobs")
            logger.info("=" * 80)
            jobs = self.discover_jobs(max_jobs=max_jobs)
            
            if not jobs:
                logger.warning("No jobs discovered. Exiting.")
                return
            
            # Step 3: Match and rank
            logger.info("\n" + "=" * 80)
            logger.info("STEP 3: Matching and Ranking Jobs")
            logger.info("=" * 80)
            ranked_jobs = self.match_and_rank_jobs(jobs)
            
            # Step 4: Review and apply
            logger.info("\n" + "=" * 80)
            logger.info("STEP 4: Review and Apply")
            logger.info("=" * 80)
            stats = self.review_and_apply(ranked_jobs, auto_apply=auto_apply)
            
            # Final summary
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETED")
            logger.info("=" * 80)
            logger.info(f"Total jobs discovered: {stats['total_jobs']}")
            logger.info(f"Jobs reviewed: {stats['reviewed']}")
            logger.info(f"Applications submitted: {stats['applied']}")
            logger.info(f"Jobs skipped: {stats['skipped']}")
            logger.info(f"Failed applications: {stats['failed']}")
            logger.info("=" * 80)
        
        except KeyboardInterrupt:
            logger.warning("\nPipeline interrupted by user")
            sys.exit(0)
        
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automated Job Application Agent for AI/ML Engineering Positions"
    )
    
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=50,
        help="Maximum number of jobs to discover (default: 50)"
    )
    
    parser.add_argument(
        "--rebuild-profile",
        action="store_true",
        help="Force rebuild candidate profile from sources"
    )
    
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        help="Automatically apply to jobs without manual review (NOT RECOMMENDED initially)"
    )
    
    parser.add_argument(
        "--profile-only",
        action="store_true",
        help="Only build candidate profile and exit"
    )
    
    args = parser.parse_args()
    
    # Create agent
    agent = JobApplicationAgent()
    
    # Profile-only mode
    if args.profile_only:
        agent.build_candidate_profile(force_rebuild=args.rebuild_profile)
        return
    
    # Run full pipeline
    agent.run(
        max_jobs=args.max_jobs,
        force_profile_rebuild=args.rebuild_profile,
        auto_apply=args.auto_apply,
    )


if __name__ == "__main__":
    main()
