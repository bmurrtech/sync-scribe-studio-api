#!/usr/bin/env python3
"""
Unit Tests for Mandatory Health Endpoints

Following TDD principles - these tests define the expected behavior
for the mandatory endpoints as specified in Rule BEW5.

Tests cover:
1. Root endpoint (/) - service info, version, key endpoints
2. Basic health endpoint (/health) - service status, timestamp, version
3. Detailed health endpoint (/health/detailed) - env vars, diagnostics, warnings
"""

import pytest
import sys
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app import create_app
from version import BUILD_NUMBER


class TestHealthEndpoints:
    """Test suite for mandatory health endpoints per Rule BEW5"""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        app = create_app()
        app.config['TESTING'] = True
        return app.test_client()

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables for testing"""
        return {
            'PORT': '8080',
            'PYTHONUNBUFFERED': '1',
            'BUILD_NUMBER': '200',
            'WHISPER_CACHE_DIR': '/tmp/whisper_cache'
        }

    def test_root_endpoint_returns_service_info(self, client):
        """Test that / endpoint returns service name, version, and key endpoints per Rule BEW5"""
        response = client.get('/')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Required fields per Rule BEW5
        assert 'service' in data
        assert 'version' in data
        assert 'endpoints' in data
        
        # Service identification
        assert data['service'] == "Sync Scribe Studio API"
        assert data['version'] == BUILD_NUMBER
        assert data['status'] == "running"
        
        # Key endpoints must be listed
        endpoints = data['endpoints']
        assert isinstance(endpoints, dict)
        assert '/' in endpoints
        assert '/health' in endpoints
        assert '/health/detailed' in endpoints
        
        # Should include some key API endpoints
        assert any('/v1/' in endpoint for endpoint in endpoints.keys())

    def test_root_endpoint_includes_documentation(self, client):
        """Test that / endpoint includes documentation link"""
        response = client.get('/')
        data = response.get_json()
        
        assert 'documentation' in data
        assert isinstance(data['documentation'], str)
        assert data['documentation'].startswith('http')

    def test_root_endpoint_includes_build_info(self, client):
        """Test that / endpoint includes build information"""
        response = client.get('/')
        data = response.get_json()
        
        assert 'build_info' in data
        build_info = data['build_info']
        
        assert 'build_number' in build_info
        assert 'python_version' in build_info
        assert build_info['build_number'] == BUILD_NUMBER

    def test_basic_health_endpoint_returns_200(self, client):
        """Test that /health endpoint returns 200 status and required fields per Rule BEW5"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Required fields per Rule BEW5
        assert 'status' in data
        assert 'timestamp' in data  
        assert 'version' in data
        assert 'service' in data
        
        # Field validation
        assert data['status'] == "healthy"
        assert isinstance(data['timestamp'], int)
        assert data['version'] == BUILD_NUMBER
        assert data['service'] == "Sync Scribe Studio API"

    def test_basic_health_endpoint_timestamp_is_recent(self, client):
        """Test that /health endpoint timestamp is current"""
        start_time = int(time.time())
        response = client.get('/health')
        end_time = int(time.time())
        
        data = response.get_json()
        timestamp = data['timestamp']
        
        # Timestamp should be within a reasonable range of request time
        assert start_time <= timestamp <= end_time

    def test_basic_health_endpoint_includes_port(self, client):
        """Test that /health endpoint includes port information"""
        response = client.get('/health')
        data = response.get_json()
        
        assert 'port' in data
        # Should be string representation of port
        assert isinstance(data['port'], str)

    @patch.dict(os.environ, {
        'PORT': '8080',
        'PYTHONUNBUFFERED': '1', 
        'BUILD_NUMBER': '200',
        'WHISPER_CACHE_DIR': '/tmp/whisper_cache'
    })
    def test_detailed_health_endpoint_returns_200_when_healthy(self, client):
        """Test that /health/detailed returns 200 when all required env vars present"""
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('subprocess.run') as mock_subprocess, \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3)):
            
            # Mock successful FFmpeg check
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = client.get('/health/detailed')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Basic health fields
            assert data['status'] == "healthy"
            assert 'timestamp' in data
            assert 'version' in data
            assert data['version'] == BUILD_NUMBER

    def test_detailed_health_endpoint_reports_env_vars_status(self, client):
        """Test that /health/detailed reports environment variables presence per Rule BEW5"""
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('subprocess.run') as mock_subprocess, \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3)):
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = client.get('/health/detailed')
            data = response.get_json()
            
            # Environment variables status
            assert 'environment_variables' in data
            env_vars = data['environment_variables']
            assert isinstance(env_vars, dict)
            
            # Should check required variables
            required_vars = ['PORT', 'PYTHONUNBUFFERED', 'BUILD_NUMBER', 'WHISPER_CACHE_DIR']
            for var in required_vars:
                assert var in env_vars

    def test_detailed_health_endpoint_reports_missing_deps_warnings(self, client):
        """Test that /health/detailed reports missing dependencies warnings per Rule BEW5"""
        with patch('subprocess.run', side_effect=Exception("FFmpeg not found")), \
             patch('os.path.exists', return_value=False), \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 1*1024**3)):
            
            response = client.get('/health/detailed')
            data = response.get_json()
            
            # Warnings should be present
            assert 'warnings' in data
            assert isinstance(data['warnings'], list)
            assert len(data['warnings']) > 0
            
            # Should have FFmpeg warning
            ffmpeg_warnings = [w for w in data['warnings'] if 'FFmpeg' in w]
            assert len(ffmpeg_warnings) > 0

    def test_detailed_health_endpoint_reports_service_checks(self, client):
        """Test that /health/detailed includes service dependency checks"""
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3)):
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = client.get('/health/detailed')
            data = response.get_json()
            
            # Service checks
            assert 'service_checks' in data
            service_checks = data['service_checks']
            
            assert 'ffmpeg' in service_checks
            assert 'whisper_cache' in service_checks
            assert 'tmp_disk_space' in service_checks

    @patch.dict(os.environ, {}, clear=True)
    def test_detailed_health_endpoint_returns_200_when_missing_required_vars(self, client):
        """Test that /health/detailed returns 200 even when required environment variables are missing"""
        with patch('subprocess.run', side_effect=Exception("FFmpeg not found")), \
             patch('os.path.exists', return_value=False):
            
            response = client.get('/health/detailed')
            
            # Should always return 200 but with degraded status
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['status'] == "degraded"
            assert 'missing_dependencies' in data
            assert len(data['missing_dependencies']['required']) > 0

    def test_detailed_health_endpoint_includes_hostname(self, client):
        """Test that /health/detailed includes hostname information"""
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3)):
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = client.get('/health/detailed')
            data = response.get_json()
            
            assert 'hostname' in data
            assert isinstance(data['hostname'], str)

    def test_detailed_health_endpoint_checks_disk_space(self, client):
        """Test that /health/detailed monitors disk space and warns when low"""
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('shutil.disk_usage', return_value=(100*1024**3, 99*1024**3, 0.5*1024**3)):  # Low disk space
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = client.get('/health/detailed')
            data = response.get_json()
            
            # Should warn about low disk space
            warnings = data['warnings']
            disk_warnings = [w for w in warnings if 'disk space' in w.lower()]
            assert len(disk_warnings) > 0

    def test_all_health_endpoints_return_json_content_type(self, client):
        """Test that all health endpoints return proper JSON content type"""
        endpoints = ['/', '/health', '/health/detailed']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.content_type.startswith('application/json')

    def test_health_endpoints_handle_method_not_allowed(self, client):
        """Test that health endpoints only accept GET requests"""
        endpoints = ['/', '/health', '/health/detailed']
        
        for endpoint in endpoints:
            # Test POST (should fail)
            response = client.post(endpoint)
            assert response.status_code == 405

    def test_endpoints_are_consistent_with_version(self, client):
        """Test that all endpoints return consistent version information"""
        endpoints = ['/', '/health', '/health/detailed']
        
        versions = []
        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.get_json()
            versions.append(data['version'])
        
        # All endpoints should return the same version
        assert len(set(versions)) == 1
        assert versions[0] == BUILD_NUMBER

    def test_service_name_consistency(self, client):
        """Test that service name is consistent across all endpoints"""
        endpoints = ['/', '/health', '/health/detailed']
        
        service_names = []
        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.get_json()
            service_names.append(data['service'])
        
        # All endpoints should return the same service name
        assert len(set(service_names)) == 1
        assert service_names[0] == "Sync Scribe Studio API"


