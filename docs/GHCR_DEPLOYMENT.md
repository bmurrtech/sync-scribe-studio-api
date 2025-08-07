# GitHub Container Registry (GHCR) Deployment Guide

## Overview

This document provides comprehensive instructions for deploying the Sync Scribe Studio API using GitHub Container Registry (GHCR) as the container registry and various deployment platforms.

## Table of Contents

- [Quick Start](#quick-start)
- [GitHub Actions CI/CD Pipeline](#github-actions-cicd-pipeline)
- [Available Image Tags](#available-image-tags)
- [Deployment Platforms](#deployment-platforms)
  - [Local Docker](#local-docker)
  - [Google Cloud Run](#google-cloud-run)
  - [Docker Compose](#docker-compose)
- [Environment Variables](#environment-variables)
- [Security and Best Practices](#security-and-best-practices)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Pull and Run Latest Image

```bash
# Pull the latest stable image
docker pull ghcr.io/bmurrtech/sync-scribe-studio-api:latest

# Run with required environment variables
docker run -d \
  --name sync-scribe-api \
  -p 8080:8080 \
  -e API_KEY=your-secure-api-key \
  -e DB_TOKEN=your-secure-db-token \
  -e PORT=8080 \
  ghcr.io/bmurrtech/sync-scribe-studio-api:latest
```

### 2. Using the Deployment Script

```bash
# Deploy locally with latest image
./scripts/deploy-from-ghcr.sh --platform local --tag latest

# View all options
./scripts/deploy-from-ghcr.sh --help
```

## GitHub Actions CI/CD Pipeline

The project includes a comprehensive CI/CD pipeline that automatically builds, tests, and deploys container images to GHCR.

### Pipeline Stages

1. **Security Scanning**
   - Bandit security analysis for Python code
   - Safety check for Python dependencies
   - NPM audit for Node.js dependencies

2. **Testing**
   - Unit tests across Python 3.10, 3.11, 3.12
   - Integration tests with Redis
   - Node.js microservice tests
   - Coverage reporting to Codecov

3. **Docker Build & Test**
   - Multi-stage Docker builds
   - Container functionality testing
   - Health endpoint validation

4. **Container Security**
   - Trivy vulnerability scanning
   - SARIF upload to GitHub Security tab

5. **Deployment to GHCR**
   - Multi-platform builds (linux/amd64, linux/arm64)
   - Semantic versioning and tagging
   - Build attestation and provenance

6. **Optional Cloud Run Deployment**
   - Automatic deployment to Google Cloud Run
   - Environment-specific configurations

### Triggering the Pipeline

The pipeline runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch
- Git tags matching `v*`

### Pipeline Configuration

The pipeline is defined in `.github/workflows/ghcr-ci-cd.yml` and includes:

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'
```

## Available Image Tags

### Automatic Tags

| Tag Pattern | Description | Example |
|------------|-------------|---------|
| `latest` | Latest stable release from main | `latest` |
| `build-{NUMBER}` | Specific CI build number | `build-123` |
| `main-{SHA}` | Latest commit from main branch | `main-a1b2c3d` |
| `{branch}-{SHA}` | Branch-specific builds | `develop-x1y2z3` |

### Semantic Version Tags

For tagged releases:

| Tag Pattern | Description | Example |
|------------|-------------|---------|
| `v{VERSION}` | Full semantic version | `v1.2.3` |
| `v{MAJOR}.{MINOR}` | Major.minor version | `v1.2` |

### Usage Examples

```bash
# Latest stable
docker pull ghcr.io/bmurrtech/sync-scribe-studio-api:latest

# Specific build
docker pull ghcr.io/bmurrtech/sync-scribe-studio-api:build-123

# Semantic version
docker pull ghcr.io/bmurrtech/sync-scribe-studio-api:v1.2.3
```

## Deployment Platforms

### Local Docker

#### Quick Deploy

```bash
./scripts/deploy-from-ghcr.sh --platform local --tag latest
```

#### Manual Deployment

```bash
# Pull image
docker pull ghcr.io/bmurrtech/sync-scribe-studio-api:latest

# Run container
docker run -d \
  --name sync-scribe-api \
  -p 8080:8080 \
  -e API_KEY=your-api-key \
  -e DB_TOKEN=your-db-token \
  -e PORT=8080 \
  ghcr.io/bmurrtech/sync-scribe-studio-api:latest

# Check health
curl http://localhost:8080/health
```

#### Advanced Options

```bash
# With environment file
./scripts/deploy-from-ghcr.sh \
  --platform local \
  --tag latest \
  --env-file .env.production \
  --port 9090 \
  --cleanup

# With resource limits
docker run -d \
  --name sync-scribe-api \
  --memory=2g \
  --cpus=2 \
  -p 8080:8080 \
  --env-file .env.production \
  ghcr.io/bmurrtech/sync-scribe-studio-api:latest
```

### Google Cloud Run

#### Using Deployment Script

```bash
./scripts/deploy-from-ghcr.sh \
  --platform cloud-run \
  --tag build-123 \
  --project your-gcp-project \
  --region us-central1 \
  --env-file .env.production
```

#### Manual Deployment

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy sync-scribe-studio-api \
  --image ghcr.io/bmurrtech/sync-scribe-studio-api:build-123 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --max-instances 10 \
  --set-env-vars=\"PORT=8080,ENVIRONMENT=production\"
```

#### Cloud Run Configuration

The deployment includes optimized Cloud Run settings:

- **Memory**: 2GB (configurable)
- **CPU**: 2 vCPUs (configurable) 
- **Concurrency**: 100 requests per instance
- **Scaling**: 0 to 10 instances (auto-scaling)
- **Timeout**: 300 seconds
- **Health checks**: Automatic via `/health` endpoint

### Docker Compose

#### Quick Deploy

```bash
./scripts/deploy-from-ghcr.sh \
  --platform docker-compose \
  --tag latest \
  --environment production
```

This creates a `docker-compose.override.yml` file with:

```yaml
version: '3.8'

services:
  api:
    image: ghcr.io/bmurrtech/sync-scribe-studio-api:latest
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
      - ENVIRONMENT=production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

volumes:
  redis_data:
```

#### Advanced Compose Setup

Create a custom `docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  api:
    image: ghcr.io/bmurrtech/sync-scribe-studio-api:latest
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
      - ENVIRONMENT=production
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    name: sync-scribe-network
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_KEY` | API authentication key | `your-secure-api-key` |
| `DB_TOKEN` | Database/service token | `your-secure-db-token` |
| `PORT` | Server port (auto-set in Cloud Run) | `8080` |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment type |
| `BUILD_NUMBER` | Auto-set | Build number from CI |
| `WORKERS` | CPU cores + 1 | Gunicorn workers |
| `TIMEOUT` | 300 | Request timeout |

### Platform-Specific Variables

#### Google Cloud Run

```bash
# Automatically set by Cloud Run
PORT=8080

# Custom environment variables
gcloud run deploy sync-scribe-studio-api \
  --set-env-vars="API_KEY=your-key,DB_TOKEN=your-token"
```

#### Local Development

Create `.env.local`:

```env
API_KEY=dev-api-key-12345
DB_TOKEN=dev-db-token-12345
PORT=8080
ENVIRONMENT=development
DEBUG=true
```

## Security and Best Practices

### Container Security

1. **Non-root User**: Containers run as non-root user
2. **Vulnerability Scanning**: Automatic Trivy scans in CI/CD
3. **Security Headers**: Implemented via Helmet.js
4. **Input Validation**: Joi schema validation
5. **Rate Limiting**: Progressive rate limiting

### Access Control

1. **API Authentication**: Required for all protected endpoints
2. **Environment Variables**: Secure secret management
3. **Network Policies**: Configurable network access
4. **Image Signatures**: Build attestation and provenance

### Production Deployment

1. **Use Specific Tags**: Avoid `latest` in production
2. **Environment Files**: Secure environment variable management
3. **Health Checks**: Implement proper health endpoints
4. **Monitoring**: Set up logging and metrics
5. **Backup Strategies**: Plan for disaster recovery

## Monitoring and Observability

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/` | Service information |
| `/health` | Basic health status |
| `/health/detailed` | Comprehensive health info |

### Logging

The application provides structured logging:

```json
{
  \"timestamp\": \"2025-08-07T18:30:45Z\",
  \"level\": \"INFO\",
  \"message\": \"Request processed\",
  \"request_id\": \"req-12345\",
  \"duration\": 150
}
```

### Metrics Collection

Configure monitoring with:

- **Application metrics**: Response times, error rates
- **Container metrics**: CPU, memory usage
- **Business metrics**: API usage, feature adoption

### Cloud Run Monitoring

```bash
# View logs
gcloud logging read \"resource.type=cloud_run_revision\" --limit 50

# Monitor metrics
gcloud monitoring dashboards list
```

## Troubleshooting

### Common Issues

#### Image Pull Errors

```bash
# Authenticate to GHCR
echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin

# Check image exists
docker manifest inspect ghcr.io/bmurrtech/sync-scribe-studio-api:latest
```

#### Container Startup Failures

```bash
# Check logs
docker logs sync-scribe-api

# Debug with shell
docker run -it --entrypoint /bin/bash ghcr.io/bmurrtech/sync-scribe-studio-api:latest
```

#### Health Check Failures

```bash
# Test health endpoint
curl -v http://localhost:8080/health

# Check container networking
docker inspect sync-scribe-api | grep -i port
```

#### Cloud Run Deployment Issues

```bash
# Check deployment status
gcloud run services describe sync-scribe-studio-api --region=us-central1

# View deployment logs
gcloud logging read \"resource.type=cloud_run_revision\" --limit 10
```

### Performance Issues

#### Memory Issues

```bash
# Check memory usage
docker stats sync-scribe-api

# Increase memory limits
docker run --memory=2g ghcr.io/bmurrtech/sync-scribe-studio-api:latest
```

#### Scaling Issues

```bash
# Check container resource usage
docker exec sync-scribe-api top

# Monitor Cloud Run metrics
gcloud run services describe sync-scribe-studio-api --region=us-central1
```

### Debug Mode

Enable debug logging:

```bash
docker run -e DEBUG=true ghcr.io/bmurrtech/sync-scribe-studio-api:latest
```

## Support and Contributing

### Getting Help

1. **Documentation**: Check this guide and README.md
2. **Issues**: Create GitHub issues for bugs
3. **Community**: Join the No-Code Architects Community
4. **Logs**: Always include logs when reporting issues

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. CI/CD will automatically test and build

### Release Process

1. Create pull request to `main`
2. CI/CD runs full test suite
3. Merge triggers deployment to GHCR
4. Tag release for semantic versioning
5. Automatic deployment notifications

---

## Conclusion

This GHCR deployment setup provides:

- ✅ **Automated CI/CD** with comprehensive testing
- ✅ **Multi-platform support** for various deployment targets
- ✅ **Security-first approach** with vulnerability scanning
- ✅ **Production-ready** configurations
- ✅ **Comprehensive monitoring** and observability
- ✅ **Easy-to-use deployment scripts**

The deployment pipeline ensures that your application is always production-ready with proper testing, security scanning, and deployment automation.
