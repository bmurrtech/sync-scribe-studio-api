"""
FastAPI-compatible Security Module
Provides API key authentication, rate limiting, and security middleware.
"""

import os
import logging
import secrets
import re
from typing import Optional, Dict, Any, List
from functools import wraps
from datetime import datetime, timedelta
import json

# FastAPI-style imports and Flask compatibility
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Request, Depends, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from flask import request as flask_request, jsonify, g
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
SECURITY_CONFIG = {
    'RATE_LIMIT_DEFAULT': os.getenv('RATE_LIMIT_DEFAULT', '100/minute'),
    'ENABLE_SECURITY_LOGGING': os.getenv('ENABLE_SECURITY_LOGGING', 'true').lower() == 'true',
    'ENABLE_AUDIT_LOGGING': os.getenv('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true',
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
}

# FastAPI-compatible HTTPBearer scheme
class APIKeyHTTPBearer(HTTPBearer):
    """Custom HTTPBearer for API key validation with auto_error=False"""
    
    def __init__(self, auto_error: bool = False):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Extract and validate bearer token from request"""
        try:
            credentials = await super().__call__(request)
            if credentials:
                return credentials
        except HTTPException:
            pass
        return None

# Global security scheme instance
security_scheme = APIKeyHTTPBearer(auto_error=False)

class APIKeyValidator:
    """Validates API keys against environment variables"""
    
    def __init__(self):
        self.db_token = self._load_db_token()
    
    def _load_db_token(self) -> str:
        """Load DB_TOKEN from environment with validation"""
        token = os.getenv('DB_TOKEN')
        if not token:
            raise ValueError("DB_TOKEN environment variable is required")
        
        if SECURITY_CONFIG['ENABLE_SECURITY_LOGGING']:
            masked_token = self._mask_token(token)
            logger.info(f"DB_TOKEN loaded: {masked_token}")
        
        return token
    
    def _mask_token(self, token: str, reveal_chars: int = 4) -> str:
        """Mask token for logging purposes (first4****last4)"""
        if len(token) <= reveal_chars * 2:
            return '*' * len(token)
        
        return f"{token[:reveal_chars]}{'*' * (len(token) - reveal_chars * 2)}{token[-reveal_chars:]}"
    
    def validate_api_key(self, provided_key: str) -> bool:
        """Validate provided API key against DB_TOKEN using constant-time comparison"""
        if not provided_key or not self.db_token:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(self.db_token, provided_key)
    
    def log_auth_attempt(self, success: bool, ip_address: str, token: str = None) -> None:
        """Log authentication attempts with masked tokens"""
        if not SECURITY_CONFIG['ENABLE_SECURITY_LOGGING']:
            return
        
        status = 'SUCCESS' if success else 'FAILED'
        masked_token = self._mask_token(token) if token else 'None'
        message = f"Auth attempt {status} - IP: {ip_address} - Token: {masked_token}"
        
        if success:
            logger.info(message)
        else:
            logger.warning(message)

# Global validator instance (initialized lazily)
api_key_validator = None

def get_api_key_validator():
    """Get or create global API key validator instance"""
    global api_key_validator
    if api_key_validator is None:
        api_key_validator = APIKeyValidator()
    return api_key_validator

# Rate limiter setup with SlowAPI
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[SECURITY_CONFIG['RATE_LIMIT_DEFAULT']]
)

class SecurityMiddleware:
    """Security middleware for FastAPI-style authentication in Flask"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app"""
        # Add SlowAPI middleware for rate limiting
        app.state = type('State', (), {})()  # Add state attribute for SlowAPI compatibility
        
        # Register error handler for rate limiting
        @app.errorhandler(429)
        def rate_limit_handler(e):
            return jsonify({
                "error": "Rate limit exceeded",
                "message": "Too many requests",
                "retry_after": getattr(e, 'retry_after', 60)
            }), 429

def get_api_key_from_request() -> Optional[str]:
    """Extract API key from Flask request headers"""
    # Check Authorization header (Bearer token)
    auth_header = flask_request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1]
    
    # Check X-API-KEY header as fallback
    api_key = flask_request.headers.get('X-API-KEY')
    if api_key:
        return api_key
    
    return None

