# Tests Directory - Quick Start Guide

## Setup Steps

### 1. Navigate to project root
```bash
cd /path/to/sync-scribe-studio-api
```

### 2. Set up virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 3. Install dependencies
```bash
pip install -r test-requirements.txt
```

### 4. Configure .env (CRITICAL - tests will fail without this)
```bash
cp .env.example .env
# Edit .env and set:
API_KEY=your_actual_api_key
LOCAL_BASE_URL=http://localhost:8080
CLOUD_BASE_URL=https://your-cloud-api.com
```

### 5. Start Docker (for local tests)
```bash
docker-compose up -d
# Wait ~10 seconds for initialization
```

### 6. Run tests
```bash
# Unit tests
pytest tests/ -v

# Local endpoint tests with async (recommended)
python tests/local_test_endpoints.py --async

# Cloud tests (no Docker needed)
python tests/cloud_test_endpoints.py
```

⚠️ **IMPORTANT**: 
- `.env` MUST be configured or ALL tests will fail
- Docker MUST be running for local tests
- Use `--async` flag for complete testing (adds buffer time)
- Check `docker-compose logs -f` if tests fail

## Structure
- `test_*.py` - Test files (pytest automatically discovers these)
- Group related tests in descriptive files
- Mirror source structure when appropriate

## Naming Conventions
- Test files: `test_<feature>.py` (e.g., `test_security_unit.py`)
- Test functions: `test_<scenario>()` (e.g., `test_valid_email()`)
- Test classes: `Test<Feature>` (e.g., `TestAuthentication`)

## Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_security_unit.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v
```

## Best Practices
- Write tests FIRST (Red-Green-Refactor cycle)
- Aim for >80% code coverage
- Critical paths must have 100% coverage
- Mock external dependencies
- Use descriptive test names and docstrings
- Test edge cases and error conditions

## Endpoint Testing Scripts

### 1. `local_test_endpoints.py`
Tests API endpoints on a local instance (typically running in Docker).

**Features:**
- Docker container management
- Webhook server for async testing
- Health check validation
- JUnit XML and JSON report generation

**Usage:**
```bash
# Basic local testing
python tests/local_test_endpoints.py

# With Docker management
python tests/local_test_endpoints.py --docker

# With async webhook testing
python tests/local_test_endpoints.py --async

# Full test with Docker
python tests/local_test_endpoints.py --docker --async --stop-docker
```

### 2. `cloud_test_endpoints.py`
Tests API endpoints on cloud deployment with exponential back-off polling.

**Features:**
- Reads `CLOUD_BASE_URL` and `API_KEY` from `.env`
- Exponential back-off polling for async jobs
- Optional webhook support
- Separate cloud report generation (`cloud_report.xml`)

**Usage:**
```bash
# Basic cloud testing with polling
python tests/cloud_test_endpoints.py

# With webhook instead of polling
python tests/cloud_test_endpoints.py --webhook

# With custom webhook URL
python tests/cloud_test_endpoints.py --webhook-url https://your-webhook.ngrok.io/webhook

# Disable polling (for sync endpoints only)
python tests/cloud_test_endpoints.py --no-polling

# Custom max polling attempts
python tests/cloud_test_endpoints.py --max-polls 20
```

## Configuration

Both endpoint testing scripts read configuration from `.env` file:

```env
# For local testing
LOCAL_BASE_URL=http://localhost:8080

# For cloud testing
CLOUD_BASE_URL=https://your-cloud-api.com

# API authentication
API_KEY=your_api_key_here
```

## Async Job Handling

### Local Testing
- Uses webhook server on port 5555
- Docker containers can reach it via `host.docker.internal:5555`

### Cloud Testing
- **Default**: Uses exponential back-off polling
  - Initial delay: 1 second
  - Max delay: 60 seconds
  - Default max attempts: 10
- **Webhook Mode**: Provide accessible webhook URL
  - Use ngrok or similar for local webhook servers
  - Or provide a public webhook endpoint

## Exponential Back-off Algorithm

The cloud script implements intelligent polling:
1. Initial poll after 1 second
2. Each subsequent delay doubles (with jitter)
3. Maximum delay capped at 60 seconds
4. Stops when job completes, fails, or max attempts reached

Example polling sequence:
- Attempt 1: 1.0s delay
- Attempt 2: 2.5s delay
- Attempt 3: 5.3s delay
- Attempt 4: 11.1s delay
- Attempt 5: 22.7s delay
- ...continues until completion or timeout

## Test Reports

Reports are generated in the `reports/` directory:

### Local Testing
- `junit_report_TIMESTAMP.xml` - JUnit format for CI/CD
- `test_report_TIMESTAMP.json` - Detailed JSON report

### Cloud Testing
- `cloud_report.xml` - Latest cloud test results (JUnit)
- `cloud_report_TIMESTAMP.xml` - Timestamped cloud results
- `cloud_test_report_TIMESTAMP.json` - Detailed JSON report

## Endpoints Tested

Both scripts test the following endpoints:
- `/health` - Health check
- `/v1/toolkit/authenticate` - Authentication
- `/v1/toolkit/test` - API setup verification
- `/v1/toolkit/job_status` - Single job status
- `/v1/toolkit/jobs_status` - Multiple job statuses
- `/v1/video/caption` - Video captioning (async)
- `/v1/video/trim` - Video trimming (async)
- `/v1/video/thumbnail` - Thumbnail generation (async)
- `/v1/media/metadata` - Media metadata extraction (async)
- `/v1/image/screenshot_webpage` - Webpage screenshot (async)
