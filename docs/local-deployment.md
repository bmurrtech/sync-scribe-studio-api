# Local Deployment Guide

Comprehensive guide for deploying Sync Scribe Studio API locally using Docker with platform-specific optimizations and configurations.

## Platform Compatibility

| Platform | CPU Build | GPU Build | Recommended Tag | Notes |
|----------|-----------|-----------|----------------|-------|
| **Intel/AMD x64** | ✅ | ✅ | `latest` / `gpu` | Full compatibility |
| **Apple Silicon (M1/M2/M3)** | ✅ | ❌ | `latest` (ARM64) | Use `--platform linux/arm64` |
| **ARM64 Linux** | ✅ | ⚠️ | `latest` / `gpu` | GPU if CUDA ARM available |
| **Windows (WSL2)** | ✅ | ✅ | `latest` / `gpu` | Requires WSL2 + Docker Desktop |

## Prerequisites

### 🖥️ **CPU Deployment Prerequisites**
| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Docker** | 20.10+ | Latest stable |
| **RAM** | 4GB | 8GB+ |
| **CPU Cores** | 2 | 4+ |
| **Storage** | 10GB | 20GB+ |
| **OS** | Any with Docker | Linux/macOS/Windows 10+ |

### 🚀 **GPU Deployment Prerequisites**
| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **GPU** | NVIDIA GTX 1060 | RTX 3070+ |
| **VRAM** | 4GB | 8GB+ |
| **CUDA** | 11.8+ | 12.1+ |
| **Docker** | 20.10+ with GPU support | Latest with NVIDIA runtime |
| **RAM** | 8GB | 16GB+ |

## Quick Start Commands

### 🖥️ **CPU Deployment**

**Standard CPU Deploy:**
```bash
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here --name sync-scribe-cpu bmurrtech/sync-scribe-studio:latest
```

**Apple Silicon (M1/M2/M3):**
```bash
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here --platform linux/arm64 --name sync-scribe-cpu bmurrtech/sync-scribe-studio:latest
```

**Windows (PowerShell):**
```powershell
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here --name sync-scribe-cpu bmurrtech/sync-scribe-studio:latest
```

### 🚀 **GPU Deployment**

**Standard GPU Deploy:**
```bash
docker run -d -p 8080:8080 --gpus all -e API_KEY=your_secure_api_key_here -e ASR_DEVICE=auto --name sync-scribe-gpu bmurrtech/sync-scribe-studio:gpu
```

**Memory-Conscious GPU (<8GB VRAM):**
```bash
docker run -d -p 8080:8080 --gpus all -e API_KEY=your_secure_api_key_here -e ASR_DEVICE=cuda -e ASR_COMPUTE_TYPE=int8 -e ASR_BATCH_SIZE=8 -e ASR_MODEL_ID=openai/whisper-small --name sync-scribe-gpu bmurrtech/sync-scribe-studio:gpu
```

**High-Performance GPU (16GB+ VRAM):**
```bash
docker run -d -p 8080:8080 --gpus all -e API_KEY=your_secure_api_key_here -e ASR_DEVICE=cuda -e ASR_COMPUTE_TYPE=float16 -e ASR_BATCH_SIZE=32 -e ASR_MODEL_ID=openai/whisper-large-v3 --name sync-scribe-gpu bmurrtech/sync-scribe-studio:gpu
```

## Development Mode

### 🔧 **Development with Live Logs**
```bash
# Run without -d flag to see live output
docker run -p 8080:8080 -e API_KEY=dev_api_key_12345 -e APP_DEBUG=true -e SKIP_MODEL_WARMUP=true --name sync-scribe-dev bmurrtech/sync-scribe-studio:latest
```

### 📁 **Development with Volume Mounting**
```bash
# Mount local directory for development
docker run -d -p 8080:8080 -e API_KEY=dev_api_key_12345 -v $(pwd)/data:/app/data -e LOCAL_STORAGE_PATH=/app/data --name sync-scribe-dev bmurrtech/sync-scribe-studio:latest
```

### 🔄 **Development with Auto-Restart**
```bash
# Use --restart unless-stopped for development
docker run -d -p 8080:8080 --restart unless-stopped -e API_KEY=dev_api_key_12345 -e APP_DEBUG=true --name sync-scribe-dev bmurrtech/sync-scribe-studio:latest
```

## CUDA Setup (GPU Users)

### Prerequisites Check

**Check NVIDIA GPU:**
```bash
nvidia-smi
```

**Test Docker GPU Access:**
```bash
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

**Install NVIDIA Docker Runtime (if needed):**
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### GPU Memory Optimization

| VRAM Available | Recommended Settings |
|----------------|---------------------|
| **4GB** | `ASR_COMPUTE_TYPE=int8`, `ASR_BATCH_SIZE=4`, `whisper-tiny` |
| **6GB** | `ASR_COMPUTE_TYPE=int8`, `ASR_BATCH_SIZE=8`, `whisper-small` |
| **8GB** | `ASR_COMPUTE_TYPE=float16`, `ASR_BATCH_SIZE=16`, `whisper-small` |
| **12GB+** | `ASR_COMPUTE_TYPE=float16`, `ASR_BATCH_SIZE=32`, `whisper-medium` |
| **16GB+** | `ASR_COMPUTE_TYPE=float16`, `ASR_BATCH_SIZE=64`, `whisper-large-v3` |

## Container Management

### 📊 **Status and Monitoring**
| Command | Purpose |
|---------|---------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers |
| `docker logs sync-scribe-cpu` | View container logs |
| `docker logs sync-scribe-cpu -f` | Follow logs in real-time |
| `docker stats sync-scribe-cpu` | Monitor resource usage |

### 🔄 **Container Lifecycle**
| Command | Purpose |
|---------|---------|
| `docker stop sync-scribe-cpu` | Stop container |
| `docker start sync-scribe-cpu` | Start stopped container |
| `docker restart sync-scribe-cpu` | Restart container |
| `docker rm sync-scribe-cpu` | Remove container |
| `docker rm -f sync-scribe-cpu` | Force remove running container |

### 🔄 **Updates and Maintenance**
```bash
# Update to latest version
docker pull bmurrtech/sync-scribe-studio:latest

