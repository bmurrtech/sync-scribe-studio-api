# Audio to M4B Conversion API with Audiobook Metadata
Version: 1.0.0
Date: 2025-08-23
Status: Draft
Author: Development Team

## 1. Overview

### Purpose
Add a new endpoint for converting audio files (WAV/MP3) to M4B format with comprehensive audiobook metadata support, optimized for media servers like Plex and Audiobookshelf.

### Goals
- Create dedicated audiobook conversion endpoint
- Support rich metadata injection
- Ensure compatibility with popular audiobook platforms
- Maintain high audio quality
- Preserve chapter information if available

### Non-Goals
- Video processing
- DRM management
- Multi-book compilation
- Real-time audio processing

## 2. Technical Specification

### 2.1 Endpoint Details

**Route:** `/v1/media/convert/audio_to_m4b`
**Method:** POST
**Authentication:** Required (x-api-key header)

### 2.2 Request Format

#### Minimal Request
```json
{
  "media_url": "string (required) - URL of input audio file"
}
```

#### Full Request (All Options)
```json
{
  "media_url": "string (required) - URL of input audio file",
  "metadata": {
    "artist_name": "string (optional) - Author name",
    "album": "string (optional) - Book series name",
    "title": "string (optional) - Book title",
    "comments": "string (optional) - Book synopsis",
    "cover_url": "string (optional) - URL to cover image",
    "publication_year": "string (optional) - Year of publication",
    "genre": "string (optional) - e.g., Fantasy, Science Fiction",
    "publisher": "string (optional) - Publisher name",
    "narrator": "string (optional) - Narrator name",
    "isbn": "string (optional) - Book ISBN"
  },
  "audio_options": {
    "bitrate": "string (optional, default: 64k) - AAC bitrate",
    "channels": "integer (optional, default: 1) - Mono(1) or Stereo(2)",
    "sample_rate": "integer (optional, default: 44100)",
    "chapter_marks": "array (optional) - Array of chapter timestamps"
  },
  "webhook_url": "string (required) - Callback URL",
  "id": "string (required) - Unique request identifier"
}
```

### 2.3 Default Behavior

When only `media_url` is provided:
1. Audio file will be converted to M4B using optimal audiobook defaults:
   - Bitrate: 64k (optimal for spoken word)
   - Channels: 1 (mono)
   - Sample rate: 44100 Hz
   - Format: M4B with AAC codec

2. Metadata handling:
   - Will attempt to extract existing metadata from source file
   - If no metadata is found, will use filename as title
   - No cover art will be embedded
   - No chapter marks will be added

3. Output naming:
   - Will use sanitized version of input filename with .m4b extension

### Storage Behavior
- Use existing storage service configuration from the application (GCP or S3) via the established storage provider.
- Support both GCP and S3 backends and follow the provider selection logic already implemented in the codebase.
- Follow established path patterns for storage URLs:
  {storage_base_url}/audio/m4b/{unique_id}/{filename}.m4b
  e.g. https://storage.googleapis.com/my-bucket/audio/m4b/{job_id}/book_title.m4b
- Use the existing cloud storage upload service (services/cloud_storage.py) and validate that returned URLs match project conventions.
- Maintain existing access control and expiry policies configured for other media endpoints (signed URLs / ACLs managed by storage provider).


### 2.4 Response Format

Minimal synchronous response (when no webhook_url provided) — mirrors other media endpoints:

```json
{
  "code": 200,
  "response": {
    "file_url": "https://storage.example.com/audio/m4b/{unique_id}/{filename}.m4b",
    "duration": "HH:MM:SS",
    "format_info": {
      "bitrate": "64k",
      "channels": 1,
      "sample_rate": 44100
    }
  }
}
```

Full envelope used by queued/async responses (kept consistent with existing endpoints):

```json
{
  "code": 200,
  "id": "client-provided-id",
  "job_id": "generated-uuid",
  "response": {
    "file_url": "string - URL to converted M4B file",
    "duration": "string - Total duration (HH:MM:SS)",
    "chapters": "array - List of detected/added chapters",
    "metadata": {
      "artist_name": "string",
      "album": "string",
      "title": "string",
      "length": "string",
      "comments": "string",
      "cover_url": "string"
    },
    "format_info": {
      "bitrate": "string",
      "channels": "integer",
      "sample_rate": "integer"
    }
  },
  "message": "success",
  "pid": "number",
  "queue_id": "number",
  "run_time": "number",
  "queue_time": "number",
  "total_time": "number",
  "queue_length": "number",
  "build_number": "string"
}
```

Optional Webhook Support
- `webhook_url` is optional.
- If provided, the request follows the async queued flow and a webhook will be delivered to the provided URL with the standard queued response envelope when processing completes.
- If omitted, the endpoint processes synchronously and returns the minimal synchronous response containing `file_url` and `format_info`.


## 3. Implementation Details

### 3.1 Directory Structure

