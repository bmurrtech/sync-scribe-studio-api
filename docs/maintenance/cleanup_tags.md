# Docker Hub Tag Cleanup Instructions

## Current Status
✅ **Successfully deployed and tested:** v2.0.3-gpu image is working perfectly with Faster-Whisper as default

## Tags to Keep (Per Your Policy)
- `latest` → Stable CPU build (amd64, maximum compatibility)
- `gpu` → Rolling GPU build (for GPU-enabled deployments)  
- `v2.0.3-gpu` → Most recent experimental (currently running)

## Tags to Remove (Deprecated/Superseded)
- `cpu` → Redundant with `latest`
- `macos` → Architecture-specific, not needed
- `v2.0.0` → Old version
- `v2.0.1` → Old version
- `v2.0.1-cpu` → Old version
- `v2.0.2-cpu` → Superseded by `latest`
- `v2.0.2-gpu` → Superseded by `gpu`
- `v2.0.3-cpu` → Superseded by `latest`

## Manual Cleanup via Docker Hub Web Interface

1. Go to: https://hub.docker.com/r/bmurrtech/sync-scribe-studio-api/tags
2. For each deprecated tag, click the "..." menu → "Delete tag"
3. Confirm deletion

## Result After Cleanup
```
bmurrtech/sync-scribe-studio-api:latest     → CPU optimized, stable
bmurrtech/sync-scribe-studio-api:gpu        → GPU optimized, rolling  
bmurrtech/sync-scribe-studio-api:v2.0.3-gpu → Current experimental
```

This follows your minimal tag retention policy:
- ✅ Keep `latest` (broadest compatibility) 
- ✅ Keep `gpu` (rolling by architecture)
- ✅ Keep most recent experimental for testing
- ✅ Delete all superseded versions
