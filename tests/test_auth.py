import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path to import upload_vids
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import upload_vids


@patch('upload_vids.build')
@patch('upload_vids.InstalledAppFlow')
@patch('upload_vids.Credentials')
@patch('upload_vids.os.path.exists')
def test_auth_via_token_json_success(mock_exists, mock_creds_cls, mock_flow, mock_build):
    """Test that authentication uses token.json when available."""
    print("\nTesting auth via token.json...")
    
    # Simulate token.json exists
    mock_exists.return_value = True
    
    # Simulate valid credentials
    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_creds_cls.from_authorized_user_file.return_value = mock_creds_instance
    
    # Call method
    service = upload_vids.get_authenticated_service()
    
    # Assertions
    mock_exists.assert_called_with('token.json')
    mock_creds_cls.from_authorized_user_file.assert_called_with('token.json', upload_vids.SCOPES)
    mock_flow.from_client_secrets_file.assert_not_called()
    mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds_instance)
    print("Auth via token.json passed.")

@patch('upload_vids.build')
@patch('upload_vids.InstalledAppFlow')
@patch('upload_vids.Credentials')
@patch('upload_vids.os.path.exists')
@patch('builtins.open', new_callable=MagicMock)
def test_auth_fallback_manual(mock_open, mock_exists, mock_creds_cls, mock_flow, mock_build):
    """Test fallback to manual auth when token.json is missing."""
    print("\nTesting auth fallback...")
    
    # Simulate token.json DOES NOT exist
    mock_exists.return_value = False
    
    # Setup mock flow
    mock_flow_instance = MagicMock()
    mock_flow.from_client_secrets_file.return_value = mock_flow_instance
    mock_creds_instance = MagicMock()
    mock_flow_instance.run_local_server.return_value = mock_creds_instance
    
    # Call method
    service = upload_vids.get_authenticated_service()
    
    # Assertions
    mock_exists.assert_called_with('token.json')
    mock_flow.from_client_secrets_file.assert_called_once()
    mock_flow_instance.run_local_server.assert_called_once()
    
    # Verify file write (saving token)
    mock_open.assert_called_with('token.json', 'w')
    
    mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds_instance)
    print("Auth fallback passed.")

@patch('upload_vids.build')
@patch('upload_vids.InstalledAppFlow')
@patch('upload_vids.Credentials')
@patch('upload_vids.os.path.exists')
@patch('upload_vids.Request')
@patch('builtins.open', new_callable=MagicMock)
def test_auth_refresh_token(mock_open, mock_request, mock_exists, mock_creds_cls, mock_flow, mock_build):
    """Test that token is refreshed if expired."""
    print("\nTesting token refresh...")
    
    # Simulate token.json exists
    mock_exists.return_value = True
    
    # Simulate EXPIRED but REFRESHABLE credentials
    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = False
    mock_creds_instance.expired = True
    mock_creds_instance.refresh_token = True
    mock_creds_instance.to_json.return_value = '{"fake": "json"}'
    mock_creds_cls.from_authorized_user_file.return_value = mock_creds_instance
    
    # Call method
    service = upload_vids.get_authenticated_service()
    
    # Assertions
    mock_creds_instance.refresh.assert_called_once()
    mock_flow.from_client_secrets_file.assert_not_called()
    mock_open.assert_called_with('token.json', 'w')
    mock_build.assert_called_once_with("youtube", "v3", credentials=mock_creds_instance)
    print("Token refresh passed.")
