#!/bin/bash

# Docker Build Script for Cloud Run Deployment
# Usage: ./build-docker.sh [tag-suffix]
# Example: ./build-docker.sh dev

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get build number from version.py
get_build_number() {
    if [ -f "version.py" ]; then
        BUILD_NUMBER=$(grep "BUILD_NUMBER" version.py | cut -d'=' -f2 | tr -d ' ')
        echo $BUILD_NUMBER
    else
        print_error "version.py not found"
        exit 1
    fi
}

# Generate semantic version
generate_version() {
    local build_num=$1
    local suffix=$2
    
    # Convert build number to semantic version (e.g., 200 -> 2.0.0)
    local major=$(( build_num / 100 ))
    local minor=$(( (build_num % 100) / 10 ))
    local patch=$(( build_num % 10 ))
    
    local version="${major}.${minor}.${patch}"
    
    if [ -n "$suffix" ]; then
        version="${version}-${suffix}"
    fi
    
    echo $version
}

# Main build function
build_image() {
    local tag_suffix=$1
    
    print_status "Starting Docker build for Cloud Run..."
    
    # Get build number
    BUILD_NUMBER=$(get_build_number)
    print_status "Build number: $BUILD_NUMBER"
    
    # Generate semantic version
    VERSION=$(generate_version $BUILD_NUMBER $tag_suffix)
    print_status "Semantic version: $VERSION"
    
    # Set image name and registry
    IMAGE_NAME="sync-scribe-studio-api"
    REGISTRY=${DOCKER_REGISTRY:-"gcr.io"}
    PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
    
    # Full image tags
    IMAGE_TAG_VERSIONED="${REGISTRY}/${PROJECT_ID}/${IMAGE_NAME}:${VERSION}"
    IMAGE_TAG_LATEST="${REGISTRY}/${PROJECT_ID}/${IMAGE_NAME}:latest"
    IMAGE_TAG_BUILD="${REGISTRY}/${PROJECT_ID}/${IMAGE_NAME}:build-${BUILD_NUMBER}"
    
    print_status "Building multi-stage Docker image..."
    print_status "Image tags:"
    echo "  - $IMAGE_TAG_VERSIONED"
    echo "  - $IMAGE_TAG_LATEST" 
    echo "  - $IMAGE_TAG_BUILD"
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Build the image with build args
    print_status "Building image (this may take several minutes for FFmpeg compilation)..."
    
    docker build \
        --build-arg BUILD_NUMBER=$BUILD_NUMBER \
        --target final \
        --tag $IMAGE_TAG_VERSIONED \
        --tag $IMAGE_TAG_LATEST \
        --tag $IMAGE_TAG_BUILD \
        --progress=plain \
        .
    
    if [ $? -eq 0 ]; then
        print_success "Docker build completed successfully!"
        
        # Show image size
        print_status "Image information:"
        docker images $IMAGE_TAG_VERSIONED --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        
        # Check image size
        SIZE_BYTES=$(docker inspect $IMAGE_TAG_VERSIONED --format='{{.Size}}')
        SIZE_MB=$((SIZE_BYTES / 1024 / 1024))
        SIZE_GB=$((SIZE_MB / 1024))
        
        print_status "Image size: ${SIZE_MB}MB (${SIZE_GB}GB)"
        
        if [ $SIZE_GB -gt 1 ]; then
            print_warning "Image size exceeds 1GB. Consider optimizing for Cloud Run."
        fi
        
        print_success "Build completed with tags:"
        echo "  - Versioned: $IMAGE_TAG_VERSIONED"
        echo "  - Latest: $IMAGE_TAG_LATEST"
        echo "  - Build: $IMAGE_TAG_BUILD"
        
    else
        print_error "Docker build failed!"
        exit 1
    fi
}

# Test the built image
test_image() {
    local image_tag=$1
    
    print_status "Testing built image..."
    
    # Test that the image starts and responds to health check
    print_status "Starting container for health check..."
    
    CONTAINER_ID=$(docker run -d -p 8080:8080 -e PORT=8080 $image_tag)
    
    if [ $? -eq 0 ]; then
        print_status "Container started with ID: $CONTAINER_ID"
        
        # Wait for container to be ready
        sleep 5
        
        # Test health endpoint
        print_status "Testing health endpoint..."
        
        if curl -f http://localhost:8080/health >/dev/null 2>&1; then
            print_success "Health check passed!"
        else
            print_error "Health check failed!"
            docker logs $CONTAINER_ID
        fi
        
        # Cleanup
        docker stop $CONTAINER_ID >/dev/null 2>&1
        docker rm $CONTAINER_ID >/dev/null 2>&1
        
    else
        print_error "Failed to start container for testing"
        exit 1
    fi
}

# Push to registry
push_image() {
    local image_tag=$1
    
    print_status "Pushing image to registry..."
    
    # Configure Docker for GCR if needed
    if [[ $image_tag == gcr.io/* ]]; then
        print_status "Configuring Docker for Google Container Registry..."
        gcloud auth configure-docker --quiet
    fi
    
    docker push $image_tag
    
    if [ $? -eq 0 ]; then
        print_success "Image pushed successfully: $image_tag"
    else
        print_error "Failed to push image: $image_tag"
        exit 1
    fi
}

# Main script
main() {
    local tag_suffix=$1
    
    print_status "=== Docker Build Script for Cloud Run ==="
    print_status "Timestamp: $(date)"
    print_status "Working directory: $(pwd)"
    
    # Build image
    build_image $tag_suffix
    
    # Get the versioned tag for testing and pushing
    BUILD_NUMBER=$(get_build_number)
    VERSION=$(generate_version $BUILD_NUMBER $tag_suffix)
    REGISTRY=${DOCKER_REGISTRY:-"gcr.io"}
    PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
    IMAGE_TAG_VERSIONED="${REGISTRY}/${PROJECT_ID}/sync-scribe-studio-api:${VERSION}"
    
    # Test image
    print_status "=== Testing Image ==="
    test_image $IMAGE_TAG_VERSIONED
    
    # Ask user if they want to push
    read -p "Push image to registry? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "=== Pushing to Registry ==="
        push_image $IMAGE_TAG_VERSIONED
        push_image "${REGISTRY}/${PROJECT_ID}/sync-scribe-studio-api:latest"
        push_image "${REGISTRY}/${PROJECT_ID}/sync-scribe-studio-api:build-${BUILD_NUMBER}"
    else
        print_status "Skipping push to registry"
    fi
    
    print_success "=== Build Complete ==="
    print_status "To deploy to Cloud Run, use:"
    echo "  gcloud run deploy sync-scribe-studio-api \\"
    echo "    --image $IMAGE_TAG_VERSIONED \\"
    echo "    --platform managed \\"
    echo "    --region us-central1 \\"
    echo "    --allow-unauthenticated \\"
    echo "    --port 8080 \\"
    echo "    --memory 2Gi \\"
    echo "    --cpu 1 \\"
    echo "    --max-instances 10"
}

# Handle script arguments
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage: $0 [tag-suffix]"
    echo ""
    echo "Build Docker image for Cloud Run with semantic versioning"
    echo ""
    echo "Options:"
    echo "  tag-suffix    Optional suffix for the version tag (e.g., 'dev', 'staging')"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DOCKER_REGISTRY      Docker registry (default: gcr.io)"
    echo "  GOOGLE_CLOUD_PROJECT GCP project ID (default: your-project-id)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Build with version from BUILD_NUMBER"
    echo "  $0 dev                # Build with version like 2.0.0-dev"
    echo "  $0 staging            # Build with version like 2.0.0-staging"
    exit 0
fi

# Run main function
main $1
