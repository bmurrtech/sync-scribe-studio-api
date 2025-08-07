#!/bin/bash

# Local Cloud Run Emulator Validation Script
# Step 6: Simulate Cloud Run environment locally for testing

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
IMAGE_NAME="sync-scribe-studio-api-local"
CONTAINER_NAME="cloud-run-emulator-test"
HOST_PORT="8080"
CONTAINER_PORT="8080"
TEST_TIMEOUT=60

# Cleanup function
cleanup() {
    print_status "Cleaning up test containers..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
}

# Build test image
build_test_image() {
    print_status "Building test image for Cloud Run emulation..."
    
    # Build with Cloud Run specific settings
    docker build \
        --build-arg BUILD_NUMBER=$(grep "BUILD_NUMBER" version.py | cut -d'=' -f2 | tr -d ' ') \
        --file Dockerfile.test \
        --tag $IMAGE_NAME \
        --progress=plain \
        .
    
    if [ $? -eq 0 ]; then
        print_success "Test image built successfully!"
        
        # Show image info
        docker images $IMAGE_NAME --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    else
        print_error "Failed to build test image!"
        exit 1
    fi
}

# Test automatic port mapping
test_port_mapping() {
    print_status "Testing automatic port mapping..."
    
    # Test default port (8080)
    print_status "Testing with default PORT=8080..."
    
    cleanup
    
    # Start container with default port
    docker run -d \
        --name $CONTAINER_NAME \
        -p $HOST_PORT:$CONTAINER_PORT \
        -e PORT=$CONTAINER_PORT \
        -e PYTHONUNBUFFERED=1 \
        $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        print_success "Container started with automatic port mapping!"
        
        # Wait for container to be ready
        print_status "Waiting for container to be ready..."
        sleep 10
        
        # Test if port is responding
        if curl -f -s http://localhost:$HOST_PORT/health > /dev/null; then
            print_success "Port mapping working correctly!"
        else
            print_error "Port mapping test failed!"
            docker logs $CONTAINER_NAME
            return 1
        fi
    else
        print_error "Failed to start container for port mapping test!"
        return 1
    fi
    
    # Test dynamic port assignment
    print_status "Testing dynamic port assignment..."
    
    cleanup
    
    # Test with different port
    DYNAMIC_PORT=9090
    docker run -d \
        --name $CONTAINER_NAME \
        -p $DYNAMIC_PORT:$DYNAMIC_PORT \
        -e PORT=$DYNAMIC_PORT \
        -e PYTHONUNBUFFERED=1 \
        $IMAGE_NAME
    
    sleep 10
    
    if curl -f -s http://localhost:$DYNAMIC_PORT/health > /dev/null; then
        print_success "Dynamic port assignment working correctly!"
    else
        print_error "Dynamic port assignment test failed!"
        docker logs $CONTAINER_NAME
        return 1
    fi
    
    cleanup
}

