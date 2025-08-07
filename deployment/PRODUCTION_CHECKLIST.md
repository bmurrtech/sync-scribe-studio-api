# Production Deployment Checklist and Rollback Procedures

## Pre-Deployment Checklist

### 🔍 Code Quality and Testing
- [ ] All unit tests pass (`npm test` in YouTube service)
- [ ] Integration tests pass with Rick Roll video
- [ ] Security tests validate SSRF protection
- [ ] Rate limiting tests confirm proper throttling
- [ ] Load tests demonstrate acceptable performance
- [ ] Code review completed and approved
- [ ] No critical security vulnerabilities in dependencies (`npm audit`)
- [ ] ESLint and Prettier formatting checks pass

### 🐳 Docker Validation
- [ ] Docker image builds successfully
- [ ] Container passes health checks
- [ ] Multi-arch build (if needed) completed
- [ ] Image size optimized (< 500MB recommended)
- [ ] Non-root user configuration verified
- [ ] Security scanning completed (no HIGH/CRITICAL vulnerabilities)

### ☁️ GCP Cloud Run Preparation
- [ ] GCP project and billing configured
- [ ] Required APIs enabled (Cloud Run, Container Registry, Cloud Build)
- [ ] Service account created with minimal permissions
- [ ] IAM roles properly configured
- [ ] Environment variables reviewed and secured
- [ ] Resource limits appropriate (2GB RAM, 1 vCPU)
- [ ] Timeout configuration set (15 minutes for downloads)

### 🔐 Security Configuration
- [ ] CORS origins properly configured for production domains
- [ ] Rate limiting thresholds appropriate for production load
- [ ] Input validation and sanitization tested
- [ ] No sensitive data in environment variables or logs
- [ ] HTTPS enforcement configured
- [ ] Security headers properly set (Helmet.js configuration)

### 📊 Monitoring and Logging
- [ ] Log-based metrics configured in GCP
- [ ] Error tracking and alerting set up
- [ ] Performance monitoring enabled
- [ ] Health check endpoints responding correctly
- [ ] Log aggregation and retention policies set

### 📝 Documentation
- [ ] API documentation updated
- [ ] Deployment procedures documented
- [ ] Environment variables documented
- [ ] Troubleshooting guide available
- [ ] Architecture Decision Records (ADRs) up to date

## Deployment Process

### Phase 1: Pre-Deployment
```bash
# 1. Run comprehensive tests
cd tests
npm install
npm run test:integration
npm run test:security

# 2. Test Docker deployment locally
cd ..
chmod +x tests/deployment/docker-deployment-test.sh
./tests/deployment/docker-deployment-test.sh

# 3. Verify environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export BUILD_TAG="v$(date +%Y%m%d-%H%M%S)"
```

### Phase 2: Staging Deployment
```bash
# 1. Deploy to staging environment
cd deployment/gcp-cloud-run
chmod +x deploy.sh
./deploy.sh

# 2. Run smoke tests against staging
curl https://staging-youtube-downloader-service.run.app/healthz

# 3. Test Rick Roll functionality
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  https://staging-youtube-downloader-service.run.app/v1/media/youtube/info
```

### Phase 3: Production Deployment
```bash
# 1. Update production environment variables
export GCP_PROJECT_ID="production-project-id"
export GCP_REGION="us-central1"
export BUILD_TAG="production-v$(date +%Y%m%d-%H%M%S)"

# 2. Deploy to production
./deploy.sh

# 3. Verify deployment
curl https://youtube-downloader-service.run.app/healthz
```

### Phase 4: Post-Deployment Validation
```bash
# 1. Run production smoke tests
RICK_ROLL_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
SERVICE_URL="https://youtube-downloader-service.run.app"

# Health check
curl -f $SERVICE_URL/healthz || echo "Health check failed"

# Video info test
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "'$RICK_ROLL_URL'"}' \
  $SERVICE_URL/v1/media/youtube/info | jq '.success'

# Security header test
curl -I $SERVICE_URL/healthz | grep -i "x-content-type-options"

# Rate limiting test
for i in {1..10}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"url": "'$RICK_ROLL_URL'"}' \
    $SERVICE_URL/v1/media/youtube/info
done
```

## Monitoring and Alerting Setup

### Key Metrics to Monitor
- **Error Rate**: > 5% error rate triggers alert
- **Response Time**: > 30s for info endpoint, > 5min for downloads
- **Request Volume**: Unusual spikes or drops
- **Memory Usage**: > 80% of allocated memory
- **CPU Usage**: > 90% for extended periods
- **Concurrent Connections**: Approaching concurrency limits

### GCP Monitoring Setup
```bash
# Create alerting policies
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring/error-rate-policy.yaml

gcloud alpha monitoring policies create \
  --policy-from-file=monitoring/response-time-policy.yaml

# Set up log-based metrics
gcloud logging metrics create youtube_downloader_errors \
  --description="Error count for YouTube Downloader" \
  --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR'
```

## Rollback Procedures

### Immediate Rollback (Emergency)
If critical issues are detected within first 15 minutes:

```bash
# 1. Get previous revision
PREVIOUS_REVISION=$(gcloud run revisions list \
  --service=youtube-downloader \
  --region=us-central1 \
  --limit=2 \
  --format="value(metadata.name)" | tail -1)

# 2. Route 100% traffic to previous revision
gcloud run services update-traffic youtube-downloader \
  --to-revisions=$PREVIOUS_REVISION=100 \
  --region=us-central1

# 3. Verify rollback
curl https://youtube-downloader-service.run.app/healthz
```

