#!/usr/bin/env python3
"""
Comprehensive Test Runner for Sync Scribe Studio API

This script runs the complete test suite including:
1. Unit tests for all components
2. Integration tests with Docker
3. Security and code quality checks
4. Health check verification

Usage:
    python tests/run_all_tests.py [--unit] [--integration] [--security] [--docker] [--coverage] [--verbose]

Options:
    --unit          Run unit tests only
    --integration   Run integration tests only  
    --security      Run security scans only
    --docker        Run Docker integration tests only
    --coverage      Generate coverage report
    --verbose       Verbose output
    --no-cleanup    Don't cleanup Docker containers after tests
    --parallel      Run tests in parallel where possible
    --env-file      Specify custom .env file for testing
"""

import os
import sys
import subprocess
import argparse
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging


# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / 'test-results' / 'test-runner.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


class TestRunner:
    """Main test runner class"""
    
    def __init__(self, args):
        self.args = args
        self.project_root = PROJECT_ROOT
        self.test_results_dir = self.project_root / 'test-results'
        self.test_results_dir.mkdir(exist_ok=True)
        
        # Test environment setup
        self.test_env = self._setup_test_environment()
        self.results = {
            'unit_tests': {},
            'integration_tests': {},
            'security_scan': {},
            'docker_tests': {},
            'overall': {'passed': False, 'start_time': time.time()}
        }
    
    def _setup_test_environment(self) -> Dict[str, str]:
        """Set up test environment variables"""
        env = os.environ.copy()
        
        # Load from custom env file if specified
        if self.args.env_file and os.path.exists(self.args.env_file):
            from dotenv import load_dotenv
            load_dotenv(self.args.env_file)
            logger.info(f"Loaded environment from {self.args.env_file}")
        
        # Set test-specific environment variables
        test_env_vars = {
            'DB_TOKEN': 'test_api_key_for_local_testing_12345678901234567890',
            'API_KEY': 'test_api_key_for_local_testing_12345678901234567890',  # For config.py compatibility
            'PYTHONUNBUFFERED': '1',
            'TESTING': '1',
            'BUILD_NUMBER': 'test-build',
            'RATE_LIMIT_DEFAULT': '100/minute',
            'LOG_LEVEL': 'DEBUG' if self.args.verbose else 'INFO',
            'LOCAL_STORAGE_PATH': '/tmp'
        }
        
        env.update(test_env_vars)
        return env
    
    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                     capture_output: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        if cwd is None:
            cwd = self.project_root
            
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=self.test_env,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0 and capture_output:
                logger.error(f"Command failed: {' '.join(cmd)}")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            raise
        except Exception as e:
            logger.error(f"Command error: {e}")
            raise
    
    def check_prerequisites(self) -> bool:
        """Check that all prerequisites are available"""
        logger.info("Checking prerequisites...")
        
        required_files = [
            'requirements.txt',
            'tests/requirements.txt',
            'Dockerfile',
            'app.py',
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False
        
        # Check Python virtual environment
        if not self._setup_virtual_environment():
            return False
        
        # Check Docker availability (if needed)
        if self.args.docker or self.args.integration:
            if not self._check_docker():
                logger.warning("Docker not available - skipping Docker tests")
                self.args.docker = False
                self.args.integration = False
        
        logger.info("✅ Prerequisites check passed")
        return True
    
    def _setup_virtual_environment(self) -> bool:
        """Set up Python virtual environment"""
        logger.info("Setting up virtual environment...")
        
        # Determine venv name based on Python version
        result = self._run_command([
            'python3', '-c', 
            'import sys; print(f"{sys.version_info.major}{sys.version_info.minor}{sys.version_info.micro}")'
        ])
        
        if result.returncode != 0:
            logger.error("Failed to get Python version")
            return False
        
        py_version = result.stdout.strip()
        venv_name = f"venv_{py_version}"
        self.venv_path = self.project_root / venv_name
        
        # Create venv if it doesn't exist
        if not self.venv_path.exists():
            logger.info(f"Creating virtual environment: {venv_name}")
            result = self._run_command(['python3', '-m', 'venv', str(self.venv_path)])
            if result.returncode != 0:
                logger.error("Failed to create virtual environment")
                return False
        
        # Install dependencies
        pip_path = self.venv_path / 'bin' / 'pip'
        if not pip_path.exists():
            pip_path = self.venv_path / 'Scripts' / 'pip.exe'  # Windows
        
        if not pip_path.exists():
            logger.error("pip not found in virtual environment")
            return False
        
        logger.info("Installing dependencies...")
        result = self._run_command([str(pip_path), 'install', '--upgrade', 'pip'])
        if result.returncode != 0:
            logger.error("Failed to upgrade pip")
            return False
        
        # Install project dependencies
        for req_file in ['requirements.txt', 'tests/requirements.txt']:
            result = self._run_command([str(pip_path), 'install', '-r', req_file])
            if result.returncode != 0:
                logger.error(f"Failed to install {req_file}")
                return False
        
        # Set up python and pytest paths
        python_path = self.venv_path / 'bin' / 'python'
        if not python_path.exists():
            python_path = self.venv_path / 'Scripts' / 'python.exe'  # Windows
        
        self.python_cmd = str(python_path)
        self.pytest_cmd = [self.python_cmd, '-m', 'pytest']
        
        logger.info(f"✅ Virtual environment ready: {venv_name}")
        return True
    
    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = self._run_command(['docker', '--version'], timeout=10)
            if result.returncode == 0:
                logger.info(f"Docker available: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("Docker not available")
        return False
    
    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        if not self.args.unit and not self.args.all:
            return True
        
        logger.info("🧪 Running unit tests...")
        start_time = time.time()
        
        test_groups = [
            ('health-endpoints', ['tests/unit/test_health_endpoints.py']),
            ('security-auth', ['tests/test_security.py', 'tests/unit/test_api_endpoints_auth.py']),
            ('api-endpoints', ['tests/unit/', '--ignore=tests/unit/test_health_endpoints.py', '--ignore=tests/unit/test_api_endpoints_auth.py'])
        ]
        
        all_passed = True
        detailed_results = {}
        
        for group_name, test_paths in test_groups:
            logger.info(f"Running {group_name} tests...")
            
            cmd = self.pytest_cmd + [
                '-v',
                '--tb=short',
                '--junit-xml', str(self.test_results_dir / f'unittest-{group_name}.xml')
            ]
            
            if self.args.coverage:
                cmd.extend(['--cov=server', '--cov=routes', '--cov-report=xml', '--cov-report=html'])
            
            if self.args.parallel:
                cmd.extend(['-n', 'auto'])
            
            cmd.extend(test_paths)
            
            result = self._run_command(cmd)
            
            detailed_results[group_name] = {
                'passed': result.returncode == 0,
                'output': result.stdout if result.stdout else '',
                'error': result.stderr if result.stderr else ''
            }
            
            if result.returncode != 0:
                all_passed = False
                logger.error(f"❌ {group_name} tests failed")
            else:
                logger.info(f"✅ {group_name} tests passed")
        
        duration = time.time() - start_time
        self.results['unit_tests'] = {
            'passed': all_passed,
            'duration': duration,
            'details': detailed_results
        }
        
        logger.info(f"Unit tests completed in {duration:.2f}s - {'PASSED' if all_passed else 'FAILED'}")
        return all_passed
    
    def run_integration_tests(self) -> bool:
        """Run integration tests (non-Docker)"""
        if not self.args.integration and not self.args.all:
            return True
        
        logger.info("🔗 Running integration tests...")
        start_time = time.time()
        
        cmd = self.pytest_cmd + [
            'tests/integration/',
            '--ignore=tests/integration/test_docker_integration.py',  # Skip Docker tests
            '-v',
            '--tb=short',
            '--junit-xml', str(self.test_results_dir / 'integration-tests.xml')
        ]
        
        if self.args.parallel:
            cmd.extend(['-n', 'auto'])
        
        result = self._run_command(cmd)
        
        duration = time.time() - start_time
        passed = result.returncode == 0
        
        self.results['integration_tests'] = {
            'passed': passed,
            'duration': duration,
            'output': result.stdout if result.stdout else '',
            'error': result.stderr if result.stderr else ''
        }
        
        status = "PASSED" if passed else "FAILED"
        logger.info(f"Integration tests completed in {duration:.2f}s - {status}")
        
        return passed
    
    def run_security_scan(self) -> bool:
        """Run security scans"""
        if not self.args.security and not self.args.all:
            return True
        
        logger.info("🔒 Running security scans...")
        start_time = time.time()
        
        security_tools = [
            (['bandit', '-r', '.', '-f', 'json', '-o', str(self.test_results_dir / 'bandit-report.json')], 'Bandit security scan'),
            (['safety', 'check', '--json', '--output', str(self.test_results_dir / 'safety-report.json')], 'Safety dependency check'),
            (['flake8', '--max-line-length=100', '--tee', '--output-file', str(self.test_results_dir / 'flake8-report.txt'), '.'], 'Code linting')
        ]
        
        all_passed = True
        detailed_results = {}
        
        for cmd_parts, description in security_tools:
            logger.info(f"Running {description}...")
            
            # Prepend python command for Python tools
            if cmd_parts[0] in ['bandit', 'safety', 'flake8']:
                cmd = [self.python_cmd, '-m'] + cmd_parts
            else:
                cmd = cmd_parts
            
            result = self._run_command(cmd)
            
            tool_name = cmd_parts[0]
            detailed_results[tool_name] = {
                'passed': result.returncode == 0,
                'output': result.stdout if result.stdout else '',
                'error': result.stderr if result.stderr else ''
            }
            
            if result.returncode != 0:
                logger.warning(f"⚠️  {description} found issues")
                # Don't fail overall for security warnings
            else:
                logger.info(f"✅ {description} passed")
        
        duration = time.time() - start_time
        self.results['security_scan'] = {
            'passed': all_passed,
            'duration': duration,
            'details': detailed_results
        }
        
        logger.info(f"Security scans completed in {duration:.2f}s")
        return True  # Don't fail on security warnings
    
    def run_docker_tests(self) -> bool:
        """Run Docker integration tests"""
        if not self.args.docker and not self.args.all:
            return True
        
        if not self._check_docker():
            logger.warning("Docker not available - skipping Docker tests")
            return True
        
        logger.info("🐳 Running Docker integration tests...")
        start_time = time.time()
        
        cmd = self.pytest_cmd + [
            'tests/integration/test_docker_integration.py',
            '-v',
            '--tb=short',
            '-s',  # Don't capture output for Docker tests
            '--junit-xml', str(self.test_results_dir / 'docker-integration-tests.xml')
        ]
        
        result = self._run_command(cmd, timeout=600)  # 10 minute timeout for Docker tests
        
        duration = time.time() - start_time
        passed = result.returncode == 0
        
        self.results['docker_tests'] = {
            'passed': passed,
            'duration': duration,
            'output': result.stdout if result.stdout else '',
            'error': result.stderr if result.stderr else ''
        }
        
        status = "PASSED" if passed else "FAILED"
        logger.info(f"Docker tests completed in {duration:.2f}s - {status}")
        
        return passed
    
    def cleanup_docker(self):
        """Clean up Docker containers and images from tests"""
        if not self.args.no_cleanup:
            logger.info("🧹 Cleaning up Docker resources...")
            
            # Clean up test containers
            test_containers = [
                "test-api-container",
                "test-missing-env", 
                "test-shutdown"
            ]
            
            for container_name in test_containers:
                try:
                    self._run_command(['docker', 'stop', container_name], timeout=10)
                    self._run_command(['docker', 'rm', container_name], timeout=10)
                except:
                    pass  # Container might not exist
            
            # Clean up dangling images
            try:
                result = self._run_command(['docker', 'images', '--filter', 'dangling=true', '-q'], timeout=10)
                if result.stdout.strip():
                    image_ids = result.stdout.strip().split('\n')
                    self._run_command(['docker', 'rmi'] + image_ids, timeout=30)
            except:
                pass
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 Generating test report...")
        
        # Calculate overall results
        total_duration = time.time() - self.results['overall']['start_time']
        
        overall_passed = all([
            self.results.get('unit_tests', {}).get('passed', True),
            self.results.get('integration_tests', {}).get('passed', True),
            self.results.get('docker_tests', {}).get('passed', True)
            # Note: security_scan doesn't fail overall
        ])
        
        self.results['overall']['passed'] = overall_passed
        self.results['overall']['duration'] = total_duration
        
        # Create summary report
        report = [
            "# Test Execution Summary",
            f"**Overall Status:** {'✅ PASSED' if overall_passed else '❌ FAILED'}",
            f"**Total Duration:** {total_duration:.2f} seconds",
            f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Test Results",
        ]
        
        for test_type, result in self.results.items():
            if test_type == 'overall':
                continue
                
            if not result:  # Skip empty results
                continue
                
            status = "✅ PASSED" if result.get('passed', False) else "❌ FAILED"
            duration = result.get('duration', 0)
            
            report.extend([
                f"### {test_type.replace('_', ' ').title()}",
                f"- Status: {status}",
                f"- Duration: {duration:.2f}s",
                ""
            ])
        
        # Save detailed results as JSON
        with open(self.test_results_dir / 'test-results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Save markdown report
        with open(self.test_results_dir / 'test-report.md', 'w') as f:
            f.write('\n'.join(report))
        
        # Print summary
        logger.info("=" * 60)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("=" * 60)
        for line in report[2:]:  # Skip header
            if line.startswith('**') or line.startswith('###') or line.startswith('- Status:'):
                logger.info(line.replace('**', '').replace('###', '').replace('- Status: ', ''))
        logger.info("=" * 60)
        logger.info(f"Detailed results: {self.test_results_dir / 'test-report.md'}")
        logger.info(f"JSON results: {self.test_results_dir / 'test-results.json'}")
    
    def run_all(self) -> bool:
        """Run all selected test suites"""
        logger.info("🚀 Starting comprehensive test suite...")
        
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites check failed")
            return False
        
        success = True
        
        try:
            # Run test suites in order
            if not self.run_unit_tests():
                success = False
            
            if not self.run_integration_tests():
                success = False
            
            if not self.run_security_scan():
                pass  # Security scans don't fail overall
            
            if not self.run_docker_tests():
                success = False
            
        finally:
            # Always cleanup and report
            self.cleanup_docker()
            self.generate_test_report()
        
        return success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive test runner for Sync Scribe Studio API")
    
    # Test suite selection
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--security', action='store_true', help='Run security scans only')
    parser.add_argument('--docker', action='store_true', help='Run Docker integration tests only')
    
    # Options
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-cleanup', action='store_true', help="Don't cleanup Docker containers")
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel where possible')
    parser.add_argument('--env-file', help='Specify custom .env file for testing')
    
    args = parser.parse_args()
    
    # If no specific suite selected, run all
    if not any([args.unit, args.integration, args.security, args.docker]):
        args.all = True
        args.unit = args.integration = args.security = args.docker = True
    else:
        args.all = False
    
    runner = TestRunner(args)
    success = runner.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