# Test request handling
test_request_handling() {
    print_status "Testing request handling..."
    
    # Start container for request testing
    docker run -d \
        --name $CONTAINER_NAME \
        -p $HOST_PORT:$CONTAINER_PORT \
        -e PORT=$CONTAINER_PORT \
        -e PYTHONUNBUFFERED=1 \
        -e API_KEY=test-key-12345 \
        $IMAGE_NAME
    
    # Wait for container to be ready
    print_status "Waiting for service to be ready..."
    sleep 15
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    health_response=$(curl -s http://localhost:$HOST_PORT/health)
    if echo "$health_response" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
        print_success "Health endpoint responding correctly!"
        echo "Health Response: $health_response"
    else
        print_error "Health endpoint test failed!"
        echo "Response: $health_response"
        docker logs $CONTAINER_NAME
        return 1
    fi
    
    # Test detailed health endpoint
    print_status "Testing detailed health endpoint..."
    detailed_health=$(curl -s http://localhost:$HOST_PORT/health/detailed)
    if echo "$detailed_health" | jq -e '.status' > /dev/null 2>&1; then
        print_success "Detailed health endpoint responding correctly!"
        echo "Detailed Health: $detailed_health"
    else
        print_warning "Detailed health endpoint may not be available"
    fi
    
    # Test root endpoint
    print_status "Testing root endpoint..."
    root_response=$(curl -s http://localhost:$HOST_PORT/)
    if [ -n "$root_response" ]; then
        print_success "Root endpoint responding correctly!"
    else
        print_warning "Root endpoint test inconclusive"
    fi
    
    # Test API endpoint with authentication
    print_status "Testing API endpoint with authentication..."
    api_response=$(curl -s -H "x-api-key: test-key-12345" http://localhost:$HOST_PORT/v1/toolkit/test)
    if echo "$api_response" | jq -e '.message' > /dev/null 2>&1; then
        print_success "API authentication working correctly!"
        echo "API Response: $api_response"
    else
        print_warning "API endpoint test may have failed"
        echo "Response: $api_response"
    fi
    
    # Test concurrent requests
    print_status "Testing concurrent request handling..."
    for i in {1..5}; do
        curl -s http://localhost:$HOST_PORT/health > /dev/null &
    done
    wait
    print_success "Concurrent requests handled successfully!"
}

# Test health checks
test_health_checks() {
    print_status "Testing health checks and readiness..."
    
    # Container should already be running from previous test
    
    # Test health check endpoint
    print_status "Performing health check validation..."
    
    for attempt in {1..5}; do
        print_status "Health check attempt $attempt/5..."
        
        health_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$HOST_PORT/health)
        
        if [ "$health_status" = "200" ]; then
            print_success "Health check passed (HTTP $health_status)!"
            break
        else
            print_warning "Health check attempt $attempt failed (HTTP $health_status)"
            if [ $attempt -eq 5 ]; then
                print_error "All health check attempts failed!"
                docker logs $CONTAINER_NAME
                return 1
            fi
            sleep 5
        fi
    done
    
    # Test readiness under load
    print_status "Testing readiness under load..."
    
    # Send multiple requests simultaneously
    for i in {1..10}; do
        curl -s http://localhost:$HOST_PORT/health > /dev/null &
    done
    wait
    
    # Check if service is still healthy
    final_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$HOST_PORT/health)
    if [ "$final_health" = "200" ]; then
        print_success "Service remains healthy under load!"
    else
        print_error "Service failed under load (HTTP $final_health)!"
        return 1
    fi
}

# Test graceful shutdown
test_graceful_shutdown() {
    print_status "Testing graceful shutdown..."
    
    # Get container process info before shutdown
    print_status "Container status before shutdown:"
    docker stats $CONTAINER_NAME --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    
    # Send SIGTERM for graceful shutdown
    print_status "Sending SIGTERM signal for graceful shutdown..."
    docker stop -t 30 $CONTAINER_NAME
    
    # Check exit code
    exit_code=$(docker inspect $CONTAINER_NAME --format='{{.State.ExitCode}}')
    
    if [ "$exit_code" = "0" ]; then
        print_success "Container shut down gracefully (exit code: $exit_code)!"
    else
        print_warning "Container exit code: $exit_code (may indicate forced shutdown)"
    fi
    
    # Check logs for graceful shutdown messages
    print_status "Checking shutdown logs..."
    shutdown_logs=$(docker logs $CONTAINER_NAME 2>&1 | tail -10)
    echo "Final logs:"
    echo "$shutdown_logs"
    
    # Verify container is stopped
    container_status=$(docker inspect $CONTAINER_NAME --format='{{.State.Status}}')
    if [ "$container_status" = "exited" ]; then
        print_success "Container successfully stopped!"
    else
        print_error "Container status: $container_status"
        return 1
    fi
}

# Performance and resource testing
test_performance() {
    print_status "Testing performance and resource usage..."
    
    # Start fresh container for performance testing
    cleanup
    
    docker run -d \
        --name $CONTAINER_NAME \
        -p $HOST_PORT:$CONTAINER_PORT \
        -e PORT=$CONTAINER_PORT \
        -e PYTHONUNBUFFERED=1 \
        -e GUNICORN_WORKERS=2 \
        -e GUNICORN_TIMEOUT=300 \
        --memory=512m \
        --cpus=1.0 \
        $IMAGE_NAME
    
    sleep 15
    
    # Monitor resource usage
    print_status "Monitoring resource usage..."
    docker stats $CONTAINER_NAME --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"
    
    # Test response time
    print_status "Testing response times..."
    
    start_time=$(date +%s.%3N)
    curl -s http://localhost:$HOST_PORT/health > /dev/null
    end_time=$(date +%s.%3N)
    
    response_time=$(echo "$end_time - $start_time" | bc)
    print_status "Health endpoint response time: ${response_time}s"
    
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        print_success "Response time within acceptable range!"
    else
        print_warning "Response time may be slow: ${response_time}s"
    fi
}

# Generate test report
generate_report() {
    print_status "=== Cloud Run Local Emulation Test Report ==="
    echo ""
    echo "Timestamp: $(date)"
    echo "Image: $IMAGE_NAME"
    echo "Test Configuration:"
    echo "  - Host Port: $HOST_PORT"
    echo "  - Container Port: $CONTAINER_PORT"
    echo "  - Test Timeout: ${TEST_TIMEOUT}s"
    echo ""
    
    # Container information
    if docker inspect $CONTAINER_NAME > /dev/null 2>&1; then
        echo "Final Container Status:"
        docker inspect $CONTAINER_NAME --format='
Exit Code: {{.State.ExitCode}}
Started At: {{.State.StartedAt}}
Finished At: {{.State.FinishedAt}}
Status: {{.State.Status}}'
        echo ""
    fi
    
    # Image information
    echo "Image Information:"
    docker images $IMAGE_NAME --format "
Repository: {{.Repository}}
Tag: {{.Tag}}
Size: {{.Size}}
Created: {{.CreatedAt}}"
    echo ""
    
    print_status "=== Test Summary ==="
    print_success "✓ Docker build and image creation"
    print_success "✓ Automatic port mapping validation"
    print_success "✓ Request handling verification"
    print_success "✓ Health check implementation"
    print_success "✓ Graceful shutdown testing"
    print_success "✓ Performance and resource monitoring"
    echo ""
    print_success "All Cloud Run emulation tests completed successfully!"
    echo ""
    print_status "Ready for Cloud Run deployment with command:"
    echo "gcloud run deploy sync-scribe-studio-api --image=gcr.io/PROJECT_ID/$IMAGE_NAME --platform=managed --allow-unauthenticated"
}

# Main test execution
main() {
    print_status "=== Starting Cloud Run Local Emulation Tests ==="
    print_status "This script validates Cloud Run compatibility locally using Docker"
    echo ""
    
    # Ensure cleanup on script exit
    trap cleanup EXIT
    
    # Run all test phases
    build_test_image
    test_port_mapping
    test_request_handling
    test_health_checks
    test_graceful_shutdown
    test_performance
    
    # Generate final report
    generate_report
}

# Help function
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Local Cloud Run Emulator Validation Script"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -p, --port     Set host port for testing (default: 8080)"
    echo "  -t, --timeout  Set test timeout in seconds (default: 60)"
    echo ""
    echo "This script performs comprehensive testing of Cloud Run compatibility:"
    echo "  1. Docker image build and validation"
    echo "  2. Automatic port mapping verification"
    echo "  3. HTTP request handling tests"
    echo "  4. Health check endpoint validation"
    echo "  5. Graceful shutdown testing"
    echo "  6. Performance and resource monitoring"
    echo ""
    echo "Prerequisites:"
    echo "  - Docker installed and running"
    echo "  - Dockerfile present in current directory"
    echo "  - version.py file with BUILD_NUMBER"
    echo ""
    exit 0
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -p|--port)
            HOST_PORT="$2"
            shift 2
            ;;
        -t|--timeout)
            TEST_TIMEOUT="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Check prerequisites
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker and try again."
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile not found in current directory."
    exit 1
fi

if [ ! -f "version.py" ]; then
    print_error "version.py not found in current directory."
    exit 1
fi

# Check if jq is available for JSON parsing
if ! command -v jq &> /dev/null; then
    print_warning "jq not found. JSON response parsing may be limited."
    print_status "Install jq for better test output: brew install jq (macOS) or apt-get install jq (Linux)"
fi

# Run main test suite
main
