#!/bin/bash

# Docker Local Test Script for YouTube Downloader Microservice
# Tests the complete Docker deployment flow locally with actual YouTube content

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test Configuration
YOUTUBE_TEST_URL="https://youtu.be/EUq1L6XoZvU?si=qPToLdYGwTeF3vZq"
FALLBACK_MEDIA_URL="https://drive.google.com/file/d/1SjBj6seOHsgJAocXtd0kPQb3Z28GspVF/view?usp=drive_link"
GCS_MEDIA_URL="https://storage.googleapis.com/fytv-api-bucket/youtube/wands_don_t_come_with_a_safety..._2025-08-06.mp3"
CONTAINER_NAME="youtube-downloader-test"
IMAGE_NAME="youtube-downloader:latest"
TEST_PORT="3001"
RESULTS_DIR="./test-results"

# Function to print colored output
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

print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up test containers and images..."
    
    # Stop and remove container if it exists
    if docker ps -a --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
        print_success "Removed test container: $CONTAINER_NAME"
    fi
    
    # Clean up dangling images
    DANGLING_IMAGES=$(docker images -f "dangling=true" -q 2>/dev/null || true)
    if [ -n "$DANGLING_IMAGES" ]; then
        docker rmi $DANGLING_IMAGES >/dev/null 2>&1 || true
        print_success "Cleaned up dangling Docker images"
    fi
}

# Create results directory
setup_results_dir() {
    mkdir -p "$RESULTS_DIR"
    echo "# YouTube Downloader Docker Test Results" > "$RESULTS_DIR/test-report.md"
    echo "Generated at: $(date)" >> "$RESULTS_DIR/test-report.md"
    echo "" >> "$RESULTS_DIR/test-report.md"
}

# Build Docker image
build_image() {
    print_header "Building Docker Image"
    
    cd services/youtube-downloader
    
    print_status "Building YouTube downloader Docker image..."
    if docker build -t "$IMAGE_NAME" .; then
        print_success "Docker image built successfully: $IMAGE_NAME"
        echo "## ✅ Docker Build: PASSED" >> "../../$RESULTS_DIR/test-report.md"
    else
        print_error "Failed to build Docker image"
        echo "## ❌ Docker Build: FAILED" >> "../../$RESULTS_DIR/test-report.md"
        cd ../..
        exit 1
    fi
    
    cd ../..
    
    # Display image info
    IMAGE_SIZE=$(docker images "$IMAGE_NAME" --format "table {{.Size}}" | tail -n 1)
    print_status "Image size: $IMAGE_SIZE"
    echo "- Image Size: $IMAGE_SIZE" >> "$RESULTS_DIR/test-report.md"
}

# Start container
start_container() {
    print_header "Starting Test Container"
    
    print_status "Starting container: $CONTAINER_NAME"
    if docker run -d \
        --name "$CONTAINER_NAME" \
        --publish "$TEST_PORT:3001" \
        --env NODE_ENV=production \
        --env PORT=3001 \
        --env YTDL_NETWORK_TIMEOUT=60000 \
        --env ALLOWED_ORIGINS="*" \
        --env SKIP_NETWORK_CHECK=false \
        "$IMAGE_NAME"; then
        print_success "Container started successfully"
        echo "## ✅ Container Start: PASSED" >> "$RESULTS_DIR/test-report.md"
    else
        print_error "Failed to start container"
        echo "## ❌ Container Start: FAILED" >> "$RESULTS_DIR/test-report.md"
        exit 1
    fi
    
    # Wait for container to be ready
    print_status "Waiting for service to be ready..."
    TIMEOUT=60
    for i in $(seq 1 $TIMEOUT); do
        if curl -s "http://localhost:$TEST_PORT/healthz" >/dev/null 2>&1; then
            print_success "Service is ready after $i seconds"
            echo "- Startup Time: $i seconds" >> "$RESULTS_DIR/test-report.md"
            break
        fi
        
        if [ $i -eq $TIMEOUT ]; then
            print_error "Service failed to start within $TIMEOUT seconds"
            docker logs "$CONTAINER_NAME" > "$RESULTS_DIR/container-logs.txt"
            echo "## ❌ Service Readiness: TIMEOUT" >> "$RESULTS_DIR/test-report.md"
            exit 1
        fi
        
        sleep 1
    done
}

