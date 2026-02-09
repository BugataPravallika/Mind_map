@echo off
echo ==========================================
echo      AI Study Map - GitHub Pusher
echo ==========================================

REM Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in your PATH.
    echo Please install Git from https://git-scm.com/download/win
    echo After installing, restart your terminal and run this script again.
    pause
    exit /b
)

REM Use the provided repository URL
set REPO_URL=https://github.com/BugataPravallika/Mind_map

echo.
echo [1/5] Initializing Git repository...
git init

echo.
echo [2/5] Adding files...
git add .

echo.
echo [3/5] Committing files...
git commit -m "Initial commit of AI Study Map Generator"

echo.
echo [4/5] Adding remote origin...
git remote add origin %REPO_URL%

echo.
echo [5/5] Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo ==========================================
echo      Done! Project pushed to GitHub.
echo ==========================================
pause
