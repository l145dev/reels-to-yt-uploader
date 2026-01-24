import os
import sys

import pytest

# Add parent directory to path to import upload_vids
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import upload_vids


@pytest.fixture
def video_path():
    # Calculate path relative to this script file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    videos_dir = os.path.join(project_root, "tests", "videos_test")
    
    path = ""
    if os.path.exists(videos_dir):
        for f in os.listdir(videos_dir):
            if f.lower().endswith((".mp4", ".mov")):
                path = os.path.join(videos_dir, f)
                break
    
    if not os.path.exists(path):
        pytest.skip(f"Test video not found at {path}")
        
    return path

def test_generate_metadata(video_path):
    print("\n\n" + "="*60)
    print("WARNING: This test involves running the text model (gemma3:1b).")
    print("It typically takes ~20 seconds on CPU, does not use GPU acceleration.")
    print("="*60 + "\n")
    
    try:
        response = input("Do you want to run this test? (y/n): ")
    except OSError:
        pytest.skip("Skipping interactive test. Run with `pytest -s` to enable input prompt, or use standard skipping if preferred.")
        
    if response.lower() != 'y':
        pytest.skip("User opted not to run the slow test.")

    print("Starting test...")
    
    title, desc = upload_vids.generate_metadata(video_path)
    
    print(f"Title: {title}")
    print(f"Description: {desc}")
    
    assert title, "Title should not be empty"
    assert desc, "Description should not be empty"
    assert isinstance(title, str)
    assert isinstance(desc, str)
    assert "#shorts" in desc