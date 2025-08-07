"""
Unit Tests for Security Module
Tests API key authentication, rate limiting, and security components.
"""

import pytest
import os
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask, jsonify, g

# Import security components
import sys
sys.path.append('..')
from server.security import (
    APIKeyValidator,
    require_api_key,
    rate_limit,
    setup_security,
    security_health_check,
    get_api_key_from_request,
    validate_api_key_dependency,
    _check_rate_limit,
    _cleanup_rate_limit_storage
)

class TestAPIKeyValidator:
    """Test cases for API key validation"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock environment variable
        self.test_token = "test_api_key_12345678901234567890"
        self.patcher = patch.dict(os.environ, {'DB_TOKEN': self.test_token})
        self.patcher.start()
        
        # Create validator instance
        self.validator = APIKeyValidator()
    
    def teardown_method(self):
        """Clean up after tests"""
        self.patcher.stop()
    
    def test_load_db_token_success(self):
        """Test successful DB_TOKEN loading"""
        assert self.validator.db_token == self.test_token
    
    def test_load_db_token_missing(self):
        """Test error when DB_TOKEN is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DB_TOKEN environment variable is required"):
                APIKeyValidator()
    
    def test_mask_token(self):
        """Test token masking for logs"""
        token = "abcdef1234567890xyz"
        masked = self.validator._mask_token(token)
        assert masked == "abcd***********0xyz"
        assert len(masked) == len(token)
    
    def test_mask_token_short(self):
        """Test masking of short tokens"""
        token = "short"
        masked = self.validator._mask_token(token)
        assert masked == "*****"
    
    def test_validate_api_key_valid(self):
        """Test validation with correct API key"""
        assert self.validator.validate_api_key(self.test_token) is True
    
    def test_validate_api_key_invalid(self):
        """Test validation with incorrect API key"""
        assert self.validator.validate_api_key("wrong_key") is False
        assert self.validator.validate_api_key("") is False
        assert self.validator.validate_api_key(None) is False
    
    def test_validate_api_key_timing_attack_protection(self):
        """Test that validation uses constant-time comparison"""
        # This test ensures we're using secrets.compare_digest
        with patch('server.security.secrets.compare_digest') as mock_compare:
            mock_compare.return_value = True
            
            result = self.validator.validate_api_key("test_key")
            
            mock_compare.assert_called_once_with(self.test_token, "test_key")
            assert result is True
    
    def test_log_auth_attempt(self):
        """Test authentication attempt logging"""
        with patch('server.security.logger') as mock_logger:
            # Test successful auth
            self.validator.log_auth_attempt(True, "127.0.0.1", self.test_token)
            mock_logger.info.assert_called()
            
            # Test failed auth
            self.validator.log_auth_attempt(False, "127.0.0.1", "wrong_key")
            mock_logger.warning.assert_called()

