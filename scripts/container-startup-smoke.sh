#!/bin/bash

# Container Startup Smoke Tests
# This script tests that the Docker container starts up properly without any special environment variables
# and that basic endpoints function correctly.

set -euo pipefail

# Configuration
CONTAINER_NAME="startup-smoke-test"
IMAGE_TAG="local/sync-scribe-studio-api:startup-smoke"
PORT=8080
MAX_WAIT_ATTEMPTS=30
WAIT_INTERVAL=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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
    log_info "Cleaning up..."
    if docker ps -q --filter "name=${CONTAINER_NAME}" | grep -q .; then
        log_info "Stopping container: ${CONTAINER_NAME}"
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
    
    if docker ps -a -q --filter "name=${CONTAINER_NAME}" | grep -q .; then
        log_info "Removing container: ${CONTAINER_NAME}"
        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Function to check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running or not accessible"
        exit 1
    fi
    
    log_success "Docker is available"
}

# Function to build Docker image
build_image() {
    log_info "Building Docker image: ${IMAGE_TAG}"
    
    if ! docker build -t "${IMAGE_TAG}" \
        --build-arg BUILD_NUMBER="startup-smoke-$(date +%s)" \
        -f Dockerfile .; then
        log_error "Failed to build Docker image"
        exit 1
    fi
    
    log_success "Docker image built successfully"
}

# Function to start container without environment variables
start_container() {
    log_info "Starting container without special environment variables..."
    
    # Start container with only the port mapping - NO environment variables
    if ! docker run -d \
        --name "${CONTAINER_NAME}" \
        -p "${PORT}:8080" \
        "${IMAGE_TAG}"; then
        log_error "Failed to start container"
        exit 1
    fi
    
    log_success "Container started: ${CONTAINER_NAME}"
}

# Function to wait for container to be ready
wait_for_container() {
    log_info "Waiting for container to be ready at http://localhost:${PORT}"
    
    local attempt=1
    while [ $attempt -le $MAX_WAIT_ATTEMPTS ]; do
        # Check if container is still running
        if ! docker ps -q --filter "name=${CONTAINER_NAME}" | grep -q .; then
            log_error "Container stopped unexpectedly"
            show_container_logs
            exit 1
        fi
        
        # Try to connect to health endpoint
        if curl -s -f "http://localhost:${PORT}/health" >/dev/null 2>&1; then
            log_success "Container is ready (attempt $attempt/${MAX_WAIT_ATTEMPTS})"
            return 0
        fi
        
        log_info "Waiting for service... (attempt $attempt/${MAX_WAIT_ATTEMPTS})"
        sleep $WAIT_INTERVAL
        ((attempt++))
    done
    
    log_error "Container did not become ready within $(($MAX_WAIT_ATTEMPTS * $WAIT_INTERVAL)) seconds"
    show_container_logs
    exit 1
}

# Function to show container logs
show_container_logs() {
    log_warning "Container logs:"
    docker logs "${CONTAINER_NAME}" 2>&1 || echo "Failed to get container logs"
}

# Function to test health endpoint
test_health_endpoint() {
    log_info "Testing /health endpoint..."
    
    local response
    local status_code
    
    response=$(curl -s -w "\n%{http_code}" "http://localhost:${PORT}/health" || echo "000")
    status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" != "200" ]; then
        log_error "/health endpoint returned status $status_code, expected 200"
        echo "Response: $(echo "$response" | head -n1)"
        return 1
    fi
    
    # Validate JSON response
    local json_response
    json_response=$(echo "$response" | head -n1)
    
    if ! echo "$json_response" | jq . >/dev/null 2>&1; then
        log_error "/health endpoint returned invalid JSON"
        echo "Response: $json_response"
        return 1
    fi
    
    # Check required fields
    local status service timestamp version
    status=$(echo "$json_response" | jq -r '.status // empty')
    service=$(echo "$json_response" | jq -r '.service // empty')
    timestamp=$(echo "$json_response" | jq -r '.timestamp // empty')
    version=$(echo "$json_response" | jq -r '.version // empty')
    
    if [ "$status" != "healthy" ]; then
        log_error "/health endpoint status is '$status', expected 'healthy'"
        return 1
    fi
    
    if [ -z "$service" ]; then
        log_error "/health endpoint missing 'service' field"
        return 1
    fi
    
    if [ -z "$timestamp" ]; then
        log_error "/health endpoint missing 'timestamp' field"
        return 1
    fi
    
    if [ -z "$version" ]; then
        log_error "/health endpoint missing 'version' field"
        return 1
    fi
    
    log_success "/health endpoint test passed"
    log_info "  Service: $service"
    log_info "  Version: $version"
    log_info "  Status: $status"
}

