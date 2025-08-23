# API Testing Guide

## Why Test?
Testing ensures your API endpoints work correctly before deploying to production. This guide provides comprehensive test scripts that cover all 23 API endpoints locally and in the cloud with just one command.

## Quick Start

### Prerequisites
1. Python 3.8+ installed
2. API running locally or deployed to cloud
3. `.env` file with your API key

### Setup (One-time)
```bash
# Install dependencies
pip install requests python-dotenv

# Copy the example environment file
cp .env.example .env

# Edit .env and configure these required settings:
# - API_KEY=your-api-key-here
# - LOCAL_BASE_URL=http://localhost:8080  
# - CLOUD_BASE_URL=https://your-api-url.run.app

# Optional: Add cloud storage credentials (for higher pass rates)
# GCP Storage (recommended):
# - GCP_PROJECT_ID=your-project-id
# - GCP_BUCKET_NAME=your-bucket-name  
# - GCP_SA_EMAIL=service-account@project.iam.gserviceaccount.com
# - GCP_SA_CREDENTIALS={json_key_content}  # Decoded service account JSON

# S3 Compatible Storage:
# - S3_ACCESS_KEY=your-access-key
# - S3_SECRET_KEY=your-secret-key
# - S3_ENDPOINT_URL=https://your-endpoint
# - S3_REGION=your-region
# - S3_BUCKET_NAME=your-bucket
```

## Running Tests

### Test Local API
```bash
# From project root
python tests/test_local.py
```

This will:
- Test all 23 endpoints on your local API
- Show PASS/FAIL for each endpoint
- Save results to `tests/results/local_test_summary.txt`
- Detect if operations are synchronous (fast) or asynchronous
- Expected pass rate: 
  - 30-40% without cloud storage configured
  - 60-70% with cloud storage configured (GCP/S3)

### Test Cloud API
```bash
# From project root
python tests/test_cloud.py
```

This will:
- Test all 23 endpoints on your cloud API
- Show PASS/FAIL for each endpoint
- Save results to `tests/results/cloud_test_summary.txt`
- Handle longer timeouts for cloud responses (30s vs 10s local)
- Expected pass rate:
  - 85-90% typical (some endpoints may have specific requirements)
  - 95-100% with all features configured

## Understanding Results

### Console Output
```
Testing: Health Check... ✓ PASS
Testing: Media Metadata... ✓ PASS (sync)
Testing: Video Caption... ✗ FAIL - Expected 200, got 404
```

- `✓ PASS` - Endpoint works as expected
- `✗ FAIL` - Endpoint returned unexpected status code
- `(sync)` - Operation completed synchronously (<1 second)

### Report Files

**Summary File** (`tests/results/local_test_summary.txt`):
```
PASS: Health Check (/health)
PASS: Media Metadata (/v1/media/metadata)
FAIL: Job Status (/v1/toolkit/job_status)

Pass Rate: 66.7% (2/3)
```

**Detailed Report** (`tests/results/local_test_results.json`):
Contains response times, error messages, and full test details.

## Common Issues & Solutions

### "Cannot reach API"
- **Local**: Make sure your API is running (`docker-compose up` or `docker run`)
- **Cloud**: Check your internet connection and CLOUD_BASE_URL in `.env`

### "Authentication failed (401)"
- Check your API_KEY in `.env` matches your actual API key
- Ensure no quotes around the API key: `API_KEY=key123` not `API_KEY="key123"`

### "Expected 200, got 404"
- The endpoint doesn't exist or has a different path
- Check if the endpoint is implemented in your API
- Some endpoints like `/v1/media/feedback` may not be deployed

### "500 Internal Server Error (Local)"
- Often due to missing cloud storage configuration (S3/GCS)
- Check Docker logs: `docker logs <container-name>`
- Common for video/audio endpoints without storage setup

### "405 Method Not Allowed"
- Endpoint exists but wrong HTTP method (GET vs POST)
- Check the endpoint documentation

## Adding New Endpoints

To test a new endpoint, edit the test script and add to the `ENDPOINTS` list:

### Example: Add a new endpoint

1. Open `tests/test_local.py` (and `tests/test_cloud.py`)
2. Find the `ENDPOINTS = [` section
3. Add your endpoint:

```python
ENDPOINTS = [
    # ... existing endpoints ...
    {
        "name": "My New Feature",
        "method": "POST",
        "path": "/v1/my/new/endpoint",
        "auth": True,  # Requires API key?
        "payload": {
            "param1": "value1",
            "param2": "value2"
        },
        "expected": 200  # or [200, 201] for multiple valid codes
    }
]
```

### Endpoint Configuration Fields

- `name`: Human-readable name for the test
- `method`: HTTP method (GET or POST)
- `path`: API endpoint path
- `auth`: Boolean - whether API key is required
- `payload`: JSON body for POST requests (or None)
- `params`: Query parameters for GET requests (optional)
- `expected`: Expected HTTP status code(s)
  - Single code: `200`
  - Multiple valid codes: `[200, 201, 202]`

