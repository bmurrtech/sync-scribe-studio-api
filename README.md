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

## Configuration Guide

SyncScribe Studio API uses environment variables for configuration. This section provides a comprehensive guide organized by complexity level.

### Required Configuration

These variables are mandatory for basic operation:

#### `API_KEY`
- **Purpose**: Primary authentication for API access
- **Format**: String (recommended: 32+ characters)
- **Example**: `your_secure_api_key_here`
- **Security**: Store securely, never commit to version control

#### Storage Provider (Choose One)

**Option 1: S3-Compatible Storage**
```bash
S3_ENDPOINT_URL=https://s3.amazonaws.com          # S3 endpoint URL
S3_ACCESS_KEY=your_access_key                     # Access key ID
S3_SECRET_KEY=your_secret_key                     # Secret access key
S3_BUCKET_NAME=your_bucket                        # Target bucket name
S3_REGION=us-east-1                              # AWS region
```

**Option 2: Google Cloud Storage**
```bash
GCP_SA_CREDENTIALS='{"type":"service_account"...}'  # Service account JSON
GCP_BUCKET_NAME=your_gcs_bucket                    # GCS bucket name
GCP_PROJECT_ID=your_project_id                     # GCP project ID
GCP_STORAGE_BUCKET=your_bucket_name                # Storage bucket
GCP_SA_EMAIL=service@project.iam.gserviceaccount.com
```

---

### Recommended Configuration

These settings improve performance and provide basic security:

#### Performance Tuning
```bash
GUNICORN_WORKERS=4                    # Worker processes (2-4× CPU cores)
GUNICORN_TIMEOUT=300                  # Request timeout (seconds)
MAX_QUEUE_LENGTH=20                   # Concurrent task limit
LOCAL_STORAGE_PATH=/tmp               # Temporary file directory
```

#### Basic Rate Limiting
```bash
RATE_LIMIT_PER_MINUTE=100            # Requests per minute per IP
RATE_LIMIT_BURST=100                 # Burst capacity
RATE_LIMIT_KEY=ip                    # Rate limit by 'ip' or 'api_key'
```

#### ASR (Speech Recognition) Configuration
```bash
# CPU-optimized defaults (recommended for most deployments)
ASR_MODEL_ID=openai/whisper-small    # Model size (tiny/base/small/medium/large-v3)
ASR_DEVICE=auto                      # Auto-detects optimal device (cpu/cuda/auto)
ASR_COMPUTE_TYPE=auto                # Auto-selects precision (int8/float16/float32)
ASR_BEAM_SIZE=5                      # Search width (1-10)
ASR_BATCH_SIZE=auto                  # Auto-sizing: CPU=4, GPU=16, Auto=8
ENABLE_MODEL_WARM_UP=true            # Preload models at startup for better UX
```

---

### Advanced Configuration

These settings provide enhanced security, optimization, and feature control:

#### Security Headers & CORS
```bash
ENABLE_SECURITY_HEADERS=true         # Enable security headers
ALLOWED_ORIGINS=https://app.example.com,https://dashboard.example.com
```

#### Feature Flags
```bash
ENABLE_OPENAI_WHISPER=false         # Use legacy OpenAI Whisper (default: Faster-Whisper)
SKIP_MODEL_WARMUP=false             # Skip model preloading (useful for CI/CD)
APP_DEBUG=false                     # Debug mode (never enable in production)
```

#### ASR Advanced Settings
```bash
ASR_CACHE_DIR=/app/asr_cache        # Model cache directory
WHISPER_CACHE_DIR=/app/whisper_cache # Whisper model cache
HF_HOME=/app/huggingface_cache      # Hugging Face cache
```

#### Application Settings
```bash
APP_NAME=SyncScribeStudio           # Application name
APP_DOMAIN=api.example.com          # Domain (without protocol)
APP_URL=https://api.example.com     # Full application URL
CLOUD_BASE_URL=https://your-api.run.app  # Deployed API URL
LOCAL_BASE_URL=http://localhost:8080     # Local development URL
```

#### Docker Build Configuration (Build-time only)
```bash
BUILD_VARIANT=gpu                   # Build type: 'gpu' or 'cpu'
CUDA_VERSION=12.1.0                 # CUDA version for GPU builds
CUDNN_VERSION=8                     # cuDNN version for GPU builds
```

---

### Configuration Templates

#### Minimal Production Setup
```bash
# Essential configuration for basic deployment
API_KEY=your_secure_api_key_here
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket
S3_REGION=us-east-1
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=300
```

