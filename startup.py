"""
Application startup and warm-up utilities.
Handles model preloading and health check readiness.
"""

import os
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Global variable to track initialization status
_initialization_status = {
    'model_loaded': False,
    'model_load_time': None,
    'model_error': None,
    'initialized_at': None,
}


def warm_up_asr_model() -> Dict[str, Any]:
    """
    Warm up the ASR model if enabled.
    
    Returns:
        dict: Status information about the warm-up process
    """
    global _initialization_status
    
    # Check if ASR warm-up is enabled
    enable_warm_up = os.environ.get('ENABLE_MODEL_WARM_UP', 'false').lower() == 'true'
    enable_faster_whisper = os.environ.get('ENABLE_FASTER_WHISPER', 'false').lower() == 'true'
    
    if not enable_warm_up:
        logger.info("Model warm-up is disabled (ENABLE_MODEL_WARM_UP=false)")
        return {
            'status': 'skipped',
            'reason': 'warm_up_disabled',
            'message': 'Model warm-up is disabled'
        }
    
    if not enable_faster_whisper:
        logger.info("ASR model is disabled (ENABLE_FASTER_WHISPER=false)")
        return {
            'status': 'skipped',
            'reason': 'asr_disabled',
            'message': 'ASR model is disabled'
        }
    
    logger.info("=" * 60)
    logger.info("Starting Application Warm-up")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    try:
        # Import ASR model loader
        from services.asr import get_model
        
        logger.info("Loading ASR model for warm-up...")
        
        # Attempt to load the model
        model = get_model()
        
        if model is not None:
            load_time = time.time() - start_time
            
            _initialization_status['model_loaded'] = True
            _initialization_status['model_load_time'] = load_time
            _initialization_status['initialized_at'] = time.time()
            
            logger.info(f"✓ ASR model loaded successfully in {load_time:.2f} seconds")
            logger.info("=" * 60)
            
            return {
                'status': 'success',
                'model_loaded': True,
                'load_time': load_time,
                'message': f'Model loaded in {load_time:.2f}s'
            }
        else:
            error_msg = "Model loader returned None"
            _initialization_status['model_error'] = error_msg
            
            logger.warning(f"Model warm-up completed with issues: {error_msg}")
            
            return {
                'status': 'partial',
                'model_loaded': False,
                'error': error_msg,
                'message': 'Model warm-up failed but application can continue'
            }
            
    except ImportError as e:
        error_msg = f"Failed to import ASR module: {e}"
        _initialization_status['model_error'] = error_msg
        
        logger.error(error_msg)
        logger.info("Application will continue without ASR model")
        
        return {
            'status': 'error',
            'model_loaded': False,
            'error': str(e),
            'message': 'ASR module not available'
        }
        
    except Exception as e:
        error_msg = f"Unexpected error during warm-up: {e}"
        _initialization_status['model_error'] = error_msg
        
        logger.error(error_msg)
        logger.exception("Detailed error information:")
        
        return {
            'status': 'error',
            'model_loaded': False,
            'error': str(e),
            'message': 'Warm-up failed with unexpected error'
        }


def get_initialization_status() -> Dict[str, Any]:
    """
    Get the current initialization status.
    
    Returns:
        dict: Current initialization status
    """
    return _initialization_status.copy()


def is_ready() -> bool:
    """
    Check if the application is ready to serve requests.
    
    Returns:
        bool: True if ready, False otherwise
    """
    # Check if warm-up is enabled
    enable_warm_up = os.environ.get('ENABLE_MODEL_WARM_UP', 'false').lower() == 'true'
    enable_faster_whisper = os.environ.get('ENABLE_FASTER_WHISPER', 'false').lower() == 'true'
    
    # If warm-up is disabled or ASR is disabled, always ready
    if not enable_warm_up or not enable_faster_whisper:
        return True
    
    # If warm-up is enabled, check if model is loaded
    return _initialization_status['model_loaded']


def perform_startup_tasks():
    """
    Perform all startup tasks including model warm-up.
    This is the main entry point for application initialization.
    """
    logger.info("Performing startup tasks...")
    
    # Warm up ASR model if enabled
    warm_up_result = warm_up_asr_model()
    
    # Log the result
    if warm_up_result['status'] == 'success':
        logger.info("✓ All startup tasks completed successfully")
    elif warm_up_result['status'] == 'skipped':
        logger.info("✓ Startup tasks completed (warm-up skipped)")
    else:
        logger.warning(f"⚠ Startup tasks completed with status: {warm_up_result['status']}")
    
    return warm_up_result


# For testing purposes
if __name__ == "__main__":
    import sys
    
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test warm-up with different configurations
    test_configs = [
        {},  # Default (disabled)
        {'ENABLE_MODEL_WARM_UP': 'true'},  # Warm-up enabled but ASR disabled
        {'ENABLE_MODEL_WARM_UP': 'true', 'ENABLE_FASTER_WHISPER': 'true'},  # Both enabled
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n{'=' * 60}")
        print(f"Test Configuration {i}:")
        for key, value in config.items():
            os.environ[key] = value
            print(f"  {key} = {value}")
        print(f"{'=' * 60}")
        
        result = perform_startup_tasks()
        print(f"Result: {result}")
        
        status = get_initialization_status()
        print(f"Status: {status}")
        
        is_ready_flag = is_ready()
        print(f"Is Ready: {is_ready_flag}")
