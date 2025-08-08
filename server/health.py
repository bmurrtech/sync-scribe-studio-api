"""
Health Check Module
Provides health endpoints for monitoring API status and dependencies.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from flask import Blueprint, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Create health blueprint
health_bp = Blueprint('health', __name__)

def check_environment_variables() -> Dict[str, Any]:
    """Check presence of recommended environment variables"""
    recommended_vars = [
        'X_API_KEY',      # Primary API key
        'API_KEY',        # Alternative API key (config.py looks for both) 
        'DB_TOKEN',       # Database/auth token
        'OPENAI_API_KEY'  # OpenAI API key
    ]
    
    optional_vars = [
        'RATE_LIMIT_DEFAULT',
        'ENABLE_SECURITY_LOGGING',
        'ENABLE_AUDIT_LOGGING',
        'LOG_LEVEL'
    ]
    
    env_status = {
        'status': 'healthy',
        'recommended_vars': {},
        'optional_vars': {}
    }
    
    missing_recommended = []
    
    # Check recommended variables
    for var in recommended_vars:
        present = bool(os.getenv(var))
        env_status['recommended_vars'][var] = {
            'present': present,
            'masked_value': _mask_env_var(var) if present else None
        }
        if not present:
            missing_recommended.append(var)
    
    # Check optional variables
    for var in optional_vars:
        present = bool(os.getenv(var))
        env_status['optional_vars'][var] = {
            'present': present,
            'value': os.getenv(var) if present else None
        }
    
    # Mark as degraded (not unhealthy) if recommended vars are missing
    if missing_recommended:
        env_status['status'] = 'degraded'
        env_status['missing_recommended'] = missing_recommended
        env_status['warning'] = 'Some recommended environment variables are missing. Features may be limited.'
    
    return env_status

def _mask_env_var(var_name: str) -> str:
    """Mask sensitive environment variables for health checks"""
    value = os.getenv(var_name)
    if not value:
        return None
    
    # Variables that should be fully masked
    sensitive_vars = ['DB_TOKEN', 'OPENAI_API_KEY', 'SECRET_KEY', 'X_API_KEY', 'API_KEY']
    
    if var_name in sensitive_vars:
        if len(value) <= 8:
            return '*' * len(value)
        return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
    
    return value

@health_bp.route('/health', methods=['GET'])
def basic_health():
    """Basic health endpoint returning service status"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'SyncScribeStudio API',
            'version': '1.0.0',
            'uptime': 'running'
        }
        return jsonify(health_data), 200
    except Exception as e:
        logger.error(f"Basic health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health():
    """Detailed health endpoint with comprehensive system status"""
    try:
        # Import security health check
        try:
            from server.security import security_health_check
            security_health = security_health_check()
        except ImportError:
            security_health = {
                'status': 'unavailable',
                'error': 'Security module not available'
            }
        
        # Check environment variables
        env_health = check_environment_variables()
        
        # Overall system health
        overall_status = 'healthy'
        if (security_health.get('status') != 'healthy' or 
            env_health.get('status') != 'healthy'):
            overall_status = 'degraded'
        
        health_data = {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'service': 'SyncScribeStudio API',
            'version': '1.0.0',
            'components': {
                'environment': env_health,
                'security': security_health,
                'api': {
                    'status': 'healthy',
                    'endpoints_active': True,
                    'request_processing': 'operational'
                }
            }
        }
        
        status_code = 200 if overall_status == 'healthy' else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/', methods=['GET'])
def root_info():
    """Root endpoint with service information and key endpoints"""
    try:
        service_info = {
            'service': 'SyncScribeStudio API',
            'version': '1.0.0',
            'description': 'AI-powered transcription and content processing API',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'health': {
                    'basic': '/health',
                    'detailed': '/health/detailed'
                },
                'api': {
                    'documentation': '/docs',
                    'openapi': '/openapi.json'
                }
            },
            'authentication': {
                'method': 'Bearer Token or X-API-KEY header',
                'required': True
            },
            'rate_limiting': {
                'default': os.getenv('RATE_LIMIT_DEFAULT', '100/minute'),
                'enabled': True
            }
        }
        return jsonify(service_info), 200
    except Exception as e:
        logger.error(f"Root info endpoint failed: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

# Additional utility functions for health monitoring
def check_disk_space(threshold_percent: float = 90.0) -> Dict[str, Any]:
    """Check available disk space"""
    try:
        import psutil
        disk_usage = psutil.disk_usage('/')
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        return {
            'status': 'healthy' if used_percent < threshold_percent else 'warning',
            'used_percent': round(used_percent, 2),
            'total_gb': round(disk_usage.total / (1024**3), 2),
            'used_gb': round(disk_usage.used / (1024**3), 2),
            'free_gb': round(disk_usage.free / (1024**3), 2)
        }
    except ImportError:
        return {'status': 'unavailable', 'error': 'psutil not installed'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_memory_usage(threshold_percent: float = 85.0) -> Dict[str, Any]:
    """Check memory usage"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        return {
            'status': 'healthy' if memory.percent < threshold_percent else 'warning',
            'used_percent': memory.percent,
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2)
        }
    except ImportError:
        return {'status': 'unavailable', 'error': 'psutil not installed'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

# Register blueprint function
def register_health_endpoints(app):
    """Register health endpoints with Flask app"""
    app.register_blueprint(health_bp)
    logger.info("Health endpoints registered: /, /health, /health/detailed")

# Export main components
__all__ = [
    'health_bp',
    'register_health_endpoints',
    'check_environment_variables',
    'check_disk_space', 
    'check_memory_usage'
]
