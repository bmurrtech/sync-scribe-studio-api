"""
Singleton model loader utility for ASR service.
Loads WhisperModel from faster-whisper once per Gunicorn worker.
Auto-detects CUDA availability and optimizes compute type accordingly.
"""

import os
import time
import logging
import threading
import numpy as np
from typing import Optional
from pathlib import Path

# Set up logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import (
    ASR_MODEL_ID,
    ASR_DEVICE,
    ASR_COMPUTE_TYPE,
    ASR_BEAM_SIZE,
    ASR_BATCH_SIZE,
    ASR_NUM_WORKERS,
    ASR_CACHE_DIR,
    LOCAL_STORAGE_PATH,
    ENABLE_OPENAI_WHISPER
)

# Try to import faster-whisper with workarounds for library issues
try:
    from .faster_whisper_loader import FASTER_WHISPER_AVAILABLE, WhisperModel, IMPORT_ERROR
    if not FASTER_WHISPER_AVAILABLE:
        logger.warning(f"faster-whisper not available: {IMPORT_ERROR}")
except ImportError as e:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None
    logger.warning(f"Failed to load faster_whisper_loader: {e}")

# Try to import torch for CUDA detection
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.info("PyTorch not available. Will use CPU for inference.")

# Module-level variables for singleton pattern
_model: Optional['WhisperModel'] = None
_model_lock = threading.Lock()
_model_config = {}


def detect_cuda_availability() -> tuple[bool, str, int]:
    """
    Auto-detect CUDA availability and capabilities.
    
    Returns:
        tuple: (cuda_available, cuda_version, device_count)
    """
    if not TORCH_AVAILABLE:
        logger.info("PyTorch not available, defaulting to CPU")
        return False, "N/A", 0
    
    try:
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            cuda_version = torch.version.cuda or "Unknown"
            device_count = torch.cuda.device_count()
            
            # Log detailed GPU information
            for i in range(device_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)  # Convert to GB
                logger.info(f"GPU {i}: {gpu_name}, Memory: {gpu_memory:.2f} GB")
            
            return True, cuda_version, device_count
        else:
            logger.info("CUDA not available on this system")
            return False, "N/A", 0
    except Exception as e:
        logger.warning(f"Error detecting CUDA: {e}")
        return False, "N/A", 0


def determine_device_and_compute_type() -> tuple[str, str]:
    """
    Determine the optimal device and compute type based on system capabilities.
    Implements best practices for CPU vs GPU performance optimization.
    
    Returns:
        tuple: (device, compute_type)
    """
    # Check if user has explicitly set device preference
    if ASR_DEVICE and ASR_DEVICE != 'auto':
        device = ASR_DEVICE
        logger.info(f"Using user-specified device: {device}")
    else:
        # Auto-detect best device
        cuda_available, cuda_version, device_count = detect_cuda_availability()
        
        if cuda_available and device_count > 0:
            device = "cuda"
            logger.info(f"Auto-detected CUDA {cuda_version} with {device_count} GPU(s)")
        else:
            device = "cpu"
            logger.info("Auto-detected CPU as compute device")
    
    # Determine compute type based on device and best practices
    if ASR_COMPUTE_TYPE and ASR_COMPUTE_TYPE != 'auto':
        compute_type = ASR_COMPUTE_TYPE
        logger.info(f"Using user-specified compute type: {compute_type}")
    else:
        if device == "cuda":
            # Use float16 for GPU (optimal performance/memory trade-off)
            compute_type = "float16"
            logger.info("Auto-selected float16 compute type for GPU (optimal for CUDA)")
        else:
            # Use int8 for CPU (best performance on CPU via quantization)
            compute_type = "int8"
            logger.info("Auto-selected int8 compute type for CPU (quantized for better speed)")
    
    # Validate and optimize compute type compatibility
    if device == "cuda" and compute_type in ["int8", "int8_float32"]:
        logger.warning("int8 quantization on GPU - using for VRAM efficiency, but float16 typically faster")
    elif device == "cpu" and compute_type == "float16":
        logger.warning("float16 on CPU may be slower than int8 quantization, consider int8 for better throughput")
    elif device == "cpu" and compute_type == "int8":
        logger.info("Using int8 quantization on CPU - optimal for throughput/accuracy balance")
    
    return device, compute_type


