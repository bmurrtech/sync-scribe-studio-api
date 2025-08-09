#!/usr/bin/env python3
"""
Unit tests for security.py module.

Tests API key authentication and rate limiting functionality.
"""

import unittest
import time
from unittest.mock import MagicMock, patch
import os
import sys

# Add parent directory to path to import security module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security import require_api_key, rate_limit, _get_client_ip, _get_rate_limit_key


class TestAPIKeyAuthentication(unittest.TestCase):
    """Test API key authentication decorator."""

    @patch('security.request')
    def test_require_api_key_missing_server_config(self, mock_request):
        """Test when API_KEY env var is not set."""
        mock_request.headers = {'X-API-Key': 'test-key'}
        
        # Temporarily remove API_KEY from environment
        original_api_key = os.environ.get('API_KEY')
        if 'API_KEY' in os.environ:
            del os.environ['API_KEY']
        
        @require_api_key
        def test_func():
            return "success", 200
        
        result = test_func()
        self.assertEqual(result[1], 500)
        self.assertIn("Server misconfiguration", str(result[0]))
        
        # Restore API_KEY
        if original_api_key:
            os.environ['API_KEY'] = original_api_key

    @patch('security.request')
    def test_require_api_key_invalid(self, mock_request):
        """Test with invalid API key."""
        mock_request.headers = {'X-API-Key': 'wrong-key'}
        os.environ['API_KEY'] = 'correct-key'
        
        @require_api_key
        def test_func():
            return "success", 200
        
        result = test_func()
        self.assertEqual(result[1], 401)
        self.assertIn("Unauthorized", str(result[0]))

    @patch('security.request')
    def test_require_api_key_valid(self, mock_request):
        """Test with valid API key."""
        mock_request.headers = {'X-API-Key': 'correct-key'}
        os.environ['API_KEY'] = 'correct-key'
        
        @require_api_key
        def test_func():
            return "success", 200
        
        result = test_func()
        self.assertEqual(result, ("success", 200))

    @patch('security.request')
    def test_require_api_key_missing_header(self, mock_request):
        """Test when X-API-Key header is missing."""
        mock_request.headers = {}
        os.environ['API_KEY'] = 'correct-key'
        
        @require_api_key
        def test_func():
            return "success", 200
        
        result = test_func()
        self.assertEqual(result[1], 401)


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality."""

    def setUp(self):
        """Clear rate limit buckets before each test."""
        import security
        security._rate_buckets.clear()

    @patch('security.request')
    @patch('security.time.time')
    def test_rate_limit_allows_requests_under_limit(self, mock_time, mock_request):
        """Test that requests under the limit are allowed."""
        mock_request.remote_addr = '127.0.0.1'
        mock_request.headers = {}
        mock_time.return_value = 1000.0
        
        @rate_limit(max_per_minute=5)
        def test_func():
            return "success", 200
        
        # Make 5 requests (should all succeed)
        for i in range(5):
            result = test_func()
            self.assertEqual(result, ("success", 200))

    @patch('security.request')
    @patch('security.time.time')
    def test_rate_limit_blocks_excess_requests(self, mock_time, mock_request):
        """Test that requests over the limit are blocked."""
        mock_request.remote_addr = '127.0.0.1'
        mock_request.headers = {}
        mock_time.return_value = 1000.0
        
        @rate_limit(max_per_minute=3)
        def test_func():
            return "success", 200
        
        # Make 3 requests (should succeed)
        for i in range(3):
            result = test_func()
            self.assertEqual(result, ("success", 200))
        
        # 4th request should be blocked
        result = test_func()
        self.assertEqual(result[1], 429)
        self.assertIn("Too Many Requests", str(result[0]))

    @patch('security.request')
    @patch('security.time.time')
    def test_rate_limit_window_sliding(self, mock_time, mock_request):
        """Test that the rate limit window slides over time."""
        mock_request.remote_addr = '127.0.0.1'
        mock_request.headers = {}
        
        @rate_limit(max_per_minute=2)
        def test_func():
            return "success", 200
        
        # Make 2 requests at t=1000
        mock_time.return_value = 1000.0
        for i in range(2):
            result = test_func()
            self.assertEqual(result, ("success", 200))
        
        # 3rd request at t=1000 should be blocked
        result = test_func()
        self.assertEqual(result[1], 429)
        
        # After 61 seconds, should be able to make new requests
        mock_time.return_value = 1061.0
        result = test_func()
        self.assertEqual(result, ("success", 200))

    @patch('security.request')
    def test_rate_limit_by_ip(self, mock_request):
        """Test rate limiting by IP address."""
        import security
        security._rate_buckets.clear()
        
        # Set to rate limit by IP
        os.environ['RATE_LIMIT_KEY'] = 'ip'
        
        @rate_limit(max_per_minute=1)
        def test_func():
            return "success", 200
        
        # Request from IP 1
        mock_request.remote_addr = '192.168.1.1'
        mock_request.headers = {}
        result = test_func()
        self.assertEqual(result, ("success", 200))
        
        # Second request from IP 1 should be blocked
        result = test_func()
        self.assertEqual(result[1], 429)
        
        # Request from IP 2 should succeed
        mock_request.remote_addr = '192.168.1.2'
        result = test_func()
        self.assertEqual(result, ("success", 200))


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""

    @patch('security.request')
    def test_get_client_ip_from_x_forwarded_for(self, mock_request):
        """Test getting client IP from X-Forwarded-For header."""
        from security import _get_client_ip
        
        mock_request.headers = {'X-Forwarded-For': '203.0.113.1, 198.51.100.1'}
        mock_request.remote_addr = '10.0.0.1'
        
        ip = _get_client_ip(mock_request)
        self.assertEqual(ip, '203.0.113.1')

    @patch('security.request')
    def test_get_client_ip_from_remote_addr(self, mock_request):
        """Test getting client IP from remote_addr when X-Forwarded-For is absent."""
        from security import _get_client_ip
        
        mock_request.headers = {}
        mock_request.remote_addr = '192.168.1.100'
        
        ip = _get_client_ip(mock_request)
        self.assertEqual(ip, '192.168.1.100')

    @patch('security.request')
    def test_get_rate_limit_key_by_ip(self, mock_request):
        """Test getting rate limit key by IP."""
        from security import _get_rate_limit_key
        
        os.environ['RATE_LIMIT_KEY'] = 'ip'
        mock_request.headers = {}
        mock_request.remote_addr = '192.168.1.1'
        
        key = _get_rate_limit_key(mock_request)
        self.assertEqual(key, 'ip:192.168.1.1')

    @patch('security.request')
    def test_get_rate_limit_key_by_api_key(self, mock_request):
        """Test getting rate limit key by API key."""
        from security import _get_rate_limit_key
        
        os.environ['RATE_LIMIT_KEY'] = 'api_key'
        mock_request.headers = {'X-API-Key': 'test-api-123'}
        mock_request.remote_addr = '192.168.1.1'
        
        key = _get_rate_limit_key(mock_request)
        self.assertEqual(key, 'api_key:test-api-123')


if __name__ == '__main__':
    # Set up test environment
    os.environ['API_KEY'] = 'test-api-key'
    os.environ['RATE_LIMIT_PER_MINUTE'] = '10'
    os.environ['RATE_LIMIT_BURST'] = '15'
    os.environ['RATE_LIMIT_KEY'] = 'ip'
    
    # Run tests
    unittest.main(verbosity=2)
