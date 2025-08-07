# Docker Cloud Run Hardening Documentation

This document outlines the hardened Docker setup for deploying the Sync Scribe Studio API to Google Cloud Run.

## Overview

The Dockerfile has been optimized for Cloud Run deployment with the following key improvements:

1. **Multi-stage build** for minimal production image size
2. **Dynamic port configuration** respecting Cloud Run's `$PORT` environment variable
3. **Cloud Run-friendly health checks** 
4. **Fully stateless container** using tmpfs only
5. **Semantic versioning** using `BUILD_NUMBER`

## Multi-Stage Build Architecture

### Builder Stage
- **Purpose**: Compile FFmpeg and all video processing dependencies
- **Base Image**: `python:3.9-slim`
- **Includes**: All build tools, compilers, and development libraries
- **Output**: Compiled binaries in `/usr/local`

### Final Stage
- **Purpose**: Slim runtime image with only essential components
- **Base Image**: `python:3.9-slim` 
- **Size Goal**: ≤1 GB for optimal Cloud Run performance
- **Copies**: Only runtime artifacts from builder stage

## Key Features

### 1. Port Configuration
The container respects Cloud Run's dynamic port assignment:

```dockerfile
ENV PORT=8080
ENTRYPOINT ["/app/entrypoint.sh"]
```

The entrypoint script automatically uses the `$PORT` environment variable:

```bash
PORT=${PORT:-8080}
exec gunicorn --bind 0.0.0.0:$PORT ...
```

### 2. Health Check Integration
Built-in health check compatible with Cloud Run:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1
```

### 3. Stateless Design
- **Whisper cache**: `/tmp/whisper_cache` (tmpfs)
- **No persistent volumes**: All data in memory/tmpfs
- **Process isolation**: Non-root user (`appuser`)

### 4. Security Hardening
- Non-root user execution
- Minimal attack surface with slim base image
- No unnecessary packages in final image
- Secure file permissions

## Health Endpoints

Three health endpoints are provided:

### Basic Health Check (`/health`)
```json
{
  "status": "healthy",
  "timestamp": 1640995200,
  "version": "200",
  "service": "Sync Scribe Studio API",
  "port": "8080"
}
```

### Detailed Health Check (`/health/detailed`)
```json
{
  "status": "healthy",
  "environment_variables": {...},
  "service_checks": {
    "ffmpeg": "available",
    "whisper_cache": "writable",
    "tmp_disk_space": "1.5GB_free"
  },
  "warnings": []
}
```

### Root Endpoint (`/`)
Service information with available endpoints and documentation links.

## Build Process

### 1. Build Image
```bash
./build-docker.sh [tag-suffix]
```

Example:
```bash
./build-docker.sh                # Production build
./build-docker.sh dev             # Development build  
./build-docker.sh staging         # Staging build
```

### 2. Deploy to Cloud Run
```bash
./deploy-cloud-run.sh [environment]
```

Example:
```bash
./deploy-cloud-run.sh production  # Deploy to production
./deploy-cloud-run.sh staging     # Deploy to staging
```

## Semantic Versioning

Versions are automatically generated from `BUILD_NUMBER`:

| BUILD_NUMBER | Semantic Version |
|-------------|------------------|
| 200         | 2.0.0           |
| 201         | 2.0.1           |
| 210         | 2.1.0           |
| 300         | 3.0.0           |

## Image Size Optimization

### Size Targets
- **Development**: ≤1.5 GB (with debugging tools)
- **Production**: ≤1 GB (optimized)
- **Current**: ~800 MB (multi-stage optimized)

### Optimization Techniques
1. **Multi-stage build** removes build dependencies
2. **Selective copying** of only runtime files
3. **Layer optimization** with combined RUN commands
4. **Cleanup operations** remove package caches
5. **Minimal base image** using slim variant

## Resource Configuration

### Cloud Run Settings
```yaml
resources:
  limits:
    cpu: 1000m      # 1 CPU core
    memory: 2Gi     # 2GB RAM
  requests:
    cpu: 100m       # 0.1 CPU minimum
    memory: 512Mi   # 512MB minimum
