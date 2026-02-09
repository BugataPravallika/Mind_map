import random
from typing import List, Dict, Tuple

class QuizGenerator:
    """
    Generates multiple-choice questions (MCQs) from SVO relationships.
    Questions are derived from the structure: [Subject] [Verb] [Object]
    """

    def __init__(self):
        pass

    def generate_quiz_from_structure(self, structure: dict) -> List[Dict]:
        """
        Generates 5 simple questions based ONLY on the structured map branches.
        """
        branches = structure.get("branches", [])
        if not branches:
            return []
            
        questions = []
        random.shuffle(branches)
        
        # 1. Multiple Choice from Branch Meanings
        for b in branches[:3]:
            if not b.get("nodes"): continue
            
            # Pick a core node if possible
            core_nodes = [n for n in b["nodes"] if n.get("category") == "CORE"]
            goal_node = core_nodes[0] if core_nodes else b["nodes"][0]
            goal = goal_node["text"]
            
            # Create distractors from OTHER branch titles
            other_titles = [x["title"] for x in branches if x["title"] != b["title"]]
            random.shuffle(other_titles)
            
            choices = [b["title"]] + other_titles[:3]
            random.shuffle(choices)
            
            questions.append({
                "question": f"Which section explains: *\"{goal}\"*?",
                "options": choices,
                "answer": b["title"],
                "explanation": f"Correct! {b['title']} is where we discuss this topic.",
                "type": "mcq"
            })

        # 2. True/False from specific nodes
        for b in branches[3:5]:
            if not b.get("nodes"): continue
            node = b["nodes"][random.randint(0, len(b["nodes"])-1)]
            point = node["text"]
            
            questions.append({
                "question": f"True or False: **{b['title']}** involves {point}.",
                "options": ["True", "False"],
                "answer": "True",
                "explanation": f"Yes! That is a key part of {b['title']}.",
                "type": "tf"
            })
            
        return questions[:5]