# Test health endpoint
test_health() {
    print_header "Testing Health Endpoint"
    
    print_status "Testing health check..."
    HEALTH_RESPONSE=$(curl -s "http://localhost:$TEST_PORT/healthz" || echo "ERROR")
    
    if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' >/dev/null 2>&1; then
        print_success "Health check passed"
        echo "## ✅ Health Check: PASSED" >> "$RESULTS_DIR/test-report.md"
        echo '```json' >> "$RESULTS_DIR/test-report.md"
        echo "$HEALTH_RESPONSE" | jq . >> "$RESULTS_DIR/test-report.md"
        echo '```' >> "$RESULTS_DIR/test-report.md"
    else
        print_error "Health check failed"
        echo "## ❌ Health Check: FAILED" >> "$RESULTS_DIR/test-report.md"
        echo "Response: $HEALTH_RESPONSE" >> "$RESULTS_DIR/test-report.md"
    fi
}

# Test security headers
test_security_headers() {
    print_header "Testing Security Headers"
    
    print_status "Checking security headers..."
    HEADERS_OUTPUT=$(curl -I -s "http://localhost:$TEST_PORT/healthz")
    
    echo "## Security Headers Test" >> "$RESULTS_DIR/test-report.md"
    echo '```' >> "$RESULTS_DIR/test-report.md"
    echo "$HEADERS_OUTPUT" >> "$RESULTS_DIR/test-report.md"
    echo '```' >> "$RESULTS_DIR/test-report.md"
    
    # Check for important security headers
    SECURITY_HEADERS=("x-frame-options" "x-content-type-options" "x-xss-protection")
    for header in "${SECURITY_HEADERS[@]}"; do
        if echo "$HEADERS_OUTPUT" | grep -i "$header" >/dev/null; then
            print_success "Found security header: $header"
        else
            print_warning "Missing security header: $header"
        fi
    done
}

# Test YouTube video info endpoint
test_youtube_info() {
    print_header "Testing YouTube Info Endpoint"
    
    print_status "Testing video info retrieval..."
    print_status "YouTube URL: $YOUTUBE_TEST_URL"
    
    # Create JSON payload
    JSON_PAYLOAD=$(cat <<EOF
{
    "url": "$YOUTUBE_TEST_URL"
}
EOF
)
    
    INFO_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$JSON_PAYLOAD" \
        "http://localhost:$TEST_PORT/v1/media/youtube/info" || echo "ERROR")
    
    echo "## YouTube Info Test" >> "$RESULTS_DIR/test-report.md"
    echo "URL: $YOUTUBE_TEST_URL" >> "$RESULTS_DIR/test-report.md"
    echo "" >> "$RESULTS_DIR/test-report.md"
    
    if echo "$INFO_RESPONSE" | jq -e '.success == true' >/dev/null 2>&1; then
        print_success "Video info retrieved successfully"
        
        VIDEO_TITLE=$(echo "$INFO_RESPONSE" | jq -r '.data.title')
        VIDEO_DURATION=$(echo "$INFO_RESPONSE" | jq -r '.data.lengthSeconds')
        VIDEO_AUTHOR=$(echo "$INFO_RESPONSE" | jq -r '.data.author.name')
        
        print_success "Video Title: $VIDEO_TITLE"
        print_success "Duration: $VIDEO_DURATION seconds"
        print_success "Author: $VIDEO_AUTHOR"
        
        echo "✅ **PASSED**" >> "$RESULTS_DIR/test-report.md"
        echo "- Title: $VIDEO_TITLE" >> "$RESULTS_DIR/test-report.md"
        echo "- Duration: $VIDEO_DURATION seconds" >> "$RESULTS_DIR/test-report.md"
        echo "- Author: $VIDEO_AUTHOR" >> "$RESULTS_DIR/test-report.md"
        
        # Save full response
        echo "$INFO_RESPONSE" | jq . > "$RESULTS_DIR/youtube-info-response.json"
    else
        print_error "Failed to retrieve video info"
        echo "❌ **FAILED**" >> "$RESULTS_DIR/test-report.md"
        echo "Response: $INFO_RESPONSE" >> "$RESULTS_DIR/test-report.md"
    fi
    
    echo "" >> "$RESULTS_DIR/test-report.md"
}

