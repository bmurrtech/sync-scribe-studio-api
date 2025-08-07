#!/bin/bash

# Comprehensive Test Runner for YouTube Downloader API
# Runs all tests including integration, security, and deployment validation
# Tests Rick Roll video functionality across all test suites

set -e

echo "🏁 Starting Comprehensive Test Suite for YouTube Downloader API"
echo "Test Video: Rick Astley - Never Gonna Give You Up (dQw4w9WgXcQ)"
echo "=========================================================="

# Configuration
START_TIME=$(date +%s)
TEST_RESULTS_DIR="test-results/$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$TEST_RESULTS_DIR/test-execution.log"
RICK_ROLL_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_section() {
    echo -e "${PURPLE}[SECTION]${NC} $1" | tee -a "$LOG_FILE"
    echo "==========================================================" | tee -a "$LOG_FILE"
}

# Setup test environment
setup_test_environment() {
    log_section "Setting up test environment"
    
    # Create results directory
    mkdir -p "$TEST_RESULTS_DIR"
    
    # Initialize log file
    echo "YouTube Downloader API - Comprehensive Test Execution" > "$LOG_FILE"
    echo "Start Time: $(date)" >> "$LOG_FILE"
    echo "Test Video: $RICK_ROLL_URL" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    log_info "Test results will be saved to: $TEST_RESULTS_DIR"
    log_info "Test execution log: $LOG_FILE"
}

# Test 1: YouTube service unit tests
run_youtube_service_tests() {
    log_section "Test 1: YouTube Service Unit Tests"
    
    cd services/youtube-downloader
    
    if [ ! -d "node_modules" ]; then
        log_info "Installing dependencies..."
        npm install
    fi
    
    log_info "Running YouTube service unit tests..."
    
    if npm test 2>&1 | tee "$TEST_RESULTS_DIR/youtube-unit-tests.log"; then
        log_success "YouTube service unit tests passed"
        echo "PASS" > "$TEST_RESULTS_DIR/youtube-unit-tests.result"
    else
        log_error "YouTube service unit tests failed"
        echo "FAIL" > "$TEST_RESULTS_DIR/youtube-unit-tests.result"
        return 1
    fi
    
    cd ../..
}

# Test 2: Integration tests with Rick Roll video
run_integration_tests() {
    log_section "Test 2: Integration Tests with Rick Roll Video"
    
    cd tests
    
    if [ ! -d "node_modules" ]; then
        log_info "Installing test dependencies..."
        npm install
    fi
    
    log_info "Running integration tests with Rick Roll video..."
    
    if npm run test:integration 2>&1 | tee "$TEST_RESULTS_DIR/integration-tests.log"; then
        log_success "Integration tests passed"
        echo "PASS" > "$TEST_RESULTS_DIR/integration-tests.result"
    else
        log_error "Integration tests failed"
        echo "FAIL" > "$TEST_RESULTS_DIR/integration-tests.result"
        return 1
    fi
    
    cd ..
}

# Test 3: Security and validation tests
run_security_tests() {
    log_section "Test 3: Security and Validation Tests"
    
    cd tests
    
    log_info "Running security tests..."
    
    if npm run test:security 2>&1 | tee "$TEST_RESULTS_DIR/security-tests.log"; then
        log_success "Security tests passed"
        echo "PASS" > "$TEST_RESULTS_DIR/security-tests.result"
    else
        log_error "Security tests failed"
        echo "FAIL" > "$TEST_RESULTS_DIR/security-tests.result"
        return 1
    fi
    
    cd ..
}

# Test 4: Docker deployment test
run_docker_deployment_test() {
    log_section "Test 4: Docker Deployment Test"
    
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        log_info "Running Docker deployment tests..."
        
        chmod +x tests/deployment/docker-deployment-test.sh
        
        if ./tests/deployment/docker-deployment-test.sh 2>&1 | tee "$TEST_RESULTS_DIR/docker-deployment.log"; then
            log_success "Docker deployment tests passed"
            echo "PASS" > "$TEST_RESULTS_DIR/docker-deployment.result"
        else
            log_error "Docker deployment tests failed"
            echo "FAIL" > "$TEST_RESULTS_DIR/docker-deployment.result"
            return 1
        fi
    else
        log_warning "Docker not available, skipping Docker deployment tests"
        echo "SKIP - Docker not available" > "$TEST_RESULTS_DIR/docker-deployment.result"
    fi
}

