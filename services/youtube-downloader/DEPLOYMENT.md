# YouTube Downloader CI/CD Deployment Guide

This document provides comprehensive information about the CI/CD pipeline and deployment process for the YouTube Downloader microservice.

## Overview

The CI/CD pipeline automatically builds, tests, and deploys the YouTube Downloader service to Google Cloud Run in multiple environments (staging and production) with comprehensive security scanning, quality checks, and monitoring.

## Pipeline Architecture

### Workflow Triggers
- **Push to `main`**: Triggers full pipeline → Production deployment
- **Push to `develop`/`staging`**: Triggers pipeline → Staging deployment
- **Pull Requests**: Triggers testing and security scans (no deployment)
- **Manual Dispatch**: Allows manual deployment to specific environments

### Pipeline Stages

1. **Security & Dependency Scanning**
   - npm audit for known vulnerabilities
   - Snyk security scanning for dependencies
   - Runs on PRs and main branch pushes

2. **Code Quality & Linting**
   - ESLint for code quality
   - Prettier for code formatting
   - TODO/FIXME comment detection

3. **Testing**
   - Unit tests with Jest
   - Integration tests with Supertest
   - Code coverage reporting
   - Multi-Node.js version testing (18, 20)

4. **Docker Build & Security Scan**
   - Multi-stage Docker build for optimized images
   - Container vulnerability scanning with Trivy
   - Push to Google Container Registry

5. **Deployment**
   - Staging: Zero-downtime deployment with traffic allocation
   - Production: Canary deployment with gradual traffic migration
   - Automated smoke tests after deployment

## Environments

### Staging Environment
- **URL**: `https://youtube-downloader-staging-[hash].run.app`
- **Purpose**: Final testing before production
- **Resources**: 1 CPU, 512Mi memory, 0-10 instances
- **Deployment**: Automatic on `develop`/`staging` branch pushes

### Production Environment
- **URL**: `https://youtube-downloader-[hash].run.app`
- **Purpose**: Live user-facing service
- **Resources**: 2 CPU, 1Gi memory, 1-100 instances
- **Deployment**: Automatic on `main` branch pushes with canary rollout

## Deployment Process

### Automatic Deployment

#### To Staging
1. Push code to `develop` or `staging` branch
2. Pipeline runs all quality checks
3. If checks pass, builds and pushes Docker image
4. Deploys to Cloud Run staging service
5. Runs smoke tests to verify deployment

#### To Production
1. Push code to `main` branch (typically via PR merge)
2. Pipeline runs all quality checks
3. If checks pass, builds and pushes Docker image
4. Deploys to Cloud Run with canary strategy:
   - Initial: 10% traffic to new version, 90% to previous
   - After 5 minutes: 100% traffic to new version
5. Runs comprehensive smoke tests

### Manual Deployment

1. Go to **Actions** tab in GitHub repository
2. Select **YouTube Downloader CI/CD Pipeline**
3. Click **Run workflow**
4. Choose target environment and options
5. Click **Run workflow**

## Configuration

### Environment Variables

#### Staging
```bash
NODE_ENV=staging
LOG_LEVEL=info
PORT=3001
```

#### Production
```bash
NODE_ENV=production
LOG_LEVEL=warn
PORT=3001
```

### Secrets Management

Secrets are managed via Google Secret Manager:
- `youtube-downloader-api-key`: API authentication key
- Additional secrets can be added as needed

See [GitHub Secrets Guide](../../.github/SECRETS.md) for configuration details.

### Resource Allocation

#### Staging
- **CPU**: 1 vCPU
- **Memory**: 512Mi
- **Concurrency**: 100 requests per instance
- **Min Instances**: 0 (cost optimization)
- **Max Instances**: 10
- **Timeout**: 300 seconds

#### Production
- **CPU**: 2 vCPUs
- **Memory**: 1Gi
- **Concurrency**: 100 requests per instance
- **Min Instances**: 1 (availability)
- **Max Instances**: 100
- **Timeout**: 300 seconds

## Monitoring & Observability

### Health Checks
- **Endpoint**: `/healthz`
- **Frequency**: Every 30 seconds
- **Timeout**: 10 seconds
- **Failure Threshold**: 3 consecutive failures

### Smoke Tests
After each deployment, automated tests verify:
- Health endpoint responds correctly
- Core functionality works (video info retrieval)
- Response format is correct
- Security headers are present

### Logs
- **Location**: Google Cloud Logging
- **Retention**: 30 days (configurable)
- **Levels**: Error, Warn, Info (staging), Warn+ (production)