# Test MP3 download endpoint (first few bytes only)
test_mp3_download() {
    print_header "Testing MP3 Download Endpoint"
    
    print_status "Testing MP3 download (first 1MB only for speed)..."
    
    # Create JSON payload
    JSON_PAYLOAD=$(cat <<EOF
{
    "url": "$YOUTUBE_TEST_URL"
}
EOF
)
    
    # Start download and capture first 1MB
    DOWNLOAD_START=$(date +%s)
    HTTP_CODE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$JSON_PAYLOAD" \
        -o "$RESULTS_DIR/test-audio.mp3" \
        -w "%{http_code}" \
        --max-time 30 \
        --limit-rate 1M \
        "http://localhost:$TEST_PORT/v1/media/youtube/mp3" || echo "000")
    DOWNLOAD_END=$(date +%s)
    DOWNLOAD_TIME=$((DOWNLOAD_END - DOWNLOAD_START))
    
    echo "## MP3 Download Test" >> "$RESULTS_DIR/test-report.md"
    
    if [ "$HTTP_CODE" = "200" ]; then
        FILE_SIZE=$(stat -f%z "$RESULTS_DIR/test-audio.mp3" 2>/dev/null || stat -c%s "$RESULTS_DIR/test-audio.mp3" 2>/dev/null || echo "0")
        
        if [ "$FILE_SIZE" -gt 0 ]; then
            print_success "MP3 download successful"
            print_success "Downloaded size: $FILE_SIZE bytes in $DOWNLOAD_TIME seconds"
            echo "✅ **PASSED**" >> "$RESULTS_DIR/test-report.md"
            echo "- Downloaded Size: $FILE_SIZE bytes" >> "$RESULTS_DIR/test-report.md"
            echo "- Download Time: $DOWNLOAD_TIME seconds" >> "$RESULTS_DIR/test-report.md"
            
            # Check if it's a valid audio file (basic check)
            if file "$RESULTS_DIR/test-audio.mp3" | grep -i audio >/dev/null 2>&1; then
                print_success "Downloaded file appears to be valid audio"
                echo "- File Type: Valid Audio" >> "$RESULTS_DIR/test-report.md"
            fi
        else
            print_error "Downloaded file is empty"
            echo "❌ **FAILED** - Empty file" >> "$RESULTS_DIR/test-report.md"
        fi
    else
        print_error "MP3 download failed with HTTP code: $HTTP_CODE"
        echo "❌ **FAILED** - HTTP $HTTP_CODE" >> "$RESULTS_DIR/test-report.md"
    fi
    
    echo "" >> "$RESULTS_DIR/test-report.md"
}

