@echo off
echo ==========================================
echo      AI Study Map - Environment Setup
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo.
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo.
    echo *** CRITICAL STEP ***
    echo During installation, you MUST check the box that says:
    echo "Add Python.exe to PATH"
    echo.
    echo After installing, close this window and run me again!
    pause
    exit /b
)

echo [OK] Python found!

echo.
echo [1/3] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/3] Installing dependencies...
python -m pip install -r ai_study_mapper/requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

echo.
echo [3/3] Downloading AI models...
python ai_study_mapper/scripts/download_models.py

echo.
echo ==========================================
echo      Setup Complete! You are ready.
echo ==========================================
echo To run the app, use: run_app.bat
pause
