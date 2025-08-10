"""
Pytest fixtures and shared test configuration
"""

import os
import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests_mock
from faker import Faker
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Faker for test data generation
fake = Faker()

# Test constants
TEST_API_KEY = os.getenv("API_KEY", "test-api-key-12345")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:5555/webhook")

# Sample media URLs for testing
SAMPLE_MEDIA_URLS = {
    "video": "https://example.com/sample.mp4",
    "audio": "https://example.com/sample.mp3",
    "image": "https://example.com/sample.jpg",
    "invalid": "https://example.com/nonexistent.mp4"
}

# JSON Schema definitions for response validation
SCHEMAS = {
    "job_response": {
        "type": "object",
        "required": ["code", "job_id", "message"],
        "properties": {
            "code": {"type": "integer"},
            "job_id": {"type": "string"},
            "message": {"type": "string"},
            "id": {"type": ["string", "null"]},
            "pid": {"type": "integer"},
            "queue_id": {"type": "integer"},
            "queue_length": {"type": "integer"},
            "build_number": {"type": "string"}
        }
    },
    "success_response": {
        "type": "object",
        "required": ["code", "job_id", "response"],
        "properties": {
            "code": {"type": "integer", "enum": [200]},
            "job_id": {"type": "string"},
            "response": {"type": ["string", "object", "array"]},
            "message": {"type": "string"},
            "run_time": {"type": "number", "minimum": 0},
            "queue_time": {"type": "number", "minimum": 0},
            "total_time": {"type": "number", "minimum": 0}
        }
    },
    "error_response": {
        "type": "object",
        "required": ["code", "message"],
        "properties": {
            "code": {"type": "integer", "minimum": 400, "maximum": 599},
            "message": {"type": "string"},
            "job_id": {"type": ["string", "null"]}
        }
    },
    "webhook_response": {
        "type": "object",
        "required": ["endpoint", "code", "job_id"],
        "properties": {
            "endpoint": {"type": "string"},
            "code": {"type": "integer"},
            "job_id": {"type": "string"},
            "response": {"type": ["string", "object", "array", "null"]},
            "message": {"type": "string"},
            "run_time": {"type": "number"},
            "queue_time": {"type": "number"},
            "total_time": {"type": "number"}
        }
    },
    "media_metadata": {
        "type": "object",
        "required": ["filesize", "duration"],
        "properties": {
            "filesize": {"type": "integer", "minimum": 0},
            "duration": {"type": "number", "minimum": 0},
            "video_codec": {"type": ["string", "null"]},
            "audio_codec": {"type": ["string", "null"]},
            "width": {"type": ["integer", "null"]},
            "height": {"type": ["integer", "null"]},
            "frame_rate": {"type": ["number", "null"]},
            "video_bitrate": {"type": ["integer", "null"]},
            "audio_bitrate": {"type": ["integer", "null"]}
        }
    }
}

@pytest.fixture
def api_key():
    """Provide test API key"""
    return TEST_API_KEY

@pytest.fixture
def base_url():
    """Provide base URL for API"""
    return BASE_URL

@pytest.fixture
def webhook_url():
    """Provide webhook URL for async tests"""
    return WEBHOOK_URL

@pytest.fixture
def sample_media_urls():
    """Provide sample media URLs for testing"""
    return SAMPLE_MEDIA_URLS

@pytest.fixture
def mock_requests():
    """Mock requests for unit tests"""
    with requests_mock.Mocker() as m:
        yield m

@pytest.fixture
def mock_flask_app():
    """Create a mock Flask application for testing"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def mock_job_id():
    """Generate a mock job ID"""
    return fake.uuid4()

@pytest.fixture
def mock_webhook_server():
    """Mock webhook server for testing callbacks"""
    server = Mock()
    server.callbacks = []
    server.add_callback = lambda data: server.callbacks.append(data)
    server.get_callbacks = lambda: server.callbacks
    server.clear_callbacks = lambda: server.callbacks.clear()
    return server

@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    # Cleanup
    try:
        os.unlink(f.name)
    except:
        pass

@pytest.fixture
def mock_storage():
    """Mock cloud storage operations"""
    with patch('services.cloud_storage.upload_file') as mock_upload:
        mock_upload.return_value = "https://storage.example.com/test-file.txt"
        yield mock_upload

@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg operations"""
    with patch('ffmpeg.run') as mock_run:
        mock_run.return_value = None
        with patch('ffmpeg.probe') as mock_probe:
            mock_probe.return_value = {
                'streams': [
                    {'codec_type': 'video', 'width': 1920, 'height': 1080},
                    {'codec_type': 'audio', 'sample_rate': '44100'}
                ],
                'format': {'duration': '60.0', 'size': '1000000'}
            }
            yield {'run': mock_run, 'probe': mock_probe}

