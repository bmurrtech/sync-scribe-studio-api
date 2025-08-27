# Media to M4A Conversion

The `/v1/media/convert/m4a` endpoint converts common audio files (MP3, WAV, AAC, etc.) and audio tracks from video files into M4A (AAC) format optimized for audiobooks.

## Endpoint Details

**URL Path:** `/v1/media/convert/m4a`

## 1. Overview

The `/v1/media/convert/m4a` endpoint is part of the API's media transformation functionality. It allows users to convert various media files (audio or video) to M4A format. This endpoint is registered in the `app.py` file under the `v1_m4a` blueprint.

## 2. Endpoint

```
POST /v1/media/convert/m4a
```

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

- `media_url` (required, string): The URL of the media file to be converted (supports mp3, wav, m4a, aac, and common video formats containing audio).
- `metadata` (optional, object): Metadata fields to embed (artist_name, album, title, comments, cover_url, publication_year, genre, publisher, narrator, isbn).
- `audio_options` (optional, object): Options such as `bitrate` (default `64k`), `channels` (default `1`), `sample_rate` (default `44100`).
- `webhook_url` (optional, string): The URL to receive a webhook notification upon completion (if omitted, the endpoint processes synchronously and returns the result).
- `id` (optional, string): A unique identifier for the request.

The `validate_payload` directive in the routes file enforces the following JSON schema for the request body:

```json
{
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "metadata": {"type": "object"},
        "audio_options": {"type": "object"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
}
```

### Example Request

```json
{
    "media_url": "https://example.com/book.wav",
    "metadata": {
      "artist_name": "Author Name",
      "title": "Book Title",
      "narrator": "Narrator Name"
    },
    "audio_options": {
      "bitrate": "64k",
      "channels": 1,
      "sample_rate": 44100
    },
    "id": "unique-request-id"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"media_url":"https://example.com/book.wav","id":"req-1"}' \
     https://your-api-endpoint.com/v1/media/convert/m4a
```

## 4. Response

### Success Response (synchronous; no webhook_url provided)

```json
{
  "code": 200,
  "response": {
    "file_url": "https://storage.example.com/audio/m4a/{unique_id}/{filename}.m4a",
    "duration": "HH:MM:SS", 
    "format_info": {
      "bitrate": "64k",
      "channels": 1,
      "sample_rate": 44100
    }
  }
}
```

### Async/Queued Response (webhook_url provided)

The queued response follows the standard envelope used across the API (see `app.py`) and returns a 202 with job_id. A webhook will be POSTed on completion with the full response envelope.

### Error Responses

- 400 Bad Request: Invalid JSON schema or missing required fields.
- 401 Unauthorized: Missing or invalid `x-api-key`.
- 413 Payload Too Large: Input media size exceeds configured limits.
- 415 Unsupported Media Type: Input format is unsupported.
- 422 Invalid audio file: FFmpeg could not process the file.
- 429 Too Many Requests: Queue limit reached.
- 500 Internal Server Error: Unexpected server error during conversion.

## 5. Notes & Best Practices

- Supported input formats: MP3, WAV, M4A/AAC, OGG, FLAC and most video formats with an audio track.
- For very large files or long durations, provide `webhook_url` to use asynchronous processing.
- Configure `AUDIO_CONVERT_TIMEOUT_SEC` environment variable in production to protect long-running conversions.
- Use `id` to correlate requests with logs and job status files.

## 6. Troubleshooting

- If conversion fails, check logs for FFmpeg errors. The service will attempt to include FFmpeg stderr in error messages.
- Verify that the storage provider environment variables (GCP or S3) are configured for uploads.
- If you see repeated timeouts, raise `AUDIO_CONVERT_TIMEOUT_SEC` or prefer webhook async flow for very large inputs.