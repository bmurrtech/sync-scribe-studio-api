"""
Minimal security utilities compatible with this repository.

Goals:
- Avoid breaking imports/startup
- Keep dependency-free (no extra packages)
- Provide API key auth decorator and lightweight, per-instance rate limiting
- Provide optional security headers and basic CORS support via env vars

Notes:
- This file is an example/reference. Integrate selectively.
- In-memory rate limiting is per-container and resets on scale events.
- For robust/global rate limiting and WAF, use Cloud Armor or Cloudflare.
"""

from __future__ import annotations

import os
import time
import threading
from collections import deque
from functools import wraps
from typing import Callable, Deque, Dict, Tuple

from flask import Request, Response, request, jsonify


# -----------------------------
# Configuration via environment
# -----------------------------

RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "100"))
RATE_LIMIT_BURST = int(os.environ.get("RATE_LIMIT_BURST", str(max(100, RATE_LIMIT_PER_MINUTE))))
RATE_LIMIT_KEY = os.environ.get("RATE_LIMIT_KEY", "ip").lower()  # "ip" or "api_key"

ENABLE_SECURITY_HEADERS = os.environ.get("ENABLE_SECURITY_HEADERS", "true").lower() in {"1", "true", "yes"}
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").strip()  # CSV list; empty disables CORS header


# -----------------------------
# Helpers
# -----------------------------

def _get_client_ip(flask_request: Request) -> str:
    # Honor X-Forwarded-For (Cloud Run behind LB/Proxy)
    xff = flask_request.headers.get("X-Forwarded-For", "")
    if xff:
        # First IP in the list is the original client
        return xff.split(",")[0].strip()
    return flask_request.remote_addr or "unknown"


def _get_rate_limit_key(flask_request: Request) -> str:
    if RATE_LIMIT_KEY == "api_key":
        api_key = flask_request.headers.get("X-API-Key", "")
        if api_key:
            return f"api_key:{api_key}"
    return f"ip:{_get_client_ip(flask_request)}"


# -----------------------------
# API Key Authentication
# -----------------------------

def require_api_key(func: Callable) -> Callable:
    """Simple API key decorator using the X-API-Key header.

    Reads expected key from the environment variable API_KEY to avoid importing
    config at module import time. This prevents startup failures if API_KEY is
    not yet set while this module is merely imported.
    """

    @wraps(func)
    def _wrapper(*args, **kwargs):
        expected = os.environ.get("API_KEY", "")
        provided = request.headers.get("X-API-Key", "")
        if not expected:
            return jsonify({"message": "Server misconfiguration: API_KEY not set"}), 500
        if provided != expected:
            return jsonify({"message": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return _wrapper


# -----------------------------
# Lightweight Rate Limiting
# -----------------------------

_rate_lock = threading.Lock()
_rate_buckets: Dict[str, Deque[float]] = {}


def rate_limit(max_per_minute: int | None = None, burst: int | None = None) -> Callable:
    """Sliding-window rate limit by IP or API key (configurable).

    - max_per_minute: allowed requests per 60s window (default from env)
    - burst: maximum queued timestamps kept to bound memory (default from env)
    """

    limit = max_per_minute or RATE_LIMIT_PER_MINUTE
    cap = burst or RATE_LIMIT_BURST

    def _decorator(func: Callable) -> Callable:
        @wraps(func)
        def _wrapped(*args, **kwargs):
            now = time.time()
            key = _get_rate_limit_key(request)

            with _rate_lock:
                bucket = _rate_buckets.get(key)
                if bucket is None:
                    bucket = deque()
                    _rate_buckets[key] = bucket

                # Drop entries older than 60s
                cutoff = now - 60.0
                while bucket and bucket[0] < cutoff:
                    bucket.popleft()

                if len(bucket) >= limit:
                    retry_after = max(1, int(bucket[0] - cutoff))
                    return (
                        jsonify({"message": "Too Many Requests"}),
                        429,
                        {"Retry-After": str(retry_after)},
                    )

                # Record the request
                bucket.append(now)
                # Bound memory
                while len(bucket) > cap:
                    bucket.popleft()

            return func(*args, **kwargs)

        return _wrapped

    return _decorator


# -----------------------------
# Security Headers / Basic CORS
# -----------------------------

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    # HSTS should only be set when served over HTTPS; Cloud Run uses HTTPS by default
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    # Keep CSP conservative by default; adjust if you serve static content
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def add_security_headers(response: Response) -> Response:
    if ENABLE_SECURITY_HEADERS:
        for k, v in _SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)

    if ALLOWED_ORIGINS:
        # Basic CORS allowlist
        origin = request.headers.get("Origin", "")
        allowed = {o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()}
        if origin and origin in allowed:
            response.headers.setdefault("Access-Control-Allow-Origin", origin)
            response.headers.setdefault("Vary", "Origin")
            response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
    return response


def register_security(app) -> None:
    """Attach after_request hook for headers/CORS."""

    @app.after_request
    def _after(resp: Response) -> Response:  # type: ignore[override]
        return add_security_headers(resp)


# -----------------------------
# Example usage (do not auto-execute)
# -----------------------------

# from flask import Flask
# app = Flask(__name__)
# register_security(app)
#
# @app.route("/secure")
# @rate_limit()            # default env: 100 rpm
# @require_api_key         # requires X-API-Key header matching env API_KEY
# def secure():
#     return {"ok": True}
