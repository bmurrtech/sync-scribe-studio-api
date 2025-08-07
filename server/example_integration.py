"""
Example Integration for Security Middleware
Shows how to apply @require_api_key and @rate_limit decorators to existing Flask routes.
"""

import os
from flask import Flask, jsonify, request, g
from server.security import require_api_key, rate_limit, setup_security
from server.health import register_health_endpoints
from server.mcpo_config import register_openapi_endpoints

def create_secure_app():
    """Create Flask app with security middleware enabled"""
    app = Flask(__name__)
    
    # Setup security middleware
    setup_security(app)
    
    # Register health and documentation endpoints
    register_health_endpoints(app)
    register_openapi_endpoints(app)
    
    # Example: Public endpoint (no authentication required)
    @app.route('/api/public')
    @rate_limit("50/minute")  # Still rate limited
    def public_endpoint():
        """Public endpoint with rate limiting only"""
        return jsonify({
            "message": "This is a public endpoint",
            "authenticated": False,
            "client_ip": request.remote_addr
        })
    
    # Example: Protected endpoint requiring API key
    @app.route('/api/protected')
    @require_api_key
    @rate_limit("100/minute")
    def protected_endpoint():
        """Protected endpoint requiring API key authentication"""
        return jsonify({
            "message": "This is a protected endpoint",
            "authenticated": True,
            "api_key_used": g.current_api_key[:8] + "..." if hasattr(g, 'current_api_key') else None,
            "client_ip": request.remote_addr
        })
    
    # Example: High-security endpoint with stricter rate limiting
    @app.route('/api/admin')
    @require_api_key
    @rate_limit("10/minute")  # Stricter rate limit
    def admin_endpoint():
        """Admin endpoint with strict rate limiting"""
        return jsonify({
            "message": "This is an admin endpoint with strict rate limiting",
            "authenticated": True,
            "rate_limit": "10 requests per minute",
            "security_level": "high"
        })
    
    # Example: Data processing endpoint
    @app.route('/api/process', methods=['POST'])
    @require_api_key
    @rate_limit("20/minute")
    def process_data():
        """Process data endpoint with authentication and rate limiting"""
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        # Mock processing
        result = {
            "status": "processed",
            "input_data": data,
            "processed_by": "SyncScribeStudio API",
            "authenticated": True
        }
        
        return jsonify(result)
    
    # Example: File upload endpoint with different rate limit
    @app.route('/api/upload', methods=['POST'])
    @require_api_key
    @rate_limit("5/minute")  # Lower limit for resource-intensive operations
    def upload_file():
        """File upload endpoint with strict rate limiting"""
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        # Mock file processing
        return jsonify({
            "message": "File upload received",
            "filename": file.filename,
            "size_bytes": len(file.read()),
            "authenticated": True,
            "rate_limit": "5 uploads per minute"
        })
    
    # Example: Batch processing endpoint
    @app.route('/api/batch', methods=['POST'])
    @require_api_key
    @rate_limit("2/minute")  # Very strict for batch operations
    def batch_process():
        """Batch processing endpoint with very strict rate limiting"""
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        items = data.get('items', [])
        
        # Mock batch processing
        results = []
        for i, item in enumerate(items):
            results.append({
                "index": i,
                "item": item,
                "status": "processed",
                "timestamp": "2025-01-27T10:00:00Z"
            })
        
        return jsonify({
            "batch_id": "batch_12345",
            "total_items": len(items),
            "results": results,
            "authenticated": True,
            "processing_time_ms": 150
        })
    
    # Example: Health check for protected resources
    @app.route('/api/health/secure')
    @require_api_key
    def secure_health():
        """Authenticated health check endpoint"""
        return jsonify({
            "status": "healthy",
            "authenticated": True,
            "message": "Secure health check passed",
            "api_key_masked": g.current_api_key[:4] + "****" if hasattr(g, 'current_api_key') else None
        })
    
    # Example: Configuration endpoint
    @app.route('/api/config')
    @require_api_key
    @rate_limit("30/minute")
    def get_config():
        """Get API configuration (authenticated)"""
        config = {
            "api_name": "SyncScribeStudio API",
            "version": "1.0.0",
            "rate_limits": {
                "default": os.getenv('RATE_LIMIT_DEFAULT', '100/minute'),
                "admin": "10/minute",
                "upload": "5/minute",
                "batch": "2/minute"
            },
            "security": {
                "authentication_required": True,
                "rate_limiting_enabled": True,
                "security_headers_enabled": True
            },
            "authenticated": True
        }
        return jsonify(config)
    
    return app

def integrate_with_existing_app(app):
    """
    Function to integrate security middleware with an existing Flask app.
    Call this with your existing Flask app instance.
    """
    # Setup security middleware
    setup_security(app)
    
    # Register health and documentation endpoints
    register_health_endpoints(app)
    register_openapi_endpoints(app)
    
    # Example of adding security to existing routes
    # You can apply decorators to existing route functions like this:
    
    # Method 1: Wrap existing route function
    if '/api/existing-route' in [rule.rule for rule in app.url_map.iter_rules()]:
        # Get the existing view function
        existing_view = app.view_functions.get('existing_route_function_name')
        if existing_view:
            # Wrap with security decorators
            secured_view = require_api_key(rate_limit("50/minute")(existing_view))
            # Replace the view function
            app.view_functions['existing_route_function_name'] = secured_view
    
    # Method 2: Add new secure endpoints to existing app
    @app.route('/api/new-secure-endpoint')
    @require_api_key
    @rate_limit("25/minute")
    def new_secure_endpoint():
        return jsonify({
            "message": "New secure endpoint added to existing app",
            "authenticated": True
        })
    
    return app

# Example usage functions
def example_usage():
    """Example of how to use the security middleware"""
    
    # Option 1: Create new app with security
    app = create_secure_app()
    
    # Option 2: Add security to existing app
    # existing_app = Flask(__name__)
    # secured_app = integrate_with_existing_app(existing_app)
    
    return app

if __name__ == '__main__':
    # Example: Run the secure app
    app = create_secure_app()
    
    # Make sure you have DB_TOKEN set in environment
    if not os.getenv('DB_TOKEN'):
        print("WARNING: DB_TOKEN not set in environment!")
        print("Set it with: export DB_TOKEN='your-secure-api-key-here'")
    
    print("Starting SyncScribeStudio API with security enabled...")
    print("Available endpoints:")
    print("  GET  /                     - Service information")
    print("  GET  /health               - Basic health check")
    print("  GET  /health/detailed      - Detailed health check")
    print("  GET  /docs                 - API documentation")
    print("  GET  /openapi.json         - OpenAPI schema")
    print("  GET  /api/public           - Public endpoint (rate limited)")
    print("  GET  /api/protected        - Protected endpoint (requires API key)")
    print("  GET  /api/admin            - Admin endpoint (strict rate limit)")
    print("  POST /api/process          - Data processing (requires API key)")
    print("  POST /api/upload           - File upload (strict rate limit)")
    print("  POST /api/batch            - Batch processing (very strict limit)")
    print("  GET  /api/health/secure    - Authenticated health check")
    print("  GET  /api/config           - API configuration")
    print("")
    print("Authentication:")
    print("  Use 'Authorization: Bearer <your-api-key>' header")
    print("  Or 'X-API-KEY: <your-api-key>' header")
    print("")
    print("Rate limiting is IP-based with different limits per endpoint.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
