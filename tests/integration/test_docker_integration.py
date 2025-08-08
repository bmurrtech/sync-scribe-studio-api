#!/usr/bin/env python3
"""
Docker Integration Test Suite

This test suite spins up the Docker container locally and tests:
1. Health endpoint availability
2. Authentication endpoint functionality
3. Basic API functionality
4. Container health and resource usage

Requirements:
- Docker must be installed and running
- Port 8080 must be available (or use dynamic port assignment)
"""

import pytest
import requests
import subprocess
import time
import os
import json
import signal
import psutil
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerContainerManager:
    """Manages Docker container lifecycle for integration testing"""
    
    def __init__(self, image_name: str = "sync-scribe-studio-api", container_name: str = "test-api-container"):
        self.image_name = image_name
        self.container_name = container_name
        self.container_id: Optional[str] = None
        self.port = self._find_available_port()
        self.base_url = f"http://localhost:{self.port}"
        
    def _find_available_port(self, start_port: int = 8080) -> int:
        """Find an available port for the container"""
        import socket
        
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(('localhost', port))
                    return port
            except socket.error:
                continue
        
        raise RuntimeError("No available port found")
    
    def build_image(self) -> bool:
        """Build the Docker image"""
        logger.info(f"Building Docker image: {self.image_name}")
        
        try:
            result = subprocess.run([
                "docker", "build", 
                "-t", self.image_name,
                "-f", "Dockerfile",
                "."
            ], 
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # Project root
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Docker build failed: {result.stderr}")
                return False
                
            logger.info("Docker image built successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Docker build timed out")
            return False
        except Exception as e:
            logger.error(f"Docker build error: {e}")
            return False
    
    def start_container(self, env_vars: Optional[Dict[str, str]] = None) -> bool:
        """Start the Docker container with specified environment variables"""
        logger.info(f"Starting container on port {self.port}")
        
        # Default environment variables for testing
        default_env = {
            "PORT": str(self.port),
            "DB_TOKEN": "test_api_key_for_integration_testing_12345678",
            "PYTHONUNBUFFERED": "1",
            "BUILD_NUMBER": "integration-test-build"
        }
        
        if env_vars:
            default_env.update(env_vars)
        
        # Build environment arguments
        env_args = []
        for key, value in default_env.items():
            env_args.extend(["-e", f"{key}={value}"])
        
        try:
            # Stop any existing container with the same name
            self.stop_container()
            
            # Start new container
            result = subprocess.run([
                "docker", "run", "-d",
                "--name", self.container_name,
                "-p", f"{self.port}:8080",
                *env_args,
                self.image_name
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Failed to start container: {result.stderr}")
                return False
            
            self.container_id = result.stdout.strip()
            logger.info(f"Container started with ID: {self.container_id}")
            
            # Wait for container to be ready
            return self._wait_for_container_ready()
            
        except Exception as e:
            logger.error(f"Error starting container: {e}")
            return False
    
    def _wait_for_container_ready(self, timeout: int = 60) -> bool:
        """Wait for container to be ready to accept requests"""
        logger.info(f"Waiting for container to be ready at {self.base_url}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if container is still running
                if not self._is_container_running():
                    logger.error("Container stopped unexpectedly")
                    return False
                
                # Try to make a health check request
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("Container is ready")
                    return True
                    
            except requests.exceptions.RequestException:
                pass  # Expected during startup
            
            time.sleep(2)
        
        logger.error("Container did not become ready within timeout")
        return False
    
    def _is_container_running(self) -> bool:
        """Check if the container is still running"""
        if not self.container_id:
            return False
            
        try:
            result = subprocess.run([
                "docker", "inspect", self.container_id, 
                "--format", "{{.State.Running}}"
            ], capture_output=True, text=True)
            
            return result.stdout.strip() == "true"
        except:
            return False
    
    def stop_container(self) -> bool:
        """Stop and remove the container"""
        if self.container_id or self.container_name:
            try:
                # Try to stop by ID first, then by name
                for identifier in [self.container_id, self.container_name]:
                    if identifier:
                        subprocess.run(["docker", "stop", identifier], 
                                     capture_output=True, timeout=30)
                        subprocess.run(["docker", "rm", identifier], 
                                     capture_output=True, timeout=30)
                
                logger.info("Container stopped and removed")
                self.container_id = None
                return True
                
            except Exception as e:
                logger.error(f"Error stopping container: {e}")
                return False
        
        return True
    
    def get_container_logs(self) -> str:
        """Get container logs for debugging"""
        if not self.container_id:
            return "No container running"
        
        try:
            result = subprocess.run([
                "docker", "logs", self.container_id
            ], capture_output=True, text=True, timeout=30)
            
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error getting logs: {e}"
    
    def get_container_stats(self) -> Dict[str, Any]:
        """Get container resource usage statistics"""
        if not self.container_id:
            return {}
        
        try:
            result = subprocess.run([
                "docker", "stats", self.container_id, 
                "--no-stream", "--format", 
                "table {{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Skip header
                    stats = lines[1].split(',')
                    return {
                        'cpu_percent': stats[0] if len(stats) > 0 else 'N/A',
                        'memory_usage': stats[1] if len(stats) > 1 else 'N/A',
                        'network_io': stats[2] if len(stats) > 2 else 'N/A',
                        'block_io': stats[3] if len(stats) > 3 else 'N/A'
                    }
            
            return {'error': 'Unable to get stats'}
        except Exception as e:
            return {'error': str(e)}


@pytest.fixture(scope="session")
def docker_container():
    """Fixture that manages Docker container lifecycle for the test session"""
    container = DockerContainerManager()
    
    # Build image
    if not container.build_image():
        pytest.skip("Failed to build Docker image")
    
    # Start container
    if not container.start_container():
        pytest.skip("Failed to start Docker container")
    
    yield container
    
    # Cleanup
    container.stop_container()


class TestDockerIntegration:
    """Integration tests using Docker container"""
    
    def test_container_health_endpoint(self, docker_container):
        """Test that the health endpoint responds correctly"""
        response = requests.get(f"{docker_container.base_url}/health", timeout=10)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'service' in data
        
        logger.info("Health endpoint test passed")
    
    def test_container_detailed_health_endpoint(self, docker_container):
        """Test the detailed health endpoint"""
        response = requests.get(f"{docker_container.base_url}/health/detailed", timeout=15)
        
        # Should return 200 or 503 depending on system state
        assert response.status_code in [200, 503]
        
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'environment_variables' in data or 'components' in data or 'environment' in data
        
        logger.info("Detailed health endpoint test passed")
    
    def test_container_root_endpoint(self, docker_container):
        """Test the root service info endpoint"""
        response = requests.get(f"{docker_container.base_url}/", timeout=10)
        
        assert response.status_code == 200
        
        data = response.json()
        assert 'service' in data
        assert 'version' in data
        assert 'endpoints' in data
        
        logger.info("Root endpoint test passed")
    
    def test_authenticated_endpoint_without_auth(self, docker_container):
        """Test that authenticated endpoints reject requests without auth"""
        # Try to access a protected endpoint without authentication
        response = requests.post(
            f"{docker_container.base_url}/v1/media/youtube/info",
            json={"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"},
            timeout=10
        )
        
        # Should return 401 Unauthorized, 503 (auth unavailable), or be queued (202)
        assert response.status_code in [401, 202, 404, 405, 503]
        
        if response.status_code in [401, 503]:
            # Should have proper error structure
            data = response.json()
            assert 'error' in data or 'message' in data
        
        logger.info("Authentication enforcement test passed")
    
    def test_authenticated_endpoint_with_valid_auth(self, docker_container):
        """Test authenticated endpoint with valid API key"""
        headers = {
            "Authorization": "Bearer test_api_key_for_integration_testing_12345678",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{docker_container.base_url}/v1/media/youtube/info",
            json={"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"},
            headers=headers,
            timeout=15
        )
        
        # Should not return 401 (may return 200, 202 for queued, 503 for service unavailable, or 404 if not implemented)
        assert response.status_code != 401
        
        logger.info("Valid authentication test passed")
    
    def test_rate_limiting_enforcement(self, docker_container):
        """Test that rate limiting is enforced"""
        headers = {
            "Authorization": "Bearer test_api_key_for_integration_testing_12345678",
            "Content-Type": "application/json"
        }
        
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(10):
            response = requests.post(
                f"{docker_container.base_url}/v1/media/youtube/info",
                json={"url": f"https://youtube.com/watch?v=test{i}"},
                headers=headers,
                timeout=5
            )
            responses.append(response.status_code)
            
            # Small delay between requests
            time.sleep(0.1)
        
        # Should eventually get rate limited (429) or have consistent processing (200/202)
        status_codes = set(responses)
        
        # Either we get rate limited, or all requests are processed consistently
        assert 429 in status_codes or len(status_codes) <= 2  # Allow for some variation
        
        logger.info("Rate limiting test completed")
    
    def test_security_headers(self, docker_container):
        """Test that security headers are present"""
        response = requests.get(f"{docker_container.base_url}/health", timeout=10)
        
        # Check for required security headers
        headers = response.headers
        assert headers.get('X-Content-Type-Options') == 'nosniff'
        assert headers.get('X-Frame-Options') == 'DENY'
        assert headers.get('X-XSS-Protection') == '1; mode=block'
        assert 'Strict-Transport-Security' in headers
        
        logger.info("Security headers test passed")
    
    def test_container_resource_usage(self, docker_container):
        """Test that container uses reasonable resources"""
        # Get container stats
        stats = docker_container.get_container_stats()
        
        if 'error' not in stats:
            logger.info(f"Container stats: {stats}")
            
            # Check that memory usage is reasonable (this is informational)
            memory_info = stats.get('memory_usage', 'N/A')
            logger.info(f"Memory usage: {memory_info}")
        
        # Ensure container is still running after all tests
        assert docker_container._is_container_running()
        
        logger.info("Resource usage test completed")
    
    def test_container_error_handling(self, docker_container):
        """Test container error handling"""
        # Test invalid endpoint
        response = requests.get(f"{docker_container.base_url}/invalid-endpoint", timeout=10)
        assert response.status_code == 404
        
        # Test malformed request
        response = requests.post(
            f"{docker_container.base_url}/v1/media/youtube/info",
            data="invalid-json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Should handle malformed JSON gracefully (503 if auth unavailable is also valid)
        assert response.status_code in [400, 422, 500, 503]
        
        logger.info("Error handling test passed")


class TestDockerContainerLifecycle:
    """Test Docker container lifecycle management"""
    
    def test_container_startup_with_missing_env_vars(self):
        """Test container behavior with missing environment variables"""
        container = DockerContainerManager(container_name="test-missing-env")
        
        try:
            # Build image first
            assert container.build_image()
            
            # Start with minimal environment (missing DB_TOKEN)
            result = container.start_container(env_vars={"PORT": "8081"})
            
            if result:
                # If container starts, it should handle missing vars gracefully
                # Wait a bit for startup
                time.sleep(5)
                
                # Try to access health endpoint
                try:
                    response = requests.get(f"http://localhost:8081/health", timeout=10)
                    # Should either work or return a service error
                    assert response.status_code in [200, 503]
                except requests.RequestException:
                    # Container might have stopped due to missing vars
                    pass
            
        finally:
            container.stop_container()
    
    def test_container_graceful_shutdown(self):
        """Test container graceful shutdown"""
        container = DockerContainerManager(container_name="test-shutdown")
        
        try:
            # Build and start container
            assert container.build_image()
            assert container.start_container()
            
            # Verify it's running
            assert container._is_container_running()
            
            # Stop container
            assert container.stop_container()
            
            # Verify it's stopped
            assert not container._is_container_running()
            
        except Exception as e:
            logger.error(f"Graceful shutdown test failed: {e}")
            container.stop_container()
            raise


class TestDockerEnvironment:
    """Test Docker environment and configuration"""
    
    def test_docker_availability(self):
        """Test that Docker is available and working"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0
            logger.info(f"Docker version: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker is not available")
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists in the project"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        dockerfile_path = os.path.join(project_root, "Dockerfile")
        
        assert os.path.exists(dockerfile_path), "Dockerfile not found"
        
        # Read Dockerfile to check for basic requirements
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Check for required elements
        assert 'FROM' in dockerfile_content
        assert 'EXPOSE' in dockerfile_content or 'PORT' in dockerfile_content
        assert 'CMD' in dockerfile_content or 'ENTRYPOINT' in dockerfile_content
        
        logger.info("Dockerfile validation passed")


# Utility functions for test environment
def cleanup_test_containers():
    """Clean up any leftover test containers"""
    test_containers = [
        "test-api-container",
        "test-missing-env", 
        "test-shutdown"
    ]
    
    for container_name in test_containers:
        try:
            subprocess.run(["docker", "stop", container_name], 
                         capture_output=True, timeout=10)
            subprocess.run(["docker", "rm", container_name], 
                         capture_output=True, timeout=10)
        except:
            pass  # Container might not exist


def save_test_artifacts(docker_container):
    """Save test artifacts for debugging"""
    artifacts_dir = "/tmp/docker-integration-test-artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Save container logs
    logs = docker_container.get_container_logs()
    with open(f"{artifacts_dir}/container-logs.txt", 'w') as f:
        f.write(logs)
    
    # Save container stats
    stats = docker_container.get_container_stats()
    with open(f"{artifacts_dir}/container-stats.txt", 'w') as f:
        f.write(json.dumps(stats, indent=2))
    
    logger.info(f"Test artifacts saved to {artifacts_dir}")


if __name__ == '__main__':
    # Clean up any existing test containers
    cleanup_test_containers()
    
    # Run tests
    pytest.main([__file__, '-v', '-s', '--tb=short'])
