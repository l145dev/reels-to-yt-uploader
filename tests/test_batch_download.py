import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import unittest
from unittest.mock import patch

import batch_download_posts


class TestBatchDownload(unittest.TestCase):
    @patch('batch_download_posts.subprocess.run')
    @patch('builtins.input')
    def test_batch_install(self, mock_input, mock_subprocess):
        # Setup
        # Patch the VIDEO_FOLDER to "test_download"
        test_dir = "tests/test_download"
        with patch('batch_download_posts.VIDEO_FOLDER', test_dir):
            test_posts = ["DT1-joNjV63", "DT203fgjbDL", "DT28fs-jcY1"]
            batch_download_posts.batch_install(test_posts)

            # Verification
            self.assertEqual(mock_subprocess.call_count, 3)
            
            expected_calls = [
                unittest.mock.call(["instaloader", "--dirname-pattern=" + test_dir, "+args.txt", "--", "-DT1-joNjV63"], check=True),
                unittest.mock.call(["instaloader", "--dirname-pattern=" + test_dir, "+args.txt", "--", "-DT203fgjbDL"], check=True),
                unittest.mock.call(["instaloader", "--dirname-pattern=" + test_dir, "+args.txt", "--", "-DT28fs-jcY1"], check=True)
            ]
            
            mock_subprocess.assert_has_calls(expected_calls)

class TestBatchDownloadIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "tests/test_download"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        # Clean up directory before starting
        for f in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, f))

    def test_batch_install_real(self):
        with patch('batch_download_posts.VIDEO_FOLDER', self.test_dir):
            test_posts = ["DT1-joNjV63", "DT203fgjbDL", "DT28fs-jcY1"] 
            
            try:
                batch_download_posts.batch_install(test_posts)
            except subprocess.CalledProcessError as e:
                self.fail(f"Download failed: {e}")

            # Verify file exists
            # Check if mp4 is there
            files = os.listdir(self.test_dir)
            mp4_files = [f for f in files if f.endswith('.mp4')]
            self.assertTrue(len(mp4_files) > 0, "No .mp4 files found in download directory")

    def tearDown(self):
         # Cleanup files
         for f in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, f))

if __name__ == '__main__':
    unittest.main()
