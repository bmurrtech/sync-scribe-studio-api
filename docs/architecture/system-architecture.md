# System Architecture - Sync Scribe Studio API

## Overview

The Sync Scribe Studio API is designed as a microservices-based system that provides media processing capabilities with a focus on YouTube content download and transcription services.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                            │
├─────────────────────────────────────────────────────────────┤
│  Web Apps  │  Mobile Apps  │  API Clients  │  Third-party   │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway / Load Balancer              │
│                     (nginx / HAProxy)                      │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                Main Python API (Flask)                      │
├─────────────────────────────────────────────────────────────┤
│  • Authentication & Authorization                           │
│  • Request Validation & Rate Limiting                      │
│  • Job Queue Management                                     │
│  • Response Orchestration                                   │
│  • Dynamic Route Registration                               │
└─────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
┌─────────────────────┐  ┌──────────────┐  ┌──────────────┐
│   YouTube Download  │  │    Media     │  │   Future     │
│   Microservice      │  │  Processing  │  │ Microservices│
│   (Node.js/Express) │  │   Services   │  │              │
├─────────────────────┤  ├──────────────┤  ├──────────────┤
│ • Video Info        │  │ • Transcribe │  │ • Translation│
│ • MP3 Download      │  │ • Convert    │  │ • Analysis   │
│ • MP4 Download      │  │ • Edit       │  │ • etc.       │
│ • Health Checks     │  │ • Compress   │  │              │
└─────────────────────┘  └──────────────┘  └──────────────┘
           │                      │               │
           ▼                      ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Services Layer                   │
├─────────────────────────────────────────────────────────────┤
│  YouTube API  │  Cloud Storage  │  CDN  │  Monitoring      │
│               │  (GCP/AWS/S3)   │       │  (Prometheus)    │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Main Python API (Flask)

**Location**: Root directory  
**Technology**: Python 3.11+, Flask, Gunicorn  
**Responsibilities**:
- Centralized authentication and authorization
- Request validation using JSON schemas
- Rate limiting and security measures
- Job queue management for long-running tasks
- Dynamic route registration system
- Microservice orchestration
- Response formatting and error handling

**Key Features**:
- **Dynamic Route Discovery**: Automatically registers all Flask blueprints in `/routes` directory
- **Authentication Middleware**: JWT/API key based authentication
- **Queue System**: Redis-based job queue for async processing
- **Monitoring**: Health checks and metrics collection
- **Security**: Rate limiting, input validation, secure headers

### 2. YouTube Download Microservice

**Location**: `/services/youtube-downloader/`  
**Technology**: Node.js 18+, Express.js, ytdl-core  
**Responsibilities**:
- YouTube video metadata extraction
- Audio download (MP3 format)
- Video download (MP4 format)
- Stream-based content delivery
- URL validation and sanitization

**Architecture Details**:
```
┌─────────────────────────────────┐
│     YouTube Microservice        │
├─────────────────────────────────┤
│  Express.js Application         │
│  ┌─────────────────────────────┐ │
│  │     Route Handlers          │ │
│  │ • /v1/media/youtube/info    │ │
│  │ • /v1/media/youtube/mp3     │ │
│  │ • /v1/media/youtube/mp4     │ │
│  │ • /healthz                  │ │
│  └─────────────────────────────┘ │
│  ┌─────────────────────────────┐ │
│  │     Middleware Stack        │ │
│  │ • CORS                      │ │
│  │ • Rate Limiting             │ │
│  │ • Request Validation        │ │
│  │ • Error Handling            │ │
│  └─────────────────────────────┘ │
│  ┌─────────────────────────────┐ │
│  │     Core Services           │ │
│  │ • ytdl-core Integration     │ │
│  │ • Stream Processing         │ │
│  │ • URL Validation            │ │
│  └─────────────────────────────┘ │
└─────────────────────────────────┘
           │
           ▼
    YouTube API/CDN
```

**Communication Pattern**:
- **Protocol**: HTTP/HTTPS REST API
- **Data Format**: JSON for metadata, Binary streams for media
- **Timeout**: Configurable (default: 30 seconds)
- **Retry Logic**: Exponential backoff with 3 attempts
- **Health Checks**: `/healthz` endpoint with service status

### 3. Media Processing Services

**Location**: `/services/v1/`  
**Technology**: Python, FFmpeg, various media libraries  
**Responsibilities**:
- Audio/video transcription
- Format conversion
- Media editing and processing
- Cloud storage integration
- Metadata extraction

### 4. Communication Patterns

