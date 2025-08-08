# Sync Scribe Studio API 🎬🎵

**The Complete Media Processing & YouTube Integration API**

*A powerful, serverless-ready API for media processing, transcription, and YouTube content workflows - designed to replace expensive SaaS subscriptions and save businesses thousands.*

## ✨ Key Features

• **🎥 YouTube Integration** - Download, extract info, convert to MP3/MP4  
• **🎙️ Audio Transcription** - OpenAI Whisper integration for accurate transcripts  
• **🔄 Media Conversion** - Convert between audio/video formats with FFmpeg  
• **📝 Caption Generation** - Add captions and subtitles to videos  
• **🖼️ Image Processing** - Screenshots, image-to-video conversion  
• **☁️ Cloud Storage** - S3, Google Cloud Storage, Dropbox integration  
• **🚀 Serverless Ready** - Deploy to Cloud Run, DigitalOcean, RunPod with GPU support  
• **🔐 Enterprise Security** - X-API-KEY authentication, rate limiting, CORS protection  
• **📊 Production Grade** - Health monitoring, logging, graceful scaling  

## 💰 Cost Savings

Replace expensive SaaS subscriptions and save thousands annually:

• **ChatGPT Whisper API** → Self-hosted transcription  
• **Cloud Convert** → Built-in media conversion  
• **Createomate** → Video processing workflows  
• **JSON2Video** → Programmatic video generation  
• **PDF.co** → Document processing  
• **Placid** → Dynamic image generation  
• **OCodeKit** → All-in-one media toolkit  

---

## 🎯 Primary API Endpoints

### YouTube Integration
- **`/v1/media/youtube/info`** - Extract comprehensive YouTube video metadata, formats, and thumbnails
- **`/v1/media/youtube/mp3`** - Download YouTube videos as MP3 audio with quality selection  
- **`/v1/media/youtube/mp4`** - Download YouTube videos as MP4 with resolution options

### Media Processing
- **`/v1/media/transcribe`** - Transcribe or translate audio/video content with OpenAI Whisper
- **`/v1/media/convert`** - Convert between audio/video formats with customizable codec options
- **`/v1/media/convert/mp3`** - Convert various media formats specifically to MP3 audio

### Image & Video Processing  
- **`/v1/image/convert/video`** - Transform static images into videos with duration and effects
- **`/v1/image/screenshot/webpage`** - Capture screenshots with Playwright
- **`/v1/video/caption`** - Add customizable captions to videos
- **`/v1/video/concatenate`** - Combine multiple videos into single files
- **`/v1/video/thumbnail`** - Extract thumbnails from specific timestamps

### Health & Status
- **`/`** - Service information and documentation
- **`/health`** - Basic health status check
- **`/health/detailed`** - Comprehensive health information with dependencies

**Security Features:**
- 🔐 **Enhanced Security**: Joi schema validation, SSRF/RFI attack prevention
- ⚡ **Rate Limiting**: Progressive rate limiting with configurable thresholds
- 🧹 **Input Sanitization**: Comprehensive sanitization to prevent XSS attacks
- 🛡️ **Security Headers**: Implemented with Helmet.js for enhanced protection
- 📝 **Secure Logging**: No sensitive data exposure in logs

---

## 🚀 Deploy to Cloud-Managed Serverless Platforms

### A. Google Cloud Run (GCP)

```bash
# Deploy to Google Cloud Run
gcloud run deploy sync-scribe-studio-api \
  --image bmurrtech/sync-scribe-studio-api:latest \
  --platform managed \
  --port 8080 \
  --allow-unauthenticated \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars="X_API_KEY=your-secure-api-key"
```

**GPU-Accelerated Processing:**
Google Cloud Run now supports GPU acceleration for dramatically faster AI processing while maintaining serverless cost benefits:

```bash
# Deploy with GPU support for faster transcription
gcloud run deploy sync-scribe-studio-api \
  --image ghcr.io/bmurrtech/sync-scribe-studio-api:latest \
  --platform managed \
  --region us-central1 \
  --cpu 4 \
  --memory 8Gi \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --set-env-vars="X_API_KEY=your-secure-api-key,ENABLE_GPU=true"
```

### B. DigitalOcean App Platform  

**Deploy from Container Image:**
1. Create new app in DigitalOcean App Platform
2. Choose "Deploy from Container Image"  
3. Specify: `ghcr.io/bmurrtech/sync-scribe-studio-api:latest`
4. Set environment variables: `X_API_KEY=your-secure-api-key`
5. Configure port: `8080`
6. Deploy - service runs serverless with auto-scaling

### C. RunPod (GPU-Focused AI Platform)

