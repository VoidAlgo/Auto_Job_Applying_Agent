"""
Job Matcher - Semantic Matching Between Jobs and Candidate Profiles

This module implements intelligent job matching using semantic embeddings,
skill overlap analysis, and contextual relevance scoring.

Author: Auto Job Applier System
Date: December 2025
"""

import numpy as np
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

from candidate.embedding_generator import EmbeddingGenerator
from candidate.profile_builder import CandidateProfile
from matching.skill_extractor import SkillExtractor, ExtractedSkills
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MatchScore:
    """Comprehensive match score between job and candidate."""
    
    # Overall score (0-100)
    overall_score: float
    
    # Component scores (0-100 each)
    semantic_similarity: float
    skill_match: float
    experience_match: float
    education_match: float
    project_relevance: float
    
    # Detailed breakdown
    skill_overlap: Dict[str, Any] = field(default_factory=dict)
    matched_skills: Set[str] = field(default_factory=set)
    missing_skills: Set[str] = field(default_factory=set)
    
    # Metadata
    confidence: float = 0.0  # 0-1
    match_reasons: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'overall_score': round(self.overall_score, 2),
            'component_scores': {
                'semantic_similarity': round(self.semantic_similarity, 2),
                'skill_match': round(self.skill_match, 2),
                'experience_match': round(self.experience_match, 2),
                'education_match': round(self.education_match, 2),
                'project_relevance': round(self.project_relevance, 2),
            },
            'skill_overlap': self.skill_overlap,
            'matched_skills': list(self.matched_skills),
            'missing_skills': list(self.missing_skills),
            'confidence': round(self.confidence, 2),
            'match_reasons': self.match_reasons,
            'concerns': self.concerns,
        }
    
    def get_recommendation(self) -> str:
        """Get application recommendation based on score."""
        if self.overall_score >= 80:
            return "Highly Recommended"
        elif self.overall_score >= 65:
            return "Recommended"
        elif self.overall_score >= 50:
            return "Consider"
        else:
            return "Not Recommended"


