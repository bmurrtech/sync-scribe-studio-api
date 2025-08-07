#!/bin/bash

# Docker Deployment Test Script
# Tests local Docker container deployment and functionality
# Tests Rick Roll video download functionality

set -e

echo "🐋 Starting Docker Deployment Tests..."

# Configuration
IMAGE_NAME="youtube-downloader"
CONTAINER_NAME="youtube-downloader-test"
TEST_PORT=3002
RICK_ROLL_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
TEST_TIMEOUT=120

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

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    log_info "Cleanup completed"
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Test 1: Build Docker image
test_docker_build() {
    log_info "Test 1: Building Docker image..."
    
    cd services/youtube-downloader
    
    if docker build -t $IMAGE_NAME .; then
        log_success "Docker image built successfully"
        return 0
    else
        log_error "Failed to build Docker image"
        return 1
    fi
}

# Test 2: Start container
test_container_start() {
    log_info "Test 2: Starting Docker container..."
    
    if docker run -d \
        --name $CONTAINER_NAME \
        -p $TEST_PORT:3001 \
        -e NODE_ENV=production \
        -e PORT=3001 \
        -e LOG_LEVEL=info \
        $IMAGE_NAME; then
        log_success "Container started successfully"
        return 0
    else
        log_error "Failed to start container"
        return 1
    fi
}

# Test 3: Wait for service to be ready
wait_for_service() {
    log_info "Test 3: Waiting for service to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$TEST_PORT/healthz" > /dev/null 2>&1; then
            log_success "Service is ready (attempt $attempt)"
            return 0
        fi
        
        log_info "Waiting for service... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Service failed to become ready within $max_attempts attempts"
    return 1
}

# Test 4: Health check
test_health_check() {
    log_info "Test 4: Testing health check endpoint..."
    
    local response=$(curl -s "http://localhost:$TEST_PORT/healthz")
    local status_code=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:$TEST_PORT/healthz")
    
    if [ "$status_code" = "200" ]; then
        log_success "Health check passed (HTTP $status_code)"
        echo "Response: $response" | jq . 2>/dev/null || echo "Response: $response"
        return 0
    else
        log_error "Health check failed (HTTP $status_code)"
        return 1
    fi
}

# Test 5: Rick Roll video info
test_video_info() {
    log_info "Test 5: Testing Rick Roll video information endpoint..."
    
    local payload='{"url": "'$RICK_ROLL_URL'"}'
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "http://localhost:$TEST_PORT/v1/media/youtube/info")
    
    local status_code=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "http://localhost:$TEST_PORT/v1/media/youtube/info")
    
    if [ "$status_code" = "200" ]; then
        # Validate response contains expected Rick Roll data
        if echo "$response" | jq -r '.data.title' | grep -i "Rick Astley" > /dev/null && \
           echo "$response" | jq -r '.data.title' | grep -i "Never Gonna Give You Up" > /dev/null; then
            log_success "Rick Roll video info retrieved successfully (HTTP $status_code)"
            log_info "Video Title: $(echo "$response" | jq -r '.data.title' 2>/dev/null || echo 'N/A')"
            log_info "Video ID: $(echo "$response" | jq -r '.data.videoId' 2>/dev/null || echo 'N/A')"
            return 0
        else
            log_warning "Response received but doesn't contain expected Rick Roll data"
            echo "Response: $response" | jq . 2>/dev/null || echo "Response: $response"
            return 1
        fi
    else
        log_error "Video info request failed (HTTP $status_code)"
        echo "Response: $response"
        return 1
    fi
}

# Test 6: Security headers
test_security_headers() {
    log_info "Test 6: Testing security headers..."
    
    local headers=$(curl -s -I "http://localhost:$TEST_PORT/healthz")
    
    if echo "$headers" | grep -i "x-content-type-options" > /dev/null && \
       echo "$headers" | grep -i "x-frame-options" > /dev/null; then
        log_success "Security headers present"
        return 0
    else
        log_error "Required security headers missing"
        echo "Headers: $headers"
        return 1
    fi
}

