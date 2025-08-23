"""
Test Utilities Module
=====================
Shared utility functions for both test scripts and pytest suites.
Provides common helpers for API testing, job polling, and URL conversion.
"""

import os
import time
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode
import re

# Configure module logger
logger = logging.getLogger(__name__)


def load_env(env_file: str = ".env", required_vars: Optional[list] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file with validation.
    
    Args:
        env_file: Path to the .env file (default: ".env")
        required_vars: List of required environment variable names to validate
    
    Returns:
        Dictionary of loaded environment variables
        
    Raises:
        FileNotFoundError: If env_file doesn't exist
        ValueError: If required variables are missing
        
    Example:
        >>> env = load_env(required_vars=['API_KEY', 'BASE_URL'])
        >>> api_key = env['API_KEY']
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found: {env_file}")
    
    # Load the environment file
    load_dotenv(env_file, override=True)
    logger.info(f"Loaded environment from: {env_file}")
    
    # Collect all loaded variables
    env_vars = {}
    
    # Read and parse the env file to get all defined variables
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Get from environment (in case of variable expansion)
                    env_vars[key] = os.getenv(key, value)
    
    # Validate required variables
    if required_vars:
        missing = []
        for var in required_vars:
            if var not in env_vars or not env_vars[var]:
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    logger.info(f"Loaded {len(env_vars)} environment variables")
    return env_vars


def post_json(
    url: str,
    payload: Dict[str, Any],
    api_key: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    verify_ssl: bool = True
) -> requests.Response:
    """
    Wrapper for making JSON POST requests with standard headers.
    
    Args:
        url: The URL to POST to
        payload: Dictionary to send as JSON payload
        api_key: Optional API key for X-API-Key header
        headers: Additional headers to include (merged with defaults)
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
    
    Returns:
        requests.Response object
        
    Raises:
        requests.RequestException: On request failure
        
    Example:
        >>> response = post_json(
        ...     "https://api.example.com/v1/process",
        ...     {"media_url": "https://example.com/video.mp4"},
        ...     api_key="your-api-key"
        ... )
        >>> print(response.json())
    """
    # Default headers for JSON requests
    default_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "TestUtils/1.0"
    }
    
    # Add API key if provided
    if api_key:
        default_headers["X-API-Key"] = api_key
    
    # Merge with custom headers
    if headers:
        default_headers.update(headers)
    
    logger.debug(f"POST {url} with payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=default_headers,
            timeout=timeout,
            verify=verify_ssl
        )
        
        logger.info(f"POST {url} returned {response.status_code}")
        return response
        
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise


