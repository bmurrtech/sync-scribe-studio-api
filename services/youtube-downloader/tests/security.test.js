const request = require('supertest');
const app = require('../server');

describe('Security Features', () => {
  describe('Rate Limiting', () => {
    it('should allow reasonable number of health check requests', async () => {
      for (let i = 0; i < 5; i++) {
        const response = await request(app)
          .get('/healthz');
        
        expect(response.status).toBe(200);
      }
    });

    it('should reject requests exceeding rate limit for info endpoint', async () => {
      const validPayload = {
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
      };

      // Make multiple requests quickly
      const promises = [];
      for (let i = 0; i < 35; i++) { // Exceeds 30 req/min limit
        promises.push(
          request(app)
            .post('/v1/media/youtube/info')
            .send(validPayload)
        );
      }

      const responses = await Promise.all(promises);
      const rateLimitedResponses = responses.filter(res => res.status === 429);
      
      expect(rateLimitedResponses.length).toBeGreaterThan(0);
      expect(rateLimitedResponses[0].body.error).toContain('rate limit');
    }, 10000);
  });

  describe('Input Validation', () => {
    it('should reject invalid YouTube URLs', async () => {
      const invalidUrls = [
        'https://example.com/watch?v=invalid',
        'https://notayoutubesite.com/video',
        'javascript:alert("xss")',
        'data:text/html,<script>alert("xss")</script>',
        'http://192.168.1.1/internal',
        'http://localhost:8080/private'
      ];

      for (const url of invalidUrls) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .send({ url });

        expect(response.status).toBe(400);
        expect(response.body.success).toBe(false);
        expect(response.body.error).toBe('Validation failed');
      }
    });

    it('should accept valid YouTube URLs', async () => {
      const validUrls = [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://youtu.be/dQw4w9WgXcQ',
        'https://m.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://music.youtube.com/watch?v=dQw4w9WgXcQ'
      ];

      for (const url of validUrls) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .send({ url });

        // Should pass validation (might fail at ytdl level, but that's expected in tests)
        expect([200, 500]).toContain(response.status);
        if (response.status === 400) {
          expect(response.body.error).not.toBe('Validation failed');
        }
      }
    });
  });

  describe('SSRF Protection', () => {
    it('should block private IP addresses', async () => {
      const dangerousUrls = [
        'https://192.168.1.1/youtube.com',
        'http://10.0.0.1/malicious',
        'https://172.16.0.1/internal',
        'http://127.0.0.1:8080/admin'
      ];

      for (const url of dangerousUrls) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .send({ url });

        expect(response.status).toBe(403);
        expect(response.body.error).toBe('Forbidden');
        expect(response.body.message).toContain('private networks');
      }
    });

    it('should block localhost access', async () => {
      const localhostUrls = [
        'http://localhost/admin',
        'https://localhost:3000/internal'
      ];

      for (const url of localhostUrls) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .send({ url });

        expect(response.status).toBe(403);
        expect(response.body.error).toBe('Forbidden');
      }
    });

    it('should block non-standard ports', async () => {
      const nonStandardPorts = [
        'https://youtube.com:8080/watch?v=test',
        'https://youtube.com:3000/video'
      ];

      for (const url of nonStandardPorts) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .send({ url });

        expect(response.status).toBe(403);
        expect(response.body.error).toBe('Forbidden');
        expect(response.body.message).toContain('non-standard ports');
      }
    });
  });

  describe('Input Sanitization', () => {
    it('should sanitize XSS attempts in request body', async () => {
      const maliciousPayload = {
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'evil<script>alert("xss")</script>': 'value',
        nested: {
          'malicious<iframe>evil</iframe>': 'content'
        }
      };

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send(maliciousPayload);

      // Should not contain script or iframe tags in any response
      const responseString = JSON.stringify(response.body);
      expect(responseString).not.toContain('<script>');
      expect(responseString).not.toContain('<iframe>');
      expect(responseString).not.toContain('javascript:');
    });
  });

  describe('Content Security', () => {
    it('should set security headers', async () => {
      const response = await request(app).get('/');

      expect(response.headers['x-content-type-options']).toBe('nosniff');
      expect(response.headers['x-frame-options']).toBe('DENY');
      expect(response.headers['x-xss-protection']).toBeDefined();
      expect(response.headers['strict-transport-security']).toBeDefined();
      expect(response.headers['content-security-policy']).toBeDefined();
    });

    it('should reject oversized payloads', async () => {
      const largePayload = {
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        data: 'x'.repeat(2 * 1024 * 1024) // 2MB of data
      };

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send(largePayload);

      expect(response.status).toBe(413);
      expect(response.body.error).toBe('Payload too large');
    });
  });

  describe('Quality Parameter Validation', () => {
    it('should accept valid audio quality parameters', async () => {
      const validQualities = ['highestaudio', 'lowestaudio', 'highest', 'lowest'];
      
      for (const quality of validQualities) {
        const response = await request(app)
          .post('/v1/media/youtube/mp3')
          .send({
            url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            quality: quality
          });

        // Should pass validation
        expect(response.status).not.toBe(400);
      }
    });

    it('should reject invalid audio quality parameters', async () => {
      const invalidQualities = ['invalid', '1080p', 'best', 'ultra'];
      
      for (const quality of invalidQualities) {
        const response = await request(app)
          .post('/v1/media/youtube/mp3')
          .send({
            url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            quality: quality
          });

        expect(response.status).toBe(400);
        expect(response.body.error).toBe('Validation failed');
      }
    });

    it('should accept valid video quality parameters', async () => {
      const validQualities = ['highest', 'lowest', '720p', '1080p'];
      
      for (const quality of validQualities) {
        const response = await request(app)
          .post('/v1/media/youtube/mp4')
          .send({
            url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            quality: quality
          });

        // Should pass validation
        expect(response.status).not.toBe(400);
      }
    });
  });

  describe('Header Validation', () => {
    it('should validate User-Agent header', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .set('User-Agent', '<script>alert("xss")</script>')
        .send({
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Invalid headers');
    });

    it('should accept valid User-Agent headers', async () => {
      const validUserAgents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'PostmanRuntime/7.26.8',
        'curl/7.68.0'
      ];

      for (const userAgent of validUserAgents) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .set('User-Agent', userAgent)
          .send({
            url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
          });

        expect(response.status).not.toBe(400);
      }
    });
  });

  describe('Error Handling', () => {
    it('should not expose sensitive information in error messages', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({
          url: 'https://www.youtube.com/watch?v=invalid_video_id'
        });

      // Should not contain sensitive server paths or internal details
      const responseString = JSON.stringify(response.body);
      expect(responseString).not.toMatch(/\/Users\//);
      expect(responseString).not.toMatch(/\/home\//);
      expect(responseString).not.toMatch(/node_modules/);
      expect(responseString).not.toContain('stack trace');
      expect(responseString).not.toContain('at Object.');
    });

    it('should handle malformed JSON gracefully', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .set('Content-Type', 'application/json')
        .send('{"invalid": json}');

      expect(response.status).toBe(400);
      expect(response.body).toBeDefined();
    });
  });

  describe('Response Security', () => {
    it('should not include sensitive data in video info response', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        });

      if (response.status === 200) {
        const responseString = JSON.stringify(response.body);
        
        // Should not contain sensitive internal data
        expect(responseString).not.toContain('password');
        expect(responseString).not.toContain('token');
        expect(responseString).not.toContain('secret');
        expect(responseString).not.toContain('api_key');
        
        // Should limit data exposure
        if (response.body.data && response.body.data.description) {
          expect(response.body.data.description.length).toBeLessThanOrEqual(500);
        }
        
        if (response.body.data && response.body.data.formats) {
          expect(response.body.data.formats.audioFormats.length).toBeLessThanOrEqual(10);
          expect(response.body.data.formats.videoFormats.length).toBeLessThanOrEqual(10);
        }
      }
    });

    it('should sanitize filenames in download responses', async () => {
      // This would need to be tested with a real video that has special characters
      // For now, we'll test the sanitization function directly
      const { sanitizeFilename } = require('../utils/validation');
      
      const unsafeFilenames = [
        'Video<script>alert("xss")</script>',
        'Video/with\\slashes',
        'Video:with*special?chars',
        'Video|with>illegal<chars'
      ];

      for (const filename of unsafeFilenames) {
        const sanitized = sanitizeFilename(filename);
        expect(sanitized).not.toContain('<');
        expect(sanitized).not.toContain('>');
        expect(sanitized).not.toContain('/');
        expect(sanitized).not.toContain('\\');
        expect(sanitized).not.toContain('*');
        expect(sanitized).not.toContain('?');
        expect(sanitized).not.toContain('|');
        expect(sanitized).not.toContain(':');
      }
    });
  });
});
