"""
GitHub profile analyzer to extract repositories, contributions, and code statistics.
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from github import Github, GithubException
from loguru import logger

from config.config_manager import get_config


class GitHubAnalyzer:
    """Analyze GitHub profile for technical assessment."""
    
    def __init__(self, username: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize GitHub analyzer.
        
        Args:
            username: GitHub username. If None, extracts from config.
            token: GitHub API token. If None, uses environment variable.
        """
        config = get_config()
        
        # Extract username from GitHub URL in config
        if username is None:
            github_url = config.candidate_profile.links.github
            username = github_url.rstrip('/').split('/')[-1]
        
        self.username = username
        self.token = token or os.getenv("GITHUB_TOKEN")
        
        if not self.token:
            logger.warning("GitHub token not found, API rate limits will be restrictive")
            self.client = Github()
        else:
            self.client = Github(self.token)
        
        self.user = None
        self.profile_data: Optional[Dict[str, Any]] = None
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze GitHub profile comprehensively.
        
        Returns:
            Complete GitHub profile analysis
        """
        logger.info(f"Analyzing GitHub profile: {self.username}")
        
        try:
            self.user = self.client.get_user(self.username)
        except GithubException as e:
            logger.error(f"Failed to fetch GitHub user: {e}")
            raise
        
        self.profile_data = {
            "basic_info": self._get_basic_info(),
            "repositories": self._analyze_repositories(),
            "languages": self._get_language_stats(),
            "contributions": self._get_contribution_stats(),
            "top_repos": self._get_top_repositories(limit=5),
            "activity_summary": self._get_activity_summary(),
        }
        
        logger.info("GitHub profile analysis completed")
        return self.profile_data
    
    def _get_basic_info(self) -> Dict[str, Any]:
        """Extract basic profile information."""
        return {
            "username": self.user.login,
            "name": self.user.name,
            "bio": self.user.bio,
            "location": self.user.location,
            "company": self.user.company,
            "blog": self.user.blog,
            "email": self.user.email,
            "public_repos": self.user.public_repos,
            "followers": self.user.followers,
            "following": self.user.following,
            "created_at": self.user.created_at.isoformat() if self.user.created_at else None,
            "updated_at": self.user.updated_at.isoformat() if self.user.updated_at else None,
        }
    
    def _analyze_repositories(self) -> List[Dict[str, Any]]:
        """Analyze all public repositories."""
        repos_data = []
        
        try:
            repos = self.user.get_repos(type='owner', sort='updated')
            
            for repo in repos:
                if repo.fork:
                    continue  # Skip forked repositories
                
                repo_info = {
                    "name": repo.name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "watchers": repo.watchers_count,
                    "open_issues": repo.open_issues_count,
                    "size": repo.size,  # KB
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "url": repo.html_url,
                    "topics": repo.get_topics(),
                    "has_readme": self._check_readme(repo),
                    "license": repo.license.name if repo.license else None,
                }
                
                repos_data.append(repo_info)
        
        except GithubException as e:
            logger.error(f"Failed to fetch repositories: {e}")
        
        return repos_data
    
    def _check_readme(self, repo) -> bool:
        """Check if repository has a README."""
        try:
            repo.get_readme()
            return True
        except:
            return False
    
    def _get_language_stats(self) -> Dict[str, int]:
        """Get language statistics across all repositories."""
        language_stats = {}
        
        try:
            repos = self.user.get_repos(type='owner')
            
            for repo in repos:
                if repo.fork:
                    continue
                
                try:
                    languages = repo.get_languages()
                    for lang, bytes_count in languages.items():
                        language_stats[lang] = language_stats.get(lang, 0) + bytes_count
                except:
                    continue
        
        except GithubException as e:
            logger.error(f"Failed to fetch language stats: {e}")
        
        # Sort by bytes count
        language_stats = dict(sorted(language_stats.items(), key=lambda x: x[1], reverse=True))
        
        return language_stats
    
    def _get_contribution_stats(self) -> Dict[str, Any]:
        """Get contribution statistics."""
        # Note: GitHub API doesn't provide detailed contribution graph data
        # This would require scraping or using GraphQL API
        
        stats = {
            "total_commits": 0,
            "total_prs": 0,
            "total_issues": 0,
            "total_reviews": 0,
        }
        
        try:
            # Get commits from all repos (last year)
            one_year_ago = datetime.now() - timedelta(days=365)
            
            repos = self.user.get_repos(type='owner')
            
            for repo in repos:
                if repo.fork:
                    continue
                
                try:
                    # Count commits
                    commits = repo.get_commits(author=self.user, since=one_year_ago)
                    stats["total_commits"] += commits.totalCount
                except:
                    pass
        
        except GithubException as e:
            logger.error(f"Failed to fetch contribution stats: {e}")
        
        return stats
    
    def _get_top_repositories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top repositories by stars and activity.
        
        Args:
            limit: Number of top repos to return
            
        Returns:
            List of top repositories
        """
        try:
            repos = self.user.get_repos(type='owner', sort='updated')
            
            # Filter out forks and sort by stars
            non_fork_repos = [repo for repo in repos if not repo.fork]
            sorted_repos = sorted(non_fork_repos, key=lambda x: x.stargazers_count, reverse=True)
            
            top_repos = []
            for repo in sorted_repos[:limit]:
                top_repos.append({
                    "name": repo.name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "url": repo.html_url,
                    "topics": repo.get_topics(),
                })
            
            return top_repos
        
        except GithubException as e:
            logger.error(f"Failed to fetch top repositories: {e}")
            return []
    
    def _get_activity_summary(self) -> Dict[str, Any]:
        """Get activity summary (last 90 days)."""
        summary = {
            "active_repos": 0,
            "recent_commits": 0,
            "recent_prs": 0,
            "languages_used": set(),
        }
        
        try:
            ninety_days_ago = datetime.now() - timedelta(days=90)
            repos = self.user.get_repos(type='owner', sort='updated')
            
            for repo in repos:
                if repo.fork:
                    continue
                
                # Check if updated in last 90 days
                if repo.updated_at and repo.updated_at > ninety_days_ago:
                    summary["active_repos"] += 1
                    
                    if repo.language:
                        summary["languages_used"].add(repo.language)
                    
                    # Count recent commits
                    try:
                        commits = repo.get_commits(author=self.user, since=ninety_days_ago)
                        summary["recent_commits"] += commits.totalCount
                    except:
                        pass
        
        except GithubException as e:
            logger.error(f"Failed to fetch activity summary: {e}")
        
        summary["languages_used"] = list(summary["languages_used"])
        
        return summary
    
    def get_ai_ml_projects(self) -> List[Dict[str, Any]]:
        """
        Identify AI/ML related projects.
        
        Returns:
            List of AI/ML projects
        """
        ai_ml_keywords = [
            'ai', 'ml', 'machine-learning', 'deep-learning', 'neural-network',
            'llm', 'nlp', 'computer-vision', 'pytorch', 'tensorflow',
            'transformers', 'gpt', 'rag', 'langchain', 'embeddings',
        ]
        
        ai_ml_projects = []
        
        if not self.profile_data:
            self.analyze()
        
        for repo in self.profile_data["repositories"]:
            # Check topics and description
            topics_lower = [t.lower() for t in repo.get("topics", [])]
            desc_lower = (repo.get("description") or "").lower()
            
            is_ai_ml = any(
                keyword in topics_lower or keyword in desc_lower 
                for keyword in ai_ml_keywords
            )
            
            # Check primary language
            if repo.get("language") in ["Python", "Jupyter Notebook"]:
                is_ai_ml = True
            
            if is_ai_ml:
                ai_ml_projects.append(repo)
        
        return ai_ml_projects
    
    def get_summary(self) -> str:
        """
        Get text summary of GitHub profile.
        
        Returns:
            Summary string
        """
        if not self.profile_data:
            self.analyze()
        
        basic = self.profile_data["basic_info"]
        languages = list(self.profile_data["languages"].keys())[:5]
        activity = self.profile_data["activity_summary"]
        
        summary = (
            f"GitHub: {basic['public_repos']} repos, {basic['followers']} followers | "
            f"Languages: {', '.join(languages)} | "
            f"Recent activity: {activity['active_repos']} active repos, "
            f"{activity['recent_commits']} commits (90 days)"
        )
        
        return summary


def analyze_github_profile(username: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze GitHub profile.
    
    Args:
        username: GitHub username
        
    Returns:
        GitHub profile analysis
    """
    analyzer = GitHubAnalyzer(username)
    return analyzer.analyze()
