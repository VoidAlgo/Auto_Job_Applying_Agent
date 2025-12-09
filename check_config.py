"""
Configuration validation and health check script.
"""

import os
import sys
from pathlib import Path

from loguru import logger


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        logger.error(f"Python 3.10+ required, found {version.major}.{version.minor}")
        return False
    logger.info(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_environment_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if not env_path.exists():
        logger.error("✗ .env file not found. Copy from .env.example")
        return False
    logger.info("✓ .env file exists")
    return True


def check_api_keys():
    """Check if required API keys are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_keys = {
        "ANTHROPIC_API_KEY": "Anthropic (Claude)",
        "OPENAI_API_KEY": "OpenAI (Embeddings)",
    }
    
    optional_keys = {
        "GITHUB_TOKEN": "GitHub API",
        "LINKEDIN_EMAIL": "LinkedIn",
        "PINECONE_API_KEY": "Pinecone",
    }
    
    all_good = True
    
    logger.info("\nRequired API Keys:")
    for key, name in required_keys.items():
        value = os.getenv(key)
        if value and value != f"your_{key.lower()}_here":
            logger.info(f"✓ {name}: Set")
        else:
            logger.error(f"✗ {name}: Not set")
            all_good = False
    
    logger.info("\nOptional API Keys:")
    for key, name in optional_keys.items():
        value = os.getenv(key)
        if value and value != f"your_{key.lower()}_here":
            logger.info(f"✓ {name}: Set")
        else:
            logger.warning(f"○ {name}: Not set (optional)")
    
    return all_good


def check_config_files():
    """Check if configuration files exist."""
    config_files = [
        "config/settings.yaml",
        "config/candidate_profile.yaml",
    ]
    
    all_exist = True
    logger.info("\nConfiguration Files:")
    
    for file_path in config_files:
        path = Path(file_path)
        if path.exists():
            logger.info(f"✓ {file_path}")
        else:
            logger.error(f"✗ {file_path} not found")
            all_exist = False
    
    return all_exist


def check_documents():
    """Check if required documents exist."""
    logger.info("\nRequired Documents:")
    
    # Check resume
    resume_path = Path("docs/resume.pdf")
    if resume_path.exists():
        logger.info(f"✓ Resume: {resume_path}")
    else:
        logger.warning(f"○ Resume not found: {resume_path}")
        logger.warning("  Add your resume or update path in config/candidate_profile.yaml")
    
    # Check projects folder
    projects_path = Path("projects")
    if projects_path.exists():
        md_files = list(projects_path.glob("*.md"))
        if md_files:
            logger.info(f"✓ Projects folder: {len(md_files)} project(s) found")
            for md_file in md_files:
                logger.info(f"  - {md_file.name}")
        else:
            logger.warning(f"○ No project markdown files in {projects_path}")
    else:
        logger.error(f"✗ Projects folder not found: {projects_path}")
        return False
    
    return True


def check_directories():
    """Check if required directories exist."""
    directories = ["data", "logs", "docs", "projects"]
    
    logger.info("\nRequired Directories:")
    for dir_name in directories:
        path = Path(dir_name)
        if path.exists():
            logger.info(f"✓ {dir_name}/")
        else:
            logger.warning(f"○ Creating {dir_name}/")
            path.mkdir(parents=True, exist_ok=True)
    
    return True


def check_dependencies():
    """Check if key dependencies are installed."""
    required_packages = [
        "anthropic",
        "openai",
        "selenium",
        "PyPDF2",
        "pdfplumber",
        "faiss",
        "loguru",
        "pydantic",
    ]
    
    logger.info("\nKey Dependencies:")
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package}")
        except ImportError:
            logger.error(f"✗ {package} not installed")
            all_installed = False
    
    if not all_installed:
        logger.error("\nInstall missing dependencies: pip install -r requirements.txt")
    
    return all_installed


def check_candidate_profile_config():
    """Check if candidate profile is configured."""
    logger.info("\nCandidate Profile Configuration:")
    
    try:
        import yaml
        
        with open("config/candidate_profile.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        # Check personal info
        personal = config.get("personal", {})
        placeholders = ["Your Name", "your.email@example.com", "Makilesh M"]
        
        name = personal.get("name", "")
        email = personal.get("email", "")
        
        if name and name not in placeholders:
            logger.info(f"✓ Name: {name}")
        else:
            logger.warning(f"○ Name not configured: {name}")
        
        if email and email not in placeholders and "@" in email:
            logger.info(f"✓ Email: {email}")
        else:
            logger.warning(f"○ Email not configured: {email}")
        
        # Check links
        links = config.get("links", {})
        github = links.get("github", "")
        
        if github and "github.com" in github and "yourusername" not in github:
            logger.info(f"✓ GitHub: {github}")
        else:
            logger.warning(f"○ GitHub not configured: {github}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error reading candidate_profile.yaml: {e}")
        return False


def main():
    """Run all checks."""
    logger.remove()
    logger.add(sys.stdout, format="<level>{message}</level>", colorize=True, level="INFO")
    
    logger.info("=" * 60)
    logger.info("Automated Job Application Agent - Configuration Check")
    logger.info("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_environment_file),
        ("API Keys", check_api_keys),
        ("Config Files", check_config_files),
        ("Directories", check_directories),
        ("Dependencies", check_dependencies),
        ("Documents", check_documents),
        ("Profile Config", check_candidate_profile_config),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            logger.error(f"Check '{check_name}' failed: {e}")
            results[check_name] = False
    
    logger.info("\n" + "=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {check_name}")
    
    logger.info(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        logger.info("\n🎉 All checks passed! You're ready to run the agent.")
        logger.info("\nNext steps:")
        logger.info("1. Build profile: python main.py --profile-only")
        logger.info("2. Test scraping: python main.py --max-jobs 10")
        return 0
    else:
        logger.error("\n⚠️  Some checks failed. Please fix the issues above.")
        logger.error("\nCommon fixes:")
        logger.error("- Copy .env.example to .env and add API keys")
        logger.error("- Update config/candidate_profile.yaml with your info")
        logger.error("- Add your resume to docs/resume.pdf")
        logger.error("- Run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