### Metrics
Monitored via Google Cloud Monitoring:
- Request count and latency
- Error rates
- Memory and CPU usage
- Instance scaling events

## Troubleshooting

### Common Deployment Issues

#### 1. Pipeline Fails at Testing Stage
**Symptoms**: Tests fail in CI
**Solutions**:
- Check test logs in GitHub Actions
- Run tests locally: `npm test`
- Ensure all dependencies are installed
- Check for environment-specific issues

#### 2. Docker Build Fails
**Symptoms**: Docker build step fails
**Solutions**:
- Check Dockerfile syntax
- Ensure all files are included (not in .dockerignore)
- Verify base image availability
- Check for build context issues

#### 3. GCP Authentication Issues
**Symptoms**: "Permission denied" or "Authentication failed"
**Solutions**:
- Verify `GCP_SA_KEY` secret is correctly configured
- Check service account permissions
- Ensure GCP APIs are enabled
- Verify project ID is correct

#### 4. Cloud Run Deployment Fails
**Symptoms**: Deployment fails or service doesn't start
**Solutions**:
- Check Cloud Run logs for startup errors
- Verify environment variables and secrets
- Check resource limits and quotas
- Ensure port configuration is correct (3001)

#### 5. Smoke Tests Fail
**Symptoms**: Deployment succeeds but smoke tests fail
**Solutions**:
- Check service logs for runtime errors
- Verify external dependencies (YouTube API)
- Check network connectivity
- Ensure health endpoint is responding

### Debugging Commands

```bash
# Check Cloud Run service status
gcloud run services describe youtube-downloader --region=us-central1

# View service logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=youtube-downloader" --limit=50

# Test service locally
curl https://your-service-url/healthz
curl -X POST -H "Content-Type: application/json" -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' https://your-service-url/v1/media/youtube/info

# Check current traffic allocation
gcloud run services describe youtube-downloader --region=us-central1 --format="value(spec.traffic[].percent, spec.traffic[].tag)"
```

## Rollback Procedures

### Automatic Rollback
- If smoke tests fail, the pipeline will not migrate traffic to the new version
- Previous version continues to serve traffic

### Manual Rollback

1. **Via GitHub Actions**:
   - Go to Actions tab → Find previous successful deployment
   - Re-run the workflow with the same parameters

2. **Via Google Cloud Console**:
   - Navigate to Cloud Run → Select service
   - Go to Revisions tab → Find previous revision
   - Manage Traffic → Allocate 100% to previous revision

3. **Via gcloud CLI**:
   ```bash
   # List revisions
   gcloud run revisions list --service=youtube-downloader --region=us-central1
   
   # Roll back to specific revision
   gcloud run services update-traffic youtube-downloader \
     --region=us-central1 \
     --to-revisions=REVISION_NAME=100
   ```

## Performance Optimization

### Image Optimization
- Multi-stage Docker build reduces image size
- Node.js 18 Alpine base for minimal footprint
- Only production dependencies in final image

### Caching Strategy
- GitHub Actions cache for Node.js dependencies
- Docker layer caching for faster builds
- Container Registry image caching

### Resource Tuning
- Memory and CPU allocation based on load testing
- Auto-scaling configuration for traffic spikes
- Connection pooling and keep-alive settings

## Security Considerations

### Container Security
- Non-root user execution
- Minimal base image (Alpine Linux)
- Regular vulnerability scanning with Trivy
- No sensitive data in container images

### Network Security
- HTTPS-only communication
- Proper CORS configuration
- Security headers (HSTS, CSP, etc.)
- Rate limiting and request validation

### Access Control
- Service account with minimal required permissions
- Secret management via Google Secret Manager
- Regular key rotation
- Audit logging for all access

## Maintenance

### Regular Tasks
- **Weekly**: Review deployment logs and metrics
- **Monthly**: Update dependencies and base images
- **Quarterly**: Rotate service account keys
- **Annually**: Review and update security policies

### Updates and Patches
1. Security patches are prioritized and deployed immediately
2. Feature updates follow normal development workflow
3. Dependency updates are tested in staging first
4. Breaking changes require migration planning

## Support and Contacts

### Escalation Path
1. Check this documentation and troubleshooting section
2. Review GitHub Actions logs and GCP logs
3. Contact DevOps team with specific error messages
4. Create incident ticket for production issues

### Useful Links
- [GitHub Repository](../..)
- [Google Cloud Console](https://console.cloud.google.com)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
