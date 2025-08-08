#!/usr/bin/env python3
"""
Unit Tests for Application Boot Without Environment Variables

Following TDD principles - these tests validate that the application can start
and serve basic endpoints even when critical environment variables are missing.

Tests cover:
1. App initialization without API_KEY, OPENAI_API_KEY, DB_TOKEN
2. Health endpoints accessibility
3. Graceful degradation of functionality
4. Proper warning/error handling
"""

import pytest
import os
import sys
from unittest.mock import patch, Mock
from flask import Flask

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


class TestAppBootWithoutSecrets:
    """Test application boot without critical environment variables"""
    
    @pytest.fixture
    def clean_env(self):
        """Clean environment with no sensitive variables"""
        with patch.dict(os.environ, {}, clear=True):
            # Set only minimal required environment variables
            with patch.dict(os.environ, {
                'PORT': '8080',
                'FLASK_ENV': 'testing'
            }):
                yield

    @pytest.fixture
    def partial_env(self):
        """Environment with only some variables missing"""
        with patch.dict(os.environ, {
            'PORT': '8080',
            'FLASK_ENV': 'testing',
            'API_KEY': 'test_api_key_123456',
            # DB_TOKEN and OPENAI_API_KEY are missing
        }, clear=True):
            yield

    def test_app_imports_without_secrets(self, clean_env):
        """Test that the app can be imported without environment variables"""
        try:
            from app import create_app
            assert create_app is not None
        except Exception as e:
            pytest.fail(f"App import failed without secrets: {e}")

    def test_app_creates_without_secrets(self, clean_env):
        """Test that Flask app can be created without environment variables"""
        try:
            from app import create_app
            app = create_app()
            assert app is not None
            assert isinstance(app, Flask)
        except Exception as e:
            pytest.fail(f"App creation failed without secrets: {e}")

    def test_config_loads_without_api_key(self, clean_env):
        """Test that config module loads gracefully without API_KEY"""
        try:
            import config
            # Should warn but not crash
            assert config.API_KEY is None or config.API_KEY == ""
        except Exception as e:
            pytest.fail(f"Config loading failed without API_KEY: {e}")

    def test_security_module_loads_without_db_token(self, clean_env):
        """Test that security module loads gracefully without DB_TOKEN"""
        try:
            from server import security
            # Should be able to create validator with auto_error=False
            validator = security.APIKeyValidator(auto_error=False)
            assert validator.db_token is None
        except Exception as e:
            pytest.fail(f"Security module loading failed without DB_TOKEN: {e}")

    def test_security_utils_loads_without_secrets(self, clean_env):
        """Test that security_utils loads gracefully without secrets"""
        try:
            import security_utils
            # Should create secret manager without requiring secrets
            manager = security_utils.SecretManager(require_secrets=False)
            assert manager is not None
        except Exception as e:
            pytest.fail(f"Security utils loading failed without secrets: {e}")

    def test_health_endpoints_work_without_secrets(self, clean_env):
        """Test that health endpoints work even without secrets"""
        try:
            from app import create_app
            
            app = create_app()
            # Don't register health endpoints again since they're already registered by create_app
            
            with app.test_client() as client:
                # Test basic health endpoint
                response = client.get('/health')
                assert response.status_code == 200
                
                # Test detailed health endpoint  
                response = client.get('/health/detailed')
                # Should return 200 or 503 (degraded but not crashed)
                assert response.status_code in [200, 503]
                
                # Test root endpoint
                response = client.get('/')
                assert response.status_code == 200
                
        except Exception as e:
            pytest.fail(f"Health endpoints failed without secrets: {e}")

    def test_security_health_check_without_db_token(self, clean_env):
        """Test security health check works without DB_TOKEN"""
        try:
            from server.security import security_health_check
            
            health = security_health_check()
            assert health is not None
            assert 'status' in health
            assert 'components' in health
            
            # Should indicate DB_TOKEN is not configured
            api_validator_status = health['components']['api_key_validator']
            assert api_validator_status['db_token_configured'] is False
            
        except Exception as e:
            pytest.fail(f"Security health check failed without DB_TOKEN: {e}")

    def test_environment_health_check_shows_degraded(self, clean_env):
        """Test environment health check shows degraded status when vars missing"""
        try:
            from server.health import check_environment_variables
            
            env_status = check_environment_variables()
            assert env_status is not None
            assert env_status['status'] == 'degraded'
            assert 'missing_recommended' in env_status
            
            # Should list missing variables
            missing = env_status['missing_recommended']
            expected_missing = ['X_API_KEY', 'API_KEY', 'DB_TOKEN', 'OPENAI_API_KEY']
            for var in expected_missing:
                assert var in missing
                
        except Exception as e:
            pytest.fail(f"Environment health check failed: {e}")

    def test_api_key_validation_graceful_failure(self, clean_env):
        """Test API key validation fails gracefully without DB_TOKEN"""
        try:
            from server.security import APIKeyValidator
            
            # Create validator with auto_error=False
            validator = APIKeyValidator(auto_error=False)
            
            # Should return False for any key when DB_TOKEN is missing
            result = validator.validate_api_key("test_key")
            assert result is False
            
            # Should not raise exception
            assert validator.db_token is None
            
        except Exception as e:
            pytest.fail(f"API key validation failed to handle missing DB_TOKEN: {e}")

    def test_require_api_key_decorator_without_token(self, clean_env):
        """Test @require_api_key decorator behavior without DB_TOKEN"""
        try:
            from server.security import require_api_key
            from flask import Flask, jsonify
            
            app = Flask(__name__)
            
            # Test with auto_error=False 
            @app.route('/test_no_error')
            @require_api_key(auto_error=False)
            def test_endpoint_no_error():
                return jsonify({"message": "success"})
            
            with app.test_client() as client:
                response = client.get('/test_no_error')
                # Should not return 503 or crash, might return 401 or allow through
                assert response.status_code != 500
                
        except Exception as e:
            pytest.fail(f"require_api_key decorator failed without DB_TOKEN: {e}")

    def test_partial_functionality_with_some_secrets(self, partial_env):
        """Test app works with some but not all secrets"""
        try:
            from app import create_app
            
            app = create_app()
            # Don't register health endpoints again since they're already registered by create_app
            
            with app.test_client() as client:
                # Health endpoints should work
                response = client.get('/health')
                assert response.status_code == 200
                
                # Some degradation expected but not complete failure
                response = client.get('/health/detailed')
                assert response.status_code in [200, 503]
                
        except Exception as e:
            pytest.fail(f"Partial functionality test failed: {e}")

    def test_logging_works_without_secrets(self, clean_env):
        """Test that logging doesn't crash without secrets"""
        try:
            from server.security import logger
            from security_utils import logger as security_logger
            
            # Should be able to log without crashing
            logger.warning("Test log message")
            security_logger.warning("Test security log message")
            
            # No assertion needed - just testing it doesn't crash
            
        except Exception as e:
            pytest.fail(f"Logging failed without secrets: {e}")


