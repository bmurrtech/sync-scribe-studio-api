#!/bin/bash

# GCP Cloud Run Deployment Script
# Builds, pushes, and deploys YouTube Downloader microservice to GCP Cloud Run

set -e

echo "☁️ Starting GCP Cloud Run Deployment..."

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-""}
REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME="youtube-downloader"
IMAGE_NAME="youtube-downloader"
REPOSITORY="sync-scribe-studio"
TAG=${BUILD_TAG:-"latest"}

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it from https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker."
        exit 1
    fi
    
    # Check if PROJECT_ID is set
    if [ -z "$PROJECT_ID" ]; then
        log_error "PROJECT_ID is not set. Please set GCP_PROJECT_ID environment variable."
        log_info "Example: export GCP_PROJECT_ID=your-project-id"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Authenticate and set up GCP
setup_gcp() {
    log_info "Setting up GCP configuration..."
    
    # Set the project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    log_info "Enabling required GCP APIs..."
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable artifactregistry.googleapis.com
    
    # Configure Docker authentication
    gcloud auth configure-docker
    
    log_success "GCP setup completed"
}

# Build and push Docker image
build_and_push() {
    log_info "Building Docker image..."
    
    cd services/youtube-downloader
    
    # Build image with Cloud Build for better performance and caching
    IMAGE_URL="gcr.io/$PROJECT_ID/$IMAGE_NAME:$TAG"
    
    log_info "Building image: $IMAGE_URL"
    
    # Use Cloud Build for building and pushing
    gcloud builds submit --tag $IMAGE_URL --timeout=20m .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built and pushed successfully: $IMAGE_URL"
        cd ../..
        return 0
    else
        log_error "Failed to build and push Docker image"
        cd ../..
        return 1
    fi
}

# Create service account if it doesn't exist
setup_service_account() {
    log_info "Setting up service account..."
    
    SERVICE_ACCOUNT="$SERVICE_NAME-sa"
    SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"
    
    # Check if service account exists
    if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
        log_info "Creating service account: $SERVICE_ACCOUNT_EMAIL"
        gcloud iam service-accounts create $SERVICE_ACCOUNT \
            --display-name="YouTube Downloader Service Account" \
            --description="Service account for YouTube Downloader microservice"
    else
        log_info "Service account already exists: $SERVICE_ACCOUNT_EMAIL"
    fi
    
    # Grant necessary roles
    log_info "Granting IAM roles..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/logging.logWriter"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/monitoring.metricWriter"
    
    log_success "Service account setup completed"
}

# Deploy to Cloud Run
deploy_service() {
    log_info "Deploying to Cloud Run..."
    
    IMAGE_URL="gcr.io/$PROJECT_ID/$IMAGE_NAME:$TAG"
    SERVICE_ACCOUNT_EMAIL="$SERVICE_NAME-sa@$PROJECT_ID.iam.gserviceaccount.com"
    
    # Deploy the service
    gcloud run deploy $SERVICE_NAME \
        --image $IMAGE_URL \
        --platform managed \
        --region $REGION \
        --service-account $SERVICE_ACCOUNT_EMAIL \
        --allow-unauthenticated \
        --port 3001 \
        --memory 2Gi \
        --cpu 1 \
        --timeout 900s \
        --concurrency 100 \
        --min-instances 1 \
        --max-instances 10 \
        --cpu-throttling \
        --execution-environment gen2 \
        --set-env-vars NODE_ENV=production,PORT=3001,LOG_LEVEL=info \
        --set-env-vars RATE_LIMIT_WINDOW_MS=900000,RATE_LIMIT_MAX_REQUESTS=100 \
        --set-env-vars YTDL_NETWORK_TIMEOUT=30000 \
        --ingress all
    
    if [ $? -eq 0 ]; then
        # Get the service URL
        SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
        log_success "Service deployed successfully!"
        log_success "Service URL: $SERVICE_URL"
        return 0
    else
        log_error "Failed to deploy service"
        return 1
    fi
}

