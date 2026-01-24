import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path to import upload_vids
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import upload_vids


@patch('upload_vids.InstalledAppFlow')
@patch('upload_vids.build')
def test_get_authenticated_service(mock_build, mock_flow):
    print("\nTesting get_authenticated_service...")
    # Setup mocks
    mock_flow_instance = MagicMock()
    mock_flow.from_client_secrets_file.return_value = mock_flow_instance
    mock_flow_instance.run_local_server.return_value = "fake_creds"
    
    # Call method
    service = upload_vids.get_authenticated_service()
    
    # Assertions
    mock_flow.from_client_secrets_file.assert_called_once()
    mock_flow_instance.run_local_server.assert_called_once()
    mock_build.assert_called_once_with("youtube", "v3", credentials="fake_creds")
    print("get_authenticated_service passed.")
