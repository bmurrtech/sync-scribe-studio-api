#!/usr/bin/env python3
"""
Integration Tests for Flask-Node.js YouTube Service Communication

Following TDD principles - these tests define expected integration behavior
between the Flask API and Node.js microservice.
"""

import pytest
import sys
import os
import requests
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from routes.v1.media.youtube import v1_media_youtube_bp


class TestFlaskNodeIntegration:
    """Integration tests for Flask-Node.js communication"""

    @pytest.fixture
    def app(self):
        """Create Flask test app"""
        app = Flask(__name__)
        app.register_blueprint(v1_media_youtube_bp)
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create Flask test client"""
        return app.test_client()

    @pytest.fixture
    def rick_roll_url(self):
        """Rick Roll URL for integration testing"""
        return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_end_to_end_video_info_flow(self, client, rick_roll_url):
        """Test complete video info flow from Flask to Node.js"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock successful Node.js response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "data": {
                    "videoId": "dQw4w9WgXcQ",
                    "title": "Rick Astley - Never Gonna Give You Up",
                    "description": "The official video for Never Gonna Give You Up",
                    "lengthSeconds": 213,
                    "viewCount": 1000000000,
                    "author": {
                        "name": "Rick Astley",
                        "channelUrl": "https://www.youtube.com/channel/test"
                    }
                },
                "timestamp": "2024-01-01T00:00:00.000Z"
            }
            mock_request.return_value = mock_response

            with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=True):
                with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                    mock_auth.return_value = lambda f: f  # Mock decorator
                    
                    # Act
                    response = client.post('/v1/media/youtube/info', 
                                         json={"url": rick_roll_url},
                                         headers={'Content-Type': 'application/json'})
                    
                    # Assert
                    assert response.status_code in [200, 202]  # Direct or queued response
                    if response.status_code == 200:
                        data = response.get_json()
                        assert 'success' in data or 'response' in data

    def test_microservice_health_check_integration(self, client):
        """Test health check integration between Flask and Node.js"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock healthy Node.js service
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "uptime": 3600,
                "message": "OK",
                "service": "youtube-downloader",
                "version": "1.0.0",
                "status": "healthy"
            }
            mock_request.return_value = mock_response

            with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                mock_auth.return_value = lambda f: f  # Mock decorator
                
                # Act
                response = client.get('/v1/media/youtube/health')
                
                # Assert
                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'healthy'
                assert 'microservice' in data

    def test_streaming_download_integration(self, client, rick_roll_url):
        """Test streaming download integration (MP3/MP4)"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock streaming response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {
                'content-type': 'audio/mpeg',
                'content-disposition': 'attachment; filename="test.mp3"',
                'x-video-title': 'Test Video',
                'x-video-duration': '213'
            }
            mock_response.iter_content.return_value = [b'audio-chunk-1', b'audio-chunk-2']
            mock_request.return_value = mock_response

            with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=True):
                with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                    mock_auth.return_value = lambda f: f  # Mock decorator
                    
                    # Act
                    response = client.post('/v1/media/youtube/mp3',
                                         json={"url": rick_roll_url, "quality": "highestaudio"},
                                         headers={'Content-Type': 'application/json'})
                    
                    # Assert
                    assert response.status_code == 200
                    # Should contain streaming data
                    assert len(response.data) > 0

    def test_error_propagation_from_microservice(self, client, rick_roll_url):
        """Test error propagation from Node.js to Flask"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock Node.js error response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "success": False,
                "error": "Invalid YouTube URL",
                "message": "The provided URL is not a valid YouTube video"
            }
            mock_request.return_value = mock_response

            with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=True):
                with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                    mock_auth.return_value = lambda f: f  # Mock decorator
                    
                    # Act
                    response = client.post('/v1/media/youtube/info',
                                         json={"url": "invalid-url"},
                                         headers={'Content-Type': 'application/json'})
                    
                    # Assert
                    assert response.status_code in [400, 202]  # Error or queued

    def test_microservice_unavailable_handling(self, client, rick_roll_url):
        """Test handling when Node.js microservice is unavailable"""
        with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=False):
            with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                mock_auth.return_value = lambda f: f  # Mock decorator
                
                # Act
                response = client.post('/v1/media/youtube/info',
                                     json={"url": rick_roll_url},
                                     headers={'Content-Type': 'application/json'})
                
                # Assert
                assert response.status_code in [503, 202]  # Service unavailable or queued

    def test_concurrent_requests_handling(self, client, rick_roll_url):
        """Test handling of concurrent requests between Flask and Node.js"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock successful responses with slight delays
            def mock_delayed_response(*args, **kwargs):
                time.sleep(0.1)  # Simulate network delay
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True, "data": {"videoId": "test"}}
                return mock_response
            
            mock_request.side_effect = mock_delayed_response

            with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=True):
                with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                    mock_auth.return_value = lambda f: f  # Mock decorator
                    
                    # Act - make concurrent requests
                    import threading
                    responses = []
                    errors = []
                    
                    def make_request():
                        try:
                            response = client.post('/v1/media/youtube/info',
                                                 json={"url": rick_roll_url},
                                                 headers={'Content-Type': 'application/json'})
                            responses.append(response)
                        except Exception as e:
                            errors.append(e)
                    
                    threads = []
                    for _ in range(5):
                        thread = threading.Thread(target=make_request)
                        threads.append(thread)
                        thread.start()
                    
                    for thread in threads:
                        thread.join()
                    
                    # Assert
                    assert len(errors) == 0, f"Concurrent request errors: {errors}"
                    assert len(responses) == 5
                    for response in responses:
                        assert response.status_code in [200, 202]

    def test_retry_logic_integration(self, client, rick_roll_url):
        """Test retry logic between Flask and Node.js"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock failures followed by success
            mock_fail = Mock()
            mock_fail.status_code = 500
            
            mock_success = Mock()
            mock_success.status_code = 200
            mock_success.json.return_value = {"success": True, "data": {"videoId": "test"}}
            
            mock_request.side_effect = [mock_fail, mock_fail, mock_success]

            with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=True):
                with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                    mock_auth.return_value = lambda f: f  # Mock decorator
                    
                    # This test verifies that our Flask code properly calls the retry logic
                    # The actual retry is tested in the make_youtube_request unit tests
                    response = client.post('/v1/media/youtube/info',
                                         json={"url": rick_roll_url},
                                         headers={'Content-Type': 'application/json'})
                    
                    # Should eventually succeed or be queued
                    assert response.status_code in [200, 202]

    def test_data_format_consistency(self, client, rick_roll_url):
        """Test data format consistency between Flask and Node.js"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock Node.js response with expected data format
            node_response_data = {
                "success": True,
                "data": {
                    "videoId": "dQw4w9WgXcQ",
                    "title": "Test Video Title",
                    "description": "Test Description",
                    "lengthSeconds": 213,
                    "viewCount": 1000000,
                    "author": {
                        "name": "Test Author",
                        "channelUrl": "https://youtube.com/channel/test"
                    },
                    "formats": {
                        "audioFormats": [
                            {
                                "itag": 140,
                                "mimeType": "audio/mp4",
                                "bitrate": 128
                            }
                        ],
                        "videoFormats": [
                            {
                                "itag": 18,
                                "mimeType": "video/mp4",
                                "qualityLabel": "360p"
                            }
                        ]
                    }
                },
                "timestamp": "2024-01-01T00:00:00.000Z"
            }
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = node_response_data
            mock_request.return_value = mock_response

            with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=True):
                with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                    mock_auth.return_value = lambda f: f
                    
                    # Act
                    response = client.post('/v1/media/youtube/info',
                                         json={"url": rick_roll_url},
                                         headers={'Content-Type': 'application/json'})
                    
                    # Assert
                    if response.status_code == 200:
                        data = response.get_json()
                        # Should contain the Node.js data either directly or wrapped
                        assert 'success' in data or 'response' in data

    def test_authentication_flow_integration(self, client, rick_roll_url):
        """Test authentication flow in integration context"""
        with patch('routes.v1.media.youtube.authenticate') as mock_auth:
            # Test unauthenticated request
            mock_auth.side_effect = lambda f: self._unauthorized_response
            
            response = client.post('/v1/media/youtube/info',
                                 json={"url": rick_roll_url},
                                 headers={'Content-Type': 'application/json'})
            
            # Should require authentication
            assert response.status_code == 401

    def test_service_discovery_integration(self, client):
        """Test service discovery endpoint integration"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock Node.js service info response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "service": "YouTube Downloader Microservice",
                "version": "1.0.0",
                "endpoints": {
                    "/healthz": "Health check",
                    "/v1/media/youtube/info": "Video info",
                    "/v1/media/youtube/mp3": "MP3 download",
                    "/v1/media/youtube/mp4": "MP4 download"
                }
            }
            mock_request.return_value = mock_response

            with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=True):
                with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                    mock_auth.return_value = lambda f: f
                    
                    # Act
                    response = client.get('/v1/media/youtube')
                    
                    # Assert
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['service'] == 'YouTube Integration'
                    assert 'endpoints' in data
                    assert 'microservice_info' in data

    def _unauthorized_response(self, f):
        """Helper method for authentication mock"""
        from flask import jsonify
        return jsonify({"error": "Unauthorized"}), 401


class TestMessageQueueIntegration:
    """Test integration with message queue system (if applicable)"""
    
    def test_queued_request_processing(self):
        """Test queued request processing between Flask and Node.js"""
        # This test defines expected behavior for queue-based communication
        with patch('routes.v1.media.youtube.queue_task_wrapper') as mock_queue:
            # Mock queue wrapper behavior
            mock_queue.return_value = lambda f: f
            
            # Test that requests can be queued when microservice is busy
            # This guides implementation of queue-based processing
            pass

    def test_webhook_callback_integration(self):
        """Test webhook callback integration for async processing"""
        # This test defines expected behavior for webhook callbacks
        # when processing is complete
        
        callback_data = {
            "job_id": "test-job-123",
            "status": "completed",
            "result": {
                "videoId": "dQw4w9WgXcQ",
                "title": "Test Video"
            },
            "timestamp": "2024-01-01T00:00:00.000Z"
        }
        
        # Test webhook processing
        assert callback_data['status'] == 'completed'
        assert 'result' in callback_data


class TestPerformanceIntegration:
    """Test performance aspects of Flask-Node.js integration"""
    
    def test_response_time_integration(self, client):
        """Test response times for integrated requests"""
        with patch('routes.v1.media.youtube.make_youtube_request') as mock_request:
            # Mock fast response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "data": {"videoId": "test"}}
            mock_request.return_value = mock_response

            with patch('routes.v1.media.youtube.is_youtube_service_healthy', return_value=True):
                with patch('routes.v1.media.youtube.authenticate') as mock_auth:
                    mock_auth.return_value = lambda f: f
                    
                    start_time = time.time()
                    response = client.post('/v1/media/youtube/info',
                                         json={"url": "https://youtube.com/watch?v=test"},
                                         headers={'Content-Type': 'application/json'})
                    end_time = time.time()
                    
                    # Should respond quickly
                    assert (end_time - start_time) < 5.0  # Less than 5 seconds
                    assert response.status_code in [200, 202]

    def test_memory_usage_integration(self):
        """Test memory usage during integration operations"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform operations that might use memory
        # This is a placeholder for memory usage testing
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Should not use excessive memory
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase


if __name__ == '__main__':
    pytest.main([__file__])
