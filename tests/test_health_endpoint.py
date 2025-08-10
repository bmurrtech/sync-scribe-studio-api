"""
Test suite for health check endpoint - TDD Example
This test is written BEFORE the implementation exists (RED phase of TDD)
"""
import pytest
from unittest.mock import patch, MagicMock
import json


def test_health_check_endpoint_exists(mock_flask_app):
    """
    Test that health check endpoint exists and returns expected structure.
    This test will FAIL initially because the endpoint doesn't exist yet.
    """
    # Attempt to call the non-existent endpoint
    response = mock_flask_app.get("/health")
    
    # These assertions define our expected behavior
    assert response.status_code == 200
    
    data = response.json
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data


def test_health_check_includes_service_status(mock_flask_app):
    """
    Test that health check includes status of dependent services.
    This test will also FAIL initially.
    """
    response = mock_flask_app.get("/health")
    
    assert response.status_code == 200
    data = response.json
    
    # Expect service health checks
    assert "services" in data
    services = data["services"]
    
    # We expect at least these core services to be checked
    assert "database" in services
    assert "storage" in services
    assert "api" in services
    
    # Each service should have a status
    for service_name, service_data in services.items():
        assert "status" in service_data
        assert service_data["status"] in ["healthy", "degraded", "unhealthy"]


def test_health_check_with_detailed_flag(mock_flask_app):
    """
    Test that health check can return detailed information when requested.
    This defines the behavior for a detailed health check.
    """
    response = mock_flask_app.get("/health?detailed=true")
    
    assert response.status_code == 200
    data = response.json
    
    # When detailed=true, we expect more information
    assert "system" in data
    system_info = data["system"]
    
    assert "memory_usage" in system_info
    assert "cpu_usage" in system_info
    assert "disk_usage" in system_info
    assert "uptime" in system_info


def test_health_check_handles_service_failures_gracefully(mock_flask_app):
    """
    Test that health check degrades gracefully when a service is down.
    This ensures resilience in monitoring.
    """
    # Mock a service being down
    with patch('routes.health.check_database_health') as mock_db_check:
        mock_db_check.return_value = {"status": "unhealthy", "error": "Connection timeout"}
        
        response = mock_flask_app.get("/health")
        
        # Endpoint should still respond even if a service is down
        assert response.status_code == 200
        
        data = response.json
        assert data["status"] == "degraded"  # Overall status should be degraded
        assert data["services"]["database"]["status"] == "unhealthy"


def test_health_check_authentication_not_required(mock_flask_app):
    """
    Test that health check endpoint doesn't require authentication.
    Health checks should be accessible for monitoring tools.
    """
    # Make request without any authentication headers
    response = mock_flask_app.get("/health")
    
    # Should succeed without authentication
    assert response.status_code == 200


def test_health_check_response_time(mock_flask_app):
    """
    Test that health check responds quickly.
    Health checks should be lightweight and fast.
    """
    import time
    
    start_time = time.time()
    response = mock_flask_app.get("/health")
    end_time = time.time()
    
    # Health check should respond in less than 1 second
    assert (end_time - start_time) < 1.0
    assert response.status_code == 200


@pytest.mark.parametrize("service_name,expected_keys", [
    ("database", ["status", "response_time"]),
    ("storage", ["status", "available_space"]),
    ("api", ["status", "rate_limit_remaining"])
])
def test_health_check_service_details(mock_flask_app, service_name, expected_keys):
    """
    Parameterized test for service-specific health details.
    Each service should return specific health metrics.
    """
    response = mock_flask_app.get("/health?detailed=true")
    
    assert response.status_code == 200
    data = response.json
    
    assert service_name in data["services"]
    service_data = data["services"][service_name]
    
    for key in expected_keys:
        assert key in service_data, f"Service {service_name} missing key: {key}"
