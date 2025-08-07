#!/usr/bin/env python3
"""
Test script for YouTube microservice integration

This script tests the YouTube microservice integration endpoints
to ensure proper communication between the Flask app and Node.js microservice.

Usage:
    python tests/test_youtube_integration.py
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
FLASK_API_BASE = os.getenv('FLASK_API_BASE', 'http://localhost:8080')
YOUTUBE_SERVICE_BASE = os.getenv('YOUTUBE_SERVICE_URL', 'http://localhost:3001')
API_KEY = os.getenv('API_KEY', 'test-api-key')

# Test YouTube URL (public domain video)
TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

class YouTubeIntegrationTest:
    def __init__(self):
        self.flask_base = FLASK_API_BASE
        self.youtube_base = YOUTUBE_SERVICE_BASE
        self.api_key = API_KEY
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        self.results = []

    def log_result(self, test_name: str, success: bool, message: str, response: Dict[Any, Any] = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': time.time()
        }
        if response:
            result['response'] = response
        
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")

    def test_youtube_microservice_health(self):
        """Test YouTube microservice direct health check"""
        try:
            response = requests.get(f"{self.youtube_base}/healthz", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "YouTube Microservice Health",
                    True,
                    f"Service healthy: {data.get('service', 'unknown')} v{data.get('version', '?')}",
                    data
                )
                return True
            else:
                self.log_result(
                    "YouTube Microservice Health",
                    False,
                    f"Service returned {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_result(
                "YouTube Microservice Health",
                False,
                f"Connection failed: {str(e)}"
            )
            return False

    def test_flask_youtube_health(self):
        """Test Flask app's YouTube health endpoint"""
        try:
            response = requests.get(
                f"{self.flask_base}/v1/media/youtube/health",
                headers={'X-API-Key': self.api_key},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Flask YouTube Health Endpoint",
                    True,
                    f"Integration healthy, microservice status: {data.get('status', 'unknown')}",
                    data
                )
                return True
            else:
                self.log_result(
                    "Flask YouTube Health Endpoint",
                    False,
                    f"Endpoint returned {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_result(
                "Flask YouTube Health Endpoint",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    def test_youtube_service_discovery(self):
        """Test YouTube service discovery endpoint"""
        try:
            response = requests.get(
                f"{self.flask_base}/v1/media/youtube",
                headers={'X-API-Key': self.api_key},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get('endpoints', {})
                expected_endpoints = [
                    '/v1/media/youtube',
                    '/v1/media/youtube/health',
                    '/v1/media/youtube/info',
                    '/v1/media/youtube/mp3',
                    '/v1/media/youtube/mp4'
                ]
                
                missing_endpoints = [ep for ep in expected_endpoints if ep not in endpoints]
                if not missing_endpoints:
                    self.log_result(
                        "YouTube Service Discovery",
                        True,
                        f"All {len(expected_endpoints)} endpoints available",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "YouTube Service Discovery",
                        False,
                        f"Missing endpoints: {missing_endpoints}"
                    )
                    return False
            else:
                self.log_result(
                    "YouTube Service Discovery",
                    False,
                    f"Endpoint returned {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_result(
                "YouTube Service Discovery",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    def test_youtube_video_info(self):
        """Test YouTube video info endpoint"""
        try:
            payload = {"url": TEST_YOUTUBE_URL}
            response = requests.post(
                f"{self.flask_base}/v1/media/youtube/info",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 202:
                # Queued response, should have job_id
                data = response.json()
                job_id = data.get('job_id')
                if job_id:
                    self.log_result(
                        "YouTube Video Info (Queued)",
                        True,
                        f"Request queued successfully, job_id: {job_id}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "YouTube Video Info (Queued)",
                        False,
                        "Queued response missing job_id"
                    )
                    return False
            elif response.status_code == 200:
                # Direct response
                data = response.json()
                video_data = data.get('data', {}) if data.get('success') else data.get('response', {}).get('data', {})
                if video_data and video_data.get('videoId'):
                    self.log_result(
                        "YouTube Video Info",
                        True,
                        f"Video info retrieved: {video_data.get('title', 'Unknown Title')}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "YouTube Video Info",
                        False,
                        f"Invalid response format: {data}"
                    )
                    return False
            else:
                self.log_result(
                    "YouTube Video Info",
                    False,
                    f"Endpoint returned {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_result(
                "YouTube Video Info",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    def test_authentication(self):
        """Test that endpoints require proper authentication"""
        try:
            # Test without API key
            response = requests.get(f"{self.flask_base}/v1/media/youtube", timeout=5)
            if response.status_code == 401:
                self.log_result(
                    "Authentication Required",
                    True,
                    "Endpoints properly protected with authentication"
                )
                return True
            else:
                self.log_result(
                    "Authentication Required",
                    False,
                    f"Expected 401, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_result(
                "Authentication Required",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    def test_invalid_youtube_url(self):
        """Test handling of invalid YouTube URL"""
        try:
            payload = {"url": "https://example.com/not-a-youtube-video"}
            response = requests.post(
                f"{self.flask_base}/v1/media/youtube/info",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            # Should be queued or return error
            if response.status_code in [202, 400, 422]:
                self.log_result(
                    "Invalid YouTube URL Handling",
                    True,
                    f"Invalid URL properly handled (status: {response.status_code})"
                )
                return True
            else:
                self.log_result(
                    "Invalid YouTube URL Handling",
                    False,
                    f"Unexpected status code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_result(
                "Invalid YouTube URL Handling",
                False,
                f"Request failed: {str(e)}"
            )
            return False

    def run_all_tests(self):
        """Run all tests and return overall result"""
        print("🚀 Starting YouTube Integration Tests")
        print("=" * 50)
        
        # List of tests to run
        tests = [
            self.test_youtube_microservice_health,
            self.test_flask_youtube_health,
            self.test_authentication,
            self.test_youtube_service_discovery,
            self.test_invalid_youtube_url,
            self.test_youtube_video_info,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
            
            # Brief pause between tests
            time.sleep(0.5)
        
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed! YouTube integration is working correctly.")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Check the logs above.")
            return False

    def save_results(self, filename: str = "youtube_integration_test_results.json"):
        """Save test results to file"""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'total_tests': len(self.results),
                    'passed_tests': len([r for r in self.results if r['success']]),
                    'failed_tests': len([r for r in self.results if not r['success']]),
                    'configuration': {
                        'flask_api_base': self.flask_base,
                        'youtube_service_base': self.youtube_base,
                        'test_url': TEST_YOUTUBE_URL
                    },
                    'results': self.results
                }, f, indent=2)
            print(f"📄 Test results saved to {filename}")
        except Exception as e:
            print(f"Failed to save results: {str(e)}")

def main():
    """Main test runner"""
    print("YouTube Microservice Integration Test")
    print("=====================================")
    print(f"Flask API: {FLASK_API_BASE}")
    print(f"YouTube Service: {YOUTUBE_SERVICE_BASE}")
    print(f"API Key: {'*' * (len(API_KEY) - 4)}{API_KEY[-4:] if len(API_KEY) > 4 else '****'}")
    print()
    
    tester = YouTubeIntegrationTest()
    success = tester.run_all_tests()
    tester.save_results()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
