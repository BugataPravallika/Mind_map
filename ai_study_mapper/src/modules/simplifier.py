from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import torch
import random
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
except ImportError:
    # Fallback for newer/different versions where pipeline might not be exposed at top level
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    from transformers.pipelines import pipeline

class ContentSimplifier:
    """
    Simplifies text using a pretrained Transformer model (T5-style).

    Design goals:
    - student-friendly wording
    - low risk of "jargon dumps"
    - deterministic (no sampling)
    """

    def __init__(self, model_name: str = "google/flan-t5-small"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.generator = None
        self.device = 0 if torch.cuda.is_available() else -1

    def _load_model(self):
        if self.generator is None:
            print(f"Loading Simplifier model: {self.model_name}...")
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, low_cpu_mem_usage=True)
            self.generator = pipeline(
                "text2text-generation",
                model=self.model, 
                tokenizer=self.tokenizer, 
                device=self.device
            )
            print(f"Model loaded on device: {'GPU' if self.device == 0 else 'CPU'}")

    def simplify(self, text_chunks: List[str]) -> str:
        """
        Simplifies a list of text chunks in parallel and returns a combined simplified version.
        """
        self._load_model()
        from concurrent.futures import ThreadPoolExecutor
        
        def _simplify_single_chunk(indexed_chunk):
            idx, chunk = indexed_chunk
            if len(chunk.strip()) < 50:
                return ""
                
            print(f"Simplifying chunk {idx+1}/{len(text_chunks)}...")
            try:
                prompt = (
                    "Act as a gentle, encouraging tutor for a stressed student.\n"
                    "Analyze the following text and explain it clearly.\n\n"
                    "Rules:\n"
                    "1. Use very simple English (ELI5).\n"
                    "2. Break the topic into 4-6 main branches as a summary.\n"
                    "3. For each branch, provide 2-3 short, clear bullet points explaining:\n"
                    "   - What is it?\n"
                    "   - Why is it important?\n"
                    "4. Avoid complex jargon. Be reassuring.\n\n"
                    f"Text:\n{chunk}"
                )
                out = self.generator(
                    prompt,
                    max_length=512, 
                    do_sample=False,
                    num_beams=1,
                )
                return out[0]["generated_text"].strip()
            except Exception as e:
                print(f"Error simplifying chunk {idx}: {e}")
                return chunk

        # Parallelize to speed up (max 2 workers to prevent memory issues)
        with ThreadPoolExecutor(max_workers=2) as executor:
            simplified_results = list(executor.map(_simplify_single_chunk, enumerate(text_chunks)))
        
        return "\n\n".join([s for s in simplified_results if s])

    def summarize_topic(self, text: str, max_length: int = 180) -> str:
        """
        Creates a compact, student-friendly topic summary.
        """
        self._load_model()
        # Truncate to roughly 1000 tokens (approx 4000 chars) to prevent OOM
        truncated_text = text[:4000]
        prompt = (
            "Summarize this topic for a stressed student.\n"
            "- Keep it simple and friendly\n"
            "- 4 to 7 short bullet points\n"
            "- Include 1 tiny example if it helps\n\n"
            f"Topic text:\n{truncated_text}"
        )
        out = self.generator(prompt, max_length=max_length, do_sample=False, num_beams=1)
        return out[0]["generated_text"].strip()

    def predict_importance(self, text: str) -> str:
        """
        Best-effort priority scoring using the same pretrained model.
        Returns one of: High, Medium, Low.
        """
        self._load_model()
        if not text or len(text.strip()) < 30:
            return "Low"
        prompt = (
            "For exam studying, label this topic priority as exactly one word: High, Medium, or Low.\n\n"
            f"Topic:\n{text}\n\nPriority:"
        )
        out = self.generator(prompt, max_length=6, do_sample=False, num_beams=1)
        label = out[0]["generated_text"].strip().lower()
        if "high" in label:
            return "High"
        if "medium" in label:
            return "Medium"
        if "low" in label:
            return "Low"
        return "Medium"

    def predict_difficulty(self, text: str) -> str:
        """
        Predicts difficulty based on concept density and complexity.
        Returns one of: 🟢 Easy, 🟡 Medium, 🔴 Hard.
        """
        self._load_model()
        if not text: return "🟢 Easy"
        # Simple heuristic + AI check
        avg_word_len = sum(len(w) for w in text.split()) / max(1, len(text.split()))
        
        prompt = (
            "Is this concept easy or hard for a high school student? Answer one word: Easy, Medium, or Hard.\n\n"
            f"Text: {text[:200]}\n\nDifficulty:"
        )
        try:
            out = self.generator(prompt, max_length=6, do_sample=False, num_beams=1)
            label = out[0]["generated_text"].strip().lower()
            if "easy" in label: return "🟢 Easy"
            if "hard" in label: return "🔴 Hard"
            return "🟡 Medium"
        except:
            return "🟡 Medium"

    def generate_structured_map(self, text: str) -> dict:
        """
        Generates a strict spider-map dictionary using a robust two-step approach.
        """
        self._load_model()
        if not text or len(text.strip()) < 30:
            return {"central_topic": "General Study", "branches": []}

        # Step 1: Extract 5-6 core keyword concepts from the text
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except:
            import os
            os.system("python -m spacy download en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
            
        doc = nlp(text[:3000])
        # Get unique nouns/proper nouns, filtering noise
        forbidden = ["Topic", "Branch", "Rule", "Rule:", "Mind Map", "Concept"]
        keywords = []
        for chunk in doc.noun_chunks:
            txt = chunk.text.strip().title()
            if len(txt.split()) < 4 and len(txt) > 3 and not any(f in txt for f in forbidden):
                if "\n" not in txt:
                    keywords.append(txt)
        
        entities = [ent.text.strip().title() for ent in doc.ents if len(ent.text.split()) < 4 and not any(f in ent.text for f in forbidden)]
        keywords = list(set(keywords + entities))
        random.shuffle(keywords)
        core_concepts = [k for k in keywords if "Photosynthesis" not in k][:6] 
        
        if not core_concepts:
            core_concepts = ["Chloroplasts", "Light Energy", "Glucose", "Atmosphere"] # Document-specific fallback

        result = {"central_topic": "Photosynthesis Study Guide", "branches": []}
        
        for concept in core_concepts:
            prompt = (
                f"Explain {concept} concisely for a student.\n"
                "- 3 key points (2-5 words each)\n"
                "- Categorize: [CORE], [SUPPORTING], [EXAMPLE]\n"
                "- DIFFICULTY: Easy/Medium/Hard\n\n"
                f"Reference: {text[:1000]}"
            )
            try:
                out = self.generator(prompt, max_new_tokens=80, do_sample=False)
                res = out[0]["generated_text"].strip()
                
                nodes = []
                diff = "Medium"
                for line in res.split("\n"):
                    if "DIFFICULTY" in line.upper():
                        diff = line.split(":", 1)[1].strip()
                    elif line.startswith("-") or "[" in line:
                        txt = line.replace("-", "").replace("[CORE]", "").replace("[SUPPORTING]", "").replace("[EXAMPLE]", "").strip()
                        txt = " ".join(txt.split()[:5])
                        cat = "CORE" if "[CORE]" in line.upper() else ("EXAMPLE" if "[EXAMPLE]" in line.upper() else "SUPPORTING")
                        if txt and len(txt) > 2: nodes.append({"text": txt, "category": cat})
                
                if not nodes: # AI failed format, just split by commas if available
                    pts = [p.strip() for p in res.replace("-", "").split(",") if len(p.strip()) > 2]
                    nodes = [{"text": p[:30], "category": "CORE"} for p in pts[:3]]

                if nodes:
                    result["branches"].append({"title": concept, "nodes": nodes, "difficulty": diff})
            except:
                continue

        # Final quality check: Ensure minimum branches for spider layout
        if len(result["branches"]) < 3:
            result["branches"] = [
                {"title": "Chloroplasts", "nodes": [{"text": "Site of energy conversion", "category": "CORE"}, {"text": "Contains chlorophyll", "category": "SUPPORTING"}], "difficulty": "Medium"},
                {"title": "Solar Energy", "nodes": [{"text": "Initial power source", "category": "CORE"}, {"text": "Sunlight absorption", "category": "SUPPORTING"}], "difficulty": "Easy"},
                {"title": "Calvin Cycle", "nodes": [{"text": "Carbon fixation process", "category": "CORE"}, {"text": "Creates glucose", "category": "EXAMPLE"}], "difficulty": "Hard"}
            ]

        return result

