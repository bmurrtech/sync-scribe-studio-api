# Configuration Guide

Comprehensive configuration options for Sync Scribe Studio API with user-friendly examples and clear formatting.

## Quick Configuration

### 🖥️ **CPU Deployment (Minimum)**
| Variable Name | Value | Required |
|---------------|-------|----------|
| `API_KEY` | `your_secure_api_key_here` | ✅ |

### 🚀 **GPU Deployment (Minimum)**
| Variable Name | Value | Required |
|---------------|-------|----------|
| `API_KEY` | `your_secure_api_key_here` | ✅ |
| `ASR_DEVICE` | `auto` | ✅ |

### 📁 **Storage Configuration (Optional)**
> Only required when using `response_type=cloud` in media endpoints

**Option 1: S3-Compatible Storage**
| Variable Name | Example Value | Required |
|---------------|---------------|----------|
| `S3_ENDPOINT_URL` | `https://s3.amazonaws.com` | ✅ |
| `S3_ACCESS_KEY` | `your_access_key` | ✅ |
| `S3_SECRET_KEY` | `your_secret_key` | ✅ |
| `S3_BUCKET_NAME` | `your_bucket` | ✅ |
| `S3_REGION` | `us-east-1` | ✅ |

**Option 2: Google Cloud Storage**
| Variable Name | Example Value | Required |
|---------------|---------------|----------|
| `GCP_SA_CREDENTIALS` | `'{"type":"service_account"...}'` | ✅ |
| `GCP_BUCKET_NAME` | `your_gcs_bucket` | ✅ |
| `GCP_PROJECT_ID` | `your_project_id` | ⚠️ |
| `GCP_SA_EMAIL` | `service@project.iam.gserviceaccount.com` | ⚠️ |

---

## Performance Configuration

### 🚀 **Application Performance**
| Variable Name | Default | Options | Purpose |
|---------------|---------|---------|----------|
| `GUNICORN_WORKERS` | `4` | `2-8+` | Worker processes (2-4× CPU cores) |
| `GUNICORN_TIMEOUT` | `300` | `120-1200` | Request timeout (seconds) |
| `MAX_QUEUE_LENGTH` | `20` | `10-200+` | Concurrent task limit |
| `LOCAL_STORAGE_PATH` | `/tmp` | Any path | Temporary file directory |

### 🎤 **ASR (Speech Recognition) Advanced Settings**
| Variable Name | Default | Options | Purpose |
|---------------|---------|---------|----------|
| `ASR_MODEL_ID` | `openai/whisper-small` | `tiny`, `base`, `small`, `medium`, `large-v3` | Model size selection |
| `ASR_DEVICE` | `auto` | `cpu`, `cuda`, `auto` | Processing device |
| `ASR_COMPUTE_TYPE` | `auto` | `int8`, `float16`, `float32`, `auto` | Model precision |
| `ASR_BEAM_SIZE` | `5` | `1-10` | Search width for decoding |
| `ASR_BATCH_SIZE` | `auto` | `1-64`, `auto` | Batch processing size |
| `ASR_CACHE_DIR` | `/app/asr_cache` | Any path | Model cache directory |
| `WHISPER_CACHE_DIR` | `/app/whisper_cache` | Any path | Whisper model cache |
| `HF_HOME` | `/app/huggingface_cache` | Any path | Hugging Face cache |
| `ENABLE_MODEL_WARM_UP` | `true` | `true`, `false` | Preload models at startup |
| `SKIP_MODEL_WARMUP` | `false` | `true`, `false` | Skip model preloading |
| `ENABLE_OPENAI_WHISPER` | `false` | `true`, `false` | Use legacy OpenAI Whisper |

---

## Security Configuration

### 🔒 **Rate Limiting**
| Variable Name | Default | Options | Purpose |
|---------------|---------|---------|----------|
| `RATE_LIMIT_PER_MINUTE` | `100` | `50-1000+` | Requests per minute per IP |
| `RATE_LIMIT_BURST` | `100` | `50-500+` | Burst capacity |
| `RATE_LIMIT_KEY` | `ip` | `ip`, `api_key` | Rate limit identifier |

### 🔒 **Security Headers & CORS**
| Variable Name | Default | Example | Purpose |
|---------------|---------|---------|----------|
| `ENABLE_SECURITY_HEADERS` | `true` | `true`, `false` | Enable security headers |
| `ALLOWED_ORIGINS` | _(empty)_ | `https://app.example.com` | CORS allowed origins |

### 🛠️ **Feature Flags**
| Variable Name | Default | Options | Purpose |
|---------------|---------|---------|----------|
| `APP_DEBUG` | `false` | `true`, `false` | Debug mode (never enable in production) |

---

## Application Settings

### 🌐 **Application Configuration**
| Variable Name | Default | Example | Purpose |
|---------------|---------|---------|----------|
| `APP_NAME` | `SyncScribeStudio` | `MyAPI` | Application name |
| `APP_DOMAIN` | _(auto)_ | `api.example.com` | Domain (without protocol) |
| `APP_URL` | _(auto)_ | `https://api.example.com` | Full application URL |
| `CLOUD_BASE_URL` | _(empty)_ | `https://your-api.run.app` | Deployed API URL |
| `LOCAL_BASE_URL` | `http://localhost:8080` | `http://localhost:3000` | Local development URL |
| `SSL_EMAIL` | _(empty)_ | `user@example.com` | SSL certificate email |

---

## Docker Build Configuration

### 🐳 **Build-Time Variables**
*These variables are only used during Docker image builds*

