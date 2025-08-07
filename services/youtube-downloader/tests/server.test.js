const request = require('supertest');
const app = require('../server');

describe('YouTube Downloader Microservice', () => {
  describe('Health Check', () => {
    test('GET /healthz should return health status', async () => {
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
  });

  describe('Root Endpoint', () => {
    test('GET / should return service information', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.body).toMatchObject({
        service: 'YouTube Downloader Microservice',
        version: '1.0.0',
        endpoints: {
          '/healthz': 'Health check endpoint',
          '/v1/media/youtube/info': 'Get video information (POST)',
          '/v1/media/youtube/mp3': 'Download audio as MP3 (POST)',
          '/v1/media/youtube/mp4': 'Download video as MP4 (POST)'
        }
      });
    });
  });

  describe('URL Validation', () => {
    test('POST /v1/media/youtube/info with invalid URL should return 400', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: 'not-a-url' })
        .expect(400);

      expect(response.body).toMatchObject({
        error: 'Validation failed'
      });
      expect(response.body).toHaveProperty('details');
    });

    test('POST /v1/media/youtube/info with non-YouTube URL should return 400', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: 'https://www.google.com' })
        .expect(400);

      expect(response.body).toMatchObject({
        error: 'Validation failed'
      });
    });

    test('POST /v1/media/youtube/info without URL should return 400', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({})
        .expect(400);

      expect(response.body).toMatchObject({
        error: 'Validation failed'
      });
    });
  });

  describe('Video Info Endpoint', () => {
    test('POST /v1/media/youtube/info with valid URL should return video info', async () => {
      // Using a known YouTube video for testing
      const testUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
      
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: testUrl })
        .timeout(10000); // 10 second timeout for API calls

      if (response.status === 200) {
        expect(response.body).toMatchObject({
          success: true,
          data: {
            videoId: expect.any(String),
            title: expect.any(String),
            description: expect.any(String),
            lengthSeconds: expect.any(Number),
            author: {
              name: expect.any(String)
            }
          }
        });
        expect(response.body.data).toHaveProperty('thumbnails');
        expect(response.body.data).toHaveProperty('formats');
      } else {
        // If the request fails due to YouTube blocks, just check the error format
        expect(response.body).toHaveProperty('success', false);
        expect(response.body).toHaveProperty('error');
      }
    }, 15000);
  });

  describe('404 Handler', () => {
    test('GET /nonexistent should return 404 with available endpoints', async () => {
      const response = await request(app)
        .get('/nonexistent')
        .expect(404);

      expect(response.body).toMatchObject({
        success: false,
        error: 'Endpoint not found',
        availableEndpoints: {
          '/healthz': 'GET - Health check',
          '/v1/media/youtube/info': 'POST - Get video information',
          '/v1/media/youtube/mp3': 'POST - Download audio as MP3',
          '/v1/media/youtube/mp4': 'POST - Download video as MP4'
        }
      });
    });
  });

  describe('Security Headers', () => {
    test('Responses should include security headers', async () => {
      const response = await request(app)
        .get('/healthz');

      // Check for some security headers set by helmet
      expect(response.headers).toHaveProperty('x-content-type-options');
      expect(response.headers).toHaveProperty('x-frame-options');
    });
  });

  describe('Rate Limiting', () => {
    test('Should include rate limit headers', async () => {
      const response = await request(app)
        .get('/healthz');

      expect(response.headers).toHaveProperty('x-ratelimit-limit');
      expect(response.headers).toHaveProperty('x-ratelimit-remaining');
    });
  });
});
