#!/bin/bash

# Cloud Run Compatible Entrypoint Script
# Respects the $PORT environment variable set by Cloud Run

set -e

# Set default port if not provided
PORT=${PORT:-8080}

echo "Starting Sync Scribe Studio API on port $PORT"
echo "Build Number: ${BUILD_NUMBER:-unknown}"
echo "Workers: ${GUNICORN_WORKERS:-2}"
echo "Timeout: ${GUNICORN_TIMEOUT:-300}"

# Start Gunicorn with Cloud Run optimized settings
# Use simple_test_app for validation, fallback to app if available
if [ -f "simple_test_app.py" ]; then
    echo "Using simple_test_app for Cloud Run validation"
    exec gunicorn \
        --bind 0.0.0.0:$PORT \
        --workers ${GUNICORN_WORKERS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-300} \
        --worker-class sync \
        --keep-alive 80 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        --capture-output \
        --enable-stdio-inheritance \
        simple_test_app:app
else
    echo "Using main app.py"
    exec gunicorn \
        --bind 0.0.0.0:$PORT \
        --workers ${GUNICORN_WORKERS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-300} \
        --worker-class sync \
        --keep-alive 80 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        --capture-output \
        --enable-stdio-inheritance \
        app:app
fi
