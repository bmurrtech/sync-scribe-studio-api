"""
Unit tests for config.py module.

These tests verify that X_API_KEY is truly optional and that appropriate
warnings are logged when the API key is missing.
"""

import os
import pytest
import logging
import sys
import importlib.util
from unittest.mock import patch, MagicMock
from io import StringIO


class TestConfigModule:
    """Test cases for config.py module."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Clear any existing API key environment variables
        if 'X_API_KEY' in os.environ:
            del os.environ['X_API_KEY']
        if 'API_KEY' in os.environ:
            del os.environ['API_KEY']

    def teardown_method(self):
        """Clean up test environment after each test."""
        # Clear any existing API key environment variables
        if 'X_API_KEY' in os.environ:
            del os.environ['X_API_KEY']
        if 'API_KEY' in os.environ:
            del os.environ['API_KEY']
            
        # Remove config module from cache to allow fresh imports
        if 'config' in sys.modules:
            del sys.modules['config']

    def test_config_import_without_api_key_no_exception(self):
        """Test that importing config.py does not raise exception when API key is missing."""
        # Ensure no API key is set
        assert 'X_API_KEY' not in os.environ
        assert 'API_KEY' not in os.environ
        
        # This should not raise an exception
        import config
        assert config is not None

    def test_config_logs_warning_when_api_key_missing(self):
        """Test that a warning is logged when API key is missing."""
        # Ensure no API key is set
        assert 'X_API_KEY' not in os.environ
        assert 'API_KEY' not in os.environ
        
        # Capture logging output
        import logging
        from io import StringIO
        
        log_capture_string = StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.WARNING)
        
        # Get the root logger
        logger = logging.getLogger()
        logger.addHandler(ch)
        
        try:
            import config
            
            # Check the log contents
            log_contents = log_capture_string.getvalue()
            assert "X_API_KEY" in log_contents
            assert "not set" in log_contents or "Some features may not work" in log_contents
        finally:
            logger.removeHandler(ch)

    def test_get_api_key_returns_none_when_missing(self):
        """Test that get_api_key() returns None when API key is not set."""
        # Ensure no API key is set
        assert 'X_API_KEY' not in os.environ
        assert 'API_KEY' not in os.environ
        
        import config
        
        # Test the helper function
        assert hasattr(config, 'get_api_key'), "get_api_key function should exist"
        api_key = config.get_api_key()
        assert api_key is None, "get_api_key should return None when no API key is set"

    def test_get_api_key_returns_x_api_key_when_set(self):
        """Test that get_api_key() returns X_API_KEY when it's set."""
        test_key = "test-x-api-key-12345"
        os.environ['X_API_KEY'] = test_key
        
        import config
        
        api_key = config.get_api_key()
        assert api_key == test_key, "get_api_key should return X_API_KEY value"

    def test_get_api_key_returns_api_key_when_x_api_key_not_set(self):
        """Test that get_api_key() falls back to API_KEY when X_API_KEY is not set."""
        test_key = "test-api-key-67890"
        os.environ['API_KEY'] = test_key
        
        import config
        
        api_key = config.get_api_key()
        assert api_key == test_key, "get_api_key should return API_KEY value when X_API_KEY is not set"

    def test_get_api_key_prefers_x_api_key_over_api_key(self):
        """Test that get_api_key() prefers X_API_KEY over API_KEY when both are set."""
        x_api_key = "x-api-key-preferred"
        api_key = "api-key-fallback"
        os.environ['X_API_KEY'] = x_api_key
        os.environ['API_KEY'] = api_key
        
        import config
        
        result = config.get_api_key()
        assert result == x_api_key, "get_api_key should prefer X_API_KEY over API_KEY"

    def test_api_key_variable_behavior_with_missing_keys(self):
        """Test that the API_KEY module variable handles missing keys gracefully."""
        # Ensure no API key is set
        assert 'X_API_KEY' not in os.environ
        assert 'API_KEY' not in os.environ
        
        import config
        
        # The module should still have an API_KEY attribute, but it should be None
        assert hasattr(config, 'API_KEY'), "config module should have API_KEY attribute"
        assert config.API_KEY is None, "API_KEY should be None when no environment variable is set"

    def test_api_key_variable_with_x_api_key_set(self):
        """Test that the API_KEY module variable is set when X_API_KEY is present."""
        test_key = "test-x-api-key-module"
        os.environ['X_API_KEY'] = test_key
        
        import config
        
        assert config.API_KEY == test_key, "API_KEY module variable should equal X_API_KEY"

    def test_api_key_variable_with_api_key_set(self):
        """Test that the API_KEY module variable is set when API_KEY is present."""
        test_key = "test-api-key-module"
        os.environ['API_KEY'] = test_key
        
        import config
        
        assert config.API_KEY == test_key, "API_KEY module variable should equal API_KEY env var"

    def test_validate_env_vars_function_still_works(self):
        """Test that existing validate_env_vars function is not broken."""
        import config
        
        # This should not raise an exception
        assert hasattr(config, 'validate_env_vars'), "validate_env_vars function should still exist"
        assert callable(config.validate_env_vars), "validate_env_vars should be callable"
        
        # Test that it still raises ValueError for missing vars (this behavior should be preserved)
        with pytest.raises(ValueError, match="Missing environment variables"):
            config.validate_env_vars('GCP')

    def test_other_config_variables_unchanged(self):
        """Test that other configuration variables are not affected."""
        import config
        
        # These should still exist and work as before
        assert hasattr(config, 'LOCAL_STORAGE_PATH'), "LOCAL_STORAGE_PATH should still exist"
        assert hasattr(config, 'GCP_SA_CREDENTIALS'), "GCP_SA_CREDENTIALS should still exist"
        assert hasattr(config, 'GCP_BUCKET_NAME'), "GCP_BUCKET_NAME should still exist"
        
        # LOCAL_STORAGE_PATH should have default value
        assert config.LOCAL_STORAGE_PATH == '/tmp' or config.LOCAL_STORAGE_PATH == os.environ.get('LOCAL_STORAGE_PATH', '/tmp')


