# YouTube Integration Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting steps for common issues with the YouTube integration in the Sync Scribe Studio API. It covers both the Python API integration and the Node.js microservice components.

## Quick Diagnosis

### Health Check Commands
```bash
# Test main API YouTube endpoints
curl -X GET http://localhost:8080/v1/media/youtube/health \
  -H "x-api-key: YOUR_API_KEY"

# Test microservice directly
curl http://localhost:3001/healthz

# Test connectivity between services
docker exec main-api curl http://youtube-downloader:3001/healthz
```

### Service Status Check
```bash
# Check if services are running
docker-compose ps

# Check service logs
docker-compose logs youtube-downloader
docker-compose logs main-api
```

## Common Issues and Solutions

### 1. Service Connectivity Issues

#### Symptom: "YouTube service unavailable" errors
```json
{
  "error": "YouTube service is currently unavailable",
  "code": 503
}
```

#### Possible Causes and Solutions

##### A. Microservice Not Running
```bash
# Check if microservice is running
docker ps | grep youtube-downloader

# Start the microservice
docker-compose up -d youtube-downloader

# Check microservice logs for startup errors
docker-compose logs youtube-downloader
```

##### B. Network Configuration Issues
```bash
# Check Docker network
docker network ls
docker network inspect sync-scribe-studio-api_default

# Verify service can reach microservice
docker exec main-api ping youtube-downloader
docker exec main-api nslookup youtube-downloader
```

##### C. Port Configuration Problems
```bash
# Check if port 3001 is accessible
netstat -tulpn | grep :3001

# Verify environment variables in main API
docker exec main-api env | grep YOUTUBE_SERVICE_URL
```

**Solution Steps:**
1. Ensure microservice is running: `docker-compose up -d youtube-downloader`
2. Check network connectivity: `docker exec main-api curl http://youtube-downloader:3001/healthz`
3. Verify environment variables: `YOUTUBE_SERVICE_URL=http://youtube-downloader:3001`
4. Check firewall/security group rules if deployed in cloud

### 2. YouTube URL Validation Errors

#### Symptom: "Invalid YouTube URL" errors
```json
{
  "error": "Invalid YouTube URL format",
  "code": 400
}
```

#### Valid URL Formats
```bash
# Supported formats:
https://www.youtube.com/watch?v=VIDEO_ID
https://youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID
https://m.youtube.com/watch?v=VIDEO_ID
```

#### Troubleshooting Steps
```bash
# Test with a known working URL
curl -X POST http://localhost:8080/v1/media/youtube/info \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Check URL validation regex in code
grep -r "youtube.*pattern" routes/v1/media/youtube.py
```

**Solution:**
- Use properly formatted YouTube URLs
- Ensure URL includes video ID
- Check for special characters or encoding issues

### 3. Download/Streaming Failures

#### Symptom: Downloads fail or stream interrupts
```json
{
  "error": "Download failed: Video unavailable",
  "code": 500
}
```

#### Troubleshooting Steps

##### A. Video Availability
```bash
# Test URL directly with ytdl-core
cd services/youtube-downloader/
node -e "
const ytdl = require('ytdl-core');
ytdl.validateURL('YOUR_URL_HERE').then(console.log);
"
```

##### B. Geographic Restrictions
```bash
# Check if video is geo-blocked
curl -X POST http://localhost:3001/v1/media/youtube/info \
  -H "Content-Type: application/json" \
  -d '{"url": "YOUR_URL_HERE"}'
```

##### C. Rate Limiting
```bash
# Check for rate limiting in logs
docker-compose logs youtube-downloader | grep -i "rate\|limit\|429"

# Check current rate limit status
curl -I http://localhost:3001/v1/media/youtube/info
```

**Solutions:**
1. **Video Unavailable**: Try different video, check if video exists
2. **Geo-restrictions**: Video may not be available in your region
3. **Rate Limiting**: Wait before retrying, implement backoff logic
4. **Age Restrictions**: Some videos require authentication

### 4. Memory and Performance Issues

#### Symptom: High memory usage or OOM kills
```bash
# Check memory usage
docker stats youtube-downloader

# Check for memory-related container restarts
docker-compose ps -a
```

