import networkx as nx
from typing import List, Dict, Tuple
import torch

class GraphBuilder:
    """
    Builds a NetworkX graph from extracted concepts and relationships.
    Includes "Cognitive Load Control" via:
    - Semantic node merging (using embeddings)
    - Dynamic pruning based on complexity level
    """

    def __init__(self, use_embeddings: bool = True):
        self.graph = nx.DiGraph()
        self.use_embeddings = use_embeddings
        self.embedder = None
        if self.use_embeddings:
            # Lazy load to avoid startup cost if not strictly needed immediately
            pass

    def _get_embedder(self):
        if self.embedder is None:
            try:
                print("Loading SentenceTransformer for semantic merging...")
                from sentence_transformers import SentenceTransformer
                # Use a tiny, fast model
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                print("SentenceTransformer not found. Skipping semantic merging.")
                self.use_embeddings = False
        return self.embedder

    @staticmethod
    def _concept_text(c) -> str:
        if isinstance(c, str):
            return c
        if isinstance(c, dict):
            return str(c.get("text", "")).strip()
        return str(c).strip()

    @staticmethod
    def _rank(group: str) -> int:
        # Higher = more important
        return {"core": 3, "supporting": 2, "example": 1}.get(group or "", 0)

    def build_graph(
        self, 
        concepts: Dict, 
        relationships: List[Tuple[str, str, str]], 
        complexity: str = "Medium"
    ) -> nx.DiGraph:
        """
        Constructs a study-friendly graph with Cognitive Load Control.
        
        Complexity Levels:
        - Low: Aggressive merging, max 3 children, focus on Core.
        - Medium: Balanced, max 5 children.
        - High: Detailed, max 8 children.
        """
        self.graph.clear()
        
        # 1. Configuration based on Complexity
        if complexity == "Low":
            max_children = 3
            merge_threshold = 0.65  # Merge aggressively
        elif complexity == "High":
            max_children = 8
            merge_threshold = 0.85  # Merge only very similar
        else: # Medium
            max_children = 5
            merge_threshold = 0.75

        # 2. Extract texts
        core_list = [self._concept_text(c) for c in concepts.get("core_ideas", [])]
        supporting_list = [self._concept_text(c) for c in concepts.get("supporting_ideas", [])]
        examples_list = [self._concept_text(c) for c in concepts.get("examples", [])]

        all_nodes = []
        for c in core_list: all_nodes.append({"text": c, "group": "core", "priority": 3})
        for c in supporting_list: all_nodes.append({"text": c, "group": "supporting", "priority": 2})
        for c in examples_list: all_nodes.append({"text": c, "group": "example", "priority": 1})

        # 3. Semantic Merging (Deduplication)
        # We want to merge "Solar power" (supporting) into "Solar Energy" (core) if similar.
        final_nodes = []
        
        embedder = self._get_embedder()
        
        if self.use_embeddings and embedder and all_nodes:
            # Sort by priority so we keep the "Core" term as the canon
            all_nodes.sort(key=lambda x: x["priority"], reverse=True)
            
            kept_nodes = []
            embeddings = embedder.encode([n["text"] for n in all_nodes])
            
            from sentence_transformers import util
            
            # Simple greedy clustering
            # For each node, check if it merges into an already kept node
            for i, node in enumerate(all_nodes):
                is_merged = False
                if kept_nodes:
                    # Check similarity against all kept nodes
                    # Optimization: In a huge graph this is O(N^2), but N is small (<50) usually
                    current_emb = embeddings[i]
                    kept_embs = embedder.encode([n["text"] for n in kept_nodes]) # Re-encoding is inefficient but simple for now
                    
                    scores = util.cos_sim(current_emb, kept_embs)[0]
                    best_score_idx = torch.argmax(scores).item()
                    best_score = scores[best_score_idx].item()
                    
                    if best_score > merge_threshold:
                        # Merge!
                        target = kept_nodes[best_score_idx]
                        print(f"Merging '{node['text']}' -> '{target['text']}' (Score: {best_score:.2f})")
                        is_merged = True
                
                if not is_merged:
                    kept_nodes.append(node)
                    
            final_nodes = kept_nodes
        else:
            final_nodes = all_nodes

        # 4. Build Graph Structure
        if not final_nodes:
             return self.graph

        # Center Node
        center_candidates = [n for n in final_nodes if n["group"] == "core"]
        center_text = center_candidates[0]["text"] if center_candidates else "Study Map"
        
        self.graph.add_node(center_text, group="core", title="Main Idea", size=40, color="#FF6B6B")
        
        node_lookup = {n["text"]: n for n in final_nodes}

        # Add Nodes
        for n in final_nodes:
            if n["text"] == center_text: continue
            
            # Styling - Pastel Palette
            # Core: Pastel Pink/Red
            # Supporting: Pastel Blue/Purple
            # Example: Pastel Green
            color = "#FCD5CE" if n["group"] == "core" else ("#A2D2FF" if n["group"] == "supporting" else "#D4E5A9")
            
            # Larger fonts for readability
            size = 40 if n["group"] == "core" else (28 if n["group"] == "supporting" else 20)
            
            self.graph.add_node(n["text"], group=n["group"], title=n["group"].title(), size=size, color=color, shape="box", font={'multi': 'html'})

        # 5. Add and Filter Edges
        # Only add edges if both start/end exist in our merged list
        # (Need to remap relationships if terms were merged... strictly speaking we should, 
        # but for now we assume distinctness or precise string match from extractor)
        
        valid_names = set(n["text"] for n in final_nodes)
        
        # Add implicit Code->Center edges
        for n in final_nodes:
            if n["group"] == "core" and n["text"] != center_text:
                self.graph.add_edge(center_text, n["text"])

        # Add Explicit Relationships
        for parent, relation, child in relationships:
            if parent in valid_names and child in valid_names:
                if parent != child:
                    self.graph.add_edge(parent, child, title=relation, label=relation)

        # 6. Tree Enforcement (Single Parent)
        for node in list(self.graph.nodes()):
            if node == center_text: continue
            parents = list(self.graph.predecessors(node))
            if len(parents) > 1:
                # Keep parent with highest priority group
                best_p = max(parents, key=lambda p: self._rank(self.graph.nodes[p].get("group", "")))
                for p in parents:
                    if p != best_p:
                        self.graph.remove_edge(p, node)

        # 7. Cognitive Load Pruning (Child Limits)
        for parent in list(self.graph.nodes()):
            children = list(self.graph.successors(parent))
            if len(children) <= max_children:
                continue
                
            # Keep highest priority children
            def child_score(c):
                # Priority > OutDegree (hubs) > Length (shorter is better)
                prio = self._rank(self.graph.nodes[c].get("group", ""))
                return (prio, -len(c)) 
            
            keep = sorted(children, key=child_score, reverse=True)[:max_children]
            drop = [c for c in children if c not in set(keep)]
            
            for c in drop:
                self.graph.remove_edge(parent, c)
                # If child becomes orphan, remove it (unless it's core)
                if self.graph.in_degree(c) == 0 and self.graph.nodes[c].get("group") != "core":
                     self.graph.remove_node(c)

        return self.graph

if __name__ == "__main__":
    builder = GraphBuilder()
    concepts = {
        "core_ideas": ["Machine Learning"],
        "supporting_ideas": ["Methods", "Data"],
        "details": ["Tasks", "Performance"]
    }
    rels = [("Machine Learning", "Methods"), ("Methods", "Data")]
    G = builder.build_graph(concepts, rels)
    print("Nodes:", G.nodes(data=True))
    print("Edges:", G.edges())
