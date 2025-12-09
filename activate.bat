@echo off
REM Activate virtual environment for Auto Job Applier

echo ========================================
echo Activating Virtual Environment
echo ========================================
echo.

call "%~dp0venv\Scripts\activate.bat"

echo.
echo ✓ Virtual environment activated!
echo.
echo Quick commands:
echo   python check_config.py          - Check configuration
echo   python main.py --max-jobs 10    - Run job application pipeline
echo   deactivate                       - Exit virtual environment
echo.
