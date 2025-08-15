# Sync Scribe Studio API

## Executive Summary

Sync Scribe Studio API is a comprehensive media processing and automation platform that eliminates the need for expensive third-party API subscriptions. Built with Python Flask, it provides enterprise-grade media manipulation, transcription, and cloud storage integration capabilities through a secure, self-hosted solution.

## Problem Statement

Organizations spend thousands of dollars monthly on multiple API subscriptions for media processing, transcription, and file management. These costs compound with:
- Multiple vendor dependencies
- API rate limitations
- Data privacy concerns
- Vendor lock-in
- Inconsistent API interfaces

## Solution Overview

Sync Scribe Studio API consolidates essential media processing capabilities into a single, self-hosted platform that:
- **Eliminates recurring API costs** by replacing services like ChatGPT Whisper, Cloud Convert, Createomate, JSON2Video, PDF.co, Placid, and OCodeKit
- **Provides complete data sovereignty** with on-premise or private cloud deployment
- **Offers unlimited processing** without rate limits or usage-based pricing
- **Ensures consistent API interface** across all media operations
- **Integrates seamlessly** with cloud storage providers (S3, GCS, Dropbox)


## Core Features

### Media Processing
- **Audio/Video Conversion**: Transform between formats with customizable codecs
- **Transcription & Translation**: Convert speech to text in multiple languages
- **Video Captioning**: Add professional captions with customizable styling
- **Media Concatenation**: Combine multiple files seamlessly
- **Silence Detection**: Identify and process silent segments
- **Metadata Extraction**: Retrieve comprehensive media information

### Advanced Capabilities
- **Web Screenshots**: Capture web pages with device emulation
- **Python Code Execution**: Run custom processing scripts remotely
- **FFmpeg Integration**: Access advanced media manipulation
- **Cloud Storage**: Direct integration with S3, GCS, and Dropbox

## Security Features

### Authentication & Authorization
- **API Key Authentication**: Secure access control via `X-API-Key` header
- **Environment-based Configuration**: Sensitive credentials stored securely
- **Request Validation**: Comprehensive payload validation on all endpoints

### Rate Limiting & Protection
- **Configurable Rate Limits**: Prevent abuse with customizable thresholds
- **Queue Management**: Control concurrent processing with `MAX_QUEUE_LENGTH`
- **Timeout Protection**: Configurable timeouts for long-running operations

### Security Headers
- **CORS Configuration**: Controlled cross-origin resource sharing
- **Content-Type Validation**: Strict input validation
- **Secure File Handling**: Sandboxed file operations with cleanup

### Data Protection
- **Temporary File Cleanup**: Automatic removal of processed files
- **No Data Retention**: Files processed in memory when possible
- **Encrypted Storage**: Support for encrypted cloud storage backends

## API Endpoints

Each endpoint is supported by robust payload validation and detailed API documentation to facilitate easy integration and usage.

### Audio

- **`/v1/audio/concatenate`**
  - Combines multiple audio files into a single audio file.

### Code

- **`/v1/code/execute/python`**
  - Executes Python code remotely and returns the execution results.

### FFmpeg

- **`/v1/ffmpeg/compose`**
  - Provides a flexible interface to FFmpeg for complex media processing operations.

### Image

- **`/v1/image/convert/video`**
  - Transforms a static image into a video with custom duration and zoom effects.

- **`/v1/image/screenshot/webpage`**
  - Captures screenshots of web pages using Playwright with advanced options like viewport size, device emulation, and custom HTML/CSS/JS injection.

### Media

- **`/v1/media/convert`**
  - Converts media files from one format to another with customizable codec options.

- **`/v1/media/convert/mp3`**
  - Converts various media formats specifically to MP3 audio.

- **`/v1/BETA/media/download`**
  - Downloads media content from various online sources using yt-dlp.

- **`/v1/media/feedback`**
  - Provides a web interface for collecting and displaying feedback on media content.

- **`/v1/media/transcribe`**
  - Transcribes or translates audio/video content from a provided media URL.

- **`/v1/media/silence`**
  - Detects silence intervals in a given media file.

- **`/v1/media/metadata`**
  - Extracts comprehensive metadata from media files including format, codecs, resolution, and bitrates.