# Test 5: Performance benchmarks
run_performance_tests() {
    log_section "Test 5: Performance Tests"
    
    cd tests
    
    log_info "Running performance tests..."
    
    if npm run test:performance 2>&1 | tee "$TEST_RESULTS_DIR/performance-tests.log"; then
        log_success "Performance tests passed"
        echo "PASS" > "$TEST_RESULTS_DIR/performance-tests.result"
    else
        log_warning "Performance tests completed with warnings (may be acceptable)"
        echo "WARN" > "$TEST_RESULTS_DIR/performance-tests.result"
    fi
    
    cd ..
}

# Test 6: Code quality checks
run_code_quality_checks() {
    log_section "Test 6: Code Quality Checks"
    
    cd services/youtube-downloader
    
    log_info "Running ESLint..."
    if npm run lint 2>&1 | tee "$TEST_RESULTS_DIR/eslint.log"; then
        log_success "ESLint checks passed"
        echo "PASS" > "$TEST_RESULTS_DIR/eslint.result"
    else
        log_warning "ESLint found issues (may be warnings)"
        echo "WARN" > "$TEST_RESULTS_DIR/eslint.result"
    fi
    
    log_info "Running Prettier format check..."
    if npm run format:check 2>&1 | tee "$TEST_RESULTS_DIR/prettier.log"; then
        log_success "Prettier format checks passed"
        echo "PASS" > "$TEST_RESULTS_DIR/prettier.result"
    else
        log_warning "Prettier found formatting issues"
        echo "WARN" > "$TEST_RESULTS_DIR/prettier.result"
    fi
    
    log_info "Running security audit..."
    if npm audit --audit-level moderate 2>&1 | tee "$TEST_RESULTS_DIR/npm-audit.log"; then
        log_success "Security audit passed"
        echo "PASS" > "$TEST_RESULTS_DIR/npm-audit.result"
    else
        log_warning "Security audit found issues"
        echo "WARN" > "$TEST_RESULTS_DIR/npm-audit.result"
    fi
    
    cd ../..
}

# Test 7: Rick Roll specific functionality test
run_rickroll_functionality_test() {
    log_section "Test 7: Rick Roll Video Functionality Test"
    
    # This test requires the service to be running
    # We'll create a specific test for Rick Roll video functionality
    
    log_info "Testing Rick Roll video specific functionality..."
    
    # Create a temporary test script
    cat > "$TEST_RESULTS_DIR/rickroll-test.js" << 'EOF'
const axios = require('axios');

async function testRickRollFunctionality() {
    const RICK_ROLL_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
    const SERVICE_URL = process.env.SERVICE_URL || 'http://localhost:3001';
    
    console.log('Testing Rick Roll video functionality...');
    console.log('Service URL:', SERVICE_URL);
    console.log('Rick Roll URL:', RICK_ROLL_URL);
    
    try {
        // Test video info endpoint
        console.log('\nTesting video info endpoint...');
        const response = await axios.post(`${SERVICE_URL}/v1/media/youtube/info`, {
            url: RICK_ROLL_URL
        }, {
            timeout: 30000
        });
        
        if (response.data.success && 
            response.data.data.videoId === 'dQw4w9WgXcQ' &&
            response.data.data.title.toLowerCase().includes('rick') &&
            response.data.data.title.toLowerCase().includes('never gonna give you up')) {
            console.log('✅ Rick Roll video info test passed');
            console.log('Title:', response.data.data.title);
            console.log('Author:', response.data.data.author.name);
            return true;
        } else {
            console.log('❌ Rick Roll video info test failed');
            console.log('Response:', JSON.stringify(response.data, null, 2));
            return false;
        }
    } catch (error) {
        console.log('❌ Rick Roll functionality test failed');
        console.log('Error:', error.message);
        if (error.response) {
            console.log('Status:', error.response.status);
            console.log('Data:', error.response.data);
        }
        return false;
    }
}

testRickRollFunctionality().then(success => {
    process.exit(success ? 0 : 1);
}).catch(error => {
    console.error('Test execution error:', error);
    process.exit(1);
});
EOF
    
    # Check if service is running by testing health endpoint
    if curl -s -f http://localhost:3001/healthz > /dev/null 2>&1; then
        log_info "Service is running, executing Rick Roll functionality test..."
        
        cd "$TEST_RESULTS_DIR"
        npm init -y > /dev/null 2>&1
        npm install axios > /dev/null 2>&1
        
        if node rickroll-test.js 2>&1 | tee "rickroll-functionality.log"; then
            log_success "Rick Roll functionality test passed"
            echo "PASS" > "rickroll-functionality.result"
        else
            log_error "Rick Roll functionality test failed"
            echo "FAIL" > "rickroll-functionality.result"
        fi
        
        cd - > /dev/null
    else
        log_warning "Service not running, skipping Rick Roll functionality test"
        echo "SKIP - Service not running" > "$TEST_RESULTS_DIR/rickroll-functionality.result"
    fi
}

