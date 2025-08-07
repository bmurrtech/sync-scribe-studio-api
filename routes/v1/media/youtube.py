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

import requests
import os
import logging
from flask import Blueprint, request, jsonify, Response
from app_utils import validate_payload, queue_task_wrapper
from services.authentication import authenticate
from urllib.parse import urljoin
import time

# YouTube microservice integration blueprint
v1_media_youtube_bp = Blueprint('v1_media_youtube', __name__)
logger = logging.getLogger(__name__)

# YouTube microservice configuration
YOUTUBE_SERVICE_URL = os.environ.get('YOUTUBE_SERVICE_URL', 'http://localhost:3001')
YOUTUBE_SERVICE_TIMEOUT = int(os.environ.get('YOUTUBE_SERVICE_TIMEOUT', '30'))
YOUTUBE_RETRY_ATTEMPTS = int(os.environ.get('YOUTUBE_RETRY_ATTEMPTS', '3'))
YOUTUBE_RETRY_DELAY = int(os.environ.get('YOUTUBE_RETRY_DELAY', '1'))

def make_youtube_request(endpoint, data=None, method='POST', stream=False):
    """
    Make HTTP request to YouTube microservice with retry logic
    
    Args:
        endpoint (str): The endpoint path (e.g., '/v1/media/youtube/info')
        data (dict): Request data (for POST requests)
        method (str): HTTP method ('GET', 'POST')
        stream (bool): Whether to stream the response
        
    Returns:
        requests.Response: The response from the microservice
        
    Raises:
        requests.RequestException: If all retry attempts fail
    """
    url = urljoin(YOUTUBE_SERVICE_URL, endpoint)
    
    for attempt in range(YOUTUBE_RETRY_ATTEMPTS):
        try:
            logger.info(f"Attempt {attempt + 1}/{YOUTUBE_RETRY_ATTEMPTS}: {method} {url}")
            
            if method.upper() == 'GET':
                response = requests.get(
                    url,
                    timeout=YOUTUBE_SERVICE_TIMEOUT,
                    stream=stream,
                    headers={'User-Agent': 'Sync-Scribe-Studio-API/1.0'}
                )
            else:  # POST
                response = requests.post(
                    url,
                    json=data,
                    timeout=YOUTUBE_SERVICE_TIMEOUT,
                    stream=stream,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'Sync-Scribe-Studio-API/1.0'
                    }
                )
            
            # Check if the request was successful
            if response.status_code < 500:  # Don't retry on client errors (4xx)
                return response
                
            logger.warning(f"YouTube service returned {response.status_code}, retrying...")
            
        except requests.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}/{YOUTUBE_RETRY_ATTEMPTS}")
        except requests.ConnectionError:
            logger.warning(f"Connection error on attempt {attempt + 1}/{YOUTUBE_RETRY_ATTEMPTS}")
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}/{YOUTUBE_RETRY_ATTEMPTS}: {str(e)}")
        
        if attempt < YOUTUBE_RETRY_ATTEMPTS - 1:
            time.sleep(YOUTUBE_RETRY_DELAY)
    
    # All attempts failed
    raise requests.RequestException(f"YouTube microservice unavailable after {YOUTUBE_RETRY_ATTEMPTS} attempts")

def is_youtube_service_healthy():
    """Check if YouTube microservice is healthy"""
    try:
        response = make_youtube_request('/healthz', method='GET')
        return response.status_code == 200
    except:
        return False

# Health check endpoint for YouTube microservice
@v1_media_youtube_bp.route('/v1/media/youtube/health', methods=['GET'])
@authenticate
def youtube_health():
    """Check YouTube microservice health"""
    try:
        response = make_youtube_request('/healthz', method='GET')
        if response.status_code == 200:
            service_info = response.json()
            return jsonify({
                "status": "healthy",
                "microservice": service_info,
                "url": YOUTUBE_SERVICE_URL,
                "timeout": YOUTUBE_SERVICE_TIMEOUT
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "error": f"Service returned {response.status_code}",
                "url": YOUTUBE_SERVICE_URL
            }), 503
    except Exception as e:
        logger.error(f"YouTube health check failed: {str(e)}")
        return jsonify({
            "status": "unavailable",
            "error": str(e),
            "url": YOUTUBE_SERVICE_URL
        }), 503

