"""
Resume parser to extract structured information from PDF resumes.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import PyPDF2
import pdfplumber
from loguru import logger

from config.config_manager import get_config


class ResumeParser:
    """Parse resume PDF and extract structured information."""
    
    def __init__(self, resume_path: Optional[Path] = None):
        """
        Initialize resume parser.
        
        Args:
            resume_path: Path to resume PDF. If None, uses config value.
        """
        config = get_config()
        self.resume_path = resume_path or config.get_resume_path()
        
        if not self.resume_path.exists():
            raise FileNotFoundError(f"Resume not found: {self.resume_path}")
        
        self.raw_text: Optional[str] = None
        self.parsed_data: Optional[Dict[str, Any]] = None
    
    def extract_text(self) -> str:
        """
        Extract text from PDF resume.
        
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from resume: {self.resume_path}")
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(self.resume_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                
                if text.strip():
                    self.raw_text = text
                    logger.info(f"Extracted {len(text)} characters using pdfplumber")
                    return text
        
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}, trying PyPDF2")
        
        # Fallback to PyPDF2
        try:
            with open(self.resume_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                
                self.raw_text = text
                logger.info(f"Extracted {len(text)} characters using PyPDF2")
                return text
        
        except Exception as e:
            logger.error(f"Failed to extract text from resume: {e}")
            raise
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse resume and extract structured information.
        
        Returns:
            Parsed resume data
        """
        if not self.raw_text:
            self.extract_text()
        
        logger.info("Parsing resume data...")
        
        self.parsed_data = {
            "contact": self._extract_contact_info(),
            "education": self._extract_education(),
            "experience": self._extract_experience(),
            "skills": self._extract_skills(),
            "projects": self._extract_projects(),
            "certifications": self._extract_certifications(),
            "achievements": self._extract_achievements(),
        }
        
        logger.info("Resume parsing completed")
        return self.parsed_data
    
    def _extract_contact_info(self) -> Dict[str, Optional[str]]:
        """Extract contact information."""
        contact = {
            "email": None,
            "phone": None,
            "linkedin": None,
            "github": None,
            "location": None,
        }
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, self.raw_text)
        if emails:
            contact["email"] = emails[0]
        
        # Phone (Indian format)
        phone_patterns = [
            r'\+91[-\s]?\d{10}',
            r'\d{10}',
            r'\+91[-\s]?\d{5}[-\s]?\d{5}',
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, self.raw_text)
            if phones:
                contact["phone"] = phones[0]
                break
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9_-]+'
        linkedins = re.findall(linkedin_pattern, self.raw_text, re.IGNORECASE)
        if linkedins:
            contact["linkedin"] = f"https://{linkedins[0]}"
        
        # GitHub
        github_pattern = r'github\.com/[A-Za-z0-9_-]+'
        githubs = re.findall(github_pattern, self.raw_text, re.IGNORECASE)
        if githubs:
            contact["github"] = f"https://{githubs[0]}"
        
        # Location (look for Indian cities)
        indian_cities = [
            "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Hyderabad", 
            "Chennai", "Kolkata", "Pune", "Ahmedabad", "Coimbatore",
        ]
        for city in indian_cities:
            if city.lower() in self.raw_text.lower():
                contact["location"] = city
                break
        
        return contact
    
    def _extract_education(self) -> List[Dict[str, str]]:
        """Extract education information."""
        education = []
        
        # Look for education section
        education_pattern = r'(?:EDUCATION|Education|Academic)(.*?)(?:EXPERIENCE|Experience|PROJECTS|Projects|SKILLS|$)'
        matches = re.search(education_pattern, self.raw_text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            edu_section = matches.group(1)
            
            # Extract degree information
            degree_patterns = [
                r'(B\.?Tech|Bachelor of Technology|B\.?E|Bachelor of Engineering|M\.?Tech|Master of Technology|PhD)',
                r'(Computer Science|CSE|AI|ML|Artificial Intelligence|Machine Learning)',
            ]
            
            # Extract year
            year_pattern = r'(20\d{2})'
            years = re.findall(year_pattern, edu_section)
            
            # Extract institution
            lines = edu_section.split('\n')
            institution = None
            for line in lines:
                if len(line.strip()) > 20 and any(word in line.lower() for word in ['college', 'university', 'institute']):
                    institution = line.strip()
                    break
            
            education.append({
                "degree": "Bachelor of Technology",  # Default, can be improved
                "major": "Computer Science / AI & ML",
                "institution": institution or "Not found",
                "year": years[0] if years else "Not found",
            })
        
        return education
    
    def _extract_experience(self) -> List[Dict[str, Any]]:
        """Extract work experience."""
        experience = []
        
        # Look for experience section
        exp_pattern = r'(?:EXPERIENCE|Experience|Work Experience|Internship)(.*?)(?:EDUCATION|Education|PROJECTS|Projects|SKILLS|$)'
        matches = re.search(exp_pattern, self.raw_text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            exp_section = matches.group(1)
            
            # Extract company names (capitalized words, possibly with acronyms)
            lines = exp_section.split('\n')
            current_exp = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is a company/position header
                if any(keyword in line.lower() for keyword in ['intern', 'engineer', 'developer', 'analyst']):
                    if current_exp:
                        experience.append(current_exp)
                    
                    current_exp = {
                        "position": line,
                        "company": "To be extracted",
                        "duration": "To be extracted",
                        "responsibilities": [],
                    }
                
                elif current_exp and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    current_exp["responsibilities"].append(line.lstrip('•-* '))
            
            if current_exp:
                experience.append(current_exp)
        
        return experience
    
    def _extract_skills(self) -> Dict[str, List[str]]:
        """Extract skills categorized by type."""
        skills = {
            "programming_languages": [],
            "ml_frameworks": [],
            "llm_tools": [],
            "databases": [],
            "cloud_platforms": [],
            "tools": [],
            "soft_skills": [],
        }
        
        # Define skill keywords
        skill_mappings = {
            "programming_languages": [
                "Python", "Java", "JavaScript", "TypeScript", "C++", "C", "Go", "Rust",
                "SQL", "R", "Scala", "Julia",
            ],
            "ml_frameworks": [
                "PyTorch", "TensorFlow", "Keras", "scikit-learn", "XGBoost", "LightGBM",
                "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Hugging Face",
                "Transformers", "spaCy", "NLTK",
            ],
            "llm_tools": [
                "LangChain", "LlamaIndex", "OpenAI", "GPT", "Claude", "Llama",
                "RAG", "Prompt Engineering", "Fine-tuning", "PEFT", "LoRA",
                "Embeddings", "Vector Database",
            ],
            "databases": [
                "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
                "Pinecone", "FAISS", "Chroma", "Weaviate", "Qdrant",
            ],
            "cloud_platforms": [
                "AWS", "Azure", "GCP", "Google Cloud", "Oracle Cloud",
                "Docker", "Kubernetes", "Terraform",
            ],
            "tools": [
                "Git", "GitHub", "GitLab", "Jupyter", "VS Code", "PyCharm",
                "FastAPI", "Flask", "Django", "Streamlit", "Gradio",
                "Selenium", "BeautifulSoup", "Scrapy",
            ],
        }
        
        text_lower = self.raw_text.lower()
        
        for category, keywords in skill_mappings.items():
            for skill in keywords:
                if skill.lower() in text_lower:
                    skills[category].append(skill)
        
        # Remove duplicates
        for category in skills:
            skills[category] = list(set(skills[category]))
        
        return skills
    
    def _extract_projects(self) -> List[Dict[str, Any]]:
        """Extract project information."""
        projects = []
        
        # Look for projects section
        proj_pattern = r'(?:PROJECTS|Projects|Key Projects)(.*?)(?:EXPERIENCE|Experience|EDUCATION|Education|SKILLS|Certifications|$)'
        matches = re.search(proj_pattern, self.raw_text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            proj_section = matches.group(1)
            
            # Split by project (look for capitalized titles)
            lines = proj_section.split('\n')
            current_project = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is a project title (mostly capitalized or title case)
                if len(line) > 10 and (line[0].isupper() or line.isupper()) and not line.startswith(('•', '-', '*')):
                    if current_project:
                        projects.append(current_project)
                    
                    current_project = {
                        "name": line,
                        "description": [],
                        "technologies": [],
                    }
                
                elif current_project and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    current_project["description"].append(line.lstrip('•-* '))
            
            if current_project:
                projects.append(current_project)
        
        return projects
    
    def _extract_certifications(self) -> List[Dict[str, str]]:
        """Extract certifications."""
        certifications = []
        
        # Look for certifications section
        cert_pattern = r'(?:CERTIFICATIONS|Certifications|Certificates)(.*?)(?:PROJECTS|Projects|EXPERIENCE|Experience|SKILLS|$)'
        matches = re.search(cert_pattern, self.raw_text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            cert_section = matches.group(1)
            
            # Common certification providers
            providers = ["Oracle", "AWS", "Azure", "Google", "IBM", "Microsoft", "Coursera", "Udacity"]
            
            lines = cert_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:
                    certifications.append({
                        "name": line.lstrip('•-* '),
                        "issuer": next((p for p in providers if p.lower() in line.lower()), "Unknown"),
                    })
        
        return certifications
    
    def _extract_achievements(self) -> List[str]:
        """Extract key achievements and metrics."""
        achievements = []
        
        # Look for quantifiable achievements
        metric_patterns = [
            r'(\d+%\s+(?:improvement|reduction|increase|accuracy|faster))',
            r'(<\d+ms\s+latency)',
            r'(\d+x\s+(?:faster|improvement))',
            r'(deployed|production|live)',
        ]
        
        for pattern in metric_patterns:
            matches = re.findall(pattern, self.raw_text, re.IGNORECASE)
            achievements.extend(matches)
        
        return list(set(achievements))
    
    def get_summary(self) -> str:
        """
        Get a text summary of the resume.
        
        Returns:
            Resume summary
        """
        if not self.parsed_data:
            self.parse()
        
        summary_parts = []
        
        # Skills summary
        all_skills = []
        for category, skills in self.parsed_data["skills"].items():
            all_skills.extend(skills)
        summary_parts.append(f"Skills: {', '.join(all_skills[:15])}")
        
        # Experience summary
        if self.parsed_data["experience"]:
            summary_parts.append(f"Experience: {len(self.parsed_data['experience'])} positions")
        
        # Projects summary
        if self.parsed_data["projects"]:
            summary_parts.append(f"Projects: {len(self.parsed_data['projects'])} key projects")
        
        return " | ".join(summary_parts)


def parse_resume(resume_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to parse resume.
    
    Args:
        resume_path: Path to resume PDF
        
    Returns:
        Parsed resume data
    """
    parser = ResumeParser(resume_path)
    return parser.parse()