class TestHealthEndpointsPerformance:
    """Performance tests for health endpoints to ensure they respond quickly"""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        app = create_app()
        app.config['TESTING'] = True
        return app.test_client()

    def test_basic_health_endpoint_responds_quickly(self, client):
        """Test that /health endpoint responds within reasonable time"""
        start_time = time.time()
        response = client.get('/health')
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should respond within 100ms
        assert (end_time - start_time) < 0.1

    def test_detailed_health_endpoint_responds_reasonably(self, client):
        """Test that /health/detailed endpoint responds within reasonable time"""
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3)):
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            start_time = time.time()
            response = client.get('/health/detailed')
            end_time = time.time()
            
            assert response.status_code == 200
            # Detailed health check should respond within 1 second
            assert (end_time - start_time) < 1.0


class TestHealthEndpointsOptionalVars:
    """Test suite for health endpoints with missing optional variables"""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        app = create_app()
        app.config['TESTING'] = True
        return app.test_client()

    @patch.dict(os.environ, {
        'PORT': '8080',
        'PYTHONUNBUFFERED': '1', 
        'BUILD_NUMBER': '200',
        'WHISPER_CACHE_DIR': '/tmp/whisper_cache'
        # Intentionally omitting all optional vars
    })
    def test_detailed_health_without_optional_vars_returns_200(self, client):
        """Test that /health/detailed returns 200 even when all optional env vars are missing"""
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('subprocess.run') as mock_subprocess, \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3)):
            
            # Mock successful FFmpeg check
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = client.get('/health/detailed')
            
            # Should return 200 regardless of missing optional vars
            assert response.status_code == 200
            data = response.get_json()
            
            # Should be healthy since only optional vars are missing
            assert data['status'] == "healthy"
            
            # Check that optional vars are marked as "missing (optional)"
            env_vars = data['environment_variables']
            optional_vars = ['YOUTUBE_SERVICE_URL', 'GUNICORN_WORKERS', 'GUNICORN_TIMEOUT', 'MAX_QUEUE_LENGTH']
            
            for var in optional_vars:
                assert var in env_vars
                assert env_vars[var] == "missing (optional)"
            
            # Missing optional vars should be tracked
            assert 'missing_dependencies' in data
            assert 'optional' in data['missing_dependencies']
            assert len(data['missing_dependencies']['optional']) == len(optional_vars)
            
            # Should have informational warnings about optional vars
            warnings = data['warnings']
            optional_warnings = [w for w in warnings if 'optional env var' in w]
            assert len(optional_warnings) == len(optional_vars)

    @patch.dict(os.environ, {
        'PORT': '8080',
        'PYTHONUNBUFFERED': '1', 
        'BUILD_NUMBER': '200',
        'WHISPER_CACHE_DIR': '/tmp/whisper_cache',
        'YOUTUBE_SERVICE_URL': 'http://youtube-service:8080',
        'GUNICORN_WORKERS': '4'
        # Partial optional vars - some present, some missing
    })
    def test_detailed_health_with_partial_optional_vars(self, client):
        """Test that /health/detailed properly reports mix of present/missing optional vars"""
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('subprocess.run') as mock_subprocess, \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3)):
            
            # Mock successful FFmpeg check
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = client.get('/health/detailed')
            
            assert response.status_code == 200
            data = response.get_json()
            
            env_vars = data['environment_variables']
            
            # Present optional vars should be marked as "present"
            assert env_vars['YOUTUBE_SERVICE_URL'] == "present"
            assert env_vars['GUNICORN_WORKERS'] == "present"
            
            # Missing optional vars should be marked as "missing (optional)"
            assert env_vars['GUNICORN_TIMEOUT'] == "missing (optional)"
            assert env_vars['MAX_QUEUE_LENGTH'] == "missing (optional)"
            
            # Should track only the actually missing optional vars
            missing_optional = data['missing_dependencies']['optional']
            assert 'GUNICORN_TIMEOUT' in missing_optional
            assert 'MAX_QUEUE_LENGTH' in missing_optional
            assert 'YOUTUBE_SERVICE_URL' not in missing_optional
            assert 'GUNICORN_WORKERS' not in missing_optional

    @patch.dict(os.environ, {}, clear=True)
    def test_detailed_health_with_no_env_vars_at_all(self, client):
        """Test that /health/detailed handles complete absence of environment variables gracefully"""
        with patch('subprocess.run', side_effect=Exception("FFmpeg not found")), \
             patch('os.path.exists', return_value=False):
            
            response = client.get('/health/detailed')
            
            # Should still return 200 (never fails)
            assert response.status_code == 200
            data = response.get_json()
            
            # Should be degraded due to missing required vars
            assert data['status'] == "degraded"
            
            # All required vars should be missing
            required_vars = ['PORT', 'PYTHONUNBUFFERED', 'BUILD_NUMBER', 'WHISPER_CACHE_DIR']
            for var in required_vars:
                assert data['environment_variables'][var] == "missing (required)"
            
            # All optional vars should be missing
            optional_vars = ['YOUTUBE_SERVICE_URL', 'GUNICORN_WORKERS', 'GUNICORN_TIMEOUT', 'MAX_QUEUE_LENGTH']
            for var in optional_vars:
                assert data['environment_variables'][var] == "missing (optional)"
            
            # Should have comprehensive warnings
            warnings = data['warnings']
            assert len(warnings) > 0
            
            # Should have warnings for both required and optional vars
            required_warnings = [w for w in warnings if 'required env var' in w]
            optional_warnings = [w for w in warnings if 'optional env var' in w]
            assert len(required_warnings) == len(required_vars)
            assert len(optional_warnings) == len(optional_vars)

    def test_basic_health_never_fails_regardless_of_env_vars(self, client):
        """Test that /health endpoint always returns 200 regardless of environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            response = client.get('/health')
            
            # Basic health should always return 200
            assert response.status_code == 200
            data = response.get_json()
            
            # Should always report as healthy (basic endpoint doesn't check env vars)
            assert data['status'] == "healthy"
            assert 'timestamp' in data
            assert 'version' in data
            assert 'service' in data


class TestHealthEndpointsEdgeCases:
    """Edge case tests for health endpoints"""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        app = create_app()
        app.config['TESTING'] = True
        return app.test_client()

    def test_health_endpoints_with_unicode_hostname(self, client):
        """Test health endpoints work with unicode characters in hostname"""
        with patch('socket.gethostname', return_value='test-ñame'), \
             patch('subprocess.run') as mock_subprocess, \
             patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch('shutil.disk_usage', return_value=(100*1024**3, 50*1024**3, 50*1024**3)):
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            response = client.get('/health/detailed')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'hostname' in data

    def test_health_endpoints_with_system_errors(self, client):
        """Test health endpoints handle system errors gracefully"""
        with patch('subprocess.run', side_effect=Exception("System error")), \
             patch('os.path.exists', side_effect=Exception("Filesystem error")), \
             patch('shutil.disk_usage', side_effect=Exception("Disk error")):
            
            response = client.get('/health/detailed')
            
            # Should always return 200 (never fails) but with warnings
            assert response.status_code == 200
            data = response.get_json()
            
            # Should have warnings about the errors
            assert 'warnings' in data
            assert len(data['warnings']) > 0


if __name__ == '__main__':
    # Allow running tests directly
    pytest.main([__file__, '-v'])