#### A. Inter-Service Communication
```
Main API ←──HTTP──→ YouTube Microservice
    │                      │
    │                      ▼
    │               YouTube API/CDN
    │
    ├──HTTP──→ Media Processing Services
    │                      │
    │                      ▼
    │               FFmpeg/External Tools
    │
    └──HTTP──→ Cloud Storage (Upload/Download)
```

#### B. Request Flow
1. **Client Request** → Main API
2. **Authentication** → Validate API key
3. **Request Validation** → JSON schema validation
4. **Job Queuing** → Add to processing queue (if async)
5. **Microservice Call** → Forward to appropriate microservice
6. **Response Processing** → Format and return response
7. **Webhook Notification** → Notify client (if configured)

#### C. Error Handling Flow
```
Error Occurs → Log Error → Determine Error Type
     │              │            │
     │              │            ├──4xx Client Error──→ Return Error to Client
     │              │            │
     │              │            ├──5xx Server Error──→ Retry Logic
     │              │            │
     │              │            └──503 Service Down──→ Circuit Breaker
     │              │
     │              └──Security Events──→ Rate Limiting / Blocking
     │
     └──Metrics Collection──→ Monitoring Dashboard
```

## Data Flow Architecture

### 1. YouTube Video Processing Flow
```
Client Request
     │
     ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Validate      │───▶│   Queue Job      │───▶│  Call YouTube   │
│   YouTube URL   │    │   (if async)     │    │  Microservice   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Return        │◀───│   Process        │◀───│  Download from  │
│   Response      │    │   Response       │    │  YouTube API    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 2. Media Download Flow (Streaming)
```
Client Request ──┐
                 ▼
           ┌──────────┐
           │ Main API │
           └──────────┘
                 │ HTTP Request
                 ▼
      ┌─────────────────────┐
      │YouTube Microservice │
      └─────────────────────┘
                 │ HTTP Stream Request  
                 ▼
          ┌─────────────┐
          │ YouTube API │
          └─────────────┘
                 │ Media Stream
                 ▼
      ┌─────────────────────┐
      │YouTube Microservice │──┐
      └─────────────────────┘  │ Process & Stream
                 ▲             │
                 │             ▼
           ┌──────────┐    ┌──────────┐
           │ Main API │◀───│  Client  │
           └──────────┘    └──────────┘
