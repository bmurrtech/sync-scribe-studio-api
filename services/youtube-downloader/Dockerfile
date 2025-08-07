# YouTube Downloader Microservice Dockerfile
# Multi-stage build for production optimization and security

# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git \
    && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./

# Install only production dependencies
RUN npm ci --omit=dev && npm cache clean --force

# Copy source code
COPY . .

# Production stage
FROM node:18-alpine AS production

# Create app user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S appuser -u 1001 -G nodejs

# Install runtime dependencies and security updates
RUN apk add --no-cache \
    dumb-init \
    tini \
    wget \
    ffmpeg \
    && apk upgrade \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy built application from builder stage
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package*.json ./
COPY --chown=appuser:nodejs . .

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:nodejs /app/logs && \
    chmod 755 /app/logs

# Environment variables with defaults
ENV NODE_ENV=production \
    PORT=3001 \
    YTDL_NETWORK_TIMEOUT=30000 \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_UPDATE_NOTIFIER=false

# Health check with wget instead of curl for alpine
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT}/healthz || exit 1

# Security: Run as non-root user
USER appuser

# Expose port (for internal networking only)
EXPOSE 3001

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Run the start script
CMD ["./start.sh"]
