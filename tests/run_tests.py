#!/usr/bin/env python3
"""
Test Runner Script

This script provides a unified interface to run all test suites,
following TDD principles and providing comprehensive coverage reporting.

Usage:
    python tests/run_tests.py [options]
    
Options:
    --unit           Run only unit tests
    --integration    Run only integration tests
    --manual         Run manual test scripts
    --all           Run all tests (default)
    --coverage      Generate coverage report
    --html          Generate HTML coverage report
    --parallel      Run tests in parallel
    --verbose       Verbose output
    --quick         Quick mode (skip slow tests)
"""

import argparse
import os
import sys
import subprocess
import time
from typing import List, Dict, Any
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class TestRunner:
    """Unified test runner for all test suites"""
    
    def __init__(self):
        self.results = {
            'start_time': time.time(),
            'unit_tests': {},
            'integration_tests': {},
            'manual_tests': {},
            'coverage': {},
            'summary': {}
        }
        
    def run_unit_tests(self, coverage: bool = False, parallel: bool = False, verbose: bool = False, quick: bool = False) -> bool:
        """Run unit tests with optional coverage"""
        print("🧪 Running Unit Tests")
        print("=" * 50)
        
        # Python unit tests
        python_cmd = self._build_pytest_command(
            "tests/unit/test_*.py",
            coverage=coverage,
            parallel=parallel,
            verbose=verbose,
            quick=quick
        )
        
        print(f"Command: {' '.join(python_cmd)}")
        python_result = subprocess.run(python_cmd, cwd=project_root)
        
        # Node.js unit tests
        node_cmd = [
            "npm", "test", "--prefix", "services/youtube-downloader"
        ]
        
        print(f"\nCommand: {' '.join(node_cmd)}")
        node_result = subprocess.run(node_cmd, cwd=project_root)
        
        success = python_result.returncode == 0 and node_result.returncode == 0
        
        self.results['unit_tests'] = {
            'python_exit_code': python_result.returncode,
            'node_exit_code': node_result.returncode,
            'success': success
        }
        
        return success
    
    def run_integration_tests(self, verbose: bool = False, quick: bool = False) -> bool:
        """Run integration tests"""
        print("\n🔗 Running Integration Tests")
        print("=" * 50)
        
        cmd = self._build_pytest_command(
            "tests/integration/",
            markers="integration",
            verbose=verbose,
            quick=quick
        )
        
        print(f"Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=project_root)
        
        success = result.returncode == 0
        
        self.results['integration_tests'] = {
            'exit_code': result.returncode,
            'success': success
        }
        
        return success
    
    def run_manual_tests(self) -> bool:
        """Run manual test scripts if environment is configured"""
        print("\n🔧 Running Manual Tests")
        print("=" * 50)
        
        results = {}
        
        # Check if staging environment is configured
        staging_url = os.getenv('STAGING_RAILWAY_URL')
        api_key = os.getenv('API_KEY')
        
        if staging_url and staging_url != 'https://your-app.up.railway.app':
            print("Running staging environment tests...")
            cmd = [sys.executable, "tests/manual/test_staging_environment.py"]
            result = subprocess.run(cmd, cwd=project_root)
            results['staging'] = {
                'exit_code': result.returncode,
                'success': result.returncode == 0
            }
        else:
            print("⚠️  Skipping staging tests - STAGING_RAILWAY_URL not configured")
            results['staging'] = {'skipped': True, 'reason': 'environment not configured'}
        
        # Check if production environment is configured
        prod_url = os.getenv('PROD_RAILWAY_URL')
        
        if prod_url and prod_url != 'https://your-prod-app.up.railway.app':
            print("Running production environment tests...")
            cmd = [sys.executable, "tests/manual/test_production_environment.py"]
            result = subprocess.run(cmd, cwd=project_root)
            results['production'] = {
                'exit_code': result.returncode,
                'success': result.returncode == 0
            }
        else:
            print("⚠️  Skipping production tests - PROD_RAILWAY_URL not configured")
            results['production'] = {'skipped': True, 'reason': 'environment not configured'}
        
        # Overall success if all configured tests passed
        success = all(
            result.get('success', True) for result in results.values() 
            if not result.get('skipped', False)
        )
        
        self.results['manual_tests'] = results
        
        return success
    
    def _build_pytest_command(self, path: str, coverage: bool = False, parallel: bool = False, 
                             verbose: bool = False, quick: bool = False, markers: str = None) -> List[str]:
        """Build pytest command with options"""
        cmd = [sys.executable, "-m", "pytest", path]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        if quick:
            cmd.extend(["-m", "not slow"])
        
        if markers:
            cmd.extend(["-m", markers])
        
        if coverage:
            cmd.extend([
                "--cov=routes",
                "--cov=services", 
                "--cov-report=term-missing",
                "--cov-report=xml"
            ])
        
        cmd.extend(["--tb=short", "--color=yes"])
        
        return cmd
    
    def generate_coverage_report(self, html: bool = False) -> bool:
        """Generate coverage report"""
        print("\n📊 Generating Coverage Report")
        print("=" * 50)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            "tests/unit/",
            "--cov=routes",
            "--cov=services",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=70"  # Minimum 70% coverage
        ]
        
        if html:
            cmd.append("--cov-report=html")
        
        result = subprocess.run(cmd, cwd=project_root)
        
        success = result.returncode == 0
        
        self.results['coverage'] = {
            'exit_code': result.returncode,
            'success': success
        }
        
        if html and success:
            print("📄 HTML coverage report generated: htmlcov/index.html")
        
        return success
    
    def run_all_tests(self, **kwargs) -> bool:
        """Run all test suites"""
        print("🚀 Running Complete Test Suite")
        print("=" * 50)
        print(f"Project Root: {project_root}")
        print(f"Python Version: {sys.version}")
        print()
        
        results = []
        
        # Run unit tests
        unit_success = self.run_unit_tests(**kwargs)
        results.append(('Unit Tests', unit_success))
        
        # Run integration tests
        integration_success = self.run_integration_tests(**kwargs)
        results.append(('Integration Tests', integration_success))
        
        # Run manual tests if requested
        if kwargs.get('manual', True):
            manual_success = self.run_manual_tests()
            results.append(('Manual Tests', manual_success))
        
        # Generate coverage report if requested
        if kwargs.get('coverage', False):
            coverage_success = self.generate_coverage_report(kwargs.get('html', False))
            results.append(('Coverage Report', coverage_success))
        
        # Summary
        self.print_summary(results)
        
        # Overall success
        overall_success = all(success for _, success in results)
        
        self.results['summary'] = {
            'overall_success': overall_success,
            'results': dict(results),
            'end_time': time.time(),
            'duration': time.time() - self.results['start_time']
        }
        
        return overall_success
    
    def print_summary(self, results: List[tuple]) -> None:
        """Print test results summary"""
        print("\n📈 Test Results Summary")
        print("=" * 50)
        
        for test_type, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {test_type}")
        
        total_tests = len(results)
        passed_tests = sum(1 for _, success in results if success)
        
        print("\n" + "=" * 50)
        print(f"📊 Overall Results: {passed_tests}/{total_tests} test suites passed")
        
        if passed_tests == total_tests:
            print("🎉 All test suites completed successfully!")
        else:
            print(f"⚠️  {total_tests - passed_tests} test suite(s) failed.")
    
    def save_results(self, filename: str = "test_results.json") -> None:
        """Save test results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"📄 Test results saved to {filename}")
        except Exception as e:
            print(f"Failed to save results: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Run YouTube Integration Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tests/run_tests.py                    # Run all tests
    python tests/run_tests.py --unit            # Run only unit tests
    python tests/run_tests.py --coverage --html # Run with HTML coverage
    python tests/run_tests.py --quick --parallel # Quick parallel execution
        """
    )
    
    # Test selection
    parser.add_argument('--unit', action='store_true', 
                       help='Run only unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run only integration tests') 
    parser.add_argument('--manual', action='store_true',
                       help='Run manual test scripts')
    parser.add_argument('--all', action='store_true', default=True,
                       help='Run all tests (default)')
    
    # Test options
    parser.add_argument('--coverage', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--html', action='store_true',
                       help='Generate HTML coverage report')
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--quick', action='store_true',
                       help='Quick mode (skip slow tests)')
    
    # Output options
    parser.add_argument('--save-results', metavar='FILE',
                       help='Save test results to JSON file')
    
    args = parser.parse_args()
    
    # Validate environment
    print("🔍 Validating Test Environment")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('tests'):
        print("❌ Error: tests directory not found. Please run from project root.")
        return 1
    
    # Check Python dependencies
    try:
        import pytest
        print("✅ pytest found")
    except ImportError:
        print("❌ pytest not found. Install with: pip install -r tests/requirements.txt")
        return 1
    
    # Check Node.js dependencies for microservice tests
    if os.path.exists('services/youtube-downloader/package.json'):
        if os.path.exists('services/youtube-downloader/node_modules'):
            print("✅ Node.js dependencies found")
        else:
            print("⚠️  Node.js dependencies not found. Run: cd services/youtube-downloader && npm install")
    
    print()
    
    # Create runner and execute tests
    runner = TestRunner()
    
    try:
        if args.unit and not args.integration and not args.manual:
            success = runner.run_unit_tests(
                coverage=args.coverage,
                parallel=args.parallel, 
                verbose=args.verbose,
                quick=args.quick
            )
        elif args.integration and not args.unit and not args.manual:
            success = runner.run_integration_tests(
                verbose=args.verbose,
                quick=args.quick
            )
        elif args.manual and not args.unit and not args.integration:
            success = runner.run_manual_tests()
        else:
            # Run all tests
            success = runner.run_all_tests(
                coverage=args.coverage,
                html=args.html,
                parallel=args.parallel,
                verbose=args.verbose,
                quick=args.quick,
                manual=True
            )
        
        # Save results if requested
        if args.save_results:
            runner.save_results(args.save_results)
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
