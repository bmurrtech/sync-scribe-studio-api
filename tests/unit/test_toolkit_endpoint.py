"""
Unit and Integration tests for Toolkit endpoints
Following TDD: RED -> GREEN -> REFACTOR approach
"""

import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
import requests_mock
import jsonschema
from datetime import datetime

# Test the /v1/toolkit/test endpoint
class TestToolkitTestEndpoint:
    """Tests for /v1/toolkit/test endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_toolkit_test_success_unit(self, mock_requests, api_key, base_url, validate_schema):
        """RED: Test toolkit test endpoint returns success URL"""
        # Arrange
        endpoint = "/v1/toolkit/test"
        expected_url = "https://storage.example.com/success.txt"
        
        mock_requests.get(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "test-job-123",
                "response": expected_url,
                "message": "success",
                "run_time": 0.5,
                "queue_time": 0,
                "total_time": 0.5,
                "pid": 12345,
                "queue_id": 67890,
                "queue_length": 0,
                "build_number": "1.0.0"
            },
            status_code=200,
            headers={"X-API-Key": api_key}
        )
        
        # Act
        import requests
        response = requests.get(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert validate_schema(data, "success_response")
        assert data["response"] == expected_url
        assert data["code"] == 200
        assert "job_id" in data
        assert data["run_time"] >= 0
        assert data["total_time"] >= 0
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_toolkit_test_missing_auth(self, mock_requests, base_url):
        """RED: Test toolkit endpoint requires authentication"""
        # Arrange
        endpoint = "/v1/toolkit/test"
        mock_requests.get(
            f"{base_url}{endpoint}",
            json={"code": 401, "message": "Unauthorized: API key required"},
            status_code=401
        )
        
        # Act
        import requests
        response = requests.get(f"{base_url}{endpoint}")
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert "Unauthorized" in data["message"]
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_toolkit_test_invalid_api_key(self, mock_requests, base_url):
        """RED: Test toolkit endpoint rejects invalid API key"""
        # Arrange
        endpoint = "/v1/toolkit/test"
        mock_requests.get(
            f"{base_url}{endpoint}",
            json={"code": 403, "message": "Forbidden: Invalid API key"},
            status_code=403,
            headers={"X-API-Key": "invalid-key"}
        )
        
        # Act
        import requests
        response = requests.get(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": "invalid-key"}
        )
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == 403
        assert "Invalid API key" in data["message"]
    
    @pytest.mark.integration
    @pytest.mark.toolkit
    def test_toolkit_test_integration(self, integration_helper, validate_schema):
        """GREEN: Integration test for toolkit test endpoint"""
        # Act
        response = integration_helper.make_request("GET", "/v1/toolkit/test")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert validate_schema(data, "success_response")
        assert data["response"].startswith("http")  # Should be a URL
        assert data["response"].endswith(".txt")
        assert data["message"] == "success"
        assert data["run_time"] > 0
        assert data["total_time"] > 0


class TestJobStatusEndpoint:
    """Tests for /v1/toolkit/job_status and /v1/toolkit/job/status endpoints"""
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_job_status_not_found(self, mock_requests, base_url, api_key, validate_schema):
        """RED: Test job status returns 404 for non-existent job"""
        # Arrange
        endpoint = "/v1/toolkit/job/status"
        job_id = str(uuid.uuid4())
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 404,
                "message": "Job not found",
                "job_id": job_id
            },
            status_code=404
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"job_id": job_id}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert validate_schema(data, "error_response")
        assert data["code"] == 404
        assert "not found" in data["message"].lower()
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_job_status_queued(self, mock_requests, base_url, api_key):
        """RED: Test job status for queued job"""
        # Arrange
        endpoint = "/v1/toolkit/job/status"
        job_id = str(uuid.uuid4())
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "job_status": "queued",
                "job_id": job_id,
                "queue_id": 12345,
                "process_id": 67890,
                "response": None
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"job_id": job_id}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["job_status"] == "queued"
        assert data["job_id"] == job_id
        assert data["response"] is None
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_job_status_running(self, mock_requests, base_url, api_key):
        """RED: Test job status for running job"""
        # Arrange
        endpoint = "/v1/toolkit/job/status"
        job_id = str(uuid.uuid4())
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "job_status": "running",
                "job_id": job_id,
                "queue_id": 12345,
                "process_id": 67890,
                "response": None
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"job_id": job_id}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["job_status"] == "running"
        assert data["job_id"] == job_id
        assert data["response"] is None
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_job_status_completed(self, mock_requests, base_url, api_key, validate_schema):
        """RED: Test job status for completed job"""
        # Arrange
        endpoint = "/v1/toolkit/job/status"
        job_id = str(uuid.uuid4())
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "job_status": "done",
                "job_id": job_id,
                "queue_id": 12345,
                "process_id": 67890,
                "response": {
                    "code": 200,
                    "job_id": job_id,
                    "response": "https://example.com/result.mp4",
                    "message": "success",
                    "run_time": 5.234,
                    "queue_time": 1.2,
                    "total_time": 6.434
                }
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"job_id": job_id}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["job_status"] == "done"
        assert data["job_id"] == job_id
        assert data["response"] is not None
        assert data["response"]["code"] == 200
        assert data["response"]["run_time"] > 0
        assert data["response"]["total_time"] > 0
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_job_status_missing_job_id(self, mock_requests, base_url, api_key):
        """RED: Test job status endpoint requires job_id"""
        # Arrange
        endpoint = "/v1/toolkit/job/status"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Missing required field: job_id"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 400
        assert "job_id" in data["message"]
    
    @pytest.mark.integration
    @pytest.mark.toolkit
    def test_job_status_integration_flow(self, integration_helper):
        """GREEN: Integration test for job status tracking flow"""
        # Step 1: Make a request that creates a job
        response = integration_helper.make_request("GET", "/v1/toolkit/test")
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Step 2: Check job status
        status_response = integration_helper.make_request(
            "POST",
            "/v1/toolkit/job/status",
            json={"job_id": job_id}
        )
        
        # Assert
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["job_status"] in ["queued", "running", "done"]
        
        # If job is done, verify response structure
        if status_data["job_status"] == "done":
            assert status_data["response"] is not None
            assert "code" in status_data["response"]
            assert "message" in status_data["response"]


class TestJobsStatusEndpoint:
    """Tests for /v1/toolkit/jobs_status endpoint (multiple jobs)"""
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_jobs_status_multiple(self, mock_requests, base_url, api_key):
        """RED: Test retrieving status for multiple jobs"""
        # Arrange
        endpoint = "/v1/toolkit/jobs_status"
        job_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "jobs": [
                    {"job_id": job_ids[0], "status": "done", "code": 200},
                    {"job_id": job_ids[1], "status": "running", "code": None},
                    {"job_id": job_ids[2], "status": "queued", "code": None}
                ]
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"job_ids": job_ids}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert len(data["jobs"]) == 3
        
        # Check each job status
        statuses = {job["job_id"]: job["status"] for job in data["jobs"]}
        assert statuses[job_ids[0]] == "done"
        assert statuses[job_ids[1]] == "running"
        assert statuses[job_ids[2]] == "queued"
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    def test_jobs_status_empty_list(self, mock_requests, base_url, api_key):
        """RED: Test jobs status with empty list"""
        # Arrange
        endpoint = "/v1/toolkit/jobs_status"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "No job IDs provided"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"job_ids": []}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 400
        assert "No job IDs" in data["message"]


class TestAuthenticateEndpoint:
    """Tests for /v1/toolkit/authenticate endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    @pytest.mark.auth
    def test_authenticate_valid_key(self, mock_requests, base_url, api_key):
        """RED: Test authentication with valid API key"""
        # Arrange
        endpoint = "/v1/toolkit/authenticate"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "message": "Authentication successful",
                "authenticated": True
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["authenticated"] is True
        assert "successful" in data["message"]
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    @pytest.mark.auth
    def test_authenticate_invalid_key(self, mock_requests, base_url):
        """RED: Test authentication with invalid API key"""
        # Arrange
        endpoint = "/v1/toolkit/authenticate"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 403,
                "message": "Authentication failed: Invalid API key",
                "authenticated": False
            },
            status_code=403
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": "wrong-key"}
        )
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == 403
        assert data["authenticated"] is False
        assert "Invalid API key" in data["message"]
    
    @pytest.mark.unit
    @pytest.mark.toolkit
    @pytest.mark.auth
    def test_authenticate_missing_key(self, mock_requests, base_url):
        """RED: Test authentication without API key"""
        # Arrange
        endpoint = "/v1/toolkit/authenticate"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 401,
                "message": "Authentication failed: No API key provided",
                "authenticated": False
            },
            status_code=401
        )
        
        # Act
        import requests
        response = requests.post(f"{base_url}{endpoint}")
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["authenticated"] is False
        assert "No API key" in data["message"]
    
    @pytest.mark.integration
    @pytest.mark.toolkit
    @pytest.mark.auth
    def test_authenticate_integration(self, integration_helper):
        """GREEN: Integration test for authentication endpoint"""
        # Test valid authentication
        response = integration_helper.make_request("POST", "/v1/toolkit/authenticate")
        
        # Assert success
        assert response.status_code == 200
        data = response.json()
        assert data.get("authenticated") is True
        
        # Test invalid authentication
        invalid_helper = integration_helper
        invalid_helper.session.headers["X-API-Key"] = "invalid-key-123"
        
        invalid_response = invalid_helper.make_request("POST", "/v1/toolkit/authenticate")
        
        # Assert failure
        assert invalid_response.status_code in [401, 403]
        invalid_data = invalid_response.json()
        assert invalid_data.get("authenticated") is False
