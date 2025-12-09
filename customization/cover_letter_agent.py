"""
Cover Letter Agent - AI-Powered Cover Letter Generation

This module generates personalized, professional cover letters for each job
application using Claude Sonnet 4.5 with careful prompting for freshers.

Author: Auto Job Applier System
Date: December 2025
"""

import anthropic
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import os

from candidate.profile_builder import CandidateProfile
from candidate.knowledge_base import KnowledgeBase
from matching.job_matcher import MatchScore
from config.config_manager import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CoverLetter:
    """Generated cover letter with metadata."""
    
    content: str
    word_count: int
    job_title: str
    company: str
    
    # Highlighted elements
    key_projects: List[str]
    key_skills: List[str]
    achievements: List[str]
    
    # Generation metadata
    model: str
    temperature: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'content': self.content,
            'word_count': self.word_count,
            'job_title': self.job_title,
            'company': self.company,
            'key_projects': self.key_projects,
            'key_skills': self.key_skills,
            'achievements': self.achievements,
            'metadata': {
                'model': self.model,
                'temperature': self.temperature,
                'prompt_tokens': self.prompt_tokens,
                'completion_tokens': self.completion_tokens,
            }
        }
    
    def save(self, output_path: Path) -> None:
        """Save cover letter to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.content)
        logger.info(f"Saved cover letter to {output_path}")


class CoverLetterAgent:
    """
    Generate personalized cover letters using Claude Sonnet 4.5.
    
    Specializes in fresh graduate positioning:
    - Emphasizes learning ability and growth mindset
    - Highlights relevant projects with quantifiable impact
    - Professional yet enthusiastic tone
    - Connects internship experience to full-time readiness
    - Length: 250-350 words (one page)
    """
    
    # Claude models
    CLAUDE_SONNET_4_5 = "claude-sonnet-4-20250514"
    CLAUDE_SONNET_3_5 = "claude-3-5-sonnet-20241022"
    
    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        model: str = CLAUDE_SONNET_4_5,
        temperature: float = 0.7
    ):
        """
        Initialize the cover letter agent.
        
        Args:
            knowledge_base: KnowledgeBase for retrieving relevant projects
            model: Claude model to use
            temperature: Generation temperature (0-1)
        """
        self.logger = logger
        self.config = get_config()
        
        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        
        # Knowledge base for RAG
        self.knowledge_base = knowledge_base
        
        self.logger.info(f"CoverLetterAgent initialized with model: {model}")
    
    def generate(
        self,
        job: Dict[str, Any],
        profile: CandidateProfile,
        match_score: Optional[MatchScore] = None
    ) -> CoverLetter:
        """
        Generate a personalized cover letter.
        
        Args:
            job: Job dictionary
            profile: Candidate profile
            match_score: Match score (optional, for better customization)
            
        Returns:
            CoverLetter object
        """
        self.logger.info(
            f"Generating cover letter for {job.get('title')} at {job.get('company')}"
        )
        
        # Retrieve relevant projects
        relevant_projects = self._get_relevant_projects(job, profile)
        
        # Build prompt
        prompt = self._build_prompt(job, profile, match_score, relevant_projects)
        
        # Generate with Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract content
        content = response.content[0].text
        
        # Parse and structure
        cover_letter = self._parse_response(
            content,
            job,
            response.usage.input_tokens,
            response.usage.output_tokens
        )
        
        self.logger.info(
            f"Generated cover letter: {cover_letter.word_count} words, "
            f"{len(cover_letter.key_projects)} projects highlighted"
        )
        
        return cover_letter
    
    def _get_relevant_projects(
        self,
        job: Dict[str, Any],
        profile: CandidateProfile
    ) -> List[Dict[str, Any]]:
        """Retrieve most relevant projects for the job."""
        if not self.knowledge_base:
            # Return all projects if no knowledge base
            return profile.projects[:2]  # Top 2 projects
        
        # Use RAG to find relevant projects
        job_description = job.get('description', '')
        relevant_projects = self.knowledge_base.get_relevant_projects_for_job(
            job_description,
            top_k=2
        )
        
        return relevant_projects
    
    def _build_prompt(
        self,
        job: Dict[str, Any],
        profile: CandidateProfile,
        match_score: Optional[MatchScore],
        relevant_projects: List[Dict[str, Any]]
    ) -> str:
        """Build the prompt for Claude."""
        
        # Extract job details
        job_title = job.get('title', '')
        company = job.get('company', '')
        job_desc = job.get('description', '')
        
        # Extract candidate details
        name = profile.personal_info.get('name', 'Candidate')
        email = profile.personal_info.get('email', '')
        
        # Build projects context
        projects_text = "\n\n".join([
            f"Project: {p.get('name', 'Unnamed')}\n"
            f"Description: {p.get('description', '')}\n"
            f"Technologies: {', '.join(p.get('technologies', []))}\n"
            f"Achievements: {', '.join(p.get('achievements', []))}"
            for p in relevant_projects
        ])
        
        # Build experience context
        experience_text = "\n".join([
            f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')}): "
            f"{exp.get('description', '')}"
            for exp in profile.experience[:2]  # Top 2 experiences
        ])
        
        # Build skills context
        skills_text = ", ".join(profile.skills[:15])  # Top 15 skills
        
        # Match score insights
        match_insights = ""
        if match_score:
            matched_skills = list(match_score.matched_skills)[:5]
            match_insights = f"\n\nKey matching skills: {', '.join(matched_skills)}"
        
        # Construct prompt
        prompt = f"""You are an expert career advisor helping a fresh graduate AI/ML engineer write a compelling cover letter.

