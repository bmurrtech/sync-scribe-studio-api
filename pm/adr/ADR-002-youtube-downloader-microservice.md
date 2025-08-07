# ADR-002: YouTube Downloader Microservice Implementation

**Date:** 2025-08-07  
**Status:** Accepted  
**Context:** Implementation of YouTube media downloading capabilities

## Decision

Implement YouTube downloading functionality as a separate Node.js/Express microservice using ytdl-core library, running independently from the main Python API.

## Context

The Sync Scribe Studio API requires YouTube video downloading capabilities to support transcription workflows. We need to decide between integrating this functionality directly into the main Python API or implementing it as a separate microservice.

## Options Considered

### Option 1: Integrate into Main Python API
- **Pros:**
  - Single codebase
  - Simpler deployment
  - Direct integration with existing endpoints
- **Cons:**
  - Python YouTube libraries are less reliable than ytdl-core
  - Mixing Python and Node.js dependencies
  - Monolithic architecture

### Option 2: Separate Node.js Microservice (CHOSEN)
- **Pros:**
  - Best-in-class ytdl-core library for YouTube downloading
  - Microservice architecture allows independent scaling
  - Clear separation of concerns
  - Technology-specific optimization (Node.js for streaming)
- **Cons:**
  - Additional deployment complexity
  - Service-to-service communication overhead
  - Multiple codebases to maintain

### Option 3: Third-party Service
- **Pros:**
  - No maintenance overhead
  - Potentially better uptime
- **Cons:**
  - External dependency
  - Cost implications
  - Limited customization
  - Data privacy concerns

## Decision

**Choose Option 2: Separate Node.js Microservice**

## Rationale

1. **Technical Excellence**: ytdl-core is the most reliable and maintained YouTube downloading library
2. **Scalability**: YouTube downloading is resource-intensive and benefits from independent scaling
3. **Reliability**: Isolating this functionality prevents YouTube-related issues from affecting the main API
4. **Performance**: Node.js streams are optimal for media downloading and streaming
5. **Security**: Dedicated security measures for external media source handling

## Implementation Details

### Architecture
```
Main Python API ←→ YouTube Downloader Microservice (Node.js)
                         ↓
                   ytdl-core library
                         ↓
                    YouTube API
```

### Key Features
- **Endpoints**: `/v1/media/youtube/{info,mp3,mp4}`
- **Security**: URL validation, sanitization, rate limiting
- **Monitoring**: Health checks, comprehensive logging
- **Deployment**: Docker containerization, independent scaling

### Security Measures
- Input validation and sanitization
- YouTube URL validation
- Rate limiting (100 requests per 15 minutes)
- Security headers via Helmet.js
- Request logging and monitoring

### API Design
- RESTful endpoints with consistent response format
- Stream-based downloads (no server storage)
- Comprehensive error handling
- Health check endpoint at `/healthz`

## Consequences

### Positive
- Best-in-class YouTube downloading capabilities
- Independent scaling and deployment
- Clear separation of concerns
- Technology-specific optimization
- Robust error handling and security

### Negative
- Additional operational complexity
- Service discovery and communication overhead
- Multiple deployment pipelines
- Potential network latency between services

### Neutral
- Need to implement service-to-service communication
- Additional monitoring and logging setup
- Separate testing and maintenance workflows

## Compliance Considerations

- Respects YouTube Terms of Service through proper API usage
- Implements rate limiting to avoid abuse
- Includes disclaimer for educational/personal use
- No storage of downloaded content on servers

## Monitoring and Observability

- Health check endpoint for service status
- Comprehensive logging with Winston
- Request/response tracking
- Error monitoring and alerting
- Performance metrics collection

## Future Considerations

- Potential integration with other video platforms
- Caching layer for video metadata
- Queue system for batch processing
- Integration with CDN for improved performance

## Related ADRs

- ADR-001: Project Structure and Development Setup
- Future ADRs may address service mesh, monitoring, or scaling decisions

---
**Implemented by:** AI Assistant  
**Reviewed by:** [Pending]  
**Next Review:** [When scaling requirements change]
