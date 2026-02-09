import os
import time
from typing import List, Dict
from src.modules.input_handler import InputHandler
from src.modules.text_cleaner import TextCleaner
from src.modules.simplifier import ContentSimplifier
from src.modules.concept_extractor import ConceptExtractor
from src.modules.graph_builder import GraphBuilder
from src.modules.visualizer import Visualizer
from src.modules.study_planner import StudyPlanner
from src.modules.voice_generator import VoiceGenerator
from src.modules.language_service import LanguageService
from src.modules.topic_clusterer import TopicClusterer
from src.modules.quiz_generator import QuizGenerator

class StudyMapPipeline:
    """
    Orchestrates the entire AI Study Map pipeline.
    """

    def __init__(self, output_dir: str = "data/output", prefer_offline: bool = False, model_name: str = "google/flan-t5-small"):
        self.output_dir = output_dir
        self.prefer_offline = prefer_offline
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        print(f"Initializing Pipeline with model: {model_name}...")
        self.input_handler = InputHandler()
        self.text_cleaner = TextCleaner()
        self.simplifier = ContentSimplifier(model_name=model_name) # T5
        self.extractor = ConceptExtractor() # spaCy
        self.topic_clusterer = TopicClusterer(max_topics=6)
        self.graph_builder = GraphBuilder()
        self.visualizer = Visualizer(output_dir)
        self.planner = StudyPlanner()
        self.voice_generator = VoiceGenerator()
        self.language_service = LanguageService(prefer_offline=self.prefer_offline)
        self.quiz_generator = QuizGenerator()
        print("Pipeline Initialized.")

    def run(
        self,
        file_paths: List[str],
        target_lang: str = "en",
        available_time_mins: int = 60,
        generate_audio: bool = True,
        complexity: str = "Medium",
    ):
        """
        Runs the pipeline on given files.
        """
        results = {}
        
        # 1. Input Processing
        print("\n--- Step 1: Input Processing ---")
        raw_text = self.input_handler.process_files(file_paths)
        if not raw_text:
            print("No text extracted. Aborting.")
            return None

        # 1b. Language detection + pivot to English
        print("\n--- Step 1b: Language Detection + Pivot to English ---")
        lang_result = self.language_service.pivot_to_english(raw_text)
        results["detected_language"] = lang_result.detected
        pivot_text = lang_result.pivot_text_en
            
        # 2. Text Preprocessing
        print("\n--- Step 2: Text Preprocessing ---")
        cleaned_text = self.text_cleaner.clean_text(pivot_text)
        chunks = self.text_cleaner.segment_text(cleaned_text)
        print(f"Text segmented into {len(chunks)} chunks.")
        results["chunk_count"] = len(chunks)
        
        # 3. Multi-document topic clustering + simplification
        print("\n--- Step 3: Topic Clustering + Student-Friendly Simplification ---")
        topic_clusters = self.topic_clusterer.cluster(chunks)
        from concurrent.futures import ThreadPoolExecutor
        
        def process_topic(tc):
            merged = "\n\n".join(tc.chunks)
            title = " / ".join(tc.top_terms[:3]).strip() if tc.top_terms else tc.topic_id.replace("_", " ").title()
            
            # These calls are now thread-safe due to internal Lazy Loading
            summary = self.simplifier.summarize_topic(merged)
            priority = self.simplifier.predict_importance(summary)
            
            return {
                "topic_id": tc.topic_id,
                "title": title,
                "priority": priority,
                "summary": summary,
                "source_chunks": list(tc.chunk_indices),
                "top_terms": tc.top_terms,
                "estimated_words": len(merged.split()),
            }

        with ThreadPoolExecutor(max_workers=3) as executor:
            topics_out = list(executor.map(process_topic, topic_clusters))

        # Sort back to original order if needed, but here cluster order is fine
        topics_out.sort(key=lambda x: x['topic_id'])

        # Unified simplified text for display + downstream processing
        simplified_text = "\n\n".join([f"{t['title']}\n{t['summary']}" for t in topics_out]).strip()
        results["topics"] = topics_out
        results["simplified_text"] = simplified_text
        
        # 4. Structured Map Generation
        print("\n--- Step 4: Map Structuring ---")
        structured_map = self.simplifier.generate_structured_map(simplified_text)
        
        # 5b. Quiz Generation (From Structure)
        print("\n--- Step 5b: Smart Quiz Generation ---")
        quiz = self.quiz_generator.generate_quiz_from_structure(structured_map)
        results['quiz'] = quiz

        # 5. Static Diagram Generation (Unified Sheet)
        print("\n--- Step 5: Static Diagram Generation ---")
        map_path = self.visualizer.generate_static_diagram(structured_map, quiz, "study_map.html")
        results['map_path'] = map_path
        
        # 6. Study Planning
        print("\n--- Step 6: Study Planning ---")
        # concepts is currently unused by the planner, but we pass an empty dict to satisfy signature
        plan = self.planner.create_plan(simplified_text, available_time_mins, {}, topics=results.get("topics"))
        results['study_plan'] = plan
        
        # 7. Voice Generation
        if generate_audio:
            print("\n--- Step 7: Voice Generation ---")
            audio_path = os.path.join(self.output_dir, "summary_audio.wav")
            # Generate audio for the first ~1000 chars as a preview
            self.voice_generator.generate_audio(simplified_text[:1000], audio_path)
            results['audio_path'] = audio_path
        
        # 8. Translation (if needed): English -> target
        if target_lang != "en":
            print(f"\n--- Step 8: Translation to {target_lang} ---")
            translated_text = self.language_service.translate_from_english(simplified_text, target_lang)
            results["translated_text"] = translated_text
            
        print("\nPipeline Complete!")
        return results

if __name__ == "__main__":
    # Test stub
    # pipeline = StudyMapPipeline()
    # pipeline.run(["test.pdf"])
    pass
