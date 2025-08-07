# YouTube Downloader Service - Docker Containerization

This document describes the containerization setup for the YouTube Downloader microservice, including Docker configuration, deployment, and operational considerations.

## Overview

The YouTube Downloader service is containerized using Docker with the following key features:

- **Multi-stage build** for production optimization
- **Node.js 18 LTS** (Alpine Linux) as the base image
- **Security hardening** with non-root user and minimal permissions
- **Resource constraints** and restart policies
- **Internal networking** only (no host-published ports)
- **Health checks** and monitoring capabilities
- **Graceful shutdown** handling

## Container Architecture

### Base Image
- **Primary**: `node:18-alpine` (Node.js LTS matching toolkit baseline)
- **Init System**: `tini` for proper signal handling
- **Runtime**: Production-optimized Alpine Linux

### Security Features
- Non-root user (`appuser:1001`)
- Security options: `no-new-privileges:true`
- Multi-stage build to reduce attack surface
- No sensitive data in logs or environment

### Resource Management
- **CPU Limits**: 1.0 CPU, 0.25 CPU reserved
- **Memory Limits**: 512MB limit, 128MB reserved
- **Restart Policy**: On-failure with exponential backoff

## Files Structure

```
services/youtube-downloader/
├── Dockerfile              # Multi-stage Docker build
├── start.sh                # Entrypoint script with validation
├── docker-build.sh         # Build and test automation
├── .dockerignore           # Build context optimization
└── README-Docker.md        # This documentation
```

## Environment Variables

### Required
- `NODE_ENV` - Application environment (production/development)
- `PORT` - Service port (default: 3001)

### Optional
- `YTDL_NETWORK_TIMEOUT` - Network timeout for downloads (default: 30000ms)
- `ALLOWED_ORIGINS` - CORS origins (default: *)
- `SKIP_NETWORK_CHECK` - Skip startup network validation (default: false)
- `STARTUP_TIMEOUT` - Startup health check timeout (default: 30s)

## Building the Container

### Basic Build
```bash
# Build with default settings
./docker-build.sh

# Build only (no testing)
./docker-build.sh --build-only

# Build with custom tag
TAG=v1.2.0 ./docker-build.sh
```

### Manual Build
```bash
# Build production image
docker build --target production -t youtube-downloader:latest .

# Build with specific Node.js version
docker build --build-arg NODE_VERSION=18.19.0 -t youtube-downloader:latest .
```

## Running the Container

### Standalone Container
```bash
# Run with default settings
docker run -d \
  --name youtube-downloader \
  --env NODE_ENV=production \
  --env PORT=3001 \
  --env YTDL_NETWORK_TIMEOUT=30000 \
  youtube-downloader:latest

# Run with custom configuration
docker run -d \
  --name youtube-downloader \
  --env-file .env \
  --expose 3001 \
  --restart unless-stopped \
  youtube-downloader:latest
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# Start only YouTube downloader
docker-compose up -d youtube-downloader

# View logs
docker-compose logs -f youtube-downloader
```

## Internal Networking

The service is configured for **internal networking only**:

- **No published ports** to the host
- **Internal Docker networks**: `internal` (isolated), `web` (with Traefik)
- **Service discovery**: Available as `youtube-downloader:3001` to other services
- **Security**: Cannot be accessed directly from outside the Docker network

### Network Configuration in docker-compose.yml
```yaml
networks:
  web:
    driver: bridge
  internal:
    driver: bridge
    internal: true  # No external access
```

## Health Checks

### Docker Health Check
- **Endpoint**: `http://localhost:3001/healthz`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts
- **Start Period**: 30 seconds

### Manual Health Check
```bash
# Check container health
docker inspect youtube-downloader --format='{{.State.Health.Status}}'

# Test health endpoint
docker exec youtube-downloader wget --quiet --tries=1 --spider http://localhost:3001/healthz
```

## Resource Constraints

### CPU and Memory
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'      # Maximum 1 CPU core
      memory: 512M     # Maximum 512MB RAM
    reservations:
      cpus: '0.25'     # Reserved 0.25 CPU core
      memory: 128M     # Reserved 128MB RAM
```

### Restart Policy
```yaml
deploy:
  restart_policy:
    condition: on-failure    # Restart only on failure
    delay: 5s               # Wait 5 seconds before restart
    max_attempts: 3         # Maximum 3 restart attempts
    window: 120s            # Reset counter every 2 minutes
