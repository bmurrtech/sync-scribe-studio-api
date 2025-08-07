# ADR-003: Microservice Communication Patterns

**Date:** 2025-01-27  
**Status:** Accepted  
**Context:** Standardizing communication patterns between Python API and Node.js microservices

## Decision

Implement HTTP-based request-response communication pattern with retry logic, health checks, and streaming support for media downloads.

## Context

With the introduction of the YouTube downloader microservice, we needed to establish clear communication patterns between the main Python Flask API and external Node.js microservices. The system must be resilient, performant, and maintainable.

## Options Considered

### Option 1: Message Queue (Redis/RabbitMQ) (NOT CHOSEN)
- **Pros:**
  - Asynchronous processing
  - Built-in retry mechanisms
  - Horizontal scaling
  - Fault tolerance
- **Cons:**
  - Additional infrastructure complexity
  - Operational overhead
  - Learning curve for team
  - Overkill for current requirements

### Option 2: HTTP Request-Response with Retry Logic (CHOSEN)
- **Pros:**
  - Simple and well-understood
  - Direct integration with existing Flask patterns
  - Easy testing and debugging
  - No additional infrastructure requirements
- **Cons:**
  - Synchronous nature can block requests
  - Less resilient than message queues
  - Potential cascading failures

### Option 3: gRPC Communication (NOT CHOSEN)
- **Pros:**
  - High performance
  - Type safety with protobuf
  - Streaming support
- **Cons:**
  - Additional complexity
  - Learning curve
  - HTTP/2 requirements
  - Overkill for current scale

## Decision Rationale

**Choose Option 2: HTTP Request-Response with Retry Logic**

## Implementation Details

### Core Communication Pattern
```python
def make_youtube_request(endpoint, data=None, method='POST', stream=False):
    """
    Make HTTP request to YouTube microservice with retry logic
    """
    url = urljoin(YOUTUBE_SERVICE_URL, endpoint)
    
    for attempt in range(YOUTUBE_RETRY_ATTEMPTS):
        try:
            # Make request with appropriate method
            if method.upper() == 'GET':
                response = requests.get(url, timeout=YOUTUBE_SERVICE_TIMEOUT, stream=stream)
            else:
                response = requests.post(url, json=data, timeout=YOUTUBE_SERVICE_TIMEOUT, stream=stream)
            
            # Don't retry on client errors (4xx)
            if response.status_code < 500:
                return response
                
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt < YOUTUBE_RETRY_ATTEMPTS - 1:
                time.sleep(YOUTUBE_RETRY_DELAY)
            continue
    
    raise requests.RequestException("Microservice unavailable after all retry attempts")
```

### Key Features

#### 1. Retry Logic
- Configurable retry attempts (default: 3)
- Exponential backoff with configurable delay
- Smart retry logic (don't retry 4xx errors)
- Comprehensive error logging

#### 2. Health Checks
- Dedicated health check endpoints
- Service availability verification before requests
- Graceful degradation when services are unhealthy

#### 3. Streaming Support
- Stream large media files without buffering
- Memory-efficient chunk-based streaming
- Proper header propagation

#### 4. Error Handling
- Timeout handling
- Connection error recovery
- JSON error response parsing
- Fallback error messages

#### 5. Configuration
- Environment-based configuration
- Configurable timeouts and retry parameters
- Service URL configuration

### Configuration Parameters

```python
YOUTUBE_SERVICE_URL = os.environ.get('YOUTUBE_SERVICE_URL', 'http://localhost:3001')
YOUTUBE_SERVICE_TIMEOUT = int(os.environ.get('YOUTUBE_SERVICE_TIMEOUT', '30'))
YOUTUBE_RETRY_ATTEMPTS = int(os.environ.get('YOUTUBE_RETRY_ATTEMPTS', '3'))
YOUTUBE_RETRY_DELAY = int(os.environ.get('YOUTUBE_RETRY_DELAY', '1'))
```

### API Design Patterns

#### 1. Consistent Error Responses
```python
# Success
return response_data, endpoint, 200

# Client error
return error_message, endpoint, 400

# Service unavailable
return "YouTube service unavailable", endpoint, 503
```

#### 2. Health Check Integration
```python
if not is_youtube_service_healthy():
    return "YouTube service is currently unavailable", endpoint, 503
```

#### 3. Streaming Response Pattern
```python
def generate():
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            yield chunk

return Response(generate(), headers=response_headers)
```

## Consequences

### Positive
- Simple and maintainable communication pattern
- Built-in resilience with retry logic
- Efficient streaming for large media files
- Easy to test and debug
- No additional infrastructure required
- Consistent error handling across services

### Negative
- Synchronous nature can impact performance under high load
- No built-in load balancing (requires external load balancer)
- Potential cascading failures if not properly handled
- Limited to request-response patterns

### Neutral
- Requires proper service discovery configuration
- Need to monitor service health actively
- Must implement circuit breaker patterns for production

## Monitoring and Observability

### Logging Strategy
- Log all service requests with attempt numbers
- Log retry attempts and reasons
- Log service health check results
- Include job IDs for request tracing

### Metrics to Monitor
- Service response times
- Retry attempt frequencies
- Health check success rates
- Error response patterns
- Streaming throughput

## Future Considerations

### Potential Improvements
1. **Circuit Breaker Pattern**: Implement circuit breakers to prevent cascading failures
2. **Load Balancing**: Add support for multiple service instances
3. **Connection Pooling**: Implement HTTP connection pooling for better performance
4. **Service Discovery**: Implement dynamic service discovery mechanism
5. **Message Queue Migration**: Consider migrating to async patterns as scale increases

### Breaking Changes
- Any changes to this communication pattern should maintain backward compatibility
- New microservices should follow these established patterns
- Consider versioning communication protocols

## Related ADRs

- ADR-002: YouTube Downloader Microservice Implementation
- Future: ADR-004: Service Discovery and Load Balancing
- Future: ADR-005: Circuit Breaker Implementation

## References

- [requests library documentation](https://docs.python-requests.org/)
- [Flask Response streaming](https://flask.palletsprojects.com/en/2.3.x/patterns/streaming/)
- [Microservice Communication Patterns](https://microservices.io/patterns/communication-style/messaging.html)

---
**Implemented by:** AI Assistant  
**Reviewed by:** [Pending]  
**Next Review:** [When adding new microservices or scaling requirements change]