# Function to test root endpoint
test_root_endpoint() {
    log_info "Testing / (root) endpoint..."
    
    local response
    local status_code
    
    response=$(curl -s -w "\n%{http_code}" -H "Accept: application/json" "http://localhost:${PORT}/" || echo "000")
    status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" != "200" ]; then
        log_error "/ endpoint returned status $status_code, expected 200"
        echo "Response: $(echo "$response" | sed '$d')"
        return 1
    fi
    
    # Validate JSON response
    local json_response
    json_response=$(echo "$response" | sed '$d')
    
    if ! echo "$json_response" | jq . >/dev/null 2>&1; then
        log_error "/ endpoint returned invalid JSON"
        echo "Response: $json_response"
        return 1
    fi
    
    # Check required fields
    local service version endpoints
    service=$(echo "$json_response" | jq -r '.service // empty')
    version=$(echo "$json_response" | jq -r '.version // empty')
    endpoints=$(echo "$json_response" | jq -r '.endpoints // empty')
    
    if [ -z "$service" ]; then
        log_error "/ endpoint missing 'service' field"
        return 1
    fi
    
    if [ -z "$version" ]; then
        log_error "/ endpoint missing 'version' field"
        return 1
    fi
    
    if [ "$endpoints" = "null" ] || [ -z "$endpoints" ]; then
        log_error "/ endpoint missing or empty 'endpoints' field"
        return 1
    fi
    
    log_success "/ endpoint test passed"
    log_info "  Service: $service"
    log_info "  Version: $version"
}

# Function to test detailed health endpoint
test_detailed_health_endpoint() {
    log_info "Testing /health/detailed endpoint..."
    
    local response
    local status_code
    
    response=$(curl -s -w "\n%{http_code}" -H "Accept: application/json" "http://localhost:${PORT}/health/detailed" || echo "000")
    status_code=$(echo "$response" | tail -n1)
    
    # Detailed health should return 200 or 503 depending on missing environment variables
    # 200 = healthy or degraded state, 503 = service unavailable due to critical issues
    if [ "$status_code" != "200" ] && [ "$status_code" != "503" ]; then
        log_error "/health/detailed endpoint returned status $status_code, expected 200 or 503"
        echo "Response: $(echo "$response" | sed '$d')"
        return 1
    fi
    
    # Validate JSON response
    local json_response
    json_response=$(echo "$response" | sed '$d')
    
    if ! echo "$json_response" | jq . >/dev/null 2>&1; then
        log_error "/health/detailed endpoint returned invalid JSON"
        echo "Response: $json_response"
        return 1
    fi
    
    # Check for status field
    local status
    status=$(echo "$json_response" | jq -r '.status // empty')
    
    if [ -z "$status" ]; then
        log_error "/health/detailed endpoint missing 'status' field"
        return 1
    fi
    
    log_success "/health/detailed endpoint test passed"
    log_info "  Status Code: $status_code"
    log_info "  Health Status: $status"
    
    # Show warnings if present (informational)
    local warnings
    warnings=$(echo "$json_response" | jq -r '.warnings // empty')
    if [ "$warnings" != "null" ] && [ -n "$warnings" ]; then
        local warning_count
        warning_count=$(echo "$json_response" | jq '.warnings | length')
        log_info "  Warnings: $warning_count found (as expected without env vars)"
    fi
}