def wait_for_job_status(
    job_id: str,
    base_url: str,
    api_key: Optional[str] = None,
    timeout: int = 300,
    poll_interval: float = 2.0,
    exponential_backoff: bool = True,
    max_poll_interval: float = 30.0,
    status_endpoint: str = "/v1/toolkit/job_status"
) -> Tuple[str, Dict[str, Any], float]:
    """
    Poll for async job completion with configurable polling strategy.
    
    Args:
        job_id: The job ID to monitor
        base_url: Base URL of the API
        api_key: Optional API key for authentication
        timeout: Maximum time to wait in seconds (default: 300)
        poll_interval: Initial polling interval in seconds (default: 2.0)
        exponential_backoff: Whether to use exponential backoff (default: True)
        max_poll_interval: Maximum polling interval for backoff (default: 30.0)
        status_endpoint: The endpoint path for checking job status
    
    Returns:
        Tuple of (final_status, response_data, total_wait_time)
        where final_status is one of: "completed", "failed", "error", "timeout"
        
    Raises:
        ValueError: If job_id is invalid
        requests.RequestException: On network errors
        
    Example:
        >>> status, data, wait_time = wait_for_job_status(
        ...     "job-123",
        ...     "https://api.example.com",
        ...     api_key="your-key",
        ...     timeout=120
        ... )
        >>> if status == "completed":
        ...     print(f"Job completed in {wait_time:.2f} seconds")
        ...     print(data['response'])
    """
    if not job_id:
        raise ValueError("job_id is required")
    
    # Construct the status check URL
    base_url = base_url.rstrip('/')
    status_url = f"{base_url}{status_endpoint}"
    
    # Setup headers
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    
    start_time = time.time()
    current_interval = poll_interval
    attempt = 0
    
    logger.info(f"Waiting for job {job_id} to complete (timeout: {timeout}s)")
    
    while True:
        attempt += 1
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed >= timeout:
            logger.warning(f"Job {job_id} timed out after {elapsed:.2f} seconds")
            return "timeout", {"message": f"Job timed out after {timeout} seconds"}, elapsed
        
        try:
            # Make status check request
            response = requests.get(
                status_url,
                params={"job_id": job_id},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                
                logger.debug(f"Job {job_id} status check #{attempt}: {status} (elapsed: {elapsed:.1f}s)")
                
                # Check for terminal states
                if status in ["completed", "complete", "success"]:
                    logger.info(f"Job {job_id} completed successfully after {elapsed:.2f} seconds")
                    return "completed", data, elapsed
                    
                elif status in ["failed", "error", "failure"]:
                    logger.warning(f"Job {job_id} failed after {elapsed:.2f} seconds")
                    return status, data, elapsed
                
                # Job still processing
                elif status in ["processing", "pending", "queued", "running"]:
                    pass  # Continue polling
                    
                else:
                    logger.warning(f"Unknown job status: {status}")
            
            elif response.status_code == 404:
                logger.error(f"Job {job_id} not found")
                return "error", {"message": "Job not found", "code": 404}, elapsed
                
            else:
                logger.warning(f"Status check returned {response.status_code}: {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"Error checking job status: {e}")
            # Continue polling on transient errors
        
        # Wait before next poll
        time.sleep(current_interval)
        
        # Apply exponential backoff if enabled
        if exponential_backoff:
            current_interval = min(current_interval * 1.5, max_poll_interval)


def gdrive_to_download_url(share_url: str) -> str:
    """
    Convert Google Drive sharing URLs to direct download URLs.
    
    Supports various Google Drive URL formats:
    - https://drive.google.com/file/d/{FILE_ID}/view
    - https://drive.google.com/open?id={FILE_ID}
    - https://drive.google.com/uc?id={FILE_ID}
    - https://docs.google.com/document/d/{FILE_ID}/edit
    - https://docs.google.com/spreadsheets/d/{FILE_ID}/edit
    - https://docs.google.com/presentation/d/{FILE_ID}/edit
    
    Args:
        share_url: Google Drive sharing URL
        
    Returns:
        Direct download URL for the file
        
    Raises:
        ValueError: If URL is not a valid Google Drive URL
        
    Example:
        >>> url = "https://drive.google.com/file/d/1ABC123/view?usp=sharing"
        >>> download_url = gdrive_to_download_url(url)
        >>> print(download_url)
        https://drive.google.com/uc?export=download&id=1ABC123
    """
    if not share_url:
        raise ValueError("URL cannot be empty")
    
    # Parse the URL
    parsed = urlparse(share_url)
    
    # Check if it's a Google domain
    valid_domains = ['drive.google.com', 'docs.google.com']
    if parsed.netloc not in valid_domains:
        raise ValueError(f"Not a valid Google Drive URL: {share_url}")
    
    file_id = None
    
    # Try different URL patterns
    # Pattern 1: /file/d/{FILE_ID}/
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', share_url)
    if match:
        file_id = match.group(1)
    
    # Pattern 2: /open?id={FILE_ID}
    if not file_id:
        query_params = parse_qs(parsed.query)
        if 'id' in query_params:
            file_id = query_params['id'][0]
    
    # Pattern 3: /uc?id={FILE_ID}
    if not file_id and '/uc' in parsed.path:
        query_params = parse_qs(parsed.query)
        if 'id' in query_params:
            file_id = query_params['id'][0]
    
    # Pattern 4: Google Docs/Sheets/Slides - /document/d/{FILE_ID}/
    if not file_id:
        match = re.search(r'/(document|spreadsheets|presentation)/d/([a-zA-Z0-9_-]+)', share_url)
        if match:
            file_id = match.group(2)
    
    # Pattern 5: Shortened URL with just the ID in path
    if not file_id:
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', share_url)
        if match:
            file_id = match.group(1)
    
    if not file_id:
        raise ValueError(f"Could not extract file ID from URL: {share_url}")
    
    # Construct direct download URL
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    logger.info(f"Converted Google Drive URL to download URL: {download_url}")
    return download_url


# Additional utility functions for common test operations

def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> requests.Response:
    """
    Wrapper for making JSON GET requests with standard headers.
    
    Args:
        url: The URL to GET from
        params: Query parameters
        api_key: Optional API key for X-API-Key header
        headers: Additional headers to include
        timeout: Request timeout in seconds
    
    Returns:
        requests.Response object
    """
    default_headers = {
        "Accept": "application/json",
        "User-Agent": "TestUtils/1.0"
    }
    
    if api_key:
        default_headers["X-API-Key"] = api_key
    
    if headers:
        default_headers.update(headers)
    
    logger.debug(f"GET {url} with params: {params}")
    
    try:
        response = requests.get(
            url,
            params=params,
            headers=default_headers,
            timeout=timeout
        )
        
        logger.info(f"GET {url} returned {response.status_code}")
        return response
        
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise


def validate_json_response(
    response: requests.Response,
    expected_status: Union[int, list] = 200,
    required_fields: Optional[list] = None
) -> Dict[str, Any]:
    """
    Validate a JSON response and extract data.
    
    Args:
        response: The response object to validate
        expected_status: Expected status code(s)
        required_fields: List of required fields in response JSON
    
    Returns:
        Parsed JSON data
        
    Raises:
        AssertionError: If validation fails
    """
    # Check status code
    if isinstance(expected_status, int):
        expected_status = [expected_status]
    
    assert response.status_code in expected_status, \
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    
    # Parse JSON
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise AssertionError(f"Invalid JSON response: {e}")
    
    # Check required fields
    if required_fields:
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise AssertionError(f"Missing required fields: {missing}")
    
    return data


def generate_test_id(prefix: str = "test") -> str:
    """
    Generate a unique test ID for tracking.
    
    Args:
        prefix: Prefix for the ID
    
    Returns:
        Unique test ID string
    """
    import uuid
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}"


def retry_on_failure(
    func,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry a function on failure with exponential backoff.
    
    Args:
        func: Function to retry (callable)
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    
    Returns:
        Function result on success
        
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= backoff
            else:
                logger.error(f"All {max_attempts} attempts failed")
    
    raise last_exception


def format_test_summary(
    passed: int,
    failed: int,
    skipped: int = 0,
    duration: float = 0.0
) -> str:
    """
    Format a test summary string with colors.
    
    Args:
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        duration: Total duration in seconds
    
    Returns:
        Formatted summary string
    """
    total = passed + failed + skipped
    
    # Color codes for terminal output
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    
    parts = []
    
    if passed > 0:
        parts.append(f"{GREEN}{passed} passed{RESET}")
    if failed > 0:
        parts.append(f"{RED}{failed} failed{RESET}")
    if skipped > 0:
        parts.append(f"{YELLOW}{skipped} skipped{RESET}")
    
    summary = f"Tests: {', '.join(parts)} ({total} total)"
    
    if duration > 0:
        summary += f" in {duration:.2f}s"
    
    return summary


# Export main utilities
__all__ = [
    'load_env',
    'post_json',
    'wait_for_job_status',
    'gdrive_to_download_url',
    'get_json',
    'validate_json_response',
    'generate_test_id',
    'retry_on_failure',
    'format_test_summary'
]
