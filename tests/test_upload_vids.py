import datetime
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path to import upload_vids
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import upload_vids


@pytest.fixture
def test_video_path():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    videos_test_dir = os.path.join(project_root, "videos_test")
    
    # Ensure videos_test exists
    if not os.path.exists(videos_test_dir):
        os.makedirs(videos_test_dir)
        
    # Find a video file
    for f in os.listdir(videos_test_dir):
        if f.endswith(('.mp4', '.mov')):
            return os.path.join(videos_test_dir, f)
            
    return None

@patch('upload_vids.generate_metadata')
@patch('upload_vids.MediaFileUpload')
def test_upload_video(mock_media_file, mock_metadata, test_video_path):
    print("\nTesting upload_video...")
    
    if not test_video_path:
        pytest.skip("No video found in videos_test directory to test upload_video")
        
    # Mock metadata generation
    mock_metadata.return_value = ("Test Title", "Test Description #shorts")
    
    # Mock Youtube service
    mock_youtube = MagicMock()
    mock_request = MagicMock()
    mock_youtube.videos().insert.return_value = mock_request
    mock_request.execute.return_value = {"id": "12345"}
    
    # Date time for upload
    schedule_time = datetime.datetime(2026, 1, 24, 12, 0, 0)
    
    # Call method
    response = upload_vids.upload_video(mock_youtube, test_video_path, schedule_time)
    
    # Assertions
    mock_metadata.assert_called_once_with(test_video_path)
    mock_youtube.videos().insert.assert_called_once()
    
    # Check args passed to insert
    _, kwargs = mock_youtube.videos().insert.call_args
    assert kwargs['part'] == "snippet,status"
    assert kwargs['body']['snippet']['title'] == "Test Title"
    assert kwargs['body']['status']['privacyStatus'] == "private"
    assert kwargs['body']['status']['publishAt'] == "2026-01-24T12:00:00Z"
    
    mock_request.execute.assert_called_once()
    
    print("upload_video passed.")
