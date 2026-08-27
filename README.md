# Automated Job Application Agent

An intelligent, automated system for discovering and applying to AI/ML Engineer positions tailored for fresh graduates with strong internship experience



## 🎯 Overview

This system automates the entire job application process:
- **Profile Analysis**: Parses your resume, analyzes GitHub activity, and builds a comprehensive candidate profile
- **Job Discovery**: Scrapes LinkedIn, Indeed, Glassdoor, and other platforms for entry-level AI/ML roles
- **Intelligent Matching**: Uses semantic embeddings to match your skills with job requirements
- **Smart Customization**: Generates tailored cover letters and customizes resumes for each application
- **Automated Submission**: Fills out applications automatically with human-in-the-loop review
- **Tracking & Follow-up**: Manages applications and sends automated follow-upsa
aaaaaa
## ✨ Key Features

### Candidate Profile Analyzer ✅ COMPLETE
- ✅ PDF resume parsing with structured data extraction
- ✅ GitHub API integration (repos, languages, contributions)
- ✅ LinkedIn profile scraping (optional)
- ✅ Project knowledge base with RAG for contextual retrieval
- ✅ Semantic embeddings for skill matching

### Job Discovery & Scraping ✅ COMPLETE
- ✅ LinkedIn job scraper with anti-detection
- ✅ Entry-level AI/ML role filtering (0-2 years experience)
- ✅ Remote/Hybrid job support
- ✅ Anti-bot measures (rotating proxies, rate limiting, stealth mode)
- 🚧 Indeed, Glassdoor, AngelList scrapers (Phase 3)

### Intelligent Matching ✅ COMPLETE (Phase 2)
- ✅ NLP-based skill extraction (90+ skills tracked)
- ✅ Semantic similarity scoring with embeddings
- ✅ Multi-component matching (skills, experience, education, projects)
- ✅ Multi-criteria ranking (strategic fit, difficulty, timing, preferences)
- ✅ Priority assignment (High/Medium/Low)
- ✅ Match confidence and recommendations

### Application Customization ✅ PARTIAL (Phase 2)
- ✅ AI-powered cover letter generation with Claude Sonnet 4.5
- ✅ Fresh graduate positioning (professional yet enthusiastic)
- ✅ RAG-enhanced project highlighting
- ✅ Job-specific customization (250-350 words)
- 🚧 Resume customization (keyword optimization, project reordering)
- 🚧 Screening question answerer with authentic responses

### Automated Submission 🚧 Coming in Phase 3
- 🚧 Multi-platform support (Lever, Greenhouse, Workday, etc.)
- 🚧 Selenium/Playwright with stealth mode
- 🚧 Human-like form filling with random delays

### Tracking & Analytics 🚧 Coming in Phase 4
- 🚧 Application database (status, responses, interviews)
- 🚧 Automated follow-ups (Week 1: Thank you, Week 2: Status inquiry)
- 🚧 Success metrics and skills gap analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Chrome browser (for Selenium)
- Git

### Installation

```bash
# Clone the repository
cd auto_job_applier

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy model (for NLP)
python -m spacy download en_core_web_sm
```

### Configuration

1. **Copy environment variables:**
```bash
copy .env.example .env
```

2. **Edit `.env` and add your API keys:**
```env
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GITHUB_TOKEN=your_github_token_here
```

3. **Update `config/candidate_profile.yaml` with your information:**
```yaml
personal:
  name: "Your Name"
  email: "your.email@example.com"
  phone: "+91XXXXXXXXXX"
  location: "Your City, India"

links:
  github: "https://github.com/yourusername"
  linkedin: "https://linkedin.com/in/yourprofile"

documents:
  resume: "./docs/resume.pdf"
  projects_folder: "./projects/"
```

4. **Add your resume:**
   - Place your resume PDF in `docs/resume.pdf`

