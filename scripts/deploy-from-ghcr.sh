#!/bin/bash

# =============================================================================
# Sync Scribe Studio API - GHCR Deployment Script
# =============================================================================
# 
# This script deploys the Sync Scribe Studio API using container images 
# from GitHub Container Registry (GHCR) to various cloud platforms.
#
# Usage:
#   ./scripts/deploy-from-ghcr.sh [OPTIONS]
#
# Examples:
#   ./scripts/deploy-from-ghcr.sh --platform local --tag latest
#   ./scripts/deploy-from-ghcr.sh --platform cloud-run --tag build-123 --project my-gcp-project
#   ./scripts/deploy-from-ghcr.sh --platform docker-compose --tag latest --env production
#
# =============================================================================

set -euo pipefail

# Configuration
DEFAULT_REGISTRY="ghcr.io"
DEFAULT_REPOSITORY="bmurrtech/sync-scribe-studio-api"
DEFAULT_TAG="latest"
DEFAULT_PLATFORM="local"
DEFAULT_PORT="8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Initialize variables
REGISTRY="$DEFAULT_REGISTRY"
REPOSITORY="$DEFAULT_REPOSITORY"
TAG="$DEFAULT_TAG"
PLATFORM="$DEFAULT_PLATFORM"
PORT="$DEFAULT_PORT"
PROJECT_ID=""
REGION="us-central1"
SERVICE_NAME="sync-scribe-studio-api"
ENV_FILE=""
ENVIRONMENT="development"
FORCE_PULL=false
DETACHED=true
CLEANUP=false

# Function to display usage
usage() {
    cat << EOF
${BLUE}Sync Scribe Studio API - GHCR Deployment Script${NC}

${YELLOW}USAGE:${NC}
    $0 [OPTIONS]

${YELLOW}OPTIONS:${NC}
    -r, --registry REGISTRY     Container registry (default: $DEFAULT_REGISTRY)
    -R, --repository REPO       Repository name (default: $DEFAULT_REPOSITORY)
    -t, --tag TAG              Image tag (default: $DEFAULT_TAG)
    -p, --platform PLATFORM    Deployment platform: local, cloud-run, docker-compose
    -P, --port PORT            Local port mapping (default: $DEFAULT_PORT)
    --project PROJECT_ID       GCP Project ID (required for cloud-run)
    --region REGION            GCP Region (default: $REGION)
    --service SERVICE_NAME     Cloud Run service name (default: $SERVICE_NAME)
    -e, --env-file FILE        Environment file path
    --environment ENV          Environment type: development, staging, production
    --force-pull               Force pull latest image
    --foreground               Run in foreground (not detached)
    --cleanup                  Clean up existing containers/services
    -h, --help                 Show this help message

${YELLOW}PLATFORMS:${NC}
    ${GREEN}local${NC}         - Run locally with Docker
    ${GREEN}cloud-run${NC}     - Deploy to Google Cloud Run
    ${GREEN}docker-compose${NC} - Run with Docker Compose

${YELLOW}EXAMPLES:${NC}
    # Run locally with latest image
    $0 --platform local --tag latest

    # Deploy to Cloud Run with specific build
    $0 --platform cloud-run --tag build-123 --project my-gcp-project

    # Run with Docker Compose using production environment
    $0 --platform docker-compose --tag v1.2.3 --environment production

    # Force update local deployment with cleanup
    $0 --platform local --force-pull --cleanup --env-file .env.local

EOF
}

# Function to log messages
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${CYAN}[$timestamp] INFO:${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[$timestamp] WARN:${NC} $message" ;;
        "ERROR") echo -e "${RED}[$timestamp] ERROR:${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[$timestamp] SUCCESS:${NC} $message" ;;
        "DEBUG") echo -e "${PURPLE}[$timestamp] DEBUG:${NC} $message" ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    if ! command_exists docker; then
        log "ERROR" "Docker is required but not installed"
        exit 1
    fi
    
    case "$PLATFORM" in
        "cloud-run")
            if ! command_exists gcloud; then
                log "ERROR" "gcloud CLI is required for Cloud Run deployment"
                exit 1
            fi
            if [[ -z "$PROJECT_ID" ]]; then
                log "ERROR" "GCP Project ID is required for Cloud Run deployment"
                exit 1
            fi
            ;;
        "docker-compose")
            if ! command_exists docker-compose; then
                log "ERROR" "docker-compose is required for Docker Compose deployment"
                exit 1
            fi
            ;;
    esac
    
    log "SUCCESS" "Prerequisites check completed"
}

# Function to construct full image URL
get_image_url() {
    echo "${REGISTRY}/${REPOSITORY}:${TAG}"
}

