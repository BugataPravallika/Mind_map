from __future__ import annotations

import argparse
import os
from typing import List, Optional


def _missing_deps() -> List[str]:
    missing = []
    try:
        import transformers  # noqa: F401
    except Exception:
        missing.append("transformers")

    try:
        import whisper  # noqa: F401
    except Exception:
        missing.append("openai-whisper (import name: whisper)")

    try:
        from TTS.api import TTS  # noqa: F401
    except Exception:
        missing.append("coqui-tts (import name: TTS)")

    return missing


def _print_install_help() -> None:
    print(
        "\nMissing Python packages.\n"
        "Install dependencies first, then rerun this downloader.\n\n"
        "From the project root, run:\n"
        "  pip install -r ai_study_mapper/requirements.txt\n\n"
        "Optional (UI):\n"
        "  pip install streamlit\n\n"
        "Then rerun:\n"
        "  python ai_study_mapper/scripts/download_models.py --include-whisper --whisper-size base --include-tts\n"
    )


def _download_transformers_model(model_name: str, cache_dir: str | None) -> None:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    kw = {}
    if cache_dir:
        kw["cache_dir"] = cache_dir

    print(f"\n[download] {model_name}")
    AutoTokenizer.from_pretrained(model_name, **kw)
    AutoModelForSeq2SeqLM.from_pretrained(model_name, **kw)

def _download_whisper(model_size: str) -> None:
    """
    Downloads/caches the Whisper model weights.
    openai-whisper stores models in the default cache location.
    """
    import whisper

    print(f"\n[download] whisper:{model_size}")
    whisper.load_model(model_size)


def _download_coqui_tts(model_name: str) -> None:
    """
    Downloads/caches a Coqui TTS model.
    Coqui stores models in its own cache directory by default.
    """
    from TTS.api import TTS
    import torch

    use_gpu = torch.cuda.is_available()
    print(f"\n[download] coqui-tts:{model_name} (GPU available: {use_gpu})")
    # Instantiating triggers download if missing.
    TTS(model_name=model_name, progress_bar=False, gpu=use_gpu)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-download models for offline use.")
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Optional HuggingFace cache dir (otherwise default HF cache is used).",
    )
    parser.add_argument(
        "--include-whisper",
        action="store_true",
        help="Also download Whisper model weights for offline transcription.",
    )
    parser.add_argument(
        "--whisper-size",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size to download (default: base).",
    )
    parser.add_argument(
        "--include-tts",
        action="store_true",
        help="Also download a Coqui TTS model for offline audio generation.",
    )
    parser.add_argument(
        "--tts-model",
        default="tts_models/en/ljspeech/vits",
        help="Coqui TTS model name (default: tts_models/en/ljspeech/vits).",
    )
    parser.add_argument(
        "--include-telugu",
        action="store_true",
        help="Also try downloading Telugu models (may not exist in every mirror).",
    )
    args = parser.parse_args()

    missing = _missing_deps()
    if missing:
        print("[error] Missing modules:", ", ".join(missing))
        _print_install_help()
        return 3

    cache_dir = args.cache_dir
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        print(f"Using cache dir: {cache_dir}")

    # Core simplification model
    models: List[str] = [
        "google/flan-t5-base",
        # MarianMT (English <-> requested Indian languages)
        "Helsinki-NLP/opus-mt-hi-en",
        "Helsinki-NLP/opus-mt-en-hi",
        "Helsinki-NLP/opus-mt-ta-en",
        "Helsinki-NLP/opus-mt-en-ta",
        "Helsinki-NLP/opus-mt-ml-en",
        "Helsinki-NLP/opus-mt-en-ml",
        # Fallback pivot (many languages -> English)
        "Helsinki-NLP/opus-mt-mul-en",
    ]

    if args.include_telugu:
        models.extend(
            [
                "Helsinki-NLP/opus-mt-te-en",
                "Helsinki-NLP/opus-mt-en-te",
            ]
        )

    failed = []
    # Transformers / Marian / T5
    for m in models:
        try:
            _download_transformers_model(m, cache_dir)
        except Exception as e:
            failed.append((m, str(e)))
            print(f"[warn] Failed to download {m}: {e}")

    # Whisper (video/audio -> text)
    if args.include_whisper:
        try:
            _download_whisper(args.whisper_size)
        except Exception as e:
            failed.append((f"whisper:{args.whisper_size}", str(e)))
            print(f"[warn] Failed to download whisper:{args.whisper_size}: {e}")

    # Coqui TTS (text -> audio)
    if args.include_tts:
        try:
            _download_coqui_tts(args.tts_model)
        except Exception as e:
            failed.append((f"coqui-tts:{args.tts_model}", str(e)))
            print(f"[warn] Failed to download coqui-tts:{args.tts_model}: {e}")

    print("\nDone.")
    if failed:
        print("\nSome models could not be downloaded:")
        for m, err in failed:
            print(f"- {m}: {err}")
        print("\nYou can still run offline using the models that succeeded.")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

