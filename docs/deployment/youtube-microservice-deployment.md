# YouTube Microservice Deployment Guide

## Overview

This guide covers the deployment of the YouTube downloader microservice for the Sync Scribe Studio API. The microservice is implemented as a Node.js/Express application that handles YouTube video downloading and metadata extraction.

## Architecture

```
┌─────────────────────┐    HTTP/REST    ┌────────────────────────┐
│                     │ ────────────── │                        │
│ Main Python API     │                │ YouTube Microservice   │
│ (Flask)             │ ←──────────── │ (Node.js/Express)      │
│                     │                │                        │
└─────────────────────┘                └────────────────────────┘
           │                                        │
           │                                        │
           ▼                                        ▼
    ┌─────────────┐                         ┌─────────────┐
    │   Client    │                         │  YouTube    │
    │ Applications│                         │    API      │
    └─────────────┘                         └─────────────┘
```

## Prerequisites

### System Requirements
- Node.js 18.x LTS or later
- npm 8.x or later
- Minimum 1GB RAM
- Minimum 2GB free disk space

### Dependencies
- YouTube microservice requires internet access
- Python API must be able to reach microservice
- No database dependencies (stateless service)

### Environment Setup
- Docker (recommended for production)
- Docker Compose (for orchestration)
- Access to container registry (if using containers)

## Deployment Options

### Option 1: Local Development Setup

#### 1. Clone and Setup
```bash
# Navigate to microservice directory
cd services/youtube-downloader/

# Install dependencies
npm install

# Copy environment template
cp .env.example .env
```

#### 2. Configure Environment
```bash
# .env file
NODE_ENV=development
PORT=3001
YOUTUBE_SERVICE_TIMEOUT=30000
MAX_DOWNLOAD_SIZE=104857600  # 100MB
RATE_LIMIT_WINDOW=900000     # 15 minutes
RATE_LIMIT_MAX=100           # requests per window

# Health check configuration
HEALTH_CHECK_ENDPOINT=/healthz
HEALTH_CHECK_TIMEOUT=5000

# Logging configuration
LOG_LEVEL=info
LOG_FORMAT=combined
```

#### 3. Start the Service
```bash
# Development mode with auto-restart
npm run dev

# Production mode
npm start

# With PM2 (recommended for production)
npm run pm2:start
```

#### 4. Verify Deployment
```bash
# Test health endpoint
curl http://localhost:3001/healthz

# Test info endpoint
curl -X POST http://localhost:3001/v1/media/youtube/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Option 2: Docker Deployment

#### 1. Build Docker Image
```bash
# Build from project root
docker build -t sync-scribe-youtube:latest -f services/youtube-downloader/Dockerfile ./services/youtube-downloader/

# Or using docker-compose
docker-compose build youtube-downloader
```

#### 2. Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  youtube-downloader:
    build:
      context: ./services/youtube-downloader
      dockerfile: Dockerfile
    container_name: youtube-downloader
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - PORT=3001
      - YOUTUBE_SERVICE_TIMEOUT=30000
      - MAX_DOWNLOAD_SIZE=104857600
      - RATE_LIMIT_MAX=100
    volumes:
      - ./logs:/app/logs
    networks:
      - sync-scribe-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  main-api:
    build: .
    container_name: main-api
    ports:
      - "8080:8080"
    environment:
      - YOUTUBE_SERVICE_URL=http://youtube-downloader:3001
      - YOUTUBE_SERVICE_TIMEOUT=30
      - YOUTUBE_RETRY_ATTEMPTS=3
    depends_on:
      - youtube-downloader
    networks:
      - sync-scribe-network

networks:
  sync-scribe-network:
    driver: bridge
```

#### 3. Deploy with Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f youtube-downloader

