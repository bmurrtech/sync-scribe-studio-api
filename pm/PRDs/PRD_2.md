# PRD_2: sync-scribe-studio-api — Local Development & Packaging Prep for Gated Distribution

> **Context:**
> This PRD_2 is for an existing (brownfield) project. The end goal is to enable distribution. (e.g., DockerHub etc.). However, this document focuses strictly on local development and packaging. All external dependencies (such as self-hosted registries, automation for whitelist sync, and production databases) are out of scope for this PRD and are the responsibility of the user to set up.

---

## 1. Objective
- Prepare the sync-scribe-studio-api for local development, testing, and packaging.
- Ensure the codebase is ready for future cloud deployment and gated distribution, but do not implement or require any external infrastructure or automations at this stage.

---

## 2. Functional Requirements

### 2.1. Local Development
- The project must be runnable locally via Docker Compose or a simple `docker run` command.
- All configuration should be possible via environment variables or local config files.
- No external services (registries, auth providers, databases) are required to run or test locally.

### 2.2. Packaging
- Provide a Dockerfile that builds the sync-scribe-studio-api image.
- The image should expose the HTTP API on a configurable port (default: 8080).
- The container must be stateless (no persistent local storage required).
- Include a basic healthcheck endpoint (e.g., `/healthz`).

### 2.3. Local Testing
- Document how to build and run the image locally.
- Provide example curl commands for hitting the API endpoints.
- Include a simple local whitelist mechanism (e.g., a static file or environment variable) for simulating gated access, but do not implement any external sync or automation.
- Unauthorized requests should return 401/403.

---

## 3. Out of Scope
- Setting up or configuring a public/private Docker registry.
- Automating whitelist sync from Skool or any other external service.
- Managing or deploying any production database or external authentication provider.
- Any infrastructure or automation outside the local development environment.

---

## 4. Non-Functional & Deployment Requirements
- The container must be stateless and not require any storage dependencies.
- All configuration must be local and documented.
- The Docker image should be tagged and versioned for future rollback.
- CI/CD pipeline steps (if any) should only cover build and local test, not deployment or external publishing.

---

## 5. Acceptance Criteria
- The Docker image can be built and run locally by any developer.
- API endpoints are reachable and enforce local whitelist gating.
- Unauthorized users are blocked.
- All local configuration and test steps are clearly documented in the README.
- The codebase is ready for future cloud deployment and integration with external gating/automation, but does not require it for local use.

---

## 6. Local Test Workflow
- Build image: `docker build -t sync-scribe-studio-api .`
- Run locally: `docker run -p 8080:8080 -e PORT=8080 sync-scribe-studio-api`
- Test endpoint with token/email (using local whitelist):
  ```bash
  curl -H "X-API-KEY: <key>" http://localhost:8080/info?url=...
  ```
- Update local whitelist and test access/offboard.

---

## 7. Future Context (for Reference Only)
- The ultimate goal is to enable gated distribution and automated management of deployment access for paying/active members.
- External dependencies (e.g., registry, automation, production DB) will be addressed in future PRDs or deployment guides.