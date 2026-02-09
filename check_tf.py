
import sys
try:
    import transformers
    print(f"Transformers path: {transformers.__file__}")
    print(f"Transformers version: {transformers.__version__}")
    
    if hasattr(transformers, 'pipeline'):
        print("transformers.pipeline FOUND")
    else:
        print("transformers.pipeline NOT found")
        
    try:
        from transformers import pipeline
        print("Import 'from transformers import pipeline' SUCCESS")
    except ImportError as e:
        print(f"Import 'from transformers import pipeline' FAILED: {e}")

    try:
        from transformers.pipelines import pipeline
        print("Import 'from transformers.pipelines import pipeline' SUCCESS")
    except ImportError as e:
        print(f"Import 'from transformers.pipelines import pipeline' FAILED: {e}")

except ImportError as e:
    print(f"Failed to import transformers: {e}")
