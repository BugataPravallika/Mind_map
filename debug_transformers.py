try:
    import transformers
    print(f"Transformers version: {transformers.__version__}")
    print(f"Transformers file: {transformers.__file__}")
    
    try:
        from transformers import pipeline
        print("Successfully imported pipeline from transformers")
    except ImportError as e:
        print(f"Error importing pipeline: {e}")
        
    print("Contents of transformers module:")
    print(dir(transformers))
    
except Exception as e:
    print(f"General Error: {e}")