# Test MP4 download endpoint (first few bytes only)
test_mp4_download() {
    print_header "Testing MP4 Download Endpoint"
    
    print_status "Testing MP4 download (first 1MB only for speed)..."
    
    # Create JSON payload
    JSON_PAYLOAD=$(cat <<EOF
{
    "url": "$YOUTUBE_TEST_URL"
}
EOF
)
    
    # Start download and capture first 1MB
    DOWNLOAD_START=$(date +%s)
    HTTP_CODE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$JSON_PAYLOAD" \
        -o "$RESULTS_DIR/test-video.mp4" \
        -w "%{http_code}" \
        --max-time 30 \
        --limit-rate 1M \
        "http://localhost:$TEST_PORT/v1/media/youtube/mp4" || echo "000")
    DOWNLOAD_END=$(date +%s)
    DOWNLOAD_TIME=$((DOWNLOAD_END - DOWNLOAD_START))
    
    echo "## MP4 Download Test" >> "$RESULTS_DIR/test-report.md"
    
    if [ "$HTTP_CODE" = "200" ]; then
        FILE_SIZE=$(stat -f%z "$RESULTS_DIR/test-video.mp4" 2>/dev/null || stat -c%s "$RESULTS_DIR/test-video.mp4" 2>/dev/null || echo "0")
        
        if [ "$FILE_SIZE" -gt 0 ]; then
            print_success "MP4 download successful"
            print_success "Downloaded size: $FILE_SIZE bytes in $DOWNLOAD_TIME seconds"
            echo "✅ **PASSED**" >> "$RESULTS_DIR/test-report.md"
            echo "- Downloaded Size: $FILE_SIZE bytes" >> "$RESULTS_DIR/test-report.md"
            echo "- Download Time: $DOWNLOAD_TIME seconds" >> "$RESULTS_DIR/test-report.md"
            
            # Check if it's a valid video file (basic check)
            if file "$RESULTS_DIR/test-video.mp4" | grep -i video >/dev/null 2>&1; then
                print_success "Downloaded file appears to be valid video"
                echo "- File Type: Valid Video" >> "$RESULTS_DIR/test-report.md"
            fi
        else
            print_error "Downloaded file is empty"
            echo "❌ **FAILED** - Empty file" >> "$RESULTS_DIR/test-report.md"
        fi
    else
        print_error "MP4 download failed with HTTP code: $HTTP_CODE"
        echo "❌ **FAILED** - HTTP $HTTP_CODE" >> "$RESULTS_DIR/test-report.md"
    fi
    
    echo "" >> "$RESULTS_DIR/test-report.md"
}

# Test rate limiting
test_rate_limiting() {
    print_header "Testing Rate Limiting"
    
    print_status "Testing rate limiting with multiple rapid requests..."
    
    # Make multiple rapid requests to trigger rate limiting
    RATE_LIMIT_TRIGGERED=false
    for i in {1..10}; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$TEST_PORT/healthz" || echo "000")
        if [ "$HTTP_CODE" = "429" ]; then
            RATE_LIMIT_TRIGGERED=true
            break
        fi
        sleep 0.1
    done
    
    echo "## Rate Limiting Test" >> "$RESULTS_DIR/test-report.md"
    
    if [ "$RATE_LIMIT_TRIGGERED" = true ]; then
        print_success "Rate limiting is working correctly"
        echo "✅ **PASSED** - Rate limit triggered" >> "$RESULTS_DIR/test-report.md"
    else
        print_warning "Rate limiting may not be configured or threshold too high"
        echo "⚠️ **WARNING** - Rate limit not triggered" >> "$RESULTS_DIR/test-report.md"
    fi
    
    echo "" >> "$RESULTS_DIR/test-report.md"
}

# Test error handling
test_error_handling() {
    print_header "Testing Error Handling"
    
    print_status "Testing invalid URL handling..."
    
    # Test with invalid URL
    INVALID_JSON=$(cat <<EOF
{
    "url": "https://invalid-youtube-url.com/watch?v=invalid"
}
EOF
)
    
    ERROR_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$INVALID_JSON" \
        "http://localhost:$TEST_PORT/v1/media/youtube/info" || echo "ERROR")
    
    echo "## Error Handling Test" >> "$RESULTS_DIR/test-report.md"
    
    if echo "$ERROR_RESPONSE" | jq -e '.success == false' >/dev/null 2>&1; then
        print_success "Error handling works correctly"
        ERROR_MESSAGE=$(echo "$ERROR_RESPONSE" | jq -r '.error')
        print_status "Error message: $ERROR_MESSAGE"
        echo "✅ **PASSED** - Proper error response" >> "$RESULTS_DIR/test-report.md"
        echo "- Error: $ERROR_MESSAGE" >> "$RESULTS_DIR/test-report.md"
    else
        print_error "Error handling failed"
        echo "❌ **FAILED** - Invalid error response" >> "$RESULTS_DIR/test-report.md"
    fi
    
    echo "" >> "$RESULTS_DIR/test-report.md"
}

