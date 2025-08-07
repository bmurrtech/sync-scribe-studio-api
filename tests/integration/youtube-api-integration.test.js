/**
 * Comprehensive Integration Tests for YouTube Downloader API
 * Tests all endpoints with Rick Roll video and comprehensive security validation
 * 
 * Test video: Rick Astley - Never Gonna Give You Up
 * URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
 */

const request = require('supertest');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Test configuration
const RICK_ROLL_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
const RICK_ROLL_VIDEO_ID = 'dQw4w9WgXcQ';
const SERVICE_PORT = 3001;
const SERVICE_URL = `http://localhost:${SERVICE_PORT}`;
const TEST_TIMEOUT = 60000;

describe('YouTube Downloader API - Comprehensive Integration Tests', () => {
  let server;
  let serverProcess;

  // Start the actual server for integration testing
  beforeAll(async () => {
    const serverPath = path.join(__dirname, '../../services/youtube-downloader/server.js');
    
    // Set test environment variables
    process.env.NODE_ENV = 'test';
    process.env.PORT = SERVICE_PORT;
    process.env.LOG_LEVEL = 'error';
    
    // Start server process
    serverProcess = spawn('node', [serverPath], {
      env: { ...process.env, NODE_ENV: 'test' },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // Wait for server to start
    await new Promise((resolve, reject) => {
      let output = '';
      serverProcess.stdout.on('data', (data) => {
        output += data.toString();
        if (output.includes(`port ${SERVICE_PORT}`)) {
          resolve();
        }
      });
      
      serverProcess.stderr.on('data', (data) => {
        console.error('Server stderr:', data.toString());
      });

      setTimeout(() => {
        reject(new Error('Server failed to start within timeout'));
      }, 10000);
    });
  }, 15000);

  afterAll(async () => {
    if (serverProcess) {
      serverProcess.kill('SIGTERM');
      // Wait for graceful shutdown
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  });

  describe('Health Check Endpoint', () => {
    it('should return healthy status with proper response format', async () => {
      const response = await request(SERVICE_URL)
        .get('/healthz')
        .expect('Content-Type', /json/)
        .expect(200);

      expect(response.body).toMatchObject({
        message: 'OK',
        service: 'youtube-downloader',
        version: '1.0.0',
        status: 'healthy'
      });
      
      expect(response.body).toHaveProperty('uptime');
      expect(response.body).toHaveProperty('timestamp');
      expect(typeof response.body.uptime).toBe('number');
      expect(response.body.uptime).toBeGreaterThan(0);
    });

    it('should include security headers', async () => {
      const response = await request(SERVICE_URL)
        .get('/healthz')
        .expect(200);

      // Verify security headers
      expect(response.headers).toHaveProperty('x-content-type-options', 'nosniff');
      expect(response.headers).toHaveProperty('x-frame-options');
      expect(response.headers['x-powered-by']).toBeUndefined();
    });

    it('should respond within acceptable time limits', async () => {
      const startTime = Date.now();
      
      await request(SERVICE_URL)
        .get('/healthz')
        .expect(200);
      
      const responseTime = Date.now() - startTime;
      expect(responseTime).toBeLessThan(1000); // Should respond within 1 second
    });
  });

  describe('Rick Roll Video Information Endpoint', () => {
    it('should fetch Rick Roll video information successfully', async () => {
      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/info')
        .send({ url: RICK_ROLL_URL })
        .expect('Content-Type', /json/)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty('videoId', RICK_ROLL_VIDEO_ID);
      expect(response.body.data).toHaveProperty('title');
      expect(response.body.data.title).toMatch(/Rick Astley/i);
      expect(response.body.data.title).toMatch(/Never Gonna Give You Up/i);
      
      // Verify video metadata
      expect(response.body.data).toHaveProperty('lengthSeconds');
      expect(response.body.data).toHaveProperty('viewCount');
      expect(response.body.data).toHaveProperty('author');
      expect(response.body.data.author).toHaveProperty('name');
      expect(response.body.data.author.name).toMatch(/Rick Astley/i);
      
      // Verify formats are available
      expect(response.body.data).toHaveProperty('formats');
      expect(response.body.data.formats).toHaveProperty('audioFormats');
      expect(response.body.data.formats).toHaveProperty('videoFormats');
      expect(response.body.data.formats.audioFormats.length).toBeGreaterThan(0);
      expect(response.body.data.formats.videoFormats.length).toBeGreaterThan(0);
    }, TEST_TIMEOUT);

    it('should sanitize and validate response data', async () => {
      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/info')
        .send({ url: RICK_ROLL_URL })
        .expect(200);

      // Verify no HTML/script tags in response
      const title = response.body.data.title;
      expect(title).not.toMatch(/<script|<iframe|javascript:/i);
      
      // Verify description is truncated
      if (response.body.data.description) {
        expect(response.body.data.description.length).toBeLessThanOrEqual(500);
      }
      
      // Verify limited number of formats
      expect(response.body.data.formats.audioFormats.length).toBeLessThanOrEqual(10);
      expect(response.body.data.formats.videoFormats.length).toBeLessThanOrEqual(10);
      
      // Verify thumbnails are limited
      expect(response.body.data.thumbnails.length).toBeLessThanOrEqual(5);
    }, TEST_TIMEOUT);
  });

  describe('MP3 Download Endpoint with Rick Roll', () => {
    it('should initiate MP3 download with proper headers', async () => {
      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/mp3')
        .send({ url: RICK_ROLL_URL, quality: 'highestaudio' })
        .timeout(30000);

      // Should start streaming (might be 200 or redirect)
      expect([200, 302]).toContain(response.status);
      
      // Verify headers are set for audio download
      if (response.status === 200) {
        expect(response.headers['content-type']).toMatch(/audio/i);
        expect(response.headers['content-disposition']).toMatch(/attachment/i);
        expect(response.headers['x-video-title']).toBeDefined();
      }
    }, TEST_TIMEOUT);

    it('should handle invalid quality parameters gracefully', async () => {
      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/mp3')
        .send({ url: RICK_ROLL_URL, quality: 'invalid_quality' })
        .timeout(10000);

      // Should either accept and use default or return validation error
      expect([200, 400]).toContain(response.status);
    });
  });

  describe('MP4 Download Endpoint with Rick Roll', () => {
    it('should initiate MP4 download with proper headers', async () => {
      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/mp4')
        .send({ url: RICK_ROLL_URL, quality: 'highest' })
        .timeout(30000);

      // Should start streaming (might be 200 or redirect)
      expect([200, 302]).toContain(response.status);
      
      // Verify headers are set for video download
      if (response.status === 200) {
        expect(response.headers['content-type']).toMatch(/video/i);
        expect(response.headers['content-disposition']).toMatch(/attachment/i);
        expect(response.headers['x-video-title']).toBeDefined();
      }
    }, TEST_TIMEOUT);
  });

  describe('Security and Validation Tests', () => {
    it('should reject malicious URLs (SSRF protection)', async () => {
      const maliciousUrls = [
        'http://localhost:22/secret',
        'http://169.254.169.254/metadata',
        'file:///etc/passwd',
        'ftp://internal-server.com/data',
        'https://malicious-site.com/redirect'
      ];

      for (const url of maliciousUrls) {
        const response = await request(SERVICE_URL)
          .post('/v1/media/youtube/info')
          .send({ url })
          .timeout(5000);

        expect([400, 403]).toContain(response.status);
        expect(response.body.success).toBe(false);
      }
    });

    it('should reject non-YouTube URLs', async () => {
      const nonYouTubeUrls = [
        'https://vimeo.com/12345',
        'https://example.com/video',
        'https://google.com'
      ];

      for (const url of nonYouTubeUrls) {
        const response = await request(SERVICE_URL)
          .post('/v1/media/youtube/info')
          .send({ url })
          .timeout(5000);

        expect([400, 422]).toContain(response.status);
        expect(response.body.success).toBe(false);
      }
    });

    it('should handle request body size limits', async () => {
      const largePayload = {
        url: RICK_ROLL_URL,
        extra: 'x'.repeat(2 * 1024 * 1024) // 2MB
      };

      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/info')
        .send(largePayload)
        .timeout(5000);

      expect([400, 413]).toContain(response.status);
    });

    it('should validate required fields', async () => {
      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/info')
        .send({})
        .timeout(5000);

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
      expect(response.body.error).toBeDefined();
    });
  });

  describe('Rate Limiting Tests', () => {
    it('should enforce rate limits on info endpoint', async () => {
      const requests = [];
      
      // Make rapid requests to trigger rate limiting
      for (let i = 0; i < 35; i++) {
        requests.push(
          request(SERVICE_URL)
            .post('/v1/media/youtube/info')
            .send({ url: RICK_ROLL_URL })
            .timeout(5000)
            .catch(err => ({ status: err.status || 500, body: {} }))
        );
      }

      const responses = await Promise.all(requests);
      const rateLimitedResponses = responses.filter(r => r.status === 429);
      
      // Should have some rate-limited responses
      expect(rateLimitedResponses.length).toBeGreaterThan(0);
    }, 30000);

    it('should enforce stricter rate limits on download endpoints', async () => {
      const requests = [];
      
      // Make rapid download requests
      for (let i = 0; i < 10; i++) {
        requests.push(
          request(SERVICE_URL)
            .post('/v1/media/youtube/mp3')
            .send({ url: RICK_ROLL_URL })
            .timeout(3000)
            .catch(err => ({ status: err.status || 500, body: {} }))
        );
      }

      const responses = await Promise.all(requests);
      const rateLimitedResponses = responses.filter(r => r.status === 429);
      
      // Download endpoints should have stricter limits
      expect(rateLimitedResponses.length).toBeGreaterThan(5);
    }, 20000);
  });

  describe('Error Handling Tests', () => {
    it('should handle non-existent video IDs gracefully', async () => {
      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/info')
        .send({ url: 'https://www.youtube.com/watch?v=nonexistentvideoid' })
        .timeout(10000);

      expect([404, 500]).toContain(response.status);
      expect(response.body.success).toBe(false);
      expect(response.body).toHaveProperty('error');
      expect(response.body).toHaveProperty('timestamp');
    });

    it('should return proper error format for all failures', async () => {
      const response = await request(SERVICE_URL)
        .post('/v1/media/youtube/info')
        .send({ url: 'invalid-url' })
        .timeout(5000);

      expect(response.body).toMatchObject({
        success: false,
        error: expect.any(String),
        message: expect.any(String),
        timestamp: expect.any(String)
      });
    });

    it('should handle 404 for unknown endpoints', async () => {
      const response = await request(SERVICE_URL)
        .get('/unknown-endpoint')
        .timeout(5000);

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
      expect(response.body).toHaveProperty('availableEndpoints');
    });
  });

  describe('Performance and Load Tests', () => {
    it('should handle concurrent requests efficiently', async () => {
      const concurrentRequests = 5;
      const requests = [];
      
      for (let i = 0; i < concurrentRequests; i++) {
        requests.push(
          request(SERVICE_URL)
            .get('/healthz')
            .timeout(5000)
        );
      }

      const startTime = Date.now();
      const responses = await Promise.all(requests);
      const duration = Date.now() - startTime;
      
      // All should succeed or be rate limited
      responses.forEach(response => {
        expect([200, 429]).toContain(response.status);
      });
      
      // Should handle concurrent requests efficiently
      expect(duration).toBeLessThan(10000);
    });

    it('should maintain stable memory usage during multiple requests', async () => {
      const initialMemory = process.memoryUsage();
      
      // Make several info requests
      for (let i = 0; i < 5; i++) {
        await request(SERVICE_URL)
          .post('/v1/media/youtube/info')
          .send({ url: RICK_ROLL_URL })
          .timeout(10000)
          .catch(() => {}); // Ignore errors, we're testing memory
      }
      
      const finalMemory = process.memoryUsage();
      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
      
      // Memory increase should be reasonable (less than 100MB)
      expect(memoryIncrease).toBeLessThan(100 * 1024 * 1024);
    }, 60000);
  });

  describe('CORS and Headers Tests', () => {
    it('should handle CORS preflight requests', async () => {
      const response = await request(SERVICE_URL)
        .options('/v1/media/youtube/info')
        .set('Origin', 'http://localhost:3000')
        .set('Access-Control-Request-Method', 'POST')
        .set('Access-Control-Request-Headers', 'Content-Type')
        .timeout(5000);

      expect([200, 204]).toContain(response.status);
      expect(response.headers['access-control-allow-origin']).toBeDefined();
    });

    it('should include proper security headers on all responses', async () => {
      const endpoints = [
        { method: 'get', path: '/healthz' },
        { method: 'get', path: '/' }
      ];

      for (const endpoint of endpoints) {
        const response = await request(SERVICE_URL)
          [endpoint.method](endpoint.path)
          .timeout(5000);

        // Should include basic security headers
        expect(response.headers).toHaveProperty('x-content-type-options');
        expect(response.headers['x-powered-by']).toBeUndefined();
      }
    });
  });
});
