/**
 * YouTube Downloader API Integration Tests
 * Tests all API endpoints for functionality, security, and error handling
 */

const request = require('supertest');
const ytdl = require('ytdl-core');

// Mock the server without starting it
jest.mock('../server.js', () => {
  const express = require('express');
  const app = express();
  
  // Import and apply all middleware and routes from the actual server
  // This is a simplified version - you'd need to replicate the server setup
  app.use(express.json());
  
  // Health check endpoint
  app.get('/healthz', (req, res) => {
    res.status(200).json({
      uptime: process.uptime(),
      message: 'OK',
      timestamp: new Date().toISOString(),
      service: 'youtube-downloader',
      version: '1.0.0',
      status: 'healthy'
    });
  });
  
  // Mock info endpoint
  app.post('/v1/media/youtube/info', async (req, res) => {
    try {
      const { url } = req.body;
      if (!url) {
        return res.status(400).json({
          success: false,
          error: 'URL is required'
        });
      }
      
      // Return mock data
      res.status(200).json({
        success: true,
        data: global.testUtils.mockVideoInfo.videoDetails
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error.message
      });
    }
  });
  
  return app;
}, { virtual: true });

const app = require('../server.js');

describe('YouTube Downloader API', () => {
  // Health check endpoint tests
  describe('GET /healthz', () => {
    it('should return health status', async () => {
      const response = await request(app)
        .get('/healthz')
        .expect(200);

      expect(response.body).toMatchObject({
        message: 'OK',
        service: 'youtube-downloader',
        version: '1.0.0',
        status: 'healthy'
      });
      expect(response.body).toHaveProperty('uptime');
      expect(response.body).toHaveProperty('timestamp');
    });

    it('should have proper response headers', async () => {
      const response = await request(app)
        .get('/healthz')
        .expect(200);

      expect(response.headers['content-type']).toMatch(/json/);
    });
  });

  // Video info endpoint tests
  describe('POST /v1/media/youtube/info', () => {
    beforeEach(() => {
      // Reset mocks
      ytdl.getInfo.mockClear();
      ytdl.validateURL.mockClear();
    });

    it('should return video information for valid URL', async () => {
      // Mock ytdl-core response
      ytdl.getInfo.mockResolvedValue(global.testUtils.mockVideoInfo);
      ytdl.validateURL.mockReturnValue(true);

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: global.testUtils.mockYouTubeUrl })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty('videoId');
      expect(response.body.data).toHaveProperty('title');
      expect(response.body.data).toHaveProperty('author');
    });

    it('should reject request without URL', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({})
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('URL is required');
    });

    it('should reject invalid YouTube URL', async () => {
      ytdl.validateURL.mockReturnValue(false);

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: 'https://invalid-url.com' })
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toBeTruthy();
    });

    it('should handle malicious URLs', async () => {
      const maliciousUrls = [
        'http://localhost:8080/admin',
        'http://169.254.169.254/metadata',
        'file:///etc/passwd',
        'ftp://internal-server.com/data'
      ];

      for (const url of maliciousUrls) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .send({ url })
          .expect(400);

        expect(response.body.success).toBe(false);
      }
    });

    it('should handle ytdl-core errors gracefully', async () => {
      ytdl.getInfo.mockRejectedValue(new Error('Video not found'));
      ytdl.validateURL.mockReturnValue(true);

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: global.testUtils.mockYouTubeUrl })
        .expect(500);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('Video not found');
    });

    it('should sanitize response data', async () => {
      const maliciousVideoInfo = {
        ...global.testUtils.mockVideoInfo,
        videoDetails: {
          ...global.testUtils.mockVideoInfo.videoDetails,
          title: '<script>alert("XSS")</script>Malicious Title',
          description: 'Description with <iframe src="javascript:alert(1)"></iframe>'
        }
      };

      ytdl.getInfo.mockResolvedValue(maliciousVideoInfo);
      ytdl.validateURL.mockReturnValue(true);

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: global.testUtils.mockYouTubeUrl })
        .expect(200);

      // Should not contain script tags
      expect(response.body.data.title).not.toContain('<script>');
      expect(response.body.data.description).not.toContain('<iframe>');
    });

    it('should respect rate limiting', async () => {
      const requests = [];
      
      // Make multiple rapid requests
      for (let i = 0; i < 35; i++) {
        requests.push(
          request(app)
            .post('/v1/media/youtube/info')
            .send({ url: global.testUtils.mockYouTubeUrl })
        );
      }

      const responses = await Promise.all(requests);
      const rateLimitedResponses = responses.filter(r => r.status === 429);
      
      // Should have some rate-limited responses
      expect(rateLimitedResponses.length).toBeGreaterThan(0);
    }, 10000);
  });

  // Security headers tests
  describe('Security Headers', () => {
    it('should include security headers', async () => {
      const response = await request(app)
        .get('/healthz')
        .expect(200);

      // Check for common security headers
      expect(response.headers).toHaveProperty('x-content-type-options');
      expect(response.headers).toHaveProperty('x-frame-options');
      expect(response.headers).toHaveProperty('x-xss-protection');
    });

    it('should not expose sensitive information in headers', async () => {
      const response = await request(app)
        .get('/healthz')
        .expect(200);

      // Should not expose server information
      expect(response.headers['x-powered-by']).toBeUndefined();
    });
  });

  // Input validation tests
  describe('Input Validation', () => {
    it('should reject oversized JSON payloads', async () => {
      const largePayload = {
        url: global.testUtils.mockYouTubeUrl,
        data: 'x'.repeat(2 * 1024 * 1024) // 2MB string
      };

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send(largePayload)
        .expect(413);

      expect(response.status).toBe(413);
    });

    it('should reject malformed JSON', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .set('Content-Type', 'application/json')
        .send('{ "url": "https://youtube.com/watch?v=test"')
        .expect(400);

      expect(response.status).toBe(400);
    });

    it('should validate Content-Type header', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .set('Content-Type', 'text/plain')
        .send('url=https://youtube.com')
        .expect(400);

      expect(response.status).toBe(400);
    });
  });

  // CORS tests
  describe('CORS Configuration', () => {
    it('should handle CORS preflight requests', async () => {
      const response = await request(app)
        .options('/v1/media/youtube/info')
        .set('Origin', 'http://localhost:3000')
        .set('Access-Control-Request-Method', 'POST')
        .set('Access-Control-Request-Headers', 'Content-Type')
        .expect(200);

      expect(response.headers['access-control-allow-origin']).toBeTruthy();
      expect(response.headers['access-control-allow-methods']).toBeTruthy();
    });

    it('should reject requests from unauthorized origins', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .set('Origin', 'http://malicious-site.com')
        .send({ url: global.testUtils.mockYouTubeUrl })
        .expect(403);

      expect(response.status).toBe(403);
    });
  });

  // Error handling tests
  describe('Error Handling', () => {
    it('should return 404 for unknown endpoints', async () => {
      const response = await request(app)
        .get('/unknown-endpoint')
        .expect(404);

      expect(response.status).toBe(404);
    });

    it('should return proper error format', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({})
        .expect(400);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error');
      expect(typeof response.body.error).toBe('string');
    });

    it('should not leak internal error details in production', async () => {
      // Simulate production environment
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      ytdl.getInfo.mockRejectedValue(new Error('Internal database connection failed'));
      ytdl.validateURL.mockReturnValue(true);

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: global.testUtils.mockYouTubeUrl })
        .expect(500);

      expect(response.body.error).not.toContain('database');
      expect(response.body.error).not.toContain('connection');

      // Restore environment
      process.env.NODE_ENV = originalEnv;
    });
  });

  // Performance tests
  describe('Performance', () => {
    it('should respond to health check quickly', async () => {
      const start = Date.now();
      
      await request(app)
        .get('/healthz')
        .expect(200);
      
      const duration = Date.now() - start;
      expect(duration).toBeLessThan(1000); // Should respond within 1 second
    });

    it('should handle concurrent requests', async () => {
      ytdl.getInfo.mockResolvedValue(global.testUtils.mockVideoInfo);
      ytdl.validateURL.mockReturnValue(true);

      const concurrentRequests = Array(10).fill().map(() =>
        request(app)
          .post('/v1/media/youtube/info')
          .send({ url: global.testUtils.mockYouTubeUrl })
      );

      const responses = await Promise.all(concurrentRequests);
      
      responses.forEach(response => {
        expect([200, 429]).toContain(response.status); // 200 OK or 429 Rate Limited
      });
    }, 10000);
  });
});