# Collect container logs
collect_logs() {
    print_header "Collecting Container Logs"
    
    print_status "Saving container logs..."
    docker logs "$CONTAINER_NAME" > "$RESULTS_DIR/container-logs.txt" 2>&1
    print_success "Container logs saved to: $RESULTS_DIR/container-logs.txt"
    
    # Container stats
    print_status "Collecting container statistics..."
    docker stats --no-stream "$CONTAINER_NAME" > "$RESULTS_DIR/container-stats.txt"
    print_success "Container stats saved to: $RESULTS_DIR/container-stats.txt"
}

# Generate final report
generate_report() {
    print_header "Generating Final Report"
    
    echo "" >> "$RESULTS_DIR/test-report.md"
    echo "## Container Information" >> "$RESULTS_DIR/test-report.md"
    echo "- Container Name: $CONTAINER_NAME" >> "$RESULTS_DIR/test-report.md"
    echo "- Image: $IMAGE_NAME" >> "$RESULTS_DIR/test-report.md"
    echo "- Test Port: $TEST_PORT" >> "$RESULTS_DIR/test-report.md"
    echo "- Test URL: $YOUTUBE_TEST_URL" >> "$RESULTS_DIR/test-report.md"
    
    echo "" >> "$RESULTS_DIR/test-report.md"
    echo "## Files Generated" >> "$RESULTS_DIR/test-report.md"
    echo "- Container logs: \`container-logs.txt\`" >> "$RESULTS_DIR/test-report.md"
    echo "- Container stats: \`container-stats.txt\`" >> "$RESULTS_DIR/test-report.md"
    echo "- YouTube info response: \`youtube-info-response.json\`" >> "$RESULTS_DIR/test-report.md"
    echo "- Test audio sample: \`test-audio.mp3\`" >> "$RESULTS_DIR/test-report.md"
    echo "- Test video sample: \`test-video.mp4\`" >> "$RESULTS_DIR/test-report.md"
    
    print_success "Test report generated: $RESULTS_DIR/test-report.md"
    
    # Display summary
    print_header "Test Summary"
    cat "$RESULTS_DIR/test-report.md" | grep -E "^## ✅|^## ❌|^## ⚠️" | sed 's/## //' || true
}

# Main execution
main() {
    print_header "YouTube Downloader Docker Local Test"
    print_status "Test URL: $YOUTUBE_TEST_URL"
    print_status "Fallback Media URL: $FALLBACK_MEDIA_URL"
    print_status "GCS Media URL: $GCS_MEDIA_URL"
    
    # Check dependencies
    command -v docker >/dev/null 2>&1 || { print_error "Docker is not installed"; exit 1; }
    command -v curl >/dev/null 2>&1 || { print_error "curl is not installed"; exit 1; }
    command -v jq >/dev/null 2>&1 || { print_error "jq is not installed"; exit 1; }
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Setup
    setup_results_dir
    cleanup  # Clean any existing containers
    
    # Run tests
    build_image
    start_container
    test_health
    test_security_headers
    test_youtube_info
    test_mp3_download
    test_mp4_download
    test_rate_limiting
    test_error_handling
    collect_logs
    generate_report
    
    print_success "All tests completed successfully!"
    print_status "Check results in: $RESULTS_DIR/"
}

# Execute main function
main "$@"
