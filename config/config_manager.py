"""
Utility functions for loading and validating configuration files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class PersonalInfo(BaseModel):
    """Personal information model."""
    name: str
    email: str
    phone: str
    location: str


class Links(BaseModel):
    """Professional links model."""
    github: str
    linkedin: str
    leetcode: Optional[str] = None
    portfolio: Optional[str] = None


class Documents(BaseModel):
    """Document paths model."""
    resume: str
    projects_folder: str
    certifications_folder: Optional[str] = None


class Preferences(BaseModel):
    """Candidate preferences model."""
    work_type: list[str]
    locations: Dict[str, list[str]]
    company_size: list[str]
    company_stage: Optional[list[str]] = None
    salary_expectations: Optional[Dict[str, Any]] = None


class CandidateProfile(BaseModel):
    """Complete candidate profile model."""
    personal: PersonalInfo
    links: Links
    documents: Documents
    target_roles: Dict[str, list[str]]
    preferences: Preferences
    skills: Optional[Dict[str, list[str]]] = None
    key_projects: Optional[list[Dict[str, Any]]] = None
    experience: Optional[Dict[str, Any]] = None
    certifications: Optional[list[Dict[str, str]]] = None
    education: Optional[Dict[str, str]] = None
    availability: Optional[Dict[str, Any]] = None
    additional: Optional[Dict[str, Any]] = None


class ApplicationSettings(BaseModel):
    """Application settings model."""
    max_applications_per_day: int = Field(default=15, ge=1, le=50)
    match_score_threshold: float = Field(default=70.0, ge=0.0, le=100.0)
    auto_approve_threshold: float = Field(default=90.0, ge=0.0, le=100.0)
    manual_review_count: int = Field(default=20, ge=0)
    rate_limit_delay: int = Field(default=300, ge=60)


class Settings(BaseModel):
    """Complete settings model."""
    application: ApplicationSettings
    job_criteria: Dict[str, Any]
    matching: Dict[str, Any]
    job_boards: Dict[str, Any]
    scraping: Dict[str, Any]
    llm: Dict[str, Any]
    database: Dict[str, Any]
    follow_up: Dict[str, Any]
    customization: Dict[str, Any]
    logging: Dict[str, Any]


class Config:
    """Configuration manager for the job application system."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Path to configuration directory. Defaults to ./config/
        """
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.project_root = Path(__file__).parent.parent
        
        # Load environment variables
        load_dotenv(self.project_root / ".env")
        
        # Load configuration files
        self.settings: Settings = self._load_settings()
        self.candidate_profile: CandidateProfile = self._load_candidate_profile()
        
        # Environment variables
        self.env = self._load_environment()
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_settings(self) -> Settings:
        """Load application settings."""
        data = self._load_yaml("settings.yaml")
        return Settings(**data)
    
    def _load_candidate_profile(self) -> CandidateProfile:
        """Load candidate profile."""
        data = self._load_yaml("candidate_profile.yaml")
        return CandidateProfile(**data)
    
    def _load_environment(self) -> Dict[str, str]:
        """Load environment variables."""
        return {
            # API Keys
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY", ""),
            "PINECONE_ENVIRONMENT": os.getenv("PINECONE_ENVIRONMENT", ""),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", ""),
            "LINKEDIN_EMAIL": os.getenv("LINKEDIN_EMAIL", ""),
            "LINKEDIN_PASSWORD": os.getenv("LINKEDIN_PASSWORD", ""),
            "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY", ""),
            
            # Proxy
            "PROXY_URL": os.getenv("PROXY_URL", ""),
            "PROXY_USERNAME": os.getenv("PROXY_USERNAME", ""),
            "PROXY_PASSWORD": os.getenv("PROXY_PASSWORD", ""),
            
            # Database
            "DATABASE_URL": os.getenv(
                "DATABASE_URL", 
                f"sqlite:///{self.project_root}/data/job_agent.db"
            ),
            
            # Logging
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "LOG_FILE": os.getenv("LOG_FILE", "logs/job_agent.log"),
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return {
            "provider": self.settings.llm["provider"],
            "model": self.settings.llm["model"],
            "temperature": self.settings.llm["temperature"],
            "max_tokens": self.settings.llm["max_tokens"],
            "api_key": self._get_llm_api_key(),
        }
    
    def _get_llm_api_key(self) -> str:
        """Get appropriate API key based on LLM provider."""
        provider = self.settings.llm["provider"].lower()
        if provider == "anthropic":
            return self.env["ANTHROPIC_API_KEY"]
        elif provider == "openai":
            return self.env["OPENAI_API_KEY"]
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def get_embeddings_config(self) -> Dict[str, Any]:
        """Get embeddings configuration."""
        return {
            "provider": self.settings.llm["embeddings"]["provider"],
            "model": self.settings.llm["embeddings"]["model"],
            "dimension": self.settings.llm["embeddings"]["dimension"],
            "api_key": self.env["OPENAI_API_KEY"],
        }
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        return self.env["DATABASE_URL"]
    
    def get_resume_path(self) -> Path:
        """Get absolute path to resume."""
        resume_path = Path(self.candidate_profile.documents.resume)
        if not resume_path.is_absolute():
            resume_path = self.project_root / resume_path
        return resume_path
    
    def get_projects_folder(self) -> Path:
        """Get absolute path to projects folder."""
        projects_path = Path(self.candidate_profile.documents.projects_folder)
        if not projects_path.is_absolute():
            projects_path = self.project_root / projects_path
        return projects_path
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        errors = []
        
        # Check API keys
        if self.settings.llm["provider"] == "anthropic" and not self.env["ANTHROPIC_API_KEY"]:
            errors.append("ANTHROPIC_API_KEY not set")
        
        if self.settings.llm["provider"] == "openai" and not self.env["OPENAI_API_KEY"]:
            errors.append("OPENAI_API_KEY not set")
        
        if self.settings.llm["embeddings"]["provider"] == "openai" and not self.env["OPENAI_API_KEY"]:
            errors.append("OPENAI_API_KEY required for embeddings")
        
        # Check resume exists
        resume_path = self.get_resume_path()
        if not resume_path.exists():
            errors.append(f"Resume not found: {resume_path}")
        
        # Check projects folder exists
        projects_path = self.get_projects_folder()
        if not projects_path.exists():
            errors.append(f"Projects folder not found: {projects_path}")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors))
        
        return True


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """
    Reload configuration from files.
    
    Returns:
        New Config instance
    """
    global _config
    _config = Config()
    return _config
