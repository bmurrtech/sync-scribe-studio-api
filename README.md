# Sync Scribe Studio API

A comprehensive, self-hosted media processing and transcription platform that eliminates expensive third-party API subscriptions. CPU-optimized by default with automatic GPU acceleration.

## Quick Start

### 🖥️ **CPU Deployment (Default Balanced Profile)**
| Variable Name | Value | Notes |
|---------------|-------|-------|
| `API_KEY` | `your_secure_api_key_here` | Required |
| `ASR_PROFILE` | `balanced` | Default (whisper-small, auto-optimized) |

```bash
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here bmurrtech/sync-scribe-studio:latest
```

### 🚀 **GPU Deployment (Default Balanced Profile)**
| Variable Name | Value | Notes |
|---------------|-------|-------|
| `API_KEY` | `your_secure_api_key_here` | Required |
| `ASR_DEVICE` | `auto` | Auto-detects CUDA |
| `ASR_PROFILE` | `balanced` | Default (whisper-small, auto-optimized) |

```bash
docker run -d -p 8080:8080 --gpus all -e API_KEY=your_secure_api_key_here -e ASR_DEVICE=auto bmurrtech/sync-scribe-studio:gpu
```

### ⚡ **Performance Profile Configurations**

**Speed Profile (Maximum Throughput):**
```bash
# Fastest transcription - greedy decoding, aggressive VAD
docker run -d -p 8080:8080 \
  -e API_KEY=your_secure_api_key_here \
  -e ASR_PROFILE=speed \
  bmurrtech/sync-scribe-studio:latest
```

**Balanced Profile (Default - Good Speed/Accuracy):**
```bash
# Balanced transcription - whisper-small with beam search
docker run -d -p 8080:8080 \
  -e API_KEY=your_secure_api_key_here \
  -e ASR_PROFILE=balanced \
  bmurrtech/sync-scribe-studio:latest
```

**Accuracy Profile (Maximum Quality):**
```bash
# Best quality transcription - large-v3 model with extensive search
docker run -d -p 8080:8080 --gpus all \
  -e API_KEY=your_secure_api_key_here \
  -e ASR_DEVICE=cuda \
  -e ASR_PROFILE=accuracy \
  bmurrtech/sync-scribe-studio:gpu
```

> **📊 Advanced Performance Tuning**: For detailed ASR profiles, deterministic decoding, VAD optimization, and performance analysis, see [ASR Performance Profiles](docs/ASR_PERFORMANCE_PROFILES.md).

### ✅ **Test Your Deployment**
```bash
curl -X GET http://localhost:8080/v1/toolkit/test -H "X-API-Key: your_secure_api_key_here"
```

> **📁 Storage Configuration**: Only required for `response_type=cloud` in media endpoints. 
> For S3/GCS setup, see [Configuration Guide](docs/configuration.md).

*Note: `ASR_DEVICE=auto` detects CUDA availability and optimizes automatically.*

---


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

### 💻 **Local Deployment**

**Quick Deploy - CPU:**
```bash
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here --name sync-scribe-cpu bmurrtech/sync-scribe-studio:latest
```

**Quick Deploy - GPU:**
```bash
docker run -d -p 8080:8080 --gpus all -e API_KEY=your_secure_api_key_here -e ASR_DEVICE=auto --name sync-scribe-gpu bmurrtech/sync-scribe-studio:gpu
```

**Apple Silicon (M1/M2/M3):**
```bash
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here --platform linux/arm64 --name sync-scribe-cpu bmurrtech/sync-scribe-studio:latest
```

> **📚 Complete Local Guide**: For platform compatibility, CUDA setup, development mode, troubleshooting, and advanced configurations, see [Local Deployment Guide](docs/local-deployment.md).

### ☁️ **Cloud Deployment**

#### Pull from Docker Hub

```bash
docker pull bmurrtech/sync-scribe-studio:latest
```

#### Or Build Locally

```bash
docker build -t bmurrtech/sync-scribe-studio:latest .
```

## Configuration

### Basic Configuration (Required)

**CPU Deployment:** Only `API_KEY` is required - everything else auto-optimizes for CPU performance.

**GPU Deployment:** Add `ASR_DEVICE=auto` for automatic CUDA detection and optimization.

**Storage Configuration:** Only required when using `response_type=cloud` in media endpoints.

### Advanced Configuration

For detailed configuration options including performance tuning, security settings, rate limiting, and advanced ASR options, see the [Configuration Guide](./docs/configuration.md).

**Common configurations:**
- **Performance optimization**: Worker counts, timeouts, queue management
- **Security**: Rate limiting, CORS, security headers
- **GPU tuning**: Model selection, batch sizing, memory optimization
- **Development**: Debug modes, local testing, CI/CD settings

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

## Attribution

This project is based on concepts from Stephen G. Pope's **No-Code Architect Tool Kit** but is an independent implementation and is not affiliated with or endorsed by Stephen G. Pope or his original work.

## Disclaimer

**USE AT YOUR OWN RISK**: This software is provided "as is" without warranty of any kind. The authors and contributors assume no liability for any damages, losses, or consequences arising from the use of this API. Users are responsible for ensuring compliance with applicable laws and regulations when using this software.

## License

This project is licensed under the [GNU General Public License v2.0 (GPL-2.0)](LICENSE).

---

**Made with ❤️ for humanity** | *Sync Scribe Studio API - Advanced media processing and transcription toolkit.*
