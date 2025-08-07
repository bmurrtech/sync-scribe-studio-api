# Sync Scribe Studio API - Test Suite

This directory contains the comprehensive test suite for the Sync Scribe Studio API, including unit tests, integration tests, security scans, and Docker integration tests.

## Overview

The test suite provides:

- 🧪 **Unit Tests**: Fast, isolated tests for individual components
- 🔗 **Integration Tests**: End-to-end tests with real API interactions
- 🐳 **Docker Integration Tests**: Full container lifecycle testing
- 🔒 **Security Scans**: Code quality and security vulnerability checks
- 📊 **Coverage Reports**: Code coverage analysis and reporting

## Quick Start

### Run All Tests
```bash
# From project root
./run_tests.sh

# Or directly with Python
python tests/run_all_tests.py
```

### Run Specific Test Suites
```bash
# Unit tests only
./run_tests.sh --unit

# Integration tests only
./run_tests.sh --integration

# Docker tests only
./run_tests.sh --docker

# Security scans only
./run_tests.sh --security

# With coverage report
./run_tests.sh --coverage

# Verbose output
./run_tests.sh --verbose

# Run tests in parallel (faster)
./run_tests.sh --parallel
```

## Test Structure

```
tests/
├── README.md                              # This file
├── requirements.txt                       # Test dependencies
├── run_all_tests.py                      # Comprehensive test runner
├── conftest.py                           # Pytest configuration and fixtures
│
├── unit/                                 # Unit tests
│   ├── test_health_endpoints.py         # Health check endpoint tests
│   └── test_api_endpoints_auth.py       # API authentication/rate limiting tests
│
├── integration/                          # Integration tests
│   ├── test_flask_node_integration.py   # Flask-Node microservice tests
│   └── test_docker_integration.py       # Docker container lifecycle tests
│
└── test_security.py                     # Security component tests
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests that don't require external dependencies:

- **Health Endpoints** (`test_health_endpoints.py`)
  - Basic health check functionality
  - Detailed health status reporting
  - Root endpoint service information
  - Health check decorators and utilities

- **API Authentication & Rate Limiting** (`test_api_endpoints_auth.py`)
  - API key authentication (Bearer token, X-API-KEY header)
  - Rate limiting per IP and time windows
  - Security headers validation
  - Error handling and logging
  - Authentication decorator behavior

### Integration Tests (`tests/integration/`)

Full-stack tests that use real API interactions:

- **Flask-Node Integration** (`test_flask_node_integration.py`)
  - Multi-service communication testing
  - YouTube API endpoint testing
  - Queue processing and concurrency
  - Error handling across services
  - Performance and streaming tests

- **Docker Integration** (`test_docker_integration.py`)
  - Full Docker container lifecycle
  - Container startup with environment variables
  - Health check validation inside containers
  - Authenticated endpoint testing
  - Resource usage and monitoring
  - Graceful shutdown testing

### Security Tests (`test_security.py`)

Security-focused tests for authentication and rate limiting:

- API key validation and security
- Rate limiting implementation
- Security middleware setup
- Authentication decorator behavior
- Integration between auth and rate limiting components

## Environment Configuration

### Test Environment Variables

The test suite uses these environment variables:

```bash
# Authentication
DB_TOKEN=test_api_key_for_local_testing_12345678901234567890

# General settings
TESTING=1
PYTHONUNBUFFERED=1
BUILD_NUMBER=test-build
RATE_LIMIT_DEFAULT=100/minute
LOG_LEVEL=INFO  # or DEBUG for verbose output
```

### Custom Environment Files

You can specify a custom `.env` file for testing:

```bash
./run_tests.sh --env-file .env.test
```

## Docker Testing

The Docker integration tests require Docker to be installed and running:

### Prerequisites
- Docker Engine installed and running
- `docker` command available in PATH
- Sufficient disk space for building images

### Docker Test Features
- **Image Building**: Validates Dockerfile and builds test images
- **Container Lifecycle**: Tests startup, readiness, and shutdown
- **Health Checks**: Validates `/health` endpoints inside containers
- **Authentication**: Tests API key validation in containerized environment
- **Environment Variables**: Tests configuration through Docker environment
- **Resource Monitoring**: Checks container resource usage
- **Cleanup**: Automatic cleanup of test containers and images

## CI/CD Integration

The test suite is designed to work in CI/CD environments:

### GitHub Actions

The provided CI/CD workflow (`.github/workflows/api-ci-cd.yml`) includes:

- **Unit Test Jobs**: Separate jobs for different test groups
- **Security Scanning**: Automated security and code quality checks
- **Docker Integration**: Full container testing in CI environment
- **Coverage Reporting**: Code coverage analysis and artifact upload
- **Parallel Execution**: Fast test execution with parallel jobs

### Environment Variables in CI

```yaml
env:
  DB_TOKEN: ${{ secrets.DB_TOKEN || 'test_api_key_for_ci' }}
  TESTING: '1'
  BUILD_NUMBER: ${{ github.run_number }}