# Test the deployed service
test_deployment() {
    log_info "Testing deployed service..."
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    
    if [ -z "$SERVICE_URL" ]; then
        log_error "Could not get service URL"
        return 1
    fi
    
    log_info "Testing health check endpoint: $SERVICE_URL/healthz"
    
    # Test health check
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$SERVICE_URL/healthz" > /dev/null 2>&1; then
            log_success "Health check passed (attempt $attempt)"
            break
        fi
        
        log_info "Waiting for service to be ready... (attempt $attempt/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Service failed to become ready within $max_attempts attempts"
        return 1
    fi
    
    # Test Rick Roll video info endpoint
    log_info "Testing Rick Roll video endpoint..."
    
    RICK_ROLL_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    PAYLOAD='{"url": "'$RICK_ROLL_URL'"}'
    
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" \
        "$SERVICE_URL/v1/media/youtube/info")
    
    if echo "$RESPONSE" | grep -q '"success":true' && \
       echo "$RESPONSE" | grep -q 'Rick Astley'; then
        log_success "Rick Roll video endpoint test passed"
    else
        log_warning "Rick Roll video endpoint test failed or returned unexpected data"
        echo "Response: $RESPONSE"
    fi
    
    log_success "Deployment testing completed"
    return 0
}

# Setup monitoring and logging
setup_monitoring() {
    log_info "Setting up monitoring and logging..."
    
    # Create log-based metrics for monitoring
    log_info "Creating log-based metrics..."
    
    # Error rate metric
    gcloud logging metrics create youtube_downloader_error_rate \
        --description="Error rate for YouTube Downloader service" \
        --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'" AND severity>=ERROR' \
        --quiet || true
    
    # Request count metric
    gcloud logging metrics create youtube_downloader_request_count \
        --description="Request count for YouTube Downloader service" \
        --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'" AND httpRequest.requestMethod!=""' \
        --quiet || true
    
    log_success "Monitoring setup completed"
}

# Main deployment function
main() {
    log_info "Starting GCP Cloud Run deployment for YouTube Downloader"
    log_info "Project ID: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Service: $SERVICE_NAME"
    log_info "Image tag: $TAG"
    echo
    
    # Run deployment steps
    check_prerequisites
    echo
    
    setup_gcp
    echo
    
    build_and_push
    echo
    
    setup_service_account
    echo
    
    deploy_service
    echo
    
    test_deployment
    echo
    
    setup_monitoring
    echo
    
    # Final summary
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    
    log_info "============================================"
    log_info "Deployment Summary"
    log_info "============================================"
    log_success "✅ Service: $SERVICE_NAME"
    log_success "✅ URL: $SERVICE_URL"
    log_success "✅ Region: $REGION"
    log_success "✅ Image: gcr.io/$PROJECT_ID/$IMAGE_NAME:$TAG"
    echo
    log_info "Test endpoints:"
    log_info "  Health Check: $SERVICE_URL/healthz"
    log_info "  Rick Roll Info: $SERVICE_URL/v1/media/youtube/info"
    log_info "  MP3 Download: $SERVICE_URL/v1/media/youtube/mp3"
    log_info "  MP4 Download: $SERVICE_URL/v1/media/youtube/mp4"
    echo
    log_success "🎉 Deployment completed successfully!"
}

# Handle script arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "GCP Cloud Run Deployment Script"
    echo
    echo "Usage: $0 [options]"
    echo
    echo "Environment Variables:"
    echo "  GCP_PROJECT_ID    - GCP project ID (required)"
    echo "  GCP_REGION        - GCP region (default: us-central1)"
    echo "  BUILD_TAG         - Image tag (default: latest)"
    echo
    echo "Examples:"
    echo "  export GCP_PROJECT_ID=my-project"
    echo "  export GCP_REGION=us-west1"
    echo "  export BUILD_TAG=v1.0.0"
    echo "  $0"
    echo
    exit 0
fi

# Run the deployment
main
exit $?
