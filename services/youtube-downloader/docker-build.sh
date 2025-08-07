#!/bin/bash
set -e

# Docker Build and Test Script for YouTube Downloader Service
# Usage: ./docker-build.sh [--build-only|--test|--clean]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="youtube-downloader"
TAG="${TAG:-latest}"
CONTAINER_NAME="${IMAGE_NAME}-test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

build_image() {
    log_info "Building Docker image: ${IMAGE_NAME}:${TAG}"
    
    docker build \
        --target production \
        --tag "${IMAGE_NAME}:${TAG}" \
        --file Dockerfile \
        . || {
        log_error "Failed to build Docker image"
        exit 1
    }
    
    log_success "Docker image built successfully"
    
    # Show image info
    docker image inspect "${IMAGE_NAME}:${TAG}" --format='
Image: {{.RepoTags}}
Size: {{.Size}} bytes
Created: {{.Created}}
Architecture: {{.Architecture}}
OS: {{.Os}}' || log_warning "Could not inspect image"
}

test_container() {
    log_info "Testing Docker container..."
    
    # Clean up any existing test container
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    
    # Run container in detached mode
    log_info "Starting test container: $CONTAINER_NAME"
    docker run -d \
        --name "$CONTAINER_NAME" \
        --env NODE_ENV=production \
        --env PORT=3001 \
        --env YTDL_NETWORK_TIMEOUT=30000 \
        --env SKIP_NETWORK_CHECK=true \
        "${IMAGE_NAME}:${TAG}" || {
        log_error "Failed to start container"
        exit 1
    }
    
    # Wait for container to start
    log_info "Waiting for container to start..."
    sleep 10
    
    # Check if container is running
    if ! docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}" | grep -q "$CONTAINER_NAME"; then
        log_error "Container is not running"
        docker logs "$CONTAINER_NAME" 2>&1 | tail -20
        docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
        exit 1
    fi
    
    # Get container IP
    CONTAINER_IP=$(docker inspect "$CONTAINER_NAME" --format '{{.NetworkSettings.IPAddress}}')
    if [ -z "$CONTAINER_IP" ]; then
        log_warning "Could not get container IP, using localhost"
        CONTAINER_IP="localhost"
    fi
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    for i in {1..10}; do
        if docker exec "$CONTAINER_NAME" wget --quiet --timeout=5 --tries=1 --spider "http://localhost:3001/healthz" 2>/dev/null; then
            log_success "Health check passed"
            break
        elif [ $i -eq 10 ]; then
            log_error "Health check failed after 10 attempts"
            docker logs "$CONTAINER_NAME" 2>&1 | tail -20
            docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
            exit 1
        else
            log_info "Health check attempt $i/10 failed, retrying..."
            sleep 3
        fi
    done
    
    # Show container logs
    log_info "Container logs (last 10 lines):"
    docker logs --tail 10 "$CONTAINER_NAME" 2>&1 | while read line; do
        echo "  $line"
    done
    
    # Show container stats
    log_info "Container stats:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "$CONTAINER_NAME" || log_warning "Could not get container stats"
    
    # Clean up test container
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    log_success "Container test completed successfully"
}

clean_images() {
    log_info "Cleaning up Docker images and containers..."
    
    # Remove test container if exists
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    
    # Remove image
    docker rmi "${IMAGE_NAME}:${TAG}" 2>/dev/null || log_warning "Image ${IMAGE_NAME}:${TAG} not found"
    
    # Clean dangling images
    docker image prune -f || log_warning "Could not prune dangling images"
    
    log_success "Cleanup completed"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --build-only    Build image only (no testing)"
    echo "  --test          Run tests on existing image"
    echo "  --clean         Clean up images and containers"
    echo "  --help          Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  TAG             Image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0                      # Build and test"
    echo "  TAG=v1.0.0 $0         # Build with custom tag"
    echo "  $0 --build-only        # Build without testing"
    echo "  $0 --clean             # Clean up"
}

# Main execution
case "${1:-}" in
    --build-only)
        build_image
        ;;
    --test)
        test_container
        ;;
    --clean)
        clean_images
        ;;
    --help)
        show_usage
        ;;
    "")
        build_image
        test_container
        ;;
    *)
        log_error "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac

log_success "Script completed successfully!"