```

## Coverage Reports

### Generating Coverage

```bash
# Generate HTML and XML coverage reports
./run_tests.sh --coverage

# Coverage reports will be in:
# - htmlcov/index.html (HTML report)
# - coverage.xml (XML for CI)
```

### Coverage Targets

The test suite aims for:
- **Unit Tests**: >90% coverage
- **Integration Tests**: Critical path coverage
- **Overall**: >85% combined coverage

## Development Workflow

### Running Tests During Development

```bash
# Quick unit tests (fastest feedback)
./run_tests.sh --unit

# Test specific file
python -m pytest tests/unit/test_health_endpoints.py -v

# Test with coverage for specific module
python -m pytest tests/unit/test_api_endpoints_auth.py --cov=server.security -v

# Debug failing test
python -m pytest tests/integration/test_docker_integration.py::TestDockerIntegration::test_health_endpoint -v -s
```

### Adding New Tests

1. **Unit Tests**: Add to appropriate `tests/unit/test_*.py` file
2. **Integration Tests**: Add to `tests/integration/test_*.py`
3. **Fixtures**: Add shared fixtures to `conftest.py`
4. **Test Data**: Create test data files in `tests/data/` if needed

### Test Best Practices

- **Fast Tests**: Keep unit tests under 100ms each
- **Isolated Tests**: Don't depend on external services in unit tests
- **Clear Names**: Use descriptive test method names
- **Arrange-Act-Assert**: Follow AAA pattern
- **Mock External**: Mock external APIs and services
- **Clean Up**: Always clean up resources (containers, files, etc.)

## Debugging

### Common Issues

1. **Docker Tests Failing**
   - Check Docker is running: `docker --version`
   - Check port availability: `lsof -i :8080`
   - Clean up containers: `docker container prune -f`

2. **Permission Errors**
   - Make scripts executable: `chmod +x run_tests.sh`
   - Check file permissions in test directory

3. **Import Errors**
   - Check virtual environment: `which python3`
   - Verify dependencies: `pip list | grep pytest`

4. **Port Conflicts**
   - Tests automatically find available ports
   - Check for services on ports 8080-8090

### Debugging Commands

```bash
# Check test environment
python tests/run_all_tests.py --verbose --unit

# Run single test with full output
python -m pytest tests/integration/test_docker_integration.py::TestDockerLifecycle::test_container_startup -v -s

# Check Docker resources
docker ps -a
docker images | grep test

# Clean up test artifacts
rm -rf test-results/
docker container prune -f
docker image prune -f
```

## Performance

### Test Performance Targets

- **Unit Tests**: Complete in <30 seconds
- **Integration Tests**: Complete in <2 minutes
- **Docker Tests**: Complete in <5 minutes
- **Security Scans**: Complete in <1 minute
- **Full Suite**: Complete in <10 minutes

### Optimization Tips

- Use `--parallel` for faster execution
- Run unit tests first for faster feedback
- Use `--no-cleanup` for debugging (skip Docker cleanup)
- Cache virtual environments between runs

## Reporting

### Test Results

All test results are saved in the `test-results/` directory:

```
test-results/
├── test-runner.log                    # Full test runner log
├── test-results.json                  # Machine-readable results
├── test-report.md                     # Human-readable summary
├── unittest-*.xml                     # JUnit XML for CI
├── integration-tests.xml              # Integration test results
├── docker-integration-tests.xml       # Docker test results
├── bandit-report.json                 # Security scan results
├── safety-report.json                 # Dependency scan results
├── flake8-report.txt                  # Code style report
├── coverage.xml                       # Coverage XML report
└── htmlcov/                          # HTML coverage report
```

### CI Integration

The test results integrate with CI systems:

- **GitHub Actions**: Automatic artifact upload
- **Coverage**: Codecov/Coveralls integration
- **Security**: SARIF format for GitHub Security tab
- **JUnit**: Test result visualization in CI

## Contributing

When adding new functionality:

1. Write tests first (TDD approach)
2. Ensure >90% test coverage for new code
3. Add both unit and integration tests
4. Update this README if adding new test categories
5. Verify all tests pass: `./run_tests.sh`

For questions or issues with the test suite, please check the existing tests for examples or create an issue with detailed reproduction steps.

---

**Happy Testing!** 🧪✅