**Job Details:**
- Position: {job_title}
- Company: {company}
- Job Description: {job_desc[:1000]}  

**Candidate Profile:**
- Name: {name}
- Email: {email}
- Education: {profile.education[0].get('degree', '') if profile.education else 'BTech CSE'}
- Key Skills: {skills_text}
{match_insights}

**Relevant Experience:**
{experience_text}

**Key Projects to Highlight:**
{projects_text}

**Instructions:**
Generate a professional, personalized cover letter with these requirements:

1. **Length**: 250-350 words (one page)
2. **Tone**: Professional yet enthusiastic - show genuine interest without being overeager
3. **Structure**:
   - Opening: Express interest and briefly state why you're excited about this role
   - Body (2-3 paragraphs):
     * Connect your most relevant project(s) to the job requirements with QUANTIFIABLE achievements
     * Highlight transferable skills from internships/projects
     * Show understanding of the company's mission/tech stack
   - Closing: Express enthusiasm for contributing and request an interview

4. **Fresh Graduate Positioning**:
   - Emphasize learning ability and growth mindset
   - Frame internships as production experience (if applicable)
   - Use confident language: "developed", "implemented", "optimized" (not "helped with" or "assisted")
   - Include specific metrics and impact from projects
   - Show you understand the role's requirements and have relevant experience

5. **Avoid**:
   - Generic phrases ("I am a hard worker", "fast learner" without evidence)
   - Overusing "I" - vary sentence structure
   - Apologizing for lack of experience
   - Listing skills without context
   - Exceeding 350 words

6. **Include**:
   - Specific project names and their impact
   - Technologies/frameworks mentioned in the job description
   - One sentence about why THIS company/role specifically

Generate the cover letter now. Format it professionally with:
- Date: [Current Date]
- Recipient: Hiring Manager
- Company address placeholder
- Proper business letter format