def warm_up_model(model: 'WhisperModel') -> float:
    """
    Perform a warm-up transcription to initialize the model.
    
    Args:
        model: The WhisperModel instance to warm up
    
    Returns:
        float: Time taken for warm-up in seconds
    """
    logger.info("Starting model warm-up...")
    start_time = time.time()
    
    try:
        # Create a 1-second dummy audio (16kHz sample rate, mono)
        sample_rate = 16000
        duration = 1.0  # 1 second
        num_samples = int(sample_rate * duration)
        
        # Generate silent audio (zeros)
        dummy_audio = np.zeros(num_samples, dtype=np.float32)
        
        # Add a small amount of noise to avoid complete silence
        # (some models may behave differently with complete silence)
        dummy_audio += np.random.normal(0, 0.001, num_samples).astype(np.float32)
        
        # Perform dummy transcription
        segments, _ = model.transcribe(
            dummy_audio,
            beam_size=1,  # Use smaller beam size for warm-up
            language="en",  # Specify language to avoid detection overhead
            without_timestamps=True,  # Skip timestamp generation for warm-up
            vad_filter=False,  # Disable VAD for warm-up
        )
        
        # Consume the generator to ensure full warm-up
        _ = list(segments)
        
        warm_up_time = time.time() - start_time
        logger.info(f"Model warm-up completed in {warm_up_time:.3f} seconds")
        
        return warm_up_time
        
    except Exception as e:
        warm_up_time = time.time() - start_time
        logger.error(f"Error during model warm-up: {e}")
        logger.info(f"Warm-up attempted for {warm_up_time:.3f} seconds")
        # Don't fail completely if warm-up fails
        return warm_up_time


def load_model(force_reload: bool = False) -> Optional['WhisperModel']:
    """
    Load the Whisper model with singleton pattern.
    The model is loaded once per worker process and cached.
    
    Args:
        force_reload: Force reload the model even if already loaded
    
    Returns:
        WhisperModel instance or None if loading fails
    """
    global _model, _model_config
    
    if not FASTER_WHISPER_AVAILABLE:
        logger.error("faster-whisper is not installed")
        return None
    
    # Faster-Whisper is now the default, only skip if explicitly using OpenAI Whisper
    if ENABLE_OPENAI_WHISPER:
        logger.warning("Using legacy OpenAI Whisper backend (ENABLE_OPENAI_WHISPER=true)")
        return None
    
    # Check if model is already loaded and not forcing reload
    if _model is not None and not force_reload:
        logger.debug("Using cached model instance")
        return _model
    
    with _model_lock:
        # Double-check after acquiring lock
        if _model is not None and not force_reload:
            return _model
        
        logger.info("=" * 60)
        logger.info("Initializing ASR Model Loader")
        logger.info("=" * 60)
        
        # Record start time
        total_start_time = time.time()
        
        # Determine device and compute type
        device, compute_type = determine_device_and_compute_type()
        
        # Ensure cache directory exists
        cache_dir = Path(ASR_CACHE_DIR)
        cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model cache directory: {cache_dir}")
        
        # Store configuration for reference
        _model_config = {
            'model_id': ASR_MODEL_ID,
            'device': device,
            'compute_type': compute_type,
            'beam_size': ASR_BEAM_SIZE,
            'cache_dir': str(cache_dir),
            'worker_pid': os.getpid(),
        }
        
        logger.info("Model Configuration:")
        for key, value in _model_config.items():
            logger.info(f"  {key}: {value}")
        
        # Load the model
        logger.info("-" * 60)
        
        # Convert model ID format if needed
        # Faster Whisper expects: "base", "small", "medium", "large", "large-v2", "large-v3"
        # Or a Hugging Face model ID like "openai/whisper-base" or "Systran/faster-whisper-base"
        model_name = ASR_MODEL_ID
        
        # Map common OpenAI and community model names to Faster Whisper compatible names
        model_mapping = {
            # OpenAI official models
            'openai/whisper-tiny': 'tiny',
            'openai/whisper-base': 'base', 
            'openai/whisper-small': 'small',
            'openai/whisper-medium': 'medium',
            'openai/whisper-large': 'large',
            'openai/whisper-large-v2': 'large-v2',
            'openai/whisper-large-v3': 'large-v3',
            # Short form variants
            'whisper-tiny': 'tiny',
            'whisper-base': 'base',
            'whisper-small': 'small',
            'whisper-medium': 'medium', 
            'whisper-large': 'large',
            'whisper-large-v2': 'large-v2',
            'whisper-large-v3': 'large-v3',
            # Community turbo variants (experimental)
            'whisper-large-v3-turbo': 'large-v3-turbo',
            'openai/whisper-large-v3-turbo': 'large-v3-turbo',
        }
        
        # Apply mapping if needed, with safe fallback
        if model_name in model_mapping:
            mapped_name = model_mapping[model_name]
            logger.info(f"Mapping model ID '{model_name}' to Faster Whisper format '{mapped_name}'")
            model_name = mapped_name
        elif model_name.startswith(('openai/', 'whisper-')) and model_name not in ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']:
            # Unknown model format, fallback to small with warning
            logger.warning(f"Unknown model format '{model_name}', falling back to 'small' for safety")
            logger.warning("Supported models: tiny, base, small, medium, large, large-v2, large-v3")
            model_name = 'small'
        
        logger.info(f"Loading model: {model_name} (original: {ASR_MODEL_ID})")
        load_start_time = time.time()
        
        try:
            _model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                download_root=str(cache_dir),
                local_files_only=False,  # Allow downloading if not cached
                num_workers=1,  # Number of workers for audio loading
            )
            
            load_time = time.time() - load_start_time
            logger.info(f"Loaded Faster-Whisper model: {model_name} (configured as {ASR_MODEL_ID}) in {load_time:.3f} seconds")
            
            # Perform warm-up
            logger.info("-" * 60)
            warm_up_time = warm_up_model(_model)
            
            # Calculate total initialization time
            total_time = time.time() - total_start_time
            
            # Log summary
            logger.info("=" * 60)
            logger.info("Model Initialization Summary:")
            logger.info(f"  Model: {ASR_MODEL_ID}")
            logger.info(f"  Device: {device}")
            logger.info(f"  Compute Type: {compute_type}")
            logger.info(f"  Load Time: {load_time:.3f} seconds")
            logger.info(f"  Warm-up Time: {warm_up_time:.3f} seconds")
            logger.info(f"  Total Time: {total_time:.3f} seconds")
            logger.info(f"  Worker PID: {os.getpid()}")
            logger.info("=" * 60)
            
            return _model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.exception("Detailed error information:")
            _model = None
            return None


