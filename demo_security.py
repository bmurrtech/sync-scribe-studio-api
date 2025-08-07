#!/usr/bin/env python3
"""
Security Middleware Demonstration
Shows how to use the FastAPI-compatible security middleware with Flask.
"""

import os
import sys
import time
import requests
from threading import Thread

def run_demo_server():
    """Run the demo server in a separate thread"""
    # Set environment variable for demo
    os.environ['DB_TOKEN'] = 'demo_api_key_12345678901234567890123456789'
    
    # Import and run the example server
    from server.example_integration import create_secure_app
    app = create_secure_app()
    
    print("Starting demo server...")
    app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)

def test_endpoints():
    """Test the security endpoints"""
    base_url = "http://127.0.0.1:5555"
    valid_api_key = 'demo_api_key_12345678901234567890123456789'
    invalid_api_key = 'invalid_key'
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    print("\n" + "="*60)
    print("SECURITY MIDDLEWARE DEMONSTRATION")
    print("="*60)
    
    # Test 1: Public endpoint (no auth required)
    print("\n1. Testing public endpoint (rate limited only)...")
    try:
        response = requests.get(f"{base_url}/api/public", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Protected endpoint with valid API key
    print("\n2. Testing protected endpoint with valid Bearer token...")
    try:
        headers = {'Authorization': f'Bearer {valid_api_key}'}
        response = requests.get(f"{base_url}/api/protected", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Protected endpoint with valid X-API-KEY header
    print("\n3. Testing protected endpoint with X-API-KEY header...")
    try:
        headers = {'X-API-KEY': valid_api_key}
        response = requests.get(f"{base_url}/api/protected", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Protected endpoint with invalid API key
    print("\n4. Testing protected endpoint with invalid API key...")
    try:
        headers = {'Authorization': f'Bearer {invalid_api_key}'}
        response = requests.get(f"{base_url}/api/protected", headers=headers, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Protected endpoint with no API key
    print("\n5. Testing protected endpoint with no API key...")
    try:
        response = requests.get(f"{base_url}/api/protected", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 6: Rate limiting - Admin endpoint (10/minute limit)
    print("\n6. Testing rate limiting on admin endpoint (10/minute)...")
    headers = {'Authorization': f'Bearer {valid_api_key}'}
    
    # Make several requests quickly
    for i in range(3):
        try:
            response = requests.get(f"{base_url}/api/admin", headers=headers, timeout=5)
            print(f"   Request {i+1}: Status {response.status_code}")
            if response.status_code == 429:
                print(f"   Rate limited: {response.json()}")
                break
        except Exception as e:
            print(f"   Error on request {i+1}: {e}")
    
    # Test 7: Health checks
    print("\n7. Testing health endpoints...")
    try:
        # Basic health
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Basic health - Status: {response.status_code}")
        
        # Detailed health  
        response = requests.get(f"{base_url}/health/detailed", timeout=5)
        print(f"   Detailed health - Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Overall status: {health_data.get('status')}")
            print(f"   Components: {list(health_data.get('components', {}).keys())}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 8: OpenAPI documentation
    print("\n8. Testing OpenAPI endpoints...")
    try:
        # OpenAPI schema
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        print(f"   OpenAPI schema - Status: {response.status_code}")
        
        # Documentation page
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"   API docs - Status: {response.status_code}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 9: Service information
    print("\n9. Testing service information endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            service_info = response.json()
            print(f"   Service: {service_info.get('service')}")
            print(f"   Version: {service_info.get('version')}")
            print(f"   Authentication required: {service_info.get('authentication', {}).get('required')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)
    print(f"\nTo manually test endpoints:")
    print(f"  curl {base_url}/api/public")
    print(f"  curl -H 'Authorization: Bearer {valid_api_key}' {base_url}/api/protected")
    print(f"  curl -H 'X-API-KEY: {valid_api_key}' {base_url}/api/protected")
    print(f"  curl {base_url}/health")
    print(f"  curl {base_url}/docs")

def main():
    """Main demonstration function"""
    print("FastAPI-Compatible Security Middleware Demo")
    print("==========================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--server-only':
        # Just run the server
        print("Running server only...")
        run_demo_server()
    else:
        # Run full demo with tests
        # Start server in background thread
        server_thread = Thread(target=run_demo_server, daemon=True)
        server_thread.start()
        
        # Run tests
        test_endpoints()
        
        print("\nDemo completed. Server is still running on http://127.0.0.1:5555")
        print("Press Ctrl+C to stop the server.")
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")

if __name__ == '__main__':
    main()
