from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from langdetect import DetectorFactory, detect

from .translator import Translator


DetectorFactory.seed = 42  # make langdetect deterministic(ish)


@dataclass
class LanguageResult:
    detected: str
    pivot_text_en: str


class LanguageService:
    """
    Detects language and optionally pivots content to English (en).

    Why pivot:
    - keeps simplification + spaCy concept extraction consistent
    - reduces failure modes for non-English PDFs/lectures
    """

    def __init__(self, prefer_offline: bool = False):
        self.prefer_offline = prefer_offline

    def detect_language(self, text: str) -> str:
        if not text or len(text.strip()) < 20:
            return "en"
        try:
            return (detect(text) or "en").lower()
        except Exception:
            return "en"

    def pivot_to_english(self, text: str, src_lang: Optional[str] = None) -> LanguageResult:
        src = (src_lang or self.detect_language(text)).lower()
        if src == "en":
            return LanguageResult(detected=src, pivot_text_en=text)

        # First try direct src->en model
        translator = Translator(src_lang=src, target_lang="en", prefer_offline=self.prefer_offline)
        pivot = translator.translate_text(text)

        # If that fails (common for less-supported pairs), fall back to mul->en
        if (pivot == text) or (translator.model is None):
            translator2 = Translator(src_lang="mul", target_lang="en", prefer_offline=self.prefer_offline)
            pivot2 = translator2.translate_text(text)
            if pivot2 and pivot2 != text:
                pivot = pivot2

        return LanguageResult(detected=src, pivot_text_en=pivot)

    def translate_from_english(self, text_en: str, target_lang: str) -> str:
        tgt = (target_lang or "en").lower()
        if tgt == "en":
            return text_en
        translator = Translator(src_lang="en", target_lang=tgt, prefer_offline=self.prefer_offline)
        return translator.translate_text(text_en)

