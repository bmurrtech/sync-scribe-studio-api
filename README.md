# Sync Scribe Studio API

**The most accurate and fastest ASR transcription API** - Outperforms OpenAI Whisper base models with **42% faster processing** and **superior accuracy** on long-form content. Self-hosted media processing platform that eliminates expensive third-party API subscriptions.

## 🏆 **Why Choose Sync Scribe Studio for Transcription**

- **🎯 Superior Accuracy**: Proper phrase recognition ("hallowed be" vs "hall of be"), professional formality preserved
- **⚡ 42% Faster**: ~60s vs ~85s on 42-minute audio compared to legacy solutions  
- **⚙️ Self-Hosted**: Complete control, no API limits, eliminate subscription costs
- **📈 100x Real-Time**: Process 42 minutes of audio in ~69 seconds

📊 **[Complete Performance Analysis](docs/performance-analysis.md)** | 🏆 **[Optimal Configurations](docs/optimal-configurations.md)**

## 🗺️ **Feature Roadmap**

### ✅ **Available Now**
```
🎯 Superior ASR Transcription     🎵 Audio/Video Processing
🎬 Video Captioning               ☁️  Cloud Storage Integration
🖼️  Web Screenshots               🐍 Python Code Execution
⚙️  FFmpeg Integration            🔐 Enterprise Security
📊 Performance Profiles          🚀 Docker Hub Images
```

### 🚧 **In Development**
```
🖼️  Self-Hosted Image Generation
   ├─ FLUX.1 [dev] model integration
   ├─ LoRA fine-tuning support
   └─ Custom prompt optimization

🗣️  Text-to-Speech (TTS)
   ├─ Kokoro TTS (82M parameters)
   ├─ Open-weight model support
   └─ Multi-language voice synthesis

🎬 Image & Text to Video
   ├─ img2vid generation (Wan v2.2-a14b)
   ├─ txt2vid capabilities
   └─ Self-hostable open-source models
```

### 🔮 **Future Enhancements**
```
🎨 Advanced Media AI            🌐 Multi-Modal Processing
🔊 Real-time Audio Processing   📱 Mobile SDK Support
🤖 Custom Model Fine-tuning     🔄 Workflow Automation
```

## 🔐 Security Features

### 🔑 Authentication & Authorization
- **API Key Authentication**: Secure access control via `X-API-Key` header
- **Environment-based Configuration**: Sensitive credentials stored securely
- **Request Validation**: Comprehensive payload validation on all endpoints

### 🛡️ Rate Limiting & Protection
- **Configurable Rate Limits**: Prevent abuse with customizable thresholds
- **Queue Management**: Control concurrent processing with `MAX_QUEUE_LENGTH`
- **Timeout Protection**: Configurable timeouts for long-running operations

### 🔒 Security Headers
- **CORS Configuration**: Controlled cross-origin resource sharing
- **Content-Type Validation**: Strict input validation
- **Secure File Handling**: Sandboxed file operations with cleanup

### 🛡️ Data Protection
- **Temporary File Cleanup**: Automatic removal of processed files
- **No Data Retention**: Files processed in memory when possible
- **Encrypted Storage**: Support for encrypted cloud storage backends

## Quick Start

### 🖥️ **CPU Deployment (Default Balanced Profile)**
| Variable Name | Value | Notes |
|---------------|-------|-------|
| `API_KEY` | `your_secure_api_key_here` | Required |
| `ASR_PROFILE` | `balanced` | Default (whisper-small, auto-optimized) |

```bash
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here bmurrtech/sync-scribe-studio-api:latest
```

### 🚀 **GPU Deployment (Default Balanced Profile)**
| Variable Name | Value | Notes |
|---------------|-------|-------|
| `API_KEY` | `your_secure_api_key_here` | Required |
| `ASR_DEVICE` | `auto` | Auto-detects CUDA |
| `ASR_PROFILE` | `balanced` | Default (whisper-small, auto-optimized) |

```bash
docker run -d -p 8080:8080 --gpus all -e API_KEY=your_secure_api_key_here -e ASR_DEVICE=auto bmurrtech/sync-scribe-studio-api:gpu
```