5. **Add project descriptions:**
   - Create markdown files in `projects/` folder
   - See `projects/voice_agent.md` for example format

### Usage

#### Build Candidate Profile
```bash
python main.py --profile-only
```

This will:
- Parse your resume
- Analyze your GitHub profile
- Load project descriptions
- Generate embeddings
- Save profile to `data/candidate_profile.json`

#### Discover Jobs (LinkedIn)
```bash
python main.py --max-jobs 50
```

This will:
1. Build/load your candidate profile
2. Scrape LinkedIn for entry-level AI/ML roles
3. Match jobs with your profile
4. Display matching jobs

#### Full Pipeline (Coming Soon)
```bash
python main.py --max-jobs 50 --auto-apply
```

**⚠️ Warning:** `--auto-apply` is not recommended until you've reviewed the first 20 applications manually.

## 📁 Project Structure

```
auto_job_applier/
├── candidate/                  # Candidate profile analysis
│   ├── profile_builder.py      # Main profile builder
│   ├── resume_parser.py        # PDF resume parsing
│   ├── github_analyzer.py      # GitHub API integration
│   ├── linkedin_analyzer.py    # LinkedIn scraping
│   ├── embedding_generator.py  # Semantic embeddings
│   └── knowledge_base.py       # RAG for projects
├── scrapers/                   # Job board scrapers
│   ├── base_scraper.py         # Base class with anti-detection
│   ├── linkedin_scraper.py     # LinkedIn jobs
│   ├── indeed_scraper.py       # Indeed jobs (TODO)
│   ├── glassdoor_scraper.py    # Glassdoor jobs (TODO)
│   └── angellist_scraper.py    # AngelList jobs (TODO)
├── matching/                   # Matching engine (TODO)
│   ├── job_matcher.py          # Semantic matching
│   ├── skill_extractor.py      # NLP skill extraction
│   └── ranker.py               # Multi-criteria ranking
├── customization/              # Application customization (TODO)
│   ├── cover_letter_agent.py   # LLM cover letter generation
│   ├── resume_customizer.py    # Smart resume adaptation
│   └── question_answerer.py    # Screening questions
├── application/                # Automated submission (TODO)
│   ├── form_filler.py          # Selenium automation
│   └── ats_handlers/           # ATS-specific handlers
├── tracking/                   # Tracking & analytics (TODO)
│   ├── database.py             # SQLite/PostgreSQL
│   ├── analytics.py            # Success metrics
│   └── follow_up_scheduler.py  # Automated follow-ups
├── review/                     # Human-in-the-loop (TODO)
│   └── approval_interface.py   # Streamlit dashboard
├── config/                     # Configuration
│   ├── settings.yaml           # App settings
│   ├── candidate_profile.yaml  # Your profile
│   └── config_manager.py       # Config loader
├── utils/                      # Utilities
│   └── logger.py               # Logging setup
├── projects/                   # Your project descriptions
│   └── voice_agent.md          # Example project
├── docs/                       # Documents
│   └── resume.pdf              # Your resume
├── data/                       # Generated data
│   └── candidate_profile.json  # Built profile
├── logs/                       # Application logs
├── main.py                     # Main orchestrator
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🎓 For Fresh Graduates

This system is specifically designed for fresh graduates with:
- Strong internship experience (1-2 internships)
- Personal projects with production deployments
- Modern AI/ML tech stack (LLMs, RAG, PyTorch, etc.)
- Quantifiable achievements (latency improvements, accuracy metrics, etc.)

### Positioning Strategy

**Cover Letter Tone:**
- Emphasize learning ability and growth mindset
- Show passion through projects and self-learning
- Highlight tangible impact from internships
- Express genuine enthusiasm for company's AI work
- Balance confidence (strong projects) with humility (eager to learn)

**Project Highlighting Priority:**
1. Production deployments (real users, real impact)
2. Measurable business value (80% reduction, 95% accuracy)
3. Complex technical challenges (sub-200ms latency, real-time systems)
4. Modern AI stack (LLMs, RAG, Multi-agent, Vector DBs)
5. End-to-end ownership (design, development, deployment)

**Red Flags to Avoid:**
- ❌ Don't claim senior-level expertise
- ❌ Don't apply to roles requiring 3+ years
- ❌ Don't overstate responsibilities
- ❌ Don't use generic templates
- ❌ Don't ignore company culture fit

**Green Flags to Emphasize:**
- ✅ Certifications (Oracle, AWS, etc.)
- ✅ GitHub activity (consistent commits, quality code)
- ✅ Internship impact (quantified with metrics)
- ✅ Modern tech stack (shows relevance)
- ✅ Production experience (shows maturity)

## 🔧 Configuration

### Target Roles
Edit `config/settings.yaml`:
```yaml
job_criteria:
  target_roles:
    - "AI Engineer"
    - "ML Engineer"
    - "LLM Engineer"
    - "GenAI Engineer"
  
  experience_levels:
    - "Entry Level"
    - "Junior"
    - "0-2 years"
    - "Fresh Graduate"
