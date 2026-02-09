import random
from typing import List, Dict

class QuizGenerator:
    """
    Generates strict 4-option Multiple Choice Questions (MCQs) from the mind map.
    """

    def __init__(self):
        pass

    def generate_quiz_from_structure(self, structure: dict) -> List[Dict]:
        """
        Generates 3-5 MCQs based strictly on the structured map.
        Each question has 4 unique options (A, B, C, D).
        """
        branches = structure.get("branches", [])
        if len(branches) < 2:
            return []
            
        questions = []
        all_titles = [b["title"] for b in branches]
        
        # Shuffle to pick random branches for questions
        random.shuffle(branches)
        
        for b in branches[:5]:
            nodes = b.get("nodes", [])
            if not nodes: continue
            
            # Pick a core concept as the question focus
            core_nodes = [n for n in nodes if n.get("category") == "CORE"]
            target_node = core_nodes[0] if core_nodes else nodes[0]
            concept_text = target_node["text"]
            
            # Create exactly 4 options
            # Distractor 1-3 from other branch titles or random concepts
            distractors = [t for t in all_titles if t != b["title"]]
            if len(distractors) < 3:
                # Add generic academic distractors if not enough branches
                distractors += ["General Theory", "Practical Application", "System Framework", "Standard Protocol"]
            
            random.shuffle(distractors)
            choices = [b["title"]] + distractors[:3]
            random.shuffle(choices)
            
            questions.append({
                "question": f"Which concept is most directly associated with: *\"{concept_text}\"*?",
                "options": choices,
                "answer": b["title"],
                "explanation": f"Correct! {b['title']} encompasses this key idea.",
                "type": "mcq"
            })

        return questions[:5]
