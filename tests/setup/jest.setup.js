/**
 * Jest Setup for Integration Tests
 * Global configuration and utilities for comprehensive API testing
 */

// Set test environment
process.env.NODE_ENV = 'test';
process.env.PORT = 3001;
process.env.LOG_LEVEL = 'error';
process.env.ALLOWED_ORIGINS = 'http://localhost:3000';

// Extend Jest timeout for integration tests
jest.setTimeout(60000);

// Global error handling
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

// Global test utilities
global.testConfig = {
  RICK_ROLL_URL: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  RICK_ROLL_VIDEO_ID: 'dQw4w9WgXcQ',
  SERVICE_PORT: 3001,
  SERVICE_URL: 'http://localhost:3001',
  TEST_TIMEOUT: 60000,
  
  // Security test URLs
  MALICIOUS_URLS: [
    'http://localhost:22/secret',
    'http://169.254.169.254/metadata',
    'file:///etc/passwd',
    'ftp://internal-server.com/data',
    'https://malicious-site.com/redirect'
  ],
  
  NON_YOUTUBE_URLS: [
    'https://vimeo.com/12345',
    'https://example.com/video',
    'https://google.com'
  ]
};

// Utility functions
global.testUtils = {
  // Wait helper
  wait: (ms = 1000) => new Promise(resolve => setTimeout(resolve, ms)),
  
  // Generate large payload for testing
  generateLargePayload: (sizeInMB = 2) => ({
    url: global.testConfig.RICK_ROLL_URL,
    data: 'x'.repeat(sizeInMB * 1024 * 1024)
  }),
  
  // Verify response format
  verifyErrorResponse: (response) => {
    expect(response.body).toHaveProperty('success', false);
    expect(response.body).toHaveProperty('error');
    expect(response.body).toHaveProperty('message');
    expect(response.body).toHaveProperty('timestamp');
    expect(typeof response.body.error).toBe('string');
    expect(typeof response.body.message).toBe('string');
    expect(typeof response.body.timestamp).toBe('string');
  },
  
  // Verify success response format
  verifySuccessResponse: (response) => {
    expect(response.body).toHaveProperty('success', true);
    expect(response.body).toHaveProperty('data');
    expect(response.body).toHaveProperty('timestamp');
    expect(typeof response.body.timestamp).toBe('string');
  },
  
  // Verify security headers
  verifySecurityHeaders: (response) => {
    expect(response.headers).toHaveProperty('x-content-type-options');
    expect(response.headers['x-powered-by']).toBeUndefined();
  },
  
  // Check if response is rate limited
  isRateLimited: (response) => response.status === 429,
  
  // Generate concurrent requests
  generateConcurrentRequests: (requestFn, count = 5) => {
    const requests = [];
    for (let i = 0; i < count; i++) {
      requests.push(requestFn());
    }
    return requests;
  },
  
  // Memory usage helper
  getMemoryUsage: () => {
    const usage = process.memoryUsage();
    return {
      heapUsed: usage.heapUsed,
      heapTotal: usage.heapTotal,
      external: usage.external,
      rss: usage.rss
    };
  },
  
  // Format bytes for readable output
  formatBytes: (bytes) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }
};

// Clean up after each test
afterEach(() => {
  // Force garbage collection if available (run node with --expose-gc)
  if (global.gc) {
    global.gc();
  }
});

// Global cleanup
afterAll(async () => {
  // Allow time for any pending async operations to complete
  await global.testUtils.wait(2000);
});

// Console override to reduce noise during testing
if (!process.env.DEBUG_TESTS) {
  const originalConsole = global.console;
  global.console = {
    ...originalConsole,
    log: () => {}, // Suppress console.log during tests
    info: () => {}, // Suppress console.info during tests
    warn: originalConsole.warn, // Keep warnings
    error: originalConsole.error // Keep errors
  };
}
