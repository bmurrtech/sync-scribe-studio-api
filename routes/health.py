# Copyright (c) 2025 Stephen G. Pope
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import time
import socket
from flask import Blueprint, jsonify
from version import BUILD_NUMBER

# Health check blueprint
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    """
    Basic health endpoint for Cloud Run
    Returns service status, timestamp, and version
    """
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": BUILD_NUMBER,
        "service": "Sync Scribe Studio API",
        "port": os.environ.get('PORT', '8080')
    }), 200

@health_bp.route('/health/detailed', methods=['GET'])
def health_detailed():
    """
    Detailed health endpoint reporting environment variables, 
    service status, and missing dependencies warnings.
    Never returns an error status - always returns 200 with detailed info.
    """
    # Check environment variables presence
    env_status = {}
    required_env_vars = [
        'PORT',
        'PYTHONUNBUFFERED', 
        'BUILD_NUMBER',
        'WHISPER_CACHE_DIR'
    ]
    
    optional_env_vars = [
        'YOUTUBE_SERVICE_URL',
        'GUNICORN_WORKERS',
        'GUNICORN_TIMEOUT',
        'MAX_QUEUE_LENGTH'
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_env_vars:
        value = os.environ.get(var)
        if value:
            env_status[var] = "present"
        else:
            env_status[var] = "missing (required)"
            missing_required.append(var)
    
    for var in optional_env_vars:
        value = os.environ.get(var)
        if value:
            env_status[var] = "present"
        else:
            env_status[var] = "missing (optional)"
            missing_optional.append(var)
    
    # Check service dependencies
    warnings = []
    
    # Check if FFmpeg is available
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        ffmpeg_status = "available" if result.returncode == 0 else "error"
        if result.returncode != 0:
            warnings.append("FFmpeg not working properly")
    except Exception:
        ffmpeg_status = "unavailable"
        warnings.append("FFmpeg not found - media processing may be limited")
    
    # Check if Whisper cache directory exists and is writable
    whisper_cache = os.environ.get('WHISPER_CACHE_DIR', '/tmp/whisper_cache')
    try:
        if os.path.exists(whisper_cache) and os.access(whisper_cache, os.W_OK):
            whisper_cache_status = "writable"
        else:
            whisper_cache_status = "not_writable"
            warnings.append("Whisper cache directory not writable - performance may be affected")
    except Exception:
        whisper_cache_status = "error"
        warnings.append("Cannot check Whisper cache directory")
    
    # Check disk space (for tmpfs)
    try:
        import shutil
        total, used, free = shutil.disk_usage('/tmp')
        tmp_space_gb = free / (1024**3)  # Convert to GB
        if tmp_space_gb < 1:
            warnings.append(f"Low tmp disk space: {tmp_space_gb:.1f}GB remaining")
        tmp_space_status = f"{tmp_space_gb:.1f}GB_free"
    except Exception:
        tmp_space_status = "unknown"
        warnings.append("Cannot check /tmp disk space")
    
    # Add informational messages for missing environment variables
    if missing_required:
        warnings.extend([f"Missing required env var: {var} - some features may not work" for var in missing_required])
    
    if missing_optional:
        warnings.extend([f"Missing optional env var: {var} - default behavior will be used" for var in missing_optional])
    
    # Determine overall service status based on critical issues only
    service_status = "healthy"
    if missing_required or ffmpeg_status == "unavailable":
        service_status = "degraded"
    
    return jsonify({
        "status": service_status,
        "timestamp": int(time.time()),
        "version": BUILD_NUMBER,
        "service": "Sync Scribe Studio API",
        "port": os.environ.get('PORT', '8080'),
        "hostname": socket.gethostname(),
        "environment_variables": env_status,
        "service_checks": {
            "ffmpeg": ffmpeg_status,
            "whisper_cache": whisper_cache_status,
            "tmp_disk_space": tmp_space_status
        },
        "warnings": warnings,
        "missing_dependencies": {
            "required": missing_required,
            "optional": missing_optional
        }
    }), 200

@health_bp.route('/', methods=['GET'])
def root():
    """
    Root endpoint with service info, key endpoints, and documentation link
    """
    return jsonify({
        "service": "Sync Scribe Studio API",
        "version": BUILD_NUMBER,
        "description": "Multi-media processing API with FFmpeg, Whisper, and YouTube integration",
        "status": "running",
        "endpoints": {
            "/": "Service information",
            "/health": "Basic health check", 
            "/health/detailed": "Detailed health check with diagnostics",
            "/v1/media/transcribe": "Audio/video transcription",
            "/v1/media/convert": "Media format conversion",
            "/v1/media/youtube": "YouTube integration services",
            "/v1/video/caption": "Video captioning",
            "/v1/image/convert": "Image processing"
        },
        "documentation": "https://github.com/your-repo/sync-scribe-studio-api",
        "build_info": {
            "build_number": BUILD_NUMBER,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "container_user": os.environ.get('USER', 'appuser'),
            "working_directory": os.getcwd()
        }
    }), 200
