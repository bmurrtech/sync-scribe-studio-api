# Adding New Routes

This document explains how to add new routes to the application using the dynamic route registration system.

## Overview

The application now uses a dynamic route registration system that automatically discovers and registers all Flask blueprints in the `routes` directory. This means you no longer need to manually import and register blueprints in `app.py`.

## How to Add a New Route

1. **Create a new route file**

   Create a new Python file in the appropriate location in the `routes` directory. For a v1 API endpoint, you would typically place it in a subdirectory under `routes/v1/` based on the functionality.

   For example:
   ```
   routes/v1/email/send_email.py
   ```

2. **Define your Blueprint**

   In your route file, define a Flask Blueprint with a unique name. Make sure to follow the naming convention:
   
   ```python
   # routes/v1/email/send_email.py
   from flask import Blueprint, request
   from services.authentication import authenticate
   from app_utils import queue_task_wrapper

   v1_email_send_bp = Blueprint('v1_email_send', __name__)

   @v1_email_send_bp.route('/v1/email/send', methods=['POST'])
   @authenticate
   @queue_task_wrapper(bypass_queue=False)
   def send_email(job_id, data):
       """
       Send an email
       
       Args:
           job_id (str): Job ID assigned by queue_task_wrapper
           data (dict): Request data containing email details
       
       Returns:
           Tuple of (response_data, endpoint_string, status_code)
       """
       # Your implementation here
       endpoint = "/v1/email/send"
       
       # Return response
       return {"message": "Email sent"}, endpoint, 200
   ```

3. **That's it!**

   No need to modify `app.py`. The blueprint will be automatically discovered and registered when the application starts.

## Naming Conventions

When creating new routes, please follow these naming conventions:

1. **Blueprint names**: Use the format `{version}_{category}_{action}_bp`
   - Example: `v1_email_send_bp` for sending emails

2. **Route paths**: Use the format `/{version}/{category}/{action}`
   - Example: `/v1/email/send`

3. **File structure**: Place files in directories that match the route structure
   - Example: `routes/v1/email/send_email.py`

## Testing Your Route

After adding your route, restart the application and your new endpoint should be available immediately.

## Advanced Route Examples

### Example: YouTube Integration Route
```python
# routes/v1/media/youtube_info.py
from flask import Blueprint, request
from services.authentication import authenticate
from app_utils import queue_task_wrapper, validate_payload
import requests
import os

v1_media_youtube_info_bp = Blueprint('v1_media_youtube_info', __name__)

@v1_media_youtube_info_bp.route('/v1/media/youtube/info', methods=['POST'])
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
    """
    Get YouTube video information via microservice
    
    Args:
        job_id (str): Job ID assigned by queue_task_wrapper
        data (dict): Request data containing YouTube URL
    
    Returns:
        Tuple of (response_data, endpoint_string, status_code)
    """
    endpoint = "/v1/media/youtube/info"
    
    try:
        # Make request to microservice
        microservice_url = os.environ.get('YOUTUBE_SERVICE_URL', 'http://localhost:3001')
        response = requests.post(
            f"{microservice_url}/v1/media/youtube/info",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json(), endpoint, 200
        else:
            return f"Microservice error: {response.status_code}", endpoint, response.status_code
            
    except requests.RequestException as e:
        return f"Service unavailable: {str(e)}", endpoint, 503
```

### Example: Streaming Route
```python
# routes/v1/media/youtube_download.py
from flask import Blueprint, request, Response
from services.authentication import authenticate
from app_utils import validate_payload
import requests
import os

v1_media_youtube_download_bp = Blueprint('v1_media_youtube_download', __name__)

@v1_media_youtube_download_bp.route('/v1/media/youtube/mp3', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "url": {"type": "string", "format": "uri"},
        "quality": {"type": "string", "default": "highestaudio"}
    },
    "required": ["url"]
})
def youtube_mp3():
    """
    Stream YouTube audio as MP3 via microservice
    
    Returns:
        Streaming response with audio data
    """
    data = request.get_json()
    
    try:
        microservice_url = os.environ.get('YOUTUBE_SERVICE_URL', 'http://localhost:3001')
        response = requests.post(
            f"{microservice_url}/v1/media/youtube/mp3",
            json=data,
            stream=True,  # Enable streaming
            timeout=30
        )
        
        if response.status_code == 200:
            # Stream the response
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # Copy headers from microservice
            headers = {}
            for key, value in response.headers.items():
                if key.lower() in ['content-type', 'content-disposition']:
                    headers[key] = value
            
            return Response(generate(), headers=headers)
        else:
            return {"error": f"Download failed: {response.status_code}"}, response.status_code
            
    except requests.RequestException as e:
        return {"error": f"Service unavailable: {str(e)}"}, 503
```

### Example: Health Check Route
```python
# routes/v1/health/youtube_health.py
from flask import Blueprint, jsonify
from services.authentication import authenticate
import requests
import os

v1_health_youtube_bp = Blueprint('v1_health_youtube', __name__)

@v1_health_youtube_bp.route('/v1/health/youtube', methods=['GET'])
@authenticate
def youtube_health():
    """
    Check YouTube microservice health
    
    Returns:
        JSON response with health status
    """
    try:
        microservice_url = os.environ.get('YOUTUBE_SERVICE_URL', 'http://localhost:3001')
        response = requests.get(f"{microservice_url}/healthz", timeout=5)
        
        if response.status_code == 200:
            return jsonify({
                "status": "healthy",
                "microservice": response.json(),
                "url": microservice_url
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "error": f"Service returned {response.status_code}"
            }), 503
            
    except Exception as e:
        return jsonify({
            "status": "unavailable",
            "error": str(e)
        }), 503
```

## Microservice Integration Patterns

### Pattern 1: Simple Request-Response
```python
def call_microservice(endpoint, data=None, method='POST'):
    """Helper function for microservice calls"""
    base_url = os.environ.get('MICROSERVICE_URL', 'http://localhost:3001')
    url = f"{base_url}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=data, timeout=30)
        
        return response
    except requests.RequestException as e:
        raise Exception(f"Microservice unavailable: {str(e)}")
```

### Pattern 2: Streaming Response
```python
def stream_from_microservice(endpoint, data):
    """Stream response from microservice"""
    response = call_microservice(endpoint, data, method='POST')
    
    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk
    
    return Response(generate(), 
                   content_type=response.headers.get('Content-Type', 'application/octet-stream'))
```

### Pattern 3: Health Check Integration
```python
def check_microservice_health(service_url):
    """Check if microservice is healthy"""
    try:
        response = requests.get(f"{service_url}/healthz", timeout=5)
        return response.status_code == 200
    except:
        return False

@your_blueprint.before_request
def verify_dependencies():
    """Check dependencies before processing requests"""
    if not check_microservice_health(MICROSERVICE_URL):
        return jsonify({"error": "Required service unavailable"}), 503
```

## Troubleshooting

If your route isn't being registered:

1. Check logs for any import errors
2. Ensure your blueprint variable is defined at the module level
3. Verify the blueprint name follows the naming convention
4. Make sure your Python file is in the correct directory under `routes/`

For microservice integration issues:

1. Verify microservice is running and accessible
2. Check environment variables are set correctly
3. Test microservice endpoints directly with curl
4. Review logs for connection errors
5. Ensure network connectivity between services
