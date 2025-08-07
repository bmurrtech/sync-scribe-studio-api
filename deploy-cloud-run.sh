#!/bin/bash

# Cloud Run Deployment Script
# Usage: ./deploy-cloud-run.sh [environment]
# Example: ./deploy-cloud-run.sh production

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

# Configuration
SERVICE_NAME="sync-scribe-studio-api"
DEFAULT_REGION="us-central1"
DEFAULT_PROJECT_ID=""

# Get build number and version
get_build_info() {
    if [ -f "version.py" ]; then
        BUILD_NUMBER=$(grep "BUILD_NUMBER" version.py | cut -d'=' -f2 | tr -d ' ')
        
        # Convert to semantic version
        local major=$(( BUILD_NUMBER / 100 ))
        local minor=$(( (BUILD_NUMBER % 100) / 10 ))
        local patch=$(( BUILD_NUMBER % 10 ))
        
        VERSION="${major}.${minor}.${patch}"
        
        echo "Build: $BUILD_NUMBER, Version: $VERSION"
    else
        print_error "version.py not found"
        exit 1
    fi
}

# Validate environment
validate_environment() {
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud. Run 'gcloud auth login'"
        exit 1
    fi
    
    # Get current project
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        print_error "No project configured. Run 'gcloud config set project PROJECT_ID'"
        exit 1
    fi
    
    print_status "Using project: $PROJECT_ID"
    
    # Check if Cloud Run API is enabled
    if ! gcloud services list --enabled --filter="name:run.googleapis.com" --format="value(name)" | grep -q run.googleapis.com; then
        print_warning "Cloud Run API not enabled. Enabling now..."
        gcloud services enable run.googleapis.com
    fi
}

# Deploy to Cloud Run
deploy_service() {
    local environment=$1
    local region=${REGION:-$DEFAULT_REGION}
    
    print_status "Deploying to Cloud Run..."
    print_status "Environment: $environment"
    print_status "Region: $region"
    print_status "Project: $PROJECT_ID"
    
    # Determine image tag based on environment
    local image_tag
    case $environment in
        "production"|"prod")
            image_tag="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${VERSION}"
            ;;
        "staging")
            image_tag="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${VERSION}-staging"
            ;;
        "development"|"dev")
            image_tag="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${VERSION}-dev"
            ;;
        *)
            image_tag="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
            ;;
    esac
    
    print_status "Using image: $image_tag"
    
    # Check if image exists
    if ! gcloud container images describe $image_tag &>/dev/null; then
        print_error "Image $image_tag not found in registry."
        print_status "Please build and push the image first using: ./build-docker.sh"
        exit 1
    fi
    
    # Deploy with optimized Cloud Run configuration
    print_status "Deploying Cloud Run service..."
    
    gcloud run deploy $SERVICE_NAME \
        --image=$image_tag \
        --platform=managed \
        --region=$region \
        --allow-unauthenticated \
        --port=8080 \
        --memory=2Gi \
        --cpu=1 \
        --timeout=900 \
        --concurrency=4 \
        --min-instances=0 \
        --max-instances=10 \
        --execution-environment=gen2 \
        --cpu-throttling \
        --set-env-vars="PORT=8080,PYTHONUNBUFFERED=1,PYTHONDONTWRITEBYTECODE=1,GUNICORN_WORKERS=2,GUNICORN_TIMEOUT=300,MAX_QUEUE_LENGTH=50,WHISPER_CACHE_DIR=/tmp/whisper_cache,BUILD_NUMBER=${BUILD_NUMBER}" \
        --tag=$environment \
        --quiet
    
    if [ $? -eq 0 ]; then
        print_success "Deployment completed successfully!"
        
        # Get service URL
        SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$region --format="value(status.url)")
        print_success "Service URL: $SERVICE_URL"
        
        # Test health endpoint
        test_deployment $SERVICE_URL
        
        # Show deployment info
        show_deployment_info $region $environment
        
    else
        print_error "Deployment failed!"
        exit 1
    fi
}

# Test deployment
test_deployment() {
    local service_url=$1
    
    print_status "Testing deployment..."
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    if curl -f -s "$service_url/health" > /dev/null; then
        print_success "Health check passed!"
        
        # Get detailed health info
        health_response=$(curl -s "$service_url/health" | jq -r '.version, .service' 2>/dev/null || echo "N/A N/A")
        print_status "Service version: $(echo $health_response | cut -d' ' -f1)"
        print_status "Service name: $(echo $health_response | cut -d' ' -f2-)"
        
    else
        print_warning "Health check failed - service may still be starting up"
    fi
    
    # Test root endpoint
    print_status "Testing root endpoint..."
    if curl -f -s "$service_url/" > /dev/null; then
        print_success "Root endpoint accessible!"
    else
        print_warning "Root endpoint not accessible"
    fi
}

