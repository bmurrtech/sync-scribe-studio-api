#!/usr/bin/env python3
"""
Transcription Test with Extended Retry Logic
Tests the media transcription endpoint with proper retry handling for async processing
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for utils import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.utils import gdrive_to_download_url

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "test-api-key")

# Test parameters
MAX_RETRIES = 50  # Maximum number of retries
RETRY_INTERVAL = 5  # Seconds between retries
MAX_WAIT_TIME = 300  # Maximum total wait time in seconds (5 minutes)

# Test media URLs - Gospel presentations with spoken audio for transcription testing
TEST_MEDIA_URLS = {
    "mp4_321_gospel": gdrive_to_download_url("https://drive.google.com/file/d/1xYEx_xF3It-Yz_aToM9OJuRiHQd9Aq8c/view?usp=drive_link"),
    "mp4_christianity_explored": gdrive_to_download_url("https://drive.google.com/file/d/1pf7v_w3hsrwyGCbC2hHlqL5_mKgZoWvC/view?usp=drive_link"),
    "mp3_animated_gospel": gdrive_to_download_url("https://drive.google.com/file/d/1sW2DmcR0RMEnpEs8uAXI7dBq09sjStq7/view?usp=drive_link"),
}

def check_health():
    """Check if the API is healthy and ASR is enabled"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API is healthy")
            print(f"  - ASR Enabled: {data.get('configuration', {}).get('asr_enabled', False)}")
            print(f"  - Model Loaded: {data.get('initialization', {}).get('model_loaded', False)}")
            return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
    return False

