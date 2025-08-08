#!/usr/bin/env python3
"""
Simple Flask test application for Cloud Run validation
This app demonstrates all the key Cloud Run compatibility features
"""

from flask import Flask, jsonify, request
import os
import time
import signal
import sys
from version import BUILD_NUMBER

app = Flask(__name__)

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(sig, frame):
    """Handle SIGTERM signal for graceful shutdown"""
    global shutdown_flag
    print(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_flag = True
    # Give the application a moment to finish current requests
    time.sleep(1)
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGTERM, signal_handler)

@app.route('/')
def root():
    """Root endpoint with service information"""
    port = os.getenv('PORT', '8080')
    workers = os.getenv('GUNICORN_WORKERS', '2')
    
    return jsonify({
        "service": "Sync Scribe Studio API - Cloud Run Test",
        "version": f"{BUILD_NUMBER // 100}.{(BUILD_NUMBER % 100) // 10}.{BUILD_NUMBER % 10}",
        "build_number": BUILD_NUMBER,
        "status": "running",
        "port": port,
        "workers": workers,
        "endpoints": {
            "health": "/health",
            "detailed_health": "/health/detailed",
            "info": "/"
        },
        "cloud_run_ready": True,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    })

@app.route('/health')
def health():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "version": f"{BUILD_NUMBER // 100}.{(BUILD_NUMBER % 100) // 10}.{BUILD_NUMBER % 10}",
        "build_number": BUILD_NUMBER,
        "service": "Sync Scribe Studio API"
    })

@app.route('/health/detailed')
def detailed_health():
    """Detailed health check with environment info"""
    env_vars = {
        "PORT": os.getenv('PORT', '8080'),
        "WORKERS": os.getenv('GUNICORN_WORKERS', '2'),
        "TIMEOUT": os.getenv('GUNICORN_TIMEOUT', '300'),
        "PYTHONUNBUFFERED": os.getenv('PYTHONUNBUFFERED', 'not_set'),
        "BUILD_NUMBER": str(BUILD_NUMBER)
    }
    
    # Check for common missing environment variables
    missing_vars = []
    warnings = []
    
    if not os.getenv('API_KEY'):
        warnings.append("API_KEY not set - authentication may not work")
    
    if not os.getenv('DB_TOKEN'):
        warnings.append("DB_TOKEN not set - security authentication unavailable")
    
    if not os.getenv('OPENAI_API_KEY'):
        warnings.append("OPENAI_API_KEY not set - AI features may not work")
    
    return jsonify({
        "status": "healthy",
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "version": f"{BUILD_NUMBER // 100}.{(BUILD_NUMBER % 100) // 10}.{BUILD_NUMBER % 10}",
        "build_number": BUILD_NUMBER,
        "service": "Sync Scribe Studio API",
        "environment_variables": env_vars,
        "dependencies": {
            "missing_vars": missing_vars,
            "warnings": warnings
        },
        "system_info": {
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "process_id": os.getpid()
        },
        "cloud_run_features": {
            "port_binding": f"0.0.0.0:{env_vars['PORT']}",
            "graceful_shutdown": "SIGTERM handler registered",
            "health_checks": "implemented",
            "logging": "stdout/stderr"
        }
    })

@app.route('/test')
def test():
    """Test endpoint for API functionality"""
    # Simulate some processing time
    processing_time = 0.1
    time.sleep(processing_time)
    
    return jsonify({
        "message": "API test successful",
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "processing_time": processing_time,
        "build_number": BUILD_NUMBER,
        "cloud_run_compatible": True
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": ["/", "/health", "/health/detailed", "/test"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }), 500

if __name__ == '__main__':
    # This will only run when called directly, not via gunicorn
    port = int(os.getenv('PORT', 8080))
    print(f"Starting Sync Scribe Studio API test server on port {port}")
    print(f"Build Number: {BUILD_NUMBER}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
