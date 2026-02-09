@echo off
echo Installing dependencies...
pip install -r ai_study_mapper/requirements.txt
pip install streamlit
python -m spacy download en_core_web_sm

echo (Optional) Downloading models for offline mode...
echo If you do NOT want to download now, close this window.
python ai_study_mapper/scripts/download_models.py --include-whisper --whisper-size base --include-tts

echo Starting AI Study Map Generator...
streamlit run ai_study_mapper/src/app.py
pause