### Graduated Rollback (Planned)
For less critical issues or planned rollbacks:

```bash
# 1. Gradually shift traffic
gcloud run services update-traffic youtube-downloader \
  --to-revisions=$PREVIOUS_REVISION=50,$CURRENT_REVISION=50 \
  --region=us-central1

# 2. Monitor metrics for 10 minutes
# 3. Complete rollback if issues persist
gcloud run services update-traffic youtube-downloader \
  --to-revisions=$PREVIOUS_REVISION=100 \
  --region=us-central1
```

### Database/State Rollback
Since this is a stateless service, no database rollback is required. However:

- [ ] Verify no configuration changes need reverting
- [ ] Check if any environment variables need restoration
- [ ] Confirm external service integrations still work

## Post-Rollback Actions

### Immediate Actions (0-30 minutes)
- [ ] Verify service functionality with Rick Roll test
- [ ] Check error rates return to normal
- [ ] Confirm all endpoints responding correctly
- [ ] Notify stakeholders of rollback completion

### Analysis Phase (30 minutes - 2 hours)
- [ ] Analyze logs to identify root cause
- [ ] Document issues in incident report
- [ ] Identify process improvements
- [ ] Update monitoring/alerting if needed

### Recovery Planning (2+ hours)
- [ ] Fix identified issues in code
- [ ] Update tests to catch similar issues
- [ ] Plan next deployment with fixes
- [ ] Update deployment procedures if needed

## Emergency Contacts and Escalation

### Primary On-Call
- **Role**: DevOps Engineer
- **Response Time**: 15 minutes
- **Responsibilities**: Deployment, rollback, infrastructure

### Secondary On-Call
- **Role**: Senior Developer
- **Response Time**: 30 minutes
- **Responsibilities**: Code issues, API problems

### Escalation Path
1. Primary On-Call (0-15 min)
2. Secondary On-Call (15-30 min)
3. Engineering Manager (30-60 min)
4. CTO/VP Engineering (60+ min)

## Testing Scenarios

### Smoke Tests (Run after every deployment)
```bash
#!/bin/bash
# smoke-test.sh
SERVICE_URL="https://youtube-downloader-service.run.app"
RICK_ROLL_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Test 1: Health Check
echo "Testing health check..."
curl -f $SERVICE_URL/healthz || exit 1

# Test 2: Rick Roll Video Info
echo "Testing Rick Roll video info..."
RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "'$RICK_ROLL_URL'"}' \
  $SERVICE_URL/v1/media/youtube/info)

if echo "$RESPONSE" | jq -r '.success' | grep -q 'true' && \
   echo "$RESPONSE" | jq -r '.data.title' | grep -qi 'rick'; then
  echo "✅ Rick Roll test passed"
else
  echo "❌ Rick Roll test failed"
  exit 1
fi

# Test 3: Security Headers
echo "Testing security headers..."
HEADERS=$(curl -s -I $SERVICE_URL/healthz)
if echo "$HEADERS" | grep -qi "x-content-type-options" && \
   echo "$HEADERS" | grep -qi "x-frame-options"; then
  echo "✅ Security headers present"
else
  echo "❌ Security headers missing"
  exit 1
fi

echo "🎉 All smoke tests passed!"
```

### Load Tests (Run before major releases)
```bash
#!/bin/bash
# load-test.sh
SERVICE_URL="https://youtube-downloader-service.run.app"
CONCURRENT_USERS=10
TEST_DURATION=60

# Install hey if not present
which hey || go install github.com/rakyll/hey@latest

# Run load test on health endpoint
echo "Running load test on health endpoint..."
hey -n 1000 -c $CONCURRENT_USERS -t $TEST_DURATION $SERVICE_URL/healthz

# Run load test on video info endpoint
echo "Running load test on video info endpoint..."
hey -n 100 -c 5 -t $TEST_DURATION \
  -m POST \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  $SERVICE_URL/v1/media/youtube/info
```

## Success Criteria

### Deployment Success
- [ ] All health checks pass
- [ ] Rick Roll video info retrieval works
- [ ] MP3/MP4 download endpoints respond
- [ ] Error rate < 1% for first hour
- [ ] Response time < 5s for info endpoint
- [ ] No critical errors in logs
- [ ] Monitoring and alerting operational

### Performance Benchmarks
- **Health Check**: < 200ms response time
- **Video Info**: < 5s response time
- **Download Initiation**: < 10s to start streaming
- **Concurrent Requests**: Support 100+ simultaneous requests
- **Memory Usage**: < 1.5GB under normal load
- **CPU Usage**: < 50% under normal load

## Maintenance Windows

### Planned Maintenance
- **Schedule**: Sundays 02:00-04:00 UTC (lowest traffic)
- **Notification**: 48 hours advance notice
- **Backup Plan**: Ability to postpone if issues arise

### Emergency Maintenance
- **Criteria**: Critical security vulnerability or service outage
- **Approval**: Engineering Manager or higher
- **Communication**: Immediate notification to stakeholders

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-27  
**Next Review**: 2025-04-27  
**Owner**: DevOps Team
