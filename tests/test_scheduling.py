import datetime
import json
import os
import sys
from unittest.mock import mock_open, patch

# Add parent directory to path to import upload_vids
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import upload_vids


def test_get_next_schedule_time():
    print("\nTesting get_next_schedule_time...")
    
    # Define a fake datetime class to control .now()
    real_datetime = datetime.datetime
    class FakeDatetime(real_datetime):
        @classmethod
        def now(cls):
            return real_datetime(2026, 1, 24, 10, 0, 0)

    # Case 1: No state file (starts from today)
    with patch('upload_vids.os.path.exists', return_value=False):
        with patch('upload_vids.datetime') as mock_dt_mod:
            mock_dt_mod.datetime = FakeDatetime
            mock_dt_mod.timedelta = datetime.timedelta
            
            next_time = upload_vids.get_next_schedule_time()
            
            # Should be today at 12:00
            expected = datetime.datetime(2026, 1, 24, 12, 0, 0)
            assert next_time == expected

    # Case 2: State file exists
    with patch('upload_vids.os.path.exists', return_value=True):
        with patch('upload_vids.datetime') as mock_dt_mod:
            mock_dt_mod.datetime = FakeDatetime
            mock_dt_mod.timedelta = datetime.timedelta
            
            # Mock reading the file
            mock_state = {'last_scheduled_date': '2026-01-24T12:00:00'}
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_state))):
                 next_time = upload_vids.get_next_schedule_time()
                 
                 # Should be next day at 12:00
                 expected = datetime.datetime(2026, 1, 25, 12, 0, 0)
                 assert next_time == expected
    print("get_next_schedule_time passed.")
