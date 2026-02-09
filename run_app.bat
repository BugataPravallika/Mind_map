@echo off
echo ==========================================
echo      AI Study Map - Application Runner
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    pause
    exit /b
)

echo [OK] Python found.

REM Check if requirements are installed (simple check for streamlit)
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Dependencies not found. Installing now...
    pip install -r ai_study_mapper/requirements.txt
    pip install streamlit
    python -m spacy download en_core_web_sm
)

echo.
echo Starting AI Study Map Generator...
streamlit run ai_study_mapper/src/app.py
pause