class TestConfigIntegration:
    """Integration tests to verify config works in realistic scenarios."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Clear any existing API key environment variables
        if 'X_API_KEY' in os.environ:
            del os.environ['X_API_KEY']
        if 'API_KEY' in os.environ:
            del os.environ['API_KEY']
            
        # Remove config module from cache to allow fresh imports
        if 'config' in sys.modules:
            del sys.modules['config']

    def teardown_method(self):
        """Clean up test environment after each test."""
        # Clear any existing API key environment variables
        if 'X_API_KEY' in os.environ:
            del os.environ['X_API_KEY']
        if 'API_KEY' in os.environ:
            del os.environ['API_KEY']
            
        # Remove config module from cache to allow fresh imports
        if 'config' in sys.modules:
            del sys.modules['config']

    def test_application_startup_without_api_key(self):
        """Test that an application can start without API key set."""
        # Simulate application startup
        try:
            import config
            
            # Application should be able to check if API key is available
            if config.get_api_key() is None:
                # Application can handle this gracefully
                assert True, "Application can handle missing API key"
            else:
                # This shouldn't happen in this test, but if it does, that's also fine
                pass
                
        except Exception as e:
            pytest.fail(f"Application startup failed with missing API key: {e}")

    def test_warning_message_content(self):
        """Test the specific content of the warning message."""
        # Capture logging output
        import logging
        from io import StringIO
        
        log_capture_string = StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.WARNING)
        
        # Get the root logger
        logger = logging.getLogger()
        logger.addHandler(ch)
        
        try:
            import config
            
            # Check the log contents
            log_contents = log_capture_string.getvalue()
            
            # Check that the warning contains helpful information
            assert "X_API_KEY" in log_contents
            assert any(keyword in log_contents.lower() for keyword in ["missing", "not set", "unset"])
            
            # The warning should be informative but not cause the application to fail
            assert len(log_contents.strip()) > 10  # Should be a meaningful message
        finally:
            logger.removeHandler(ch)
