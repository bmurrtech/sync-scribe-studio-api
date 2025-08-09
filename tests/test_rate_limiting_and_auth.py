#!/usr/bin/env python3
"""
Test script for API key authentication and rate limiting functionality.

This script tests:
1. API key authentication (valid and invalid)
2. Rate limiting (hitting the limit and getting 429 responses)
3. Endpoints accessibility with proper authentication
"""

import requests
import time
import sys
import json
from typing import Dict, Tuple, List
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"
VALID_API_KEY = "test-api-key-12345"
INVALID_API_KEY = "invalid-key-999"
RATE_LIMIT_PER_MINUTE = 10  # Should match .env configuration

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result with color coding."""
    status = f"{Colors.GREEN}✓ PASSED{Colors.RESET}" if passed else f"{Colors.RED}✗ FAILED{Colors.RESET}"
    print(f"  {test_name}: {status}")
    if details:
        print(f"    {Colors.YELLOW}{details}{Colors.RESET}")

def test_health_endpoint() -> bool:
    """Test the health endpoint (no API key required but rate limited)."""
    print_header("Testing Health Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        passed = response.status_code == 200
        print_test("Health endpoint accessible", passed, 
                  f"Status: {response.status_code}, Response: {response.json()}")
        return passed
    except Exception as e:
        print_test("Health endpoint accessible", False, f"Error: {str(e)}")
        return False

def test_authentication() -> bool:
    """Test API key authentication."""
    print_header("Testing API Key Authentication")
    
    all_passed = True
    
    # Test 1: No API key
    print("\n  Testing without API key:")
    try:
        response = requests.get(f"{BASE_URL}/v1/toolkit/authenticate")
        passed = response.status_code == 401
        print_test("    Rejected without API key", passed, 
                  f"Status: {response.status_code}")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("    Rejected without API key", False, f"Error: {str(e)}")
        all_passed = False
    
    # Test 2: Invalid API key
    print("\n  Testing with invalid API key:")
    try:
        headers = {"X-API-Key": INVALID_API_KEY}
        response = requests.get(f"{BASE_URL}/v1/toolkit/authenticate", headers=headers)
        passed = response.status_code == 401
        print_test("    Rejected with invalid API key", passed, 
                  f"Status: {response.status_code}")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("    Rejected with invalid API key", False, f"Error: {str(e)}")
        all_passed = False
    
    # Test 3: Valid API key
    print("\n  Testing with valid API key:")
    try:
        headers = {"X-API-Key": VALID_API_KEY}
        response = requests.get(f"{BASE_URL}/v1/toolkit/authenticate", headers=headers)
        passed = response.status_code == 200
        print_test("    Accepted with valid API key", passed, 
                  f"Status: {response.status_code}, Response: {response.json()}")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("    Accepted with valid API key", False, f"Error: {str(e)}")
        all_passed = False
    
    return all_passed

def test_rate_limiting() -> bool:
    """Test rate limiting functionality."""
    print_header("Testing Rate Limiting")
    
    all_passed = True
    
    # Test rate limiting on health endpoint (doesn't require API key)
    endpoint = "/health"
    print(f"\n  Testing rate limit on {endpoint} (limit: {RATE_LIMIT_PER_MINUTE} requests/minute):")
    
    results = []
    start_time = time.time()
    
    # Make requests up to and beyond the rate limit
    for i in range(RATE_LIMIT_PER_MINUTE + 5):
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            results.append({
                'request_num': i + 1,
                'status_code': response.status_code,
                'timestamp': time.time() - start_time
            })
            
            # Small delay to make the test more realistic
            time.sleep(0.1)
            
        except Exception as e:
            results.append({
                'request_num': i + 1,
                'error': str(e),
                'timestamp': time.time() - start_time
            })
    
    # Analyze results
    successful_requests = [r for r in results if r.get('status_code') == 200]
    rate_limited_requests = [r for r in results if r.get('status_code') == 429]
    
    print(f"\n    Successful requests (200): {len(successful_requests)}")
    print(f"    Rate limited requests (429): {len(rate_limited_requests)}")
    
    # Test that we get rate limited after the limit
    passed_limit = len(successful_requests) <= RATE_LIMIT_PER_MINUTE
    print_test("    Rate limit enforced", passed_limit,
              f"Got {len(successful_requests)} successful requests (limit: {RATE_LIMIT_PER_MINUTE})")
    all_passed = all_passed and passed_limit
    
    # Test that we get 429 responses when rate limited
    passed_429 = len(rate_limited_requests) > 0
    print_test("    Returns 429 when rate limited", passed_429,
              f"Got {len(rate_limited_requests)} 429 responses")
    all_passed = all_passed and passed_429
    
    # Print detailed results for debugging
    if rate_limited_requests:
        print(f"\n    First 429 response at request #{rate_limited_requests[0]['request_num']}")
    
    return all_passed

def test_endpoints_with_auth() -> List[Tuple[str, bool]]:
    """Test various endpoints with proper authentication."""
    print_header("Testing Endpoints with Authentication")
    
    endpoints = [
        "/v1/toolkit/authenticate",
        "/health",  # Health doesn't require auth but should still work
    ]
    
    results = []
    headers = {"X-API-Key": VALID_API_KEY}
    
    for endpoint in endpoints:
        try:
            # For health endpoint, we don't need API key
            if endpoint == "/health":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            
            passed = response.status_code in [200, 202]
            print_test(f"  {endpoint}", passed, 
                      f"Status: {response.status_code}")
            results.append((endpoint, passed))
        except Exception as e:
            print_test(f"  {endpoint}", False, f"Error: {str(e)}")
            results.append((endpoint, False))
    
    return results

def manual_curl_tests():
    """Print manual curl commands for testing."""
    print_header("Manual cURL Test Commands")
    
    print("You can also test manually using these curl commands:\n")
    
    print(f"{Colors.BOLD}1. Test without API key (should return 401):{Colors.RESET}")
    print(f"   curl -X GET {BASE_URL}/v1/toolkit/authenticate\n")
    
    print(f"{Colors.BOLD}2. Test with invalid API key (should return 401):{Colors.RESET}")
    print(f"   curl -X GET {BASE_URL}/v1/toolkit/authenticate \\")
    print(f"        -H 'X-API-Key: invalid-key'\n")
    
    print(f"{Colors.BOLD}3. Test with valid API key (should return 200):{Colors.RESET}")
    print(f"   curl -X GET {BASE_URL}/v1/toolkit/authenticate \\")
    print(f"        -H 'X-API-Key: {VALID_API_KEY}'\n")
    
    print(f"{Colors.BOLD}4. Test rate limiting (run multiple times quickly):{Colors.RESET}")
    print(f"   for i in {{1..15}}; do")
    print(f"     curl -X GET {BASE_URL}/health")
    print(f"     echo \"Request $i completed\"")
    print(f"   done\n")

def main():
    """Run all tests."""
    print_header("API Security Test Suite")
    print(f"Testing API at: {BASE_URL}")
    print(f"Valid API Key: {VALID_API_KEY}")
    print(f"Rate Limit: {RATE_LIMIT_PER_MINUTE} requests/minute\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}ERROR: Cannot connect to API at {BASE_URL}{Colors.RESET}")
        print(f"{Colors.YELLOW}Please ensure the API server is running:{Colors.RESET}")
        print(f"  python app.py")
        sys.exit(1)
    
    # Run tests
    test_results = {
        "Health Endpoint": test_health_endpoint(),
        "Authentication": test_authentication(),
        "Rate Limiting": test_rate_limiting(),
    }
    
    # Test endpoints
    endpoint_results = test_endpoints_with_auth()
    
    # Print summary
    print_header("Test Summary")
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"Core Tests: {passed_tests}/{total_tests} passed")
    for test_name, passed in test_results.items():
        status = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
        print(f"  {status} {test_name}")
    
    print(f"\nEndpoint Tests: {sum(1 for _, p in endpoint_results if p)}/{len(endpoint_results)} passed")
    
    # Print manual test commands
    manual_curl_tests()
    
    # Exit code based on test results
    all_passed = all(test_results.values()) and all(p for _, p in endpoint_results)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