def submit_transcription(media_url, test_name="Test"):
    """Submit a transcription job"""
    url = f"{BASE_URL}/v1/media/transcribe"
    headers = {"X-API-Key": API_KEY}
    payload = {
        "media_url": media_url,
        "task": "transcribe",
        "include_text": True,
        "language": "en"  # Specify language to speed up processing
    }
    
    try:
        print(f"\n{'='*60}")
        print(f"Testing: {test_name}")
        print(f"{'='*60}")
        print(f"Submitting transcription request...")
        print(f"  URL: {media_url[:80]}...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code in [200, 202]:
            data = response.json()
            job_id = data.get("job_id")
            
            # Check if we have the actual transcription result in the response
            transcription_text = None
            if "response" in data and isinstance(data["response"], dict):
                # Text might be in response.text
                transcription_text = data["response"].get("text")
            
            if transcription_text:
                print(f"✓ Transcription completed successfully (direct response)")
                print(f"  Processing time: {data.get('run_time', 'N/A')} seconds")
                return {
                    "status": "success",
                    "type": "synchronous",
                    "data": data,
                    "job_id": job_id,
                    "transcription": transcription_text
                }
            
            # If no direct result, treat as async
            if job_id:
                print(f"✓ Job submitted for async processing")
                print(f"  Job ID: {job_id}")
                return {
                    "status": "success",
                    "type": "asynchronous",
                    "job_id": job_id
                }
            else:
                print(f"✗ Unexpected response format")
                return {"status": "error", "error": "Unexpected response format", "data": data}
        else:
            print(f"✗ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data}")
            except:
                print(f"  Response: {response.text[:200]}")
            return {"status": "error", "error": f"Status {response.status_code}"}
            
    except Exception as e:
        print(f"✗ Exception during submission: {e}")
        return {"status": "error", "error": str(e)}

def check_job_status(job_id):
    """Check the status of a transcription job"""
    url = f"{BASE_URL}/v1/toolkit/job/status"
    headers = {"X-API-Key": API_KEY}
    payload = {"job_id": job_id}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            
            # Check for completion
            if status == "completed":
                return {
                    "status": "completed",
                    "data": data
                }
            elif status in ["failed", "error"]:
                return {
                    "status": "failed",
                    "error": data.get("error", "Unknown error"),
                    "data": data
                }
            else:
                # Still processing
                return {
                    "status": "processing",
                    "job_status": status,
                    "data": data
                }
        elif response.status_code == 404:
            return {"status": "not_found"}
        else:
            return {"status": "error", "error": f"Status check returned {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

def wait_for_transcription(job_id, max_retries=MAX_RETRIES, retry_interval=RETRY_INTERVAL):
    """Wait for a transcription job to complete with retries"""
    print(f"\nWaiting for transcription to complete...")
    print(f"  Max retries: {max_retries}")
    print(f"  Retry interval: {retry_interval} seconds")
    print(f"  Max wait time: {max_retries * retry_interval} seconds")
    
    start_time = time.time()
    
    for retry in range(max_retries):
        elapsed = time.time() - start_time
        print(f"\n[Retry {retry + 1}/{max_retries}] Checking status... (elapsed: {elapsed:.1f}s)")
        
        result = check_job_status(job_id)
        
        if result["status"] == "completed":
            print(f"✓ Transcription completed successfully!")
            
            # Extract transcription data
            data = result.get("data", {})
            transcription_text = None
            
            # Try different possible locations for transcription text
            if "result" in data:
                transcription_text = data["result"].get("text") or data["result"].get("transcription")
            elif "output" in data:
                transcription_text = data["output"].get("text") or data["output"].get("transcription")
            elif "transcription" in data:
                transcription_text = data["transcription"]
            elif "text" in data:
                transcription_text = data["text"]
            
            if transcription_text:
                print(f"  Transcription preview: {transcription_text[:200]}...")
            
            return {
                "status": "success",
                "retries": retry + 1,
                "elapsed_time": elapsed,
                "data": data,
                "transcription": transcription_text
            }
            
        elif result["status"] == "failed":
            print(f"✗ Transcription failed: {result.get('error', 'Unknown error')}")
            return {
                "status": "failed",
                "retries": retry + 1,
                "elapsed_time": elapsed,
                "error": result.get("error"),
                "data": result.get("data")
            }
            
        elif result["status"] == "not_found":
            print(f"⚠ Job not found (may still be initializing)")
            
        elif result["status"] == "error":
            print(f"⚠ Error checking status: {result.get('error')}")
            
        else:
            job_status = result.get("job_status", "processing")
            print(f"  Status: {job_status}")
        
        # Wait before next retry
        if retry < max_retries - 1:
            print(f"  Waiting {retry_interval} seconds before next check...")
            time.sleep(retry_interval)
    
    # Max retries reached
    elapsed = time.time() - start_time
    print(f"\n✗ Max retries ({max_retries}) reached after {elapsed:.1f} seconds")
    return {
        "status": "timeout",
        "retries": max_retries,
        "elapsed_time": elapsed
    }

def test_transcription(media_url, test_name):
    """Run a complete transcription test"""
    # Submit transcription
    submission = submit_transcription(media_url, test_name)
    
    if submission["status"] != "success":
        return {
            "test": test_name,
            "status": "failed",
            "error": f"Submission failed: {submission.get('error')}"
        }
    
    # If synchronous, we're done
    if submission["type"] == "synchronous":
        print(f"✓ Transcription completed synchronously")
        return {
            "test": test_name,
            "status": "success",
            "type": "synchronous",
            "data": submission["data"],
            "transcription": submission.get("transcription")
        }
    
    # For asynchronous, wait for completion
    job_id = submission["job_id"]
    result = wait_for_transcription(job_id)
    
    return {
        "test": test_name,
        "status": result["status"],
        "type": "asynchronous",
        "retries": result.get("retries"),
        "elapsed_time": result.get("elapsed_time"),
        "transcription": result.get("transcription"),
        "error": result.get("error")
    }

def main():
    """Run transcription tests"""
    print(f"\n{'='*60}")
    print(f"TRANSCRIPTION TEST WITH EXTENDED RETRIES")
    print(f"Base URL: {BASE_URL}")
    print(f"{'='*60}\n")
    
    # Check health first
    if not check_health():
        print("\n✗ API health check failed. Exiting.")
        sys.exit(1)
    
    # Test configurations
    tests = [
        {
            "name": "Short MP3 (Animated Gospel)",
            "url": TEST_MEDIA_URLS["mp3_animated_gospel"]
        },
        {
            "name": "MP4 Video (3-2-1 Gospel)",
            "url": TEST_MEDIA_URLS["mp4_321_gospel"]
        },
        {
            "name": "MP4 Video (Christianity Explored)",
            "url": TEST_MEDIA_URLS["mp4_christianity_explored"]
        }
    ]
    
    results = []
    
    # Run tests
    for test in tests:
        result = test_transcription(test["url"], test["name"])
        results.append(result)
        
        # Print result summary
        print(f"\n{'-'*40}")
        print(f"Test: {test['name']}")
        print(f"Status: {result['status']}")
        if result["status"] == "success":
            print(f"Type: {result.get('type', 'unknown')}")
            if result.get("retries"):
                print(f"Retries: {result['retries']}")
            if result.get("elapsed_time"):
                print(f"Time: {result['elapsed_time']:.1f} seconds")
            if result.get("transcription"):
                print(f"Transcription received: {len(result['transcription'])} characters")
        elif result.get("error"):
            print(f"Error: {result['error']}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    timeout = sum(1 for r in results if r["status"] == "timeout")
    
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Timeout: {timeout}")
    
    # Save detailed report
    report = {
        "test_type": "transcription_retry",
        "base_url": BASE_URL,
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "max_retries": MAX_RETRIES,
            "retry_interval": RETRY_INTERVAL,
            "max_wait_time": MAX_WAIT_TIME
        },
        "summary": {
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "timeout": timeout
        },
        "results": results
    }
    
    report_dir = Path("tests/results")
    report_dir.mkdir(exist_ok=True)
    
    report_file = report_dir / "transcription_test_results.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Exit code based on results
    if successful == len(results):
        print("\n✓ All transcription tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {len(results) - successful} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
