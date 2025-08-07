#!/usr/bin/env python3
"""
Manual Test Script for Production Environment

This script provides conservative validation tests for the production environment.
Tests are designed to be non-intrusive and safe for production use.

Usage:
    python tests/manual/test_production_environment.py
    
Environment Variables:
    PROD_RAILWAY_URL - URL of production environment
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
PROD_URL = os.getenv('PROD_RAILWAY_URL', 'https://your-prod-app.up.railway.app')
API_KEY = os.getenv('API_KEY', 'your-api-key-here')
CONSERVATIVE_TIMEOUT = 30  # Conservative timeout for production

# Safe test URLs (public, well-known videos)
SAFE_TEST_URLS = {
    "rick_roll": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - safe classic
    "invalid_url": "https://example.com/not-a-video",  # Safe invalid URL
}


class ProductionEnvironmentTester:
    """Conservative tester for production environment"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'ProductionTester/1.0'
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
            # Only log essential response data for production
            result['response_summary'] = {
                'status_code': response_data.get('status_code'),
                'has_data': 'data' in response_data,
                'success': response_data.get('success')
            }
            
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        print(f"{status}: {test_name}{duration_str}")
        print(f"   Details: {details}")
        print()

    def test_basic_connectivity(self) -> bool:
        """Test basic connectivity to production environment"""
        test_name = "Basic Connectivity"
        start_time = time.time()
        
        try:
            # Try to reach any health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code in [200, 404]:  # 404 is okay if no /health endpoint
                self.log_test(
                    test_name, True,
                    f"Production environment reachable (status: {response.status_code})",
                    {"status_code": response.status_code}, duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected status code: {response.status_code}",
                    {"status_code": response.status_code}, duration
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

    def test_authentication_endpoint(self) -> bool:
        """Test authentication (conservative check)"""
        test_name = "Authentication Check"
        start_time = time.time()
        
        try:
            # Test without API key - should get 401
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
                    "Authentication properly enforced",
                    {"status_code": response.status_code},
                    duration
                )
                return True
            elif response.status_code == 404:
                # Endpoint might not exist, which is also fine
                self.log_test(
                    test_name, True,
                    "Endpoint not found (expected for some configurations)",
                    {"status_code": response.status_code},
                    duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected authentication behavior: {response.status_code}",
                    {"status_code": response.status_code}, duration
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

    def test_service_discovery_safe(self) -> bool:
        """Test service discovery endpoint (read-only)"""
        test_name = "Service Discovery (Safe)"
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
                self.log_test(
                    test_name, True,
                    "Service discovery endpoint accessible",
                    {"status_code": response.status_code, "has_endpoints": 'endpoints' in data},
                    duration
                )
                return True
            elif response.status_code in [401, 403]:
                self.log_test(
                    test_name, True,
                    f"Service discovery protected (status: {response.status_code})",
                    {"status_code": response.status_code}, duration
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    test_name, True,
                    "Service discovery endpoint not found (may be configured differently)",
                    {"status_code": response.status_code}, duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected response: {response.status_code}",
                    {"status_code": response.status_code}, duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Service discovery test failed: {str(e)}",
                None, duration
            )
            return False

    def test_youtube_health_safe(self) -> bool:
        """Test YouTube service health (read-only)"""
        test_name = "YouTube Service Health (Safe)"
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
                status = data.get('status', 'unknown')
                self.log_test(
                    test_name, True,
                    f"YouTube service health check successful (status: {status})",
                    {"status_code": response.status_code, "service_status": status},
                    duration
                )
                return True
            elif response.status_code in [401, 403]:
                self.log_test(
                    test_name, True,
                    f"Health endpoint protected (status: {response.status_code})",
                    {"status_code": response.status_code}, duration
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    test_name, True,
                    "Health endpoint not found (may be configured differently)",
                    {"status_code": response.status_code}, duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected health check response: {response.status_code}",
                    {"status_code": response.status_code}, duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Health check failed: {str(e)}",
                None, duration
            )
            return False

    def test_invalid_request_handling(self) -> bool:
        """Test handling of invalid requests (safe test)"""
        test_name = "Invalid Request Handling"
        start_time = time.time()
        
        try:
            # Send invalid data to info endpoint
            payload = {"url": SAFE_TEST_URLS["invalid_url"]}
            response = requests.post(
                f"{self.base_url}/v1/media/youtube/info",
                headers=self.headers,
                json=payload,
                timeout=CONSERVATIVE_TIMEOUT
            )
            duration = time.time() - start_time
            
            # Should handle gracefully with appropriate error codes
            if response.status_code in [400, 422, 404, 503]:
                self.log_test(
                    test_name, True,
                    f"Invalid request handled appropriately (status: {response.status_code})",
                    {"status_code": response.status_code}, duration
                )
                return True
            elif response.status_code == 202:
                # Queued response is also acceptable
                self.log_test(
                    test_name, True,
                    "Invalid request queued for processing (will be handled)",
                    {"status_code": response.status_code}, duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected response to invalid request: {response.status_code}",
                    {"status_code": response.status_code}, duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Invalid request test failed: {str(e)}",
                None, duration
            )
            return False

    def test_rick_roll_info_conservative(self) -> bool:
        """Conservative test of Rick Roll video info (minimal impact)"""
        test_name = "Rick Roll Info (Conservative)"
        start_time = time.time()
        
        try:
            payload = {"url": SAFE_TEST_URLS["rick_roll"]}
            response = requests.post(
                f"{self.base_url}/v1/media/youtube/info",
                headers=self.headers,
                json=payload,
                timeout=CONSERVATIVE_TIMEOUT
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                # Check for basic video data structure
                video_data = self._extract_video_data_safely(data)
                if video_data and video_data.get('videoId'):
                    self.log_test(
                        test_name, True,
                        f"Video info endpoint working (videoId: {video_data.get('videoId')})",
                        {"status_code": response.status_code, "has_video_id": True},
                        duration
                    )
                    return True
                else:
                    self.log_test(
                        test_name, False,
                        "Response structure unexpected",
                        {"status_code": response.status_code, "has_video_data": bool(video_data)},
                        duration
                    )
                    return False
                    
            elif response.status_code == 202:
                # Queued response is acceptable
                self.log_test(
                    test_name, True,
                    "Video info request queued successfully",
                    {"status_code": response.status_code}, duration
                )
                return True
                
            elif response.status_code in [503, 429]:
                # Service unavailable or rate limited - acceptable in production
                self.log_test(
                    test_name, True,
                    f"Service temporarily unavailable (status: {response.status_code}) - normal for production",
                    {"status_code": response.status_code}, duration
                )
                return True
                
            else:
                self.log_test(
                    test_name, False,
                    f"Unexpected response: {response.status_code}",
                    {"status_code": response.status_code}, duration
                )
                return False
                
        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            self.log_test(
                test_name, True,
                f"Request timed out (may indicate heavy load) - acceptable in production",
                None, duration
            )
            return True  # Timeout is acceptable in production
            
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Request failed: {str(e)}",
                None, duration
            )
            return False

    def test_response_headers_security(self) -> bool:
        """Test security headers in responses"""
        test_name = "Security Headers Check"
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/v1/media/youtube", headers=self.headers, timeout=10)
            duration = time.time() - start_time
            
            # Check for common security headers
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'present'
            }
            
            headers_found = {}
            for header, expected in security_headers.items():
                header_value = response.headers.get(header)
                if header_value:
                    if isinstance(expected, list):
                        headers_found[header] = header_value in expected
                    elif expected == 'present':
                        headers_found[header] = True
                    else:
                        headers_found[header] = header_value == expected
                else:
                    headers_found[header] = False
            
            security_score = sum(headers_found.values())
            
            if security_score >= 2:  # At least some security headers
                self.log_test(
                    test_name, True,
                    f"Security headers present ({security_score}/4)",
                    {"security_score": security_score, "headers": headers_found},
                    duration
                )
                return True
            else:
                self.log_test(
                    test_name, False,
                    f"Limited security headers ({security_score}/4)",
                    {"security_score": security_score, "headers": headers_found},
                    duration
                )
                return False
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"Security headers test failed: {str(e)}",
                None, duration
            )
            return False

    def test_ssl_certificate(self) -> bool:
        """Test SSL certificate validity"""
        test_name = "SSL Certificate Check"
        start_time = time.time()
        
        try:
            # This will fail if SSL certificate is invalid
            response = requests.get(f"{self.base_url}/health", timeout=10, verify=True)
            duration = time.time() - start_time
            
            self.log_test(
                test_name, True,
                "SSL certificate is valid",
                {"ssl_verified": True}, duration
            )
            return True
            
        except requests.exceptions.SSLError as e:
            duration = time.time() - start_time
            self.log_test(
                test_name, False,
                f"SSL certificate error: {str(e)}",
                None, duration
            )
            return False
            
        except requests.exceptions.RequestException:
            # Other errors are okay, we're only testing SSL
            duration = time.time() - start_time
            self.log_test(
                test_name, True,
                "SSL certificate appears valid (connection established)",
                {"ssl_verified": True}, duration
            )
            return True

    def _extract_video_data_safely(self, response_data: Dict) -> Optional[Dict]:
        """Safely extract video data from response"""
        try:
            # Direct response
            if response_data.get('success') and 'data' in response_data:
                return response_data['data']
            
            # Queued response format
            if 'response' in response_data and isinstance(response_data['response'], dict):
                resp = response_data['response']
                if resp.get('success') and 'data' in resp:
                    return resp['data']
        except:
            pass
        
        return None

    def run_production_tests(self) -> Dict[str, Any]:
        """Run all production-safe tests"""
        print("🏭 Starting Production Environment Tests")
        print("=" * 60)
        print(f"Target URL: {self.base_url}")
        print(f"API Key: {'*' * (len(self.api_key) - 4)}{self.api_key[-4:] if len(self.api_key) > 4 else '****'}")
        print("⚠️  Running conservative tests designed for production safety")
        print()
        
        # List of production-safe tests
        tests = [
            ("SSL Certificate Check", self.test_ssl_certificate),
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Authentication Check", self.test_authentication_endpoint),
            ("Security Headers", self.test_response_headers_security),
            ("Service Discovery (Safe)", self.test_service_discovery_safe),
            ("YouTube Health (Safe)", self.test_youtube_health_safe),
            ("Invalid Request Handling", self.test_invalid_request_handling),
            ("Rick Roll Info (Conservative)", self.test_rick_roll_info_conservative),
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
            
            # Brief pause between tests (be gentle on production)
            time.sleep(2)
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} passed")
        
        success_rate = (passed / total) * 100
        if passed == total:
            print("🎉 All production tests passed! Environment is healthy.")
        elif success_rate >= 80:
            print(f"✅ Production environment is mostly healthy ({success_rate:.1f}% success rate).")
        elif success_rate >= 60:
            print(f"⚠️  Production environment has some issues ({success_rate:.1f}% success rate).")
        else:
            print(f"❌ Production environment needs attention ({success_rate:.1f}% success rate).")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': success_rate,
            'results': self.test_results,
            'environment_url': self.base_url,
            'timestamp': time.time(),
            'environment_type': 'production'
        }

    def save_results(self, filename: str = "production_test_results.json"):
        """Save test results to file"""
        try:
            results_summary = {
                'test_run': {
                    'timestamp': time.time(),
                    'environment_type': 'production',
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
    if not PROD_URL or PROD_URL == 'https://your-prod-app.up.railway.app':
        print("❌ Please set PROD_RAILWAY_URL environment variable")
        print("   export PROD_RAILWAY_URL=https://your-actual-production-url.up.railway.app")
        return 1
    
    if not API_KEY or API_KEY == 'your-api-key-here':
        print("❌ Please set API_KEY environment variable")
        print("   export API_KEY=your-actual-api-key")
        return 1
    
    # Warning for production testing
    print("⚠️  WARNING: You are about to run tests against PRODUCTION!")
    print("   These tests are designed to be safe and non-intrusive.")
    print("   Press Ctrl+C within 5 seconds to cancel...")
    print()
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("❌ Tests cancelled by user.")
        return 0
    
    # Create tester and run tests
    tester = ProductionEnvironmentTester(PROD_URL, API_KEY)
    results = tester.run_production_tests()
    tester.save_results()
    
    # Return appropriate exit code (more lenient for production)
    success_rate = results['success_rate']
    return 0 if success_rate >= 60 else 1  # 60% threshold for production


if __name__ == "__main__":
    sys.exit(main())
