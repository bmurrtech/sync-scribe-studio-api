#!/bin/bash

# CI Test Runner Script
# Provides simple interface for running tests in CI/CD pipelines
# Returns proper exit codes for pipeline integration

set -e  # Exit on error

# Colors for output (disabled in CI environments)
if [ -t 1 ] && [ -z "${CI}" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Default values
TEST_SUITE="full"
COVERAGE_THRESHOLD=70
PARALLEL=false
VERBOSE=false

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -s, --suite SUITE      Test suite to run (smoke|unit|integration|full) [default: full]"
    echo "  -c, --coverage NUM     Minimum coverage threshold percentage [default: 70]"
    echo "  -p, --parallel         Run tests in parallel"
    echo "  -v, --verbose          Enable verbose output"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 -s unit           # Run only unit tests"
    echo "  $0 -s smoke -p       # Run smoke tests in parallel"
    echo "  $0 -c 80             # Run all tests with 80% coverage requirement"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--suite)
            TEST_SUITE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}     CI Test Runner${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "Configuration:"
echo "  Test Suite: $TEST_SUITE"
echo "  Coverage Threshold: $COVERAGE_THRESHOLD%"
echo "  Parallel Execution: $PARALLEL"
echo "  Verbose: $VERBOSE"
echo ""

# Check if we're in the right directory
if [ ! -f "pytest.ini" ]; then
    echo -e "${RED}Error: pytest.ini not found. Please run from project root.${NC}"
    exit 1
fi

# Ensure test-reports directory exists
mkdir -p test-reports

# Build Python command
PYTHON_CMD="python scripts/run_tests_ci.py"
PYTHON_CMD="$PYTHON_CMD --suite $TEST_SUITE"
PYTHON_CMD="$PYTHON_CMD --coverage-threshold $COVERAGE_THRESHOLD"

if [ "$PARALLEL" = true ]; then
    PYTHON_CMD="$PYTHON_CMD --parallel"
fi

if [ "$VERBOSE" = true ]; then
    # Verbose is default, use quiet if not verbose
    :
else
    PYTHON_CMD="$PYTHON_CMD --quiet"
fi

# Run the tests
echo -e "${YELLOW}Running tests...${NC}"
echo ""

set +e  # Don't exit immediately on test failure
$PYTHON_CMD
TEST_EXIT_CODE=$?
set -e

# Display results
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    # In CI environment, display report paths
    if [ -n "${CI}" ]; then
        echo ""
        echo "Test artifacts generated:"
        echo "  - JUnit XML: test-reports/junit_*.xml"
        echo "  - HTML Report: test-reports/report_*.html"
        echo "  - Coverage XML: test-reports/coverage_*.xml"
        echo "  - Coverage HTML: test-reports/htmlcov_*/"
    fi
else
    echo -e "${RED}✗ Tests failed with exit code: $TEST_EXIT_CODE${NC}"
    
    # Provide helpful information for debugging
    echo ""
    echo "To investigate failures:"
    echo "  1. Check the HTML report in test-reports/"
    echo "  2. Review the JUnit XML for CI integration"
    echo "  3. Check coverage reports if failure was due to coverage threshold"
fi

# Exit with the test exit code for CI/CD integration
exit $TEST_EXIT_CODE