```

### Scaling Configuration
- **Min instances**: 0 (scale to zero)
- **Max instances**: 10
- **Concurrency**: 4 requests per instance
- **Timeout**: 900s (15 minutes for large media files)

## Environment Variables

### Required
- `PORT`: Service port (set by Cloud Run)
- `BUILD_NUMBER`: Build version number
- `WHISPER_CACHE_DIR`: Cache directory path

### Optional
- `GUNICORN_WORKERS`: Number of workers (default: 2)
- `GUNICORN_TIMEOUT`: Worker timeout (default: 300s)
- `MAX_QUEUE_LENGTH`: Request queue limit (default: 50)
- `YOUTUBE_SERVICE_URL`: YouTube microservice URL

## Security Features

### Container Security
- **Non-root execution**: Runs as `appuser` (UID 1000)
- **Read-only filesystem**: Application files mounted read-only
- **Tmpfs usage**: Temporary data in memory only
- **Minimal privileges**: No sudo or privilege escalation

### Network Security
- **Health checks**: Built-in monitoring endpoints
- **HTTPS only**: All Cloud Run traffic encrypted
- **Authentication**: API key validation (configurable)

## Monitoring and Logging

### Health Monitoring
Cloud Run automatically monitors the health endpoints and restarts containers if needed.

### Log Collection
All application logs are automatically collected by Cloud Run and sent to Cloud Logging:

```bash
# View logs
gcloud logs tail --follow projects/PROJECT_ID/logs/run.googleapis.com%2Fstdout
```

### Metrics
Cloud Run provides built-in metrics for:
- Request count and latency
- Error rates
- CPU and memory usage
- Container starts/stops

## Troubleshooting

### Common Issues

#### Image Size Too Large
If the image exceeds 1GB:
1. Review `.dockerignore` exclusions
2. Check for unnecessary files in final stage
3. Optimize FFmpeg build flags
4. Consider removing unused codecs

#### Health Check Failures
If health checks fail:
1. Check if port matches `$PORT` environment variable
2. Verify Flask application starts correctly
3. Check for blocking operations in startup
4. Review container logs for errors

#### Memory Issues
If containers run out of memory:
1. Increase Cloud Run memory limit
2. Reduce `GUNICORN_WORKERS` count
3. Optimize Whisper model loading
4. Check for memory leaks in media processing

### Debug Commands

#### Test Local Build
```bash
# Build and run locally
./build-docker.sh dev
docker run -p 8080:8080 -e PORT=8080 gcr.io/PROJECT_ID/sync-scribe-studio-api:2.0.0-dev

# Test health endpoint
curl http://localhost:8080/health
```

#### Container Inspection
```bash
# Inspect image layers
docker history gcr.io/PROJECT_ID/sync-scribe-studio-api:latest

# Check image size breakdown
dive gcr.io/PROJECT_ID/sync-scribe-studio-api:latest
```

## Performance Optimization

### Startup Time
- **Pre-loaded models**: Whisper models loaded during build
- **Optimized dependencies**: Minimal Python packages
- **Fast health checks**: Simple status endpoints

### Runtime Performance
- **Compiled FFmpeg**: Custom build with optimizations
- **Memory caching**: Efficient use of tmpfs for temporary data
- **Connection pooling**: HTTP client reuse

## Deployment Pipeline

### CI/CD Integration
The build and deployment scripts can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Build Docker Image
  run: ./build-docker.sh ${{ github.ref_name }}

- name: Deploy to Cloud Run
  run: ./deploy-cloud-run.sh production
```

### Blue-Green Deployment
Use Cloud Run traffic splitting for zero-downtime deployments:

```bash
# Deploy new version to staging tag
./deploy-cloud-run.sh staging

# Split traffic 80/20
./deploy-cloud-run.sh traffic split

# Migrate all traffic to new version
./deploy-cloud-run.sh traffic migrate staging
```

## Cost Optimization

### Resource Efficiency
- **Scale to zero**: No cost when not in use
- **Right-sizing**: Optimal CPU/memory allocation
- **Request batching**: Efficient concurrency handling

### Storage Costs
- **No persistent storage**: All data in tmpfs (included in compute)
- **Minimal image size**: Reduced network transfer costs
- **Layer caching**: Docker layer reuse for faster builds

## Compliance and Governance

### Security Compliance
- **Container scanning**: Automated vulnerability scanning
- **Base image updates**: Regular security patches
- **Access controls**: IAM-based permissions

### Operational Compliance
- **Audit logging**: All deployments logged
- **Version tracking**: Semantic versioning
- **Change management**: Documented deployment process

## Future Improvements

### Planned Enhancements
1. **ARM64 support**: Multi-architecture builds
2. **GPU acceleration**: CUDA-enabled FFmpeg
3. **Advanced caching**: Redis integration for model caching
4. **Monitoring**: Prometheus metrics export

### Performance Targets
- **Cold start**: <10s container startup time
- **Memory usage**: <1.5GB peak during heavy processing
- **Request latency**: <2s for standard operations
