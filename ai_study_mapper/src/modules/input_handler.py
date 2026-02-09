import os
import pdfplumber
import docx
import whisper
from typing import List, Dict, Union

class InputHandler:
    """
    Handles loading and text extraction from various file formats:
    - PDF
    - DOCX
    - Video (MP4, MKV, AVI) -> Transcribed via Whisper
    """

    def __init__(self, whisper_model_size: str = "base"):
        self.whisper_model_size = whisper_model_size
        self._whisper_model = None

    def _load_whisper(self):
        if self._whisper_model is None:
            print(f"Loading Whisper model ('{self.whisper_model_size}')...")
            self._whisper_model = whisper.load_model(self.whisper_model_size)

    def process_files(self, file_paths: List[str]) -> str:
        """
        Processes a list of file paths and returns combined extracted text.
        """
        combined_text = []

        for path in file_paths:
            if not os.path.exists(path):
                print(f"Warning: File not found: {path}")
                continue
            
            print(f"Processing: {path}")
            ext = os.path.splitext(path)[1].lower()

            try:
                if ext == ".pdf":
                    text = self._extract_text_from_pdf(path)
                elif ext == ".docx":
                    text = self._extract_text_from_docx(path)
                elif ext in [".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav"]:
                    text = self._transcribe_video(path)
                else:
                    print(f"Unsupported file type: {ext}")
                    continue
                
                if text:
                    combined_text.append(text)
            except Exception as e:
                print(f"Error processing {path}: {e}")

        return "\n\n".join(combined_text)

    def _extract_text_from_pdf(self, path: str) -> str:
        text_content = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content.append(extracted)
        return "\n".join(text_content)

    def _extract_text_from_docx(self, path: str) -> str:
        doc = docx.Document(path)
        text_content = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(text_content)

    def _transcribe_video(self, path: str) -> str:
        self._load_whisper()
        result = self._whisper_model.transcribe(path)
        return result["text"]

if __name__ == "__main__":
    # Test stub
    handler = InputHandler()
    # Add dummy files to test if needed
    print("InputHandler initialized.")