```
/routes/
  /media/
    /convert/
      __init__.py
      audio_to_m4b.py    # Main endpoint implementation
      metadata.py        # Metadata handling utilities
      schemas.py         # Request/response schemas

/tests/
  /routes/
    /media/
      /convert/
        __init__.py
        test_audio_to_m4b.py      # Core conversion tests
        test_metadata.py          # Metadata tests
        test_validation.py        # Input validation tests
        fixtures/                 # Test audio files
          sample.mp3
          sample.wav
          metadata_samples.json
```

### 3.2 FFmpeg Command Structure

```bash
ffmpeg -y -i {input} \
  -c:a aac \
  -b:a {bitrate} \
  -ac {channels} \
  -ar {sample_rate} \
  -metadata artist="{artist_name}" \
  -metadata album="{album}" \
  -metadata title="{title}" \
  -metadata comment="{comments}" \
  -metadata year="{publication_year}" \
  -metadata genre="{genre}" \
  -metadata publisher="{publisher}" \
  -metadata composer="{narrator}" \
  -movflags use_metadata_tags \
  -f mp4 \
  output.m4b
```

### 3.3 Metadata Handling

1. **Required Fields**
   - None (all fields optional)

2. **Recommended Fields**
   - artist_name (Author)
   - title (Book title)
   - album (Series name)
   - comments (Synopsis)
   - cover_url (Cover art)

3. **Platform-Specific Tags**
   - Plex compatibility tags
   - Audiobookshelf-specific metadata
   - iTunes audiobook tags

### 3.4 Audio Processing Best Practices

1. **Default Settings**
   - Bitrate: 64k (optimal for spoken word)
   - Channels: 1 (mono, unless stereo required)
   - Sample rate: 44100 Hz
   - Format: M4B with AAC codec

2. **Quality Preservation**
   - Maintain original quality if higher than defaults
   - No upsampling of lower quality sources
   - Preserve chapter markers if present

### 3.5 Minimal Implementation Priority

1. **Phase 1: Core Conversion**
   - Implement basic URL-to-M4B conversion
   - Focus on stability and performance
   - Use sensible defaults
   - Minimal error handling

2. **Phase 2: Metadata Enhancement**
   - Add full metadata support
   - Implement cover art handling
   - Add chapter mark support
   - Enhanced error handling

3. **Phase 3: Platform Optimization**
   - Add media server specific tags
   - Optimize for different platforms
   - Add advanced options
   - Full validation suite

## 4. Testing Requirements

### 4.1 Unit Tests
- Input validation
- Metadata parsing
- FFmpeg command construction
- Response formatting

### 4.2 Integration Tests
- End-to-end conversion
- Webhook delivery
- Queue management
- Error handling

### 4.3 Metadata Tests
- Optional field validation
- Platform compatibility
- Character encoding
- Cover art handling

### 4.4 Performance Tests
- Large file handling
- Concurrent conversions
- Queue behavior
- Memory usage

### 4.5 Minimal Request Testing
- Test successful conversion with only media_url
- Verify default settings are applied correctly
- Check output file naming
- Verify basic audio quality
- Test with various input formats (MP3, WAV)

## 5. Error Handling

### 5.1 HTTP Status Codes
- 400: Invalid request/metadata
- 401: Unauthorized
- 413: File too large
- 415: Unsupported media type
- 422: Invalid audio file
- 429: Queue full
- 500: Processing error

### 5.2 Error Responses
Detailed error messages with:
- Error code
- Description
- Suggested resolution
- Request ID for tracking

## 6. Security Considerations

1. **Input Validation**
   - Sanitize metadata fields
   - Validate file types
   - Check file size limits

2. **Resource Protection**
   - Rate limiting
   - Queue size limits
   - Maximum file size
   - API key validation

## 7. Documentation

1. **Technical Documentation**
   - API reference
   - Integration guide
   - Error code reference
   - Best practices guide

2. **Example Implementations**
   - cURL examples
   - Python client
   - Node.js client

3. **Troubleshooting Guide**
   - Common issues
   - Solutions
   - Support contacts

## 8. Future Considerations

1. **Potential Enhancements**
   - Batch processing
   - Additional metadata fields
   - More input formats
   - Custom chapter marking
   - Series management

2. **Platform Integration**
   - Additional media server support
   - Direct cloud storage upload
   - Streaming output options

## 9. Success Metrics

1. **Performance Metrics**
   - Conversion time
   - Queue latency
   - Error rates
   - Resource usage

2. **Quality Metrics**
   - Audio quality preservation
   - Metadata accuracy
   - Platform compatibility
   - User satisfaction

## 10. Rollout Plan

1. **Phase 1: Alpha**
   - Core conversion
   - Basic metadata
   - Internal testing

2. **Phase 2: Beta**
   - Full metadata support
   - Platform optimizations
   - External testing

3. **Phase 3: Production**
   - Full release
   - Monitoring
   - Documentation
   - Support
