# YouTube Downloader Microservice - Quick Start

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- curl (for testing)

## 1. Install Dependencies

```bash
cd services/youtube-downloader
npm install
```

## 2. Environment Setup

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults should work for local testing).

## 3. Start the Service

### Development Mode (with auto-reload)
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

The service will start on `http://localhost:3001`

## 4. Test the Endpoints

### Health Check
```bash
curl http://localhost:3001/healthz
```

### Service Info
```bash
curl http://localhost:3001/
```

### Get Video Information
```bash
curl -X POST http://localhost:3001/v1/media/youtube/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Download Audio (MP3)
```bash
curl -X POST http://localhost:3001/v1/media/youtube/mp3 \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  --output test_audio.mp3
```

### Download Video (MP4)
```bash
curl -X POST http://localhost:3001/v1/media/youtube/mp4 \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  --output test_video.mp4
```

## 5. Run Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode (for development)
npm test -- --watch
```

## 6. Docker Testing (Optional)

### Build and run with Docker
```bash
docker build -t youtube-downloader .
docker run -p 3001:3001 youtube-downloader
```

### Or use Docker Compose
```bash
docker-compose up
```

## Expected Responses

### Health Check Response
```json
{
  "uptime": 123.456,
  "message": "OK",
  "timestamp": "2025-01-27T12:00:00.000Z",
  "service": "youtube-downloader",
  "version": "1.0.0",
  "status": "healthy"
}
```

### Video Info Response
```json
{
  "success": true,
  "data": {
    "videoId": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
    "description": "...",
    "lengthSeconds": 212,
    "viewCount": 1234567890,
    "author": {
      "name": "Rick Astley",
      "channelUrl": "...",
      "subscriberCount": "..."
    },
    "publishDate": "2009-10-25",
    "thumbnails": [...],
    "formats": {
      "audioFormats": [...],
      "videoFormats": [...]
    }
  },
  "timestamp": "2025-01-27T12:00:00.000Z"
}
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Change `PORT` in `.env` to a different value
2. **YouTube blocking**: The service includes proper User-Agent headers to minimize blocking
3. **Network issues**: Check your internet connection and firewall settings
4. **Dependencies**: Make sure all npm packages installed correctly

### Debug Mode
```bash
DEBUG_TESTS=true npm test
```

### Logs
Check the following log files:
- `error.log` - Error logs only
- `combined.log` - All logs

## Integration with Main API

To integrate with the main Python API, the main API should make HTTP requests to this microservice:

```python
import requests

# Get video info
response = requests.post(
    'http://localhost:3001/v1/media/youtube/info',
    json={'url': 'https://www.youtube.com/watch?v=VIDEO_ID'}
)
video_info = response.json()

# Download audio for transcription
response = requests.post(
    'http://localhost:3001/v1/media/youtube/mp3',
    json={'url': 'https://www.youtube.com/watch?v=VIDEO_ID'}
)
# Stream the audio data directly to transcription service
```

## Next Steps

1. Test with various YouTube URLs
2. Monitor logs for any issues
3. Adjust rate limiting if needed
4. Configure for your production environment
5. Set up monitoring and alerting
