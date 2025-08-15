"""
Wrapper module for loading faster-whisper with fallback handling for library issues.
This handles ctranslate2 library loading issues in restricted environments like Cloud Run.
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

def try_import_faster_whisper():
    """
    Try to import faster_whisper with various workarounds for library loading issues.
    
    Returns:
        tuple: (success: bool, WhisperModel: class or None, error_msg: str or None)
    """
    # First, try direct import
    try:
        from faster_whisper import WhisperModel
        logger.info("Successfully imported faster_whisper (direct import)")
        return True, WhisperModel, None
    except ImportError as e:
        error_msg = str(e)
        logger.warning(f"Direct import failed: {error_msg}")
        
        # Check if it's the executable stack error
        if "cannot enable executable stack" in error_msg or "libctranslate2" in error_msg:
            logger.info("Attempting workaround for ctranslate2 library issue...")
            
            # Try setting environment variable to disable executable stack checks
            os.environ['EXECSTACK'] = '0'
            os.environ['LD_BIND_NOW'] = '1'
            
            # For Cloud Run, try to use the system's OpenMP library
            try:
                import ctypes
                # Try to preload libgomp to avoid conflicts
                try:
                    ctypes.CDLL('libgomp.so.1', mode=ctypes.RTLD_GLOBAL)
                    logger.info("Preloaded libgomp.so.1")
                except:
                    pass
                
                # Now try importing again
                from faster_whisper import WhisperModel
                logger.info("Successfully imported faster_whisper (after workaround)")
                return True, WhisperModel, None
            except ImportError as e2:
                error_msg = f"Workaround failed: {str(e2)}"
                logger.error(error_msg)
        
        return False, None, error_msg

# Try to import on module load
FASTER_WHISPER_AVAILABLE, WhisperModel, IMPORT_ERROR = try_import_faster_whisper()

if not FASTER_WHISPER_AVAILABLE:
    logger.error(f"Failed to load faster_whisper: {IMPORT_ERROR}")
    # Create a dummy class to prevent immediate failures
    class WhisperModel:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(f"Faster-Whisper not available: {IMPORT_ERROR}")
