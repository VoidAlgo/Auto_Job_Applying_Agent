"""
Knowledge base for storing and retrieving project information using RAG.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from loguru import logger

from candidate.embedding_generator import EmbeddingGenerator
from config.config_manager import get_config


class ProjectKnowledgeBase:
    """
    RAG-based knowledge base for candidate projects.
    Stores project descriptions with embeddings for semantic retrieval.
    """
    
    def __init__(self, projects_folder: Optional[Path] = None):
        """
        Initialize project knowledge base.
        
        Args:
            projects_folder: Path to folder containing project markdown files
        """
        config = get_config()
        self.projects_folder = projects_folder or config.get_projects_folder()
        
        if not self.projects_folder.exists():
            raise FileNotFoundError(f"Projects folder not found: {self.projects_folder}")
        
        self.embedding_generator = EmbeddingGenerator()
        self.projects: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.index: Optional[faiss.IndexFlatIP] = None  # Inner product for cosine similarity
    
    def load_projects(self) -> List[Dict[str, Any]]:
        """
        Load all project markdown files.
        
        Returns:
            List of project data dictionaries
        """
        logger.info(f"Loading projects from {self.projects_folder}")
        
        markdown_files = list(self.projects_folder.glob("*.md"))
        
        if not markdown_files:
            logger.warning(f"No markdown files found in {self.projects_folder}")
            return []
        
        for md_file in markdown_files:
            try:
                project_data = self._parse_project_markdown(md_file)
                self.projects.append(project_data)
                logger.debug(f"Loaded project: {project_data['name']}")
            
            except Exception as e:
                logger.error(f"Failed to parse {md_file}: {e}")
                continue
        
        logger.info(f"Loaded {len(self.projects)} projects")
        return self.projects
    
    def _parse_project_markdown(self, filepath: Path) -> Dict[str, Any]:
        """
        Parse project markdown file.
        
        Args:
            filepath: Path to markdown file
            
        Returns:
            Project data dictionary
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract sections
        project = {
            "name": filepath.stem.replace('_', ' ').title(),
            "filepath": str(filepath),
            "full_content": content,
        }
        
        # Parse specific sections
        sections = {
            "overview": self._extract_section(content, "overview"),
            "key_achievements": self._extract_section(content, "key achievements"),
            "technical_implementation": self._extract_section(content, "technical implementation"),
            "challenges": self._extract_section(content, "challenges"),
            "impact": self._extract_section(content, "impact"),
            "technologies": self._extract_technologies(content),
        }
        
        project.update(sections)
        
        # Create searchable text
        project["searchable_text"] = self._create_searchable_text(project)
        
        return project
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract specific section from markdown."""
        import re
        
        # Look for section heading (case-insensitive)
        pattern = rf'##\s*{section_name}(.*?)(?=##|\Z)'
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _extract_technologies(self, content: str) -> List[str]:
        """Extract technologies mentioned in the project."""
        technologies = set()
        
        # Common tech keywords
        tech_keywords = [
            'Python', 'PyTorch', 'TensorFlow', 'LLM', 'GPT', 'Claude', 'Llama',
            'LangChain', 'FastAPI', 'Docker', 'Kubernetes', 'AWS', 'Azure',
            'PostgreSQL', 'MongoDB', 'Redis', 'Pinecone', 'FAISS',
            'React', 'Node.js', 'TypeScript', 'JavaScript',
            'Transformers', 'Hugging Face', 'OpenAI', 'Anthropic',
        ]
        
        content_lower = content.lower()
        for tech in tech_keywords:
            if tech.lower() in content_lower:
                technologies.add(tech)
        
        return list(technologies)
    
    def _create_searchable_text(self, project: Dict[str, Any]) -> str:
        """Create comprehensive searchable text for project."""
        parts = [
            f"Project: {project['name']}",
            project.get('overview', ''),
            project.get('key_achievements', ''),
            project.get('technical_implementation', ''),
            f"Technologies: {' '.join(project.get('technologies', []))}",
        ]
        
        return "\n".join(part for part in parts if part)
    
    def build_index(self) -> None:
        """Build FAISS index for semantic search."""
        logger.info("Building FAISS index for projects...")
        
        if not self.projects:
            self.load_projects()
        
        if not self.projects:
            logger.warning("No projects to index")
            return
        
        # Generate embeddings for all projects
        searchable_texts = [proj["searchable_text"] for proj in self.projects]
        embeddings_list = self.embedding_generator.generate(searchable_texts)
        
        # Convert to numpy array and normalize for cosine similarity
        self.embeddings = np.array(embeddings_list).astype('float32')
        faiss.normalize_L2(self.embeddings)
        
        # Create FAISS index (Inner Product for normalized vectors = Cosine Similarity)
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)
        
        logger.info(f"Built FAISS index with {len(self.projects)} projects")
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for relevant projects using semantic similarity.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of (project, score) tuples
        """
        if self.index is None:
            self.build_index()
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate(query)
        query_embedding = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, min(top_k, len(self.projects)))
        
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(self.projects):
                results.append((self.projects[idx], float(score)))
        
        logger.debug(f"Found {len(results)} relevant projects for query: {query[:50]}...")
        return results
    
    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get project by name.
        
        Args:
            name: Project name
            
        Returns:
            Project data or None
        """
        name_lower = name.lower()
        for project in self.projects:
            if name_lower in project["name"].lower():
                return project
        
        return None
    
    def get_projects_by_technology(self, technology: str) -> List[Dict[str, Any]]:
        """
        Get projects that use specific technology.
        
        Args:
            technology: Technology name
            
        Returns:
            List of matching projects
        """
        matching = []
        tech_lower = technology.lower()
        
        for project in self.projects:
            project_techs = [t.lower() for t in project.get("technologies", [])]
            if tech_lower in project_techs or tech_lower in project["searchable_text"].lower():
                matching.append(project)
        
        return matching
    
    def get_relevant_projects_for_job(self, job_description: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Get most relevant projects for a job description.
        
        Args:
            job_description: Job description text
            top_k: Number of projects to return
            
        Returns:
            List of relevant projects
        """
        results = self.search(job_description, top_k=top_k)
        return [proj for proj, score in results if score > 0.6]  # Filter by threshold
    
    def save_index(self, filepath: str) -> None:
        """
        Save FAISS index and project data to file.
        
        Args:
            filepath: Path to save index
        """
        if self.index is None:
            logger.warning("No index to save")
            return
        
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.index")
        
        # Save projects data and embeddings
        data = {
            "projects": self.projects,
            "embeddings": self.embeddings.tolist() if self.embeddings is not None else None,
        }
        
        with open(f"{filepath}.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved knowledge base to {filepath}")
    
    def load_index(self, filepath: str) -> None:
        """
        Load FAISS index and project data from file.
        
        Args:
            filepath: Path to load index from
        """
        # Load FAISS index
        self.index = faiss.read_index(f"{filepath}.index")
        
        # Load projects data
        with open(f"{filepath}.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.projects = data["projects"]
        if data["embeddings"]:
            self.embeddings = np.array(data["embeddings"]).astype('float32')
        
        logger.info(f"Loaded knowledge base from {filepath}")


def create_knowledge_base(projects_folder: Optional[Path] = None) -> ProjectKnowledgeBase:
    """
    Convenience function to create and build knowledge base.
    
    Args:
        projects_folder: Path to projects folder
        
    Returns:
        ProjectKnowledgeBase instance
    """
    kb = ProjectKnowledgeBase(projects_folder)
    kb.load_projects()
    kb.build_index()
    return kb
