#!/usr/bin/env python3
"""
Unit Tests for YouTube URL Validation

Following TDD principles - these tests define the expected behavior
for URL validation functionality.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from routes.v1.media.youtube import make_youtube_request, is_youtube_service_healthy
import requests


class TestYouTubeURLValidation:
    """Test suite for YouTube URL validation"""

    @pytest.fixture
    def valid_youtube_urls(self):
        """Fixture providing valid YouTube URLs for testing"""
        return [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy4TyTh4u1-LovHRYHcwb3T",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        ]

    @pytest.fixture
    def invalid_youtube_urls(self):
        """Fixture providing invalid YouTube URLs for testing"""
        return [
            "https://example.com/video",
            "https://vimeo.com/123456789",
            "not_a_url",
            "",
            None,
            "javascript:alert('xss')",
            "file:///etc/passwd",
            "ftp://malicious.com/file",
            "https://youtube.evil.com/watch?v=fake"
        ]

    @pytest.fixture
    def rick_roll_url(self):
        """Fixture providing the Rick Roll YouTube URL for testing"""
        return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_valid_youtube_urls_are_accepted(self, valid_youtube_urls):
        """Test that valid YouTube URLs are properly accepted"""
        # This test will help us implement URL validation logic
        for url in valid_youtube_urls:
            # When we implement validate_youtube_url, it should return True
            # validate_youtube_url should be created in utils/validation.py
            assert self._is_valid_youtube_url(url), f"URL should be valid: {url}"

    def test_invalid_youtube_urls_are_rejected(self, invalid_youtube_urls):
        """Test that invalid YouTube URLs are properly rejected"""
        for url in invalid_youtube_urls:
            assert not self._is_valid_youtube_url(url), f"URL should be invalid: {url}"

    def test_rick_roll_url_is_valid(self, rick_roll_url):
        """Test that the Rick Roll URL (used in manual tests) is valid"""
        assert self._is_valid_youtube_url(rick_roll_url), "Rick Roll URL should be valid"

    def test_url_extraction_from_various_formats(self):
        """Test URL extraction from different YouTube URL formats"""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ&t=30", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_video_id in test_cases:
            video_id = self._extract_video_id(url)
            assert video_id == expected_video_id, f"Failed to extract video ID from {url}"

    def test_url_sanitization(self):
        """Test URL sanitization to prevent malicious inputs"""
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "ftp://malicious.com/file",
        ]
        
        for url in malicious_urls:
            with pytest.raises((ValueError, SecurityError)):
                self._sanitize_url(url)

    def test_url_normalization(self):
        """Test URL normalization for consistent processing"""
        test_cases = [
            ("https://youtu.be/dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ]
        
        for input_url, expected_normalized in test_cases:
            normalized = self._normalize_youtube_url(input_url)
            assert normalized == expected_normalized, f"Failed to normalize {input_url}"

    # Helper methods that define the expected interface
    # These will guide our implementation
    
    def _is_valid_youtube_url(self, url):
        """Helper method to validate YouTube URLs - to be implemented"""
        if not url or not isinstance(url, str):
            return False
        
        # Basic YouTube URL pattern matching
        import re
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://youtu\.be/[\w-]+',
            r'https?://(?:m\.)?youtube\.com/watch\?v=[\w-]+',
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)

    def _extract_video_id(self, url):
        """Helper method to extract video ID - to be implemented"""
        import re
        
        patterns = [
            r'watch\?v=([^&\n]+)',
            r'youtu\.be/([^?\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def _sanitize_url(self, url):
        """Helper method to sanitize URLs - to be implemented"""
        if not url or not isinstance(url, str):
            raise ValueError("Invalid URL")
        
        # Check for dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'file:', 'ftp:']
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                raise SecurityError(f"Dangerous protocol detected: {protocol}")
        
        return url

    def _normalize_youtube_url(self, url):
        """Helper method to normalize YouTube URLs - to be implemented"""
        video_id = self._extract_video_id(url)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return url


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class TestMakeYouTubeRequest:
    """Test suite for YouTube microservice request handling"""

    @patch('routes.v1.media.youtube.requests.post')
    def test_make_youtube_request_success(self, mock_post):
        """Test successful YouTube microservice request"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": {"videoId": "test"}}
        mock_post.return_value = mock_response
        
        # Act
        response = make_youtube_request('/test', {"url": "https://youtube.com/watch?v=test"})
        
        # Assert
        assert response.status_code == 200
        assert mock_post.called

    @patch('routes.v1.media.youtube.requests.post')
    def test_make_youtube_request_retry_logic(self, mock_post):
        """Test retry logic for failed requests"""
        # Arrange - first two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        
        mock_post.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]
        
        # Act
        with patch('routes.v1.media.youtube.time.sleep'):  # Skip sleep in tests
            response = make_youtube_request('/test', {"url": "test"})
        
        # Assert
        assert response.status_code == 200
        assert mock_post.call_count == 3

    @patch('routes.v1.media.youtube.requests.post')
    def test_make_youtube_request_all_retries_fail(self, mock_post):
        """Test behavior when all retry attempts fail"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        # Act & Assert
        with patch('routes.v1.media.youtube.time.sleep'):  # Skip sleep in tests
            with pytest.raises(requests.RequestException):
                make_youtube_request('/test', {"url": "test"})

    @patch('routes.v1.media.youtube.requests.post')
    def test_make_youtube_request_timeout_handling(self, mock_post):
        """Test timeout handling in YouTube requests"""
        # Arrange
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        # Act & Assert
        with patch('routes.v1.media.youtube.time.sleep'):  # Skip sleep in tests
            with pytest.raises(requests.RequestException):
                make_youtube_request('/test', {"url": "test"})

    @patch('routes.v1.media.youtube.make_youtube_request')
    def test_is_youtube_service_healthy_success(self, mock_request):
        """Test service health check when service is healthy"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        # Act
        result = is_youtube_service_healthy()
        
        # Assert
        assert result is True
        mock_request.assert_called_with('/healthz', method='GET')

    @patch('routes.v1.media.youtube.make_youtube_request')
    def test_is_youtube_service_healthy_failure(self, mock_request):
        """Test service health check when service is unhealthy"""
        # Arrange
        mock_request.side_effect = Exception("Service unavailable")
        
        # Act
        result = is_youtube_service_healthy()
        
        # Assert
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__])