### S3

- **`/v1/s3/upload`**
  - Uploads files to Amazon S3 storage by streaming directly from a URL.

### Toolkit

- **`/v1/toolkit/authenticate`**
  - Provides a simple authentication mechanism to validate API keys.

- **`/v1/toolkit/test`**
  - Verifies that the Sync Scribe Studio API is properly installed and functioning.

- **`/v1/toolkit/job/status`**
  - Retrieves the status of a specific job by its ID.

- **`/v1/toolkit/jobs/status`**
  - Retrieves the status of all jobs within a specified time range.

### Video

- **`/v1/video/caption`**
  - Adds customizable captions to videos with various styling options.

- **`/v1/video/concatenate`**
  - Combines multiple videos into a single continuous video file.

- **`/v1/video/thumbnail`**
  - Extracts a thumbnail image from a specific timestamp in a video.

- **`/v1/video/cut`**
  - Cuts specified segments from a video file with optional encoding settings.

- **`/v1/video/split`**
  - Splits a video into multiple segments based on specified start and end times.

- **`/v1/video/trim`**
  - Trims a video by keeping only the content between specified start and end times.

---

## Deployment Options

### Docker Deployment (Recommended)

#### Pull from Docker Hub

```bash
docker pull bmurrtech/sync-scribe-studio:latest
```

#### Or Build Locally

```bash
docker build -t bmurrtech/sync-scribe-studio:latest .
```

### General Environment Variables

#### `API_KEY`
- **Purpose**: Used for API authentication.
- **Requirement**: Mandatory.

---

### S3-Compatible Storage Environment Variables

#### `S3_ENDPOINT_URL`
- **Purpose**: Endpoint URL for the S3-compatible service.
- **Requirement**: Mandatory if using S3-compatible storage.

#### `S3_ACCESS_KEY`
- **Purpose**: The access key for the S3-compatible storage service.
- **Requirement**: Mandatory if using S3-compatible storage.

#### `S3_SECRET_KEY`
- **Purpose**: The secret key for the S3-compatible storage service.
- **Requirement**: Mandatory if using S3-compatible storage.

#### `S3_BUCKET_NAME`
- **Purpose**: The bucket name for the S3-compatible storage service.
- **Requirement**: Mandatory if using S3-compatible storage.

#### `S3_REGION`
- **Purpose**: The region for the S3-compatible storage service.
- **Requirement**: Mandatory if using S3-compatible storage, "None" is acceptible for some s3 providers.

---

### Google Cloud Storage (GCP) Environment Variables

#### `GCP_SA_CREDENTIALS`
- **Purpose**: The JSON credentials for the GCP Service Account.
- **Requirement**: Mandatory if using GCP storage.

#### `GCP_BUCKET_NAME`
- **Purpose**: The name of the GCP storage bucket.
- **Requirement**: Mandatory if using GCP storage.

---

### Performance Tuning Variables

#### `MAX_QUEUE_LENGTH`
- **Purpose**: Limits the maximum number of concurrent tasks in the queue.
- **Default**: 0 (unlimited)
- **Recommendation**: Set to a value based on your server resources, e.g., 10-20 for smaller instances.

#### `GUNICORN_WORKERS`
- **Purpose**: Number of worker processes for handling requests.
- **Default**: Number of CPU cores + 1
- **Recommendation**: 2-4× number of CPU cores for CPU-bound workloads.

#### `GUNICORN_TIMEOUT`
- **Purpose**: Timeout (in seconds) for worker processes.
- **Default**: 30
- **Recommendation**: Increase for processing large media files (e.g., 300-600).

---

### Storage Configuration

#### `LOCAL_STORAGE_PATH`
- **Purpose**: Directory for temporary file storage during processing.
- **Default**: /tmp
- **Recommendation**: Set to a path with sufficient disk space for your expected workloads.

### Notes
- Ensure all required environment variables are set based on the storage provider in use (GCP or S3-compatible). 
- Missing any required variables will result in errors during runtime.
- Performance variables can be tuned based on your workload and available resources.

### Run the Container

