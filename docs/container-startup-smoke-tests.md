# Container Startup Smoke Tests

This document describes the container startup smoke tests that ensure the Docker container starts up properly without any special environment variables and provides expected functionality.

## Overview

The container startup smoke tests verify that:

1. **Docker image builds without errors**
2. **Container starts without special environment variables**
3. **Health endpoints return expected responses**
4. **Security headers are properly configured**
5. **Error handling works correctly**
6. **Authenticated endpoints handle missing credentials appropriately**

## Test Implementation

### GitHub Actions Workflow

**File**: `.github/workflows/container-startup-smoke.yml`

The GitHub Actions workflow runs automatically on:
- Push to `main`, `develop`, or `staging` branches
- Pull requests to `main` or `develop` branches
- Manual trigger via `workflow_dispatch`

**Key Steps**:
1. Build Docker image with no push (tagged as `local/sync-scribe-studio-api:startup-smoke`)
2. Run container with **no environment variables** - just port mapping
3. Wait for `/health` endpoint to return 200 status
4. Test basic endpoints (root, health, detailed health)
5. Test security headers
6. Test authenticated endpoints behavior without credentials
7. Clean up container

### Local Test Script

**File**: `scripts/container-startup-smoke.sh`

A comprehensive shell script that can be run locally to test container startup behavior.

**Usage**:
```bash
# Make script executable
chmod +x scripts/container-startup-smoke.sh

# Run the tests
./scripts/container-startup-smoke.sh
```

**Requirements**:
- Docker installed and running
- `curl` command available
- `jq` command available (optional, but recommended for JSON validation)

## Test Scenarios

### 1. Container Startup Without Environment Variables

The container is started with **no special environment variables**, only port mapping:

```bash
docker run -d --name startup-smoke \\
  -p 8080:8080 \\
  local/sync-scribe-studio-api:startup-smoke
```

This tests that the application:
- Boots successfully without required environment variables
- Handles missing secrets gracefully
- Provides basic health monitoring capabilities

### 2. Health Endpoint Tests

#### `/health` Endpoint
- **Expected**: Always returns 200 status
- **Expected Response**: 
  ```json
  {
    "status": "healthy",
    "service": "Sync Scribe Studio API",
    "version": "...",
    "timestamp": 1234567890,
    "port": "8080"
  }
  ```

#### `/health/detailed` Endpoint
- **Expected**: Returns 200 or 503 status depending on missing environment variables
- **200 Response**: When system can operate in degraded mode
- **503 Response**: When critical services are unavailable
- **Expected Response** (both cases):
  ```json
  {
    "status": "healthy|degraded",
    "timestamp": 1234567890,
    "version": "...",
    "warnings": [...],
    "environment_variables": {...},
    "missing_dependencies": {...}
  }
  ```

#### Root `/` Endpoint
- **Expected**: Always returns 200 status
- **Expected Response**:
  ```json
  {
    "service": "Sync Scribe Studio API",
    "version": "...",
    "status": "running",
    "endpoints": {...},
    "documentation": "...",
    "build_info": {...}
  }
  ```

### 3. Security Headers Tests

The application must return required security headers on all endpoints:

- **X-Content-Type-Options**: `nosniff`
- **X-Frame-Options**: `DENY`
- **X-XSS-Protection**: `1; mode=block`
- **Strict-Transport-Security**: Present (exact value may vary)

### 4. Authentication Endpoint Tests

Authenticated endpoints (like `/v1/media/youtube/info`) should properly handle requests without credentials:

- **Expected Status Codes**: 401 (Unauthorized), 503 (Service Unavailable), 404 (Not Found), or 405 (Method Not Allowed)
- **Not Expected**: 200, 500, or other unexpected codes

### 5. Error Handling Tests

- **404 for Invalid Endpoints**: Requesting non-existent endpoints should return 404
- **Graceful JSON Error Responses**: Error responses should be properly formatted JSON

## Expected Behavior Without Environment Variables

Based on Step 3 of the project (Remove Hard Requirements for Environment Variables), the application should:

### ✅ Working Features (200 Status)
- **Basic Health Monitoring**: `/health` endpoint always available
- **Service Information**: Root endpoint provides service metadata
- **Security Features**: Security headers and basic error handling
- **Graceful Degradation**: App boots and reports degraded status instead of crashing

### ⚠️ Degraded Features (503 Status or Warnings)
- **Authentication Services**: May return 503 when `API_KEY`/`DB_TOKEN` not configured
- **AI Features**: May be unavailable when `OPENAI_API_KEY` not configured
- **Detailed Health**: May report degraded status with warnings about missing optional variables

### ❌ Expected Failures
- **Authenticated Endpoints**: Should properly reject requests (401/503 status)
- **Features Requiring External Services**: Should fail gracefully with appropriate error codes

## Troubleshooting

### Container Fails to Start
1. Check Docker is running: `docker info`
2. Check Dockerfile syntax and dependencies
3. Review container logs: `docker logs startup-smoke`

### Health Endpoints Return Unexpected Status
1. Verify environment variable handling in health modules
2. Check application startup logs for errors
3. Ensure graceful degradation is implemented correctly

### Security Headers Missing
1. Verify security middleware is properly configured
2. Check Flask/framework security configuration
3. Ensure headers are set in all response paths

### Authentication Tests Fail
1. Verify authentication middleware handles missing credentials
2. Check that 503 status is returned when authentication is unavailable
3. Ensure proper error response format

## Continuous Integration

The smoke tests run automatically on every push and pull request to guard against regressions that could:
- Break container startup without environment variables
- Remove required security headers
- Change health endpoint behavior
- Break graceful degradation features

This ensures the application maintains its resilience and development-friendly characteristics while preserving production security and functionality.

## Local Development

For local development, you can run the smoke tests to verify your changes:

```bash
# Build and test the container locally
./scripts/container-startup-smoke.sh

# Or run specific tests manually
docker build -t test-image .
docker run -d --name test-container -p 8080:8080 test-image
curl http://localhost:8080/health
docker rm -f test-container
```

This helps ensure your changes don't break the container's ability to start without special configuration.