### Testing Different Scenarios

#### GET Endpoint with Query Parameters
```python
{
    "name": "Search Items",
    "method": "GET",
    "path": "/v1/items/search",
    "auth": True,
    "params": {"query": "test", "limit": 10},
    "payload": None,
    "expected": 200
}
```

#### POST Endpoint with File URL
```python
{
    "name": "Process Video",
    "method": "POST",
    "path": "/v1/video/process",
    "auth": True,
    "payload": {
        "video_url": "https://example.com/video.mp4",
        "format": "mp4"
    },
    "expected": [200, 202]  # 200 if sync, 202 if async
}
```

#### Endpoint That Might Not Exist
```python
{
    "name": "Beta Feature",
    "method": "POST",
    "path": "/v1/beta/feature",
    "auth": True,
    "payload": {"test": "data"},
    "expected": [200, 404]  # 404 is acceptable if not deployed
}
```

## Advanced Usage

### Custom Environment
```bash
# Use different .env file
API_KEY=test-key LOCAL_BASE_URL=http://localhost:3000 python tests/test_local.py
```

### CI/CD Integration
The test scripts exit with code 0 on success, 1 on failure:
```yaml
# GitHub Actions example
- name: Run API Tests
  run: |
    python tests/test_local.py
    python tests/test_cloud.py
```

## File Structure
```
tests/
├── test_local.py          # Local API test script
├── test_cloud.py          # Cloud API test script
└── results/               # Test results (auto-created)
    ├── local_test_summary.txt
    ├── local_test_results.json
    ├── cloud_test_summary.txt
    └── cloud_test_results.json
```

## Best Practices

1. **Run local tests first** - Faster and helps catch issues early
2. **Keep `.env` secure** - Don't commit API keys to git
3. **One report per run** - Scripts overwrite previous results to prevent bloat
4. **Check sync detection** - Operations marked `(sync)` complete fast enough to not need job tracking

## Comprehensive Endpoint Coverage

The test scripts cover all 23 API endpoints:

### Health & Toolkit (5 endpoints)
- `/health` - Health check
- `/v1/toolkit/authenticate` - API key validation  
- `/v1/toolkit/test` - API functionality test
- `/v1/toolkit/job/status` - Check single job status
- `/v1/toolkit/jobs/status` - Batch job status check

### Audio Processing (1 endpoint)
- `/v1/audio/concatenate` - Combine multiple audio files

### Code Execution (1 endpoint)
- `/v1/code/execute/python` - Execute Python code remotely

### FFmpeg Operations (1 endpoint)
- `/v1/ffmpeg/compose` - Complex media processing with FFmpeg

### Image Processing (2 endpoints)
- `/v1/image/convert/video` - Convert static image to video
- `/v1/image/screenshot/webpage` - Capture webpage screenshots

### Media Operations (6 endpoints)
- `/v1/media/convert` - Convert between media formats
- `/v1/media/convert/mp3` - Convert to MP3 audio
- `/v1/media/feedback` - Media feedback interface
- `/v1/media/transcribe` - Transcribe/translate audio
- `/v1/media/silence` - Detect silence intervals
- `/v1/media/metadata` - Extract media metadata

### S3 Storage (1 endpoint)
- `/v1/s3/upload` - Stream upload to S3 storage

### Video Processing (6 endpoints)
- `/v1/video/caption` - Add captions to video
- `/v1/video/concatenate` - Combine multiple videos
- `/v1/video/thumbnail` - Extract video thumbnail
- `/v1/video/cut` - Cut video segments
- `/v1/video/split` - Split video into parts
- `/v1/video/trim` - Trim video to time range

## Known Issues & Current Failures

### Cloud API (87% pass rate)
Remaining failures typically include:
- **Toolkit: Job Status** - May have code bug with undefined variable
- **Audio: Concatenate** - FFmpeg processing issues
- **Image: Convert to Video** - URL extension detection problems

### Local API (39% pass rate without full GCP setup)
Common failures without cloud storage:
- Most video/audio processing endpoints require GCP/S3 storage
- `GCP_SA_CREDENTIALS` must be the decoded JSON, not base64
- Docker containers need environment variables passed at runtime

### Setting up GCP Credentials for Docker
```bash
# If you have a base64 encoded key:
echo $GCP_SA_KEY_BASE64 | base64 -d > service-account.json

# Run Docker with GCP credentials:
docker run -d --name api-test -p 8080:8080 \
  -e API_KEY=$API_KEY \
  -e GCP_BUCKET_NAME=$GCP_BUCKET_NAME \
  -e GCP_SA_CREDENTIALS="$(cat service-account.json)" \
  your-image:tag
```

## Support

For issues or questions:
1. Check endpoint implementation in your API code
2. Verify environment variables in `.env`
3. Review error messages in test results JSON files
4. Check Docker logs for local deployment issues
5. Verify cloud storage configuration for media endpoints
