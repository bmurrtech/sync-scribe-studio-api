# ASR Model Loader

Singleton model loader utility for Automatic Speech Recognition (ASR) using `faster-whisper`. This module provides efficient model loading with automatic CUDA detection, compute type optimization, and warm-up capabilities.

## Features

- **Singleton Pattern**: Model is loaded once per Gunicorn worker process
- **CUDA Auto-Detection**: Automatically detects and uses GPU if available
- **Optimized Compute Types**: 
  - `float16` for GPU (optimal performance/memory trade-off)
  - `int8` for CPU (best CPU performance)
- **Model Warm-up**: Performs 1-second dummy transcription to initialize model
- **Thread-Safe**: Concurrent access is handled with proper locking
- **Detailed Logging**: Comprehensive logging of device, compute type, load times, and warm-up times
- **Configuration via Environment Variables**: Flexible configuration without code changes

## Installation

Ensure `faster-whisper` is installed:

```bash
pip install faster-whisper
```

For GPU support, also install PyTorch with CUDA:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Configuration

Configure the model loader using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_FASTER_WHISPER` | `false` | Enable/disable faster-whisper ASR |
| `ASR_MODEL_ID` | `openai/whisper-base` | Model to load (e.g., `openai/whisper-large-v3`) |
| `ASR_DEVICE` | `cpu` | Device to use: `cpu`, `cuda`, or `auto` |
| `ASR_COMPUTE_TYPE` | `int8` | Compute type: `int8`, `float16`, `float32`, or `auto` |
| `ASR_BEAM_SIZE` | `5` | Beam search width for transcription |
| `ASR_BATCH_SIZE` | `16` | Batch size for processing |
| `ASR_CACHE_DIR` | `/tmp/asr_cache` | Directory for model cache |

## Usage

### Basic Usage

```python
from services.asr import get_model

# Get the singleton model instance
model = get_model()

if model:
    # Transcribe audio
    segments, info = model.transcribe("audio.wav")
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

### Check Configuration

```python
from services.asr import get_model_config

config = get_model_config()
print(f"Device: {config['device']}")
print(f"Compute Type: {config['compute_type']}")
print(f"Model: {config['model_id']}")
```

### CUDA Detection

```python
from services.asr import detect_cuda_availability

cuda_available, cuda_version, device_count = detect_cuda_availability()
if cuda_available:
    print(f"CUDA {cuda_version} available with {device_count} GPU(s)")
```

### Manual Model Management

```python
from services.asr import load_model, unload_model

# Force reload model
model = load_model(force_reload=True)

# Unload model to free memory
unload_model()
```

## Model Loading Process

1. **Configuration Reading**: Reads environment variables and config file
2. **CUDA Detection**: Checks for GPU availability
3. **Device Selection**: Chooses optimal device (GPU if available, else CPU)
4. **Compute Type Selection**: Selects optimal compute type for device
5. **Model Loading**: Downloads (if needed) and loads the model
6. **Warm-up**: Performs 1-second dummy transcription to initialize
7. **Caching**: Model instance is cached for subsequent calls

## Logging Output Example

```
============================================================
Initializing ASR Model Loader
============================================================
Model cache directory: /tmp/asr_cache
Model Configuration:
  model_id: openai/whisper-base
  device: cuda
  compute_type: float16
  beam_size: 5
  cache_dir: /tmp/asr_cache
  worker_pid: 12345
------------------------------------------------------------
Loading model: openai/whisper-base
Model loaded successfully in 2.345 seconds
------------------------------------------------------------
Starting model warm-up...
Model warm-up completed in 0.567 seconds
============================================================
Model Initialization Summary:
  Model: openai/whisper-base
  Device: cuda
  Compute Type: float16
  Load Time: 2.345 seconds
  Warm-up Time: 0.567 seconds
  Total Time: 2.912 seconds
  Worker PID: 12345
============================================================
```

## Testing

Run the test suite to verify functionality:

```bash
python services/asr/test_model_loader.py
```

The test suite includes:
- CUDA detection test
- Device and compute type selection test
- Model loading test
- Singleton pattern verification
- Thread safety test
- Model unloading test

## Performance Considerations

### GPU vs CPU

- **GPU (CUDA)**: 
  - 5-10x faster transcription
  - Uses `float16` by default
  - Requires NVIDIA GPU with CUDA support
  
- **CPU**: 
  - Uses `int8` quantization for better performance
  - Slower but works on any machine
  - Good for low-volume transcription

### Model Sizes

| Model | Parameters | Disk Size | Memory Usage |
|-------|------------|-----------|--------------|
| tiny | 39M | ~75 MB | ~390 MB |
| base | 74M | ~145 MB | ~740 MB |
| small | 244M | ~480 MB | ~2.4 GB |
| medium | 769M | ~1.5 GB | ~7.7 GB |
| large-v3 | 1550M | ~3.1 GB | ~15.5 GB |

### Warm-up Impact

The warm-up process adds ~0.5-1.5 seconds to initial load time but ensures:
- Model weights are loaded into memory
- CUDA kernels are compiled (for GPU)
- First transcription doesn't have initialization overhead

## Integration with Gunicorn

The model loader is designed to work efficiently with Gunicorn workers:

```python
# In your Flask/FastAPI app initialization
from services.asr import get_model

def on_starting(server):
    """Pre-load model when Gunicorn starts."""
    model = get_model()
    if model:
        print(f"ASR model pre-loaded for worker {os.getpid()}")

# Each worker will have its own model instance
# The singleton ensures only one model per worker
```

## Troubleshooting

### Model Not Loading

1. Check if `ENABLE_FASTER_WHISPER=true` is set
2. Verify `faster-whisper` is installed
3. Check available disk space for model download
4. Review logs for specific error messages

### CUDA Not Detected

1. Ensure PyTorch is installed with CUDA support
2. Check NVIDIA drivers are installed
3. Verify CUDA toolkit compatibility
4. Set `ASR_DEVICE=cpu` to force CPU usage

### High Memory Usage

1. Use smaller model (e.g., `tiny` or `base`)
2. Reduce `ASR_BATCH_SIZE`
3. Use `int8` compute type for lower memory usage
4. Call `unload_model()` when not in use

## License

Copyright (c) 2025 - Licensed under GNU GPL v2