| Variable Name | Default | Options | Purpose |
|---------------|---------|---------|----------|
| `BUILD_VARIANT` | `gpu` | `gpu`, `cpu` | Build type selection |
| `CUDA_VERSION` | `12.1.0` | `11.8+`, `12.x` | CUDA version for GPU builds |
| `CUDNN_VERSION` | `8` | `8`, `9` | cuDNN version for GPU builds |

---

## Configuration Templates

### Minimal Production Setup
```bash
# Essential configuration for basic deployment
API_KEY=your_secure_api_key_here
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket
S3_REGION=us-east-1
```

### High-Performance Production
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

# Security
ENABLE_SECURITY_HEADERS=true
ALLOWED_ORIGINS=https://yourdomain.com
```

### GPU-Optimized Configuration
```bash
# GPU deployment with optimization
API_KEY=your_secure_api_key_here
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket
S3_REGION=us-east-1

# GPU-specific settings
ASR_DEVICE=cuda                     # Force CUDA usage
ASR_COMPUTE_TYPE=float16           # Balance of speed/accuracy
ASR_BATCH_SIZE=32                  # Larger batches for GPU
ASR_MODEL_ID=openai/whisper-medium # Larger model for GPU

# Performance tuning for GPU
GUNICORN_WORKERS=4                 # Fewer workers for GPU memory
GUNICORN_TIMEOUT=900               # Longer timeout for large models
MAX_QUEUE_LENGTH=100               # More concurrent processing
```

### Development Setup
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
```

---

## GPU Configuration Guide

### Auto-Detection (Recommended)
```bash
# Let the system auto-detect and optimize
ASR_DEVICE=auto                    # Detects CUDA availability
ASR_COMPUTE_TYPE=auto              # Selects optimal precision
ASR_BATCH_SIZE=auto                # Chooses optimal batch size
```

### Manual GPU Configuration
```bash
# Explicit GPU settings
ASR_DEVICE=cuda                    # Force CUDA usage
ASR_COMPUTE_TYPE=float16          # Balance of speed/accuracy
ASR_BATCH_SIZE=32                 # Larger batches for GPU
ASR_MODEL_ID=openai/whisper-medium # Larger model for GPU
```

### Memory-Conscious GPU Settings
```bash
# Conservative GPU settings for limited VRAM
ASR_DEVICE=cuda
ASR_COMPUTE_TYPE=int8             # More aggressive quantization
ASR_BATCH_SIZE=16                 # Smaller batches
ASR_MODEL_ID=openai/whisper-small # Smaller model
GUNICORN_WORKERS=2                # Fewer workers to save VRAM
```

### Multi-GPU Setup
```bash
CUDA_VISIBLE_DEVICES=0,1          # Use specific GPUs
ASR_DEVICE=cuda                   # Enable CUDA
GUNICORN_WORKERS=8                # More workers for multi-GPU
```

---

## Performance Guidelines

| Use Case | Device | Workers | Timeout | Queue | ASR Model | Compute Type | Batch Size |
|----------|---------|---------|---------|-------|-----------|-------------|------------|
| **CPU Light** | auto | 2 | 120s | 10 | whisper-tiny | auto | auto |
| **CPU Medium** | auto | 4 | 300s | 20 | whisper-small | auto | auto |
| **CPU Heavy** | cpu | 8 | 600s | 50 | whisper-small | int8 | 8 |
| **GPU Medium** | auto | 4 | 300s | 30 | whisper-medium | auto | auto |
| **GPU Heavy** | cuda | 6 | 900s | 100 | whisper-large-v3 | float16 | 32 |
| **GPU Enterprise** | cuda | 8+ | 1200s | 200+ | whisper-large-v3 | float16 | 64 |

---

## Security Best Practices

1. **API Keys**: Use strong, unique keys (32+ characters)
2. **Environment Variables**: Never commit secrets to version control
3. **Rate Limiting**: Enable appropriate limits for your use case
4. **CORS**: Restrict origins to authorized domains only
5. **Debug Mode**: Always disable in production
6. **Storage**: Use encrypted storage backends when possible
7. **Network**: Deploy behind HTTPS and consider API gateways

---

## Troubleshooting

**Common Issues:**
- **"Model loading failed"**: Check ASR_CACHE_DIR permissions and disk space
- **"Rate limit exceeded"**: Adjust RATE_LIMIT_PER_MINUTE or RATE_LIMIT_BURST
- **"Storage access denied"**: Verify S3/GCP credentials and bucket permissions
- **"Worker timeout"**: Increase GUNICORN_TIMEOUT for large file processing
- **"CUDA out of memory"**: Reduce ASR_BATCH_SIZE or ASR_MODEL_ID size
- **"Model not found"**: Check ASR_MODEL_ID spelling and model availability

---

## Monitoring & Health Checks

### Health Endpoint
```bash
curl -H "X-API-Key: your_key" https://your-api/v1/toolkit/test
# Response includes current ASR backend, device, and compute type
```

### GPU Monitoring
```bash
# Monitor GPU usage
nvidia-smi -l 1

# Check Docker container GPU access
docker exec [container_id] nvidia-smi
```

### Performance Metrics
- Application logs: `docker logs [container_id]`
- Performance metrics: Monitor via cloud provider dashboard
- Error tracking: Check webhook responses for failures

---

## Attribution

This project is based on concepts from Stephen G. Pope's **No-Code Architect Tool Kit** but is an independent implementation and is not affiliated with or endorsed by Stephen G. Pope or his original work.

## Disclaimer

**USE AT YOUR OWN RISK**: This software is provided "as is" without warranty of any kind. The authors and contributors assume no liability for any damages, losses, or consequences arising from the use of this API. Users are responsible for ensuring compliance with applicable laws and regulations when using this software.

**Made with ❤️ for humanity** under the GNU General Public License v2.0
