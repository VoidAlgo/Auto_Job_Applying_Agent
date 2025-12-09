"""
Generate embeddings for candidate profile for semantic matching.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from config.config_manager import get_config


class EmbeddingGenerator:
    """Generate embeddings for text using various providers."""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize embedding generator.
        
        Args:
            provider: Embedding provider ('openai' or 'sentence-transformers')
            model: Model name
        """
        config = get_config()
        embeddings_config = config.get_embeddings_config()
        
        self.provider = provider or embeddings_config["provider"]
        self.model = model or embeddings_config["model"]
        self.dimension = embeddings_config["dimension"]
        
        logger.info(f"Initializing embedding generator: {self.provider} - {self.model}")
        
        if self.provider == "openai":
            api_key = embeddings_config["api_key"]
            if not api_key:
                raise ValueError("OpenAI API key not found")
            self.client = OpenAI(api_key=api_key)
        
        elif self.provider == "sentence-transformers":
            self.client = SentenceTransformer(self.model)
            self.dimension = self.client.get_sentence_embedding_dimension()
        
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
    
    def generate(self, text: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text or list of texts to embed
            
        Returns:
            Embedding(s) as numpy array(s)
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        if self.provider == "openai":
            embeddings = self._generate_openai(texts)
        elif self.provider == "sentence-transformers":
            embeddings = self._generate_sentence_transformers(texts)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        return embeddings[0] if is_single else embeddings
    
    def _generate_openai(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = [np.array(item.embedding) for item in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings using OpenAI")
            return embeddings
        
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise
    
    def _generate_sentence_transformers(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using Sentence Transformers."""
        try:
            embeddings = self.client.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            logger.debug(f"Generated {len(embeddings)} embeddings using Sentence Transformers")
            return [np.array(emb) for emb in embeddings]
        
        except Exception as e:
            logger.error(f"Sentence Transformers embedding generation failed: {e}")
            raise
    
    def generate_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.generate(batch)
            all_embeddings.extend(embeddings)
            
            logger.debug(f"Processed batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")
        
        return all_embeddings
    
    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)


class CandidateEmbeddings:
    """Generate and manage embeddings for candidate profile."""
    
    def __init__(self, generator: Optional[EmbeddingGenerator] = None):
        """
        Initialize candidate embeddings manager.
        
        Args:
            generator: EmbeddingGenerator instance
        """
        self.generator = generator or EmbeddingGenerator()
        self.embeddings: Dict[str, np.ndarray] = {}
    
    def generate_profile_embeddings(self, profile_data: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for different aspects of candidate profile.
        
        Args:
            profile_data: Complete candidate profile data
            
        Returns:
            Dictionary of embeddings
        """
        logger.info("Generating candidate profile embeddings...")
        
        # 1. Skills embedding
        skills_text = self._format_skills(profile_data.get("skills", {}))
        if skills_text:
            self.embeddings["skills"] = self.generator.generate(skills_text)
        
        # 2. Experience embedding
        experience_text = self._format_experience(profile_data.get("experience", []))
        if experience_text:
            self.embeddings["experience"] = self.generator.generate(experience_text)
        
        # 3. Projects embedding
        projects_text = self._format_projects(profile_data.get("projects", []))
        if projects_text:
            self.embeddings["projects"] = self.generator.generate(projects_text)
        
        # 4. Education embedding
        education_text = self._format_education(profile_data.get("education", []))
        if education_text:
            self.embeddings["education"] = self.generator.generate(education_text)
        
        # 5. Overall profile embedding (weighted combination)
        overall_text = f"{skills_text}\n{experience_text}\n{projects_text}"
        self.embeddings["overall"] = self.generator.generate(overall_text)
        
        logger.info(f"Generated {len(self.embeddings)} profile embeddings")
        return self.embeddings
    
    def _format_skills(self, skills: Dict[str, List[str]]) -> str:
        """Format skills for embedding."""
        skill_list = []
        for category, items in skills.items():
            skill_list.extend(items)
        return " ".join(skill_list)
    
    def _format_experience(self, experience: List[Dict[str, Any]]) -> str:
        """Format experience for embedding."""
        exp_texts = []
        for exp in experience:
            text = f"{exp.get('position', '')} at {exp.get('company', '')}"
            if exp.get('responsibilities'):
                text += " " + " ".join(exp['responsibilities'][:3])  # Top 3 responsibilities
            exp_texts.append(text)
        return " ".join(exp_texts)
    
    def _format_projects(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects for embedding."""
        proj_texts = []
        for proj in projects:
            text = f"{proj.get('name', '')} {proj.get('summary', '')}"
            if proj.get('technologies'):
                text += " " + " ".join(proj['technologies'])
            proj_texts.append(text)
        return " ".join(proj_texts)
    
    def _format_education(self, education: List[Dict[str, str]]) -> str:
        """Format education for embedding."""
        edu_texts = []
        for edu in education:
            text = f"{edu.get('degree', '')} {edu.get('major', '')} {edu.get('institution', '')}"
            edu_texts.append(text)
        return " ".join(edu_texts)
    
    def get_embedding(self, key: str) -> Optional[np.ndarray]:
        """
        Get specific embedding.
        
        Args:
            key: Embedding key (skills, experience, projects, education, overall)
            
        Returns:
            Embedding array or None
        """
        return self.embeddings.get(key)
    
    def save_embeddings(self, filepath: str) -> None:
        """
        Save embeddings to file.
        
        Args:
            filepath: Path to save embeddings
        """
        np.savez(filepath, **self.embeddings)
        logger.info(f"Saved embeddings to {filepath}")
    
    def load_embeddings(self, filepath: str) -> None:
        """
        Load embeddings from file.
        
        Args:
            filepath: Path to load embeddings from
        """
        data = np.load(filepath)
        self.embeddings = {key: data[key] for key in data.files}
        logger.info(f"Loaded {len(self.embeddings)} embeddings from {filepath}")


def generate_embeddings(text: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
    """
    Convenience function to generate embeddings.
    
    Args:
        text: Text or list of texts to embed
        
    Returns:
        Embedding(s)
    """
    generator = EmbeddingGenerator()
    return generator.generate(text)
