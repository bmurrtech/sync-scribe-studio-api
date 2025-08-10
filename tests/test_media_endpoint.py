"""
Unit and Integration tests for Media endpoints
Following TDD: RED -> GREEN -> REFACTOR approach
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
import requests_mock
import jsonschema
from datetime import datetime
import tempfile
import os

class TestMediaMetadataEndpoint:
    """Tests for /v1/media/metadata endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_metadata_extraction_success(self, mock_requests, base_url, api_key, sample_media_urls, validate_schema):
        """RED: Test successful metadata extraction from media file"""
        # Arrange
        endpoint = "/v1/media/metadata"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "meta-job-123",
                "response": {
                    "filesize": 5242880,
                    "duration": 120.5,
                    "video_codec": "h264",
                    "audio_codec": "aac",
                    "width": 1920,
                    "height": 1080,
                    "frame_rate": 29.97,
                    "video_bitrate": 2500000,
                    "audio_bitrate": 128000,
                    "format": "mp4",
                    "streams": 2
                },
                "message": "success",
                "run_time": 0.8,
                "queue_time": 0,
                "total_time": 0.8
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"media_url": sample_media_urls["video"]}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert validate_schema(data, "success_response")
        
        metadata = data["response"]
        assert validate_schema(metadata, "media_metadata")
        assert metadata["filesize"] > 0
        assert metadata["duration"] > 0
        assert metadata["width"] == 1920
        assert metadata["height"] == 1080
        assert metadata["video_codec"] == "h264"
        assert metadata["audio_codec"] == "aac"
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_metadata_invalid_url(self, mock_requests, base_url, api_key, validate_schema):
        """RED: Test metadata extraction with invalid media URL"""
        # Arrange
        endpoint = "/v1/media/metadata"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Invalid media URL or file not accessible"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"media_url": "not-a-valid-url"}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert validate_schema(data, "error_response")
        assert "Invalid media URL" in data["message"]
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_metadata_missing_url(self, mock_requests, base_url, api_key):
        """RED: Test metadata endpoint requires media_url"""
        # Arrange
        endpoint = "/v1/media/metadata"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Missing required field: media_url"
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
        assert "media_url" in data["message"]
    
    @pytest.mark.integration
    @pytest.mark.media
    def test_metadata_integration(self, integration_helper, sample_media_urls, validate_schema):
        """GREEN: Integration test for metadata extraction"""
        # Act
        response = integration_helper.make_request(
            "POST",
            "/v1/media/metadata",
            json={"media_url": sample_media_urls["video"]}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert validate_schema(data, "success_response")
        
        metadata = data["response"]
        assert "filesize" in metadata
        assert "duration" in metadata
        assert metadata["filesize"] > 0
        assert metadata["duration"] > 0


class TestMediaDownloadEndpoint:
    """Tests for /v1/media/download endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_download_success(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test successful media download"""
        # Arrange
        endpoint = "/v1/media/download"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "download-job-123",
                "response": "https://storage.example.com/downloaded-media.mp4",
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
            json={"media_url": sample_media_urls["video"]}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["response"].startswith("http")
        assert data["response"].endswith(".mp4")
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_download_with_webhook(self, mock_requests, base_url, api_key, webhook_url, sample_media_urls):
        """RED: Test media download with webhook callback"""
        # Arrange
        endpoint = "/v1/media/download"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 202,
                "job_id": "download-job-456",
                "message": "processing",
                "queue_length": 1
            },
            status_code=202
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["video"],
                "webhook_url": webhook_url
            }
        )
        
        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["code"] == 202
        assert data["message"] == "processing"
        assert "job_id" in data
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_download_unsupported_format(self, mock_requests, base_url, api_key):
        """RED: Test download with unsupported media format"""
        # Arrange
        endpoint = "/v1/media/download"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Unsupported media format or URL"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={"media_url": "https://example.com/file.xyz"}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported" in data["message"]


