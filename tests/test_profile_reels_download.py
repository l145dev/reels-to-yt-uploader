import os
import sys
import unittest
from unittest.mock import patch

# Ensure we can import the module from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import profile_reels_download


class TestProfileReelsDownload(unittest.TestCase):
    @patch('profile_reels_download.subprocess.run')
    @patch('builtins.input')
    def test_download_profile_reels(self, mock_input, mock_subprocess):
        # Setup
        test_dir = "tests/test_download"
        profile_name = "explainingeverythingsimply"
        
        # Patch the VIDEO_FOLDER to use the test directory
        with patch('profile_reels_download.VIDEO_FOLDER', test_dir):
            profile_reels_download.download_profile_reels(profile_name)

            # Verification: Verify the command matches exactly what the script uses
            expected_call = [
                "instaloader", 
                profile_name, 
                "--reels", 
                "+args.txt", 
                "--dirname-pattern=" + test_dir
            ]
            
            mock_subprocess.assert_called_with(expected_call, check=True)

# disabled due to rate limit issues
# class TestProfileReelsDownloadIntegration(unittest.TestCase):
#     def setUp(self):
#         self.test_dir = "tests/test_download"
#         if not os.path.exists(self.test_dir):
#             os.makedirs(self.test_dir)
#         # Clean up directory before starting
#         for f in os.listdir(self.test_dir):
#             try:
#                 os.remove(os.path.join(self.test_dir, f))
#             except OSError:
#                 pass

#     def test_download_profile_reels_real(self):
#         # Patch the VIDEO_FOLDER to "tests/test_download"
#         # We verify real download functionality
#         with patch('profile_reels_download.VIDEO_FOLDER', self.test_dir):
#             # Using the known profile that works: explainingeverythingsimply
#             profile_name = "explainingeverythingsimply"
            
#             try:
#                 profile_reels_download.download_profile_reels(profile_name)
#             except subprocess.CalledProcessError as e:
#                 self.fail(f"Download failed: {e}")

#             # Verify file exists
#             files = os.listdir(self.test_dir)
#             mp4_files = [f for f in files if f.endswith('.mp4')]
#             self.assertTrue(len(mp4_files) > 0, "No .mp4 files found in download directory")

#     def tearDown(self):
#          # Cleanup files
#          for f in os.listdir(self.test_dir):
#             try:
#                 os.remove(os.path.join(self.test_dir, f))
#             except OSError:
#                 pass

if __name__ == '__main__':
    unittest.main()
