@echo off
echo [1/4] Installing requirements...
python -m pip install -r ai_study_mapper/requirements.txt
if %errorlevel% neq 0 exit /b %errorlevel%

echo [2/4] Installing Streamlit...
python -m pip install streamlit
if %errorlevel% neq 0 exit /b %errorlevel%

echo [3/4] Downloading spaCy model...
python -m spacy download en_core_web_sm
if %errorlevel% neq 0 exit /b %errorlevel%

echo [4/4] Downloading AI models...
python ai_study_mapper/scripts/download_models.py --include-whisper --whisper-size base --include-tts
if %errorlevel% neq 0 exit /b %errorlevel%

echo Done!