```

## Security Architecture

### 1. Authentication & Authorization
```
┌──────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├──────────────────────────────────────────────────────────────┤
│ Layer 1: Network Security                                    │
│  • HTTPS/TLS encryption                                      │
│  • VPC/Private networks for inter-service communication     │
│  • Firewall rules and security groups                       │
├──────────────────────────────────────────────────────────────┤
│ Layer 2: API Gateway Security                               │
│  • Rate limiting (IP and API key based)                     │
│  • DDoS protection                                           │
│  • Request size limits                                       │
├──────────────────────────────────────────────────────────────┤
│ Layer 3: Application Security                               │
│  • API key authentication                                    │
│  • Input validation and sanitization                        │
│  • SQL injection prevention                                 │
│  • XSS protection headers                                   │
├──────────────────────────────────────────────────────────────┤
│ Layer 4: Service Security                                   │
│  • Inter-service authentication                             │
│  • Service-specific rate limiting                           │
│  • Content validation                                        │
├──────────────────────────────────────────────────────────────┤
│ Layer 5: Data Security                                      │
│  • Encryption at rest                                        │
│  • Secure temporary file handling                           │
│  • PII data masking in logs                                 │
└──────────────────────────────────────────────────────────────┘
```

### 2. Rate Limiting Strategy
```
Global Rate Limits:
├── By IP Address: 1000 requests/hour
├── By API Key: 5000 requests/hour
└── By Endpoint:
    ├── /v1/media/youtube/info: 200/15min
    ├── /v1/media/youtube/mp3: 20/15min
    ├── /v1/media/youtube/mp4: 20/15min
    └── /v1/health/*: 100/minute
```

## Deployment Architecture

### 1. Development Environment
```
┌─────────────────────────────────────────┐
│           Local Development             │
├─────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ │
│ │   Main API      │ │   YouTube       │ │
│ │   localhost:8080│ │   localhost:3001│ │
│ └─────────────────┘ └─────────────────┘ │
│ ┌─────────────────┐ ┌─────────────────┐ │
│ │   Redis         │ │   PostgreSQL    │ │
│ │   localhost:6379│ │   localhost:5432│ │
│ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────┘
```

### 2. Docker Compose Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                 Docker Network: sync-scribe-network         │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│ │   main-api      │ │youtube-downloader│ │    redis      │  │
│ │   Port: 8080    │ │   Port: 3001    │ │ Port: 6379    │  │
│ └─────────────────┘ └─────────────────┘ └───────────────┘  │
│ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│ │   nginx         │ │   postgresql    │ │  monitoring   │  │
│ │   Port: 80/443  │ │   Port: 5432    │ │ Port: 9090    │  │
│ └─────────────────┘ └─────────────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3. Cloud Deployment (GCP)
```
┌─────────────────────────────────────────────────────────────┐
│                      Google Cloud Platform                  │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│ │   Cloud Run     │ │   Cloud Run     │ │  Cloud SQL    │  │
│ │   (Main API)    │ │(YouTube Service)│ │ (PostgreSQL)  │  │
│ │   Auto-scaling  │ │   Auto-scaling  │ │  Managed      │  │
│ └─────────────────┘ └─────────────────┘ └───────────────┘  │
│ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│ │  Cloud Storage  │ │   Memorystore   │ │Cloud Monitoring│  │
│ │   (Media Files) │ │    (Redis)      │ │   & Logging   │  │
│ │   CDN Enabled   │ │   Managed       │ │   Integrated  │  │
│ └─────────────────┘ └─────────────────┘ └───────────────┘  │
│ ┌─────────────────┐ ┌─────────────────┐                   │
│ │  Load Balancer  │ │    Cloud NAT    │                   │
│ │  (Global HTTPS) │ │  (Outbound)     │                   │
│ └─────────────────┘ └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring and Observability

### 1. Logging Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Centralized Logging                      │
├─────────────────────────────────────────────────────────────┤
│ Application Logs                                            │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │  Main API   │ │  YouTube    │ │   Other     │            │
│ │    Logs     │ │   Service   │ │  Services   │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
│        │              │              │                     │
│        └──────────────┼──────────────┘                     │
│                       ▼                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │            Log Aggregation System                       │ │
│ │         (Fluentd/Logstash/Cloud Logging)               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                       │                                     │
│                       ▼                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │          Log Storage & Search                           │ │
│ │      (Elasticsearch/Cloud Logging/BigQuery)            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2. Metrics and Monitoring
```
Application Metrics:
├── Request Metrics
│   ├── Request count by endpoint
│   ├── Response time percentiles
│   ├── Error rates by service
│   └── Rate limiting violations
├── System Metrics
│   ├── CPU and memory usage
│   ├── Disk I/O and network
│   ├── Container health status
│   └── Database connections
├── Business Metrics
│   ├── YouTube downloads per hour
│   ├── Media processing jobs
│   ├── User activity patterns
│   └── Service availability SLA
└── Custom Metrics
    ├── Microservice communication latency
    ├── External API response times
    ├── Queue depth and processing times
    └── Storage utilization
```

## Scalability Considerations

### 1. Horizontal Scaling Strategy
- **Stateless Services**: All services designed to be stateless for easy scaling
- **Load Balancing**: Round-robin and health-check based routing
- **Auto-scaling**: Based on CPU, memory, and queue depth metrics
- **Database Scaling**: Read replicas and connection pooling

### 2. Performance Optimization
- **Caching**: Redis for frequently accessed data
- **CDN**: Static content and media file delivery
- **Compression**: Gzip compression for API responses
- **Streaming**: Memory-efficient streaming for large media files

### 3. Reliability Patterns
- **Circuit Breaker**: Prevent cascading failures
- **Retry Logic**: Exponential backoff for transient failures
- **Health Checks**: Comprehensive health monitoring
- **Graceful Degradation**: Fallback mechanisms for service outages

## Future Architecture Considerations

### 1. Planned Enhancements
- **Message Queue System**: Implement Apache Kafka or RabbitMQ for better async processing
- **Service Mesh**: Consider Istio for advanced service-to-service communication
- **GraphQL API**: Unified API layer for complex data fetching
- **Event-Driven Architecture**: Implement domain events for better decoupling

### 2. Technology Evolution
- **Container Orchestration**: Kubernetes for better container management
- **Serverless Components**: Cloud Functions for lightweight processing
- **AI/ML Integration**: TensorFlow Serving for media analysis
- **Real-time Features**: WebSocket support for real-time updates

---

**Last Updated**: 2025-01-27  
**Version**: 2.0.0  
**Architecture Review Date**: [Next review scheduled for Q2 2025]

> This architecture document should be reviewed and updated whenever significant changes are made to the system design or when new microservices are added.
