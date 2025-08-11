#!/bin/bash

# Test Docker Build Script
# Tests both CPU and GPU variants of the Docker image

set -e

echo "================================================"
echo "Docker Build Test Script"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check if buildx is available
if ! docker buildx version &> /dev/null; then
    echo "Warning: Docker buildx not available. Installing..."
    docker buildx create --name testbuilder --use || true
fi

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "1. Testing CPU variant build..."
echo "--------------------------------"

# Build CPU variant
if docker buildx build \
    --platform linux/amd64 \
    --build-arg BUILD_VARIANT=cpu \
    --build-arg SKIP_MODEL_WARMUP=true \
    -t sync-scribe-test:cpu \
    --load \
    . ; then
    echo -e "${GREEN}✓ CPU variant built successfully${NC}"
else
    echo -e "${RED}✗ CPU variant build failed${NC}"
    exit 1
fi

echo ""
echo "2. Testing GPU variant build..."
echo "--------------------------------"

# Build GPU variant (will work even without NVIDIA runtime, just won't run)
if docker buildx build \
    --platform linux/amd64 \
    --build-arg BUILD_VARIANT=gpu \
    --build-arg CUDA_VERSION=12.1.0 \
    --build-arg CUDNN_VERSION=8 \
    --build-arg SKIP_MODEL_WARMUP=true \
    -t sync-scribe-test:gpu \
    --load \
    . ; then
    echo -e "${GREEN}✓ GPU variant built successfully${NC}"
else
    echo -e "${RED}✗ GPU variant build failed${NC}"
    exit 1
fi

echo ""
echo "3. Checking image details..."
echo "-----------------------------"

# Check CPU image
echo "CPU Image:"
docker images sync-scribe-test:cpu --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "GPU Image:"
docker images sync-scribe-test:gpu --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "4. Verifying architecture..."
echo "-----------------------------"

# Check architecture
ARCH_CPU=$(docker inspect sync-scribe-test:cpu | grep -o '"Architecture": "[^"]*"' | cut -d'"' -f4)
ARCH_GPU=$(docker inspect sync-scribe-test:gpu | grep -o '"Architecture": "[^"]*"' | cut -d'"' -f4)

echo "CPU variant architecture: $ARCH_CPU"
echo "GPU variant architecture: $ARCH_GPU"

if [ "$ARCH_CPU" == "amd64" ] && [ "$ARCH_GPU" == "amd64" ]; then
    echo -e "${GREEN}✓ Both images are linux/amd64 (Cloud Run compatible)${NC}"
else
    echo -e "${RED}✗ Architecture mismatch - not Cloud Run compatible${NC}"
    exit 1
fi

echo ""
echo "5. Testing CPU variant runtime (if possible)..."
echo "------------------------------------------------"

# Try to run CPU variant with a simple test
if [ -f ".env" ]; then
    # Load API_KEY from .env if it exists
    export $(grep -E '^API_KEY=' .env | xargs)
fi

if [ -n "$API_KEY" ]; then
    echo "Testing CPU container startup..."
    if docker run --rm -d \
        --name test-cpu \
        -e API_KEY="$API_KEY" \
        -e ENABLE_FASTER_WHISPER=false \
        -e SKIP_MODEL_WARMUP=true \
        sync-scribe-test:cpu > /dev/null 2>&1; then
        
        sleep 5
        
        # Check if container is still running
        if docker ps | grep -q test-cpu; then
            echo -e "${GREEN}✓ CPU container started successfully${NC}"
            docker stop test-cpu > /dev/null 2>&1
        else
            echo -e "${RED}✗ CPU container failed to start${NC}"
            docker logs test-cpu 2>&1 | tail -20
        fi
    else
        echo "Could not start test container"
    fi
else
    echo "Skipping runtime test (API_KEY not set)"
fi

echo ""
echo "================================================"
echo "Build Test Summary"
echo "================================================"
echo -e "${GREEN}✓ Both CPU and GPU variants build successfully${NC}"
echo -e "${GREEN}✓ Images are linux/amd64 (Cloud Run compatible)${NC}"
echo ""
echo "Next steps:"
echo "1. Push to Docker Hub: docker push bmurrtech/sync-scribe-studio-api:latest"
echo "2. Deploy to Cloud Run with appropriate environment variables"
echo "3. For GPU testing, use a machine with NVIDIA Docker runtime"
echo ""
