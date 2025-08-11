#!/usr/bin/env python3
"""
Latency Analysis Script
Analyzes test results and compares performance metrics
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

def load_test_results(file_path: str) -> Dict:
    """Load test results from JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {file_path}")
        return None

def analyze_latencies(results: Dict) -> Dict:
    """Analyze response times from test results"""
    if not results or 'results' not in results:
        return None
    
    latencies = []
    endpoint_times = {}
    
    for test in results['results']:
        response_time = test.get('response_time', 0)
        endpoint = test.get('endpoint', 'unknown')
        name = test.get('name', 'unknown')
        status = test.get('status', 'unknown')
        
        if status == 'PASS':
            latencies.append(response_time)
            endpoint_times[name] = response_time
    
    if not latencies:
        return None
    
    # Calculate statistics
    latencies.sort()
    total = len(latencies)
    
    return {
        'count': total,
        'min': min(latencies),
        'max': max(latencies),
        'avg': sum(latencies) / total,
        'median': latencies[total // 2] if total > 0 else 0,
        'p95': latencies[int(total * 0.95)] if total > 0 else 0,
        'p99': latencies[int(total * 0.99)] if total > 0 else 0,
        'total_time': sum(latencies),
        'endpoint_times': endpoint_times
    }

def print_latency_report(stats: Dict, label: str = "Test Results"):
    """Print formatted latency report"""
    if not stats:
        print(f"No valid latency data for {label}")
        return
    
    print(f"\n{'='*60}")
    print(f"LATENCY ANALYSIS - {label}")
    print(f"{'='*60}")
    print(f"Total Successful Tests: {stats['count']}")
    print(f"Total Time: {stats['total_time']:.2f}s")
    print(f"\nLatency Statistics:")
    print(f"  Min:    {stats['min']:.3f}s")
    print(f"  Median: {stats['median']:.3f}s")
    print(f"  Avg:    {stats['avg']:.3f}s")
    print(f"  P95:    {stats['p95']:.3f}s")
    print(f"  P99:    {stats['p99']:.3f}s")
    print(f"  Max:    {stats['max']:.3f}s")
    
    # Top 5 slowest endpoints
    if 'endpoint_times' in stats:
        sorted_endpoints = sorted(stats['endpoint_times'].items(), 
                                 key=lambda x: x[1], reverse=True)[:5]
        print(f"\nTop 5 Slowest Endpoints:")
        for name, time in sorted_endpoints:
            print(f"  {name}: {time:.3f}s")

def compare_results(before: Dict, after: Dict):
    """Compare two sets of test results"""
    if not before or not after:
        print("Cannot compare - missing data")
        return
    
    print(f"\n{'='*60}")
    print("PERFORMANCE COMPARISON")
    print(f"{'='*60}")
    
    # Compare averages
    avg_before = before.get('avg', 0)
    avg_after = after.get('avg', 0)
    avg_diff = avg_after - avg_before
    avg_pct = (avg_diff / avg_before * 100) if avg_before > 0 else 0
    
    print(f"Average Latency:")
    print(f"  Before: {avg_before:.3f}s")
    print(f"  After:  {avg_after:.3f}s")
    print(f"  Change: {avg_diff:+.3f}s ({avg_pct:+.1f}%)")
    
    # Compare P95
    p95_before = before.get('p95', 0)
    p95_after = after.get('p95', 0)
    p95_diff = p95_after - p95_before
    p95_pct = (p95_diff / p95_before * 100) if p95_before > 0 else 0
    
    print(f"\nP95 Latency:")
    print(f"  Before: {p95_before:.3f}s")
    print(f"  After:  {p95_after:.3f}s")
    print(f"  Change: {p95_diff:+.3f}s ({p95_pct:+.1f}%)")
    
    # Compare total time
    total_before = before.get('total_time', 0)
    total_after = after.get('total_time', 0)
    total_diff = total_after - total_before
    total_pct = (total_diff / total_before * 100) if total_before > 0 else 0
    
    print(f"\nTotal Test Time:")
    print(f"  Before: {total_before:.2f}s")
    print(f"  After:  {total_after:.2f}s")
    print(f"  Change: {total_diff:+.2f}s ({total_pct:+.1f}%)")
    
    # Performance verdict
    print(f"\n{'='*60}")
    if avg_pct < -10:
        print("✅ PERFORMANCE IMPROVED: Tests are running faster!")
    elif avg_pct > 10:
        print("⚠️  PERFORMANCE DEGRADED: Tests are running slower!")
    else:
        print("✓ PERFORMANCE STABLE: No significant change detected")

def main():
    """Main analysis function"""
    # Default paths
    local_results = "tests/results/local_test_results.json"
    baseline_results = "tests/results/baseline_test_results.json"
    
    # Load current results
    current = load_test_results(local_results)
    if not current:
        print("Could not load current test results")
        sys.exit(1)
    
    # Analyze current results
    current_stats = analyze_latencies(current)
    print_latency_report(current_stats, "Current Run (Docker)")
    
    # Save current stats for future comparison
    stats_file = Path("tests/results/latency_stats.json")
    with open(stats_file, 'w') as f:
        json.dump({
            'timestamp': current.get('timestamp'),
            'stats': current_stats,
            'pass_rate': current.get('summary', {}).get('pass_rate', 0)
        }, f, indent=2)
    print(f"\nLatency stats saved to: {stats_file}")
    
    # Try to load baseline for comparison
    baseline = load_test_results(baseline_results)
    if baseline:
        baseline_stats = analyze_latencies(baseline)
        print_latency_report(baseline_stats, "Baseline")
        compare_results(baseline_stats, current_stats)
    else:
        # Save current as baseline if none exists
        import shutil
        shutil.copy(local_results, baseline_results)
        print(f"\nSaved current results as baseline for future comparisons")

if __name__ == "__main__":
    main()