# YouTube video information endpoint
@v1_media_youtube_bp.route('/v1/media/youtube/info', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "url": {"type": "string", "format": "uri"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def youtube_info(job_id, data):
    """Get YouTube video information via microservice"""
    
    if not is_youtube_service_healthy():
        logger.error(f"Job {job_id}: YouTube microservice is unhealthy")
        return "YouTube service is currently unavailable", "/v1/media/youtube/info", 503
    
    try:
        logger.info(f"Job {job_id}: Fetching YouTube video info for: {data.get('url')}")
        
        # Prepare request data for microservice
        microservice_data = {"url": data["url"]}
        
        # Make request to YouTube microservice
        response = make_youtube_request('/v1/media/youtube/info', microservice_data)
        
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Job {job_id}: Successfully fetched video info")
            return response_data, "/v1/media/youtube/info", 200
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"error": response.text}
            logger.error(f"Job {job_id}: Microservice error {response.status_code}: {error_data}")
            return error_data, "/v1/media/youtube/info", response.status_code
            
    except requests.RequestException as e:
        logger.error(f"Job {job_id}: YouTube microservice request failed: {str(e)}")
        return f"YouTube service unavailable: {str(e)}", "/v1/media/youtube/info", 503
    except Exception as e:
        logger.error(f"Job {job_id}: Unexpected error: {str(e)}")
        return f"Internal error: {str(e)}", "/v1/media/youtube/info", 500

# YouTube MP3 download endpoint
@v1_media_youtube_bp.route('/v1/media/youtube/mp3', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "url": {"type": "string", "format": "uri"},
        "quality": {"type": "string", "default": "highestaudio"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["url"],
    "additionalProperties": False
})
def youtube_mp3():
    """Download YouTube video as MP3 via microservice (streaming response)"""
    
    if not is_youtube_service_healthy():
        logger.error("YouTube microservice is unhealthy")
        return jsonify({"error": "YouTube service is currently unavailable"}), 503
    
    try:
        data = request.get_json()
        logger.info(f"Streaming MP3 download for: {data.get('url')}")
        
        # Prepare request data for microservice
        microservice_data = {
            "url": data["url"],
            "quality": data.get("quality", "highestaudio")
        }
        
        # Make streaming request to YouTube microservice
        response = make_youtube_request('/v1/media/youtube/mp3', microservice_data, stream=True)
        
        if response.status_code == 200:
            # Stream the audio data from microservice to client
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # Copy headers from microservice response
            headers = {}
            for key, value in response.headers.items():
                if key.lower() in ['content-type', 'content-disposition', 'x-video-title', 'x-video-duration']:
                    headers[key] = value
            
            logger.info("Successfully started MP3 streaming")
            return Response(generate(), headers=headers)
            
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"error": response.text}
            logger.error(f"Microservice error {response.status_code}: {error_data}")
            return jsonify(error_data), response.status_code
            
    except requests.RequestException as e:
        logger.error(f"YouTube microservice request failed: {str(e)}")
        return jsonify({"error": f"YouTube service unavailable: {str(e)}"}), 503
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

# YouTube MP4 download endpoint
@v1_media_youtube_bp.route('/v1/media/youtube/mp4', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "url": {"type": "string", "format": "uri"},
        "quality": {"type": "string", "default": "highest"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["url"],
    "additionalProperties": False
})
def youtube_mp4():
    """Download YouTube video as MP4 via microservice (streaming response)"""
    
    if not is_youtube_service_healthy():
        logger.error("YouTube microservice is unhealthy")
        return jsonify({"error": "YouTube service is currently unavailable"}), 503
    
    try:
        data = request.get_json()
        logger.info(f"Streaming MP4 download for: {data.get('url')}")
        
        # Prepare request data for microservice
        microservice_data = {
            "url": data["url"],
            "quality": data.get("quality", "highest")
        }
        
        # Make streaming request to YouTube microservice
        response = make_youtube_request('/v1/media/youtube/mp4', microservice_data, stream=True)
        
        if response.status_code == 200:
            # Stream the video data from microservice to client
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # Copy headers from microservice response
            headers = {}
            for key, value in response.headers.items():
                if key.lower() in ['content-type', 'content-disposition', 'x-video-title', 'x-video-duration']:
                    headers[key] = value
            
            logger.info("Successfully started MP4 streaming")
            return Response(generate(), headers=headers)
            
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"error": response.text}
            logger.error(f"Microservice error {response.status_code}: {error_data}")
            return jsonify(error_data), response.status_code
            
    except requests.RequestException as e:
        logger.error(f"YouTube microservice request failed: {str(e)}")
        return jsonify({"error": f"YouTube service unavailable: {str(e)}"}), 503
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

# YouTube service discovery endpoint
@v1_media_youtube_bp.route('/v1/media/youtube', methods=['GET'])
@authenticate
def youtube_service_info():
    """Get YouTube microservice information and available endpoints"""
    try:
        # Try to get service info from microservice
        service_healthy = is_youtube_service_healthy()
        service_info = {}
        
        if service_healthy:
            response = make_youtube_request('/', method='GET')
            if response.status_code == 200:
                service_info = response.json()
        
        return jsonify({
            "service": "YouTube Integration",
            "version": "1.0.0",
            "microservice_url": YOUTUBE_SERVICE_URL,
            "microservice_healthy": service_healthy,
            "microservice_info": service_info,
            "endpoints": {
                "/v1/media/youtube": "GET - Service information",
                "/v1/media/youtube/health": "GET - Health check",
                "/v1/media/youtube/info": "POST - Get video information",
                "/v1/media/youtube/mp3": "POST - Download audio as MP3 (streaming)",
                "/v1/media/youtube/mp4": "POST - Download video as MP4 (streaming)"
            },
            "configuration": {
                "timeout": YOUTUBE_SERVICE_TIMEOUT,
                "retry_attempts": YOUTUBE_RETRY_ATTEMPTS,
                "retry_delay": YOUTUBE_RETRY_DELAY
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting service info: {str(e)}")
        return jsonify({
            "service": "YouTube Integration",
            "version": "1.0.0",
            "microservice_url": YOUTUBE_SERVICE_URL,
            "microservice_healthy": False,
            "error": str(e)
        }), 500