```

### Job Filters
```yaml
job_criteria:
  keywords:
    required:
      - "Machine Learning"
      - "AI"
      - "LLM"
    
    preferred:
      - "RAG"
      - "LangChain"
      - "PyTorch"
    
    boost_keywords:
      - "fresh graduate"
      - "entry level"
  
  excluded_keywords:
    - "5+ years"
    - "Senior"
    - "Lead"
    - "PhD required"
```

### Application Settings
```yaml
application:
  max_applications_per_day: 15  # Quality over quantity
  match_score_threshold: 70     # Minimum match score
  manual_review_count: 20       # First N require approval
```

## 🔐 Security & Privacy

- **API Keys**: Stored in `.env` (not committed to Git)
- **Personal Data**: Encrypted in database (TODO)
- **LinkedIn**: Use responsibly, respect rate limits
- **Ethical Guidelines**: No spam, authentic applications only

## 🚧 Roadmap

### Phase 1: Foundation (✅ Completed)
- [x] Project structure and configuration
- [x] Resume PDF parsing
- [x] GitHub API integration
- [x] Project knowledge base with RAG
- [x] Embedding generation
- [x] Base scraper with anti-detection
- [x] LinkedIn job scraper

### Phase 2: Matching & Customization (🚧 In Progress)
- [ ] Skill extraction from job descriptions
- [ ] Semantic job matching engine
- [ ] Multi-criteria ranking system
- [ ] LLM-powered cover letter generator
- [ ] Resume customizer
- [ ] Screening question answerer

### Phase 3: Automation & Tracking (📅 Planned)
- [ ] Form filling automation
- [ ] ATS-specific handlers
- [ ] Application database
- [ ] Follow-up scheduler
- [ ] Analytics dashboard

### Phase 4: Review & Learning (📅 Planned)
- [ ] Streamlit approval interface
- [ ] Feedback loop for improvement
- [ ] Success metrics tracking
- [ ] Skills gap analysis

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## ⚠️ Disclaimer

**Use this system responsibly:**
- Respect job board Terms of Service
- Don't spam applications
- Review applications before submission
- Customize for genuine interest only
- Maintain authenticity in communications

**LinkedIn Scraping:**
LinkedIn's ToS prohibits automated scraping. This tool is for personal use only. Consider using LinkedIn's official API when available.

## 📝 License

MIT License - See LICENSE file for details

## 🙋‍♂️ Support

For issues or questions:
1. Check the logs in `logs/job_agent.log`
2. Review configuration files
3. Ensure all API keys are set
4. Open an issue on GitHub

## 🎉 Success Stories

*Coming soon - share your success stories!*

---

**Built with ❤️ for fresh AI/ML graduates by Makilesh M**

*Good luck with your job search! 🚀*


#but not enough-fatbat
