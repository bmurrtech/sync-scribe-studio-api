# YouTube Downloader Microservice

A secure and scalable Node.js/Express microservice for downloading YouTube videos and extracting video information using the ytdl-core library.

## Features

- 🎥 **Video Information Extraction**: Get comprehensive metadata about YouTube videos
- 🎵 **Audio Download (MP3)**: Download audio-only streams in MP3 format
- 📹 **Video Download (MP4)**: Download video streams in MP4 format
- 🔒 **Security**: Input validation, URL sanitization, and rate limiting
- 📊 **Logging**: Comprehensive logging with Winston
- 🏥 **Health Check**: Built-in health monitoring endpoint
- 🧪 **Testing**: Complete test suite with Jest
- 🐳 **Docker Support**: Ready for containerization

## API Endpoints

### Health Check
```
GET /healthz
```
Returns the health status of the microservice.

### Service Information
```
GET /
```
Returns service information and available endpoints.

### Get Video Information
```
POST /v1/media/youtube/info
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```
Returns comprehensive video metadata including title, description, duration, thumbnails, and available formats.

### Download Audio (MP3)
```
POST /v1/media/youtube/mp3
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "quality": "highestaudio" // optional
}
```
Downloads and streams the audio as MP3 format.

### Download Video (MP4)
```
POST /v1/media/youtube/mp4
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "quality": "highest" // optional
}
```
Downloads and streams the video as MP4 format.

## Installation

### Prerequisites
- Node.js 18 or higher
- npm or yarn

### Local Development

1. **Clone and navigate to the microservice directory:**
   ```bash
   cd services/youtube-downloader
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

The service will be available at `http://localhost:3001`

## Configuration

Environment variables can be configured in the `.env` file:

```env
# Server Configuration
PORT=3001
NODE_ENV=development

# Security Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
API_KEY=your-api-key-here

# Rate Limiting Configuration
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# Logging Configuration
LOG_LEVEL=info
LOG_FILE_PATH=./logs
```

## Docker Deployment

### Build Image
```bash
docker build -t youtube-downloader .
```

### Run Container
```bash
docker run -p 3001:3001 -e NODE_ENV=production youtube-downloader
```

### Docker Compose
```yaml
version: '3.8'
services:
  youtube-downloader:
    build: .
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - PORT=3001
      - ALLOWED_ORIGINS=*
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Testing

### Run Tests
```bash
npm test
```

### Run Tests with Coverage
```bash
npm test -- --coverage
```

### Run Tests in Watch Mode
```bash
npm test -- --watch
```

## Security Features

### URL Validation
- Validates YouTube URL format
- Sanitizes URLs by removing tracking parameters
- Supports various YouTube URL formats (youtube.com, youtu.be, m.youtube.com)

### Rate Limiting
- 100 requests per 15-minute window per IP
- Configurable via environment variables

### Security Headers
- Helmet.js for security headers
- CORS configuration for allowed origins
- Input validation and sanitization

### Error Handling
- Comprehensive error handling with detailed logging
- Graceful error responses without exposing sensitive information
- Stream error handling for download endpoints

## Logging

The microservice uses Winston for structured logging:

- **Console Logging**: Colorized output for development
- **File Logging**: Separate error.log and combined.log files
- **Request Logging**: Morgan middleware for HTTP request logging
- **Structured Logging**: JSON format with metadata

## API Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data here
  },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "message": "Detailed error message",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## Usage Examples

### Get Video Information
```bash
curl -X POST http://localhost:3001/v1/media/youtube/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Download Audio
```bash
curl -X POST http://localhost:3001/v1/media/youtube/mp3 \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  --output audio.mp3
```

### Download Video
```bash
curl -X POST http://localhost:3001/v1/media/youtube/mp4 \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  --output video.mp4
```

## Performance Considerations

- **Stream Processing**: Downloads are streamed directly to the client without storing on disk
- **Memory Efficient**: Uses Node.js streams to minimize memory usage
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **Error Recovery**: Graceful handling of YouTube API changes and network issues

## Monitoring

### Health Check Endpoint
The `/healthz` endpoint provides:
- Service uptime
- Current timestamp
- Service version
- Health status

### Logging Metrics
- Request/response logging
- Error tracking with stack traces
- Performance metrics
- User agent and IP logging for debugging

## Troubleshooting

### Common Issues

1. **YouTube blocking requests**: The service uses proper User-Agent headers and request patterns to minimize blocking
2. **Video not available**: Some videos may be geo-restricted or private
3. **Rate limiting**: Adjust rate limiting settings based on your usage patterns
4. **Stream errors**: Network issues may cause stream interruptions

### Debug Mode
Enable detailed logging:
```bash
DEBUG_TESTS=true npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Disclaimer

This microservice is for educational and personal use. Please respect YouTube's Terms of Service and copyright laws when using this service.