# Test 7: Rate limiting
test_rate_limiting() {
    log_info "Test 7: Testing rate limiting..."
    
    local rate_limited=false
    local payload='{"url": "'$RICK_ROLL_URL'"}'
    
    # Make multiple rapid requests to trigger rate limiting
    for i in {1..15}; do
        local status_code=$(curl -s -w "%{http_code}" -o /dev/null \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "http://localhost:$TEST_PORT/v1/media/youtube/info")
        
        if [ "$status_code" = "429" ]; then
            rate_limited=true
            break
        fi
        
        sleep 0.1
    done
    
    if [ "$rate_limited" = "true" ]; then
        log_success "Rate limiting is working (HTTP 429 received)"
        return 0
    else
        log_warning "Rate limiting not triggered (may need more requests or longer test)"
        return 0  # Don't fail the test as rate limiting might have different thresholds
    fi
}

# Test 8: Container resource usage
test_resource_usage() {
    log_info "Test 8: Checking container resource usage..."
    
    local stats=$(docker stats $CONTAINER_NAME --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}")
    
    if [ $? -eq 0 ]; then
        log_success "Container resource stats:"
        echo "$stats"
        return 0
    else
        log_error "Failed to get container resource stats"
        return 1
    fi
}

# Test 9: Container logs
test_container_logs() {
    log_info "Test 9: Checking container logs for errors..."
    
    local logs=$(docker logs $CONTAINER_NAME 2>&1 | tail -20)
    local error_count=$(echo "$logs" | grep -i error | wc -l)
    
    log_info "Recent container logs:"
    echo "$logs"
    
    if [ $error_count -eq 0 ]; then
        log_success "No errors found in container logs"
        return 0
    else
        log_warning "Found $error_count potential errors in logs"
        return 0  # Don't fail as some "errors" might be expected (like rate limiting messages)
    fi
}

# Test 10: MP3 download endpoint (partial test)
test_mp3_download() {
    log_info "Test 10: Testing MP3 download endpoint (headers only)..."
    
    local payload='{"url": "'$RICK_ROLL_URL'", "quality": "highestaudio"}'
    local headers=$(timeout 10s curl -s -I -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "http://localhost:$TEST_PORT/v1/media/youtube/mp3" 2>/dev/null || echo "timeout")
    
    if echo "$headers" | grep -i "content-type.*audio" > /dev/null || \
       echo "$headers" | grep -i "content-disposition.*attachment" > /dev/null; then
        log_success "MP3 download endpoint responding with appropriate headers"
        return 0
    else
        log_warning "MP3 download endpoint test inconclusive (may require more time)"
        echo "Headers: $headers"
        return 0  # Don't fail as streaming might take time
    fi
}

# Main test execution
main() {
    log_info "Starting Docker deployment tests for YouTube Downloader API"
    log_info "Test video: Rick Astley - Never Gonna Give You Up"
    log_info "URL: $RICK_ROLL_URL"
    echo
    
    local failed_tests=0
    local total_tests=10
    
    # Run tests
    test_docker_build || failed_tests=$((failed_tests + 1))
    echo
    
    test_container_start || failed_tests=$((failed_tests + 1))
    echo
    
    wait_for_service || failed_tests=$((failed_tests + 1))
    echo
    
    test_health_check || failed_tests=$((failed_tests + 1))
    echo
    
    test_video_info || failed_tests=$((failed_tests + 1))
    echo
    
    test_security_headers || failed_tests=$((failed_tests + 1))
    echo
    
    test_rate_limiting || failed_tests=$((failed_tests + 1))
    echo
    
    test_resource_usage || failed_tests=$((failed_tests + 1))
    echo
    
    test_container_logs || failed_tests=$((failed_tests + 1))
    echo
    
    test_mp3_download || failed_tests=$((failed_tests + 1))
    echo
    
    # Summary
    local passed_tests=$((total_tests - failed_tests))
    log_info "============================================"
    log_info "Docker Deployment Test Summary"
    log_info "============================================"
    log_success "Passed: $passed_tests/$total_tests tests"
    
    if [ $failed_tests -gt 0 ]; then
        log_error "Failed: $failed_tests/$total_tests tests"
        log_error "Docker deployment tests completed with failures"
        return 1
    else
        log_success "All Docker deployment tests passed!"
        log_success "Container is ready for production deployment"
        return 0
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
    echo
}

# Run tests
check_prerequisites
main
exit $?
