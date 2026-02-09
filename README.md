# AI Study Map Generator

An AI-powered application that converts educational documents (PDF, DOCX) and videos into simple, student-friendly mind maps and study plans.

## Features
- **File Support**: PDF, DOCX, Video (MP4, etc.)
- **Text Simplification**: Uses pretrained T5 (FLAN-T5 small) to rewrite content in friendly language.
- **Mind Mapping**: Generates interactive HTML mind maps.
- **Study Planner**: Estimates study time and creates a schedule.
- **Voice**: Converts summaries to audio using Coqui TTS.
- **Translation**: Translates content to other languages.

## Setup Instructions

1.  **Install Python**: Ensure you have Python 3.10+ installed.
2.  **Install Dependencies**:
    Run the following command in your terminal:
    ```bash
    pip install -r ai_study_mapper/requirements.txt
    pip install streamlit
    python -m spacy download en_core_web_sm
    ```
    *Note: If you have a GPU, ensure you have the correct PyTorch version installed.*

3.  **Run the Application**:
    ```bash
    streamlit run ai_study_mapper/src/app.py
    ```

## Offline setup (recommended for Telugu/Hindi/Tamil/Malayalam)

Download models once while you have internet:

```bash
python ai_study_mapper/scripts/download_models.py
```

Optional: also attempt Telugu model downloads (may fail on some mirrors):

```bash
python ai_study_mapper/scripts/download_models.py --include-telugu
```

Optional: also download voice models for fully offline video+audio support:

```bash
python ai_study_mapper/scripts/download_models.py --include-whisper --whisper-size base --include-tts
```

Then in the Streamlit sidebar, enable **Offline mode** to force “local models only”.

## Project Structure
- `src/modules`: Individual logic components (Input, Cleaning, AI models).
- `src/pipeline.py`: Orchestrator script.
- `src/app.py`: Streamlit UI entry point.
- `data/output`: Generated mind maps and audio files.

## End-to-end pipeline (what happens after upload)

### 1) Input handling (PDF / DOCX / Video / Audio)
- **PDF**: `pdfplumber` extracts text per page.
- **DOCX**: `python-docx` extracts paragraph text.
- **Video/Audio**: `openai-whisper` transcribes speech to text (pretrained).
- **Why it reduces stress**: Students don’t have to manually retype or skim everything first; the system “pulls out” the content for them.

### 2) Language detection + English pivot
- **Detect**: `langdetect` detects the input language.
- **Pivot**: non-English text is translated to **English** (pivot language) using **HuggingFace MarianMT** so the downstream NLP stays consistent.
- **Why pivot**: spaCy concept extraction + T5 simplification are much more stable in a single language.

### 3) Text preprocessing (noise removal + chunking)
Done in `src/modules/text_cleaner.py`:
- Regex cleaning removes:
  - citations like `[12]`, `(Smith, 2020)`, DOIs/URLs
  - common math/LaTeX blocks (best-effort)
  - reference/bibliography sections (truncate after heading)
- Sentence segmentation + paragraph-aware chunking to keep chunks small enough for transformers.
- **Why it reduces stress**: removes “academic clutter” that overwhelms students (citations, long formulas, references), while keeping meaning.

### 4) Multi-document topic clustering (for unified mind maps)
Done in `src/modules/topic_clusterer.py`:
- **TF‑IDF + KMeans** clusters chunks into a small number of topics (default ≤ 6).
- **Explainable**: each topic comes with top TF‑IDF terms (why the cluster exists).
- **Why it reduces stress**: students see *a few topics* instead of a wall of text.

### 5) Student-friendly simplification (pretrained model only)
Done in `src/modules/simplifier.py`:
- Uses **`google/flan-t5-small`** (pretrained, lightweight) with prompts like:
  - “Rewrite this in simple, friendly English for a stressed student…”
  - “Summarize into 4–7 short bullet points… include a tiny example…”
- **Priority scoring (High/Medium/Low)**: best-effort label via the same pretrained model (with rule-based fallbacks elsewhere).
- **Why it reduces stress**: short bullets + gentle explanations reduce cognitive load and panic.

### 6) Key concept extraction + classification (rule-based + spaCy)
Done in `src/modules/concept_extractor.py`:
- Uses **spaCy** noun chunks + entities.
- Rule-based classification into:
  - **Core ideas** (High)
  - **Supporting ideas** (Medium)
  - **Examples** (Low) based on “for example / such as …” sentences
- Hard caps on node counts to avoid overload.

### 7) Relationship mapping (simple, shallow hierarchy)
Done in `src/modules/graph_builder.py`:
- Enforces:
  - **one parent per node**
  - **limited children per node** (default 6)
  - shallow structure with a single center node
- **Why it reduces stress**: prevents huge, messy graphs that feel impossible to study.

### 8) Mind map generation (clean visualization)
Done in `src/modules/visualizer.py`:
- **NetworkX** stores the directed graph.
- **PyVis** renders a clean, light-theme, hierarchical HTML mind map.

### 9) Time-based study roadmap
Done in `src/modules/study_planner.py`:
- Estimates time using word count + reading speed.
- Allocates daily topics **by priority first** and keeps an **intentional time buffer** for breaks.
- Output: day-by-day plan.

### 10) Voice support (offline after download)
Done in `src/modules/voice_generator.py`:
- **Coqui TTS** converts the simplified summary into audio (AI voice note).
- “Human voice note” is supported via uploading audio/video for Whisper transcription.

### 11) Output language
- If the user selects a non-English target language, the simplified English output is translated back using **MarianMT**.

## Modular architecture (text diagram)

```
[Streamlit UI]
   |
   v
[StudyMapPipeline]
   |
   +--> InputHandler (pdfplumber / docx / whisper)
   |
   +--> LanguageService (langdetect + MarianMT pivot)
   |
   +--> TextCleaner (regex clean + chunking)
   |
   +--> TopicClusterer (TF-IDF + KMeans)
   |
   +--> ContentSimplifier (FLAN-T5 small)
   |
   +--> ConceptExtractor (spaCy + rules)
   |
   +--> GraphBuilder (shallow, limited edges)
   |
   +--> Visualizer (PyVis HTML)
   |
   +--> StudyPlanner (priority-based schedule)
   |
   +--> VoiceGenerator (Coqui TTS)
   |
   +--> Translator (MarianMT output translation)
```

## Model/library choices (why these)
- **Whisper (pretrained)**: robust transcription; runs locally; no training required.
- **FLAN‑T5 small**: fast + decent instruction following; good for “explain simply” prompts.
- **spaCy**: explainable, deterministic NLP primitives (noun chunks, dependencies).
- **MarianMT**: offline-capable translation after first download; many language pairs.
- **TF‑IDF + KMeans**: lightweight, explainable topic clustering.

## Future improvements (safe + student-friendly)
- Better “example” detection (pattern library + more robust parsing).
- Optional embeddings-based clustering (SentenceTransformers) for higher quality topics.
- Per-topic mini‑quizzes + spaced repetition (still rule-based, low stress).
- Export formats: PNG/SVG mind map, Anki decks, Notion/Markdown.
- Cached model loading + progress indicators for smoother UX on low-end laptops.
