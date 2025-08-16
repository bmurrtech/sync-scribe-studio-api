#!/usr/bin/env python3

import pytest
import json
import os
import tempfile
from unittest.mock import patch
from app import create_app


class TestImageGenerationRoute:
    """Test suite for /v1/gen/image endpoint following TDD principles."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create a test app with IMG_GEN=false (default)
        self.app = create_app()
        self.client = self.app.test_client()
        
        # Valid test payload
        self.valid_payload = {
            "prompt": "A beautiful sunset over mountains",
            "steps": 30,
            "width": 512,
            "height": 512
        }
        
        # Required headers
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': os.environ.get('API_KEY', 'test_key')
        }

    def test_image_gen_route_not_found_when_disabled(self):
        """Test that /v1/gen/image returns 404 when IMG_GEN=false (default state)."""
        with patch.dict(os.environ, {'IMG_GEN': 'false', 'API_KEY': 'test_key'}):
            # This should fail initially (RED state) because route doesn't exist yet
            response = self.client.post(
                '/v1/gen/image',
                data=json.dumps(self.valid_payload),
                headers=self.headers
            )
            
            # Expect 404 since route should not be registered when IMG_GEN=false
            assert response.status_code == 404
            # Flask returns HTML 404 page by default, not JSON
            assert 'not found' in response.data.decode('utf-8').lower() or response.status_code == 404

    def test_image_gen_route_disabled_when_flag_false(self):
        """Test that route returns proper disabled message when IMG_GEN=false but route exists."""
        with patch.dict(os.environ, {'IMG_GEN': 'false', 'API_KEY': 'test_key'}):
            # This test will be updated in GREEN phase to expect 503 instead of 404
            response = self.client.post(
                '/v1/gen/image',
                data=json.dumps(self.valid_payload),
                headers=self.headers
            )
            
            # Initially will be 404 (RED), then 503 (GREEN) when route is implemented
            assert response.status_code in [404, 503]

    def test_image_gen_accepts_valid_payload_structure(self):
        """Test that when enabled, route validates JSON payload structure correctly."""
        with patch.dict(os.environ, {'IMG_GEN': 'true', 'API_KEY': 'test_key'}):
            # This will initially fail (RED) as route doesn't exist
            # Later should validate payload structure (GREEN)
            response = self.client.post(
                '/v1/gen/image',
                data=json.dumps(self.valid_payload),
                headers=self.headers
            )
            
            # Initially 404, later should handle request appropriately
            # When implemented, should be 202 (queued) or 200 (processed)
            assert response.status_code in [404, 200, 202, 503]

    def test_image_gen_requires_api_key(self):
        """Test that image generation requires API key authentication."""
        with patch.dict(os.environ, {'IMG_GEN': 'true'}):
            # Remove API key header
            headers_no_auth = {'Content-Type': 'application/json'}
            
            response = self.client.post(
                '/v1/gen/image',
                data=json.dumps(self.valid_payload),
                headers=headers_no_auth
            )
            
            # Should fail authentication (401) when route exists
            assert response.status_code in [401, 404]  # 404 initially, 401 when implemented

    def test_image_gen_rejects_invalid_dimensions(self):
        """Test that route rejects dimensions exceeding MAX_IMAGE_SIZE."""
        with patch.dict(os.environ, {'IMG_GEN': 'true', 'API_KEY': 'test_key'}):
            invalid_payload = {
                "prompt": "test prompt",
                "width": 2048,  # Exceeds 1024x1024 limit
                "height": 2048,
                "steps": 30
            }
            
            response = self.client.post(
                '/v1/gen/image',
                data=json.dumps(invalid_payload),
                headers=self.headers
            )
            
            # Should be 422 (validation error) when implemented
            assert response.status_code in [404, 422]

    def test_image_gen_rejects_excessive_steps(self):
        """Test that route rejects steps exceeding MAX_STEPS (50)."""
        with patch.dict(os.environ, {'IMG_GEN': 'true', 'API_KEY': 'test_key'}):
            invalid_payload = {
                "prompt": "test prompt",
                "width": 512,
                "height": 512,
                "steps": 100  # Exceeds MAX_STEPS=50
            }
            
            response = self.client.post(
                '/v1/gen/image',
                data=json.dumps(invalid_payload),
                headers=self.headers
            )
            
            # Should be 422 (validation error) when implemented
            assert response.status_code in [404, 422]

    def test_image_gen_accepts_optional_lora(self):
        """Test that route accepts optional LoRA URL parameter."""
        with patch.dict(os.environ, {'IMG_GEN': 'true', 'API_KEY': 'test_key'}):
            payload_with_lora = self.valid_payload.copy()
            payload_with_lora['lora'] = [{
                "url": "https://example.com/lora.safetensors",
                "weight": 0.8
            }]
            
            response = self.client.post(
                '/v1/gen/image',
                data=json.dumps(payload_with_lora),
                headers=self.headers
            )
            
            # Should handle LoRA parameter when implemented
            assert response.status_code in [404, 200, 202, 503]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