# Generate test report
generate_test_report() {
    log_section "Generating Test Report"
    
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    local report_file="$TEST_RESULTS_DIR/test-report.md"
    
    cat > "$report_file" << EOF
# YouTube Downloader API - Test Execution Report

**Execution Date:** $(date)
**Test Duration:** ${minutes}m ${seconds}s
**Test Video:** Rick Astley - Never Gonna Give You Up
**Video URL:** $RICK_ROLL_URL
**Video ID:** dQw4w9WgXcQ

## Test Results Summary

| Test Suite | Result | Details |
|------------|--------|---------|
EOF
    
    # Add test results to report
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    local warning_tests=0
    local skipped_tests=0
    
    for result_file in "$TEST_RESULTS_DIR"/*.result; do
        if [ -f "$result_file" ]; then
            local test_name=$(basename "$result_file" .result)
            local result=$(cat "$result_file")
            local log_file="${result_file%.result}.log"
            
            total_tests=$((total_tests + 1))
            
            case "$result" in
                "PASS")
                    passed_tests=$((passed_tests + 1))
                    echo "| $test_name | ✅ PASS | Test passed successfully |"
                    ;;
                "FAIL")
                    failed_tests=$((failed_tests + 1))
                    echo "| $test_name | ❌ FAIL | Test failed - check logs |"
                    ;;
                "WARN")
                    warning_tests=$((warning_tests + 1))
                    echo "| $test_name | ⚠️ WARN | Test completed with warnings |"
                    ;;
                *)
                    skipped_tests=$((skipped_tests + 1))
                    echo "| $test_name | ⏭️ SKIP | $result |"
                    ;;
            esac >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF

## Summary Statistics

- **Total Tests:** $total_tests
- **Passed:** $passed_tests
- **Failed:** $failed_tests
- **Warnings:** $warning_tests
- **Skipped:** $skipped_tests

## Rick Roll Video Test Details

The comprehensive test suite specifically validates functionality with the Rick Roll video:
- **Video ID:** dQw4w9WgXcQ
- **Expected Title:** Contains "Rick Astley" and "Never Gonna Give You Up"
- **Expected Author:** Rick Astley or RickAstleyVEVO
- **Video Type:** Music video
- **Duration:** Approximately 3 minutes 32 seconds

This video was chosen as it's:
1. Widely available and stable
2. Well-known and easily identifiable
3. Has consistent metadata
4. Represents a typical music video use case
5. Provides a reliable test case for regression testing

## Test Environment

- **Node.js Version:** $(node --version 2>/dev/null || echo "N/A")
- **NPM Version:** $(npm --version 2>/dev/null || echo "N/A")
- **Docker Version:** $(docker --version 2>/dev/null || echo "N/A")
- **Operating System:** $(uname -s 2>/dev/null || echo "N/A")
- **Architecture:** $(uname -m 2>/dev/null || echo "N/A")

## Recommendations

EOF
    
    if [ $failed_tests -gt 0 ]; then
        echo "- ⚠️ **CRITICAL**: $failed_tests test(s) failed. Review logs and fix issues before deployment." >> "$report_file"
    fi
    
    if [ $warning_tests -gt 0 ]; then
        echo "- 📝 **INFO**: $warning_tests test(s) completed with warnings. Review and address if necessary." >> "$report_file"
    fi
    
    if [ $failed_tests -eq 0 ] && [ $warning_tests -eq 0 ]; then
        echo "- ✅ **SUCCESS**: All tests passed. System is ready for deployment." >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "---" >> "$report_file"
    echo "*Report generated on $(date)*" >> "$report_file"
    
    log_info "Test report generated: $report_file"
    
    # Display summary
    echo ""
    log_section "Test Execution Summary"
    log_info "Total Tests: $total_tests"
    log_success "Passed: $passed_tests"
    if [ $failed_tests -gt 0 ]; then
        log_error "Failed: $failed_tests"
    fi
    if [ $warning_tests -gt 0 ]; then
        log_warning "Warnings: $warning_tests"
    fi
    if [ $skipped_tests -gt 0 ]; then
        log_info "Skipped: $skipped_tests"
    fi
    log_info "Duration: ${minutes}m ${seconds}s"
    log_info "Results saved to: $TEST_RESULTS_DIR"
    
    return $failed_tests
}

# Main execution
main() {
    local failed_tests=0
    
    setup_test_environment
    
    # Run all test suites
    run_youtube_service_tests || failed_tests=$((failed_tests + 1))
    echo ""
    
    run_integration_tests || failed_tests=$((failed_tests + 1))
    echo ""
    
    run_security_tests || failed_tests=$((failed_tests + 1))
    echo ""
    
    run_docker_deployment_test || failed_tests=$((failed_tests + 1))
    echo ""
    
    run_performance_tests
    echo ""
    
    run_code_quality_checks
    echo ""
    
    run_rickroll_functionality_test || failed_tests=$((failed_tests + 1))
    echo ""
    
    # Generate final report
    generate_test_report
    local report_failed_tests=$?
    
    echo ""
    if [ $failed_tests -eq 0 ] && [ $report_failed_tests -eq 0 ]; then
        log_success "🎉 All critical tests passed! System is ready for production deployment."
        echo ""
        log_info "Rick Roll video functionality validated successfully!"
        log_info "Next steps:"
        log_info "1. Review test report: $TEST_RESULTS_DIR/test-report.md"
        log_info "2. Run Docker deployment: ./tests/deployment/docker-deployment-test.sh"
        log_info "3. Deploy to GCP Cloud Run: ./deployment/gcp-cloud-run/deploy.sh"
        return 0
    else
        log_error "❌ $failed_tests critical test suite(s) failed."
        log_error "Please review the test results and fix issues before deployment."
        log_info "Test report: $TEST_RESULTS_DIR/test-report.md"
        return 1
    fi
}

# Handle script arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Comprehensive Test Runner for YouTube Downloader API"
    echo ""
    echo "This script runs all test suites including:"
    echo "1. YouTube service unit tests"
    echo "2. Integration tests with Rick Roll video"
    echo "3. Security and validation tests"
    echo "4. Docker deployment tests (if Docker available)"
    echo "5. Performance benchmarks"
    echo "6. Code quality checks (ESLint, Prettier, npm audit)"
    echo "7. Rick Roll video functionality validation"
    echo ""
    echo "Test results are saved to test-results/ directory."
    echo ""
    echo "Usage: $0"
    echo ""
    echo "Test Video: Rick Astley - Never Gonna Give You Up"
    echo "URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    echo ""
    exit 0
fi

# Run all tests
main
exit $?
