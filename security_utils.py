"""
Security Utilities Module
Provides security functions, secret management, and security headers for the API.
"""

import os
import logging
import hashlib
import secrets
import re
from typing import Optional, Dict, Any, List
from functools import wraps
from datetime import datetime, timedelta
import json

# Security imports
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
SECURITY_CONFIG = {
    'ENABLE_SECURITY_HEADERS': os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() == 'true',
    'ALLOWED_ORIGINS': os.getenv('ALLOWED_ORIGINS', 'https://yourdomain.com').split(','),
    'RATE_LIMIT_REQUESTS': int(os.getenv('RATE_LIMIT_REQUESTS', 100)),
    'RATE_LIMIT_WINDOW': int(os.getenv('RATE_LIMIT_WINDOW', 60)),
    'ENABLE_SECURITY_LOGGING': os.getenv('ENABLE_SECURITY_LOGGING', 'true').lower() == 'true',
    'ENABLE_AUDIT_LOGGING': os.getenv('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true',
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
}

class SecretManager:
    """Manages API secrets and environment variables securely."""
    
    def __init__(self):
        self.required_secrets = [
            'OPENAI_API_KEY',
            'DB_TOKEN'
        ]
        self.optional_secrets = [
            'SENTRY_DSN',
            'SLACK_WEBHOOK_URL',
            'GCP_SA_CREDENTIALS',
            'S3_ACCESS_KEY',
            'S3_SECRET_KEY'
        ]
        self._validate_required_secrets()
    
    def _validate_required_secrets(self) -> None:
        """Validate that all required secrets are present."""
        missing_secrets = []
        
        for secret in self.required_secrets:
            if not os.getenv(secret):
                missing_secrets.append(secret)
        
        if missing_secrets:
            error_msg = f"Missing required environment variables: {', '.join(missing_secrets)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("All required secrets validated successfully")
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Safely retrieve a secret from environment variables."""
        value = os.getenv(key, default)
        
        if SECURITY_CONFIG['ENABLE_SECURITY_LOGGING'] and value:
            # Log secret access (masked)
            masked_value = self._mask_secret(value)
            logger.info(f"Secret accessed: {key}={masked_value}")
        
        return value
    
    def _mask_secret(self, secret: str, reveal_chars: int = 4) -> str:
        """Mask secret for logging purposes."""
        if len(secret) <= reveal_chars * 2:
            return '*' * len(secret)
        
        return f"{secret[:reveal_chars]}{'*' * (len(secret) - reveal_chars * 2)}{secret[-reveal_chars:]}"
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate a secret (for future implementation with key management service)."""
        # This would integrate with a proper key management service
        logger.warning(f"Secret rotation requested for {key} - implement with KMS")
        return False
    
    def validate_api_key(self, provided_key: str) -> bool:
        """Validate provided API key against stored token."""
        stored_token = self.get_secret('DB_TOKEN')
        
        if not stored_token or not provided_key:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(stored_token, provided_key)

class SecurityHeaders:
    """Manages security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers."""
        if not SECURITY_CONFIG['ENABLE_SECURITY_HEADERS']:
            return {}
        
        return {
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # Enable XSS protection
            'X-XSS-Protection': '1; mode=block',
            
            # Force HTTPS
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            
            # Content Security Policy
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-src 'none'; object-src 'none';",
            
            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Feature policy
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()',
            
            # Server identification
            'Server': 'SyncScribeStudio/1.0',
        }
    
    @staticmethod
    def get_cors_headers(origin: str = None) -> Dict[str, str]:
        """Get CORS headers based on origin."""
        headers = {}
        
        # Check if origin is allowed
        if origin and origin in SECURITY_CONFIG['ALLOWED_ORIGINS']:
            headers['Access-Control-Allow-Origin'] = origin
        elif '*' in SECURITY_CONFIG['ALLOWED_ORIGINS']:
            headers['Access-Control-Allow-Origin'] = '*'
        else:
            # Default to first allowed origin if none match
            headers['Access-Control-Allow-Origin'] = SECURITY_CONFIG['ALLOWED_ORIGINS'][0]
        
        headers.update({
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Max-Age': '86400',  # 24 hours
        })
        
        return headers

class InputValidator:
    """Validates and sanitizes user inputs."""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and allowed domains."""
        if not url:
            return False
        
        # Basic URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal."""
        if not filename:
            return ''
        
        # Remove directory traversal attempts
        filename = filename.replace('..', '')
        filename = filename.replace('/', '')
        filename = filename.replace('\\', '')
        
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:251] + ext
        
        return filename
    
    @staticmethod
    def validate_api_key_format(api_key: str) -> bool:
        """Validate API key format."""
        if not api_key:
            return False
        
        # Should be at least 32 characters and contain only valid characters
        if len(api_key) < 32:
            return False
        
        # Should not contain obvious patterns
        patterns_to_avoid = ['password', 'secret', 'key', '123456', 'admin']
        api_key_lower = api_key.lower()
        
        for pattern in patterns_to_avoid:
            if pattern in api_key_lower:
                return False
        
        return True