class JobMatcher:
    """
    Match candidates to jobs using semantic embeddings and skill analysis.
    
    Calculates comprehensive match scores considering:
    - Semantic similarity between job description and profile
    - Skill overlap and requirements match
    - Experience level alignment
    - Education requirements
    - Project relevance
    """
    
    # Scoring weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        'semantic_similarity': 0.30,  # Overall semantic match
        'skill_match': 0.35,           # Technical skills overlap
        'experience_match': 0.15,      # Years of experience
        'education_match': 0.10,       # Education level
        'project_relevance': 0.10,     # Relevant projects
    }
    
    def __init__(
        self,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        skill_extractor: Optional[SkillExtractor] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the job matcher.
        
        Args:
            embedding_generator: EmbeddingGenerator instance (creates if None)
            skill_extractor: SkillExtractor instance (creates if None)
            weights: Custom scoring weights (uses defaults if None)
        """
        self.logger = logger
        
        # Initialize components
        self.embedding_gen = embedding_generator or EmbeddingGenerator()
        self.skill_extractor = skill_extractor or SkillExtractor()
        
        # Set scoring weights
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()
        
        self.logger.info("JobMatcher initialized with weights: " + str(self.weights))
    
    def _validate_weights(self) -> None:
        """Validate that weights sum to 1.0."""
        weight_sum = sum(self.weights.values())
        if not np.isclose(weight_sum, 1.0, atol=0.01):
            self.logger.warning(
                f"Weights sum to {weight_sum:.3f}, normalizing to 1.0"
            )
            # Normalize weights
            for key in self.weights:
                self.weights[key] /= weight_sum
    
    def match(
        self,
        job: Dict[str, Any],
        profile: CandidateProfile
    ) -> MatchScore:
        """
        Calculate comprehensive match score between job and candidate.
        
        Args:
            job: Job dictionary with title, description, requirements, etc.
            profile: CandidateProfile object
            
        Returns:
            MatchScore with detailed breakdown
        """
        self.logger.info(f"Matching candidate to job: {job.get('title', 'Unknown')}")
        
        # Extract job information
        job_text = self._prepare_job_text(job)
        job_skills = self.skill_extractor.extract(job_text)
        
        # Calculate component scores
        semantic_score = self._calculate_semantic_similarity(job_text, profile)
        skill_score, skill_overlap = self._calculate_skill_match(job_skills, profile)
        experience_score = self._calculate_experience_match(job_skills, profile)
        education_score = self._calculate_education_match(job_skills, profile)
        project_score = self._calculate_project_relevance(job_text, profile)
        
        # Calculate weighted overall score
        overall_score = (
            self.weights['semantic_similarity'] * semantic_score +
            self.weights['skill_match'] * skill_score +
            self.weights['experience_match'] * experience_score +
            self.weights['education_match'] * education_score +
            self.weights['project_relevance'] * project_score
        )
        
        # Generate match reasons and concerns
        match_reasons, concerns = self._generate_insights(
            semantic_score, skill_score, experience_score,
            education_score, project_score, skill_overlap, job_skills
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            semantic_score, skill_score, skill_overlap
        )
        
        match_score = MatchScore(
            overall_score=overall_score,
            semantic_similarity=semantic_score,
            skill_match=skill_score,
            experience_match=experience_score,
            education_match=education_score,
            project_relevance=project_score,
            skill_overlap=skill_overlap,
            matched_skills=set(skill_overlap.get('matched_skills', [])),
            missing_skills=set(skill_overlap.get('missing_skills', [])),
            confidence=confidence,
            match_reasons=match_reasons,
            concerns=concerns,
        )
        
        self.logger.info(
            f"Match complete: {overall_score:.1f}/100 "
            f"({match_score.get_recommendation()})"
        )
        
        return match_score
    
    def _prepare_job_text(self, job: Dict[str, Any]) -> str:
        """
        Prepare job text for analysis.
        
        Args:
            job: Job dictionary
            
        Returns:
            Combined text from relevant fields
        """
        text_parts = []
        
        # Include relevant fields
        fields = ['title', 'description', 'requirements', 'qualifications', 'responsibilities']
        
        for field in fields:
            if field in job and job[field]:
                text_parts.append(str(job[field]))
        
        return ' '.join(text_parts)
    
    def _calculate_semantic_similarity(
        self,
        job_text: str,
        profile: CandidateProfile
    ) -> float:
        """
        Calculate semantic similarity between job and profile.
        
        Args:
            job_text: Job description text
            profile: Candidate profile
            
        Returns:
            Similarity score (0-100)
        """
        try:
            # Generate job embedding
            job_embedding = self.embedding_gen.generate(job_text)
            
            # Prepare profile text
            profile_text = self._prepare_profile_text(profile)
            profile_embedding = self.embedding_gen.generate(profile_text)
            
            # Calculate cosine similarity
            similarity = self.embedding_gen.cosine_similarity(
                job_embedding, profile_embedding
            )
            
            # Convert to 0-100 scale
            score = (similarity + 1) / 2 * 100  # Normalize from [-1, 1] to [0, 100]
            
            self.logger.debug(f"Semantic similarity: {score:.1f}")
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating semantic similarity: {e}")
            return 50.0  # Default middle score
    
    def _prepare_profile_text(self, profile: CandidateProfile) -> str:
        """
        Prepare profile text for embedding.
        
        Args:
            profile: Candidate profile
            
        Returns:
            Combined profile text
        """
        text_parts = []
        
        # Add summary
        if profile.summary:
            text_parts.append(profile.summary)
        
        # Add skills
        if profile.skills:
            text_parts.append("Skills: " + ", ".join(profile.skills))
        
        # Add experience
        for exp in profile.experience:
            text_parts.append(
                f"{exp.get('title', '')} at {exp.get('company', '')}: "
                f"{exp.get('description', '')}"
            )
        
        # Add projects
        for proj in profile.projects:
            text_parts.append(
                f"{proj.get('name', '')}: {proj.get('description', '')}"
            )
        
        return ' '.join(text_parts)
    
    def _calculate_skill_match(
        self,
        job_skills: ExtractedSkills,
        profile: CandidateProfile
    ) -> tuple[float, Dict[str, Any]]:
        """
        Calculate skill match score and overlap.
        
        Args:
            job_skills: Extracted skills from job
            profile: Candidate profile
            
        Returns:
            Tuple of (score, overlap_details)
        """
        # Get candidate skills
        candidate_skills = set(profile.skills) if profile.skills else set()
        
        # Add skills from experience and projects
        for exp in profile.experience:
            if 'skills' in exp:
                candidate_skills.update(exp['skills'])
        
        for proj in profile.projects:
            if 'technologies' in proj:
                candidate_skills.update(proj['technologies'])
        
        # Calculate overlap
        overlap = self.skill_extractor.calculate_skill_overlap(
            job_skills, candidate_skills
        )
        
        # Base score from overall match percentage
        score = overlap['match_percentage']
        
        # Boost for critical skills (programming languages, ML frameworks, LLM skills)
        critical_categories = ['programming_languages', 'ml_frameworks', 'llm_skills']
        category_overlaps = overlap.get('category_overlaps', {})
        
        critical_boost = 0
        for category in critical_categories:
            if category in category_overlaps:
                cat_match = category_overlaps[category]['percentage']
                critical_boost += cat_match * 0.1  # Up to 10% boost per category
        
        score = min(100, score + critical_boost)
        
        # Add matched and missing skills to overlap
        all_matched = set()
        all_missing = set()
        
        for category_data in category_overlaps.values():
            # Get matched skills (required - missing = matched)
            category_required = set(job_skills.__dict__[category])
            category_missing = set(category_data.get('missing', []))
            category_matched = category_required - category_missing
            all_matched.update(category_matched)
            all_missing.update(category_missing)
        
        overlap['matched_skills'] = list(all_matched)
        overlap['missing_skills'] = list(all_missing)
        
        self.logger.debug(f"Skill match: {score:.1f}")
        return score, overlap
    
    def _calculate_experience_match(
        self,
        job_skills: ExtractedSkills,
        profile: CandidateProfile
    ) -> float:
        """
        Calculate experience level match.
        
        Args:
            job_skills: Extracted skills from job
            profile: Candidate profile
            
        Returns:
            Experience match score (0-100)
        """
        # Calculate candidate's total experience in years
        candidate_years = self._calculate_total_experience(profile)
        
        # Get job requirement
        required_years = job_skills.years_required or 0
        
        # Perfect match if candidate meets or slightly exceeds requirement
        if candidate_years >= required_years:
            # Slight penalty for overqualification (not a concern for freshers though)
            if candidate_years > required_years + 2:
                score = 90.0
            else:
                score = 100.0
        else:
            # Penalty for underqualification (linear decrease)
            gap = required_years - candidate_years
            score = max(0, 100 - (gap * 25))  # -25 points per year gap
        
        # For entry-level positions (0-2 years), be more lenient
        if required_years <= 2:
            score = max(score, 75.0)  # Minimum 75 for entry-level
        
        self.logger.debug(
            f"Experience match: {score:.1f} "
            f"(candidate: {candidate_years}, required: {required_years})"
        )
        return score
    
    def _calculate_total_experience(self, profile: CandidateProfile) -> float:
        """
        Calculate total years of experience.
        
        Args:
            profile: Candidate profile
            
        Returns:
            Total years of experience
        """
        # For simplicity, count number of experiences
        # Each internship/job counts as partial year
        total_years = 0.0
        
        for exp in profile.experience:
            duration = exp.get('duration', '')
            
            # Parse duration (e.g., "6 months", "1 year")
            if 'year' in duration.lower():
                # Extract number before 'year'
                import re
                match = re.search(r'(\d+\.?\d*)\s*year', duration.lower())
                if match:
                    total_years += float(match.group(1))
            elif 'month' in duration.lower():
                # Extract number before 'month'
                import re
                match = re.search(r'(\d+)\s*month', duration.lower())
                if match:
                    total_years += float(match.group(1)) / 12
            else:
                # Default: count as 6 months if duration not specified
                total_years += 0.5
        
        return total_years
    
    def _calculate_education_match(
        self,
        job_skills: ExtractedSkills,
        profile: CandidateProfile
    ) -> float:
        """
        Calculate education level match.
        
        Args:
            job_skills: Extracted skills from job
            profile: Candidate profile
            
        Returns:
            Education match score (0-100)
        """
        required_education = job_skills.education_level
        
        if not required_education:
            return 100.0  # No requirement specified
        
        # Get candidate's highest education
        candidate_education = self._get_highest_education(profile)
        
        # Education hierarchy
        education_levels = {
            'phd': 4,
            'masters': 3,
            'bachelors': 2,
            'associates': 1,
        }
        
        required_level = education_levels.get(required_education.lower(), 2)
        candidate_level = education_levels.get(candidate_education.lower(), 2)
        
        # Score based on meeting or exceeding requirement
        if candidate_level >= required_level:
            score = 100.0
        else:
            # Penalty for not meeting requirement
            score = max(0, 100 - (required_level - candidate_level) * 30)
        
        self.logger.debug(
            f"Education match: {score:.1f} "
            f"(candidate: {candidate_education}, required: {required_education})"
        )
        return score
    
    def _get_highest_education(self, profile: CandidateProfile) -> str:
        """
        Get candidate's highest education level.
        
        Args:
            profile: Candidate profile
            
        Returns:
            Education level string
        """
        if not profile.education:
            return 'bachelors'  # Default assumption
        
        # Check all education entries
        education_levels = {'phd': 4, 'masters': 3, 'bachelors': 2, 'associates': 1}
        highest_level = 0
        highest_name = 'bachelors'
        
        for edu in profile.education:
            degree = edu.get('degree', '').lower()
            
            for level_name, level_value in education_levels.items():
                if level_name in degree:
                    if level_value > highest_level:
                        highest_level = level_value
                        highest_name = level_name
                        break
        
        return highest_name
    
    def _calculate_project_relevance(
        self,
        job_text: str,
        profile: CandidateProfile
    ) -> float:
        """
        Calculate project relevance score.
        
        Args:
            job_text: Job description text
            profile: Candidate profile
            
        Returns:
            Project relevance score (0-100)
        """
        if not profile.projects:
            return 50.0  # Neutral score if no projects
        
        try:
            # Generate embedding for job
            job_embedding = self.embedding_gen.generate(job_text)
            
            # Calculate similarity with each project
            similarities = []
            
            for project in profile.projects:
                project_text = (
                    f"{project.get('name', '')} "
                    f"{project.get('description', '')} "
                    f"{' '.join(project.get('technologies', []))}"
                )
                
                project_embedding = self.embedding_gen.generate(project_text)
                similarity = self.embedding_gen.cosine_similarity(
                    job_embedding, project_embedding
                )
                similarities.append(similarity)
            
            # Use best project match
            best_match = max(similarities) if similarities else 0
            
            # Convert to 0-100 scale
            score = (best_match + 1) / 2 * 100
            
            self.logger.debug(f"Project relevance: {score:.1f}")
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating project relevance: {e}")
            return 50.0
    
    def _generate_insights(
        self,
        semantic_score: float,
        skill_score: float,
        experience_score: float,
        education_score: float,
        project_score: float,
        skill_overlap: Dict[str, Any],
        job_skills: ExtractedSkills
    ) -> tuple[List[str], List[str]]:
        """
        Generate match reasons and concerns.
        
        Returns:
            Tuple of (reasons, concerns)
        """
        reasons = []
        concerns = []
        
        # Positive reasons
        if skill_score >= 75:
            reasons.append(f"Strong skill match ({skill_score:.0f}%)")
        
        if semantic_score >= 75:
            reasons.append("High semantic relevance to job description")
        
        if project_score >= 75:
            reasons.append("Relevant project experience")
        
        if experience_score >= 90:
            reasons.append("Experience level aligns perfectly")
        
        if education_score >= 90:
            reasons.append("Education requirements met")
        
        # Concerns
        if skill_score < 50:
            concerns.append(f"Low skill match ({skill_score:.0f}%)")
        
        if experience_score < 60:
            concerns.append("May not meet experience requirements")
        
        if education_score < 70:
            concerns.append("Education level below requirements")
        
        # Missing critical skills
        category_overlaps = skill_overlap.get('category_overlaps', {})
        for category in ['programming_languages', 'ml_frameworks', 'llm_skills']:
            if category in category_overlaps:
                missing = category_overlaps[category].get('missing', [])
                if missing and len(missing) > 3:
                    concerns.append(
                        f"Missing several {category.replace('_', ' ')}: "
                        f"{', '.join(list(missing)[:3])}"
                    )
        
        return reasons, concerns
    
    def _calculate_confidence(
        self,
        semantic_score: float,
        skill_score: float,
        skill_overlap: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence in the match score.
        
        Returns:
            Confidence value (0-1)
        """
        # High confidence if both semantic and skill scores are extreme (very high or very low)
        # Low confidence if scores are in the middle range
        
        avg_score = (semantic_score + skill_score) / 2
        
        # Confidence increases as we move away from 50 (middle)
        distance_from_middle = abs(avg_score - 50)
        confidence = distance_from_middle / 50  # Normalize to 0-1
        
        # Boost confidence if we have good skill coverage
        total_skills = skill_overlap.get('total_required', 1)
        if total_skills >= 5:  # Good amount of data
            confidence = min(1.0, confidence + 0.1)
        
        return confidence


def main():
    """Example usage of JobMatcher."""
    from candidate.profile_builder import ProfileBuilder
    
    # Sample job
    job = {
        'title': 'Junior ML Engineer',
        'description': '''
        We're looking for a Junior Machine Learning Engineer to join our AI team.
        
        You'll work on building and deploying LLM-based applications using RAG,
        prompt engineering, and vector databases. Experience with PyTorch and
        LangChain is a plus.
        
        Requirements:
        - 0-1 years of experience
        - Python programming
        - Basic ML knowledge
        - Bachelor's in CS or related field
        ''',
    }
    
    # Initialize matcher
    matcher = JobMatcher()
    
    # Load or build candidate profile
    # profile = ProfileBuilder(config).build()
    
    # For demo, create a sample profile
    from dataclasses import dataclass, field
    profile = CandidateProfile(
        personal_info={},
        skills=['python', 'pytorch', 'langchain', 'rag', 'machine learning'],
        experience=[
            {
                'title': 'ML Intern',
                'company': 'TechCorp',
                'duration': '6 months',
                'description': 'Built RAG systems with LangChain',
            }
        ],
        education=[{'degree': 'Bachelor of Technology in CSE'}],
        projects=[
            {
                'name': 'Voice Agent',
                'description': 'Built LLM-powered voice agent with RAG',
                'technologies': ['python', 'openai', 'langchain'],
            }
        ],
        summary='ML enthusiast with LLM experience',
    )
    
    # Calculate match
    match_score = matcher.match(job, profile)
    
    # Print results
    print("\n=== Job Match Results ===")
    print(f"\nOverall Score: {match_score.overall_score:.1f}/100")
    print(f"Recommendation: {match_score.get_recommendation()}")
    print(f"Confidence: {match_score.confidence:.2f}")
    
    print("\n Component Scores:")
    print(f"  - Semantic Similarity: {match_score.semantic_similarity:.1f}")
    print(f"  - Skill Match: {match_score.skill_match:.1f}")
    print(f"  - Experience Match: {match_score.experience_match:.1f}")
    print(f"  - Education Match: {match_score.education_match:.1f}")
    print(f"  - Project Relevance: {match_score.project_relevance:.1f}")
    
    print("\n Strengths:")
    for reason in match_score.match_reasons:
        print(f"  ✓ {reason}")
    
    if match_score.concerns:
        print("\n Concerns:")
        for concern in match_score.concerns:
            print(f"  ⚠ {concern}")


if __name__ == "__main__":
    main()