def get_model() -> Optional['WhisperModel']:
    """
    Get the singleton Whisper model instance.
    This is the main entry point for callers.
    
    Returns:
        WhisperModel instance or None if not available
    """
    if _model is None:
        return load_model()
    return _model


def get_model_config() -> dict:
    """
    Get the current model configuration.
    
    Returns:
        dict: Current model configuration
    """
    return _model_config.copy()


def unload_model() -> None:
    """
    Unload the current model to free memory.
    Useful for testing or resource management.
    """
    global _model, _model_config
    
    with _model_lock:
        if _model is not None:
            logger.info("Unloading model from memory")
            del _model
            _model = None
            _model_config = {}
            
            # Try to free GPU memory if using CUDA
            if TORCH_AVAILABLE:
                try:
                    torch.cuda.empty_cache()
                    logger.info("Cleared CUDA cache")
                except:
                    pass


# Pre-load model on module import unless explicitly using OpenAI Whisper
# This ensures the model is ready when the worker starts
if not ENABLE_OPENAI_WHISPER and FASTER_WHISPER_AVAILABLE:
    logger.info("Pre-loading Faster-Whisper ASR model on module import...")
    _initial_model = load_model()
    if _initial_model:
        logger.info("Faster-Whisper ASR model pre-loaded successfully")
    else:
        logger.warning("Failed to pre-load Faster-Whisper ASR model")


# For testing purposes
if __name__ == "__main__":
    # Test the model loader
    logger.info("Testing ASR Model Loader...")
    
    # Test loading
    model = get_model()
    if model:
        logger.info("✓ Model loaded successfully")
        
        # Display configuration
        config = get_model_config()
        logger.info("Current configuration:")
        for key, value in config.items():
            logger.info(f"  {key}: {value}")
        
        # Test with actual transcription (optional)
        try:
            # Create a test audio signal (1 second of sine wave)
            import numpy as np
            sample_rate = 16000
            duration = 1.0
            frequency = 440.0  # A4 note
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.5
            
            logger.info("Testing transcription with sine wave...")
            segments, info = model.transcribe(audio, beam_size=1)
            segments_list = list(segments)
            logger.info(f"✓ Test transcription completed, {len(segments_list)} segments")
            logger.info(f"  Language detected: {info.language}")
            logger.info(f"  Language probability: {info.language_probability:.3f}")
            
        except Exception as e:
            logger.error(f"Test transcription failed: {e}")
        
        # Test unloading
        unload_model()
        logger.info("✓ Model unloaded successfully")
    else:
        logger.error("✗ Failed to load model")
