"""
Test suite for utils.py module
"""

import pytest
import os
import tempfile
import json
from unittest.mock import patch, Mock, MagicMock
import requests
import time
from pathlib import Path

# Import the utilities we're testing
from tests.utils import (
    load_env,
    post_json,
    wait_for_job_status,
    gdrive_to_download_url,
    get_json,
    validate_json_response,
    generate_test_id,
    retry_on_failure,
    format_test_summary
)


class TestLoadEnv:
    """Test the load_env function"""
    
    def test_load_env_basic(self, tmp_path):
        """Test basic environment loading"""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("""
API_KEY=test-key-123
BASE_URL=https://api.example.com
# This is a comment
DEBUG=true
""")
        
        # Load environment
        env_vars = load_env(str(env_file))
        
        assert "API_KEY" in env_vars
        assert env_vars["API_KEY"] == "test-key-123"
        assert env_vars["BASE_URL"] == "https://api.example.com"
        assert env_vars["DEBUG"] == "true"
    
    def test_load_env_with_required_vars(self, tmp_path):
        """Test loading with required variables validation"""
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=test-key\nBASE_URL=http://localhost")
        
        # Should succeed with all required vars present
        env_vars = load_env(str(env_file), required_vars=["API_KEY", "BASE_URL"])
        assert env_vars["API_KEY"] == "test-key"
        
    def test_load_env_missing_required_vars(self, tmp_path):
        """Test that missing required vars raise an error"""
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=test-key")
        
        # Should fail with missing required var
        with pytest.raises(ValueError, match="Missing required environment variables"):
            load_env(str(env_file), required_vars=["API_KEY", "MISSING_VAR"])
    
    def test_load_env_file_not_found(self):
        """Test that non-existent file raises error"""
        with pytest.raises(FileNotFoundError):
            load_env("nonexistent.env")


class TestPostJson:
    """Test the post_json function"""
    
    @patch('requests.post')
    def test_post_json_basic(self, mock_post):
        """Test basic JSON POST request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        response = post_json(
            "https://api.example.com/test",
            {"key": "value"},
            api_key="test-key"
        )
        
        assert response.status_code == 200
        mock_post.assert_called_once()
        
        # Check headers were set correctly
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["headers"]["X-API-Key"] == "test-key"
        assert call_kwargs["headers"]["Content-Type"] == "application/json"
    
    @patch('requests.post')
    def test_post_json_custom_headers(self, mock_post):
        """Test POST with custom headers"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        response = post_json(
            "https://api.example.com/test",
            {"data": "test"},
            headers={"X-Custom": "header-value"}
        )
        
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["headers"]["X-Custom"] == "header-value"
    
    @patch('requests.post')
    def test_post_json_error_handling(self, mock_post):
        """Test error handling in POST request"""
        mock_post.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(requests.RequestException):
            post_json("https://api.example.com/test", {})


class TestWaitForJobStatus:
    """Test the wait_for_job_status function"""
    
    @patch('requests.get')
    def test_wait_for_job_success(self, mock_get):
        """Test successful job completion"""
        # First response: processing, second response: completed
        responses = [
            Mock(status_code=200, json=lambda: {"status": "processing"}),
            Mock(status_code=200, json=lambda: {"status": "completed", "response": "data"})
        ]
        mock_get.side_effect = responses
        
        with patch('time.sleep'):  # Skip actual waiting
            status, data, elapsed = wait_for_job_status(
                "job-123",
                "https://api.example.com",
                api_key="test-key",
                poll_interval=0.1
            )
        
        assert status == "completed"
        assert data["response"] == "data"
        assert mock_get.call_count == 2
    
    @patch('requests.get')
    def test_wait_for_job_failure(self, mock_get):
        """Test job failure detection"""
        mock_response = Mock(
            status_code=200,
            json=lambda: {"status": "failed", "error": "Processing failed"}
        )
        mock_get.return_value = mock_response
        
        status, data, elapsed = wait_for_job_status(
            "job-456",
            "https://api.example.com"
        )
        
        assert status == "failed"
        assert "error" in data
    
    @patch('requests.get')
    @patch('time.time')
    @patch('time.sleep')
    def test_wait_for_job_timeout(self, mock_sleep, mock_time, mock_get):
        """Test job timeout"""
        # Simulate time passing
        mock_time.side_effect = [0, 0, 301, 301]  # Start at 0, timeout at 301
        
        mock_response = Mock(
            status_code=200,
            json=lambda: {"status": "processing"}
        )
        mock_get.return_value = mock_response
        
        status, data, elapsed = wait_for_job_status(
            "job-789",
            "https://api.example.com",
            timeout=300
        )
        
        assert status == "timeout"
        assert "timed out" in data["message"]
    
    def test_wait_for_job_invalid_id(self):
        """Test that empty job_id raises error"""
        with pytest.raises(ValueError, match="job_id is required"):
            wait_for_job_status("", "https://api.example.com")


