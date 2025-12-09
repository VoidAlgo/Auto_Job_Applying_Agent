"""
Job Ranker - Multi-Criteria Job Ranking System

This module ranks jobs based on multiple criteria including match scores,
strategic fit, application difficulty, and candidate preferences.

Author: Auto Job Applier System
Date: December 2025
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from matching.job_matcher import JobMatcher, MatchScore
from candidate.profile_builder import CandidateProfile
from config.config_manager import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RankedJob:
    """Job with comprehensive ranking information."""
    
    # Original job data
    job_id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    posted_date: Optional[str] = None
    
    # Match information
    match_score: Optional[MatchScore] = None
    
    # Ranking scores (0-100)
    final_rank_score: float = 0.0
    strategic_fit_score: float = 0.0
    difficulty_score: float = 0.0
    timing_score: float = 0.0
    
    # Metadata
    rank: int = 0
    priority: str = "Medium"  # High, Medium, Low
    recommendation: str = ""
    
    # Application strategy
    apply_immediately: bool = False
    requires_customization: bool = True
    estimated_time: int = 30  # minutes
    
    # Notes
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    strategy_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'job_id': self.job_id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'posted_date': self.posted_date,
            'match_score': self.match_score.to_dict() if self.match_score else None,
            'ranking': {
                'final_rank_score': round(self.final_rank_score, 2),
                'strategic_fit_score': round(self.strategic_fit_score, 2),
                'difficulty_score': round(self.difficulty_score, 2),
                'timing_score': round(self.timing_score, 2),
                'rank': self.rank,
                'priority': self.priority,
                'recommendation': self.recommendation,
            },
            'application_strategy': {
                'apply_immediately': self.apply_immediately,
                'requires_customization': self.requires_customization,
                'estimated_time': self.estimated_time,
            },
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'strategy_notes': self.strategy_notes,
        }


class JobRanker:
    """
    Rank jobs using multi-criteria analysis.
    
    Considers:
    - Match score (from JobMatcher)
    - Strategic fit (career goals alignment)
    - Application difficulty (competition, requirements)
    - Timing (posting recency, urgency)
    - Candidate preferences (location, remote, company size)
    """
    
    # Ranking weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        'match_score': 0.50,       # Primary factor
        'strategic_fit': 0.20,     # Career alignment
        'difficulty': 0.15,        # Feasibility
        'timing': 0.10,            # Urgency/recency
        'preferences': 0.05,       # Personal preferences
    }
    
    def __init__(
        self,
        job_matcher: Optional[JobMatcher] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the job ranker.
        
        Args:
            job_matcher: JobMatcher instance (creates if None)
            weights: Custom ranking weights (uses defaults if None)
        """
        self.logger = logger
        self.config = get_config()
        
        # Initialize components
        self.matcher = job_matcher or JobMatcher()
        
        # Set ranking weights
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()
        
        # Load preferences from config
        self.preferences = self._load_preferences()
        
        self.logger.info("JobRanker initialized with weights: " + str(self.weights))
    
    def _validate_weights(self) -> None:
        """Validate that weights sum to 1.0."""
        import numpy as np
        weight_sum = sum(self.weights.values())
        if not np.isclose(weight_sum, 1.0, atol=0.01):
            self.logger.warning(
                f"Weights sum to {weight_sum:.3f}, normalizing to 1.0"
            )
            # Normalize weights
            for key in self.weights:
                self.weights[key] /= weight_sum
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load candidate preferences from config."""
        return {
            'preferred_locations': self.config.job_criteria.get('locations', []),
            'remote_preference': self.config.job_criteria.get('remote_only', False),
            'target_roles': self.config.job_criteria.get('target_roles', []),
            'preferred_company_sizes': ['startup', 'small', 'medium'],  # Freshers often prefer smaller companies
            'industry_preferences': ['ai', 'ml', 'tech', 'saas'],
        }
    
    def rank_jobs(
        self,
        jobs: List[Dict[str, Any]],
        profile: CandidateProfile,
        top_n: Optional[int] = None
    ) -> List[RankedJob]:
        """
        Rank a list of jobs for the candidate.
        
        Args:
            jobs: List of job dictionaries
            profile: Candidate profile
            top_n: Return only top N jobs (None = all)
            
        Returns:
            List of RankedJob objects sorted by rank
        """
        self.logger.info(f"Ranking {len(jobs)} jobs for candidate")
        
        ranked_jobs = []
        
        for job in jobs:
            try:
                ranked_job = self._rank_single_job(job, profile)
                ranked_jobs.append(ranked_job)
            except Exception as e:
                self.logger.error(f"Error ranking job {job.get('title', 'Unknown')}: {e}")
                continue
        
        # Sort by final rank score (descending)
        ranked_jobs.sort(key=lambda x: x.final_rank_score, reverse=True)
        
        # Assign rank numbers
        for i, job in enumerate(ranked_jobs, 1):
            job.rank = i
        
        # Slice to top N if requested
        if top_n:
            ranked_jobs = ranked_jobs[:top_n]
        
        self.logger.info(f"Ranked {len(ranked_jobs)} jobs successfully")
        
        return ranked_jobs
    
    def _rank_single_job(
        self,
        job: Dict[str, Any],
        profile: CandidateProfile
    ) -> RankedJob:
        """
        Rank a single job.
        
        Args:
            job: Job dictionary
            profile: Candidate profile
            
        Returns:
            RankedJob object
        """
        # Calculate match score
        match_score = self.matcher.match(job, profile)
        
        # Calculate component scores
        strategic_fit = self._calculate_strategic_fit(job, profile)
        difficulty = self._calculate_difficulty_score(job, match_score)
        timing = self._calculate_timing_score(job)
        preferences = self._calculate_preference_score(job)
        
        # Calculate final weighted score
        final_score = (
            self.weights['match_score'] * match_score.overall_score +
            self.weights['strategic_fit'] * strategic_fit +
            self.weights['difficulty'] * difficulty +
            self.weights['timing'] * timing +
            self.weights['preferences'] * preferences
        )
        
        # Determine priority and recommendation
        priority = self._determine_priority(final_score, match_score)
        recommendation = self._generate_recommendation(final_score, match_score)
        
        # Determine application strategy
        apply_immediately = final_score >= 80 and timing >= 70
        requires_customization = match_score.overall_score >= 60
        estimated_time = self._estimate_application_time(match_score, requires_customization)
        
        # Generate strengths and weaknesses
        strengths, weaknesses = self._generate_analysis(
            match_score, strategic_fit, difficulty, timing
        )
        
        # Generate strategy notes
        strategy_notes = self._generate_strategy_notes(
            job, match_score, strategic_fit, difficulty
        )
        
        return RankedJob(
            job_id=job.get('id', job.get('url', '')),
            title=job.get('title', ''),
            company=job.get('company', ''),
            location=job.get('location', ''),
            url=job.get('url', ''),
            description=job.get('description', ''),
            posted_date=job.get('posted_date'),
            match_score=match_score,
            final_rank_score=final_score,
            strategic_fit_score=strategic_fit,
            difficulty_score=difficulty,
            timing_score=timing,
            priority=priority,
            recommendation=recommendation,
            apply_immediately=apply_immediately,
            requires_customization=requires_customization,
            estimated_time=estimated_time,
            strengths=strengths,
            weaknesses=weaknesses,
            strategy_notes=strategy_notes,
        )
    
    def _calculate_strategic_fit(
        self,
        job: Dict[str, Any],
        profile: CandidateProfile
    ) -> float:
        """
        Calculate strategic career fit.
        
        Args:
            job: Job dictionary
            profile: Candidate profile
            
        Returns:
            Strategic fit score (0-100)
        """
        score = 50.0  # Base score
        
        job_title = job.get('title', '').lower()
        job_desc = job.get('description', '').lower()
        
        # Target roles alignment
        target_roles = [role.lower() for role in self.preferences['target_roles']]
        if any(role in job_title for role in target_roles):
            score += 20
        
        # Entry-level indicators (good for freshers)
        entry_level_keywords = ['junior', 'entry', 'associate', 'early career', 'graduate']
        if any(keyword in job_title for keyword in entry_level_keywords):
            score += 15
        
        # Growth opportunities
        growth_keywords = ['learning', 'mentorship', 'training', 'development', 'grow']
        if any(keyword in job_desc for keyword in growth_keywords):
            score += 10
        
        # Modern tech stack (AI/ML focus)
        modern_keywords = ['llm', 'gpt', 'ai agents', 'rag', 'langchain', 'modern stack']
        if any(keyword in job_desc for keyword in modern_keywords):
            score += 15
        
        # Red flags (reduce score)
        red_flags = ['senior', 'lead', '5+ years', 'extensive experience']
        if any(flag in job_title or flag in job_desc for flag in red_flags):
            score -= 20
        
        return min(100, max(0, score))
    
    def _calculate_difficulty_score(
        self,
        job: Dict[str, Any],
        match_score: MatchScore
    ) -> float:
        """
        Calculate application difficulty (inverse of competition).
        
        Lower competition = higher score = easier to win
        
        Args:
            job: Job dictionary
            match_score: Match score
            
        Returns:
            Difficulty score (0-100), higher = easier
        """
        # Base difficulty from match score
        # High match = easier application
        base_score = match_score.overall_score
        
        job_desc = job.get('description', '').lower()
        
        # Factors that make it easier
        easy_factors = 0
        
        # Entry-level positions are less competitive
        if any(keyword in job_desc for keyword in ['entry', 'junior', 'graduate']):
            easy_factors += 15
        
        # Smaller companies are less competitive
        company_size_indicators = ['startup', 'small team', 'growing company']
        if any(indicator in job_desc for indicator in company_size_indicators):
            easy_factors += 10
        
        # Remote positions have more applicants (harder)
        if 'remote' in job.get('location', '').lower():
            easy_factors -= 10
        
        # Factors that make it harder
        hard_factors = 0
        
        # FAANG/Top companies are very competitive
        top_companies = ['google', 'facebook', 'amazon', 'apple', 'microsoft', 'meta']
        if any(company in job.get('company', '').lower() for company in top_companies):
            hard_factors += 20
        
        # Many requirements = harder
        if len(match_score.missing_skills) > 5:
            hard_factors += 15
        
        # Calculate final difficulty score
        difficulty = base_score + easy_factors - hard_factors
        
        return min(100, max(0, difficulty))
    
    def _calculate_timing_score(self, job: Dict[str, Any]) -> float:
        """
        Calculate timing/urgency score based on posting date.
        
        Args:
            job: Job dictionary
            
        Returns:
            Timing score (0-100)
        """
        posted_date_str = job.get('posted_date')
        
        if not posted_date_str:
            return 50.0  # Neutral score if date unknown
        
        try:
            # Parse posted date
            # Assuming format like "2 days ago", "1 week ago", etc.
            posted_date_str = posted_date_str.lower()
            
            if 'today' in posted_date_str or 'just now' in posted_date_str:
                days_ago = 0
            elif 'yesterday' in posted_date_str:
                days_ago = 1
            elif 'day' in posted_date_str:
                import re
                match = re.search(r'(\d+)\s*day', posted_date_str)
                days_ago = int(match.group(1)) if match else 7
            elif 'week' in posted_date_str:
                import re
                match = re.search(r'(\d+)\s*week', posted_date_str)
                weeks = int(match.group(1)) if match else 2
                days_ago = weeks * 7
            elif 'month' in posted_date_str:
                import re
                match = re.search(r'(\d+)\s*month', posted_date_str)
                months = int(match.group(1)) if match else 1
                days_ago = months * 30
            else:
                days_ago = 7  # Default
            
            # Score based on recency
            if days_ago <= 1:
                score = 100  # Very fresh
            elif days_ago <= 3:
                score = 90   # Fresh
            elif days_ago <= 7:
                score = 75   # Recent
            elif days_ago <= 14:
                score = 60   # Moderate
            elif days_ago <= 30:
                score = 40   # Older
            else:
                score = 20   # Old
            
            return score
            
        except Exception as e:
            self.logger.debug(f"Error parsing date '{posted_date_str}': {e}")
            return 50.0
    
    def _calculate_preference_score(self, job: Dict[str, Any]) -> float:
        """
        Calculate score based on candidate preferences.
        
        Args:
            job: Job dictionary
            
        Returns:
            Preference score (0-100)
        """
        score = 50.0  # Base score
        
        location = job.get('location', '').lower()
        company = job.get('company', '').lower()
        
        # Remote preference
        if self.preferences.get('remote_preference'):
            if 'remote' in location:
                score += 20
            else:
                score -= 10
        
        # Location preferences
        preferred_locations = [loc.lower() for loc in self.preferences.get('preferred_locations', [])]
        if preferred_locations and any(loc in location for loc in preferred_locations):
            score += 15
        
        # Industry preferences
        industry_prefs = self.preferences.get('industry_preferences', [])
        if any(industry in company or industry in job.get('description', '').lower() 
               for industry in industry_prefs):
            score += 15
        
        return min(100, max(0, score))
    
    def _determine_priority(
        self,
        final_score: float,
        match_score: MatchScore
    ) -> str:
        """Determine application priority."""
        if final_score >= 80 and match_score.overall_score >= 75:
            return "High"
        elif final_score >= 60 and match_score.overall_score >= 60:
            return "Medium"
        else:
            return "Low"
    
    def _generate_recommendation(
        self,
        final_score: float,
        match_score: MatchScore
    ) -> str:
        """Generate application recommendation."""
        if final_score >= 80:
            return "Apply Immediately - Excellent Match"
        elif final_score >= 70:
            return "Apply Soon - Strong Match"
        elif final_score >= 60:
            return "Consider Applying - Good Match"
        elif final_score >= 50:
            return "Apply if Time Permits - Moderate Match"
        else:
            return "Skip - Weak Match"
    
    def _estimate_application_time(
        self,
        match_score: MatchScore,
        requires_customization: bool
    ) -> int:
        """
        Estimate time to complete application (minutes).
        
        Args:
            match_score: Match score
            requires_customization: Whether customization is needed
            
        Returns:
            Estimated minutes
        """
        base_time = 15  # Base application form filling
        
        if requires_customization:
            # Cover letter writing
            base_time += 20
            
            # Resume customization
            base_time += 10
        
        # Screening questions (if many missing skills, more questions expected)
        if len(match_score.missing_skills) > 5:
            base_time += 10
        
        return base_time
    
    def _generate_analysis(
        self,
        match_score: MatchScore,
        strategic_fit: float,
        difficulty: float,
        timing: float
    ) -> tuple[List[str], List[str]]:
        """Generate strengths and weaknesses."""
        strengths = []
        weaknesses = []
        
        # From match score
        if match_score.overall_score >= 75:
            strengths.append(f"Excellent overall match ({match_score.overall_score:.0f}%)")
        
        strengths.extend(match_score.match_reasons)
        weaknesses.extend(match_score.concerns)
        
        # Strategic fit
        if strategic_fit >= 75:
            strengths.append("Strong strategic career fit")
        elif strategic_fit < 50:
            weaknesses.append("Limited strategic alignment")
        
        # Difficulty
        if difficulty >= 70:
            strengths.append("Less competitive position")
        elif difficulty < 40:
            weaknesses.append("Highly competitive role")
        
        # Timing
        if timing >= 80:
            strengths.append("Recently posted (apply soon)")
        elif timing < 40:
            weaknesses.append("Older posting (may be filled)")
        
        return strengths, weaknesses
    
    def _generate_strategy_notes(
        self,
        job: Dict[str, Any],
        match_score: MatchScore,
        strategic_fit: float,
        difficulty: float
    ) -> str:
        """Generate strategic application notes."""
        notes = []
        
        # Customization recommendations
        if match_score.skill_match >= 70:
            notes.append("Emphasize matching technical skills in cover letter.")
        
        if len(match_score.missing_skills) > 0 and len(match_score.missing_skills) <= 3:
            missing = list(match_score.missing_skills)[:3]
            notes.append(f"Address missing skills ({', '.join(missing)}) by highlighting transferable skills.")
        
        # Project recommendations
        if match_score.project_relevance >= 70:
            notes.append("Lead with most relevant projects in application.")
        
        # Strategic approach
        if strategic_fit >= 75:
            notes.append("Highlight long-term career interest in this domain.")
        
        if difficulty < 50:
            notes.append("Highly competitive - ensure application is polished and submitted early.")
        
        return " ".join(notes)
    
    def save_ranked_jobs(
        self,
        ranked_jobs: List[RankedJob],
        output_path: Path
    ) -> None:
        """
        Save ranked jobs to JSON file.
        
        Args:
            ranked_jobs: List of ranked jobs
            output_path: Path to save JSON
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_jobs': len(ranked_jobs),
            'jobs': [job.to_dict() for job in ranked_jobs],
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved {len(ranked_jobs)} ranked jobs to {output_path}")


