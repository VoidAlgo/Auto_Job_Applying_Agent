@echo off
echo ========================================
echo Automated Job Application Agent Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org
    pause
    exit /b 1
)

echo [1/6] Python found
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate
echo.

REM Upgrade pip
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo [5/6] Installing dependencies...
pip install -r requirements.txt
echo.

REM Download spaCy model
echo [6/6] Downloading spaCy language model...
python -m spacy download en_core_web_sm
echo.

REM Create directories
echo Creating necessary directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist docs mkdir docs
if not exist projects mkdir projects
if not exist debug mkdir debug
echo.

REM Copy env example
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo ========================================
    echo IMPORTANT: Edit .env file and add your API keys
    echo ========================================
) else (
    echo .env file already exists
)
echo.

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env and add your API keys
echo 2. Update config/candidate_profile.yaml with your information
echo 3. Place your resume in docs/resume.pdf
echo 4. Add project descriptions to projects/ folder
echo 5. Run: python main.py --profile-only
echo.
echo For help, run: python main.py --help
echo.
pause