**For GPU-Accelerated AI Processing:**
1. Go to RunPod dashboard
2. Create new "Serverless Endpoint"  
3. Docker Image: `ghcr.io/bmurrtech/sync-scribe-studio-api:latest`
4. Select GPU type (T4, A100, etc.)
5. Set environment: `X_API_KEY=your-secure-api-key`
6. Configure port mapping: `8080`
7. Deploy - perfect for AI inference workloads

### 🌐 Cloud-Agnostic Tips

• **Vendor Agnostic**: Use Docker Hub or GHCR - supported by most platforms  
• **Environment Port**: Always use `$PORT` environment variable, never hardcode  
• **Stateless Design**: Store persistent data in external services (S3, databases)  
• **Serverless Ready**: No local state, graceful shutdown, health endpoints  

---

## 🐳 Docker Build & Run

```bash
# Pull from Docker Hub
docker pull bmurrtech/sync-scribe-studio-api:latest

# Run with X-API-KEY authentication
docker run -p 8080:8080 \
  -e X_API_KEY=your-secure-api-key \
  -e PORT=8080 \
  bmurrtech/sync-scribe-studio-api:latest
```

### GitHub Container Registry (GHCR)

**Multi-platform support (linux/amd64, linux/arm64):**

```bash
# Pull from GHCR
docker pull ghcr.io/bmurrtech/sync-scribe-studio-api:latest

# Run with X-API-KEY authentication
docker run -p 8080:8080 \
  -e X_API_KEY=your-secure-api-key \
  -e PORT=8080 \
  ghcr.io/bmurrtech/sync-scribe-studio-api:latest
```

### Local Development Build

```bash
# Build locally (native platform)
docker build -t sync-scribe-studio-api .

# Run with environment file
docker run -p 8080:8080 --env-file .env.local sync-scribe-studio-api
```

#### Apple Silicon (M1/M2/M3) Platform Notes

```bash
# Build for your native ARM architecture (faster locally)
docker build -t sync-scribe-studio-api .

# For Cloud Run deployment compatibility (linux/amd64)
docker build --platform linux/amd64 -t sync-scribe-studio-api .

# Tag and push to Docker Hub
docker tag sync-scribe-studio-api bmurrtech/sync-scribe-studio-api:latest
docker push bmurrtech/sync-scribe-studio-api:latest
```

---

## 🔧 Environment Variables

Note: This image does not require any secrets in a local .env file. The authentication key (X_API_KEY) must be configured at your cloud host/platform (Cloud Run, DigitalOcean, etc.) or passed at container runtime via -e X_API_KEY=... The provided .env.example intentionally lists only optional settings.

### Authentication (Required)

#### `X_API_KEY`
- **Purpose**: API authentication key for all protected endpoints
- **Requirement**: **Mandatory** - Set at serverless platform level
- **Example**: `your-secure-api-key-32-chars-minimum`
- **Usage**: Sent as `X-API-KEY` header in requests

### Core Application Variables

#### `PORT`  
- **Purpose**: Server listening port (auto-set by Cloud Run)
- **Default**: 8080
- **Cloud Platforms**: Automatically configured

#### `ENVIRONMENT`
- **Purpose**: Environment type for configuration
- **Options**: `development`, `staging`, `production`
- **Default**: `production`

---

### Performance Tuning & GPU Variables

#### `MAX_QUEUE_LENGTH`
- **Purpose**: Limits concurrent tasks in processing queue
- **Default**: 10
- **Recommendation**: 5-20 based on server resources

#### `GUNICORN_WORKERS`
- **Purpose**: Number of worker processes  
- **Default**: CPU cores + 1
- **Recommendation**: 2-4× CPU cores for CPU workloads

#### `GUNICORN_TIMEOUT`
- **Purpose**: Request timeout in seconds
- **Default**: 300 
- **Recommendation**: 600-900 for large media files

#### `ENABLE_GPU` 🚀
- **Purpose**: Enable GPU acceleration for transcription and AI processing
- **Default**: false
- **Benefits**: 10-50x faster processing on supported platforms
- **Example**: `ENABLE_GPU=true`

---

### Storage Configuration (Optional)

#### S3-Compatible Storage
```bash
S3_ENDPOINT_URL=https://s3.amazonaws.com
S3_ACCESS_KEY=your-access-key  
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket
S3_REGION=us-east-1
```

#### Google Cloud Storage
```bash
GCP_SA_CREDENTIALS=path/to/service-account.json
GCP_BUCKET_NAME=your-gcs-bucket
```

---

## 📡 API Usage Examples

### Health Check Endpoints
```bash
# Basic health check
curl -X GET http://localhost:8080/health

# Detailed health with dependencies
curl -X GET http://localhost:8080/health/detailed

# Service information
curl -X GET http://localhost:8080/
```

