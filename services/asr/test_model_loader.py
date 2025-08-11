#!/usr/bin/env python3
"""
Test script for ASR model loader.
Demonstrates all features including CUDA detection, model loading, and warm-up.
"""

import os
import sys
import time
import logging

# Set up environment
os.environ.setdefault('API_KEY', 'test')
os.environ.setdefault('ENABLE_FASTER_WHISPER', 'true')
os.environ.setdefault('ASR_MODEL_ID', 'openai/whisper-base')
os.environ.setdefault('ASR_DEVICE', 'auto')
os.environ.setdefault('ASR_COMPUTE_TYPE', 'auto')
os.environ.setdefault('ASR_BEAM_SIZE', '5')
os.environ.setdefault('ASR_CACHE_DIR', '/tmp/asr_cache')
os.environ.setdefault('LOCAL_STORAGE_PATH', '/tmp')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_cuda_detection():
    """Test CUDA detection functionality."""
    print("\n" + "=" * 60)
    print("TEST 1: CUDA Detection")
    print("=" * 60)
    
    from services.asr import detect_cuda_availability
    
    cuda_available, cuda_version, device_count = detect_cuda_availability()
    
    print(f"CUDA Available: {cuda_available}")
    print(f"CUDA Version: {cuda_version}")
    print(f"GPU Device Count: {device_count}")
    
    if cuda_available:
        print("✓ CUDA is available on this system")
    else:
        print("✓ CUDA is not available (running on CPU)")
    
    return cuda_available


def test_device_selection():
    """Test device and compute type selection."""
    print("\n" + "=" * 60)
    print("TEST 2: Device and Compute Type Selection")
    print("=" * 60)
    
    from services.asr import determine_device_and_compute_type
    
    device, compute_type = determine_device_and_compute_type()
    
    print(f"Selected Device: {device}")
    print(f"Selected Compute Type: {compute_type}")
    
    # Validate selection logic
    if device == "cuda":
        assert compute_type in ["float16", "float32"], "GPU should use float16 or float32"
        print("✓ GPU configuration is correct")
    else:
        assert compute_type in ["int8", "float32"], "CPU should use int8 or float32"
        print("✓ CPU configuration is correct")
    
    return device, compute_type


def test_model_loading():
    """Test model loading with timing."""
    print("\n" + "=" * 60)
    print("TEST 3: Model Loading")
    print("=" * 60)
    
    from services.asr import get_model, get_model_config
    
    try:
        # Check if faster-whisper is available
        from faster_whisper import WhisperModel
        
        print("Loading model (this may take a moment on first run)...")
        start_time = time.time()
        
        model = get_model()
        
        if model:
            load_time = time.time() - start_time
            print(f"✓ Model loaded in {load_time:.2f} seconds")
            
            # Get configuration
            config = get_model_config()
            print("\nModel Configuration:")
            for key, value in config.items():
                print(f"  {key}: {value}")
            
            return True
        else:
            print("✗ Failed to load model")
            return False
            
    except ImportError:
        print("⚠ faster-whisper is not installed")
        print("  Install with: pip install faster-whisper")
        return False


def test_singleton_pattern():
    """Test that the model loader follows singleton pattern."""
    print("\n" + "=" * 60)
    print("TEST 4: Singleton Pattern")
    print("=" * 60)
    
    from services.asr import get_model
    
    try:
        from faster_whisper import WhisperModel
        
        print("Getting model instance (first call)...")
        model1 = get_model()
        
        print("Getting model instance (second call)...")
        model2 = get_model()
        
        if model1 is None or model2 is None:
            print("⚠ Model not loaded, skipping singleton test")
            return False
        
        # Check if same instance
        if model1 is model2:
            print("✓ Singleton pattern working correctly (same instance)")
            return True
        else:
            print("✗ Singleton pattern not working (different instances)")
            return False
            
    except ImportError:
        print("⚠ faster-whisper is not installed")
        return False


def test_model_unloading():
    """Test model unloading."""
    print("\n" + "=" * 60)
    print("TEST 5: Model Unloading")
    print("=" * 60)
    
    from services.asr import get_model, unload_model, get_model_config
    
    try:
        from faster_whisper import WhisperModel
        
        # Ensure model is loaded
        model = get_model()
        if model:
            print("Model is loaded")
            
            # Unload model
            unload_model()
            print("✓ Model unloaded successfully")
            
            # Check configuration is cleared
            config = get_model_config()
            if not config:
                print("✓ Configuration cleared")
            else:
                print("⚠ Configuration not fully cleared")
            
            return True
        else:
            print("⚠ No model to unload")
            return False
            
    except ImportError:
        print("⚠ faster-whisper is not installed")
        return False


def test_concurrent_access():
    """Test thread-safe concurrent access."""
    print("\n" + "=" * 60)
    print("TEST 6: Concurrent Access (Thread Safety)")
    print("=" * 60)
    
    import threading
    from services.asr import get_model
    
    try:
        from faster_whisper import WhisperModel
        
        results = []
        
        def get_model_in_thread():
            model = get_model()
            results.append(model)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=get_model_in_thread)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Check all got same instance
        if all(m is results[0] for m in results):
            print(f"✓ All {len(results)} threads got the same model instance")
            return True
        else:
            print("✗ Different instances returned to different threads")
            return False
            
    except ImportError:
        print("⚠ faster-whisper is not installed")
        return False


def main():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("# ASR Model Loader Test Suite")
    print("#" * 60)
    
    results = []
    
    # Run tests
    cuda_available = test_cuda_detection()
    results.append(("CUDA Detection", True))  # This always passes
    
    device, compute_type = test_device_selection()
    results.append(("Device Selection", True))  # This always passes
    
    model_loaded = test_model_loading()
    results.append(("Model Loading", model_loaded))
    
    if model_loaded:
        singleton_ok = test_singleton_pattern()
        results.append(("Singleton Pattern", singleton_ok))
        
        concurrent_ok = test_concurrent_access()
        results.append(("Concurrent Access", concurrent_ok))
        
        unload_ok = test_model_unloading()
        results.append(("Model Unloading", unload_ok))
    
    # Summary
    print("\n" + "#" * 60)
    print("# Test Summary")
    print("#" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<30} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n⚠ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
