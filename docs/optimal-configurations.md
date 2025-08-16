# Optimal ASR Configuration Guide

## Performance Profile Recommendations

This guide provides data-driven recommendations for configuring Sync Scribe Studio based on your specific use case and requirements.

### 🏆 Recommended Configurations

#### For Long-Form Content (30+ minutes)

| Use Case | Profile | Model | Hardware | Speed | Accuracy | Best For |
|----------|---------|-------|----------|-------|----------|----------|
| **Professional/Formal** | `accuracy-turbo` | `large-v3-turbo` | GPU | ~69s for 42min | ⭐⭐⭐⭐⭐ | Sermons, lectures, legal |
| **General Purpose** | `speed` | `small` | GPU | ~60s for 42min | ⭐⭐⭐⭐ | Podcasts, interviews |
| **Budget/CPU Only** | Not Recommended | - | - | - | - | Use cloud GPU instead |

#### For Short-Form Content (< 10 minutes)

| Use Case | Profile | Model | Hardware | Speed | Accuracy | Best For |
|----------|---------|-------|----------|-------|----------|----------|
| **High Accuracy** | `accuracy-turbo` | `large-v3-turbo` | GPU | ~8s for 4min | ⭐⭐⭐⭐⭐ | Important recordings |
| **Fast Turnaround** | `speed` | `small` | GPU | ~6s for 4min | ⭐⭐⭐⭐ | Social media, quick notes |
| **CPU Acceptable** | `speed` | `small` | CPU | ~27s for 4min | ⭐⭐⭐ | Local processing |

### 🎯 Use Case Specific Recommendations

#### Religious/Educational Content
- **Primary**: `accuracy-turbo` with `large-v3-turbo` on GPU
- **Why**: Formal language, proper nouns, theological terms require highest accuracy
- **Alternative**: `speed` profile for draft transcripts that will be manually reviewed

#### Business/Legal
- **Primary**: `accuracy-turbo` with `large-v3-turbo` on GPU
- **Why**: Accuracy critical, formal language preservation essential
- **Note**: Consider human review for legal documents regardless of AI accuracy

#### Media/Entertainment
- **Primary**: `speed` with `small` on GPU
- **Why**: Speed prioritized, conversational tone acceptable
- **Alternative**: `accuracy-turbo` for final/published transcripts

#### Personal/Casual
- **Primary**: `speed` with `small` on CPU or GPU
- **Why**: Cost-effective, speed over perfection
- **Note**: CPU acceptable for short clips only

### ⚠️ Configurations to Avoid

#### Not Recommended
| Profile | Model | Hardware | Issue | Alternative |
|---------|-------|----------|-------|-------------|
| `accuracy` | `large-v3` | GPU | Repetition glitches | Use `accuracy-turbo` instead |
| Any | Any | CPU | OOM on long audio | Use cloud GPU |
| OpenAI Whisper | `base` | Any | Poor accuracy vs faster-whisper | Upgrade to `small` minimum |

### 📊 Performance Comparison Matrix

#### Processing Speed (42-minute audio)
```
🥇 speed (GPU):        ~60s  (100% baseline)
🥈 accuracy-turbo:     ~69s  (+15% slower, much higher accuracy)
🥉 OpenAI Whisper base: ~85s  (+42% slower, much lower accuracy)
❌ accuracy (GPU):     ~184s (+207% slower, unreliable)
```

#### Accuracy Ranking (Formal content)
```
🥇 accuracy-turbo:  ⭐⭐⭐⭐⭐  (Best formal language)
🥈 speed:           ⭐⭐⭐⭐     (Good, more casual)
🥉 OpenAI Whisper base: ⭐⭐         (Significant errors)
❌ accuracy:        ⭐           (Repetition issues)
```

### 🛠️ Configuration Examples

#### Environment Variables for Recommended Setups

**Production (Accuracy Focus)**:
```env
ASR_PROFILE=accuracy-turbo
ASR_MODEL_ID=large-v3-turbo
ASR_DEVICE=auto
ASR_COMPUTE_TYPE=float16
ENABLE_FASTER_WHISPER=true
```

**Development/Default (Speed Focus)**:
```env
# Speed profile is now the default - no configuration needed!
# ASR_PROFILE=speed  # (default, no need to set)
ASR_DEVICE=auto
ASR_COMPUTE_TYPE=auto
ENABLE_FASTER_WHISPER=true
```

**CPU Fallback (Short clips only)**:
```env
ASR_PROFILE=speed
ASR_MODEL_ID=small
ASR_DEVICE=cpu
ASR_COMPUTE_TYPE=int8
ENABLE_FASTER_WHISPER=true
```

### 💰 Cost Considerations

#### Cloud GPU Costs (Approximate)
- **L4 GPU**: ~$0.60/hour
- **42-minute transcription cost**:
  - `accuracy-turbo`: ~$0.012 per job
  - `speed`: ~$0.010 per job
- **Break-even**: ~50 jobs/hour to justify dedicated instance

#### CPU vs GPU Economics
- **CPU**: "Free" but fails on long audio
- **GPU**: Small cost but 10-100x faster and higher accuracy
- **Recommendation**: Use cloud GPU for all production workloads

### 🔬 Technical Details

#### Model Sizes & Memory Requirements
| Model | Size | VRAM (GPU) | RAM (CPU) | Quality |
|-------|------|------------|-----------|---------|
| `small` | ~244MB | ~1GB | ~2GB | Good |
| `large-v3-turbo` | ~1.5GB | ~3GB | ~6GB | Excellent |
| `large-v3` | ~1.5GB | ~3GB | ~6GB | Excellent (but buggy) |

#### Processing Characteristics
- **VAD Optimization**: Automatically removes silence, improving speed
- **Batch Processing**: Single long file more efficient than many short files
- **Model Caching**: First run slower due to download, subsequent runs faster
