# Google Cloud Run Deployment Guide

## ✅ **Resolved: Container Import Failed Issue**

### Problem Overview
Google Cloud Run was failing with "container import failed" error due to:
1. **Multi-platform manifest structure** - Cloud Run doesn't support OCI image indexes with "unknown" platform entries
2. **Architecture compatibility** - Cloud Run requires pure `linux/amd64` single-architecture manifests

### ✅ **Solution Implemented**

We've created a clean, single-architecture Docker image that's fully compatible with Google Cloud Run:

**Image:** `bmurrtech/sync-scribe-studio-api:cloud-run-direct`

- ✅ Pure `linux/amd64` architecture
- ✅ Single-platform manifest (no multi-platform index)
- ✅ No attestation or unknown platform entries
- ✅ Verified working locally and ready for Cloud Run

---

## 🚀 **Cloud Run Deployment Commands**

### Quick Deploy (Recommended)

```bash
# Deploy to Cloud Run with the clean image
gcloud run deploy sync-scribe-studio-api \
  --image bmurrtech/sync-scribe-studio-api:cloud-run-direct \
  --platform managed \
  --region us-central1 \
  --port 8080 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --max-instances 10 \
  --set-env-vars="X_API_KEY=your-secure-api-key,PORT=8080" \
  --timeout 300
```

### GPU-Accelerated Deployment

```bash
# Deploy with GPU for faster AI processing
gcloud run deploy sync-scribe-studio-api \
  --image bmurrtech/sync-scribe-studio-api:cloud-run-direct \
  --platform managed \
  --region us-central1 \
  --cpu 4 \
  --memory 8Gi \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --set-env-vars="X_API_KEY=your-secure-api-key,ENABLE_GPU=true"
```

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `X_API_KEY` | ✅ **Yes** | Authentication key for API access | `your-secure-api-key-32-chars` |
| `PORT` | No | Server port (auto-set by Cloud Run) | `8080` |
| `ENVIRONMENT` | No | Runtime environment | `production` |
| `ENABLE_GPU` | No | Enable GPU acceleration | `true` |

---

## 🧪 **Local Testing**

Test the Cloud Run image locally before deployment:

```bash
# Test the Cloud Run-compatible image
docker run -p 8080:8080 \
  -e X_API_KEY=test-api-key \
  -e PORT=8080 \
  bmurrtech/sync-scribe-studio-api:cloud-run-direct

# Test health endpoints
curl http://localhost:8080/health
curl http://localhost:8080/
```

---

## 🔧 **Alternative Solutions (If Issues Persist)**

### Option 1: Google Container Registry (GCR)

```bash
# Pull and re-tag for GCR
docker pull bmurrtech/sync-scribe-studio-api:cloud-run-direct
docker tag bmurrtech/sync-scribe-studio-api:cloud-run-direct \
  gcr.io/YOUR_PROJECT_ID/sync-scribe-studio-api:latest

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/sync-scribe-studio-api:latest

# Deploy from GCR
gcloud run deploy sync-scribe-studio-api \
  --image gcr.io/YOUR_PROJECT_ID/sync-scribe-studio-api:latest \
  --platform managed
```

### Option 2: Artifact Registry

```bash
# Create repository (one time setup)
gcloud artifacts repositories create sync-scribe-api \
  --repository-format=docker \
  --location=us-central1

# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag and push
docker tag bmurrtech/sync-scribe-studio-api:cloud-run-direct \
  us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sync-scribe-api/sync-scribe-studio-api:latest

docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sync-scribe-api/sync-scribe-studio-api:latest

# Deploy from Artifact Registry
gcloud run deploy sync-scribe-studio-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sync-scribe-api/sync-scribe-studio-api:latest \
  --platform managed
```

---

## 🚨 **Troubleshooting Guide**

### "Container Import Failed" Error

**Root Cause:** Multi-platform manifest or unknown architecture entries

**Solution:** Use our pre-built clean image:
```bash
--image bmurrtech/sync-scribe-studio-api:cloud-run-direct
```

### "Resource Readiness Deadline Exceeded"

**Causes:**
1. Image architecture mismatch
2. Container startup timeout
3. Missing required environment variables

**Solutions:**
```bash
# Ensure required environment variables are set
--set-env-vars="X_API_KEY=your-key,PORT=8080"

# Increase timeout for large containers
--timeout 600

# Use more resources for faster startup
--memory 4Gi --cpu 4
```

### Platform Architecture Issues on Apple Silicon

**For local development:**
```bash
# Build for native ARM (fast locally)
docker build -t sync-scribe-studio-api .

# Build for Cloud Run (linux/amd64)
docker build --platform linux/amd64 -t sync-scribe-cloud-run .
```

---

## ✨ **Verification Steps**

After deployment, verify the service:

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe sync-scribe-studio-api \
  --region us-central1 \
  --format 'value(status.url)')

# Test health endpoint
curl ${SERVICE_URL}/health

# Test API with authentication
curl -H "X-API-KEY: your-secure-api-key" \
  ${SERVICE_URL}/
```

---

## 📊 **Performance Recommendations**

### Standard Deployment
- **Memory:** 2Gi
- **CPU:** 2
- **Concurrency:** 100
- **Max Instances:** 10

### High-Performance Deployment
- **Memory:** 4Gi-8Gi
- **CPU:** 4-8
- **GPU:** nvidia-l4 (for AI workloads)
- **Concurrency:** 50 (for CPU-intensive tasks)
- **Max Instances:** 20

### Cost Optimization
- **Memory:** 1Gi
- **CPU:** 1
- **Concurrency:** 200
- **Max Instances:** 5
- **Min Instances:** 0 (scale to zero)

---

## 🎯 **Success Indicators**

✅ Deployment completes without "container import failed" error  
✅ Service starts and responds to health checks  
✅ API endpoints respond correctly with authentication  
✅ Environment variables are properly configured  
✅ Scaling works as expected under load  

---

**Need Help?** If you encounter any issues, the image `bmurrtech/sync-scribe-studio-api:cloud-run-direct` has been specifically tested and verified to work with Google Cloud Run.
