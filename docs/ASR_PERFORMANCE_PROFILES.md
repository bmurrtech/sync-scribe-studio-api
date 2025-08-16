# ASR Performance Profiles

The Sync Scribe Studio API supports performance-optimized configurations through the `ASR_PROFILE` environment variable or individual ASR settings.

## 🎯 Profile-Based Configuration System

The Sync Scribe Studio API uses a comprehensive profile-based system with three optimized presets that automatically configure all ASR parameters for optimal performance.

### **System Default: Balanced Profile (whisper-small)**
- **Best for**: General-purpose transcription with good speed/accuracy balance
- **Model**: `openai/whisper-small` with auto-optimized compute type
- **Performance**: Solid accuracy with reasonable processing speed
- **Memory**: Works on both CPU (1-2GB RAM) and GPU (4-6GB VRAM)
- **Profile**: `ASR_PROFILE=balanced` (default if not specified)

---

## Available Profiles

### Speed Profile (`ASR_PROFILE=speed`)
**Optimized for real-time processing and maximum throughput**

- **Model**: whisper-small (39M parameters)
- **Compute Type**: CPU: `int8`, GPU: `float16`
- **Beam Size**: 1 (greedy decoding)
- **Best Of**: 1 (single generation)
- **Temperature**: 0.0 (deterministic)
- **Temperature Increment**: 0.0 (no fallback)
- **VAD Silence**: 300ms (aggressive silence detection)
- **Batch Size**: CPU: 4, GPU: 16
- **Best For**: Real-time transcription, high-volume processing, live streaming, CPU deployments

**Expected Performance**: 2-3x faster than balanced, suitable for 5+ minute audio files in under 30 seconds on GPU.

### Balanced Profile (`ASR_PROFILE=balanced`) [SYSTEM DEFAULT]
**Good balance of speed and accuracy for general use**

- **Model**: whisper-small (39M parameters)
- **Compute Type**: Auto-optimized (CPU: `int8`, GPU: `float16`)
- **Beam Size**: 2 (small beam search)
- **Best Of**: 2 (dual generation)
- **Temperature**: 0.0 (deterministic start)
- **Temperature Increment**: 0.1 (minimal fallback)
- **VAD Silence**: 400ms (balanced silence detection)
- **Speech Pad**: Optimized for segment boundaries
- **Context Awareness**: `condition_on_previous_text=True`
- **Quality Control**: Configured compression ratio and probability thresholds
- **Best For**: General transcription, podcasts, interviews, business applications
- **Requirements**: Works on both CPU and GPU, 4-6GB VRAM recommended for GPU

**Expected Performance**: Good speed with improved accuracy over speed profile, suitable for most use cases.

### Accuracy Profile (`ASR_PROFILE=accuracy`)
**Maximum accuracy for critical transcription needs**

- **Model**: whisper-large-v3 (1550M parameters)
- **Compute Type**: `float16`
- **Beam Size**: 3 (wider beam search)
- **Best Of**: 5 (multiple generations)
- **Temperature**: 0.0 (deterministic start)
- **Temperature Increment**: 0.2 (higher fallback for quality)
- **VAD Silence**: 500ms (conservative silence detection)
- **Batch Size**: CPU: 2, GPU: 8 (conservative for large model)
- **Best For**: Professional transcription, medical/legal content, broadcast quality, multilingual audio

**Requirements**: 12-16GB VRAM for comfortable GPU processing.

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

## 🎯 Advanced Implementation Features

### Deterministic Decoding Implementation
Based on research insights for optimal speed vs quality balance:

- **Speed Profile**: `beam_size=1` + `best_of=1` for fully greedy decoding
- **Balanced/Accuracy**: Higher `best_of` values for quality with deterministic results
- **Temperature Control**: `temperature_increment_on_fallback=0.0` prevents temperature escalation in speed mode
- **Consistent Results**: `best_of` parameter generates multiple candidates and selects optimal transcript

### VAD & Conversational Audio Optimizations
- **Profile-tuned silence detection**: 300ms (speed) → 400ms (balanced) → 500ms (accuracy)
- **Reduced hallucinations**: Optimized `min_silence_duration_ms` prevents silence-based artifacts
- **Improved throughput**: Especially effective on conversational audio with natural pauses
- **Speech padding**: Optimized `speech_pad_ms` for better segment boundaries
- **Quality vs Speed**: Lower thresholds = faster processing but may miss short pauses

### Advanced Parameter Tuning
- **Quality Control Thresholds**:
  - `compression_ratio_threshold`: Detects repetitive or low-quality segments
  - `logprob_threshold`: Filters low-confidence transcriptions
  - `no_speech_threshold`: Identifies silent segments accurately
- **Context Awareness**: `condition_on_previous_text=True` for coherent long-form transcription
- **Device Optimization**: Automatic batch size adjustment per device type and profile
- **Memory Management**: Profile-specific VRAM and RAM optimization

### Profile-Specific Optimizations
| Profile | Beam Size | Best Of | Temp Increment | VAD Silence | Focus |
|---------|-----------|---------|----------------|-------------|-------|
| **Speed** | 1 (greedy) | 1 | 0.0 (none) | 300ms | Maximum throughput |
| **Balanced** | 2 | 2 | 0.1 (minimal) | 400ms | Speed/accuracy balance |
| **Accuracy** | 3 | 5 | 0.2 (quality) | 500ms | Maximum quality |

### Beam Search vs Speed
- **beam_size=1** (greedy): Fastest, ~80-90% accuracy of beam search
- **beam_size=2-3**: Good balance, minimal speed impact  
- **beam_size=5+**: Diminishing returns, significantly slower

### Model Size Considerations & Diminishing Returns
- **tiny**: Ultra-fast, poor accuracy - only for ultra-low-latency scenarios
- **base**: Fast, acceptable for simple audio - CPU fallback when small is too slow  
- **small**: **✅ Recommended CPU default** - best speed/accuracy balance
- **medium**: ⚠️ **Not recommended** - only ~10-15% accuracy improvement over small but 2x slower
- **large-v3-turbo**: **✅ Recommended GPU default** - similar accuracy to large-v3 but much faster
- **large-v3**: **Maximum accuracy** - significant compute cost, use only when quality is business-critical

### ⚖️ **Diminishing Returns Analysis**

**small → medium**: Noticeable quality improvement but much slower and higher VRAM usage. Choose medium only if your specific domain/language absolutely requires it.

**medium → large-v3**: Biggest absolute accuracy gains, but with the steepest cost in latency and VRAM. Choose this for "best possible transcripts" workloads, not real-time at scale.

**large-v3 vs large-v3-turbo**: Turbo offers similar accuracy at much higher speed and lower memory usage. Community results vary—validate on your audio before standardizing.

> **Recommendation**: Skip medium entirely. Use small for CPU speed or large-v3-turbo for GPU accuracy.

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