# Show deployment information
show_deployment_info() {
    local region=$1
    local environment=$2
    
    print_status "=== Deployment Information ==="
    
    # Service details
    gcloud run services describe $SERVICE_NAME --region=$region --format="table(
        metadata.name:label=SERVICE,
        status.url:label=URL,
        spec.template.spec.containers[0].image:label=IMAGE,
        status.conditions[0].status:label=READY,
        metadata.creationTimestamp:label=CREATED
    )"
    
    echo ""
    print_status "=== Resource Configuration ==="
    gcloud run services describe $SERVICE_NAME --region=$region --format="table(
        spec.template.metadata.annotations['run.googleapis.com/memory']:label=MEMORY,
        spec.template.metadata.annotations['run.googleapis.com/cpu']:label=CPU,
        spec.template.spec.containerConcurrency:label=CONCURRENCY,
        spec.template.metadata.annotations['autoscaling.knative.dev/maxScale']:label=MAX_INSTANCES
    )"
    
    echo ""
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$region --format="value(status.url)")
    
    print_success "=== Deployment Complete ==="
    print_status "Service URL: $SERVICE_URL"
    print_status "Environment: $environment"
    print_status "Build Number: $BUILD_NUMBER"
    print_status "Version: $VERSION"
    
    echo ""
    print_status "Test endpoints:"
    echo "  Health Check: $SERVICE_URL/health"
    echo "  Detailed Health: $SERVICE_URL/health/detailed"
    echo "  Service Info: $SERVICE_URL/"
    echo "  Media Transcribe: $SERVICE_URL/v1/media/transcribe"
    
    echo ""
    print_status "Monitor logs with:"
    echo "  gcloud logs tail --follow --format=json projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout"
    
    echo ""
    print_status "Update service with:"
    echo "  gcloud run services replace deployment/cloud-run-service.yaml --region=$region"
}

# Traffic management
manage_traffic() {
    local region=${REGION:-$DEFAULT_REGION}
    local action=$1
    local environment=$2
    
    case $action in
        "split")
            print_status "Splitting traffic between environments..."
            gcloud run services update-traffic $SERVICE_NAME \
                --region=$region \
                --to-tags=production=80,staging=20
            ;;
        "migrate")
            print_status "Migrating all traffic to $environment..."
            gcloud run services update-traffic $SERVICE_NAME \
                --region=$region \
                --to-tags=$environment=100
            ;;
        "rollback")
            print_status "Rolling back to previous revision..."
            gcloud run services update-traffic $SERVICE_NAME \
                --region=$region \
                --to-revisions=LATEST=100
            ;;
        *)
            print_error "Unknown traffic action: $action"
            ;;
    esac
}

# Main function
main() {
    local environment=${1:-"production"}
    
    print_status "=== Cloud Run Deployment Script ==="
    print_status "Timestamp: $(date)"
    print_status "Environment: $environment"
    
    # Get build information
    get_build_info
    print_status "Build Information: $BUILD_NUMBER -> $VERSION"
    
    # Validate environment
    validate_environment
    
    # Deploy service
    deploy_service $environment
}

# Handle script arguments and show help
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage: $0 [environment] [options]"
    echo ""
    echo "Deploy Sync Scribe Studio API to Google Cloud Run"
    echo ""
    echo "Environments:"
    echo "  production   Deploy production version (default)"
    echo "  staging      Deploy staging version"
    echo "  development  Deploy development version"
    echo ""
    echo "Options:"
    echo "  -h, --help   Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  REGION       Cloud Run region (default: us-central1)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy to production"
    echo "  $0 staging            # Deploy to staging"
    echo "  REGION=europe-west1 $0 production  # Deploy to different region"
    echo ""
    echo "Prerequisites:"
    echo "  - gcloud CLI installed and authenticated"
    echo "  - Project configured: gcloud config set project PROJECT_ID"
    echo "  - Docker image built and pushed to GCR"
    echo ""
    exit 0
fi

# Handle traffic management commands
if [ "$1" = "traffic" ]; then
    case "$2" in
        "split"|"migrate"|"rollback")
            manage_traffic $2 $3
            exit 0
            ;;
        *)
            print_error "Invalid traffic command. Use: split, migrate, or rollback"
            exit 1
            ;;
    esac
fi

# Run main deployment
main $1
