import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from ai_study_mapper.src.pipeline import StudyMapPipeline

def test():
    # Create dummy file if not exists
    test_file = "test_content.txt"
    with open(test_file, "w") as f:
        f.write("Photosynthesis is a process used by plants to convert light energy into chemical energy. " * 20)
    
    pipeline = StudyMapPipeline(output_dir="data/test_output")
    try:
        results = pipeline.run(
            file_paths=[test_file],
            target_lang="en",
            available_time_mins=60,
            generate_audio=False
        )
        if results:
            print("Pipeline Success!")
            print("Map Path:", results.get("map_path"))
            print("Quiz Count:", len(results.get("quiz", [])))
            print("Summary Length:", len(results.get("simplified_text", "")))
    except Exception as e:
        print(f"Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test()