Do NOT include explanations or meta-commentary - just the cover letter content."""
        
        return prompt
    
    def _parse_response(
        self,
        content: str,
        job: Dict[str, Any],
        prompt_tokens: int,
        completion_tokens: int
    ) -> CoverLetter:
        """Parse Claude's response into CoverLetter object."""
        
        # Calculate word count
        word_count = len(content.split())
        
        # Extract highlighted elements (simple heuristics)
        key_projects = []
        key_skills = []
        achievements = []
        
        # Find project mentions (look for quoted text or capitalized project names)
        import re
        
        # Look for project patterns
        project_patterns = re.findall(r'"([^"]+)"', content)
        key_projects = [p for p in project_patterns if len(p) > 5][:3]
        
        # Look for skills mentioned in content (match against common skills)
        common_skills = ['python', 'pytorch', 'tensorflow', 'langchain', 'rag', 
                        'llm', 'machine learning', 'deep learning', 'nlp']
        content_lower = content.lower()
        key_skills = [skill for skill in common_skills if skill in content_lower][:5]
        
        # Look for achievement indicators (numbers, percentages, improvements)
        achievement_patterns = re.findall(
            r'(\d+%|\d+x|\$\d+k?|\d+ users|\d+ ms|improved by \d+)',
            content,
            re.IGNORECASE
        )
        achievements = achievement_patterns[:3]
        
        return CoverLetter(
            content=content,
            word_count=word_count,
            job_title=job.get('title', ''),
            company=job.get('company', ''),
            key_projects=key_projects,
            key_skills=key_skills,
            achievements=achievements,
            model=self.model,
            temperature=self.temperature,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    
    def generate_batch(
        self,
        jobs: List[Dict[str, Any]],
        profile: CandidateProfile,
        match_scores: Optional[List[MatchScore]] = None
    ) -> List[CoverLetter]:
        """
        Generate cover letters for multiple jobs.
        
        Args:
            jobs: List of job dictionaries
            profile: Candidate profile
            match_scores: Optional list of match scores
            
        Returns:
            List of CoverLetter objects
        """
        self.logger.info(f"Generating {len(jobs)} cover letters in batch")
        
        cover_letters = []
        
        for i, job in enumerate(jobs):
            try:
                match_score = match_scores[i] if match_scores else None
                cover_letter = self.generate(job, profile, match_score)
                cover_letters.append(cover_letter)
            except Exception as e:
                self.logger.error(
                    f"Error generating cover letter for {job.get('title')}: {e}"
                )
                continue
        
        self.logger.info(f"Successfully generated {len(cover_letters)} cover letters")
        return cover_letters


def main():
    """Example usage of CoverLetterAgent."""
    from candidate.profile_builder import CandidateProfile
    
    # Sample job
    job = {
        'title': 'Junior ML Engineer',
        'company': 'AI Innovations Inc',
        'description': '''
        We're seeking a Junior ML Engineer to join our LLM applications team.
        
        You'll work on:
        - Building RAG systems with LangChain
        - Fine-tuning LLMs for specific use cases
        - Optimizing inference performance
        
        Requirements:
        - Python and PyTorch experience
        - Understanding of LLMs and prompt engineering
        - 0-2 years of experience
        - Bachelor's in CS or related field
        ''',
    }
    
    # Sample profile
    profile = CandidateProfile(
        personal_info={
            'name': 'John Doe',
            'email': 'john.doe@email.com',
        },
        skills=['python', 'pytorch', 'langchain', 'rag', 'llm'],
        experience=[
            {
                'title': 'ML Engineering Intern',
                'company': 'TechCorp',
                'duration': '6 months',
                'description': 'Built RAG systems reducing query latency by 40%',
            }
        ],
        education=[{'degree': 'BTech Computer Science'}],
        projects=[
            {
                'name': 'AI Voice Agent',
                'description': 'LLM-powered voice assistant with RAG',
                'technologies': ['python', 'openai', 'langchain', 'faiss'],
                'achievements': ['Processed 1000+ queries', '200ms latency'],
            }
        ],
        summary='ML engineer passionate about LLMs',
    )
    
    # Generate cover letter
    try:
        agent = CoverLetterAgent()
        cover_letter = agent.generate(job, profile)
        
        print("\n=== Generated Cover Letter ===\n")
        print(cover_letter.content)
        print(f"\n\nWord Count: {cover_letter.word_count}")
        print(f"Key Projects: {cover_letter.key_projects}")
        print(f"Key Skills: {cover_letter.key_skills}")
        print(f"Achievements: {cover_letter.achievements}")
        
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set ANTHROPIC_API_KEY in your .env file")


if __name__ == "__main__":
    main()
