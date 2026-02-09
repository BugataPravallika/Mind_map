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
        print(f"Loading Simplifier model: {model_name}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            # Use GPU if available
            self.device = 0 if torch.cuda.is_available() else -1
            # Use text2text so we can prompt for "friendly" simplification.
            self.generator = pipeline(
                "text2text-generation",
                model=self.model, 
                tokenizer=self.tokenizer, 
                device=self.device
            )
            print(f"Model loaded on device: {'GPU' if self.device == 0 else 'CPU'}")
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            raise e

    def simplify(self, text_chunks: List[str]) -> str:
        """
        Simplifies a list of text chunks and returns a combined simplified version.
        """
        simplified_chunks = []
        
        for i, chunk in enumerate(text_chunks):
            if len(chunk.strip()) < 50: # Skip very short chunks
                continue
                
            print(f"Simplifying chunk {i+1}/{len(text_chunks)}...")
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
                    num_beams=1, # Faster greedy search
                )
                simplified_chunks.append(out[0]["generated_text"].strip())
            except Exception as e:
                print(f"Error simplifying chunk {i}: {e}")
                simplified_chunks.append(chunk) # Fallback to original

        return "\n\n".join(simplified_chunks)

    def summarize_topic(self, text: str, max_length: int = 180) -> str:
        """
        Creates a compact, student-friendly topic summary.
        """
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

    def score_priority(self, text: str) -> str:
        """
        Best-effort priority scoring using the same pretrained model.
        Returns one of: High, Medium, Low.
        """
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

    def generate_structured_map(self, text: str) -> dict:
        """
        Generates a strict dictionary structure for the static map.
        Format:
        {
          "central_topic": "...",
          "branches": [
             {"title": "...", "points": ["...", "..."]},
             ...
          ]
        }
        """
        if not text or len(text.strip()) < 30:
            return {"central_topic": "Topic", "branches": []}

        prompt = (
            "Create a structured mental map for a revision sheet.\n"
            "Rules:\n"
            "1. Identify the Main Central Topic.\n"
            "2. Identify 4 to 6 Key Branches (Sub-topics).\n"
            "3. For each branch, write 2 concise explanation sentences.\n"
            "4. Output format MUST be:\n"
            "   TOPIC: <Main Topic>\n"
            "   BRANCH: <Branch Title>\n"
            "   - <Explanation 1>\n"
            "   - <Explanation 2>\n"
            "   BRANCH: <Next Branch Title>\n"
            "   ...\n\n"
            f"Content to map:\n{text[:2500]}" # Strictly limit context to fit model memory
        )
        
        try:
            out = self.generator(prompt, max_length=512, do_sample=False, num_beams=1)
            raw = out[0]["generated_text"].strip()
            
            # Simple Parsing Logic
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
                    current_branch = {"title": line.split(":", 1)[1].strip(), "points": []}
                elif line.startswith("-") and current_branch:
                    current_branch["points"].append(line[1:].strip())
            
            if current_branch:
                result["branches"].append(current_branch)
                
            # Fallback if parsing failed (model didn't follow format)
            if not result["branches"]:
                result["central_topic"] = "Main Ideas"
                # Just treat sentences as points
                points = [l for l in lines if len(l) > 10]
                chunk_size = 2
                for i in range(0, len(points), chunk_size):
                    chunk = points[i:i+chunk_size]
                    if chunk:
                        result["branches"].append({
                            "title": f"Key Point {i//chunk_size + 1}", 
                            "points": chunk
                        })
            
            return result
            
        except Exception as e:
            print(f"Error generating map structure: {e}")
            return {"central_topic": "Error", "branches": [{"title": "Error", "points": ["Could not generate map."]}]}

if __name__ == "__main__":
    # Test stub
    simplifier = ContentSimplifier()
    sample_text = "Photosynthesis is the process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy."
    print(simplifier.generate_structured_map(sample_text))
