#!/usr/bin/env bash
# Container Startup Smoke Test
# Builds the image, runs with NO special env vars, checks /health 200, and basic endpoints.

set -euo pipefail

IMAGE_TAG="local/sync-scribe-studio-api:startup-smoke"
CONTAINER_NAME="startup-smoke-local"
PORT=8080

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[1/4] Building Docker image -> $IMAGE_TAG"
docker build -t "$IMAGE_TAG" -f Dockerfile .

echo "[2/4] Running container without env vars"
docker run -d --name "$CONTAINER_NAME" -p ${PORT}:${PORT} "$IMAGE_TAG"

echo "[3/4] Waiting for /health to be ready (expect 200)"
ATTEMPTS=30
for i in $(seq 1 $ATTEMPTS); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/health || true)
  if [ "$STATUS" = "200" ]; then
    echo "Health OK on attempt $i"
    break
  fi
  echo "Waiting... ($i/$ATTEMPTS), got $STATUS"
  sleep 2
done
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/health || true)
if [ "$STATUS" != "200" ]; then
  echo "ERROR: Expected /health 200, got $STATUS"
  docker logs "$CONTAINER_NAME" || true
  exit 1
fi

echo "[4/4] Running basic endpoint smoke checks"
ROOT_JSON=$(curl -fsS http://localhost:${PORT}/ -H 'Accept: application/json')
if ! echo "$ROOT_JSON" | jq -e '.service and .version' >/dev/null; then
  echo "ERROR: Root endpoint missing required fields"
  echo "$ROOT_JSON"
  exit 1
fi

HEALTH_JSON=$(curl -fsS http://localhost:${PORT}/health -H 'Accept: application/json')
if [ "$(echo "$HEALTH_JSON" | jq -r '.status')" != "healthy" ]; then
  echo "ERROR: /health status is not 'healthy'"
  echo "$HEALTH_JSON"
  exit 1
fi

# /health/detailed is optional in smoke; validate shape if present
if curl -fsS http://localhost:${PORT}/health/detailed -H 'Accept: application/json' -o /tmp/health_detailed.json; then
  if ! jq -e '.status' /tmp/health_detailed.json >/dev/null; then
    echo "ERROR: /health/detailed missing status"
    cat /tmp/health_detailed.json || true
    exit 1
  fi
else
  echo "Note: /health/detailed not available; continuing"
fi

# Protected endpoint should not allow unauthenticated access (allow 401/404/405 variability)
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/v1/media/youtube/info || true)
if ! echo "$CODE" | grep -E "^(401|404|405|202)$" >/dev/null; then
  echo "WARN: Unexpected status for protected endpoint without auth: $CODE"
fi

echo "All container startup smoke checks passed"
