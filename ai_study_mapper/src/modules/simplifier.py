from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import torch
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
        Generates a strict dictionary structure for a one-page revision sheet.
        """
        self._load_model()
        if not text or len(text.strip()) < 30:
            return {"central_topic": "Topic", "branches": []}

        prompt = (
            "You are an AI educational designer. Generate a student-friendly MIND MAP.\n"
            "Structure Rules:\n"
            "1. MAIN TOPIC at center.\n"
            "2. 4-6 main BRANCHES.\n"
            "3. 3-5 short SUB-NODES per branch (Keywords only).\n"
            "4. CATEGORIZE sub-nodes: [CORE], [SUPPORTING], or [EXAMPLE].\n"
            "5. TAG difficulty: Easy, Medium, or Hard.\n"
            "6. MARK exam-focused points with ⭐.\n\n"
            "Output format MUST be:\n"
            "TOPIC: <Main Topic>\n"
            "BRANCH: <Branch Title>\n"
            "DIFFICULTY: <Easy/Medium/Hard>\n"
            "MNEMONIC: <Memory Hook>\n"
            "- [CORE] <Keyword> ⭐\n"
            "- [SUPPORTING] <Keyword>\n"
            "- [EXAMPLE] <Short example>\n"
            "...\n\n"
            f"Content: {text[:2500]}"
        )
        
        try:
            out = self.generator(prompt, max_length=1024, do_sample=False, num_beams=1)
            raw = out[0]["generated_text"].strip()
            
            lines = raw.split('\n')
            result = {"central_topic": "Study Map", "branches": []}
            current_branch = None
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                if line.upper().startswith("TOPIC:"):
                    result["central_topic"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("BRANCH:"):
                    if current_branch:
                        result["branches"].append(current_branch)
                    current_branch = {"title": line.split(":", 1)[1].strip(), "nodes": [], "difficulty": "Medium", "mnemonic": ""}
                elif line.upper().startswith("DIFFICULTY:") and current_branch:
                    current_branch["difficulty"] = line.split(":", 1)[1].strip()
                elif line.upper().startswith("MNEMONIC:") and current_branch:
                    current_branch["mnemonic"] = line.split(":", 1)[1].strip()
                elif line.startswith("-") and current_branch:
                    node_text = line[1:].strip()
                    cat = "SUPPORTING"
                    if "[CORE]" in node_text.upper(): cat = "CORE"
                    elif "[EXAMPLE]" in node_text.upper(): cat = "EXAMPLE"
                    
                    clean_text = node_text.replace("[CORE]", "").replace("[SUPPORTING]", "").replace("[EXAMPLE]", "").strip()
                    current_branch["nodes"].append({"text": clean_text, "category": cat})
            
            if current_branch:
                result["branches"].append(current_branch)
                
            # Fallback if parsing failed
            if not result["branches"]:
                result["central_topic"] = "Main Ideas"
                points = [l for l in lines if len(l) > 10]
                chunk_size = 3
                for i in range(0, len(points), chunk_size):
                    chunk = points[i:i+chunk_size]
                    if chunk:
                        result["branches"].append({
                            "title": f"Key Topic {i//chunk_size + 1}", 
                            "nodes": [{"text": p, "category": "CORE"} for p in chunk],
                            "difficulty": "Medium",
                            "mnemonic": "Remember this as a core part of the topic."
                        })
            
            return result
            
        except Exception as e:
            print(f"Error generating map structure: {e}")
            return {"central_topic": "Error", "branches": []}

if __name__ == "__main__":
    # Test stub
    simplifier = ContentSimplifier()
    sample_text = "Photosynthesis is the process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy."
    print(simplifier.generate_structured_map(sample_text))
