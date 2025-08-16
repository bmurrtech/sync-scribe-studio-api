# ASR Performance Profiles

The Sync Scribe Studio API supports performance-optimized configurations through the `ASR_PROFILE` environment variable.

## Available Profiles

### Speed Profile (`ASR_PROFILE=speed`)
**Optimized for real-time processing and maximum throughput**

- **Model**: whisper-small (39 parameters)
- **Beam Size**: 1 (greedy decoding)
- **Best Of**: 1 (single generation)
- **Temperature**: 0.0 (deterministic)
- **Temperature Increment**: 0.0 (no fallback)
- **VAD Silence**: 300ms (aggressive silence detection)
- **Batch Size**: CPU: 4, GPU: 16
- **Best For**: Real-time transcription, high-volume processing, live streaming

**Expected Performance**: 2-3x faster than default, suitable for 5+ minute audio files in under 30 seconds on GPU.

### Balanced Profile (`ASR_PROFILE=balanced`) [DEFAULT]
**Good balance of speed and accuracy for general use**

- **Model**: whisper-small (39 parameters)  
- **Beam Size**: 2 (small beam search)
- **Best Of**: 2 (dual generation)
- **Temperature**: 0.0 (deterministic start)
- **Temperature Increment**: 0.1 (minimal fallback)
- **VAD Silence**: 400ms (balanced silence detection)
- **Batch Size**: CPU: 4, GPU: 12
- **Best For**: General transcription tasks, podcasts, interviews

**Expected Performance**: Good speed with improved accuracy over speed profile.

### Accuracy Profile (`ASR_PROFILE=accuracy`)
**Maximum accuracy for high-quality transcription needs**

- **Model**: whisper-large-v3 (1550 parameters)
- **Beam Size**: 3 (wider beam search)
- **Best Of**: 5 (multiple generations)
- **Temperature**: 0.0 (deterministic start)
- **Temperature Increment**: 0.2 (higher fallback for quality)
- **VAD Silence**: 500ms (conservative silence detection)
- **Batch Size**: CPU: 2, GPU: 8 (conservative for large model)
- **Best For**: Professional transcription, medical/legal content, multilingual audio

**Requirements**: Requires 10-12GB VRAM for comfortable GPU processing.

## Environment Variables

### Primary Configuration
```bash
ASR_PROFILE=balanced  # Options: speed, balanced, accuracy
```

### Override Individual Settings (Optional)
```bash
ASR_MODEL_ID=openai/whisper-medium         # Override model
ASR_BEAM_SIZE=3                            # Override beam size
ASR_BEST_OF=5                              # Override best_of
ASR_TEMPERATURE=0.1                        # Override temperature
ASR_TEMPERATURE_INCREMENT_ON_FALLBACK=0.2  # Override fallback temp
ASR_VAD_MIN_SILENCE_MS=300                 # Override VAD timing
ASR_BATCH_SIZE=8                           # Override batch size
```

## Performance Tuning Notes

### Deterministic Decoding
All profiles use `temperature=0.0` with controlled fallback to prevent quality degradation while maintaining speed. The `best_of` parameter ensures consistent results by generating multiple candidates and selecting the best.

### VAD (Voice Activity Detection)
- **Lower silence thresholds** (300ms) = faster processing, may miss short pauses
- **Higher silence thresholds** (500ms) = better quality, preserves natural speech patterns
- Reduces hallucinations from silence and improves overall transcript quality

### Beam Search vs Speed
- **beam_size=1** (greedy): Fastest, ~80-90% accuracy of beam search
- **beam_size=2-3**: Good balance, minimal speed impact  
- **beam_size=5+**: Diminishing returns, significantly slower

### Model Size Considerations
- **tiny**: Ultra-fast, poor accuracy
- **base**: Fast, acceptable for simple audio
- **small**: Best speed/accuracy balance for most use cases
- **medium**: Better accuracy, 2x slower than small
- **large/large-v3**: Best accuracy, requires significant compute

## Usage Examples

### High-Speed Processing
```bash
export ASR_PROFILE=speed
# For livestream transcription, real-time processing
```

### Professional Quality
```bash  
export ASR_PROFILE=accuracy
# For legal depositions, medical dictation, broadcast transcription
```

### Custom Configuration
```bash
export ASR_PROFILE=balanced
export ASR_BEAM_SIZE=1          # Speed up the balanced profile  
export ASR_VAD_MIN_SILENCE_MS=250  # More aggressive VAD
```

## Monitoring Performance

The system logs profile configuration at startup:
```
ASR Performance Profile: BALANCED
Profile Description: Good balance of speed and accuracy
Faster-Whisper params: beam_size=2, best_of=2, temperature=0.0, vad_filter=True
```

Monitor transcription time vs accuracy to find the optimal profile for your use case.