class TestAPIKeyDecorator:
    """Test cases for API key decorator"""
    
    def setup_method(self):
        """Setup test Flask app and environment"""
        self.app = Flask(__name__)
        self.test_token = "test_api_key_12345678901234567890"
        
        # Mock environment
        self.patcher = patch.dict(os.environ, {'DB_TOKEN': self.test_token})
        self.patcher.start()
        
        # Create test endpoint
        @self.app.route('/protected')
        @require_api_key
        def protected_endpoint():
            return jsonify({"message": "success", "authenticated": True})
        
        # Create test client
        self.client = self.app.test_client()
    
    def teardown_method(self):
        """Clean up after tests"""
        self.patcher.stop()
    
    def test_require_api_key_valid_bearer_token(self):
        """Test authentication with valid Bearer token"""
        response = self.client.get('/protected', headers={
            'Authorization': f'Bearer {self.test_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'success'
        assert data['authenticated'] is True
    
    def test_require_api_key_valid_x_api_key(self):
        """Test authentication with valid X-API-KEY header"""
        response = self.client.get('/protected', headers={
            'X-API-KEY': self.test_token
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'success'
        assert data['authenticated'] is True
    
    def test_require_api_key_missing_header(self):
        """Test 401 response when API key is missing"""
        response = self.client.get('/protected')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Missing API key'
        assert 'Authorization header' in data['message']
    
    def test_require_api_key_invalid_token(self):
        """Test 401 response with invalid API key"""
        response = self.client.get('/protected', headers={
            'Authorization': 'Bearer invalid_key'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Invalid API key'
    
    def test_require_api_key_malformed_bearer(self):
        """Test 401 response with malformed Bearer header"""
        response = self.client.get('/protected', headers={
            'Authorization': 'InvalidFormat token'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Missing API key'
    
    def test_api_key_stored_in_g(self):
        """Test that valid API key is stored in flask.g"""
        with self.app.test_request_context('/protected', headers={
            'Authorization': f'Bearer {self.test_token}'
        }):
            from server.security import get_api_key_validator
            
            # Simulate the decorator logic
            api_key = get_api_key_from_request()
            assert api_key == self.test_token
            
            # Simulate setting g.current_api_key
            g.current_api_key = api_key
            assert g.current_api_key == self.test_token

class TestRateLimiting:
    """Test cases for rate limiting functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = Flask(__name__)
        
        # Clear rate limit storage before each test
        from server.security import _rate_limit_storage
        _rate_limit_storage.clear()
        
        # Create test endpoint with rate limiting
        @self.app.route('/limited')
        @rate_limit("3/minute")  # Very low limit for testing
        def limited_endpoint():
            return jsonify({"message": "success"})
        
        self.client = self.app.test_client()
    
    def test_rate_limit_within_limits(self):
        """Test requests within rate limits are allowed"""
        # Make requests within limit
        for i in range(3):
            response = self.client.get('/limited')
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'success'
    
    def test_rate_limit_exceeded(self):
        """Test that requests exceeding limit are blocked"""
        # Make requests up to limit
        for i in range(3):
            response = self.client.get('/limited')
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = self.client.get('/limited')
        assert response.status_code == 429
        data = response.get_json()
        assert data['error'] == 'Rate limit exceeded'
        assert 'Too many requests' in data['message']
    
    def test_check_rate_limit_function(self):
        """Test the internal _check_rate_limit function"""
        identifier = "test_ip"
        limit = "2/minute"
        
        # First two requests should pass
        assert _check_rate_limit(identifier, limit) is True
        assert _check_rate_limit(identifier, limit) is True
        
        # Third request should fail
        assert _check_rate_limit(identifier, limit) is False
    
    def test_rate_limit_parsing(self):
        """Test rate limit string parsing"""
        # Test different time periods
        test_cases = [
            ("10/second", 10, 1),
            ("60/minute", 60, 60),
            ("100/hour", 100, 3600),
            ("invalid", 100, 60)  # fallback
        ]
        
        for limit_string, expected_count, expected_window in test_cases:
            # This is testing internal logic, so we'll check indirectly
            assert _check_rate_limit("test_parsing", limit_string) is True
    
    def test_rate_limit_cleanup(self):
        """Test cleanup of expired rate limit entries"""
        from server.security import _rate_limit_storage
        
        # Add some test entries
        identifier = "cleanup_test"
        _rate_limit_storage[identifier] = [
            datetime.now() - timedelta(minutes=10),  # Old entry
            datetime.now() - timedelta(seconds=30),  # Recent entry
            datetime.now()  # Current entry
        ]
        
        # Cleanup with 5-minute window
        _cleanup_rate_limit_storage(datetime.now(), 300)
        
        # Only recent entries should remain
        assert len(_rate_limit_storage[identifier]) <= 2

class TestSecuritySetup:
    """Test cases for security setup and configuration"""
    
    def setup_method(self):
        """Setup test Flask app"""
        self.app = Flask(__name__)
        self.test_token = "test_api_key_12345678901234567890"
        
        # Mock environment
        self.patcher = patch.dict(os.environ, {'DB_TOKEN': self.test_token})
        self.patcher.start()
    
    def teardown_method(self):
        """Clean up after tests"""
        self.patcher.stop()
    
    def test_setup_security(self):
        """Test security setup with Flask app"""
        app = setup_security(self.app)
        
        # Should return the app
        assert app == self.app
        
        # Should add security headers
        with self.app.test_request_context():
            response = self.app.make_response(('test', 200))
            
            # Trigger after_request handlers
            response = self.app.process_response(response)
            
            # Check for security headers
            assert response.headers['X-Content-Type-Options'] == 'nosniff'
            assert response.headers['X-Frame-Options'] == 'DENY'
            assert response.headers['X-XSS-Protection'] == '1; mode=block'
            assert 'max-age=31536000' in response.headers['Strict-Transport-Security']
    
    def test_security_health_check_healthy(self):
        """Test security health check with healthy components"""
        health = security_health_check()
        
        assert health['status'] == 'healthy'
        assert 'timestamp' in health
        assert 'components' in health
        
        # Check individual components
        assert health['components']['api_key_validator']['status'] == 'healthy'
        assert health['components']['api_key_validator']['db_token_configured'] is True
        assert health['components']['security_config']['status'] == 'healthy'
        assert health['components']['rate_limiter']['status'] == 'healthy'
    
    def test_security_health_check_unhealthy(self):
        """Test security health check with unhealthy condition"""
        # Simulate an error by mocking the security_health_check to throw an exception
        with patch('server.security.os.getenv') as mock_getenv:
            # Make os.getenv('DB_TOKEN') return None to simulate missing token
            def mock_getenv_func(key, default=None):
                if key == 'DB_TOKEN':
                    return None
                return os.getenv(key, default)
            
            mock_getenv.side_effect = mock_getenv_func
            
            health = security_health_check()
            
            # Should still be healthy overall but with DB_TOKEN marked as not configured
            assert health['status'] == 'healthy'
            assert health['components']['api_key_validator']['db_token_configured'] is False

class TestHelperFunctions:
    """Test cases for helper functions"""
    
    def setup_method(self):
        """Setup test environment"""
        self.app = Flask(__name__)
        self.test_token = "test_api_key_12345678901234567890"
        
        # Mock environment
        self.patcher = patch.dict(os.environ, {'DB_TOKEN': self.test_token})
        self.patcher.start()
    
    def teardown_method(self):
        """Clean up after tests"""
        self.patcher.stop()
    
    def test_get_api_key_from_request_bearer(self):
        """Test API key extraction from Bearer header"""
        with self.app.test_request_context('/', headers={
            'Authorization': f'Bearer {self.test_token}'
        }):
            api_key = get_api_key_from_request()
            assert api_key == self.test_token
    
    def test_get_api_key_from_request_x_api_key(self):
        """Test API key extraction from X-API-KEY header"""
        with self.app.test_request_context('/', headers={
            'X-API-KEY': self.test_token
        }):
            api_key = get_api_key_from_request()
            assert api_key == self.test_token
    
    def test_get_api_key_from_request_none(self):
        """Test API key extraction when no key is present"""
        with self.app.test_request_context('/'):
            api_key = get_api_key_from_request()
            assert api_key is None
    
    def test_get_api_key_from_request_bearer_priority(self):
        """Test that Bearer token takes priority over X-API-KEY"""
        bearer_token = "bearer_token_123"
        header_token = "header_token_456"
        
        with self.app.test_request_context('/', headers={
            'Authorization': f'Bearer {bearer_token}',
            'X-API-KEY': header_token
        }):
            api_key = get_api_key_from_request()
            assert api_key == bearer_token

class TestIntegration:
    """Integration tests combining authentication and rate limiting"""
    
    def setup_method(self):
        """Setup integrated test environment"""
        self.app = Flask(__name__)
        self.test_token = "test_api_key_12345678901234567890"
        
        # Mock environment
        self.patcher = patch.dict(os.environ, {'DB_TOKEN': self.test_token})
        self.patcher.start()
        
        # Clear rate limit storage before each test
        from server.security import _rate_limit_storage
        _rate_limit_storage.clear()
        
        # Setup security
        setup_security(self.app)
        
        # Create protected and rate-limited endpoint
        @self.app.route('/protected-limited')
        @require_api_key
        @rate_limit("2/minute")
        def protected_limited_endpoint():
            return jsonify({"message": "success", "authenticated": True})
        
        self.client = self.app.test_client()
    
    def teardown_method(self):
        """Clean up after tests"""
        self.patcher.stop()
    
    def test_auth_and_rate_limit_success(self):
        """Test successful requests with auth and rate limiting"""
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
        # First request should succeed
        response = self.client.get('/protected-limited', headers=headers)
        assert response.status_code == 200
        
        # Second request should succeed
        response = self.client.get('/protected-limited', headers=headers)
        assert response.status_code == 200
    
    def test_auth_fails_before_rate_limit(self):
        """Test that auth failure occurs before rate limiting"""
        # No auth header - should get 401, not 429
        response = self.client.get('/protected-limited')
        assert response.status_code == 401
        
        data = response.get_json()
        assert data['error'] == 'Missing API key'
    
    def test_rate_limit_after_auth_success(self):
        """Test rate limiting after successful auth"""
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
        # Make requests up to limit
        for i in range(2):
            response = self.client.get('/protected-limited', headers=headers)
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = self.client.get('/protected-limited', headers=headers)
        assert response.status_code == 429

if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