class SecurityAuditLogger:
    """Handles security-related logging and auditing."""
    
    def __init__(self):
        self.audit_logger = logging.getLogger('security_audit')
        
        # Configure audit log format
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        
        # Add file handler for security logs
        if SECURITY_CONFIG['ENABLE_AUDIT_LOGGING']:
            handler = logging.FileHandler('logs/security_audit.log')
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
    
    def log_authentication_attempt(self, success: bool, ip_address: str, user_agent: str = None):
        """Log authentication attempts."""
        status = 'SUCCESS' if success else 'FAILED'
        message = f"Authentication {status} - IP: {ip_address}"
        if user_agent:
            message += f" - User-Agent: {user_agent}"
        
        if success:
            self.audit_logger.info(message)
        else:
            self.audit_logger.warning(message)
    
    def log_api_access(self, endpoint: str, method: str, ip_address: str, authenticated: bool):
        """Log API access."""
        auth_status = 'AUTHENTICATED' if authenticated else 'UNAUTHENTICATED'
        message = f"API Access - {method} {endpoint} - {auth_status} - IP: {ip_address}"
        self.audit_logger.info(message)
    
    def log_security_event(self, event_type: str, details: str, severity: str = 'INFO'):
        """Log general security events."""
        message = f"Security Event - {event_type}: {details}"
        
        if severity == 'CRITICAL':
            self.audit_logger.critical(message)
        elif severity == 'ERROR':
            self.audit_logger.error(message)
        elif severity == 'WARNING':
            self.audit_logger.warning(message)
        else:
            self.audit_logger.info(message)

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = {}
        self.cleanup_interval = timedelta(minutes=5)
        self.last_cleanup = datetime.now()
    
    def is_allowed(self, identifier: str, limit: int = None, window: int = None) -> bool:
        """Check if request is within rate limits."""
        limit = limit or SECURITY_CONFIG['RATE_LIMIT_REQUESTS']
        window = window or SECURITY_CONFIG['RATE_LIMIT_WINDOW']
        
        now = datetime.now()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_entries(now, window)
        
        # Get or create entry for identifier
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove expired requests
        cutoff = now - timedelta(seconds=window)
        self.requests[identifier] = [
            timestamp for timestamp in self.requests[identifier]
            if timestamp > cutoff
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) >= limit:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def _cleanup_expired_entries(self, now: datetime, window: int):
        """Clean up expired rate limit entries."""
        cutoff = now - timedelta(seconds=window * 2)  # Extra buffer
        
        expired_keys = []
        for identifier, timestamps in self.requests.items():
            # Remove expired timestamps
            self.requests[identifier] = [
                timestamp for timestamp in timestamps
                if timestamp > cutoff
            ]
            
            # Mark empty entries for removal
            if not self.requests[identifier]:
                expired_keys.append(identifier)
        
        # Remove empty entries
        for key in expired_keys:
            del self.requests[key]
        
        self.last_cleanup = now

# Global instances
secret_manager = SecretManager()
security_headers = SecurityHeaders()
input_validator = InputValidator()
audit_logger = SecurityAuditLogger()
rate_limiter = RateLimiter()

# Decorator for requiring authentication
def require_auth(f):
    """Decorator to require authentication for endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request, jsonify
        
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            audit_logger.log_authentication_attempt(
                False, 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Validate token
        if not secret_manager.validate_api_key(token):
            audit_logger.log_authentication_attempt(
                False, 
                request.remote_addr, 
                request.headers.get('User-Agent')
            )
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Log successful authentication
        audit_logger.log_authentication_attempt(
            True, 
            request.remote_addr, 
            request.headers.get('User-Agent')
        )
        
        return f(*args, **kwargs)
    
    return decorated

# Decorator for rate limiting
def rate_limit(limit: int = None, window: int = None):
    """Decorator to apply rate limiting to endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request, jsonify
            
            # Use IP address as identifier
            identifier = request.remote_addr
            
            if not rate_limiter.is_allowed(identifier, limit, window):
                audit_logger.log_security_event(
                    'RATE_LIMIT_EXCEEDED',
                    f'IP: {identifier} - Endpoint: {request.endpoint}',
                    'WARNING'
                )
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def initialize_security():
    """Initialize security components."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Log security initialization
    logger.info("Security components initialized successfully")
    logger.info(f"Security headers: {'ENABLED' if SECURITY_CONFIG['ENABLE_SECURITY_HEADERS'] else 'DISABLED'}")
    logger.info(f"Security logging: {'ENABLED' if SECURITY_CONFIG['ENABLE_SECURITY_LOGGING'] else 'DISABLED'}")
    logger.info(f"Rate limiting: {SECURITY_CONFIG['RATE_LIMIT_REQUESTS']} requests per {SECURITY_CONFIG['RATE_LIMIT_WINDOW']} seconds")
    
    return True

# Health check for security components
def security_health_check() -> Dict[str, Any]:
    """Perform health check on security components."""
    health = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {}
    }
    
    try:
        # Check secret manager
        health['components']['secret_manager'] = {
            'status': 'healthy',
            'required_secrets': len(secret_manager.required_secrets),
            'optional_secrets': len(secret_manager.optional_secrets)
        }
        
        # Check security configuration
        health['components']['security_config'] = {
            'status': 'healthy',
            'security_headers_enabled': SECURITY_CONFIG['ENABLE_SECURITY_HEADERS'],
            'security_logging_enabled': SECURITY_CONFIG['ENABLE_SECURITY_LOGGING'],
            'rate_limiting_enabled': True
        }
        
    except Exception as e:
        health['status'] = 'unhealthy'
        health['error'] = str(e)
        logger.error(f"Security health check failed: {e}")
    
    return health

if __name__ == "__main__":
    # Initialize and run health check
    initialize_security()
    health = security_health_check()
    print(json.dumps(health, indent=2))
