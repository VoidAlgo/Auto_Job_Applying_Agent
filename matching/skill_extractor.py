"""
Skill Extractor - NLP-based Skill Extraction from Job Descriptions

This module extracts technical skills, soft skills, tools, and technologies from
job descriptions using spaCy NLP, pattern matching, and domain knowledge.

Author: Auto Job Applier System
Date: December 2025
"""

import re
from typing import List, Set, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

import spacy
from spacy.matcher import PhraseMatcher
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedSkills:
    """Container for extracted skills from a job description."""
    
    # Technical Skills
    programming_languages: Set[str] = field(default_factory=set)
    frameworks: Set[str] = field(default_factory=set)
    ml_frameworks: Set[str] = field(default_factory=set)
    tools: Set[str] = field(default_factory=set)
    databases: Set[str] = field(default_factory=set)
    cloud_platforms: Set[str] = field(default_factory=set)
    
    # AI/ML Specific
    ai_ml_skills: Set[str] = field(default_factory=set)
    llm_skills: Set[str] = field(default_factory=set)
    
    # Soft Skills
    soft_skills: Set[str] = field(default_factory=set)
    
    # Experience Requirements
    years_required: Optional[int] = None
    education_level: Optional[str] = None
    
    # Raw extracted entities
    all_skills: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'programming_languages': list(self.programming_languages),
            'frameworks': list(self.frameworks),
            'ml_frameworks': list(self.ml_frameworks),
            'tools': list(self.tools),
            'databases': list(self.databases),
            'cloud_platforms': list(self.cloud_platforms),
            'ai_ml_skills': list(self.ai_ml_skills),
            'llm_skills': list(self.llm_skills),
            'soft_skills': list(self.soft_skills),
            'years_required': self.years_required,
            'education_level': self.education_level,
            'all_skills': list(self.all_skills),
        }