# Function to pull image
pull_image() {
    local image_url=$(get_image_url)
    log "INFO" "Pulling image: $image_url"
    
    if [[ "$FORCE_PULL" == true ]]; then
        docker pull --platform linux/amd64 "$image_url"
    else
        # Check if image exists locally
        if ! docker image inspect "$image_url" >/dev/null 2>&1; then
            docker pull --platform linux/amd64 "$image_url"
        else
            log "INFO" "Image already exists locally (use --force-pull to update)"
        fi
    fi
    
    log "SUCCESS" "Image ready: $image_url"
}

# Function to get environment variables
get_env_args() {
    local env_args=""
    
    # Default environment variables
    env_args+=" -e PORT=$PORT"
    env_args+=" -e ENVIRONMENT=$ENVIRONMENT"
    env_args+=" -e BUILD_NUMBER=$(date +%s)"
    
    # Add environment file if specified
    if [[ -n "$ENV_FILE" ]]; then
        if [[ -f "$ENV_FILE" ]]; then
            env_args+=" --env-file $ENV_FILE"
            log "INFO" "Using environment file: $ENV_FILE"
        else
            log "WARN" "Environment file not found: $ENV_FILE"
        fi
    fi
    
    # Set default environment variables if not in file
    if [[ -z "${API_KEY:-}" && ! -f "$ENV_FILE" ]]; then
        log "WARN" "API_KEY not set - generating temporary key"
        env_args+=" -e API_KEY=temp-$(openssl rand -hex 16)"
    fi
    
    if [[ -z "${DB_TOKEN:-}" && ! -f "$ENV_FILE" ]]; then
        log "WARN" "DB_TOKEN not set - generating temporary token"  
        env_args+=" -e DB_TOKEN=temp-$(openssl rand -hex 16)"
    fi
    
    echo "$env_args"
}

# Function for local Docker deployment
deploy_local() {
    log "INFO" "Starting local Docker deployment..."
    
    local image_url=$(get_image_url)
    local container_name="sync-scribe-studio-api"
    local env_args=$(get_env_args)
    
    # Cleanup existing container if requested
    if [[ "$CLEANUP" == true ]]; then
        log "INFO" "Cleaning up existing containers..."
        docker stop "$container_name" 2>/dev/null || true
        docker rm "$container_name" 2>/dev/null || true
    fi
    
    # Run container
    local run_args="--name $container_name -p $PORT:8080"
    
    if [[ "$DETACHED" == true ]]; then
        run_args+=" -d"
    fi
    
    log "INFO" "Starting container..."
    eval "docker run $run_args $env_args $image_url"
    
    if [[ "$DETACHED" == true ]]; then
        # Wait for health check
        log "INFO" "Waiting for service to be ready..."
        sleep 5
        
        local max_attempts=30
        local attempt=0
        
        while [[ $attempt -lt $max_attempts ]]; do
            if curl -f "http://localhost:$PORT/health" >/dev/null 2>&1; then
                break
            fi
            ((attempt++))
            sleep 2
        done
        
        if [[ $attempt -eq $max_attempts ]]; then
            log "ERROR" "Health check failed after $max_attempts attempts"
            return 1
        fi
        
        log "SUCCESS" "Service is running at http://localhost:$PORT"
        log "INFO" "Health endpoint: http://localhost:$PORT/health"
        log "INFO" "Service info: http://localhost:$PORT/"
        
        # Show container logs
        echo ""
        log "INFO" "Container logs (last 10 lines):"
        docker logs --tail 10 "$container_name"
        
        echo ""
        log "INFO" "To follow logs: docker logs -f $container_name"
        log "INFO" "To stop: docker stop $container_name"
    fi
}

# Function for Cloud Run deployment
deploy_cloud_run() {
    log "INFO" "Starting Cloud Run deployment..."
    
    local image_url=$(get_image_url)
    
    # Authenticate with gcloud if needed
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log "INFO" "Authenticating with gcloud..."
        gcloud auth login
    fi
    
    # Set project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log "INFO" "Enabling required APIs..."
    gcloud services enable run.googleapis.com containerregistry.googleapis.com
    
    # Deploy to Cloud Run
    log "INFO" "Deploying to Cloud Run..."
    
    local deploy_args=(
        "run" "deploy" "$SERVICE_NAME"
        "--image" "$image_url"
        "--platform" "managed"
        "--region" "$REGION"
        "--allow-unauthenticated"
        "--port" "8080"
        "--memory" "2Gi"
        "--cpu" "2"
        "--concurrency" "100"
        "--max-instances" "10"
        "--timeout" "300"
        "--set-env-vars" "PORT=8080,ENVIRONMENT=$ENVIRONMENT"
    )
    
    # Add environment variables from file
    if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
        log "INFO" "Adding environment variables from $ENV_FILE"
        local env_vars=""
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            
            # Remove quotes from value
            value=$(echo "$value" | sed 's/^["'"'"']//;s/["'"'"']$//')
            
            if [[ -n "$env_vars" ]]; then
                env_vars+=","
            fi
            env_vars+="$key=$value"
        done < "$ENV_FILE"
        
        if [[ -n "$env_vars" ]]; then
            deploy_args+=("--update-env-vars" "$env_vars")
        fi
    fi
    
    gcloud "${deploy_args[@]}"
    
    # Get service URL
    local service_url=$(gcloud run services describe "$SERVICE_NAME" \
        --platform managed \
        --region "$REGION" \
        --format 'value(status.url)')
    
    log "SUCCESS" "Deployment completed!"
    log "INFO" "Service URL: $service_url"
    log "INFO" "Health endpoint: $service_url/health"
    
    # Test the deployment
    log "INFO" "Testing deployment..."
    if curl -f "$service_url/health" >/dev/null 2>&1; then
        log "SUCCESS" "Health check passed"
    else
        log "WARN" "Health check failed - service may still be starting"
    fi
}

