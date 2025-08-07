#!/bin/sh
set -e

# YouTube Downloader Service Entrypoint Script
# Validates environment and starts the service with proper configuration

echo "=== YouTube Downloader Service Starting ==="
echo "Node.js Version: $(node --version)"
echo "Environment: ${NODE_ENV:-development}"
echo "Port: ${PORT:-3001}"
echo "YTDL Network Timeout: ${YTDL_NETWORK_TIMEOUT:-30000}ms"

# Environment validation
validate_env() {
    echo "Validating environment variables..."
    
    # Validate PORT
    if [ ! -z "$PORT" ]; then
        if ! echo "$PORT" | grep -Eq '^[0-9]+$' || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
            echo "ERROR: Invalid PORT value: $PORT (must be 1-65535)"
            exit 1
        fi
    fi
    
    # Validate YTDL_NETWORK_TIMEOUT
    if [ ! -z "$YTDL_NETWORK_TIMEOUT" ]; then
        if ! echo "$YTDL_NETWORK_TIMEOUT" | grep -Eq '^[0-9]+$' || [ "$YTDL_NETWORK_TIMEOUT" -lt 1000 ]; then
            echo "ERROR: Invalid YTDL_NETWORK_TIMEOUT value: $YTDL_NETWORK_TIMEOUT (must be >= 1000ms)"
            exit 1
        fi
    fi
    
    # Validate NODE_ENV
    if [ ! -z "$NODE_ENV" ]; then
        case "$NODE_ENV" in
            "production"|"development"|"test"|"staging")
                ;;
            *)
                echo "WARNING: Unrecognized NODE_ENV value: $NODE_ENV"
                ;;
        esac
    fi
    
    echo "Environment validation passed ✓"
}

# Check required directories
setup_directories() {
    echo "Setting up directories..."
    
    # Ensure logs directory exists with proper permissions
    if [ ! -d "/app/logs" ]; then
        mkdir -p /app/logs
        echo "Created logs directory"
    fi
    
    # Verify write permissions
    if [ ! -w "/app/logs" ]; then
        echo "ERROR: Cannot write to logs directory"
        exit 1
    fi
    
    echo "Directories setup complete ✓"
}

# Network connectivity check (optional)
check_network() {
    if [ "${SKIP_NETWORK_CHECK:-false}" = "false" ]; then
        echo "Testing network connectivity..."
        
        # Test DNS resolution
        if ! nslookup google.com > /dev/null 2>&1; then
            echo "WARNING: DNS resolution test failed - YouTube downloads may not work"
        else
            echo "Network connectivity test passed ✓"
        fi
    else
        echo "Network check skipped (SKIP_NETWORK_CHECK=true)"
    fi
}

# Health check function
wait_for_startup() {
    echo "Waiting for service to be ready..."
    PORT_TO_CHECK=${PORT:-3001}
    TIMEOUT=${STARTUP_TIMEOUT:-30}
    
    # Start service in background for startup check
    node server.js &
    SERVICE_PID=$!
    
    # Wait for service to respond
    for i in $(seq 1 $TIMEOUT); do
        if wget --quiet --timeout=2 --tries=1 --spider "http://localhost:$PORT_TO_CHECK/healthz" 2>/dev/null; then
            echo "Service is ready after ${i} seconds ✓"
            # Kill background process
            kill $SERVICE_PID 2>/dev/null || true
            wait $SERVICE_PID 2>/dev/null || true
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo ""
    echo "ERROR: Service failed to start within $TIMEOUT seconds"
    # Kill background process
    kill $SERVICE_PID 2>/dev/null || true
    wait $SERVICE_PID 2>/dev/null || true
    exit 1
}

# Signal handlers for graceful shutdown
cleanup() {
    echo ""
    echo "=== Shutting down YouTube Downloader Service ==="
    if [ ! -z "$SERVICE_PID" ]; then
        echo "Terminating service process $SERVICE_PID..."
        kill -TERM $SERVICE_PID 2>/dev/null || true
        wait $SERVICE_PID 2>/dev/null || true
    fi
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup TERM INT

# Main execution
main() {
    echo "Starting validation and setup..."
    validate_env
    setup_directories
    check_network
    
    # Quick startup validation in development
    if [ "${NODE_ENV}" = "development" ] || [ "${STARTUP_HEALTH_CHECK:-false}" = "true" ]; then
        wait_for_startup
    fi
    
    echo "=== Starting YouTube Downloader Service ==="
    echo "Service starting on port ${PORT:-3001}..."
    echo "Process ID: $$"
    echo "Timestamp: $(date)"
    echo ""
    
    # Execute the main application
    exec node server.js
}

# Run main function
main
