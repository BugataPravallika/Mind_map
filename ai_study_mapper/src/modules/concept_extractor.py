import spacy
from collections import Counter
from typing import Dict, List, Tuple

class ConceptExtractor:
    """
    Extracts key concepts and relationships using spaCy.
    """

    def __init__(self, model: str = "en_core_web_sm"):
        print(f"Loading spaCy model: {model}...")
        try:
            self.nlp = spacy.load(model)
        except OSError:
            print(f"Model {model} not found. Please run 'python -m spacy download {model}'")
            raise

    def extract_concepts(
        self,
        text: str,
        max_core: int = 4,
        max_supporting: int = 10,
        max_examples: int = 10,
    ) -> Tuple[Dict[str, List[Dict]], List[Tuple[str, str, str]]]:
        """
        Extracts concepts and classifies them into:
        - core_ideas (High priority)
        - supporting_ideas (Medium priority)
        - examples (Low priority)

        Returns:
        - concepts: dict of lists of {text, priority}
        - relationships: list of (parent, child)
        """
        if not text or not text.strip():
            return {"core_ideas": [], "supporting_ideas": [], "examples": []}, []

        doc = self.nlp(text)
        
        example_markers = {"for example", "e.g.", "eg", "such as", "like", "including"}
        
        # Blocklist for generic academic/filler terms
        blocklist = {
            "this study", "the study", "this paper", "the data", "results", "conclusion",
            "analysis", "method", "methods", "introduction", "background", "we", "they",
            "it", "this", "that", "these", "those", "chapter", "section", "figure", "table",
            "process", "system", "example", "types", "parts", "use", "way"
        }

        # 1. Identify Noun Chunks (Candidate Concepts)
        noun_chunks = []
        for chunk in doc.noun_chunks:
            # Clean text
            c_text = chunk.text.lower().strip()
            # Filter generic checks
            if c_text in blocklist:
                continue
            if len(c_text.split()) > 4: # Too long
                continue
            if len(c_text) < 3: # Too short
                continue
            # Remove determiners at start (the, a, an)
            if c_text.startswith("the ") or c_text.startswith("a ") or c_text.startswith("an "):
                c_text = " ".join(c_text.split()[1:])
            
            noun_chunks.append(c_text)
        
        # 2. Count Frequencies to find Main Concepts
        counts = Counter(noun_chunks)
        
        # Prefer shorter, clearer phrases
        def score_phrase(p: str) -> float:
            if p in blocklist: 
                return -100.0
            base = counts.get(p, 0)
            penalty = 0.0
            if len(p) <= 2:
                penalty += 5.0
            if any(ch.isdigit() for ch in p):
                penalty += 0.8
            return base - penalty

        sorted_phrases = sorted(set(noun_chunks), key=score_phrase, reverse=True)
        # Filter out negative scores
        sorted_phrases = [p for p in sorted_phrases if score_phrase(p) > 0]
        
        # 3. Detect example concepts (from example-like sentences)
        example_concepts: List[str] = []
        for sent in doc.sents:
            s = sent.text.lower()
            if any(m in s for m in example_markers):
                for chunk in sent.noun_chunks:
                    t = chunk.text.lower().strip()
                    # Basic cleaning
                    if t.startswith("the ") or t.startswith("a ") or t.startswith("an "):
                        t = " ".join(t.split()[1:])
                    if 1 <= len(t.split()) <= 4 and t not in blocklist:
                        example_concepts.append(t)
        example_concepts = list(dict.fromkeys(example_concepts))[: (max_examples * 2)]

        # 4. Select core/supporting (excluding examples to reduce overload)
        filtered = [p for p in sorted_phrases if p not in set(example_concepts)]
        core = filtered[:max_core]
        supporting = filtered[max_core : max_core + max_supporting]

        # 5. Entities as extra examples (keep it limited + student-friendly)
        for ent in doc.ents:
            if ent.label_ in {"DATE", "TIME", "PERCENT", "CARDINAL", "ORDINAL"}:
                continue
            t = ent.text.lower().strip()
            if t in blocklist:
                continue
            if 1 <= len(t.split()) <= 4 and t not in core and t not in supporting and t not in example_concepts:
                example_concepts.append(t)
            if len(example_concepts) >= max_examples:
                break

        examples = example_concepts[:max_examples]

        classified_concepts: Dict[str, List[Dict]] = {
            "core_ideas": [{"text": c, "priority": "High"} for c in core],
            "supporting_ideas": [{"text": c, "priority": "Medium"} for c in supporting],
            "examples": [{"text": c, "priority": "Low"} for c in examples],
        }
        
        # 6. Improved Relationship Mapping via Dependency Parsing (Subject -> Verb -> Object)
        relationships: List[Tuple[str, str, str]] = [] # Now Tuple[source, relation, target]
        
        # Create a lookup set for valid concepts to link
        valid_concepts = set(core + supporting + examples)
        
        # Helper to fuzzy match chunk text to our concepts
        def find_match(text_snippet):
            # Try exact match first
            clean = text_snippet.lower().strip()
            if clean.startswith("the ") or clean.startswith("a "):
                clean = " ".join(clean.split()[1:])
            
            if clean in valid_concepts:
                return clean
            # Identify if snippet contains a known concept
            for c in valid_concepts:
                if c in clean:
                    return c
            return None

        for sent in doc.sents:
            # Strategy 1: Subject - Object dependencies
            for token in sent:
                if token.dep_ == "nsubj" or token.dep_ == "nsubjpass": # Subject
                    subj = find_match(token.text)
                    if not subj: # try noun chunk
                        for nc in token.subtree:
                            subj = find_match(nc.text)
                            if subj: break
                    
                    if subj:
                        # Find verb head
                        verb_node = token.head
                        relation = verb_node.lemma_.lower() # e.g. "produce", "contain"
                        
                        # Find object children
                        for child in verb_node.children:
                            if child.dep_ in {"dobj", "attr", "pobj"}:
                                obj = find_match(child.text)
                                if obj and obj != subj:
                                    relationships.append((subj, relation, obj))
                            # Handle prep (e.g., "is valid for...")
                            if child.dep_ == "prep":
                                for grandchild in child.children:
                                    if grandchild.dep_ == "pobj":
                                        obj = find_match(grandchild.text)
                                        if obj and obj != subj:
                                            # relation = verb + prep
                                            relationships.append((subj, f"{relation} {child.text}", obj))
        
        # Strategy 2: Fallback to Co-occurrence if strict parsing yields nothing
        if not relationships:
            core_set = set(core)
            for sent in doc.sents:
                sent_chunks = {c.text.lower().strip().replace("the ", "") for c in sent.noun_chunks}
                parents = [c for c in core if c in sent_chunks]
                if not parents:
                    continue
                parent = parents[0]
                for c in supporting:
                    if c in sent_chunks and c != parent:
                        relationships.append((parent, "relates to", c))

        return classified_concepts, relationships

if __name__ == "__main__":
    extractor = ConceptExtractor()
    text = "Machine learning is a field of inquiry devoted to understanding and building methods that 'learn', that is, methods that leverage data to improve performance on some set of tasks."
    concepts, rels = extractor.extract_concepts(text)
    print("Concepts:", concepts)
    print("Relationships:", rels)