# Recreate container with new image
docker stop sync-scribe-cpu && docker rm sync-scribe-cpu
docker run -d -p 8080:8080 -e API_KEY=your_secure_api_key_here --name sync-scribe-cpu bmurrtech/sync-scribe-studio:latest
```

## Configuration Options

### 🏗️ **Build Tags Available**
| Tag | Description | Use Case |
|-----|-------------|----------|
| `latest` | CPU-optimized, ARM64 compatible | General use, Apple Silicon |
| `gpu` | NVIDIA CUDA enabled | GPU acceleration |
| `dev` | Development build with debug tools | Development only |

### 🌐 **Port Configuration**
| Internal Port | External Port | Protocol | Purpose |
|---------------|---------------|----------|---------|
| `8080` | `8080` | HTTP | Main API endpoint |
| `8080` | `80` | HTTP | Standard web port |
| `8080` | `443` | HTTPS | With reverse proxy |

### 📁 **Volume Mounting Options**
| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data` | `/app/data` | Persistent data storage |
| `./logs` | `/app/logs` | Log file storage |
| `./models` | `/app/models` | Model cache persistence |
| `./tmp` | `/tmp` | Temporary file storage |

## Environment Variables Reference

### 🔑 **Required Variables**
| Variable | Example | Purpose |
|----------|---------|---------|
| `API_KEY` | `your_secure_api_key_here` | Authentication |

### ⚡ **Performance Variables**
| Variable | Default | Options | Purpose |
|----------|---------|---------|---------|
| `ASR_DEVICE` | `auto` | `cpu`, `cuda`, `auto` | Processing device |
| `ASR_COMPUTE_TYPE` | `auto` | `int8`, `float16`, `float32` | Model precision |
| `ASR_BATCH_SIZE` | `auto` | `1-64` | Batch processing size |
| `ASR_MODEL_ID` | `whisper-small` | `tiny`, `small`, `medium`, `large-v3` | Model size |

### 🛠️ **Development Variables**
| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_DEBUG` | `false` | Enable debug logging |
| `SKIP_MODEL_WARMUP` | `false` | Skip model preloading |
| `LOCAL_STORAGE_PATH` | `/tmp` | Temporary storage path |

## Testing Your Deployment

### ✅ **Health Check**
```bash
curl -X GET http://localhost:8080/v1/toolkit/test -H "X-API-Key: your_secure_api_key_here"
```

### 🔍 **Expected Response**
```json
{
  "status": "success",
  "message": "API is working correctly",
  "version": "latest",
  "asr_backend": "faster-whisper",
  "device": "cpu"
}
```

### 🧪 **Test Transcription**
```bash
curl -X POST http://localhost:8080/v1/media/transcribe \
  -H "X-API-Key: your_secure_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://example.com/sample.mp3",
    "include_text": true,
    "response_type": "direct"
  }'
```

## Troubleshooting

### 🚨 **Common Issues**
| Issue | Solution |
|-------|----------|
| **Container won't start** | Check Docker is running, port 8080 is available |
| **GPU not detected** | Install NVIDIA Docker runtime, check `nvidia-smi` |
| **Out of memory** | Reduce `ASR_BATCH_SIZE` or use smaller model |
| **Slow performance** | Enable GPU or increase CPU allocation |
| **API key error** | Verify API_KEY environment variable is set correctly |

### 🔧 **Debug Commands**
```bash
# Check container environment
docker exec sync-scribe-cpu env

# Access container shell
docker exec -it sync-scribe-cpu bash

# Check GPU inside container
docker exec sync-scribe-gpu nvidia-smi

# View detailed logs
docker logs sync-scribe-cpu --details
```

### 📊 **Performance Monitoring**
```bash
# Monitor system resources
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Monitor GPU usage (GPU deployment)
watch -n 1 nvidia-smi
```

## Best Practices

### 🛡️ **Security**
- Use strong API keys (32+ characters)
- Don't expose port 8080 to the internet without authentication
- Run containers as non-root user in production
- Use Docker secrets for sensitive environment variables

### 🚀 **Performance**
- Use SSD storage for model cache
- Allocate adequate RAM (8GB+ for GPU deployments)
- Monitor container resource usage
- Use GPU for intensive transcription workloads

### 🔄 **Maintenance**
- Regularly update Docker images
- Monitor disk space usage
- Set up log rotation
- Backup important configuration files

---

## Attribution

This project is based on concepts from Stephen G. Pope's **No-Code Architect Tool Kit** but is an independent implementation and is not affiliated with or endorsed by Stephen G. Pope or his original work.

## Disclaimer

**USE AT YOUR OWN RISK**: This software is provided "as is" without warranty of any kind. The authors and contributors assume no liability for any damages, losses, or consequences arising from the use of this API. Users are responsible for ensuring compliance with applicable laws and regulations when using this software.

**Made with ❤️ for humanity** under the GNU General Public License v2.0
