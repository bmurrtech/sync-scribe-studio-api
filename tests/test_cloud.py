#!/usr/bin/env python3
"""
Cloud API Test Script
Simple test runner for cloud/production environments
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from utils import gdrive_to_download_url

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("CLOUD_BASE_URL", "https://no-code-architects-toolkit-v1-121285693414.us-east4.run.app")
API_KEY = os.getenv("API_KEY", "test-api-key")

# Test media URLs - Gospel presentations with spoken audio for transcription testing
TEST_MEDIA_URLS = {
    "mp4_321_gospel": gdrive_to_download_url("https://drive.google.com/file/d/1xYEx_xF3It-Yz_aToM9OJuRiHQd9Aq8c/view?usp=drive_link"),
    "mp4_christianity_explored": gdrive_to_download_url("https://drive.google.com/file/d/1pf7v_w3hsrwyGCbC2hHlqL5_mKgZoWvC/view?usp=drive_link"),
    "mp4_animated_gospel": gdrive_to_download_url("https://drive.google.com/file/d/1ELQorrQ_SqloaRYErqsXRCaK5N0nSAS_/view?usp=drive_link"),
    "mp3_christianity_explored": gdrive_to_download_url("https://drive.google.com/file/d/1wgTdAnFoN1MbQ1kfk3uI4ByRhay1zgfI/view?usp=drive_link"),
    "mp3_animated_gospel": gdrive_to_download_url("https://drive.google.com/file/d/1sW2DmcR0RMEnpEs8uAXI7dBq09sjStq7/view?usp=drive_link"),
}

# Test endpoints configuration
ENDPOINTS = [
    # === Health & Toolkit Endpoints ===
    {
        "name": "Health Check",
        "method": "GET",
        "path": "/health",
        "auth": False,
        "payload": None,
        "expected": 200
    },
    {
        "name": "Toolkit: Authenticate",
        "method": "GET", 
        "path": "/v1/toolkit/authenticate",
        "auth": True,
        "payload": None,
        "expected": 200
    },
    {
        "name": "Toolkit: Test",
        "method": "GET",
        "path": "/v1/toolkit/test",
        "auth": True,
        "payload": None,
        "expected": 200
    },
    {
        "name": "Toolkit: Job Status",
        "method": "POST",
        "path": "/v1/toolkit/job/status",
        "auth": True,
        "payload": {"job_id": "test-123"},
        "expected": [200, 404]  # 404 if job doesn't exist
    },
    {
        "name": "Toolkit: Jobs Status",
        "method": "POST",
        "path": "/v1/toolkit/jobs/status",
        "auth": True,
        "payload": {
            "job_ids": ["test-123", "test-456"]
        },
        "expected": [200, 404]
    },
    
    # === Audio Endpoints ===
    {
        "name": "Audio: Concatenate",
        "method": "POST",
        "path": "/v1/audio/concatenate",
        "auth": True,
        "payload": {
            "audio_urls": [
                {"audio_url": TEST_MEDIA_URLS["mp3_christianity_explored"]},
                {"audio_url": TEST_MEDIA_URLS["mp3_animated_gospel"]}
            ]
        },
        "expected": [200, 202]
    },
    
    # === Code Execution Endpoints ===
    {
        "name": "Code: Execute Python",
        "method": "POST",
        "path": "/v1/code/execute/python",
        "auth": True,
        "payload": {
            "code": "print('Hello from Cloud API test!')",
            "timeout": 5
        },
        "expected": [200, 202]
    },
    
    # === FFmpeg Endpoints ===
    {
        "name": "FFmpeg: Compose",
        "method": "POST",
        "path": "/v1/ffmpeg/compose",
        "auth": True,
        "payload": {
            "inputs": [
                {
                    "file_url": TEST_MEDIA_URLS["mp4_321_gospel"],
                    "options": [{"option": "-t", "argument": 5}]
                }
            ],
            "outputs": [
                {
                    "options": [
                        {"option": "-c:v", "argument": "libx264"},
                        {"option": "-crf", "argument": 23}
                    ]
                }
            ]
        },
        "expected": [200, 202]
    },
    
    # === Image Endpoints ===
    {
        "name": "Image: Convert to Video",
        "method": "POST",
        "path": "/v1/image/convert/video",
        "auth": True,
        "payload": {
            "image_url": "https://via.placeholder.com/1920x1080",
            "length": 5,
            "frame_rate": 30
        },
        "expected": [200, 202]
    },
    {
        "name": "Image: Screenshot Webpage",
        "method": "POST",
        "path": "/v1/image/screenshot/webpage",
        "auth": True,
        "payload": {
            "url": "https://www.example.com",
            "viewport_width": 1920,
            "viewport_height": 1080,
            "full_page": False
        },
        "expected": [200, 202, 404]  # May not be deployed
    },
    
    # === Media Endpoints ===
    {
        "name": "Media: Convert",
        "method": "POST",
        "path": "/v1/media/convert",
        "auth": True,
        "payload": {
            "media_url": TEST_MEDIA_URLS["mp4_christianity_explored"],
            "format": "mp4"
        },
        "expected": [200, 202]
    },
    {
        "name": "Media: Convert to MP3",
        "method": "POST",
        "path": "/v1/media/convert/mp3",
        "auth": True,
        "payload": {
            "media_url": TEST_MEDIA_URLS["mp4_animated_gospel"],
            "bitrate": "128k"
        },
        "expected": [200, 202]
    },
    {
        "name": "Media: Feedback",
        "method": "GET",
        "path": "/v1/media/feedback",
        "auth": False,  # Static page doesn't require auth
        "payload": None,
        "expected": [200, 500]  # May return 500 if feedback files not found
    },
    {
        "name": "Media: Transcribe",
        "method": "POST",
        "path": "/v1/media/transcribe",
        "auth": True,
        "payload": {
            "media_url": TEST_MEDIA_URLS["mp4_321_gospel"],
            "task": "transcribe",
            "include_text": True
        },
        "expected": [200, 202]
    },
    {
        "name": "Media: Silence Detection",
        "method": "POST",
        "path": "/v1/media/silence",
        "auth": True,
        "payload": {
            "media_url": TEST_MEDIA_URLS["mp4_christianity_explored"],
            "duration": 0.5,
            "noise": "-30dB"
        },
        "expected": [200, 202]
    },
    {
        "name": "Media: Metadata",
        "method": "POST",
        "path": "/v1/media/metadata",
        "auth": True,
        "payload": {
            "media_url": TEST_MEDIA_URLS["mp4_321_gospel"]
        },
        "expected": [200, 202]
    },
    
    # === S3 Endpoints ===
    {
        "name": "S3: Upload",
        "method": "POST",
        "path": "/v1/s3/upload",
        "auth": True,
        "payload": {
            "file_url": "https://via.placeholder.com/150",
            "filename": "test-image.jpg",
            "public": False
        },
        "expected": [200, 202, 500]  # May fail without S3 config
    },
    
    # === Video Endpoints ===
    {
        "name": "Video: Caption",
        "method": "POST",
        "path": "/v1/video/caption",
        "auth": True,
        "payload": {
            "video_url": TEST_MEDIA_URLS["mp4_321_gospel"],
            "settings": {"font_size": 24}
        },
        "expected": [200, 202]
    },
    {
        "name": "Video: Concatenate",
        "method": "POST",
        "path": "/v1/video/concatenate",
        "auth": True,
        "payload": {
            "video_urls": [
                {"video_url": TEST_MEDIA_URLS["mp4_christianity_explored"]},
                {"video_url": TEST_MEDIA_URLS["mp4_animated_gospel"]}
            ]
        },
        "expected": [200, 202]
    },
    {
        "name": "Video: Thumbnail",
        "method": "POST",
        "path": "/v1/video/thumbnail",
        "auth": True,
        "payload": {
            "video_url": TEST_MEDIA_URLS["mp4_321_gospel"],
            "second": 5
        },
        "expected": [200, 202]
    },
    {
        "name": "Video: Cut",
        "method": "POST",
        "path": "/v1/video/cut",
        "auth": True,
        "payload": {
            "video_url": TEST_MEDIA_URLS["mp4_christianity_explored"],
            "cuts": [
                {"start": "00:00:02", "end": "00:00:05"},
                {"start": "00:00:07", "end": "00:00:10"}
            ]
        },
        "expected": [200, 202]
    },
    {
        "name": "Video: Split",
        "method": "POST",
        "path": "/v1/video/split",
        "auth": True,
        "payload": {
            "video_url": TEST_MEDIA_URLS["mp4_animated_gospel"],
            "splits": [
                {"start": "00:00:00", "end": "00:00:05"},
                {"start": "00:00:10", "end": "00:00:15"}
            ]
        },
        "expected": [200, 202]
    },
    {
        "name": "Video: Trim",
        "method": "POST",
        "path": "/v1/video/trim",
        "auth": True,
        "payload": {
            "video_url": TEST_MEDIA_URLS["mp4_321_gospel"],
            "start": "00:00:00",
            "end": "00:00:10"
        },
        "expected": [200, 202]
    }
]

def test_endpoint(endpoint_config):
    """Test a single endpoint and return result"""
    url = f"{BASE_URL}{endpoint_config['path']}"
    headers = {}
    
    # Add authentication if required
    if endpoint_config.get("auth"):
        headers["X-API-Key"] = API_KEY
    
    # Prepare request
    method = endpoint_config["method"]
    params = endpoint_config.get("params")
    payload = endpoint_config.get("payload")
    
    try:
        # Make request with longer timeout for cloud
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=payload, headers=headers, timeout=30)
        else:
            return {
                "endpoint": endpoint_config["path"],
                "name": endpoint_config["name"],
                "status": "FAIL",
                "error": f"Unsupported method: {method}",
                "response_time": 0
            }
        
        response_time = time.time() - start_time
        
        # Check if response is as expected
        expected = endpoint_config["expected"]
        if isinstance(expected, list):
            success = response.status_code in expected
        else:
            success = response.status_code == expected
        
        # Detect if response is synchronous (has immediate result)
        is_sync = False
        try:
            body = response.json()
            # If response time < 1s and has result data, it's synchronous
            if response_time < 1.0 and body:
                if "result" in body or "data" in body or "metadata" in body:
                    is_sync = True
                # If it has job_id but also has complete data, still sync
                elif "job_id" in body and any(k in body for k in ["result", "output", "url"]):
                    is_sync = True
        except:
            body = None
        
        return {
            "endpoint": endpoint_config["path"],
            "name": endpoint_config["name"],
            "status": "PASS" if success else "FAIL",
            "response_code": response.status_code,
            "expected_code": expected,
            "response_time": round(response_time, 3),
            "is_sync": is_sync,
            "error": None if success else f"Expected {expected}, got {response.status_code}"
        }
        
    except requests.exceptions.Timeout:
        return {
            "endpoint": endpoint_config["path"],
            "name": endpoint_config["name"],
            "status": "FAIL",
            "error": "Request timeout",
            "response_time": 30.0
        }
    except requests.exceptions.ConnectionError:
        return {
            "endpoint": endpoint_config["path"],
            "name": endpoint_config["name"],
            "status": "FAIL",
            "error": "Connection failed",
            "response_time": 0
        }
    except Exception as e:
        return {
            "endpoint": endpoint_config["path"],
            "name": endpoint_config["name"],
            "status": "FAIL",
            "error": str(e),
            "response_time": 0
        }

def main():
    """Run all tests and generate report"""
    print(f"\n{'='*60}")
    print(f"CLOUD API TESTS - {BASE_URL}")
    print(f"{'='*60}\n")
    
    # Check if API is reachable
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=30)
        print(f"✓ Cloud API is reachable\n")
    except Exception as e:
        print(f"✗ Cannot reach Cloud API at {BASE_URL}")
        print(f"  Error: {str(e)}")
        print(f"  Check your internet connection and CLOUD_BASE_URL\n")
        sys.exit(1)
    
    # Run all tests
    results = []
    for endpoint in ENDPOINTS:
        print(f"Testing: {endpoint['name']}...", end=" ")
        result = test_endpoint(endpoint)
        results.append(result)
        
        # Print result
        if result["status"] == "PASS":
            sync_note = " (sync)" if result.get("is_sync") else ""
            print(f"✓ PASS{sync_note}")
        else:
            print(f"✗ FAIL - {result.get('error', 'Unknown error')}")
    
    # Calculate summary
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    # Save report (overwrites previous)
    report = {
        "test_type": "cloud",
        "base_url": BASE_URL,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate
        },
        "results": results
    }
    
    report_dir = Path("tests/results")
    report_dir.mkdir(exist_ok=True)
    
    report_file = report_dir / "cloud_test_results.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {report_file}")
    
    # Simple pass/fail by endpoint file
    simple_report = report_dir / "cloud_test_summary.txt"
    with open(simple_report, "w") as f:
        f.write(f"CLOUD TEST RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*60}\n\n")
        for result in results:
            status = "PASS" if result["status"] == "PASS" else "FAIL"
            f.write(f"{status}: {result['name']} ({result['endpoint']})\n")
        f.write(f"\n{'='*60}\n")
        f.write(f"Pass Rate: {pass_rate:.1f}% ({passed}/{total})\n")
    
    print(f"Summary saved to: {simple_report}")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
