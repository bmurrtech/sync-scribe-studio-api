# Docker Build Instructions

This project supports both CPU-only and GPU-accelerated Docker builds using Docker Buildx for multi-platform support.

## Prerequisites

- Docker 20.10+ with Buildx support
- For GPU variant: NVIDIA Docker runtime (nvidia-docker2)
- For multi-arch builds: Docker Buildx configured

## Build Variants

### 1. GPU Variant (Default)
Includes CUDA 12.1 support with CTranslate2 optimized for NVIDIA GPUs.

```bash
# Build for linux/amd64 (required for Cloud Run)
docker buildx build \
  --platform linux/amd64 \
  --build-arg BUILD_VARIANT=gpu \
  --build-arg CUDA_VERSION=12.1.0 \
  --build-arg CUDNN_VERSION=8 \
  -t bmurrtech/sync-scribe-studio-api:gpu-latest \
  -t bmurrtech/sync-scribe-studio-api:latest \
  .

# For local Apple Silicon testing (optional)
docker buildx build \
  --platform linux/arm64 \
  --build-arg BUILD_VARIANT=cpu \
  -t bmurrtech/sync-scribe-studio-api:macos_apple_silicon \
  .
```

### 2. CPU-Only Variant (CI/Testing)
Lightweight build without CUDA dependencies, suitable for CI pipelines.

```bash
# Build CPU-only variant
docker buildx build \
  --platform linux/amd64 \
  --build-arg BUILD_VARIANT=cpu \
  -t bmurrtech/sync-scribe-studio-api:cpu-latest \
  .

# For CI with model warmup disabled
docker buildx build \
  --platform linux/amd64 \
  --build-arg BUILD_VARIANT=cpu \
  --build-arg SKIP_MODEL_WARMUP=true \
  -t bmurrtech/sync-scribe-studio-api:ci \
  .
```

## Docker Compose Development

For local development, use the provided docker-compose.dev.yml:

```bash
# Build and run GPU variant
docker-compose -f docker-compose.dev.yml up app-gpu

# Build and run CPU variant
docker-compose -f docker-compose.dev.yml up app-cpu

# Build both variants
docker-compose -f docker-compose.dev.yml build
```

## Environment Variables

### Required
- `API_KEY`: API authentication key

### ASR Configuration
- `ENABLE_FASTER_WHISPER`: Enable faster-whisper ASR (true/false)
- `ASR_DEVICE`: Device to use (cuda/cpu/auto)
- `ASR_COMPUTE_TYPE`: Compute precision (float16/int8/float32/auto)
- `ASR_MODEL_ID`: Whisper model to use (e.g., openai/whisper-base)
- `SKIP_MODEL_WARMUP`: Skip model pre-loading on startup (true/false)

### Runtime Configuration
- `GUNICORN_WORKERS`: Number of Gunicorn workers (default: 2)
- `GUNICORN_TIMEOUT`: Request timeout in seconds (default: 300)

## Multi-Architecture Support

Set up Docker Buildx for multi-platform builds:

```bash
# Create and use a new buildx instance
docker buildx create --name mybuilder --use

# Bootstrap the buildx instance
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg BUILD_VARIANT=cpu \
  -t bmurrtech/sync-scribe-studio-api:multiarch \
  --push \
  .
```

## Cloud Run Deployment

**Important**: Cloud Run only supports `linux/amd64` architecture. Always build with `--platform linux/amd64`.

```bash
# Build and push for Cloud Run
docker buildx build \
  --platform linux/amd64 \
  --build-arg BUILD_VARIANT=gpu \
  -t bmurrtech/sync-scribe-studio-api:latest \
  --push \
  .

# Deploy to Cloud Run
gcloud run deploy sync-scribe-studio-api \
  --image bmurrtech/sync-scribe-studio-api:latest \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars ENABLE_FASTER_WHISPER=true,ASR_DEVICE=cpu,ASR_COMPUTE_TYPE=int8
```

## Verification

Verify the image architecture:

```bash
# Check manifest
docker manifest inspect bmurrtech/sync-scribe-studio-api:latest

# Check specific platform
docker inspect bmurrtech/sync-scribe-studio-api:latest | grep Architecture
```

## Notes

1. **CUDA Support**: The GPU variant includes CUDA 12.1 runtime. Ensure your host has compatible NVIDIA drivers (525.60.13 or newer).

2. **Model Caching**: Models are cached in `/app/asr_cache` and `/app/huggingface_cache`. Use Docker volumes to persist across container restarts.

3. **Warm-up Script**: The container runs a warm-up script on startup if `ENABLE_FASTER_WHISPER=true` and `SKIP_MODEL_WARMUP!=true`. This pre-loads the ASR model for faster first inference.

4. **CTranslate2**: Version 4.4.0 is installed, which supports CUDA 12.x. The CPU variant uses int8 quantization for optimal performance.

5. **Base Images**:
   - GPU: `nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04`
   - CPU: `python:3.9-slim`