#### High-Performance Production
```bash
# Optimized for high-volume processing
API_KEY=your_secure_api_key_here
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket
S3_REGION=us-east-1

# Performance optimization
GUNICORN_WORKERS=8
GUNICORN_TIMEOUT=600
MAX_QUEUE_LENGTH=50

# Rate limiting
RATE_LIMIT_PER_MINUTE=200
RATE_LIMIT_BURST=300
RATE_LIMIT_KEY=api_key

# ASR optimization
ASR_MODEL_ID=openai/whisper-small
ASR_DEVICE=cuda
ASR_COMPUTE_TYPE=float16
ASR_BATCH_SIZE=32

# Security
ENABLE_SECURITY_HEADERS=true
ALLOWED_ORIGINS=https://yourdomain.com
```

#### Development Setup
```bash
# Local development with debugging
API_KEY=dev_api_key_12345
LOCAL_BASE_URL=http://localhost:8080
APP_DEBUG=true
SKIP_MODEL_WARMUP=true
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=120
LOCAL_STORAGE_PATH=/tmp
ASR_MODEL_ID=openai/whisper-tiny
ASR_DEVICE=cpu
```

### Security Best Practices

1. **API Keys**: Use strong, unique keys (32+ characters)
2. **Environment Variables**: Never commit secrets to version control
3. **Rate Limiting**: Enable appropriate limits for your use case
4. **CORS**: Restrict origins to authorized domains only
5. **Debug Mode**: Always disable in production
6. **Storage**: Use encrypted storage backends when possible
7. **Network**: Deploy behind HTTPS and consider API gateways

## ASR (Automatic Speech Recognition) Optimization

### CPU-First Design Philosophy

SyncScribe Studio API is **optimized for CPU deployments by default** to ensure maximum compatibility and cost-effectiveness across cloud platforms like Google Cloud Run, Railway, and Docker containers.

#### Key Optimizations Made

**1. Model Upgrade**
- **Changed**: Default model from `whisper-base` → `whisper-small`
- **Benefit**: Better accuracy/performance balance (optimal CPU sweet spot)
- **Impact**: ~15% accuracy improvement with minimal CPU overhead

**2. Device & Compute Auto-Detection**
- **Changed**: `ASR_DEVICE` default: `cpu` → `auto`
- **Changed**: `ASR_COMPUTE_TYPE` default: `int8` → `auto`
- **Benefit**: Automatically selects optimal settings per environment
  - **CPU**: `device=cpu`, `compute_type=int8` (quantized for speed)
  - **GPU**: `device=cuda`, `compute_type=float16` (optimal VRAM/speed balance)
  - **Auto**: Detects available hardware and optimizes accordingly

**3. Smart Batch Sizing**
- **Added**: Dynamic batch size based on device detection
  - **CPU**: Batch size `4` (CPU has limited batch benefits)
  - **GPU**: Batch size `16` (conservative, can scale to 32)
  - **Auto**: Batch size `8` (safe middle ground)

**4. Comprehensive Model Mappings**
- **Added**: `whisper-tiny` mapping (was missing)
- **Added**: Community turbo variants (`large-v3-turbo`)
- **Added**: Safe fallback to `small` for unknown models with warning

**5. Enhanced User Experience**
- **Changed**: `ENABLE_MODEL_WARM_UP` default: `false` → `true`
- **Benefit**: Better first-request latency (trades cold start time for UX)
- **Added**: `SKIP_MODEL_WARMUP` for CI/CD scenarios

### Default Behavior by Environment

#### Cloud Run (CPU-only)
```yaml
ASR_DEVICE: auto          # → Detects as 'cpu'
ASR_COMPUTE_TYPE: auto    # → Selects 'int8' for speed
ASR_BATCH_SIZE: auto      # → Uses 4 for CPU optimization
ASR_MODEL_ID: openai/whisper-small  # → CPU sweet spot
ENABLE_MODEL_WARM_UP: true  # → Models load at startup
```

#### GPU Environment
```yaml
ASR_DEVICE: auto          # → Detects as 'cuda'
ASR_COMPUTE_TYPE: auto    # → Selects 'float16' for VRAM efficiency
ASR_BATCH_SIZE: auto      # → Uses 16 for GPU optimization
ASR_MODEL_ID: openai/whisper-small  # → Can upgrade to medium/large
ENABLE_MODEL_WARM_UP: true  # → GPU models warm up faster
```

