#!/usr/bin/env python3
"""
Manual Test Script for Staging Environment

This script provides manual validation tests for the staging environment,
including Rick Roll video download functionality.

Usage:
    python tests/manual/test_staging_environment.py
    
Environment Variables:
    STAGING_RAILWAY_URL - URL of staging environment
    API_KEY - API key for authentication
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
STAGING_URL = os.getenv('STAGING_RAILWAY_URL', 'https://your-app.up.railway.app')
API_KEY = os.getenv('API_KEY', 'your-api-key-here')
YOUTUBE_SERVICE_TIMEOUT = 60  # 1 minute timeout for YouTube operations

# Test URLs
RICK_ROLL_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
TEST_URLS = {
    "rick_roll": RICK_ROLL_URL,
    "valid_video": "https://www.youtube.com/watch?v=9bZkp7q19f0",  # PSY - GANGNAM STYLE
    "invalid_url": "https://example.com/not-a-video",
    "non_existent": "https://www.youtube.com/watch?v=ThisVideoDoesNotExist123",
}


class StagingEnvironmentTester:
    """Manual tester for staging environment"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'StagingTester/1.0'
        }
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str, 
                response_data: Optional[Dict] = None, duration: Optional[float] = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': time.time(),
            'duration': duration
        }
        if response_data:
            result['response'] = response_data
            
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        print(f"{status}: {test_name}{duration_str}")
        print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()

    def test_environment_health(self) -> bool:
        """Test basic environment health"""
        test_name = "Environment Health Check"
        start_time = time.time()
        
        try:
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    test_name, True,
                    f"Environment is healthy (status: {response.status_code})",
                    data, duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected status code: {response.status_code}",
                    {"status_code": response.status_code, "text": response.text}, duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Connection failed: {str(e)}",
                None, duration
            )
            return False

    def test_youtube_service_health(self) -> bool:
        """Test YouTube microservice health"""
        test_name = "YouTube Service Health"
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/v1/media/youtube/health",
                headers=self.headers,
                timeout=15
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test(
                        test_name, True,
                        f"YouTube service is healthy",
                        data, duration
                    )
                    return True
                else:
                    self.log_test(
                        test_name, False,
                        f"YouTube service unhealthy: {data.get('status')}",
                        data, duration
                    )
                    return False
            else:
                self.log_test(
                    test_name, False,
                    f"Health check failed: {response.status_code}",
                    {"status_code": response.status_code}, duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Health check request failed: {str(e)}",
                None, duration
            )
            return False

    def test_rick_roll_video_info(self) -> bool:
        """Test Rick Roll video info retrieval"""
        test_name = "Rick Roll Video Info"
        start_time = time.time()
        
        try:
            payload = {"url": RICK_ROLL_URL}
            response = requests.post(
                f"{self.base_url}/v1/media/youtube/info",
                headers=self.headers,
                json=payload,
                timeout=YOUTUBE_SERVICE_TIMEOUT
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                # Handle both direct and queued responses
                video_data = self._extract_video_data(data)
                
                if video_data and video_data.get('videoId') == 'dQw4w9WgXcQ':
                    self.log_test(
                        test_name, True,
                        f"Rick Roll video info retrieved: '{video_data.get('title', 'Unknown')}'",
                        {"videoId": video_data.get('videoId'), "title": video_data.get('title')},
                        duration
                    )
                    return True
                else:
                    self.log_test(
                        test_name, False,
                        "Invalid video data or wrong video ID",
                        data, duration
                    )
                    return False
                    
            elif response.status_code == 202:
                # Queued response
                data = response.json()
                job_id = data.get('job_id')
                self.log_test(
                    test_name, True,
                    f"Rick Roll video info request queued (job_id: {job_id})",
                    data, duration
                )
                return True
                
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected response: {response.status_code}",
                    {"status_code": response.status_code, "text": response.text[:200]},
                    duration
                )
                return False
                
        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Request timed out after {YOUTUBE_SERVICE_TIMEOUT}s",
                None, duration
            )
            return False
            
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Request failed: {str(e)}",
                None, duration
            )
            return False

    def test_rick_roll_mp3_download(self) -> bool:
        """Test Rick Roll MP3 download (streaming)"""
        test_name = "Rick Roll MP3 Download"
        start_time = time.time()
        
        try:
            payload = {
                "url": RICK_ROLL_URL,
                "quality": "highestaudio"
            }
            
            # Use stream=True for download test
            response = requests.post(
                f"{self.base_url}/v1/media/youtube/mp3",
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=YOUTUBE_SERVICE_TIMEOUT
            )
            
            if response.status_code == 200:
                # Check headers
                content_type = response.headers.get('content-type', '')
                video_title = response.headers.get('x-video-title', '')
                
                # Read a small amount of data to verify stream works
                chunk_count = 0
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        total_size += len(chunk)
                        chunk_count += 1
                        # Stop after a few chunks to avoid full download
                        if chunk_count >= 10:
                            break
                
                duration = time.time() - start_time
                
                if 'audio' in content_type and total_size > 0:
                    self.log_test(
                        test_name, True,
                        f"MP3 stream started successfully (content-type: {content_type}, "
                        f"title: {video_title}, {total_size} bytes received)",
                        {"content_type": content_type, "video_title": video_title, "bytes_received": total_size},
                        duration
                    )
                    return True
                else:
                    self.log_test(
                        test_name, False,
                        f"Invalid stream (content-type: {content_type}, size: {total_size})",
                        {"content_type": content_type, "size": total_size},
                        duration
                    )
                    return False
                    
            else:
                duration = time.time() - start_time
                try:
                    error_data = response.json()
                except:
                    error_data = {"text": response.text[:200]}
                
                self.log_test(
                    test_name, False,
                    f"Download failed: {response.status_code}",
                    error_data, duration
                )
                return False
                
        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Download timed out after {YOUTUBE_SERVICE_TIMEOUT}s",
                None, duration
            )
            return False
            
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Download request failed: {str(e)}",
                None, duration
            )
            return False

    def test_authentication(self) -> bool:
        """Test authentication requirements"""
        test_name = "Authentication Test"
        start_time = time.time()
        
        try:
            # Test without API key
            headers_no_auth = {'Content-Type': 'application/json'}
            response = requests.get(
                f"{self.base_url}/v1/media/youtube",
                headers=headers_no_auth,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test(
                    test_name, True,
                    "Authentication properly enforced (401 without API key)",
                    {"status_code": response.status_code},
                    duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Expected 401, got {response.status_code}",
                    {"status_code": response.status_code, "text": response.text[:200]},
                    duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Authentication test failed: {str(e)}",
                None, duration
            )
            return False

    def test_invalid_url_handling(self) -> bool:
        """Test handling of invalid URLs"""
        test_name = "Invalid URL Handling"
        start_time = time.time()
        
        try:
            payload = {"url": TEST_URLS["invalid_url"]}
            response = requests.post(
                f"{self.base_url}/v1/media/youtube/info",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            duration = time.time() - start_time
            
            # Should either reject immediately (4xx) or queue and handle gracefully (202)
            if response.status_code in [400, 422, 202]:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                self.log_test(
                    test_name, True,
                    f"Invalid URL properly handled (status: {response.status_code})",
                    {"status_code": response.status_code}, duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected response to invalid URL: {response.status_code}",
                    {"status_code": response.status_code}, duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Invalid URL test failed: {str(e)}",
                None, duration
            )
            return False

    def test_service_discovery(self) -> bool:
        """Test service discovery endpoint"""
        test_name = "Service Discovery"
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/v1/media/youtube",
                headers=self.headers,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                expected_endpoints = [
                    '/v1/media/youtube/health',
                    '/v1/media/youtube/info',
                    '/v1/media/youtube/mp3',
                    '/v1/media/youtube/mp4'
                ]
                
                endpoints = data.get('endpoints', {})
                missing = [ep for ep in expected_endpoints if ep not in endpoints]
                
                if not missing:
                    self.log_test(
                        test_name, True,
                        f"All expected endpoints available",
                        {"endpoints": list(endpoints.keys())}, duration
                    )
                    return True
                else:
                    self.log_test(
                        test_name, False,
                        f"Missing endpoints: {missing}",
                        {"available": list(endpoints.keys()), "missing": missing}, duration
                    )
                    return False
            else:
                self.log_test(
                    test_name, False,
                    f"Service discovery failed: {response.status_code}",
                    {"status_code": response.status_code}, duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Service discovery failed: {str(e)}",
                None, duration
            )
            return False

    def _extract_video_data(self, response_data: Dict) -> Optional[Dict]:
        """Extract video data from various response formats"""
        # Direct response
        if response_data.get('success') and 'data' in response_data:
            return response_data['data']
        
        # Queued response format
        if 'response' in response_data and isinstance(response_data['response'], dict):
            resp = response_data['response']
            if resp.get('success') and 'data' in resp:
                return resp['data']
        
        return None

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all staging environment tests"""
        print("🚀 Starting Staging Environment Tests")
        print("=" * 60)
        print(f"Target URL: {self.base_url}")
        print(f"API Key: {'*' * (len(self.api_key) - 4)}{self.api_key[-4:] if len(self.api_key) > 4 else '****'}")
        print()
        
        # List of tests to run
        tests = [
            ("Environment Health", self.test_environment_health),
            ("YouTube Service Health", self.test_youtube_service_health),
            ("Authentication", self.test_authentication),
            ("Service Discovery", self.test_service_discovery),
            ("Invalid URL Handling", self.test_invalid_url_handling),
            ("Rick Roll Video Info", self.test_rick_roll_video_info),
            ("Rick Roll MP3 Download", self.test_rick_roll_mp3_download),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ Test '{test_name}' crashed: {str(e)}")
                logger.exception(f"Test {test_name} crashed")
            
            # Brief pause between tests
            time.sleep(1)
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} passed")
        
        success_rate = (passed / total) * 100
        if passed == total:
            print("🎉 All tests passed! Staging environment is working correctly.")
        elif success_rate >= 70:
            print(f"⚠️  {total - passed} test(s) failed. Environment mostly functional ({success_rate:.1f}%).")
        else:
            print(f"❌ {total - passed} test(s) failed. Environment needs attention ({success_rate:.1f}%).")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results,
            'environment_url': self.base_url,
            'timestamp': time.time()
        }

    def save_results(self, filename: str = "staging_test_results.json"):
        """Save test results to file"""
        try:
            results_summary = {
                'test_run': {
                    'timestamp': time.time(),
                    'environment_url': self.base_url,
                    'total_tests': len(self.test_results),
                    'passed_tests': len([r for r in self.test_results if r['success']]),
                    'failed_tests': len([r for r in self.test_results if not r['success']]),
                },
                'results': self.test_results
            }
            
            with open(filename, 'w') as f:
                json.dump(results_summary, f, indent=2)
            
            print(f"📄 Test results saved to {filename}")
            
        except Exception as e:
            print(f"Failed to save results: {str(e)}")


def main():
    """Main test runner"""
    # Validate environment variables
    if not STAGING_URL or STAGING_URL == 'https://your-app.up.railway.app':
        print("❌ Please set STAGING_RAILWAY_URL environment variable")
        print("   export STAGING_RAILWAY_URL=https://your-actual-staging-url.up.railway.app")
        return 1
    
    if not API_KEY or API_KEY == 'your-api-key-here':
        print("❌ Please set API_KEY environment variable")
        print("   export API_KEY=your-actual-api-key")
        return 1
    
    # Create tester and run tests
    tester = StagingEnvironmentTester(STAGING_URL, API_KEY)
    results = tester.run_all_tests()
    tester.save_results()
    
    # Return appropriate exit code
    return 0 if results['passed_tests'] == results['total_tests'] else 1


if __name__ == "__main__":
    sys.exit(main())