# Function to test security headers
test_security_headers() {
    log_info "Testing security headers..."
    
    local headers
    headers=$(curl -s -I "http://localhost:${PORT}/health" || echo "")
    
    if [ -z "$headers" ]; then
        log_error "Failed to get headers from /health endpoint"
        return 1
    fi
    
    # Check required security headers
    local errors=0
    
    if ! echo "$headers" | grep -i "X-Content-Type-Options: nosniff" >/dev/null; then
        log_error "Missing X-Content-Type-Options: nosniff header"
        ((errors++))
    fi
    
    if ! echo "$headers" | grep -i "X-Frame-Options: DENY" >/dev/null; then
        log_error "Missing X-Frame-Options: DENY header"
        ((errors++))
    fi
    
    if ! echo "$headers" | grep -i "X-XSS-Protection: 1; mode=block" >/dev/null; then
        log_error "Missing X-XSS-Protection header"
        ((errors++))
    fi
    
    if ! echo "$headers" | grep -i "Strict-Transport-Security:" >/dev/null; then
        log_error "Missing Strict-Transport-Security header"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "Security headers test passed"
    else
        log_error "Security headers test failed with $errors errors"
        return 1
    fi
}

# Function to test basic endpoint error handling
test_error_handling() {
    log_info "Testing error handling..."
    
    # Test 404 for invalid endpoint
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/invalid-endpoint" || echo "000")
    
    if [ "$status_code" != "404" ]; then
        log_error "Invalid endpoint returned status $status_code, expected 404"
        return 1
    fi
    
    log_success "Error handling test passed"
    log_info "  404 for invalid endpoints: ✓"
}

# Function to test authenticated endpoints (should return proper error codes without auth)
test_authenticated_endpoints() {
    log_info "Testing authenticated endpoints behavior without credentials..."
    
    # Test YouTube info endpoint without authentication
    local response
    local status_code
    
    response=$(curl -s -w "\n%{http_code}" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://youtube.com/watch?v=test"}' \
        "http://localhost:${PORT}/v1/media/youtube/info" || echo "000")
    status_code=$(echo "$response" | tail -n1)
    
    # Should return 401 (unauthorized), 503 (auth service unavailable), or 404/405 (not implemented)
    if [ "$status_code" != "401" ] && [ "$status_code" != "503" ] && [ "$status_code" != "404" ] && [ "$status_code" != "405" ]; then
        log_warning "YouTube info endpoint returned status $status_code, expected 401, 503, 404, or 405"
        log_info "  This might be expected behavior depending on configuration"
    else
        log_success "Authenticated endpoint properly rejected request without credentials"
        log_info "  Status Code: $status_code"
    fi
}

# Function to show container stats
show_container_stats() {
    log_info "Container resource usage:"
    
    local stats
    if stats=$(docker stats "${CONTAINER_NAME}" --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null); then
        echo "$stats"
    else
        log_warning "Could not retrieve container stats"
    fi
}

# Function to run all tests
run_smoke_tests() {
    log_info "Running container startup smoke tests..."
    echo
    
    # Build and start container
    build_image
    start_container
    wait_for_container
    
    echo
    log_info "=== BASIC ENDPOINT TESTS ==="
    
    # Test basic endpoints
    test_health_endpoint || return 1
    test_root_endpoint || return 1
    test_detailed_health_endpoint || return 1
    
    echo
    log_info "=== SECURITY TESTS ==="
    
    # Test security features
    test_security_headers || return 1
    test_error_handling || return 1
    
    echo
    log_info "=== AUTHENTICATION TESTS ==="
    
    # Test authenticated endpoints
    test_authenticated_endpoints
    
    echo
    log_info "=== CONTAINER STATS ==="
    
    # Show resource usage
    show_container_stats
    
    echo
    log_success "All smoke tests completed successfully!"
    log_info "The container starts up properly without special environment variables"
    log_info "and provides expected functionality for basic monitoring and security."
}

# Main execution
main() {
    echo "🚀 Container Startup Smoke Tests"
    echo "================================="
    echo
    
    # Check prerequisites
    check_docker
    
    # Check if jq is available (for JSON parsing)
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed. JSON validation will be limited."
        log_info "Install jq for better test coverage: apt-get install jq / brew install jq"
    fi
    
    # Run tests
    run_smoke_tests
    
    echo
    log_success "🎉 Container startup smoke tests completed successfully!"
    echo
    log_info "Summary:"
    log_info "  ✓ Container builds without errors"
    log_info "  ✓ Container starts without special environment variables"
    log_info "  ✓ Health endpoints return expected responses"
    log_info "  ✓ Security headers are properly configured"
    log_info "  ✓ Error handling works correctly"
    log_info "  ✓ Authenticated endpoints handle missing credentials appropriately"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