class TestGracefulDegradation:
    """Test graceful degradation of features without secrets"""
    
    @pytest.fixture
    def clean_env(self):
        """Clean environment with no sensitive variables"""
        with patch.dict(os.environ, {}, clear=True):
            yield

    def test_authentication_returns_503_without_config(self, clean_env):
        """Test authentication returns 503 when not configured"""
        try:
            from app import create_app
            from flask import Flask
            
            # Create a minimal Flask app with the authentication route
            app = create_app()
            
            with app.test_client() as client:
                # Test the authenticate endpoint
                response = client.get('/authenticate')
                
                # Should return 503 (service unavailable) when API_KEY is not configured
                assert response.status_code == 503
                
                if response.get_json():
                    data = response.get_json()
                    assert "Authentication unavailable" in str(data)
                
        except Exception as e:
            pytest.fail(f"Authentication endpoint failed without API_KEY: {e}")

    def test_secret_manager_warns_about_missing_secrets(self, clean_env):
        """Test secret manager logs warnings about missing secrets"""
        try:
            with patch('security_utils.logger') as mock_logger:
                from security_utils import SecretManager
                
                # Create without requiring secrets
                manager = SecretManager(require_secrets=False)
                
                # Should have called warning about missing secrets
                mock_logger.warning.assert_called()
                
                # Warning should mention missing variables
                warning_call = mock_logger.warning.call_args[0][0]
                assert 'Missing recommended environment variables' in warning_call
                
        except Exception as e:
            pytest.fail(f"Secret manager warning test failed: {e}")

    def test_config_warns_about_missing_api_key(self, clean_env):
        """Test config module warns about missing API_KEY"""
        try:
            with patch('config.logger') as mock_logger:
                import config
                # Force reload to trigger the warning
                import importlib
                importlib.reload(config)
                
                # Should have logged warning about missing API_KEY
                mock_logger.warning.assert_called()
                
                # Check warning content
                warning_call = mock_logger.warning.call_args[0][0]
                assert 'X_API_KEY environment variable is not set' in warning_call
                
        except Exception as e:
            pytest.fail(f"Config warning test failed: {e}")


class TestApplicationRecovery:
    """Test that application can recover when secrets are added"""
    
    def test_security_validator_can_be_recreated_with_token(self):
        """Test that security validator works when DB_TOKEN is added"""
        # First without token
        with patch.dict(os.environ, {}, clear=True):
            from server.security import APIKeyValidator
            
            validator1 = APIKeyValidator(auto_error=False)
            assert validator1.db_token is None
            
            # Validation should fail
            result = validator1.validate_api_key("test_key")
            assert result is False
        
        # Then with token
        with patch.dict(os.environ, {'DB_TOKEN': 'test_token_123456'}):
            validator2 = APIKeyValidator(auto_error=False)
            assert validator2.db_token is not None
            
            # Should validate correctly now
            result = validator2.validate_api_key("test_token_123456")
            assert result is True
            
            result = validator2.validate_api_key("wrong_token")
            assert result is False

    def test_api_key_functionality_recovers_with_config(self):
        """Test that API key functionality works when API_KEY is provided"""
        # Test without API_KEY
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import config
            importlib.reload(config)
            
            assert config.API_KEY is None or config.API_KEY == ""
        
        # Test with API_KEY
        with patch.dict(os.environ, {'API_KEY': 'test_api_key_123'}):
            importlib.reload(config)
            
            assert config.API_KEY == 'test_api_key_123'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
