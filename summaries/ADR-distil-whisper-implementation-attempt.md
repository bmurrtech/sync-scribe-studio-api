# Architecture Decision Record: Distil-Whisper Implementation Attempt

**Status**: FAILED - Reverted to Stable State  
**Date**: 2025-08-20  
**Deciders**: Development Team  

## Context

The Sync Scribe Studio API was experiencing hallucinations and repetitive phrase issues with long-form audio transcription, particularly when using the `accuracy-turbo` profile with `openai/whisper-large-v3-turbo` and `openai/whisper-large-v3` models. To address this, we attempted to implement:

1. **Distil-Whisper Integration**: Using `distil-whisper/distil-large-v2` model with audio chunking
2. **Anti-Repetition Parameters**: Custom parameters to reduce hallucinations
3. **Audio Chunking System**: Breaking long audio into manageable segments

## Decision

We attempted to implement a new ASR profile called `crisper-whisper` that would:
- Use the Distil-Whisper model for faster, more accurate transcription
- Implement intelligent audio chunking with Voice Activity Detection (VAD)
- Provide seamless timestamp correction across chunks
- Reduce hallucinations through chunking and parameter tuning

## Implementation Attempts

### Phase 1: Anti-Repetition Parameters (FAILED)
**Commit Range**: After `9073982` (stable) → Various attempts

**What was tried**:
- Added `entropy_threshold`, `max_context`, `condition_on_previous_text` parameters
- Modified `PROFILE_CONFIGS` in `config.py`
- Updated transcription service to pass these parameters

**Issues encountered**:
```
WhisperModel.transcribe() got an unexpected keyword argument 'entropy_threshold'
```

**Root cause**: Faster-Whisper library doesn't support these parameters that exist in OpenAI Whisper.

### Phase 2: Configuration Refactoring (FAILED)
**What was tried**:
- Removed unsupported parameters from transcription calls
- Cleaned up configuration to only use supported Faster-Whisper parameters
- Fixed parameter passing in `media_transcribe.py`

**Issues encountered**:
```
NameError: name 'EXISTING_MODELS' is not defined
```

**Root cause**: Incomplete refactoring left references to removed `EXISTING_MODELS` dictionary.

### Phase 3: Distil-Whisper Integration (FAILED)
**What was tried**:
- Implemented `AudioChunker` class for intelligent audio segmentation
- Created `crisper-whisper` profile with chunking configuration
- Added VAD parameters for smart chunk boundary detection
- Integrated chunking logic into main transcription service

**Code components added**:
- `services/asr/audio_chunker.py` - Audio chunking logic
- Enhanced `PROFILE_CONFIGS` with chunking parameters
- Modified `media_transcribe.py` for chunking support

### Phase 4: Multiple Configuration Fixes (FAILED)
**Issues encountered**:
1. `NameError: name 'EXISTING_MODELS' is not defined` (Line 123 in config.py)
2. Missing `torch` import causing `NameError` on device detection
3. Worker boot failures with gunicorn

**Fixes attempted**:
- Fixed `EXISTING_MODELS` reference → `PROFILE_CONFIGS['balanced']`
- Added safe torch import with fallback
- Enhanced device detection logic

### Current Failure State
**Latest error** (Docker image `v2.1.5`):
```
gunicorn.errors.HaltServer: <HaltServer 'Worker failed to boot.' 3>
```

**Symptoms**:
- Workers failing to start
- Complex stack trace in gunicorn arbiter
- Application completely non-functional

## Key Technical Issues Identified

### 1. **Library Compatibility Issues**
- Faster-Whisper vs OpenAI Whisper parameter differences
- Unsupported parameters causing runtime failures
- Need for comprehensive parameter validation

### 2. **Configuration Management Problems**
- Complex nested configuration structure
- Inconsistent fallback handling
- Missing import dependencies
- Profile-specific parameter handling complexity

### 3. **Import and Dependency Issues**
- Torch import failures in config.py
- Circular import potential with complex configuration
- Runtime dependency resolution problems

### 4. **Docker Build and Deployment Issues**
- Multiple rebuilds with same tag causing confusion
- Configuration errors only appearing at runtime
- Cache invalidation problems

## Consequences of Implementation

### Negative Impacts
- **Service Downtime**: Multiple failed deployments
- **Development Velocity**: Significant time spent debugging configuration issues
- **Code Complexity**: Added complexity without functional benefits
- **Stability**: Moved from stable to completely broken state

### Lessons Learned
1. **Parameter Validation**: Need comprehensive validation of ML library parameters
2. **Gradual Implementation**: Should implement in smaller, testable increments
3. **Configuration Testing**: Need local testing before Docker builds
4. **Documentation**: Better documentation of parameter compatibility between libraries
5. **Rollback Strategy**: Need clearer rollback procedures for failed implementations

## Recovery Plan

### Immediate Actions (COMPLETED)
1. **Revert to Stable State**: 
   ```bash
   git reset --hard 9073982
   ```
   This returns to commit: "docs/update performance benchmarks and recommendations"

2. **Cleanup Failed Implementation**:
   - Remove `services/asr/audio_chunker.py`
   - Revert `config.py` to stable state
   - Remove `crisper-whisper` profile
   - Clean up transcription service changes

### Future Implementation Strategy

If attempting this again, recommend:

1. **Phase 1**: Implement chunking logic separately and test thoroughly
2. **Phase 2**: Add Distil-Whisper model support without changing existing profiles  
3. **Phase 3**: Create new experimental profile with thorough local testing
4. **Phase 4**: Gradual rollout with proper monitoring

### Alternative Approaches to Consider

1. **Pre-processing Approach**: Use VAD to clean audio before transcription
2. **Post-processing Filtering**: Remove repetitive phrases after transcription
3. **Different Model Selection**: Try other Whisper variants that are more stable
4. **Parameter Tuning**: Focus on existing supported parameters only

## Developer Handoff Notes

For any developer taking over this work:

### Code State After Reversion
- Repository reset to stable commit `9073982`
- All experimental changes removed
- Docker images may need rebuilding from stable codebase
- Railway deployment should work with stable configuration

### Key Files to Monitor
- `config.py` - Contains all ASR profile configurations
- `services/v1/media/media_transcribe.py` - Main transcription logic
- `services/asr/model_loader.py` - Model initialization and management

### Testing Recommendations
1. Always test configuration changes locally first
2. Validate all parameters against library documentation
3. Test with small audio files before long-form content
4. Implement comprehensive error handling for unsupported parameters

### Resources
- [Faster-Whisper Documentation](https://github.com/guillaumekln/faster-whisper)
- [Distil-Whisper Documentation](https://github.com/huggingface/distil-whisper)
- Previous stable configuration examples in git history

---

**Final Status**: Implementation FAILED and REVERTED  
**Stable Commit**: `9073982` - "docs/update performance benchmarks and recommendations"  
**Docker Image**: Rebuild required from stable state  
**Service Status**: Should be functional after reversion and redeployment  
