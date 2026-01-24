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
    videos_dir = os.path.join(project_root, "videos_test")
    
    path = ""
    if os.path.exists(videos_dir):
        for f in os.listdir(videos_dir):
            if f.lower().endswith((".mp4", ".mov")):
                path = os.path.join(videos_dir, f)
                break
    
    if not os.path.exists(path):
        pytest.skip(f"Test video not found in {videos_dir}")
        
    return path

def test_get_transcript(video_path):
    print("\n\n" + "="*60)
    print("Testing get_transcript with Whisper (CPU).")
    print("This might download the model if not present.")
    print("="*60 + "\n")

    transcript = upload_vids.get_transcript(video_path)
    
    print(f"\nTranscript result: {transcript}\n")
    
    assert transcript is not None
    assert isinstance(transcript, str)