### ⚡ **Performance Profile Configurations (42-minute benchmark)**

| Profile | Model | Use Case | Speed (42min audio) | Accuracy | Hardware | Variable | Value |
|---------|-------|----------|---------------------|----------|----------|----------|-------|
| **🏆 Accuracy-Turbo** | large-v3-turbo | **Best overall** | ~69s | ⭐⭐⭐⭐⭐ | 6GB+ VRAM | `ASR_PROFILE` | `accuracy-turbo` |
| **⚡ Speed** | small | **Fastest processing** | ~60s | ⭐⭐⭐⭐ | 1GB+ VRAM | `ASR_PROFILE` | `speed` |
| **💻 Balanced** | small | General purpose (CPU) | ~27s (4min) | ⭐⭐⭐ | 4GB RAM | `ASR_PROFILE` | `balanced` |
| **❌ Accuracy** | large-v3 | Not recommended | ~184s | ⚠️ Glitches | 10GB+ VRAM | - | - |

> **💾 Hardware Requirements**: Speed/Balanced profiles work on modest CPU hardware. Accuracy profile requires NVIDIA GPU with 10-12GB VRAM, Accuracy-Turbo requires 6-8GB VRAM. For detailed system specs, GPU compatibility, and performance benchmarks, see [ASR Performance Profiles](docs/ASR_PERFORMANCE_PROFILES.md).

**Speed Profile (Maximum Throughput):**
```bash
# Fastest transcription - greedy decoding, aggressive VAD
docker run -d -p 8080:8080 \
  -e API_KEY=your_secure_api_key_here \
  -e ASR_PROFILE=speed \
  bmurrtech/sync-scribe-studio-api:latest
```

**Balanced Profile (Default - General Purpose):**
```bash
# Balanced transcription - whisper-small with beam search (DEFAULT)
docker run -d -p 8080:8080 \
  -e API_KEY=your_secure_api_key_here \
  bmurrtech/sync-scribe-studio-api:latest
```

**Accuracy Profile (Not Recommended - Use Accuracy-Turbo Instead):**
```bash
# Note: This profile has glitchy transcripts - use accuracy-turbo instead
# docker run -d -p 8080:8080 --gpus all \
#   -e API_KEY=your_secure_api_key_here \
#   -e ASR_DEVICE=auto \
#   -e ASR_PROFILE=accuracy \
#   bmurrtech/sync-scribe-studio-api:gpu
```

**Accuracy-Turbo Profile (Best of Both Worlds):**
```bash
# Large model accuracy at 2-3x speed - ideal for production
docker run -d -p 8080:8080 --gpus all \
  -e API_KEY=your_secure_api_key_here \
  -e ASR_DEVICE=auto \
  -e ASR_PROFILE=accuracy-turbo \
  bmurrtech/sync-scribe-studio-api:gpu
```

> **📊 Advanced Performance Tuning**: For detailed ASR profiles, deterministic decoding, VAD optimization, and performance analysis, see [ASR Performance Profiles](docs/ASR_PERFORMANCE_PROFILES.md).  
> **🏆 Optimal Configurations**: For data-driven recommendations by use case, see [Optimal Configurations Guide](docs/optimal-configurations.md).

### ✅ **Test Your Deployment**
```bash
curl -X GET http://localhost:8080/v1/toolkit/test -H "X-API-Key: your_secure_api_key_here"
```

> **📁 Storage Configuration**: Only required for `response_type=cloud` in media endpoints. 
> For S3/GCS setup, see [Configuration Guide](docs/configuration.md).

*Note: `ASR_DEVICE=auto` detects CUDA availability and optimizes automatically.*

