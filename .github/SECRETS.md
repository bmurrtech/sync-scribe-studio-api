# GitHub Secrets Configuration Guide

This document outlines the required GitHub secrets for the CI/CD pipeline to function properly.

## Required Secrets

### Google Cloud Platform (GCP) Configuration

#### `GCP_PROJECT_ID`
- **Description**: Your Google Cloud Project ID
- **Example**: `my-project-12345`
- **Used for**: Docker registry, Cloud Run deployment

#### `GCP_SA_KEY`
- **Description**: Service Account JSON key with required permissions
- **Format**: Complete JSON service account key
- **Required Permissions**:
  - Cloud Run Admin
  - Storage Admin (for Container Registry)
  - Service Account User
  - Cloud Build Editor
  - Artifact Registry Admin (if using Artifact Registry instead of GCR)

**Example service account key structure:**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "service-account-name@your-project-id.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account-name%40your-project-id.iam.gserviceaccount.com"
}
```

### Security and Monitoring

#### `SNYK_TOKEN` (Optional)
- **Description**: Snyk API token for vulnerability scanning
- **Format**: UUID-style token
- **Used for**: Security vulnerability scanning of dependencies
- **How to get**: Sign up at https://snyk.io and generate an API token

#### `CODECOV_TOKEN` (Optional)
- **Description**: Codecov token for coverage reporting
- **Format**: UUID-style token
- **Used for**: Uploading code coverage reports
- **How to get**: Sign up at https://codecov.io and get your repository token

### Action Tokens

#### `ACTION_BYPASS` (Optional)
- **Description**: Personal Access Token for bypassing certain GitHub restrictions
- **Format**: `ghp_...` GitHub PAT
- **Used for**: Build number updates, force pushes to protected branches
- **Permissions needed**: Contents (write), Metadata (read)

## Secret Configuration Instructions

### 1. Adding Secrets to GitHub

1. Navigate to your GitHub repository
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its respective name and value

### 2. Creating Google Cloud Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
    --description="Service account for GitHub Actions CI/CD" \
    --display-name="GitHub Actions SA"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.editor"

# Generate and download key
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Copy the contents of github-actions-key.json to GCP_SA_KEY secret
cat github-actions-key.json
```

### 3. Setting up Google Secret Manager for Application Secrets

```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secret for API key
echo -n "your-youtube-downloader-api-key" | \
    gcloud secrets create youtube-downloader-api-key --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding youtube-downloader-api-key \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Create additional secrets as needed
echo -n "your-database-url" | \
    gcloud secrets create database-url --data-file=-

echo -n "your-jwt-secret" | \
    gcloud secrets create jwt-secret --data-file=-
```

## Environment-Specific Secrets

### Staging Environment
- Secrets should use the same names but contain staging values
- Consider using different GCP projects for staging/production
- Use staging-specific database connections and API endpoints

### Production Environment
- Use production-grade secrets with high entropy
- Rotate secrets regularly
- Monitor secret access logs
- Use separate service accounts with minimal permissions

## Security Best Practices

### 1. Secret Rotation
- Rotate service account keys every 90 days
- Use Google Cloud Key Management Service for automatic rotation
- Monitor secret usage and access patterns

### 2. Principle of Least Privilege
- Grant minimal necessary permissions to service accounts
- Use separate service accounts for different environments
- Regularly audit and remove unused permissions

### 3. Monitoring and Alerting
- Set up Cloud Audit Logs for secret access monitoring
- Create alerts for unusual secret access patterns
- Monitor deployment failures that might expose secrets

### 4. Secret Validation
- Validate secrets in CI/CD pipeline before deployment
- Use health checks to verify secret accessibility
- Implement fallback mechanisms for secret failures

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**
   - Verify service account has required roles
   - Check that service account key is valid and not expired
   - Ensure APIs are enabled in GCP project

2. **"Secret not found" errors**
   - Verify secret names match exactly in code and GCP
   - Check that secrets exist in the correct GCP project
   - Ensure service account has `secretmanager.secretAccessor` role

3. **Docker registry authentication failures**
   - Verify service account has `storage.admin` role
   - Check that Container Registry API is enabled
   - Ensure correct project ID is used in image names

### Testing Secret Configuration

```bash
# Test service account permissions
gcloud auth activate-service-account --key-file=github-actions-key.json

# Test Cloud Run access
gcloud run services list --region=us-central1

# Test secret access
gcloud secrets versions access latest --secret="youtube-downloader-api-key"

# Test container registry access
gcloud auth configure-docker
docker pull gcr.io/YOUR_PROJECT_ID/youtube-downloader:latest
```

## Maintenance Schedule

- **Weekly**: Review secret access logs
- **Monthly**: Audit service account permissions
- **Quarterly**: Rotate service account keys
- **Annually**: Review and update security policies

## Contact and Support

For issues with secret configuration:
1. Check the troubleshooting section above
2. Review Google Cloud documentation
3. Contact the DevOps team
4. Create an issue in the repository with logs (redacting sensitive information)