# Scale the service
docker-compose up -d --scale youtube-downloader=3
```

### Option 3: Cloud Deployment (GCP Cloud Run)

#### 1. Prepare for Cloud Run
```bash
# Build and tag for Google Container Registry
docker build -t gcr.io/YOUR_PROJECT_ID/youtube-downloader:latest -f services/youtube-downloader/Dockerfile ./services/youtube-downloader/

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/youtube-downloader:latest
```

#### 2. Deploy to Cloud Run
```bash
# Deploy the service
gcloud run deploy youtube-downloader \
  --image=gcr.io/YOUR_PROJECT_ID/youtube-downloader:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=3001 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --concurrency=100 \
  --max-instances=10 \
  --set-env-vars="NODE_ENV=production,YOUTUBE_SERVICE_TIMEOUT=30000,MAX_DOWNLOAD_SIZE=104857600"
```

#### 3. Update Main API Configuration
```bash
# Set environment variable for main API
gcloud run services update main-api \
  --set-env-vars="YOUTUBE_SERVICE_URL=https://youtube-downloader-XXXXX-uc.a.run.app" \
  --region=us-central1
```

### Option 4: Kubernetes Deployment

#### 1. Kubernetes Manifests
```yaml
# k8s/youtube-downloader-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: youtube-downloader
  labels:
    app: youtube-downloader
spec:
  replicas: 3
  selector:
    matchLabels:
      app: youtube-downloader
  template:
    metadata:
      labels:
        app: youtube-downloader
    spec:
      containers:
      - name: youtube-downloader
        image: sync-scribe-youtube:latest
        ports:
        - containerPort: 3001
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "3001"
        - name: YOUTUBE_SERVICE_TIMEOUT
          value: "30000"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 3001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 3001
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: youtube-downloader-service
spec:
  selector:
    app: youtube-downloader
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3001
  type: ClusterIP
```

#### 2. Deploy to Kubernetes
```bash
# Apply the deployment
kubectl apply -f k8s/youtube-downloader-deployment.yaml

# Verify deployment
kubectl get pods -l app=youtube-downloader
kubectl get services youtube-downloader-service

# View logs
kubectl logs -l app=youtube-downloader -f
```

## Configuration Management

### Environment Variables

#### Required Variables
```bash
PORT=3001                    # Service port
NODE_ENV=production          # Environment mode
```

#### Optional Variables
```bash
# Service Configuration
YOUTUBE_SERVICE_TIMEOUT=30000      # Request timeout in ms
MAX_DOWNLOAD_SIZE=104857600        # Max download size in bytes
RATE_LIMIT_WINDOW=900000           # Rate limit window in ms
RATE_LIMIT_MAX=100                 # Max requests per window

# Health Check Configuration
HEALTH_CHECK_ENDPOINT=/healthz     # Health check path
HEALTH_CHECK_TIMEOUT=5000          # Health check timeout

# Logging Configuration
LOG_LEVEL=info                     # Log level (error, warn, info, debug)
LOG_FORMAT=combined                # Log format
LOG_FILE=/app/logs/youtube.log     # Log file path

# Security Configuration
CORS_ORIGIN=*                      # CORS allowed origins
CORS_METHODS=GET,POST,OPTIONS      # CORS allowed methods
```

### Configuration Files

#### package.json Scripts
```json
{
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "pm2:start": "pm2 start ecosystem.config.js",
    "pm2:stop": "pm2 stop ecosystem.config.js",
    "pm2:restart": "pm2 restart ecosystem.config.js"
  }
}
```

#### PM2 Ecosystem Configuration
```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'youtube-downloader',
    script: 'index.js',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 3001
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    max_memory_restart: '1G',
    node_args: '--max-old-space-size=1024'
  }]
}
```

## Health Checks and Monitoring

### Health Check Endpoint
```bash
# Basic health check
curl http://localhost:3001/healthz

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-01-27T12:00:00.000Z",
  "version": "1.0.0",
  "uptime": 3600,
  "environment": "production",
  "memory": {
    "used": "45.2 MB",
    "total": "1024 MB"
  },
  "dependencies": {
    "ytdl-core": "4.11.5"
  }
}
```

### Monitoring Setup

#### Prometheus Metrics (Optional)
```javascript
// Add to index.js for Prometheus metrics
const prometheus = require('prom-client');
const register = prometheus.register;

