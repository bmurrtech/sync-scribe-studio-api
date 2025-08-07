#!/bin/bash

# Sync Scribe Studio API - Test Runner Wrapper
# This script provides a convenient way to run all tests with proper environment setup

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Sync Scribe Studio API - Test Suite Runner"
echo "Project Root: $PROJECT_ROOT"
echo "================================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Create test-results directory if it doesn't exist
mkdir -p test-results

# Set default environment variables for testing
export DB_TOKEN="${DB_TOKEN:-test_api_key_for_local_testing_12345678901234567890}"
export API_KEY="${API_KEY:-test_api_key_for_local_testing_12345678901234567890}"
export PYTHONUNBUFFERED=1
export TESTING=1
export BUILD_NUMBER="${BUILD_NUMBER:-test-build}"
export RATE_LIMIT_DEFAULT="${RATE_LIMIT_DEFAULT:-100/minute}"
export LOCAL_STORAGE_PATH="${LOCAL_STORAGE_PATH:-/tmp}"

# Run the Python test runner with all arguments passed through
echo "🔧 Starting test runner..."
python3 tests/run_all_tests.py "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All tests completed successfully!"
    echo "📊 Test results available in: test-results/"
else
    echo ""
    echo "❌ Some tests failed. Check the logs for details."
    echo "📊 Test results available in: test-results/"
fi

exit $exit_code
