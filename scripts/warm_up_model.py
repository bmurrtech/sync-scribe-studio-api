#!/usr/bin/env python3
"""
Model warm-up script for container initialization.
This script pre-loads the ASR model based on environment configuration.
"""

import os
import sys
import logging

# Add parent directory to path to import config and services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main warm-up function."""
    logger.info("=" * 60)
    logger.info("Starting ASR Model Warm-up")
    logger.info("=" * 60)
    
    # Check if faster-whisper is enabled
    enable_faster_whisper = os.environ.get('ENABLE_FASTER_WHISPER', 'false').lower() == 'true'
    
    if not enable_faster_whisper:
        logger.info("ENABLE_FASTER_WHISPER is not set to 'true', skipping warm-up")
        return 0
    
    # Check if warm-up should be skipped (useful for CPU-only builds in CI)
    skip_warmup = os.environ.get('SKIP_MODEL_WARMUP', 'false').lower() == 'true'
    
    if skip_warmup:
        logger.info("SKIP_MODEL_WARMUP is set to 'true', skipping warm-up")
        return 0
    
    try:
        # Import the model loader
        from services.asr.model_loader import get_model, get_model_config
        
        # Attempt to load the model
        logger.info("Loading ASR model...")
        model = get_model()
        
        if model:
            logger.info("✓ Model loaded and warmed up successfully")
            
            # Display configuration
            config = get_model_config()
            logger.info("Model configuration:")
            for key, value in config.items():
                logger.info(f"  {key}: {value}")
            
            logger.info("=" * 60)
            logger.info("ASR Model Warm-up Complete")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("✗ Failed to load model")
            logger.info("Continuing without pre-loaded model (will load on first request)")
            return 0  # Don't fail the container startup
            
    except ImportError as e:
        logger.warning(f"Could not import model_loader: {e}")
        logger.info("Continuing without pre-loaded model")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error during warm-up: {e}")
        logger.info("Continuing without pre-loaded model")
        return 0

if __name__ == "__main__":
    sys.exit(main())
