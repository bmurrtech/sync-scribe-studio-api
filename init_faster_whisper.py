#!/usr/bin/env python3
"""
Initialization script to handle faster-whisper import issues in Cloud Run.
This script attempts to work around the ctranslate2 library loading issue.
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_faster_whisper():
    """
    Initialize faster-whisper with workarounds for ctranslate2 issues.
    """
    # Set environment variables that might help
    os.environ['LD_BIND_NOW'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'  # Limit OpenMP threads
    
    # Try to import faster_whisper
    try:
        import faster_whisper
        logger.info("✓ Successfully imported faster_whisper")
        return True
    except ImportError as e:
        error_msg = str(e)
        logger.warning(f"Failed to import faster_whisper: {error_msg}")
        
        # Check if it's the executable stack error
        if "cannot enable executable stack" in error_msg:
            logger.info("Detected executable stack issue - this is a known issue with ctranslate2 in Cloud Run")
            logger.info("Falling back to OpenAI Whisper...")
            
            # Set environment variable to use OpenAI Whisper instead
            os.environ['ENABLE_OPENAI_WHISPER'] = 'true'
            
            # Try to import OpenAI Whisper
            try:
                import whisper
                logger.info("✓ Successfully imported OpenAI Whisper as fallback")
                return True
            except ImportError:
                logger.error("OpenAI Whisper is not installed either")
                logger.info("Installing OpenAI Whisper...")
                subprocess.run([sys.executable, "-m", "pip", "install", "openai-whisper"], check=True)
                logger.info("✓ Installed OpenAI Whisper")
                return True
        
        return False

if __name__ == "__main__":
    success = init_faster_whisper()
    sys.exit(0 if success else 1)
