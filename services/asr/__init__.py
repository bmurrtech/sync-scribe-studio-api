"""
ASR (Automatic Speech Recognition) service module.
Provides singleton model loading and transcription capabilities using faster-whisper.
"""

from .model_loader import (
    get_model,
    get_model_config,
    load_model,
    unload_model,
    detect_cuda_availability,
    determine_device_and_compute_type,
)

__all__ = [
    'get_model',
    'get_model_config',
    'load_model',
    'unload_model',
    'detect_cuda_availability',
    'determine_device_and_compute_type',
]

# Module version
__version__ = '1.0.0'