def validate_api_key_dependency() -> str:
    """FastAPI-style dependency for API key validation"""
    api_key = get_api_key_from_request()
    ip_address = flask_request.remote_addr or 'unknown'
    
    validator = get_api_key_validator()
    
    if not api_key:
        validator.log_auth_attempt(False, ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not validator.validate_api_key(api_key):
        validator.log_auth_attempt(False, ip_address, api_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    validator.log_auth_attempt(True, ip_address, api_key)
    return api_key

def require_api_key(f):
    """Flask decorator for API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = get_api_key_from_request()
        ip_address = flask_request.remote_addr or 'unknown'
        validator = get_api_key_validator()
        
        if not api_key:
            validator.log_auth_attempt(False, ip_address)
            return jsonify({
                "error": "Missing API key",
                "message": "Authorization header with Bearer token or X-API-KEY header required"
            }), 401
        
        if not validator.validate_api_key(api_key):
            validator.log_auth_attempt(False, ip_address, api_key)
            return jsonify({
                "error": "Invalid API key",
                "message": "The provided API key is not valid"
            }), 401
        
        validator.log_auth_attempt(True, ip_address, api_key)
        g.current_api_key = api_key
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(limit_string: str = None):
    """Rate limiting decorator using SlowAPI"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use the limit_string or default
            limit = limit_string or SECURITY_CONFIG['RATE_LIMIT_DEFAULT']
            
            # Get client IP
            ip_address = flask_request.remote_addr or 'unknown'
            
            # Simple rate limiting check (in production, use Redis or proper storage)
            # For now, we'll implement a basic in-memory rate limiter
            if not _check_rate_limit(ip_address, limit):
                logger.warning(f"Rate limit exceeded for IP: {ip_address} on endpoint: {flask_request.endpoint}")
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests from {ip_address}",
                    "limit": limit
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# In-memory rate limiter (replace with Redis in production)
_rate_limit_storage = {}
_rate_limit_cleanup_last = datetime.now()

def _check_rate_limit(identifier: str, limit_string: str) -> bool:
    """Check if request is within rate limits"""
    global _rate_limit_storage, _rate_limit_cleanup_last
    
    # Parse limit string (e.g., "100/minute", "10/second")
    try:
        count, period = limit_string.split('/')
        count = int(count)
        
        if period.startswith('second'):
            window_seconds = 1
        elif period.startswith('minute'):
            window_seconds = 60
        elif period.startswith('hour'):
            window_seconds = 3600
        else:
            window_seconds = 60  # default to minute
    except:
        count, window_seconds = 100, 60  # default
    
    now = datetime.now()
    
    # Periodic cleanup
    if now - _rate_limit_cleanup_last > timedelta(minutes=5):
        _cleanup_rate_limit_storage(now, window_seconds * 2)
        _rate_limit_cleanup_last = now
    
    # Initialize storage for identifier
    if identifier not in _rate_limit_storage:
        _rate_limit_storage[identifier] = []
    
    # Remove expired entries
    cutoff = now - timedelta(seconds=window_seconds)
    _rate_limit_storage[identifier] = [
        timestamp for timestamp in _rate_limit_storage[identifier]
        if timestamp > cutoff
    ]
    
    # Check limit
    if len(_rate_limit_storage[identifier]) >= count:
        return False
    
    # Add current request
    _rate_limit_storage[identifier].append(now)
    return True

def _cleanup_rate_limit_storage(now: datetime, window_seconds: int):
    """Clean up expired rate limit entries"""
    cutoff = now - timedelta(seconds=window_seconds)
    expired_keys = []
    
    for identifier, timestamps in _rate_limit_storage.items():
        _rate_limit_storage[identifier] = [
            timestamp for timestamp in timestamps
            if timestamp > cutoff
        ]
        if not _rate_limit_storage[identifier]:
            expired_keys.append(identifier)
    
    for key in expired_keys:
        del _rate_limit_storage[key]

def setup_security(app):
    """Setup security middleware and components for Flask app"""
    # Initialize security middleware
    security_middleware = SecurityMiddleware(app)
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Server': 'SyncScribeStudio-API/1.0'
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    # Log security setup
    logger.info("Security middleware initialized")
    logger.info(f"Rate limiting: {SECURITY_CONFIG['RATE_LIMIT_DEFAULT']}")
    logger.info(f"Security logging: {'ENABLED' if SECURITY_CONFIG['ENABLE_SECURITY_LOGGING'] else 'DISABLED'}")
    
    return app

def security_health_check() -> Dict[str, Any]:
    """Perform health check on security components"""
    health = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {}
    }
    
    try:
        # Check API key validator
        health['components']['api_key_validator'] = {
            'status': 'healthy',
            'db_token_configured': bool(os.getenv('DB_TOKEN'))
        }
        
        # Check security configuration
        health['components']['security_config'] = {
            'status': 'healthy',
            'rate_limit_default': SECURITY_CONFIG['RATE_LIMIT_DEFAULT'],
            'security_logging_enabled': SECURITY_CONFIG['ENABLE_SECURITY_LOGGING'],
            'audit_logging_enabled': SECURITY_CONFIG['ENABLE_AUDIT_LOGGING']
        }
        
        # Check rate limiter
        health['components']['rate_limiter'] = {
            'status': 'healthy',
            'active_ips': len(_rate_limit_storage)
        }
        
    except Exception as e:
        health['status'] = 'unhealthy'
        health['error'] = str(e)
        logger.error(f"Security health check failed: {e}")
    
    return health

# Export main components
__all__ = [
    'require_api_key',
    'rate_limit', 
    'setup_security',
    'validate_api_key_dependency',
    'security_health_check',
    'APIKeyValidator',
    'SecurityMiddleware'
]