class TestGdriveToDownloadUrl:
    """Test the gdrive_to_download_url function"""
    
    def test_gdrive_file_url(self):
        """Test conversion of file/d/ URL format"""
        url = "https://drive.google.com/file/d/1ABC123DEF456/view?usp=sharing"
        result = gdrive_to_download_url(url)
        assert result == "https://drive.google.com/uc?export=download&id=1ABC123DEF456"
    
    def test_gdrive_open_url(self):
        """Test conversion of open?id= URL format"""
        url = "https://drive.google.com/open?id=1ABC123DEF456"
        result = gdrive_to_download_url(url)
        assert result == "https://drive.google.com/uc?export=download&id=1ABC123DEF456"
    
    def test_gdrive_uc_url(self):
        """Test conversion of uc?id= URL format"""
        url = "https://drive.google.com/uc?id=1ABC123DEF456&export=view"
        result = gdrive_to_download_url(url)
        assert result == "https://drive.google.com/uc?export=download&id=1ABC123DEF456"
    
    def test_google_docs_url(self):
        """Test conversion of Google Docs URL"""
        url = "https://docs.google.com/document/d/1ABC123DEF456/edit"
        result = gdrive_to_download_url(url)
        assert result == "https://drive.google.com/uc?export=download&id=1ABC123DEF456"
    
    def test_google_sheets_url(self):
        """Test conversion of Google Sheets URL"""
        url = "https://docs.google.com/spreadsheets/d/1ABC123DEF456/edit#gid=0"
        result = gdrive_to_download_url(url)
        assert result == "https://drive.google.com/uc?export=download&id=1ABC123DEF456"
    
    def test_invalid_url(self):
        """Test that invalid URLs raise error"""
        with pytest.raises(ValueError, match="Not a valid Google Drive URL"):
            gdrive_to_download_url("https://example.com/file.pdf")
    
    def test_empty_url(self):
        """Test that empty URL raises error"""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            gdrive_to_download_url("")
    
    def test_url_without_file_id(self):
        """Test that URL without file ID raises error"""
        with pytest.raises(ValueError, match="Could not extract file ID"):
            gdrive_to_download_url("https://drive.google.com/")


class TestGetJson:
    """Test the get_json function"""
    
    @patch('requests.get')
    def test_get_json_basic(self, mock_get):
        """Test basic JSON GET request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response
        
        response = get_json(
            "https://api.example.com/data",
            params={"q": "search"},
            api_key="test-key"
        )
        
        assert response.status_code == 200
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["headers"]["X-API-Key"] == "test-key"
        assert call_kwargs["params"]["q"] == "search"


class TestValidateJsonResponse:
    """Test the validate_json_response function"""
    
    def test_validate_success(self):
        """Test successful validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "data": "test"}
        
        data = validate_json_response(
            mock_response,
            expected_status=200,
            required_fields=["status", "data"]
        )
        
        assert data["status"] == "ok"
        assert data["data"] == "test"
    
    def test_validate_wrong_status(self):
        """Test validation with wrong status code"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        with pytest.raises(AssertionError, match="Expected status"):
            validate_json_response(mock_response, expected_status=200)
    
    def test_validate_missing_fields(self):
        """Test validation with missing required fields"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        
        with pytest.raises(AssertionError, match="Missing required fields"):
            validate_json_response(
                mock_response,
                required_fields=["status", "missing_field"]
            )


class TestGenerateTestId:
    """Test the generate_test_id function"""
    
    def test_generate_test_id_format(self):
        """Test that generated IDs have correct format"""
        test_id = generate_test_id("mytest")
        assert test_id.startswith("mytest_")
        parts = test_id.split("_")
        assert len(parts) == 3
        assert parts[1].isdigit()  # Timestamp
        assert len(parts[2]) == 8  # UUID part
    
    def test_generate_test_id_uniqueness(self):
        """Test that generated IDs are unique"""
        ids = [generate_test_id() for _ in range(10)]
        assert len(set(ids)) == 10  # All unique


class TestRetryOnFailure:
    """Test the retry_on_failure function"""
    
    def test_retry_success_first_try(self):
        """Test function that succeeds on first try"""
        mock_func = Mock(return_value="success")
        
        result = retry_on_failure(mock_func, max_attempts=3)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    @patch('time.sleep')
    def test_retry_success_after_failures(self, mock_sleep):
        """Test function that succeeds after failures"""
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        result = retry_on_failure(mock_func, max_attempts=3, delay=0.1)
        
        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('time.sleep')
    def test_retry_all_attempts_fail(self, mock_sleep):
        """Test function that fails all attempts"""
        mock_func = Mock(side_effect=Exception("Always fails"))
        
        with pytest.raises(Exception, match="Always fails"):
            retry_on_failure(mock_func, max_attempts=3, delay=0.1)
        
        assert mock_func.call_count == 3


class TestFormatTestSummary:
    """Test the format_test_summary function"""
    
    def test_format_all_passed(self):
        """Test formatting with all tests passed"""
        summary = format_test_summary(passed=10, failed=0, duration=5.5)
        assert "10 passed" in summary
        assert "10 total" in summary  # Should show 10 total
        assert "5.50s" in summary
    
    def test_format_mixed_results(self):
        """Test formatting with mixed results"""
        summary = format_test_summary(passed=5, failed=2, skipped=1, duration=10.0)
        assert "5 passed" in summary
        assert "2 failed" in summary
        assert "1 skipped" in summary
        assert "8 total" in summary
    
    def test_format_no_duration(self):
        """Test formatting without duration"""
        summary = format_test_summary(passed=3, failed=1)
        assert "4 total" in summary
        assert "s" not in summary.split("total")[1]  # No duration shown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
