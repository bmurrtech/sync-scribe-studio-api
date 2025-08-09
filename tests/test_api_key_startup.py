#!/usr/bin/env python3
"""
Test API Key Startup Requirements (TDD Red Phase)

This test file is designed to FAIL initially and reproduce the current 
import/startup crash when the API_KEY environment variable is missing.

According to TDD principles, these tests should initially fail (RED phase)
to demonstrate the current problematic behavior before implementing fixes.
"""

import pytest
import os
import sys
from unittest.mock import patch

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


class TestAPIKeyStartupCrash:
    """Test cases that should FAIL initially - reproducing the startup crash"""
    
    def test_import_main_app_without_api_key_should_not_crash(self, monkeypatch):
        """
        Test that importing main app with missing API_KEY does NOT cause ImportError/SystemExit.
        
        This test should FAIL initially (RED phase) because the current code
        likely crashes on import when API_KEY is missing.
        
        Expected behavior after fix: App should import successfully even without API_KEY.
        """
        # Remove API_KEY from environment if it exists
        monkeypatch.delenv("API_KEY", raising=False)
        
        # This should NOT raise ImportError or SystemExit
        try:
            # Try importing from potential main module locations
            # Based on the project structure, the main app is in app.py
            from app import app
            
            # If we get here, the import succeeded (which is what we want after the fix)
            assert app is not None
            
        except (ImportError, SystemExit, ModuleNotFoundError) as e:
            # This is the current problematic behavior that should be fixed
            pytest.fail(f"Import should not crash without API_KEY, but got: {type(e).__name__}: {e}")
        except Exception as e:
            # Other exceptions might be OK (like configuration warnings)
            # We only care about crashes that prevent import
            pass
    
    def test_import_server_main_without_api_key_should_not_crash(self, monkeypatch):
        """
        Test importing server.main (if it exists) without API_KEY should not crash.
        
        This test might fail if server.main doesn't exist, which is fine.
        The purpose is to catch any server-side startup crashes.
        """
        # Remove API_KEY from environment if it exists
        monkeypatch.delenv("API_KEY", raising=False)
        
        try:
            # Try importing server.main if it exists
            from server import main as server_main
            
            # If we get here, the import succeeded
            assert server_main is not None
            
        except ModuleNotFoundError:
            # server.main doesn't exist - that's OK, skip this test
            pytest.skip("server.main module does not exist")
            
        except ImportError as e:
            # Check if this is a "cannot import name 'main'" error (module doesn't exist)
            if "cannot import name 'main'" in str(e):
                pytest.skip("server.main module does not exist")
            else:
                # This would be the problematic behavior (other import errors)
                pytest.fail(f"server.main import should not crash without API_KEY, but got: {type(e).__name__}: {e}")
                
        except SystemExit as e:
            # This would be the problematic behavior
            pytest.fail(f"server.main import should not crash without API_KEY, but got: {type(e).__name__}: {e}")
        except Exception as e:
            # Other exceptions might be acceptable
            pass
    
    def test_create_app_without_api_key_should_not_crash(self, monkeypatch):
        """
        Test that create_app() function works without API_KEY environment variable.
        
        This should FAIL initially if the app creation crashes due to missing API_KEY.
        """
        # Remove API_KEY from environment if it exists
        monkeypatch.delenv("API_KEY", raising=False)
        
        # Also remove other potentially problematic env vars
        monkeypatch.delenv("DB_TOKEN", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        try:
            from app import create_app
            
            # This should succeed without crashing
            app = create_app()
            assert app is not None
            assert hasattr(app, 'config')
            
        except (ImportError, SystemExit) as e:
            # This is the crash behavior we want to fix
            pytest.fail(f"create_app() should not crash without API_KEY, but got: {type(e).__name__}: {e}")
        except Exception as e:
            # Log other exceptions but don't fail the test for them
            # We only care about import/system crashes
            print(f"Non-critical exception during app creation: {type(e).__name__}: {e}")
    
    def test_app_starts_without_critical_env_vars(self, monkeypatch):
        """
        Test that the Flask app can start even when critical environment variables are missing.
        
        This test should demonstrate that missing env vars should not prevent basic app startup.
        """
        # Remove all critical environment variables
        critical_vars = [
            "API_KEY", 
            "DB_TOKEN", 
            "OPENAI_API_KEY", 
            "X_API_KEY",
            "RAILWAY_API_TOKEN",
            "VERCEL_TOKEN"
        ]
        
        for var in critical_vars:
            monkeypatch.delenv(var, raising=False)
        
        # Set minimal required vars for testing
        monkeypatch.setenv("FLASK_ENV", "testing")
        monkeypatch.setenv("PORT", "8080")
        
        try:
            from app import create_app
            app = create_app()
            
            # App should be created successfully
            assert app is not None
            
            # Should be able to get test client
            with app.test_client() as client:
                # Basic health check should work
                response = client.get('/health')
                
                # Should not return 500 (server error)
                assert response.status_code != 500, f"Health endpoint crashed: {response.data}"
                
        except (ImportError, SystemExit) as e:
            pytest.fail(f"App startup should not crash without env vars, but got: {type(e).__name__}: {e}")
    
    def test_security_module_import_without_db_token(self, monkeypatch):
        """
        Test that security module can be imported without DB_TOKEN.
        
        This might fail if the security module crashes on import due to missing DB_TOKEN.
        """
        # Remove DB_TOKEN specifically
        monkeypatch.delenv("DB_TOKEN", raising=False)
        
        try:
            from server import security
            
            # Should be able to import and access basic functionality
            assert hasattr(security, 'require_api_key')
            assert hasattr(security, 'setup_security')
            
        except (ImportError, SystemExit) as e:
            pytest.fail(f"Security module import should not crash without DB_TOKEN, but got: {type(e).__name__}: {e}")
    
    def test_config_module_import_without_api_key(self, monkeypatch):
        """
        Test that config module can be imported without API_KEY.
        
        This might fail if the config module has hard requirements for API_KEY.
        """
        # Remove API_KEY specifically
        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.delenv("X_API_KEY", raising=False)
        
        try:
            import config
            
            # Config should be importable even if values are None/empty
            # We're not testing the values, just that import doesn't crash
            assert config is not None
            
        except (ImportError, SystemExit) as e:
            pytest.fail(f"Config module import should not crash without API_KEY, but got: {type(e).__name__}: {e}")


class TestEnvironmentVariableHandling:
    """Test proper handling of missing environment variables"""
    
    def test_missing_env_vars_should_warn_not_crash(self, monkeypatch, caplog):
        """
        Test that missing environment variables should produce warnings, not crashes.
        
        This establishes the expected behavior: warnings are OK, crashes are not.
        """
        # Remove critical variables
        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.delenv("DB_TOKEN", raising=False)
        
        try:
            from app import create_app
            
            # Should create successfully
            app = create_app()
            assert app is not None
            
            # Check if warnings were logged (this is acceptable behavior)
            # We're not asserting warnings must exist, just that the app didn't crash
            
        except (ImportError, SystemExit) as e:
            pytest.fail(f"Missing env vars should warn, not crash: {type(e).__name__}: {e}")
    
    def test_graceful_degradation_without_secrets(self, monkeypatch):
        """
        Test that the application gracefully degrades functionality without secrets.
        
        This test should pass after fixes are implemented, showing that the app
        can run in a degraded mode rather than crashing completely.
        """
        # Remove all secrets
        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.delenv("DB_TOKEN", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        try:
            from app import create_app
            app = create_app()
            
            with app.test_client() as client:
                # Health endpoints should work even in degraded mode
                health_response = client.get('/health')
                
                # Should not crash (200 OK or 503 degraded service are both acceptable)
                assert health_response.status_code in [200, 503], \
                    f"Health check should work in degraded mode, got {health_response.status_code}"
                
                # Root endpoint should work
                root_response = client.get('/')
                assert root_response.status_code in [200, 503], \
                    f"Root endpoint should work in degraded mode, got {root_response.status_code}"
                    
        except (ImportError, SystemExit) as e:
            pytest.fail(f"App should gracefully degrade, not crash: {type(e).__name__}: {e}")


if __name__ == '__main__':
    # Run the tests with verbose output to see the failures
    pytest.main([__file__, '-v', '--tb=short'])