class TestMediaTranscribeEndpoint:
    """Tests for /v1/media/transcribe and /v1/media/media_transcribe endpoints"""
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_transcribe_audio_success(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test successful audio transcription"""
        # Arrange
        endpoint = "/v1/media/media_transcribe"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "transcribe-job-123",
                "response": {
                    "text": "This is the transcribed text from the audio file.",
                    "language": "en",
                    "duration": 30.5,
                    "segments": [
                        {
                            "start": 0.0,
                            "end": 5.0,
                            "text": "This is the transcribed"
                        },
                        {
                            "start": 5.0,
                            "end": 10.0,
                            "text": "text from the audio file."
                        }
                    ],
                    "confidence": 0.95
                },
                "message": "success",
                "run_time": 15.3,
                "queue_time": 0,
                "total_time": 15.3
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["audio"],
                "model": "base",
                "language": "en"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        
        transcript = data["response"]
        assert "text" in transcript
        assert "language" in transcript
        assert "segments" in transcript
        assert len(transcript["segments"]) > 0
        assert transcript["language"] == "en"
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_transcribe_with_srt_output(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test transcription with SRT subtitle format output"""
        # Arrange
        endpoint = "/v1/media/media_transcribe"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "transcribe-srt-123",
                "response": {
                    "text": "Full transcription text",
                    "srt_url": "https://storage.example.com/subtitles.srt",
                    "vtt_url": "https://storage.example.com/subtitles.vtt",
                    "language": "en"
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
                "media_url": sample_media_urls["audio"],
                "output_format": "srt",
                "model": "base"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        transcript = data["response"]
        assert "srt_url" in transcript
        assert transcript["srt_url"].endswith(".srt")
        assert "text" in transcript
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_transcribe_invalid_model(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test transcription with invalid model"""
        # Arrange
        endpoint = "/v1/media/media_transcribe"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Invalid model: ultra. Valid models are: tiny, base, small, medium, large"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["audio"],
                "model": "ultra"
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid model" in data["message"]
    
    @pytest.mark.integration
    @pytest.mark.media
    @pytest.mark.slow
    def test_transcribe_integration(self, integration_helper, sample_media_urls):
        """GREEN: Integration test for media transcription"""
        # Act
        response = integration_helper.make_request(
            "POST",
            "/v1/media/media_transcribe",
            json={
                "media_url": sample_media_urls["audio"],
                "model": "tiny",  # Use tiny model for faster testing
                "language": "en"
            }
        )
        
        # Assert
        assert response.status_code in [200, 202]
        data = response.json()
        
        if response.status_code == 202:
            # Job was queued, poll for result
            job_id = data["job_id"]
            result = integration_helper.poll_job_status(job_id)
            assert result is not None
            assert result.get("job_status") == "done"
        else:
            # Direct response
            assert "response" in data
            assert "text" in data["response"]


class TestMediaConvertEndpoint:
    """Tests for /v1/media/convert endpoints"""
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_convert_to_mp3_success(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test successful conversion to MP3"""
        # Arrange
        endpoint = "/v1/media/convert/media_to_mp3"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "convert-mp3-123",
                "response": "https://storage.example.com/converted.mp3",
                "message": "success",
                "run_time": 3.5,
                "queue_time": 0,
                "total_time": 3.5
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
                "bitrate": "192k"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["response"].endswith(".mp3")
        assert data["message"] == "success"
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_convert_general_format(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test general media format conversion"""
        # Arrange
        endpoint = "/v1/media/convert/media_convert"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "convert-gen-123",
                "response": "https://storage.example.com/converted.webm",
                "message": "success",
                "run_time": 5.2,
                "queue_time": 0,
                "total_time": 5.2
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
                "output_format": "webm",
                "video_codec": "vp9",
                "audio_codec": "opus"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["response"].endswith(".webm")
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_convert_invalid_format(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test conversion with invalid output format"""
        # Arrange
        endpoint = "/v1/media/convert/media_convert"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Invalid output format: xyz"
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
                "output_format": "xyz"
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid output format" in data["message"]


class TestMediaSilenceEndpoint:
    """Tests for /v1/media/silence endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_detect_silence_success(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test successful silence detection in media"""
        # Arrange
        endpoint = "/v1/media/silence"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "silence-job-123",
                "response": {
                    "silence_periods": [
                        {"start": 0.0, "end": 2.5, "duration": 2.5},
                        {"start": 15.3, "end": 17.8, "duration": 2.5},
                        {"start": 45.0, "end": 48.2, "duration": 3.2}
                    ],
                    "total_silence_duration": 8.2,
                    "media_duration": 60.0,
                    "silence_percentage": 13.67
                },
                "message": "success",
                "run_time": 1.8,
                "queue_time": 0,
                "total_time": 1.8
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "media_url": sample_media_urls["audio"],
                "threshold": -30,  # dB threshold
                "min_duration": 0.5  # minimum silence duration in seconds
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        silence_data = data["response"]
        assert "silence_periods" in silence_data
        assert "total_silence_duration" in silence_data
        assert "silence_percentage" in silence_data
        assert len(silence_data["silence_periods"]) > 0
        assert silence_data["total_silence_duration"] > 0
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_remove_silence(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test removing silence from media"""
        # Arrange
        endpoint = "/v1/media/silence"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "remove-silence-123",
                "response": {
                    "output_url": "https://storage.example.com/no-silence.mp3",
                    "original_duration": 60.0,
                    "new_duration": 51.8,
                    "removed_duration": 8.2,
                    "silence_periods_removed": 3
                },
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
                "media_url": sample_media_urls["audio"],
                "action": "remove",
                "threshold": -30,
                "min_duration": 0.5
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "output_url" in result
        assert "original_duration" in result
        assert "new_duration" in result
        assert result["new_duration"] < result["original_duration"]


class TestMediaFeedbackEndpoint:
    """Tests for /v1/media/feedback endpoint"""
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_submit_feedback_success(self, mock_requests, base_url, api_key):
        """RED: Test successful feedback submission"""
        # Arrange
        endpoint = "/v1/media/feedback"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "message": "Feedback submitted successfully",
                "feedback_id": "feedback-123"
            },
            status_code=200
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "job_id": "test-job-123",
                "rating": 5,
                "comment": "Excellent transcription quality",
                "type": "transcription"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "successfully" in data["message"]
        assert "feedback_id" in data
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_feedback_invalid_rating(self, mock_requests, base_url, api_key):
        """RED: Test feedback with invalid rating"""
        # Arrange
        endpoint = "/v1/media/feedback"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 400,
                "message": "Invalid rating: must be between 1 and 5"
            },
            status_code=400
        )
        
        # Act
        import requests
        response = requests.post(
            f"{base_url}{endpoint}",
            headers={"X-API-Key": api_key},
            json={
                "job_id": "test-job-123",
                "rating": 10,
                "comment": "Test"
            }
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid rating" in data["message"]


class TestGenerateAssEndpoint:
    """Tests for /v1/media/generate_ass endpoint (Advanced SubStation Alpha subtitles)"""
    
    @pytest.mark.unit
    @pytest.mark.media
    def test_generate_ass_subtitles(self, mock_requests, base_url, api_key, sample_media_urls):
        """RED: Test generating ASS subtitle file"""
        # Arrange
        endpoint = "/v1/media/generate_ass"
        
        mock_requests.post(
            f"{base_url}{endpoint}",
            json={
                "code": 200,
                "job_id": "ass-gen-123",
                "response": {
                    "ass_url": "https://storage.example.com/subtitles.ass",
                    "subtitle_count": 25,
                    "duration": 120.5,
                    "styles": ["Default", "Italic", "Bold"]
                },
                "message": "success",
                "run_time": 18.5,
                "queue_time": 0,
                "total_time": 18.5
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
                "style": "default",
                "font_size": 24
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]
        assert "ass_url" in result
        assert result["ass_url"].endswith(".ass")
        assert "subtitle_count" in result
        assert result["subtitle_count"] > 0