#### Solutions

##### A. Increase Memory Limits
```yaml
# docker-compose.yml
services:
  youtube-downloader:
    deploy:
      resources:
        limits:
          memory: 2G  # Increase from 1G
        reservations:
          memory: 1G  # Increase from 512M
```

##### B. Node.js Memory Optimization
```javascript
// In package.json scripts
{
  "start": "node --max-old-space-size=2048 index.js"
}
```

##### C. Implement Streaming Limits
```javascript
// Add to microservice configuration
const MAX_DOWNLOAD_SIZE = process.env.MAX_DOWNLOAD_SIZE || 104857600; // 100MB
const STREAM_TIMEOUT = process.env.STREAM_TIMEOUT || 300000; // 5 minutes
```

### 5. Authentication and Authorization Issues

#### Symptom: 401/403 errors
```json
{
  "error": "Invalid API key",
  "code": 401
}
```

#### Troubleshooting Steps
```bash
# Test with correct API key
curl -X GET http://localhost:8080/v1/media/youtube/health \
  -H "x-api-key: Test123"  # Use your actual API key

# Check API key configuration
docker exec main-api env | grep API_KEY

# Test without authentication (for microservice direct access)
curl http://localhost:3001/healthz
```

**Solutions:**
1. Verify API key is correctly set in environment
2. Ensure API key is passed in correct header (`x-api-key`)
3. Check if API key validation is working correctly

### 6. ytdl-core Library Issues

#### Symptom: YouTube extraction fails
```bash
# Common errors:
# "This video is unavailable"
# "Video is private"
# "No formats found"
```

#### Troubleshooting Steps

##### A. Update ytdl-core
```bash
cd services/youtube-downloader/
npm update ytdl-core
npm list ytdl-core  # Check version
```

##### B. Test Library Directly
```bash
cd services/youtube-downloader/
node -e "
const ytdl = require('ytdl-core');
ytdl.getInfo('YOUR_VIDEO_URL').then(info => {
  console.log('Title:', info.videoDetails.title);
  console.log('Available formats:', info.formats.length);
}).catch(console.error);
"
```

##### C. Check Library Issues
- Visit: https://github.com/fent/node-ytdl-core/issues
- Look for similar problems and solutions

**Solutions:**
1. **Update ytdl-core**: `npm update ytdl-core`
2. **Use Alternative URLs**: Try different video URLs
3. **Check Format Availability**: Not all formats may be available
4. **Library Limitations**: Some videos may not be supported

### 7. Docker and Container Issues

#### Symptom: Container fails to start or crashes

##### A. Build Issues
```bash
# Rebuild container from scratch
docker-compose build --no-cache youtube-downloader

# Check build logs
docker-compose build youtube-downloader
```

##### B. Runtime Issues
```bash
# Check container logs
docker-compose logs -f youtube-downloader

# Inspect container
docker inspect youtube-downloader

# Check container resources
docker exec youtube-downloader df -h
docker exec youtube-downloader free -m
```

##### C. Permission Issues
```bash
# Check file permissions
docker exec youtube-downloader ls -la /app

# Fix permissions if needed
docker exec --user root youtube-downloader chown -R node:node /app
```

### 8. Network and Proxy Issues

#### Symptom: External requests fail
```bash
# Test external connectivity from container
docker exec youtube-downloader curl -I https://www.youtube.com

# Test with verbose output
docker exec youtube-downloader curl -v https://www.youtube.com
```

#### Solutions for Proxy Environments
```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Add to docker-compose.yml
environment:
  - HTTP_PROXY=http://proxy.company.com:8080
  - HTTPS_PROXY=http://proxy.company.com:8080
  - NO_PROXY=localhost,127.0.0.1
```

## Logging and Monitoring

### Enable Debug Logging

#### For Python API
```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Enable Flask debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1
```

#### For Node.js Microservice
```bash
# Enable debug logging
export DEBUG=youtube-downloader:*
export NODE_ENV=development

# Set log level
export LOG_LEVEL=debug
```

