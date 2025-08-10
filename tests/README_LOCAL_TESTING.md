# Local API Endpoint Testing

## Overview
The `local_test_endpoints.py` script provides comprehensive testing for the Sync Scribe Studio API endpoints with support for Docker container management, async webhook testing, and detailed reporting.

## Features
- ✅ Automated endpoint testing with sample media URLs
- ✅ Docker container management (optional)
- ✅ Async webhook flow testing
- ✅ JUnit XML and JSON report generation
- ✅ Rate limiting validation
- ✅ Authentication testing
- ✅ Response schema validation
- ✅ Colored terminal output for better readability

## Prerequisites
```bash
# Install required dependencies
pip install python-dotenv flask werkzeug requests
```

## Configuration
Create a `.env` file in the project root with the following variables:
```bash
API_KEY=your_api_key_here
LOCAL_BASE_URL=http://localhost:8080  # Default if not specified
```

## Usage

### Basic Testing (Local API Running)
```bash
# Test endpoints with local API already running
python tests/local_test_endpoints.py
```

### With Docker Container Management
```bash
# Start Docker container if not running and run tests
python tests/local_test_endpoints.py --docker

# Stop container after tests
python tests/local_test_endpoints.py --docker --stop-docker
```

### Async Webhook Testing
```bash
# Enable webhook server for async endpoint testing
python tests/local_test_endpoints.py --async

# Combine with Docker
python tests/local_test_endpoints.py --docker --async
```

### Custom Configuration
```bash
# Override base URL and API key
python tests/local_test_endpoints.py --base-url http://localhost:3000 --api-key test-key-123

# Specify custom report directory
python tests/local_test_endpoints.py --report-dir custom_reports
```

## Command Line Options
- `--async` - Enable async webhook testing with local Flask server
- `--docker` - Start Docker container if not running
- `--stop-docker` - Stop Docker container after tests complete
- `--base-url URL` - Override base URL from .env
- `--api-key KEY` - Override API key from .env
- `--report-dir DIR` - Directory for test reports (default: reports)

## Test Coverage
The script tests the following endpoints:

### Core Endpoints
- `GET /health` - Health check (no auth required)
- `GET /v1/toolkit/authenticate` - Authentication test
- `GET /v1/toolkit/test` - API setup verification
- `GET /v1/toolkit/job_status` - Single job status
- `POST /v1/toolkit/jobs_status` - Multiple job statuses

### Media Processing Endpoints
- `POST /v1/video/caption` - Add captions to video
- `POST /v1/video/trim` - Trim video duration
- `POST /v1/video/thumbnail` - Generate video thumbnail
- `POST /v1/media/metadata` - Extract media metadata
- `POST /v1/image/screenshot_webpage` - Screenshot webpage

## Reports
After running tests, the following reports are generated in the `reports/` directory:

### JUnit XML Report
- **File**: `junit_report_YYYYMMDD_HHMMSS.xml`
- **Use**: Compatible with CI/CD systems (Jenkins, GitLab CI, etc.)
- **Contains**: Test results, timing, failure details

### JSON Report
- **File**: `test_report_YYYYMMDD_HHMMSS.json`
- **Use**: Machine-readable format for custom processing
- **Contains**: Detailed test results, request/response data

## Test Results Interpretation

### Console Output Colors
- 🟢 **Green**: Test passed
- 🔴 **Red**: Test failed or error
- 🟡 **Yellow**: Warning or additional information
- 🔵 **Blue**: Headers and section titles
- 🟦 **Cyan**: Test in progress

### Exit Codes
- `0` - All tests passed
- `1` - One or more tests failed

## Docker Container Management
The script can automatically manage the Docker container:

1. **Check Status**: Verifies if container is running
2. **Start Container**: Creates/starts container with .env configuration
3. **Health Check**: Waits for API to be ready
4. **Run Tests**: Executes full test suite
5. **Stop Container**: Optional cleanup after tests

### Docker Image
Default image: `bmurrtech/sync-scribe-studio:latest`

To use a custom image, modify the `DockerManager` class in the script:
```python
docker_manager = DockerManager(image_name="your-custom-image:tag")
```

## Webhook Testing
When `--async` flag is enabled:

1. **Local Server**: Starts Flask server on port 5555
2. **Webhook URL**: Automatically added to test payloads
3. **Callback Capture**: Records all webhook callbacks
4. **Results Display**: Shows captured callbacks after tests

### Webhook Server Endpoints
- `POST /webhook` - Receives callback data
- `GET /health` - Server health check

## Troubleshooting

### API Connection Issues
```bash
# Check if API is running
curl http://localhost:8080/health

# Start with Docker
python tests/local_test_endpoints.py --docker
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Docker Issues
```bash
# Check Docker status
docker ps

# Remove old container
docker rm -f sync-scribe-studio-test

# Pull latest image
docker pull bmurrtech/sync-scribe-studio:latest
```

### Permission Issues
```bash
# Make script executable
chmod +x tests/local_test_endpoints.py
```

## Adding New Endpoints
To add new endpoints to test, edit the `ENDPOINT_MATRIX` in the script:

```python
{
    "path": "/v1/your/endpoint",
    "method": "POST",
    "auth_required": True,
    "payload": {
        "param1": "value1",
        "param2": "value2"
    },
    "description": "Your endpoint description"
}
```

## CI/CD Integration
Example GitHub Actions workflow:

```yaml
- name: Run API Tests
  run: |
    python tests/local_test_endpoints.py --docker --stop-docker
    
- name: Upload Test Reports
  uses: actions/upload-artifact@v2
  with:
    name: test-reports
    path: reports/
```

## Support
For issues or questions, please check:
1. API logs: `docker logs sync-scribe-studio-test`
2. Test reports in `reports/` directory
3. Console output for detailed error messages
