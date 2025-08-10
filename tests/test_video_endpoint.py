"""
Unit and Integration tests for Video endpoints
Following TDD: RED -> GREEN -> REFACTOR approach
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests_mock
import jsonschema
from datetime import datetime

class TestVideoTrimEndpoint:
    """Tests for /v1/video/trim endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_trim_video_success(self, mock_requests, base_url, api_key, sample_media_urls, validate_schema):
        """RED: Test successful video trimming"""
        # Arrange
        endpoint = "/v1/video/trim"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "trim-job-123",
                "response": "https://storage.example.com/trimmed-video.mp4",
                "message": "success",
                "run_time": 4.5,
                "queue_time": 0,
                "total_time": 4.5
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "start_time": 10.0,
                "end_time": 30.0
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert validate_schema(data, "success_response")
        assert data["response"].endswith(".mp4")
        assert data["message"] == "success"
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_trim_invalid_times(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test trim with invalid time values"""
        # Arrange
        endpoint = "/v1/video/trim"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Invalid time range: start_time must be less than end_time"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "start_time": 30.0,
                "end_time": 10.0
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid time range" in data["message"]
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_trim_missing_parameters(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test trim without required parameters"""
        # Arrange
        endpoint = "/v1/video/trim"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Missing required fields: start_time, end_time"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"media_url": sample_media_urls["video"]}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Missing required fields" in data["message"]
    
    @pytest.mark.integration
    @pytest.mark.video
    def test_trim_integration(self, integration_helper, sample_media_urls):
        """GREEN: Integration test for video trimming"""
        # Act
        response = integration_helper.make_request(
            "POST",
            "/v1/video/trim",
            json={
                "media_url": sample_media_urls["video"],
                "start_time": 5,
                "end_time": 15
            }
        )
        
        # Assert
        assert response.status_code in [200, 202]
        data = response.json()
        
        if response.status_code == 202:
            # Job was queued
            job_id = data["job_id"]
            result = integration_helper.poll_job_status(job_id)
            assert result is not None
            assert result.get("job_status") == "done"
        else:
            assert data["response"].startswith("http")
            assert data["response"].endswith((".mp4", ".avi", ".mov", ".mkv"))


class TestVideoCutEndpoint:
    """Tests for /v1/video/cut endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_cut_video_segments(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test cutting multiple segments from video"""
        # Arrange
        endpoint = "/v1/video/cut"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "cut-job-123",
                "response": {
                    "segments": [
                        "https://storage.example.com/segment1.mp4",
                        "https://storage.example.com/segment2.mp4"
                    ],
                    "count": 2,
                    "total_duration": 20.0
                },
                "message": "success",
                "run_time": 6.5,
                "queue_time": 0,
                "total_time": 6.5
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "segments": [
                    {"start": 0, "end": 10},
                    {"start": 20, "end": 30}
                ]
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "segments" in result
        assert len(result["segments"]) == 2
        assert all(url.startswith("http") for url in result["segments"])
        assert result["count"] == 2
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_cut_overlapping_segments(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test cut with overlapping segments"""
        # Arrange
        endpoint = "/v1/video/cut"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Invalid segments: overlapping time ranges detected"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "segments": [
                    {"start": 0, "end": 15},
                    {"start": 10, "end": 20}
                ]
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "overlapping" in data["message"]


class TestVideoSplitEndpoint:
    """Tests for /v1/video/split endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_split_by_duration(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test splitting video by duration"""
        # Arrange
        endpoint = "/v1/video/split"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "split-job-123",
                "response": {
                    "parts": [
                        "https://storage.example.com/part1.mp4",
                        "https://storage.example.com/part2.mp4",
                        "https://storage.example.com/part3.mp4"
                    ],
                    "count": 3,
                    "duration_per_part": 30
                },
                "message": "success",
                "run_time": 7.2,
                "queue_time": 0,
                "total_time": 7.2
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "split_duration": 30  # Split every 30 seconds
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "parts" in result
        assert len(result["parts"]) == 3
        assert result["duration_per_part"] == 30
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_split_by_count(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test splitting video into N parts"""
        # Arrange
        endpoint = "/v1/video/split"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "split-count-123",
                "response": {
                    "parts": [
                        "https://storage.example.com/part1.mp4",
                        "https://storage.example.com/part2.mp4",
                        "https://storage.example.com/part3.mp4",
                        "https://storage.example.com/part4.mp4"
                    ],
                    "count": 4,
                    "avg_duration": 15.0
                },
                "message": "success",
                "run_time": 8.0,
                "queue_time": 0,
                "total_time": 8.0
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "split_count": 4  # Split into 4 equal parts
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert len(result["parts"]) == 4
        assert result["count"] == 4
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_split_invalid_parameters(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test split with both duration and count specified"""
        # Arrange
        endpoint = "/v1/video/split"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Cannot specify both split_duration and split_count"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "split_duration": 30,
                "split_count": 4
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Cannot specify both" in data["message"]


class TestVideoConcatenateEndpoint:
    """Tests for /v1/video/concatenate endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_concatenate_videos_success(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test concatenating multiple videos"""
        # Arrange
        endpoint = "/v1/video/concatenate"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "concat-job-123",
                "response": {
                    "output_url": "https://storage.example.com/concatenated.mp4",
                    "total_duration": 120.5,
                    "input_count": 3,
                    "resolution": "1920x1080",
                    "format": "mp4"
                },
                "message": "success",
                "run_time": 10.5,
                "queue_time": 0,
                "total_time": 10.5
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_urls": [
                    sample_media_urls["video"],
                    sample_media_urls["video"],
                    sample_media_urls["video"]
                ]
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "output_url" in result
        assert result["output_url"].endswith(".mp4")
        assert result["input_count"] == 3
        assert result["total_duration"] > 0
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_concatenate_with_transition(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test concatenating with transition effects"""
        # Arrange
        endpoint = "/v1/video/concatenate"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "concat-trans-123",
                "response": {
                    "output_url": "https://storage.example.com/concatenated-fade.mp4",
                    "total_duration": 125.0,
                    "input_count": 2,
                    "transition": "fade",
                    "transition_duration": 1.0
                },
                "message": "success",
                "run_time": 12.0,
                "queue_time": 0,
                "total_time": 12.0
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_urls": [
                    sample_media_urls["video"],
                    sample_media_urls["video"]
                ],
                "transition": "fade",
                "transition_duration": 1.0
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert result["transition"] == "fade"
        assert result["transition_duration"] == 1.0
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_concatenate_empty_list(self, mock_requests, base_url, api_key):
        """RED: Test concatenate with empty media list"""
        # Arrange
        endpoint = "/v1/video/concatenate"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "At least 2 media files required for concatenation"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"media_urls": []}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "At least 2" in data["message"]
    
    @pytest.mark.integration
    @pytest.mark.video
    def test_concatenate_integration(self, integration_helper, sample_media_urls):
        """GREEN: Integration test for video concatenation"""
        # Act
        response = integration_helper.make_request(
            "POST",
            "/v1/video/concatenate",
            json={
                "media_urls": [
                    sample_media_urls["video"],
                    sample_media_urls["video"]
                ]
            }
        )
        
        # Assert
        assert response.status_code in [200, 202]
        data = response.json()
        
        if response.status_code == 202:
            job_id = data["job_id"]
            result = integration_helper.poll_job_status(job_id)
            assert result is not None
        else:
            assert "response" in data
            if isinstance(data["response"], dict):
                assert "output_url" in data["response"]
            else:
                assert data["response"].startswith("http")


class TestVideoThumbnailEndpoint:
    """Tests for /v1/video/thumbnail endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_extract_thumbnail_at_time(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test extracting thumbnail at specific time"""
        # Arrange
        endpoint = "/v1/video/thumbnail"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "thumb-job-123",
                "response": {
                    "thumbnail_url": "https://storage.example.com/thumbnail.jpg",
                    "timestamp": 15.0,
                    "width": 1920,
                    "height": 1080,
                    "format": "jpg"
                },
                "message": "success",
                "run_time": 1.2,
                "queue_time": 0,
                "total_time": 1.2
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "timestamp": 15.0
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "thumbnail_url" in result
        assert result["thumbnail_url"].endswith((".jpg", ".png"))
        assert result["timestamp"] == 15.0
        assert result["width"] > 0
        assert result["height"] > 0
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_extract_multiple_thumbnails(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test extracting multiple thumbnails"""
        # Arrange
        endpoint = "/v1/video/thumbnail"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "multi-thumb-123",
                "response": {
                    "thumbnails": [
                        {"url": "https://storage.example.com/thumb1.jpg", "timestamp": 5.0},
                        {"url": "https://storage.example.com/thumb2.jpg", "timestamp": 15.0},
                        {"url": "https://storage.example.com/thumb3.jpg", "timestamp": 25.0}
                    ],
                    "count": 3,
                    "format": "jpg"
                },
                "message": "success",
                "run_time": 2.5,
                "queue_time": 0,
                "total_time": 2.5
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "timestamps": [5.0, 15.0, 25.0]
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "thumbnails" in result
        assert len(result["thumbnails"]) == 3
        assert result["count"] == 3
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_thumbnail_custom_size(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test extracting thumbnail with custom dimensions"""
        # Arrange
        endpoint = "/v1/video/thumbnail"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "custom-thumb-123",
                "response": {
                    "thumbnail_url": "https://storage.example.com/thumbnail-640x480.jpg",
                    "width": 640,
                    "height": 480,
                    "format": "jpg"
                },
                "message": "success",
                "run_time": 1.5,
                "queue_time": 0,
                "total_time": 1.5
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "width": 640,
                "height": 480
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert result["width"] == 640
        assert result["height"] == 480


class TestVideoCaptionEndpoint:
    """Tests for /v1/video/caption_video endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_add_captions_to_video(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test adding captions to video"""
        # Arrange
        endpoint = "/v1/video/caption_video"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "caption-job-123",
                "response": {
                    "output_url": "https://storage.example.com/video-with-captions.mp4",
                    "caption_format": "srt",
                    "language": "en",
                    "caption_count": 45,
                    "duration": 120.0
                },
                "message": "success",
                "run_time": 25.0,
                "queue_time": 0,
                "total_time": 25.0
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "language": "en",
                "model": "base"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "output_url" in result
        assert result["output_url"].endswith(".mp4")
        assert result["language"] == "en"
        assert result["caption_count"] > 0
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_caption_with_custom_style(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test adding captions with custom styling"""
        # Arrange
        endpoint = "/v1/video/caption_video"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "styled-caption-123",
                "response": {
                    "output_url": "https://storage.example.com/video-styled-captions.mp4",
                    "style": {
                        "font": "Arial",
                        "size": 24,
                        "color": "white",
                        "background": "black",
                        "position": "bottom"
                    },
                    "caption_count": 30
                },
                "message": "success",
                "run_time": 28.0,
                "queue_time": 0,
                "total_time": 28.0
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "style": {
                    "font": "Arial",
                    "size": 24,
                    "color": "white",
                    "background": "black",
                    "position": "bottom"
                }
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "style" in result
        assert result["style"]["font"] == "Arial"
        assert result["style"]["size"] == 24
    
    @pytest.mark.unit
    @pytest.mark.video
    def test_caption_with_existing_srt(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test adding captions from existing SRT file"""
        # Arrange
        endpoint = "/v1/video/caption_video"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "srt-caption-123",
                "response": {
                    "output_url": "https://storage.example.com/video-with-srt.mp4",
                    "caption_source": "external",
                    "caption_format": "srt",
                    "caption_count": 50
                },
                "message": "success",
                "run_time": 8.0,
                "queue_time": 0,
                "total_time": 8.0
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "srt_url": "https://example.com/captions.srt"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert result["caption_source"] == "external"
        assert result["caption_format"] == "srt"
    
    @pytest.mark.integration
    @pytest.mark.video
    @pytest.mark.slow
    def test_caption_integration(self, integration_helper, sample_media_urls):
        """GREEN: Integration test for video captioning"""
        # Act
        response = integration_helper.make_request(
            "POST",
            "/v1/video/caption_video",
            json={
                "media_url": sample_media_urls["video"],
                "language": "en",
                "model": "tiny"  # Use tiny model for speed
            }
        )
        
        # Assert
        assert response.status_code in [200, 202]
        data = response.json()
        
        if response.status_code == 202:
            job_id = data["job_id"]
            result = integration_helper.poll_job_status(job_id, max_attempts=20)
            assert result is not None
            assert result.get("job_status") == "done"
