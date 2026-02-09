
import sys
import os

print("--- Checking Dependencies ---")
dependencies = ["streamlit", "torch", "transformers", "spacy", "networkx", "pyvis", "TTS", "whisper", "langdetect"]
for dep in dependencies:
    try:
        __import__(dep)
        print(f"{dep}: OK")
    except ImportError:
        # Special handling for names that might not match package names exactly
        if dep == "TTS":
            print(f"{dep}: MISSING (might need 'pip install coqui-tts')")
        elif dep == "whisper":
            print(f"{dep}: MISSING (might need 'pip install openai-whisper')")
        else:
            print(f"{dep}: MISSING")
    except Exception as e:
         print(f"{dep}: ERROR {e}")

print("\n--- Checking Project Modules ---")
# Adjust path to include 'ai_study_mapper' so we can import 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "ai_study_mapper")
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.pipeline import StudyMapPipeline
    print("src.pipeline.StudyMapPipeline: OK")
except Exception as e:
    print(f"src.pipeline.StudyMapPipeline: ERROR {e}")