#### Fallback Behavior
- **Faster-Whisper fails** → Auto-switches to OpenAI Whisper
- **Unknown model** → Falls back to `small` with warning
- **Warm-up enabled** → Models load at startup (better first request)
- **CUDA unavailable** → Gracefully falls back to CPU with optimal settings

---

### GPU Configuration Guide

For maximum performance with GPU acceleration:

#### 1. Docker GPU Setup

**Build GPU-enabled container:**
```bash
# Build with GPU support
docker build --build-arg BUILD_VARIANT=gpu -t sync-scribe-gpu:latest .

# Or pull GPU-enabled image
docker pull bmurrtech/sync-scribe-studio:gpu
```

**Run with GPU access:**
```bash
docker run -d -p 8080:8080 \
  --gpus all \
  -e API_KEY=your_secure_api_key \
  -e ASR_DEVICE=cuda \
  -e ASR_COMPUTE_TYPE=float16 \
  -e ASR_BATCH_SIZE=32 \
  -e ASR_MODEL_ID=openai/whisper-medium \
  bmurrtech/sync-scribe-studio:gpu
```

#### 2. Optimal GPU Settings

**High-Performance GPU Configuration:**
```bash
# GPU-optimized settings
ASR_DEVICE=cuda                    # Force CUDA usage
ASR_COMPUTE_TYPE=float16          # Balance of speed/accuracy
ASR_BATCH_SIZE=32                 # Larger batches for GPU
ASR_MODEL_ID=openai/whisper-medium  # Larger model for GPU
ENABLE_MODEL_WARM_UP=true         # Faster GPU warm-up

# Performance tuning
GUNICORN_WORKERS=4                # Fewer workers for GPU memory
GUNICORN_TIMEOUT=900              # Longer timeout for large models
MAX_QUEUE_LENGTH=100              # More concurrent processing
```

**Memory-Conscious GPU Configuration:**
```bash
# Conservative GPU settings for limited VRAM
ASR_DEVICE=cuda
ASR_COMPUTE_TYPE=int8             # More aggressive quantization
ASR_BATCH_SIZE=16                 # Smaller batches
ASR_MODEL_ID=openai/whisper-small # Smaller model
GUNICORN_WORKERS=2                # Fewer workers to save VRAM
```

#### 3. Multi-GPU Setup

For multiple GPU systems:
```bash
# Environment variables
CUDA_VISIBLE_DEVICES=0,1          # Use specific GPUs
ASR_DEVICE=cuda                   # Enable CUDA
GUNICORN_WORKERS=8                # More workers for multi-GPU

# Docker with specific GPU
docker run --gpus '"device=0,1"' ... # Use GPUs 0 and 1
```

#### 4. GPU Performance Monitoring

**Check GPU utilization:**
```bash
# Monitor GPU usage
nvidia-smi -l 1

# Check Docker container GPU access
docker exec [container_id] nvidia-smi
```

**Health endpoint shows current backend:**
```bash
curl -H "X-API-Key: your_key" https://your-api/v1/toolkit/test
# Response includes:
# "asr_backend": "faster_whisper",
# "asr_device": "cuda",
# "asr_compute_type": "float16"
```

### Performance Guidelines

| Use Case | Device | Workers | Timeout | Queue | ASR Model | Compute Type | Batch Size |
|----------|---------|---------|---------|-------|-----------|-------------|------------|
| **CPU Light** | auto/cpu | 2 | 120s | 10 | whisper-tiny | int8 | 4 |
| **CPU Medium** | auto/cpu | 4 | 300s | 20 | whisper-small | int8 | 4 |
| **CPU Heavy** | cpu | 8 | 600s | 50 | whisper-small | int8 | 8 |
| **GPU Medium** | cuda | 4 | 300s | 30 | whisper-medium | float16 | 16 |
| **GPU Heavy** | cuda | 6 | 900s | 100 | whisper-large-v3 | float16 | 32 |
| **GPU Enterprise** | cuda | 8+ | 1200s | 200+ | whisper-large-v3 | float16 | 64 |

### Troubleshooting

**Common Issues:**
- **"Model loading failed"**: Check ASR_CACHE_DIR permissions and disk space
- **"Rate limit exceeded"**: Adjust RATE_LIMIT_PER_MINUTE or RATE_LIMIT_BURST
- **"Storage access denied"**: Verify S3/GCP credentials and bucket permissions
- **"Worker timeout"**: Increase GUNICORN_TIMEOUT for large file processing

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