### Log Analysis Commands
```bash
# Follow logs in real-time
docker-compose logs -f youtube-downloader

# Search for specific errors
docker-compose logs youtube-downloader | grep -i error

# Check for memory issues
docker-compose logs youtube-downloader | grep -i "memory\|oom"

# Look for rate limiting
docker-compose logs youtube-downloader | grep -i "rate\|limit\|429"
```

### Key Log Patterns to Look For
```bash
# Service startup
grep "Server.*listening" logs/youtube.log

# Request processing
grep "Processing request" logs/youtube.log

# Errors
grep "ERROR\|FATAL" logs/youtube.log

# Performance issues
grep "timeout\|slow\|memory" logs/youtube.log
```

## Performance Diagnostics

### Resource Monitoring
```bash
# Monitor container resources
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check system resources
top -p $(docker exec youtube-downloader cat /proc/1/status | grep PPid | awk '{print $2}')
```

### Request Timing
```bash
# Test response times
time curl -X POST http://localhost:8080/v1/media/youtube/info \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Test microservice directly
time curl -X POST http://localhost:3001/v1/media/youtube/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## Emergency Recovery Procedures

### Quick Service Restart
```bash
# Restart just the YouTube microservice
docker-compose restart youtube-downloader

# Restart all services
docker-compose restart
```

### Full Reset
```bash
# Stop all services
docker-compose down

# Remove containers and networks
docker-compose down --remove-orphans

# Rebuild and restart
docker-compose up -d --build
```

### Rollback to Previous Version
```bash
# Tag current version as problematic
docker tag sync-scribe-youtube:latest sync-scribe-youtube:problematic

# Restore previous version
docker tag sync-scribe-youtube:previous sync-scribe-youtube:latest

# Restart services
docker-compose up -d youtube-downloader
```

## Preventive Measures

### Health Monitoring Setup
```bash
# Add health check monitoring script
cat > scripts/health-monitor.sh << 'EOF'
#!/bin/bash
while true; do
  if ! curl -f http://localhost:3001/healthz > /dev/null 2>&1; then
    echo "$(date): YouTube service unhealthy, restarting..."
    docker-compose restart youtube-downloader
  fi
  sleep 60
done
EOF

chmod +x scripts/health-monitor.sh
```

### Automated Backups
```bash
# Backup configuration daily
cat > scripts/backup-config.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
cp .env .env.backup.$DATE
cp docker-compose.yml docker-compose.yml.backup.$DATE
echo "Configuration backed up with date: $DATE"
EOF
```

### Log Rotation
```bash
# Configure log rotation for Docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  }
}
EOF

# Restart Docker
sudo systemctl restart docker
```

## Getting Help

### Information to Collect
When reporting issues, collect the following:

1. **Service Status**
   ```bash
   docker-compose ps > service-status.txt
   ```

2. **Recent Logs**
   ```bash
   docker-compose logs --tail=100 youtube-downloader > youtube-logs.txt
   docker-compose logs --tail=100 main-api > api-logs.txt
   ```

3. **Environment Configuration**
   ```bash
   docker-compose config > docker-config.txt
   env | grep -E "(YOUTUBE|API|PORT)" > env-vars.txt
   ```

4. **System Information**
   ```bash
   docker version > docker-version.txt
   docker-compose version > compose-version.txt
   df -h > disk-space.txt
   free -m > memory-usage.txt
   ```

5. **Test Results**
   ```bash
   curl -X GET http://localhost:8080/v1/media/youtube/health -H "x-api-key: Test123" > health-check.txt
   ```

### Support Channels
- Check project documentation in `/docs` directory
- Review ADRs in `/pm/adr` for architectural decisions
- Check issue tracker for known problems
- Review troubleshooting logs systematically

## Summary Checklist

When troubleshooting YouTube integration issues:

- [ ] Check service health endpoints
- [ ] Verify Docker containers are running
- [ ] Test network connectivity between services
- [ ] Validate environment variables
- [ ] Check resource usage (CPU, memory)
- [ ] Review recent logs for errors
- [ ] Test with known working YouTube URLs
- [ ] Verify API key authentication
- [ ] Check ytdl-core library status
- [ ] Consider external factors (rate limiting, geo-blocks)

Remember to check the most recent logs first, as they often contain the most relevant information about current issues.