class SkillExtractor:
    """
    Extract skills from job descriptions using NLP and pattern matching.
    
    Uses spaCy for entity recognition and custom matchers for domain-specific
    skills relevant to AI/ML engineering positions.
    """
    
    # Skill taxonomies for AI/ML roles
    PROGRAMMING_LANGUAGES = {
        'python', 'r', 'java', 'javascript', 'typescript', 'c++', 'cpp',
        'c#', 'csharp', 'go', 'golang', 'rust', 'scala', 'julia', 'sql',
        'bash', 'shell', 'matlab'
    }
    
    FRAMEWORKS = {
        'django', 'flask', 'fastapi', 'react', 'vue', 'angular', 'node.js',
        'nodejs', 'express', 'spring', 'dotnet', '.net', 'next.js', 'nextjs'
    }
    
    ML_FRAMEWORKS = {
        'pytorch', 'tensorflow', 'keras', 'scikit-learn', 'sklearn',
        'xgboost', 'lightgbm', 'catboost', 'jax', 'mxnet', 'paddlepaddle',
        'hugging face', 'huggingface', 'transformers', 'langchain',
        'llamaindex', 'haystack', 'spacy', 'nltk', 'gensim'
    }
    
    TOOLS = {
        'git', 'docker', 'kubernetes', 'jenkins', 'github actions',
        'gitlab ci', 'terraform', 'ansible', 'jupyter', 'vscode',
        'pycharm', 'databricks', 'mlflow', 'wandb', 'tensorboard',
        'airflow', 'kafka', 'spark', 'hadoop', 'elasticsearch'
    }
    
    DATABASES = {
        'postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'cassandra',
        'dynamodb', 'firestore', 'sqlite', 'oracle', 'mssql', 'sql server',
        'neo4j', 'pinecone', 'weaviate', 'qdrant', 'chroma', 'faiss'
    }
    
    CLOUD_PLATFORMS = {
        'aws', 'amazon web services', 'azure', 'microsoft azure', 'gcp',
        'google cloud', 'google cloud platform', 'heroku', 'vercel',
        'netlify', 'digital ocean', 'digitalocean'
    }
    
    AI_ML_SKILLS = {
        'machine learning', 'deep learning', 'neural networks', 'nlp',
        'natural language processing', 'computer vision', 'cv',
        'reinforcement learning', 'supervised learning', 'unsupervised learning',
        'transfer learning', 'fine-tuning', 'model training', 'hyperparameter tuning',
        'feature engineering', 'data preprocessing', 'data augmentation',
        'model evaluation', 'cross-validation', 'a/b testing',
        'statistical modeling', 'time series', 'forecasting', 'anomaly detection',
        'recommendation systems', 'information retrieval', 'search algorithms'
    }
    
    LLM_SKILLS = {
        'llm', 'large language models', 'gpt', 'chatgpt', 'claude',
        'prompt engineering', 'prompt tuning', 'rag', 'retrieval augmented generation',
        'vector databases', 'embeddings', 'semantic search', 'text generation',
        'text classification', 'sentiment analysis', 'named entity recognition',
        'ner', 'question answering', 'summarization', 'translation',
        'few-shot learning', 'zero-shot learning', 'in-context learning',
        'chain of thought', 'agents', 'ai agents', 'langchain', 'llamaindex',
        'openai api', 'anthropic api', 'hugging face', 'transformers'
    }
    
    SOFT_SKILLS = {
        'communication', 'teamwork', 'problem solving', 'critical thinking',
        'analytical', 'leadership', 'collaboration', 'adaptability',
        'time management', 'creativity', 'attention to detail', 'self-motivated',
        'fast learner', 'quick learner', 'agile', 'scrum', 'remote work'
    }
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize the skill extractor.
        
        Args:
            spacy_model: Name of spaCy model to use (default: en_core_web_sm)
        """
        self.logger = logger
        
        try:
            self.nlp = spacy.load(spacy_model)
            self.logger.info(f"Loaded spaCy model: {spacy_model}")
        except OSError:
            self.logger.warning(
                f"spaCy model '{spacy_model}' not found. "
                f"Install with: python -m spacy download {spacy_model}"
            )
            # Create blank model as fallback
            self.nlp = spacy.blank("en")
            self.logger.info("Using blank spaCy model as fallback")
        
        # Initialize phrase matchers for each skill category
        self._init_matchers()
    
    def _init_matchers(self) -> None:
        """Initialize PhraseMatcher for each skill category."""
        self.matchers = {}
        
        skill_categories = {
            'programming_languages': self.PROGRAMMING_LANGUAGES,
            'frameworks': self.FRAMEWORKS,
            'ml_frameworks': self.ML_FRAMEWORKS,
            'tools': self.TOOLS,
            'databases': self.DATABASES,
            'cloud_platforms': self.CLOUD_PLATFORMS,
            'ai_ml_skills': self.AI_ML_SKILLS,
            'llm_skills': self.LLM_SKILLS,
            'soft_skills': self.SOFT_SKILLS,
        }
        
        for category, skills in skill_categories.items():
            matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            patterns = [self.nlp.make_doc(skill) for skill in skills]
            matcher.add(category, patterns)
            self.matchers[category] = matcher
    
    def extract(self, text: str) -> ExtractedSkills:
        """
        Extract skills from job description text.
        
        Args:
            text: Job description text
            
        Returns:
            ExtractedSkills object with categorized skills
        """
        if not text:
            self.logger.warning("Empty text provided for skill extraction")
            return ExtractedSkills()
        
        # Preprocess text
        text = self._preprocess_text(text)
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Extract skills using matchers
        skills = ExtractedSkills()
        
        for category, matcher in self.matchers.items():
            matches = matcher(doc)
            matched_skills = {doc[start:end].text.lower() for _, start, end in matches}
            
            if category == 'programming_languages':
                skills.programming_languages = matched_skills
            elif category == 'frameworks':
                skills.frameworks = matched_skills
            elif category == 'ml_frameworks':
                skills.ml_frameworks = matched_skills
            elif category == 'tools':
                skills.tools = matched_skills
            elif category == 'databases':
                skills.databases = matched_skills
            elif category == 'cloud_platforms':
                skills.cloud_platforms = matched_skills
            elif category == 'ai_ml_skills':
                skills.ai_ml_skills = matched_skills
            elif category == 'llm_skills':
                skills.llm_skills = matched_skills
            elif category == 'soft_skills':
                skills.soft_skills = matched_skills
            
            skills.all_skills.update(matched_skills)
        
        # Extract experience requirements
        skills.years_required = self._extract_years_experience(text)
        skills.education_level = self._extract_education_level(text)
        
        self.logger.info(
            f"Extracted {len(skills.all_skills)} unique skills: "
            f"{len(skills.programming_languages)} languages, "
            f"{len(skills.ml_frameworks)} ML frameworks, "
            f"{len(skills.llm_skills)} LLM skills"
        )
        
        return skills
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better skill extraction.
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text
        """
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common variations
        replacements = {
            'node.js': 'nodejs',
            'next.js': 'nextjs',
            'c++': 'cpp',
            'c#': 'csharp',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def _extract_years_experience(self, text: str) -> Optional[int]:
        """
        Extract years of experience requirement.
        
        Args:
            text: Job description text
            
        Returns:
            Number of years required or None
        """
        # Patterns for experience requirements
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
            r'experience\s+(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+in',
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                years = int(match.group(1))
                self.logger.debug(f"Extracted experience requirement: {years} years")
                return years
        
        return None
    
    def _extract_education_level(self, text: str) -> Optional[str]:
        """
        Extract education level requirement.
        
        Args:
            text: Job description text
            
        Returns:
            Education level or None
        """
        text_lower = text.lower()
        
        education_levels = {
            'phd': ['phd', 'ph.d', 'doctorate', 'doctoral'],
            'masters': ['masters', "master's", 'ms', 'm.s', 'msc', 'm.sc'],
            'bachelors': ['bachelors', "bachelor's", 'bs', 'b.s', 'bsc', 'b.sc', 'ba', 'b.a'],
        }
        
        for level, keywords in education_levels.items():
            if any(keyword in text_lower for keyword in keywords):
                self.logger.debug(f"Extracted education level: {level}")
                return level
        
        return None
    
    def calculate_skill_overlap(
        self,
        job_skills: ExtractedSkills,
        candidate_skills: Set[str]
    ) -> Dict[str, Any]:
        """
        Calculate overlap between job requirements and candidate skills.
        
        Args:
            job_skills: Extracted skills from job description
            candidate_skills: Set of candidate skills
            
        Returns:
            Dictionary with overlap statistics
        """
        # Normalize candidate skills
        candidate_skills_lower = {skill.lower() for skill in candidate_skills}
        
        # Calculate overlaps for each category
        overlaps = {}
        total_required = len(job_skills.all_skills)
        total_matched = 0
        
        categories = {
            'programming_languages': job_skills.programming_languages,
            'ml_frameworks': job_skills.ml_frameworks,
            'llm_skills': job_skills.llm_skills,
            'tools': job_skills.tools,
            'databases': job_skills.databases,
            'cloud_platforms': job_skills.cloud_platforms,
        }
        
        for category, required_skills in categories.items():
            if required_skills:
                matched = required_skills & candidate_skills_lower
                overlaps[category] = {
                    'required': len(required_skills),
                    'matched': len(matched),
                    'percentage': len(matched) / len(required_skills) * 100,
                    'missing': list(required_skills - candidate_skills_lower),
                }
                total_matched += len(matched)
        
        # Overall match percentage
        match_percentage = (total_matched / total_required * 100) if total_required > 0 else 0
        
        self.logger.info(
            f"Skill overlap: {total_matched}/{total_required} "
            f"({match_percentage:.1f}%) matched"
        )
        
        return {
            'total_required': total_required,
            'total_matched': total_matched,
            'match_percentage': match_percentage,
            'category_overlaps': overlaps,
        }


def main():
    """Example usage of SkillExtractor."""
    # Sample job description
    job_description = """
    We're looking for a Machine Learning Engineer to join our AI team.
    
    Requirements:
    - 0-2 years of experience in ML/AI
    - Strong Python programming skills
    - Experience with PyTorch or TensorFlow
    - Knowledge of LLMs, RAG, and prompt engineering
    - Familiarity with LangChain or LlamaIndex
    - Experience with vector databases (Pinecone, FAISS)
    - AWS or Azure cloud experience
    - Bachelor's degree in Computer Science or related field
    
    Nice to have:
    - Experience with Hugging Face Transformers
    - Docker and Kubernetes knowledge
    - FastAPI or Django experience
    """
    
    # Initialize extractor
    extractor = SkillExtractor()
    
    # Extract skills
    skills = extractor.extract(job_description)
    
    # Print results
    print("\n=== Extracted Skills ===")
    print(f"\nProgramming Languages: {skills.programming_languages}")
    print(f"ML Frameworks: {skills.ml_frameworks}")
    print(f"LLM Skills: {skills.llm_skills}")
    print(f"Tools: {skills.tools}")
    print(f"Databases: {skills.databases}")
    print(f"Cloud Platforms: {skills.cloud_platforms}")
    print(f"\nYears Required: {skills.years_required}")
    print(f"Education Level: {skills.education_level}")
    print(f"\nTotal Skills: {len(skills.all_skills)}")
    
    # Calculate overlap with candidate
    candidate_skills = {
        'python', 'pytorch', 'langchain', 'faiss', 'docker',
        'fastapi', 'rag', 'prompt engineering', 'machine learning'
    }
    
    overlap = extractor.calculate_skill_overlap(skills, candidate_skills)
    print(f"\n=== Skill Match ===")
    print(f"Match: {overlap['total_matched']}/{overlap['total_required']} "
          f"({overlap['match_percentage']:.1f}%)")


if __name__ == "__main__":
    main()