---

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
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here --name sync-scribe-cpu bmurrtech/sync-scribe-studio-api:latest
```

**Quick Deploy - GPU:**
```bash
docker run -d -p 8080:8080 --gpus all -e API_KEY=your_secure_api_key_here -e ASR_DEVICE=auto --name sync-scribe-gpu bmurrtech/sync-scribe-studio-api:gpu
```

**Apple Silicon (M1/M2/M3):**
```bash
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here --platform linux/arm64 --name sync-scribe-cpu bmurrtech/sync-scribe-studio-api:arm64
```

> **📚 Complete Local Guide**: For platform compatibility, CUDA setup, development mode, troubleshooting, and advanced configurations, see [Local Deployment Guide](docs/local-deployment.md).

### 🐳 **Docker Hub Images**

**Official Docker Hub Repository**: [bmurrtech/sync-scribe-studio-api](https://hub.docker.com/repository/docker/bmurrtech/sync-scribe-studio-api/general)

#### Available Tags & Architecture Guide

| Tag | Architecture | Best For | Use Case |
|-----|--------------|----------|----------|
| `latest` | amd64 | **Production (Recommended)** | Stable, broadest compatibility, Cloud Run |
| `gpu` | amd64 + CUDA | **GPU Production** | NVIDIA GPU acceleration |
| `arm64` | arm64 | **Apple Silicon & ARM** | M1/M2/M3 Macs, ARM64 servers |
| `vX.Y.Z-*` | Various | **Testing Only** | Temporary snapshots, auto-cleaned |

#### Pull Commands

**Stable Production (Recommended):**
```bash
docker pull bmurrtech/sync-scribe-studio-api:latest
```

**GPU Production:**
```bash
docker pull bmurrtech/sync-scribe-studio-api:gpu
```

**Apple Silicon:**
```bash
docker pull bmurrtech/sync-scribe-studio-api:arm64
```

#### Build Locally (Alternative)

```bash
docker build -t bmurrtech/sync-scribe-studio-api:latest .
```


## 📚 Additional Resources

### Performance & Optimization
- **[📊 Performance Analysis](./docs/performance-analysis.md)** - Complete 42-minute benchmark data, accuracy comparison vs OpenAI Whisper base
- **[🏆 Optimal Configurations](./docs/optimal-configurations.md)** - Data-driven recommendations for different use cases and hardware

### Configuration & Setup
- **[Configuration Guide](./docs/configuration.md)** - Comprehensive environment variables, performance tuning, and security settings
- **[Local Deployment Guide](./docs/local-deployment.md)** - Platform compatibility, CUDA setup, development mode, and troubleshooting
- **[ASR Performance Profiles](./docs/ASR_PERFORMANCE_PROFILES.md)** - Detailed ASR profiles, benchmarks, and optimization

### Cloud Deployment
- **[Google Cloud Run Guide](./docs/cloud-installation/gcp.md)** - Cost-effective production deployment with automatic scaling
- **[Digital Ocean Guide](./docs/cloud-installation/do.md)** - Simple deployment with predictable pricing
- **[Docker Compose Setup](./docker-compose.md)** - Self-hosted deployment with complete control

### Development
- **[Local Development Stack](./docker-compose.local.minio.n8n.md)** - Development environment with MinIO and n8n
- **[Adding Routes Guide](./docs/adding_routes.md)** - Contributing new API endpoints

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

Thanks to the original creators and maintainers of the open-source and permissively licensed software that makes Sync Scribe Studio possible:

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - Media downloading and extraction
- **[FFmpeg](https://github.com/FFmpeg/FFmpeg)** - Comprehensive media processing framework
- **[OpenAI Whisper](https://github.com/openai/whisper)** - Robust speech recognition via large-scale weak supervision
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** - Fast inference engine for Whisper models
- **[CTranslate2](https://github.com/OpenNMT/CTranslate2)** - Fast inference engine for Transformer models
- **[no-code-architects-toolkit](https://github.com/stephengpope/no-code-architects-toolkit)** by Stephen G. Pope - Original concept inspiration
- **[Playwright](https://github.com/microsoft/playwright)** - Web testing and automation framework

This project is an independent implementation and is not affiliated with or endorsed by any of the original projects or their maintainers.

## Disclaimer

**USE AT YOUR OWN RISK**: This software is provided "as is" without warranty of any kind. The authors and contributors assume no liability for any damages, losses, or consequences arising from the use of this API. Users are responsible for ensuring compliance with applicable laws and regulations when using this software.

## License

This project is licensed under the [GNU General Public License v2.0 (GPL-2.0)](LICENSE).

---

**Made with ❤️ for humanity** | *Sync Scribe Studio API - Advanced media processing and transcription toolkit.*
