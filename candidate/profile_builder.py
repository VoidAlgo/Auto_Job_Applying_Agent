"""
Comprehensive candidate profile builder.
Integrates resume parsing, GitHub analysis, LinkedIn scraping, and project knowledge base.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from candidate.embedding_generator import CandidateEmbeddings
from candidate.github_analyzer import GitHubAnalyzer
from candidate.knowledge_base import ProjectKnowledgeBase
from candidate.linkedin_analyzer import LinkedInAnalyzer
from candidate.resume_parser import ResumeParser
from config.config_manager import get_config


class CandidateProfileBuilder:
    """Build comprehensive candidate profile from multiple sources."""
    
    def __init__(self):
        """Initialize profile builder."""
        self.config = get_config()
        self.profile: Dict[str, Any] = {}
        self.embeddings_manager: Optional[CandidateEmbeddings] = None
        self.knowledge_base: Optional[ProjectKnowledgeBase] = None
    
    def build(self, 
              include_resume: bool = True,
              include_github: bool = True,
              include_linkedin: bool = False,  # Optional due to scraping complexity
              include_projects: bool = True) -> Dict[str, Any]:
        """
        Build comprehensive candidate profile.
        
        Args:
            include_resume: Parse resume PDF
            include_github: Analyze GitHub profile
            include_linkedin: Scrape LinkedIn profile (requires credentials)
            include_projects: Load project knowledge base
            
        Returns:
            Complete candidate profile
        """
        logger.info("Building candidate profile...")
        
        # Initialize profile with config data
        self.profile = {
            "personal": self._get_personal_info(),
            "links": self._get_links(),
            "target_roles": self.config.candidate_profile.target_roles,
            "preferences": self._get_preferences(),
        }
        
        # Parse resume
        if include_resume:
            logger.info("Parsing resume...")
            try:
                resume_data = self._parse_resume()
                self.profile["resume"] = resume_data
                logger.info("✓ Resume parsed successfully")
            except Exception as e:
                logger.error(f"Resume parsing failed: {e}")
                self.profile["resume"] = {}
        
        # Analyze GitHub
        if include_github:
            logger.info("Analyzing GitHub profile...")
            try:
                github_data = self._analyze_github()
                self.profile["github"] = github_data
                logger.info("✓ GitHub analysis completed")
            except Exception as e:
                logger.error(f"GitHub analysis failed: {e}")
                self.profile["github"] = {}
        
        # Analyze LinkedIn (optional)
        if include_linkedin:
            logger.info("Analyzing LinkedIn profile...")
            try:
                linkedin_data = self._analyze_linkedin()
                self.profile["linkedin"] = linkedin_data
                logger.info("✓ LinkedIn analysis completed")
            except Exception as e:
                logger.warning(f"LinkedIn analysis failed: {e}")
                self.profile["linkedin"] = {}
        
        # Load projects
        if include_projects:
            logger.info("Loading project knowledge base...")
            try:
                self.knowledge_base = ProjectKnowledgeBase()
                self.knowledge_base.load_projects()
                self.knowledge_base.build_index()
                self.profile["projects"] = self.knowledge_base.projects
                logger.info(f"✓ Loaded {len(self.knowledge_base.projects)} projects")
            except Exception as e:
                logger.error(f"Project loading failed: {e}")
                self.profile["projects"] = []
        
        # Merge and deduplicate data
        self._merge_profile_data()
        
        # Generate embeddings
        self._generate_embeddings()
        
        # Add metadata
        self.profile["metadata"] = {
            "build_date": self._get_current_timestamp(),
            "version": "1.0",
            "sources": {
                "resume": include_resume,
                "github": include_github,
                "linkedin": include_linkedin,
                "projects": include_projects,
            }
        }
        
        logger.info("✓ Candidate profile built successfully")
        return self.profile
    
    def _get_personal_info(self) -> Dict[str, str]:
        """Get personal information from config."""
        return {
            "name": self.config.candidate_profile.personal.name,
            "email": self.config.candidate_profile.personal.email,
            "phone": self.config.candidate_profile.personal.phone,
            "location": self.config.candidate_profile.personal.location,
        }
    
    def _get_links(self) -> Dict[str, str]:
        """Get professional links from config."""
        return {
            "github": self.config.candidate_profile.links.github,
            "linkedin": self.config.candidate_profile.links.linkedin,
            "leetcode": self.config.candidate_profile.links.leetcode or "",
            "portfolio": self.config.candidate_profile.links.portfolio or "",
        }
    
    def _get_preferences(self) -> Dict[str, Any]:
        """Get candidate preferences from config."""
        prefs = self.config.candidate_profile.preferences
        return {
            "work_type": prefs.work_type,
            "locations": prefs.locations,
            "company_size": prefs.company_size,
            "company_stage": prefs.company_stage if hasattr(prefs, 'company_stage') else [],
            "salary_expectations": prefs.salary_expectations if hasattr(prefs, 'salary_expectations') else {},
        }
    
    def _parse_resume(self) -> Dict[str, Any]:
        """Parse resume PDF."""
        parser = ResumeParser()
        return parser.parse()
    
    def _analyze_github(self) -> Dict[str, Any]:
        """Analyze GitHub profile."""
        analyzer = GitHubAnalyzer()
        return analyzer.analyze()
    
    def _analyze_linkedin(self) -> Dict[str, Any]:
        """Analyze LinkedIn profile."""
        analyzer = LinkedInAnalyzer()
        
        # Check if credentials are available
        import os
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")
        
        if email and password:
            return analyzer.analyze(email, password)
        else:
            logger.warning("LinkedIn credentials not available")
            return {}
    
    def _merge_profile_data(self) -> None:
        """Merge and deduplicate data from multiple sources."""
        logger.info("Merging profile data from multiple sources...")
        
        # Merge skills
        all_skills = {}
        
        # From resume
        if self.profile.get("resume", {}).get("skills"):
            for category, skills in self.profile["resume"]["skills"].items():
                all_skills[category] = set(skills)
        
        # From GitHub
        if self.profile.get("github", {}).get("languages"):
            if "programming_languages" not in all_skills:
                all_skills["programming_languages"] = set()
            all_skills["programming_languages"].update(self.profile["github"]["languages"].keys())
        
        # From LinkedIn
        if self.profile.get("linkedin", {}).get("skills"):
            if "all_skills" not in all_skills:
                all_skills["all_skills"] = set()
            all_skills["all_skills"].update(self.profile["linkedin"]["skills"])
        
        # Convert sets back to lists
        self.profile["merged_skills"] = {
            category: sorted(list(skills))
            for category, skills in all_skills.items()
        }
        
        # Merge experience
        all_experience = []
        
        if self.profile.get("resume", {}).get("experience"):
            all_experience.extend(self.profile["resume"]["experience"])
        
        if self.profile.get("linkedin", {}).get("experience"):
            # Deduplicate by company name
            existing_companies = {exp.get("company", "") for exp in all_experience}
            for exp in self.profile["linkedin"]["experience"]:
                if exp.get("company") not in existing_companies:
                    all_experience.append(exp)
        
        self.profile["merged_experience"] = all_experience
        
        logger.info("✓ Profile data merged")
    
    def _generate_embeddings(self) -> None:
        """Generate embeddings for candidate profile."""
        logger.info("Generating profile embeddings...")
        
        self.embeddings_manager = CandidateEmbeddings()
        embeddings = self.embeddings_manager.generate_profile_embeddings(self.profile)
        
        # Store embedding metadata (not the full arrays)
        self.profile["embeddings_metadata"] = {
            "dimension": embeddings["overall"].shape[0],
            "components": list(embeddings.keys()),
        }
        
        logger.info("✓ Profile embeddings generated")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_summary(self) -> str:
        """
        Get text summary of candidate profile.
        
        Returns:
            Profile summary
        """
        if not self.profile:
            return "Profile not built yet"
        
        parts = []
        
        # Personal info
        personal = self.profile.get("personal", {})
        parts.append(f"Name: {personal.get('name', 'N/A')}")
        parts.append(f"Location: {personal.get('location', 'N/A')}")
        
        # Skills
        skills = self.profile.get("merged_skills", {})
        all_skills = []
        for category, items in skills.items():
            all_skills.extend(items[:5])  # Top 5 from each category
        if all_skills:
            parts.append(f"Key Skills: {', '.join(all_skills[:10])}")
        
        # Experience
        experience = self.profile.get("merged_experience", [])
        if experience:
            parts.append(f"Experience: {len(experience)} positions")
        
        # Projects
        projects = self.profile.get("projects", [])
        if projects:
            parts.append(f"Projects: {len(projects)} key projects")
        
        # GitHub
        github = self.profile.get("github", {})
        if github.get("basic_info"):
            repos = github["basic_info"].get("public_repos", 0)
            parts.append(f"GitHub: {repos} repositories")
        
        return " | ".join(parts)
    
    def save(self, filepath: str) -> None:
        """
        Save profile to JSON file.
        
        Args:
            filepath: Path to save profile
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save main profile (without embeddings arrays)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.profile, f, indent=2, default=str)
        
        logger.info(f"Saved profile to {filepath}")
        
        # Save embeddings separately
        if self.embeddings_manager:
            embeddings_path = str(output_path.with_suffix('.embeddings'))
            self.embeddings_manager.save_embeddings(embeddings_path)
        
        # Save knowledge base index
        if self.knowledge_base:
            kb_path = str(output_path.with_suffix('').with_name(f"{output_path.stem}_kb"))
            self.knowledge_base.save_index(kb_path)
    
    def load(self, filepath: str) -> Dict[str, Any]:
        """
        Load profile from JSON file.
        
        Args:
            filepath: Path to load profile from
            
        Returns:
            Loaded profile
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)
        
        logger.info(f"Loaded profile from {filepath}")
        
        # Load embeddings
        embeddings_path = Path(filepath).with_suffix('.embeddings.npz')
        if embeddings_path.exists():
            self.embeddings_manager = CandidateEmbeddings()
            self.embeddings_manager.load_embeddings(str(embeddings_path))
        
        # Load knowledge base
        output_path = Path(filepath)
        kb_path = str(output_path.with_suffix('').with_name(f"{output_path.stem}_kb"))
        kb_index_path = Path(f"{kb_path}.index")
        
        if kb_index_path.exists():
            self.knowledge_base = ProjectKnowledgeBase()
            self.knowledge_base.load_index(kb_path)
        
        return self.profile
    
    def get_knowledge_base(self) -> Optional[ProjectKnowledgeBase]:
        """Get project knowledge base."""
        return self.knowledge_base
    
    def get_embeddings_manager(self) -> Optional[CandidateEmbeddings]:
        """Get embeddings manager."""
        return self.embeddings_manager


def build_candidate_profile() -> CandidateProfileBuilder:
    """
    Convenience function to build candidate profile.
    
    Returns:
        CandidateProfileBuilder with built profile
    """
    builder = CandidateProfileBuilder()
    builder.build(
        include_resume=True,
        include_github=True,
        include_linkedin=False,  # Set to True if LinkedIn credentials available
        include_projects=True,
    )
    return builder
