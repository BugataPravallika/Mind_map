import os
import torch

class VoiceGenerator:
    """
    Generates audio from text using Coqui TTS.
    """

    def __init__(self, model_name: str = "tts_models/en/ljspeech/vits"):
        self.model_name = model_name
        self.tts = None
        self.use_gpu = torch.cuda.is_available()

    def _load_model(self):
        if self.tts is None:
            print(f"Loading TTS model: {self.model_name} (GPU: {self.use_gpu})...")
            try:
                from TTS.api import TTS
                self.tts = TTS(model_name=self.model_name, progress_bar=False, gpu=self.use_gpu)
            except Exception as e:
                print(f"Error initializing TTS: {e}")
                self.tts = None

    def generate_audio(self, text: str, output_path: str):
        """
        Generates an audio file from text.
        """
        self._load_model()
        if not self.tts:
            print("TTS model not initialized. Skipping audio generation.")
            return
        
        print(f"Generating audio to {output_path}...")
        try:
            self.tts.tts_to_file(text=text, file_path=output_path)
            print("Audio generation complete.")
        except Exception as e:
            print(f"Error generating audio: {e}")

if __name__ == "__main__":
    # Test stub
    # generator = VoiceGenerator()
    # generator.generate_audio("Hello, this is a test.", "test.wav")
    print("VoiceGenerator stub.")