```

## Monitoring and Logs

### Container Logs
```bash
# View real-time logs
docker logs -f youtube-downloader

# View last 100 lines
docker logs --tail 100 youtube-downloader

# View logs with timestamps
docker logs -t youtube-downloader
```

### Log Volumes
```yaml
volumes:
  youtube_logs:/app/logs:rw  # Persistent log storage
```

### Container Metrics
```bash
# View resource usage
docker stats youtube-downloader

# Container information
docker inspect youtube-downloader
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check container logs
docker logs youtube-downloader

# Check environment variables
docker inspect youtube-downloader --format='{{.Config.Env}}'

# Test start script manually
docker run -it --rm youtube-downloader:latest /bin/sh
```

#### Health Check Failures
```bash
# Check health endpoint manually
docker exec youtube-downloader wget -O- http://localhost:3001/healthz

# Check if service is listening
docker exec youtube-downloader netstat -tlnp | grep 3001
```

#### Network Connectivity
```bash
# Test internal network connectivity
docker exec youtube-downloader nslookup google.com

# Check Docker networks
docker network ls
docker network inspect sync-scribe-studio-api_internal
```

#### Resource Issues
```bash
# Check resource usage
docker stats youtube-downloader

# Check system resources
docker system df
docker system prune  # Clean up unused resources
```

### Debug Mode
```bash
# Run with debug logging
docker run -d \
  --name youtube-downloader-debug \
  --env NODE_ENV=development \
  --env DEBUG=* \
  youtube-downloader:latest

# Run interactively for debugging
docker run -it --rm \
  --env NODE_ENV=development \
  youtube-downloader:latest /bin/sh
```

## Security Considerations

### Container Security
- Runs as non-root user (`appuser:1001`)
- Uses security option `no-new-privileges:true`
- Minimal Alpine Linux base image
- No privileged capabilities required

### Network Security
- Internal networking only
- No exposed ports to host
- CORS configuration for allowed origins
- Input validation and sanitization

### Data Security
- No sensitive data in container logs
- Environment variables for configuration
- Persistent logs in Docker volumes
- No data stored in container filesystem

## Production Deployment

### Pre-deployment Checklist
- [ ] Build and test container locally
- [ ] Verify environment variables are set
- [ ] Check resource limits are appropriate
- [ ] Test health checks work correctly
- [ ] Verify internal network connectivity
- [ ] Review security settings

### Deployment Commands
```bash
# Build production image
TAG=production ./docker-build.sh --build-only

# Deploy via Docker Compose
docker-compose -f docker-compose.prod.yml up -d youtube-downloader

# Verify deployment
docker-compose ps youtube-downloader
docker-compose logs youtube-downloader
```

### Scaling Considerations
```bash
# Scale service instances
docker-compose up -d --scale youtube-downloader=3

# Load balancing (via Traefik or other proxy)
# Internal services can connect to any instance
```

## Maintenance

### Regular Tasks
```bash
# Update base image
docker pull node:18-alpine
./docker-build.sh --build-only

# Clean up old images
docker image prune -a

# Backup logs
docker cp youtube-downloader:/app/logs ./backup-logs-$(date +%Y%m%d)

# Rotate logs (if needed)
docker exec youtube-downloader logrotate -f /etc/logrotate.conf
```

### Updates and Rollbacks
```bash
# Update to new version
TAG=v1.2.0 ./docker-build.sh --build-only
docker-compose up -d youtube-downloader

# Rollback to previous version
docker tag youtube-downloader:v1.1.0 youtube-downloader:latest
docker-compose up -d youtube-downloader
```

## Integration with Main Application

The containerized YouTube downloader integrates with the main application via:

1. **Internal Docker networking** - Available at `http://youtube-downloader:3001`
2. **Environment configuration** - Service URL configured via `YOUTUBE_SERVICE_URL`
3. **Health monitoring** - Main app can check `http://youtube-downloader:3001/healthz`
4. **Load balancing** - Multiple instances can run behind a proxy

### Example Integration
```javascript
// Main application configuration
const YOUTUBE_SERVICE_URL = process.env.YOUTUBE_SERVICE_URL || 'http://youtube-downloader:3001';

// Health check integration
const healthCheck = await fetch(`${YOUTUBE_SERVICE_URL}/healthz`);
const isHealthy = healthCheck.ok;
```

---

For more information about the YouTube Downloader service itself, see the main README.md file.