// Custom metrics
const httpRequestDuration = new prometheus.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code']
});

const youtubeDownloads = new prometheus.Counter({
  name: 'youtube_downloads_total',
  help: 'Total number of YouTube downloads'
});
```

#### Log Monitoring
```bash
# Using tail for real-time logs
tail -f logs/youtube.log

# Using journalctl for systemd services
journalctl -u youtube-downloader -f

# Using Docker logs
docker logs -f youtube-downloader
```

## Security Considerations

### Network Security
- Use internal networks for service communication
- Implement proper firewall rules
- Use HTTPS in production
- Restrict access to health check endpoints

### Rate Limiting
```javascript
// Built-in rate limiting configuration
const rateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false
});
```

### Input Validation
```javascript
// URL validation middleware
const validateYouTubeUrl = (req, res, next) => {
  const { url } = req.body;
  
  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }
  
  const youtubePattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
  if (!youtubePattern.test(url)) {
    return res.status(400).json({ error: 'Invalid YouTube URL' });
  }
  
  next();
};
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check port availability
netstat -tulpn | grep :3001

# Check logs
npm run dev
# or
docker logs youtube-downloader
```

#### 2. Memory Issues
```bash
# Check memory usage
docker stats youtube-downloader

# Increase memory limit
docker run --memory=2g sync-scribe-youtube:latest
```

#### 3. YouTube API Issues
```bash
# Test URL validation
curl -X POST http://localhost:3001/v1/media/youtube/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Check ytdl-core version
npm list ytdl-core
```

#### 4. Network Connectivity
```bash
# Test from main API container
docker exec main-api curl http://youtube-downloader:3001/healthz

# Check DNS resolution
nslookup youtube-downloader
```

### Debug Mode
```bash
# Enable debug logging
NODE_ENV=development DEBUG=youtube-downloader:* npm start

# Or set log level
LOG_LEVEL=debug npm start
```

### Performance Tuning

#### Node.js Optimization
```bash
# Increase memory limit
node --max-old-space-size=2048 index.js

# Enable garbage collection logging
node --trace-gc index.js
```

#### Container Optimization
```dockerfile
# Multi-stage build for smaller images
FROM node:18-alpine AS builder
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
COPY --from=builder --chown=nextjs:nodejs /app .
USER nextjs
CMD ["node", "index.js"]
```

## Backup and Recovery

### Service State
The YouTube microservice is stateless, so no data backup is required.

### Configuration Backup
```bash
# Backup environment configuration
cp .env .env.backup.$(date +%Y%m%d)

# Backup Docker compose configuration
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d)
```

### Recovery Procedures
```bash
# Quick service restart
docker-compose restart youtube-downloader

# Full redeployment
docker-compose down youtube-downloader
docker-compose up -d youtube-downloader

# Rollback to previous image
docker tag sync-scribe-youtube:previous sync-scribe-youtube:latest
docker-compose up -d youtube-downloader
```

## Scaling Considerations

### Horizontal Scaling
```bash
# Scale with Docker Compose
docker-compose up -d --scale youtube-downloader=5

# Scale with Kubernetes
kubectl scale deployment youtube-downloader --replicas=5
```

### Load Balancing
- Use nginx or HAProxy for load balancing
- Configure health checks in load balancer
- Implement session affinity if needed (though service is stateless)

### Resource Monitoring
- Monitor CPU and memory usage
- Track request latency and throughput
- Monitor YouTube API rate limits
- Set up alerts for service failures

---

## Next Steps

1. Review and customize configuration for your environment
2. Set up monitoring and alerting
3. Configure backup procedures
4. Plan for scaling requirements
5. Review security configurations

For additional support, refer to the troubleshooting section or check the project documentation.
