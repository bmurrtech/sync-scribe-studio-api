"""
OpenAPI Configuration Module
Provides dynamic OpenAPI schema generation with security schemes and rate limiting.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from flask import Flask, jsonify, Blueprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Create OpenAPI blueprint
openapi_bp = Blueprint('openapi', __name__)

def get_openapi_schema(app: Flask) -> Dict[str, Any]:
    """Generate dynamic OpenAPI schema with security configuration"""
    
    # Base OpenAPI schema
    openapi_schema = {
        "openapi": "3.0.2",
        "info": {
            "title": "SyncScribeStudio API",
            "description": "AI-powered transcription and content processing API with FastAPI-compatible authentication",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@syncscribestudio.com"
            },
            "license": {
                "name": "GPL v2",
                "url": "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html"
            }
        },
        "servers": get_server_list(),
        "components": {
            "securitySchemes": {
                "HTTPBearer": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "API-Key",
                    "description": "Enter your API token in the format: Bearer <your-token>"
                },
                "APIKeyHeader": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-KEY",
                    "description": "API key passed in X-API-KEY header"
                }
            },
            "responses": {
                "UnauthorizedError": {
                    "description": "Authentication information is missing or invalid",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"},
                                    "message": {"type": "string"}
                                }
                            }
                        }
                    },
                    "headers": {
                        "WWW-Authenticate": {
                            "description": "Authentication challenge",
                            "schema": {"type": "string"}
                        }
                    }
                },
                "RateLimitError": {
                    "description": "Rate limit exceeded",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"},
                                    "message": {"type": "string"},
                                    "retry_after": {"type": "integer"}
                                }
                            }
                        }
                    },
                    "headers": {
                        "Retry-After": {
                            "description": "Seconds to wait before retrying",
                            "schema": {"type": "integer"}
                        }
                    }
                }
            }
        },
        "paths": generate_paths(app),
        "tags": get_api_tags()
    }
    
    return openapi_schema

def get_server_list() -> List[Dict[str, str]]:
    """Generate dynamic server list for OpenAPI schema"""
    servers = [
        {
            "url": "http://localhost:5000",
            "description": "Local development server"
        }
    ]
    
    # Add production server if URL is available
    prod_url = os.getenv('PRODUCTION_URL')
    if prod_url:
        servers.insert(0, {
            "url": prod_url,
            "description": "Production server"
        })
    
    # Add staging server if URL is available
    staging_url = os.getenv('STAGING_URL')
    if staging_url:
        servers.insert(-1, {
            "url": staging_url,
            "description": "Staging server"
        })
    
    return servers

def generate_paths(app: Flask) -> Dict[str, Any]:
    """Generate OpenAPI paths from Flask routes"""
    paths = {}
    
    # Health endpoints
    paths["/"] = {
        "get": {
            "tags": ["Health"],
            "summary": "Service Information",
            "description": "Get service information, key endpoints, and documentation links",
            "responses": {
                "200": {
                    "description": "Service information",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "service": {"type": "string"},
                                    "version": {"type": "string"},
                                    "description": {"type": "string"},
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "endpoints": {"type": "object"},
                                    "authentication": {"type": "object"},
                                    "rate_limiting": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    paths["/health"] = {
        "get": {
            "tags": ["Health"],
            "summary": "Basic Health Check",
            "description": "Returns basic service health status",
            "responses": {
                "200": {
                    "description": "Service is healthy",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "service": {"type": "string"},
                                    "version": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "503": {
                    "description": "Service is unhealthy",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "error": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    paths["/health/detailed"] = {
        "get": {
            "tags": ["Health"],
            "summary": "Detailed Health Check",
            "description": "Returns comprehensive system health with component status",
            "responses": {
                "200": {
                    "description": "Detailed health information",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "service": {"type": "string"},
                                    "version": {"type": "string"},
                                    "components": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Protected endpoint example
    paths["/api/protected"] = {
        "get": {
            "tags": ["API"],
            "summary": "Protected Endpoint Example",
            "description": "Example of a protected endpoint requiring API key authentication",
            "security": [
                {"HTTPBearer": []},
                {"APIKeyHeader": []}
            ],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "authenticated": {"type": "boolean"}
                                }
                            }
                        }
                    }
                },
                "401": {"$ref": "#/components/responses/UnauthorizedError"},
                "429": {"$ref": "#/components/responses/RateLimitError"}
            }
        }
    }
    
    return paths

def get_api_tags() -> List[Dict[str, str]]:
    """Define API tags for organization"""
    return [
        {
            "name": "Health",
            "description": "Health check and monitoring endpoints"
        },
        {
            "name": "API", 
            "description": "Core API endpoints"
        },
        {
            "name": "Authentication",
            "description": "Authentication and authorization endpoints"
        }
    ]

@openapi_bp.route('/openapi.json', methods=['GET'])
def get_openapi_json():
    """OpenAPI schema endpoint with rate limiting"""
    from server.security import rate_limit
    
    @rate_limit("10/minute")  # Rate limit OpenAPI endpoint
    def generate_schema():
        from flask import current_app
        schema = get_openapi_schema(current_app)
        return jsonify(schema)
    
    return generate_schema()

@openapi_bp.route('/docs', methods=['GET'])
def swagger_ui():
    """Swagger UI documentation endpoint"""
    swagger_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SyncScribeStudio API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
        <style>
            html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin:0; background: #fafafa; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                });
            };
        </script>
    </body>
    </html>
    """
    return swagger_html

def register_openapi_endpoints(app: Flask):
    """Register OpenAPI endpoints with Flask app"""
    app.register_blueprint(openapi_bp)
    logger.info("OpenAPI endpoints registered: /openapi.json, /docs")

# Export main components
__all__ = [
    'openapi_bp',
    'register_openapi_endpoints',
    'get_openapi_schema',
    'get_server_list',
    'generate_paths'
]
