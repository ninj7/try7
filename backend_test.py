import requests
import unittest
import sys
import json

class YouTubeDownloaderAPITest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://0d03ad82-15f6-4388-8b64-aec816c9e37f.preview.emergentagent.com/api"
        self.valid_youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
        self.invalid_youtube_url = "https://www.youtube.com/invalid_url"
        self.non_youtube_url = "https://www.example.com"

    def test_01_root_endpoint(self):
        """Test the root API endpoint"""
        print("\n🔍 Testing root endpoint...")
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "YouTube Downloader API")
        print("✅ Root endpoint test passed")

    def test_02_video_info_valid_url(self):
        """Test video info extraction with a valid YouTube URL"""
        print("\n🔍 Testing video info with valid URL...")
        response = requests.post(
            f"{self.base_url}/video-info",
            json={"url": self.valid_youtube_url}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify required fields are present
        self.assertIn("title", data)
        self.assertIn("formats", data)
        self.assertIn("url", data)
        
        # Verify optional fields (may be None but should exist)
        self.assertIn("thumbnail", data)
        self.assertIn("duration", data)
        self.assertIn("uploader", data)
        self.assertIn("view_count", data)
        
        # Verify formats structure
        self.assertGreater(len(data["formats"]), 0)
        first_format = data["formats"][0]
        self.assertIn("format_id", first_format)
        self.assertIn("ext", first_format)
        self.assertIn("quality", first_format)
        
        print("✅ Video info with valid URL test passed")
        return data

    def test_03_video_info_invalid_url(self):
        """Test video info extraction with an invalid YouTube URL"""
        print("\n🔍 Testing video info with invalid URL...")
        response = requests.post(
            f"{self.base_url}/video-info",
            json={"url": self.invalid_youtube_url}
        )
        self.assertGreaterEqual(response.status_code, 400)
        print("✅ Video info with invalid URL test passed")

    def test_04_video_info_non_youtube_url(self):
        """Test video info extraction with a non-YouTube URL"""
        print("\n🔍 Testing video info with non-YouTube URL...")
        response = requests.post(
            f"{self.base_url}/video-info",
            json={"url": self.non_youtube_url}
        )
        self.assertGreaterEqual(response.status_code, 400)
        print("✅ Video info with non-YouTube URL test passed")

    def test_05_download_endpoint(self):
        """Test the download endpoint (partial test - we don't download the full file)"""
        print("\n🔍 Testing download endpoint...")
        
        # First get video info to get a valid format_id
        video_info = self.test_02_video_info_valid_url()
        if not video_info or not video_info.get("formats"):
            self.fail("Could not get video formats for testing download")
        
        format_id = video_info["formats"][0]["format_id"]
        
        # Test download endpoint with HEAD request to avoid downloading the full file
        response = requests.post(
            f"{self.base_url}/download",
            json={"url": self.valid_youtube_url, "format_id": format_id},
            stream=True
        )
        
        # Close the connection after headers are received
        response.close()
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Disposition', response.headers)
        self.assertIn('Content-Length', response.headers)
        print("✅ Download endpoint test passed")

    def test_06_download_invalid_format(self):
        """Test download with invalid format_id"""
        print("\n🔍 Testing download with invalid format_id...")
        response = requests.post(
            f"{self.base_url}/download",
            json={"url": self.valid_youtube_url, "format_id": "invalid_format_id"}
        )
        self.assertGreaterEqual(response.status_code, 400)
        print("✅ Download with invalid format test passed")

def run_tests():
    """Run all tests and return success status"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(YouTubeDownloaderAPITest('test_01_root_endpoint'))
    test_suite.addTest(YouTubeDownloaderAPITest('test_02_video_info_valid_url'))
    test_suite.addTest(YouTubeDownloaderAPITest('test_03_video_info_invalid_url'))
    test_suite.addTest(YouTubeDownloaderAPITest('test_04_video_info_non_youtube_url'))
    test_suite.addTest(YouTubeDownloaderAPITest('test_05_download_endpoint'))
    test_suite.addTest(YouTubeDownloaderAPITest('test_06_download_invalid_format'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)