# Function to create docker-compose.yml
create_docker_compose() {
    local image_url=$(get_image_url)
    local compose_file="docker-compose.override.yml"
    
    cat > "$compose_file" << EOF
version: '3.8'

services:
  api:
    image: $image_url
    ports:
      - "$PORT:8080"
    environment:
      - PORT=8080
      - ENVIRONMENT=$ENVIRONMENT
      - BUILD_NUMBER=\${BUILD_NUMBER:-$(date +%s)}
EOF

    if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
        echo "    env_file:" >> "$compose_file"
        echo "      - $ENV_FILE" >> "$compose_file"
    fi
    
    cat >> "$compose_file" << EOF
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  # Optional: Add Redis for caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:

EOF

    log "SUCCESS" "Created $compose_file"
    return "$compose_file"
}

# Function for Docker Compose deployment  
deploy_docker_compose() {
    log "INFO" "Starting Docker Compose deployment..."
    
    local compose_file
    compose_file=$(create_docker_compose)
    
    # Cleanup if requested
    if [[ "$CLEANUP" == true ]]; then
        log "INFO" "Cleaning up existing services..."
        docker-compose -f "$compose_file" down -v 2>/dev/null || true
    fi
    
    # Start services
    log "INFO" "Starting services with Docker Compose..."
    
    if [[ "$DETACHED" == true ]]; then
        docker-compose -f "$compose_file" up -d
    else
        docker-compose -f "$compose_file" up
    fi
    
    if [[ "$DETACHED" == true ]]; then
        # Wait for services to be ready
        log "INFO" "Waiting for services to be ready..."
        sleep 10
        
        # Check health
        if curl -f "http://localhost:$PORT/health" >/dev/null 2>&1; then
            log "SUCCESS" "Services are running at http://localhost:$PORT"
            log "INFO" "Health endpoint: http://localhost:$PORT/health"
            log "INFO" "Service info: http://localhost:$PORT/"
            
            echo ""
            log "INFO" "Service status:"
            docker-compose -f "$compose_file" ps
            
            echo ""
            log "INFO" "To view logs: docker-compose -f $compose_file logs -f"
            log "INFO" "To stop: docker-compose -f $compose_file down"
        else
            log "ERROR" "Health check failed"
            return 1
        fi
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -R|--repository)
            REPOSITORY="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -P|--port)
            PORT="$2"
            shift 2
            ;;
        --project)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -e|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --force-pull)
            FORCE_PULL=true
            shift
            ;;
        --foreground)
            DETACHED=false
            shift
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate platform
case "$PLATFORM" in
    "local"|"cloud-run"|"docker-compose")
        ;;
    *)
        log "ERROR" "Invalid platform: $PLATFORM"
        log "ERROR" "Supported platforms: local, cloud-run, docker-compose"
        exit 1
        ;;
esac

# Main execution
main() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "  Sync Scribe Studio API Deployment"
    echo "========================================"
    echo -e "${NC}"
    
    log "INFO" "Configuration:"
    log "INFO" "  Registry: $REGISTRY"
    log "INFO" "  Repository: $REPOSITORY" 
    log "INFO" "  Tag: $TAG"
    log "INFO" "  Platform: $PLATFORM"
    log "INFO" "  Environment: $ENVIRONMENT"
    [[ -n "$ENV_FILE" ]] && log "INFO" "  Env File: $ENV_FILE"
    [[ "$PLATFORM" == "local" || "$PLATFORM" == "docker-compose" ]] && log "INFO" "  Port: $PORT"
    [[ "$PLATFORM" == "cloud-run" ]] && log "INFO" "  GCP Project: $PROJECT_ID"
    [[ "$PLATFORM" == "cloud-run" ]] && log "INFO" "  GCP Region: $REGION"
    
    echo ""
    
    # Run deployment pipeline
    check_prerequisites
    pull_image
    
    case "$PLATFORM" in
        "local")
            deploy_local
            ;;
        "cloud-run")
            deploy_cloud_run
            ;;
        "docker-compose")
            deploy_docker_compose
            ;;
    esac
    
    echo ""
    log "SUCCESS" "Deployment completed successfully! 🚀"
}

# Execute main function
main "$@"
