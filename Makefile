# Makefile for CI-friendly test execution
# Provides convenient commands for running tests with proper reporting

.PHONY: help test test-smoke test-unit test-integration test-parallel test-coverage clean-reports install-test-deps

# Default target
help:
	@echo "Available test commands:"
	@echo ""
	@echo "  make test              - Run all tests with default settings"
	@echo "  make test-smoke        - Run smoke tests only (quick validation)"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-parallel     - Run all tests in parallel"
	@echo "  make test-coverage     - Run tests with strict coverage (80%)"
	@echo "  make test-ci           - Run tests in CI mode (full suite, strict)"
	@echo "  make clean-reports     - Clean up test report files"
	@echo "  make install-test-deps - Install testing dependencies"
	@echo ""
	@echo "Environment variables:"
	@echo "  COVERAGE_THRESHOLD - Set minimum coverage (default: 70)"
	@echo "  CI                - Set to enable CI mode output"

# Install test dependencies
install-test-deps:
	@echo "Installing test dependencies..."
	pip install pytest pytest-cov pytest-html pytest-xdist pytest-timeout pytest-env

# Run all tests with default configuration
test:
	@echo "Running all tests..."
	@python scripts/run_tests_ci.py --suite full

# Run smoke tests for quick validation
test-smoke:
	@echo "Running smoke tests..."
	@./scripts/ci-test.sh -s smoke

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	@./scripts/ci-test.sh -s unit

# Run integration tests only
test-integration:
	@echo "Running integration tests..."
	@./scripts/ci-test.sh -s integration

# Run tests in parallel
test-parallel:
	@echo "Running tests in parallel..."
	@./scripts/ci-test.sh -p

# Run tests with strict coverage requirements
test-coverage:
	@echo "Running tests with 80% coverage requirement..."
	@./scripts/ci-test.sh -c 80

# CI mode - full test suite with strict settings
test-ci:
	@echo "Running tests in CI mode..."
	@CI=1 ./scripts/ci-test.sh -s full -c 70

# Clean up test reports
clean-reports:
	@echo "Cleaning test reports..."
	@rm -rf test-reports/
	@rm -rf htmlcov/
	@rm -f test-results.xml
	@rm -f test-report.html
	@rm -f coverage.xml
	@rm -f coverage.json
	@rm -f .coverage
	@echo "Test reports cleaned."

# Generate test report summary (after running tests)
report-summary:
	@if [ -d "test-reports" ]; then \
		echo "Test Report Summary:"; \
		echo "=================="; \
		ls -la test-reports/*.xml 2>/dev/null || echo "No XML reports found"; \
		ls -la test-reports/*.html 2>/dev/null || echo "No HTML reports found"; \
		ls -la test-reports/*.json 2>/dev/null || echo "No JSON reports found"; \
	else \
		echo "No test reports found. Run tests first."; \
	fi