@pytest.fixture
def mock_whisper():
    """Mock Whisper transcription"""
    with patch('whisper.load_model') as mock_model:
        model_instance = Mock()
        model_instance.transcribe.return_value = {
            'text': 'This is a test transcription',
            'segments': [
                {'start': 0.0, 'end': 2.0, 'text': 'This is'},
                {'start': 2.0, 'end': 4.0, 'text': 'a test transcription'}
            ],
            'language': 'en'
        }
        mock_model.return_value = model_instance
        yield model_instance

@pytest.fixture
def mock_yt_dlp():
    """Mock yt-dlp download operations"""
    with patch('yt_dlp.YoutubeDL') as mock_ytdl:
        instance = Mock()
        instance.extract_info.return_value = {
            'url': 'https://example.com/video.mp4',
            'title': 'Test Video',
            'duration': 120,
            'ext': 'mp4'
        }
        instance.download.return_value = None
        mock_ytdl.return_value = instance
        yield instance

@pytest.fixture
def auth_headers(api_key):
    """Provide authentication headers"""
    return {"X-API-Key": api_key}

@pytest.fixture
def sample_request_data():
    """Provide sample request data for different endpoints"""
    return {
        "media_metadata": {
            "media_url": SAMPLE_MEDIA_URLS["video"]
        },
        "transcribe": {
            "media_url": SAMPLE_MEDIA_URLS["audio"],
            "model": "base",
            "language": "en"
        },
        "video_trim": {
            "media_url": SAMPLE_MEDIA_URLS["video"],
            "start_time": 10,
            "end_time": 30
        },
        "video_concat": {
            "media_urls": [SAMPLE_MEDIA_URLS["video"], SAMPLE_MEDIA_URLS["video"]]
        },
        "ffmpeg_compose": {
            "commands": ["-i", "input.mp4", "-c:v", "libx264", "output.mp4"]
        },
        "s3_upload": {
            "file_url": "https://example.com/file.txt",
            "bucket": "test-bucket",
            "key": "test-key"
        },
        "code_execute": {
            "code": "print('Hello, World!')",
            "language": "python"
        },
        "screenshot": {
            "url": "https://example.com",
            "width": 1920,
            "height": 1080
        }
    }

@pytest.fixture
def mock_job_status():
    """Mock job status tracking"""
    statuses = {}
    
    def log_status(job_id, status_data):
        statuses[job_id] = status_data
    
    def get_status(job_id):
        return statuses.get(job_id, {"status": "not_found"})
    
    with patch('app_utils.log_job_status', side_effect=log_status):
        yield {"log": log_status, "get": get_status, "statuses": statuses}

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables for each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def validate_schema():
    """Helper function to validate JSON against schema"""
    import jsonschema
    
    def validator(data, schema_name):
        schema = SCHEMAS.get(schema_name)
        if not schema:
            raise ValueError(f"Unknown schema: {schema_name}")
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(f"Schema validation failed: {e.message}")
            return False
    
    return validator

@pytest.fixture
def integration_helper():
    """Helper for integration tests"""
    import requests
    
    class IntegrationHelper:
        def __init__(self):
            self.base_url = BASE_URL
            self.api_key = TEST_API_KEY
            self.session = requests.Session()
            self.session.headers.update({"X-API-Key": self.api_key})
        
        def make_request(self, method, endpoint, **kwargs):
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            return response
        
        def poll_job_status(self, job_id, max_attempts=10, delay=1):
            import time
            for _ in range(max_attempts):
                response = self.make_request("GET", f"/v1/toolkit/job_status", 
                                            params={"job_id": job_id})
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") in ["completed", "failed", "error"]:
                        return data
                time.sleep(delay)
            return None
    
    return IntegrationHelper()

@pytest.fixture
def performance_timer():
    """Helper to measure performance"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()
