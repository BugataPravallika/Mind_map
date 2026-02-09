from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch
from transformers import MarianMTModel, MarianTokenizer

class Translator:
    """
    Translates text using MarianMT (offline-capable after first download).

    Supports:
    - pivoting to English (src -> en)
    - translating from English (en -> tgt)
    - direct src -> tgt when a known model exists
    """

    _MODEL_CACHE: Dict[str, Tuple[MarianTokenizer, MarianMTModel]] = {}

    def __init__(
        self,
        src_lang: str = "en",
        target_lang: str = "fr",
        prefer_offline: bool = False,
    ):
        self.src_lang = (src_lang or "en").lower()
        self.target_lang = (target_lang or "en").lower()
        self.prefer_offline = prefer_offline

        self.model_name = self._choose_model_name(self.src_lang, self.target_lang)
        self.tokenizer: Optional[MarianTokenizer] = None
        self.model: Optional[MarianMTModel] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _ensure_model_loaded(self):
        if self.model_name is None:
            return False
            
        if self.model is not None:
            return True

        if self.model_name in Translator._MODEL_CACHE:
            self.tokenizer, self.model = Translator._MODEL_CACHE[self.model_name]
            return True

        print(f"Loading Translator model: {self.model_name}...")
        try:
            self.tokenizer = MarianTokenizer.from_pretrained(
                self.model_name, local_files_only=self.prefer_offline
            )
            self.model = MarianMTModel.from_pretrained(
                self.model_name, local_files_only=self.prefer_offline
            ).to(self.device)
            Translator._MODEL_CACHE[self.model_name] = (self.tokenizer, self.model)
            return True
        except Exception as e:
            print(f"Error loading translator model {self.model_name}: {e}")
            self.model = None
            return False

    def translate(self, text_chunks: List[str]) -> List[str]:
        """
        Translates a list of text chunks.
        """
        if not self._ensure_model_loaded():
            return text_chunks # Return original if no model
        
        translated_chunks = []
        try:
            # Small batching to keep latency reasonable
            batch_size = 4
            for i in range(0, len(text_chunks), batch_size):
                batch = text_chunks[i : i + batch_size]
                inputs = self.tokenizer(
                    batch, return_tensors="pt", padding=True, truncation=True
                ).to(self.device)
                translated = self.model.generate(**inputs, max_length=256)
                for seq in translated:
                    tgt_text = self.tokenizer.decode(seq, skip_special_tokens=True)
                    translated_chunks.append(tgt_text)
        except Exception as e:
            print(f"Translation error: {e}")
            return text_chunks

        return translated_chunks

    def translate_text(self, text: str, max_chunk_chars: int = 1200) -> str:
        """
        Convenience helper for long strings: chunk -> translate -> join.
        """
        if not text or not text.strip():
            return text

        chunks: List[str] = []
        buf: List[str] = []
        cur = 0
        for part in text.split("\n"):
            part = part.strip()
            if not part:
                continue
            if cur + len(part) + 1 > max_chunk_chars and buf:
                chunks.append(" ".join(buf))
                buf = [part]
                cur = len(part)
            else:
                buf.append(part)
                cur += len(part) + 1
        if buf:
            chunks.append(" ".join(buf))

        return "\n\n".join(self.translate(chunks))

    @staticmethod
    def _choose_model_name(src_lang: str, target_lang: str) -> Optional[str]:
        """
        MarianMT model selection heuristic.

        Notes:
        - Best-effort: Marian doesn't have every possible pair.
        - We prefer direct pairs; otherwise fall back to 'mul' for ->en.
        """
        src = (src_lang or "en").lower()
        tgt = (target_lang or "en").lower()
        if src == tgt:
            return None

        # --- Strong mappings for Indian languages (requested) ---
        # Marian/OPUS uses ISO-like codes (hi, ta, ml, te, en).
        # We explicitly map these first to avoid ambiguity and maximize success.
        pair_map = {
            ("hi", "en"): "Helsinki-NLP/opus-mt-hi-en",
            ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
            ("ta", "en"): "Helsinki-NLP/opus-mt-ta-en",
            ("en", "ta"): "Helsinki-NLP/opus-mt-en-ta",
            ("ml", "en"): "Helsinki-NLP/opus-mt-ml-en",
            ("en", "ml"): "Helsinki-NLP/opus-mt-en-ml",
            # Telugu models are not guaranteed across all mirrors; try direct first.
            ("te", "en"): "Helsinki-NLP/opus-mt-te-en",
            ("en", "te"): "Helsinki-NLP/opus-mt-en-te",
            # Multilingual fallbacks
            ("mul", "en"): "Helsinki-NLP/opus-mt-mul-en",
            ("en", "mul"): "Helsinki-NLP/opus-mt-en-mul",
        }
        if (src, tgt) in pair_map:
            return pair_map[(src, tgt)]

        # Direct language pair (common)
        direct = f"Helsinki-NLP/opus-mt-{src}-{tgt}"

        # Some broad multilingual-to-English models exist
        if tgt == "en" and src not in {"en"}:
            # Prefer direct if available; if not, mul-en is a reasonable fallback.
            # We'll still attempt direct first by returning it; caller will fail
            # and can choose to re-init with mul-en if desired.
            return direct

        # English to target (common)
        if src == "en" and tgt != "en":
            return f"Helsinki-NLP/opus-mt-en-{tgt}"

        # Otherwise attempt direct
        return direct

if __name__ == "__main__":
    # Test stub
    # translator = Translator(target_lang="es") # Spanish
    # print(translator.translate(["Hello world", "This is a test."]))
    print("Translator stub.")