```bash
docker run -d -p 8080:8080 \
  # Authentication (required)
  -e API_KEY=your_secure_api_key \
  
  # Storage Configuration (choose one)
  
  # Option 1: S3-Compatible Storage
  -e S3_ENDPOINT_URL=https://s3.amazonaws.com \
  -e S3_ACCESS_KEY=your_access_key \
  -e S3_SECRET_KEY=your_secret_key \
  -e S3_BUCKET_NAME=your_bucket \
  -e S3_REGION=us-east-1 \
  
  # Option 2: Google Cloud Storage
  # -e GCP_SA_CREDENTIALS='${GCP_SERVICE_ACCOUNT_JSON}' \
  # -e GCP_BUCKET_NAME=your_gcs_bucket \
  
  # Performance & Security
  -e MAX_QUEUE_LENGTH=20 \
  -e GUNICORN_WORKERS=4 \
  -e GUNICORN_TIMEOUT=300 \
  -e LOCAL_STORAGE_PATH=/tmp \
  
  bmurrtech/sync-scribe-studio-api:latest
```

## Cloud Platform Deployment

### Production Environments

#### Google Cloud Run
- **Best for**: Cost-effective production deployments
- **Pros**: Pay-per-use pricing, automatic scaling, managed infrastructure
- **Limitations**: 60-minute timeout for HTTP requests
- **Guide**: [Deploy to Google Cloud Run](./docs/cloud-installation/gcp.md)

#### Digital Ocean App Platform
- **Best for**: Simple deployments with predictable costs
- **Pros**: Easy setup, integrated monitoring, automatic SSL
- **Note**: Use webhook_url for long-running processes (>1 minute)
- **Guide**: [Deploy to Digital Ocean](./docs/cloud-installation/do.md)

#### Self-Hosted Docker
- **Best for**: Complete control and customization
- **Pros**: No vendor lock-in, unlimited processing time
- **Requirements**: Linux server with Docker installed
- **Guide**: [Docker Compose Setup](./docker-compose.md)

### Development Environment

#### Local Development Stack
Complete development environment with MinIO (S3-compatible storage) and n8n (workflow automation):
- **Guide**: [Local Development Setup](./docker-compose.local.minio.n8n.md)

## Quick Start Guide

### 1. Deploy the API
Choose your preferred deployment method from the options above.

### 2. Configure Authentication
Set your `API_KEY` environment variable during deployment.

### 3. Test the Installation
```bash
curl -X GET https://your-api-url/v1/toolkit/test \
  -H "X-API-Key: your_api_key"
```

### 4. Test the API
- Use any API testing tool (Postman, curl, etc.)
- Configure environment variables:
  - `base_url`: Your API URL
  - `x-api-key`: Your API key
- Test example endpoints

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB available
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Docker**: Version 20.10+

### Recommended for Production
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: 100Mbps+ bandwidth

## Performance Optimization

### Scaling Guidelines

| Workload | Workers | Timeout | Queue Length | RAM |
|----------|---------|---------|--------------|-----|
| Light | 2 | 120s | 10 | 4GB |
| Medium | 4 | 300s | 20 | 8GB |
| Heavy | 8 | 600s | 50 | 16GB |

### Optimization Tips
1. Use S3-compatible storage for large files
2. Enable webhook_url for long-running tasks
3. Configure appropriate worker counts based on CPU cores
4. Monitor queue length to prevent overload

## Monitoring & Maintenance

### Health Checks
```bash
# API Health
curl https://your-api/v1/toolkit/test -H "X-API-Key: your_key"

# Job Status
curl https://your-api/v1/toolkit/jobs/status -H "X-API-Key: your_key"
```

### Logging
- Application logs: `docker logs [container_id]`
- Performance metrics: Monitor via cloud provider dashboard
- Error tracking: Check webhook responses for failures

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Code standards
- Feature requirements
- Pull request process
- Adding new routes ([Guide](docs/adding_routes.md))

## Support

- **Documentation**: Full API docs in `/docs` directory
- **Issues**: [GitHub Issues](https://github.com/bmurrtech/sync-scribe-studio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bmurrtech/sync-scribe-studio/discussions)

## License

This project is licensed under the [GNU General Public License v2.0 (GPL-2.0)](LICENSE).

---

*Sync Scribe Studio API - Advanced media processing and transcription toolkit.*