### YouTube Processing (with X-API-KEY)
```bash
# Get video information
curl -X POST \
  -H "X-API-KEY: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}' \
  http://localhost:8080/v1/media/youtube/info

# Download as MP3
curl -X POST \
  -H "X-API-KEY: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "quality": "highest"}' \
  http://localhost:8080/v1/media/youtube/mp3

# Download as MP4
curl -X POST \
  -H "X-API-KEY: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "quality": "720p"}' \
  http://localhost:8080/v1/media/youtube/mp4
```

### Media Processing
```bash  
# Transcribe audio/video
curl -X POST \
  -H "X-API-KEY: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/media.mp4", "language": "en"}' \
  http://localhost:8080/v1/media/transcribe

# Convert media format  
curl -X POST \
  -H "X-API-KEY: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video.mp4", "format": "mp3"}' \
  http://localhost:8080/v1/media/convert
```

---

## ⚠️ Cloud Run Deployment Troubleshooting

### GHCR Image URL Issue

**Problem**: Google Cloud Run only accepts certain container registry patterns and may reject GHCR URLs.

**Solution**: For Google Cloud Run deployment, we recommend:

1. **Use Google Container Registry (GCR)**:
   ```bash
   # Push to GCR instead
   docker tag ghcr.io/bmurrtech/sync-scribe-studio-api:latest gcr.io/YOUR_PROJECT/sync-scribe-studio-api:latest
   docker push gcr.io/YOUR_PROJECT/sync-scribe-studio-api:latest
   
   # Deploy from GCR
   gcloud run deploy sync-scribe-studio-api \
     --image gcr.io/YOUR_PROJECT/sync-scribe-studio-api:latest \
     --platform managed
   ```

2. **Use Artifact Registry (recommended)**:
   ```bash
   # Push to Artifact Registry
   docker tag ghcr.io/bmurrtech/sync-scribe-studio-api:latest us-central1-docker.pkg.dev/YOUR_PROJECT/sync-scribe/api:latest
   docker push us-central1-docker.pkg.dev/YOUR_PROJECT/sync-scribe/api:latest
   
   # Deploy from Artifact Registry
   gcloud run deploy sync-scribe-studio-api \
     --image us-central1-docker.pkg.dev/YOUR_PROJECT/sync-scribe/api:latest \
     --platform managed
   ```

3. **Pull and Re-push Strategy**:
   ```bash
   # Pull from GHCR
   docker pull ghcr.io/bmurrtech/sync-scribe-studio-api:latest
   
   # Re-tag for GCP
   docker tag ghcr.io/bmurrtech/sync-scribe-studio-api:latest gcr.io/YOUR_PROJECT/sync-scribe-studio-api:latest
   
   # Push to GCP registry
   docker push gcr.io/YOUR_PROJECT/sync-scribe-studio-api:latest
   ```

**Alternative Platforms**: If you prefer to use GHCR directly, consider:
- DigitalOcean App Platform (supports GHCR)
- Railway (supports GHCR)
- Render (supports GHCR)
- AWS App Runner (supports public container registries)

---

## 📚 Testing & Validation

### Local Cloud Run Validation

Test Cloud Run compatibility locally:

```bash
# Run automated validation
./docker-local-cloud-run-test.sh

# Test with custom port
./docker-local-cloud-run-test.sh -p 9090
```

### API Testing

1. **Health Endpoint**: `curl http://localhost:8080/health`
2. **Service Info**: `curl http://localhost:8080/`
3. **Authentication**: Include `X-API-KEY` header in all requests
4. **Rate Limiting**: Observe rate limit headers in responses

---

## 🤝 Contributing

We welcome contributions! This project is a fork and improvement of the original [No-Code Architects Toolkit](https://github.com/stephengpope/no-code-architects-toolkit) by Stephen Pope, enhanced with additional features, security improvements, and serverless deployment capabilities.

### How to Contribute

1. Fork the repository
2. Create a feature branch  
3. Make your changes with tests
4. Submit a pull request
5. CI/CD will automatically test and validate

### Development Setup

```bash
# Clone the repository
git clone https://github.com/bmurrtech/sync-scribe-studio-api.git

# Install dependencies
pip install -r requirements.txt

# Run locally  
python app.py
```

---

## 📄 License & Attribution

This project is licensed under the [GNU General Public License v2.0 (GPL-2.0)](LICENSE).

### Attribution

This project is a fork and enhancement of the [No-Code Architects Toolkit](https://github.com/stephengpope/no-code-architects-toolkit) created by **Stephen Pope**. We acknowledge and thank Stephen for his original work that made this project possible.

**Enhancements in this fork:**
- GitHub Container Registry deployment pipeline
- Enhanced security with X-API-KEY authentication  
- GPU acceleration support for AI processing
- Serverless platform deployment scripts
- Comprehensive health monitoring
- Production-grade containerization
- Multi-platform build support

---

*Save thousands on SaaS subscriptions. Deploy your own powerful media processing API in minutes.* 🚀
