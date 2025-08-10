#!/usr/bin/env python3
"""
CI-friendly test runner with comprehensive reporting and proper exit codes.
Generates JUnit XML, HTML reports, and coverage reports for pipeline integration.
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class TestRunner:
    """Handles test execution with CI-friendly reporting."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "test-reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_tests(
        self,
        markers: Optional[str] = None,
        parallel: bool = False,
        coverage_threshold: int = 70,
        verbose: bool = True,
        specific_tests: Optional[List[str]] = None
    ) -> Tuple[int, Dict]:
        """
        Run pytest with specified options and return exit code with results.
        
        Args:
            markers: Pytest markers to filter tests (e.g., "unit", "not slow")
            parallel: Run tests in parallel using pytest-xdist
            coverage_threshold: Minimum coverage percentage required
            verbose: Enable verbose output
            specific_tests: List of specific test files or directories
            
        Returns:
            Tuple of (exit_code, results_dict)
        """
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add custom options
        custom_opts = [
            f"--junitxml={self.reports_dir}/junit_{self.timestamp}.xml",
            f"--html={self.reports_dir}/report_{self.timestamp}.html",
            "--self-contained-html",
            f"--cov-report=html:{self.reports_dir}/htmlcov_{self.timestamp}",
            f"--cov-report=xml:{self.reports_dir}/coverage_{self.timestamp}.xml",
            f"--cov-report=json:{self.reports_dir}/coverage_{self.timestamp}.json",
            f"--cov-fail-under={coverage_threshold}",
        ]
        cmd.extend(custom_opts)
        
        # Add markers if specified
        if markers:
            cmd.extend(["-m", markers])
            
        # Add parallel execution if requested
        if parallel:
            cmd.extend(["-n", "auto"])
            
        # Add verbose flag
        if verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")
            
        # Add specific tests if provided
        if specific_tests:
            cmd.extend(specific_tests)
            
        # Run tests
        print(f"[INFO] Running command: {' '.join(cmd)}")
        print(f"[INFO] Reports will be saved to: {self.reports_dir}")
        print("-" * 80)
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        # Parse results
        results = self._parse_results(result.returncode)
        
        # Generate summary
        self._generate_summary(results)
        
        return result.returncode, results
    
    def _parse_results(self, exit_code: int) -> Dict:
        """Parse test results from generated reports."""
        results = {
            "exit_code": exit_code,
            "status": "PASS" if exit_code == 0 else "FAIL",
            "timestamp": self.timestamp,
            "reports_dir": str(self.reports_dir),
        }
        
        # Parse coverage if available
        coverage_json = self.reports_dir / f"coverage_{self.timestamp}.json"
        if coverage_json.exists():
            try:
                with open(coverage_json) as f:
                    coverage_data = json.load(f)
                    results["coverage"] = {
                        "percent": coverage_data.get("totals", {}).get("percent_covered", 0),
                        "lines_covered": coverage_data.get("totals", {}).get("covered_lines", 0),
                        "lines_total": coverage_data.get("totals", {}).get("num_statements", 0),
                    }
            except Exception as e:
                print(f"[WARNING] Could not parse coverage report: {e}")
                
        # Check for JUnit XML
        junit_xml = self.reports_dir / f"junit_{self.timestamp}.xml"
        if junit_xml.exists():
            results["junit_report"] = str(junit_xml)
            
        # Check for HTML report
        html_report = self.reports_dir / f"report_{self.timestamp}.html"
        if html_report.exists():
            results["html_report"] = str(html_report)
            
        return results
    
    def _generate_summary(self, results: Dict) -> None:
        """Generate a summary report file."""
        summary_file = self.reports_dir / f"summary_{self.timestamp}.json"
        
        # Add environment info
        results["environment"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": os.getcwd(),
        }
        
        # Write summary
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        print("\n" + "=" * 80)
        print(f"[{'PASS' if results['exit_code'] == 0 else 'FAIL'}] Test execution completed")
        print(f"[INFO] Summary saved to: {summary_file}")
        
        if "coverage" in results:
            cov = results["coverage"]
            print(f"[INFO] Coverage: {cov['percent']:.2f}% ({cov['lines_covered']}/{cov['lines_total']} lines)")
            
        if results.get("html_report"):
            print(f"[INFO] HTML Report: {results['html_report']}")
            
        if results.get("junit_report"):
            print(f"[INFO] JUnit XML: {results['junit_report']}")
            
        print("=" * 80)


def main():
    """Main entry point for CI test runner."""
    parser = argparse.ArgumentParser(description="CI-friendly test runner")
    parser.add_argument(
        "-m", "--markers",
        help="Pytest markers to filter tests (e.g., 'unit', 'not slow')"
    )
    parser.add_argument(
        "-p", "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "-c", "--coverage-threshold",
        type=int,
        default=70,
        help="Minimum coverage percentage required (default: 70)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    parser.add_argument(
        "--suite",
        choices=["smoke", "unit", "integration", "full"],
        help="Predefined test suite to run"
    )
    parser.add_argument(
        "tests",
        nargs="*",
        help="Specific test files or directories to run"
    )
    
    args = parser.parse_args()
    
    # Handle predefined suites
    markers = args.markers
    if args.suite:
        suite_markers = {
            "smoke": "smoke",
            "unit": "unit",
            "integration": "integration",
            "full": None  # Run all tests
        }
        markers = suite_markers[args.suite]
    
    # Initialize runner
    project_root = Path(__file__).parent.parent
    runner = TestRunner(project_root)
    
    # Run tests
    exit_code, results = runner.run_tests(
        markers=markers,
        parallel=args.parallel,
        coverage_threshold=args.coverage_threshold,
        verbose=not args.quiet,
        specific_tests=args.tests
    )
    
    # Exit with proper code for CI
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