def main():
    """Example usage of JobRanker."""
    from candidate.profile_builder import ProfileBuilder, CandidateProfile
    
    # Sample jobs
    jobs = [
        {
            'id': '1',
            'title': 'Junior ML Engineer',
            'company': 'AI Startup',
            'location': 'Remote',
            'url': 'https://example.com/job1',
            'description': '''
            Looking for entry-level ML Engineer to work on LLM applications.
            Requirements: Python, PyTorch, basic ML knowledge. 0-1 years experience.
            We offer mentorship and learning opportunities.
            ''',
            'posted_date': '2 days ago',
        },
        {
            'id': '2',
            'title': 'Senior ML Engineer',
            'company': 'Google',
            'location': 'San Francisco, CA',
            'url': 'https://example.com/job2',
            'description': '''
            Senior ML Engineer with 5+ years experience in production ML systems.
            Requirements: Strong CS fundamentals, TensorFlow, distributed systems.
            ''',
            'posted_date': '1 week ago',
        },
    ]
    
    # Initialize ranker
    ranker = JobRanker()
    
    # Create sample profile
    profile = CandidateProfile(
        personal_info={},
        skills=['python', 'pytorch', 'langchain', 'rag'],
        experience=[{'title': 'ML Intern', 'duration': '6 months'}],
        education=[{'degree': 'BTech CSE'}],
        projects=[{'name': 'LLM Voice Agent', 'technologies': ['python', 'openai']}],
        summary='Entry-level ML engineer',
    )
    
    # Rank jobs
    ranked_jobs = ranker.rank_jobs(jobs, profile)
    
    # Print results
    print("\n=== Ranked Jobs ===\n")
    for job in ranked_jobs:
        print(f"Rank #{job.rank}: {job.title} at {job.company}")
        print(f"  Final Score: {job.final_rank_score:.1f}/100")
        print(f"  Priority: {job.priority}")
        print(f"  Recommendation: {job.recommendation}")
        print(f"  Match: {job.match_score.overall_score:.1f}/100")
        print(f"  Strategic Fit: {job.strategic_fit_score:.1f}/100")
        print(f"  Difficulty: {job.difficulty_score:.1f}/100")
        print(f"  Timing: {job.timing_score:.1f}/100")
        print()


if __name__ == "__main__":
    main()
