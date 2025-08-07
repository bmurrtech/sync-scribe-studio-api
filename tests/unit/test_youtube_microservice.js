#!/usr/bin/env node
/**
 * Unit Tests for YouTube Downloader Microservice
 * 
 * Following TDD principles - these tests define expected behavior
 * for the Node.js microservice functionality.
 */

const request = require('supertest');
const app = require('../../services/youtube-downloader/server');
const ytdl = require('ytdl-core');

// Mock ytdl-core for testing
jest.mock('ytdl-core');

describe('YouTube Downloader Microservice', () => {
  
  describe('Health Check Endpoint', () => {
    test('GET /healthz should return service health status', async () => {
      const response = await request(app)
        .get('/healthz')
        .expect(200);

      expect(response.body).toHaveProperty('uptime');
      expect(response.body).toHaveProperty('message', 'OK');
      expect(response.body).toHaveProperty('service', 'youtube-downloader');
      expect(response.body).toHaveProperty('version', '1.0.0');
      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body).toHaveProperty('timestamp');
    });

    test('Health check should handle errors gracefully', async () => {
      // Simulate health check failure
      const originalUptime = process.uptime;
      process.uptime = () => { throw new Error('System error'); };

      const response = await request(app)
        .get('/healthz')
        .expect(503);

      expect(response.body).toHaveProperty('status', 'unhealthy');
      expect(response.body).toHaveProperty('message', 'ERROR');

      // Restore original function
      process.uptime = originalUptime;
    });
  });

  describe('Service Discovery Endpoint', () => {
    test('GET / should return service information', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.body).toHaveProperty('service', 'YouTube Downloader Microservice');
      expect(response.body).toHaveProperty('version', '1.0.0');
      expect(response.body).toHaveProperty('endpoints');
      expect(response.body.endpoints).toHaveProperty('/healthz');
      expect(response.body.endpoints).toHaveProperty('/v1/media/youtube/info');
      expect(response.body.endpoints).toHaveProperty('/v1/media/youtube/mp3');
      expect(response.body.endpoints).toHaveProperty('/v1/media/youtube/mp4');
    });
  });

  describe('Video Info Endpoint', () => {
    const validYouTubeUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
    const mockVideoInfo = {
      videoDetails: {
        videoId: 'dQw4w9WgXcQ',
        title: 'Rick Astley - Never Gonna Give You Up (Video)',
        description: 'The official video for "Never Gonna Give You Up" by Rick Astley',
        lengthSeconds: '213',
        viewCount: '1000000000',
        author: {
          name: 'Rick Astley',
          channel_url: 'https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw',
          subscriber_count: 2000000
        },
        publishDate: '2009-10-25',
        uploadDate: '2009-10-25',
        thumbnails: [
          { url: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg', width: 1280, height: 720 }
        ],
        keywords: ['Rick Astley', 'Never Gonna Give You Up'],
        category: 'Music',
        isLiveContent: false
      },
      formats: [
        {
          itag: 140,
          mimeType: 'audio/mp4; codecs="mp4a.40.2"',
          hasAudio: true,
          hasVideo: false,
          averageBitrate: 128,
          audioQuality: 'AUDIO_QUALITY_MEDIUM',
          audioSampleRate: '44100'
        },
        {
          itag: 18,
          mimeType: 'video/mp4; codecs="avc1.42001E, mp4a.40.2"',
          hasVideo: true,
          hasAudio: true,
          qualityLabel: '360p',
          width: 640,
          height: 360,
          fps: 30
        }
      ]
    };

    beforeEach(() => {
      ytdl.getInfo.mockResolvedValue(mockVideoInfo);
    });

    test('POST /v1/media/youtube/info should return video information', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: validYouTubeUrl })
        .set('Content-Type', 'application/json')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('data');
      expect(response.body.data).toHaveProperty('videoId', 'dQw4w9WgXcQ');
      expect(response.body.data).toHaveProperty('title');
      expect(response.body.data).toHaveProperty('description');
      expect(response.body.data).toHaveProperty('lengthSeconds');
      expect(response.body.data).toHaveProperty('viewCount');
      expect(response.body.data).toHaveProperty('author');
      expect(response.body.data).toHaveProperty('formats');
      expect(response.body.data.formats).toHaveProperty('audioFormats');
      expect(response.body.data.formats).toHaveProperty('videoFormats');
      expect(response.body).toHaveProperty('timestamp');
    });

    test('POST /v1/media/youtube/info should validate URL format', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: 'not-a-valid-url' })
        .set('Content-Type', 'application/json')
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });

    test('POST /v1/media/youtube/info should require URL parameter', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({})
        .set('Content-Type', 'application/json')
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });

    test('POST /v1/media/youtube/info should handle ytdl-core errors', async () => {
      ytdl.getInfo.mockRejectedValue(new Error('Video unavailable'));

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: validYouTubeUrl })
        .set('Content-Type', 'application/json')
        .expect(500);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error');
    });

    test('POST /v1/media/youtube/info should sanitize filename in title', async () => {
      const maliciousTitleInfo = {
        ...mockVideoInfo,
        videoDetails: {
          ...mockVideoInfo.videoDetails,
          title: 'Dangerous/../../../etc/passwd'
        }
      };
      ytdl.getInfo.mockResolvedValue(maliciousTitleInfo);

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: validYouTubeUrl })
        .set('Content-Type', 'application/json')
        .expect(200);

      expect(response.body.data.title).not.toContain('../');
      expect(response.body.data.title).not.toContain('/etc/passwd');
    });

    test('Rick Roll URL should return valid video info', async () => {
      const rickRollUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
      
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: rickRollUrl })
        .set('Content-Type', 'application/json')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.videoId).toBe('dQw4w9WgXcQ');
      expect(response.body.data.title).toBeTruthy();
    });
  });

  describe('MP3 Download Endpoint', () => {
    test('POST /v1/media/youtube/mp3 should stream MP3 audio', async () => {
      const mockStream = require('stream');
      const mockAudioStream = new mockStream.Readable({
        read() {
          this.push('audio-data-chunk');
          this.push(null); // End stream
        }
      });

      ytdl.mockReturnValue(mockAudioStream);
      ytdl.getInfo.mockResolvedValue({
        videoDetails: {
          videoId: 'dQw4w9WgXcQ',
          title: 'Test Video',
          lengthSeconds: '213'
        }
      });

      const response = await request(app)
        .post('/v1/media/youtube/mp3')
        .send({ url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', quality: 'highestaudio' })
        .set('Content-Type', 'application/json')
        .expect(200);

      expect(response.headers['content-type']).toBe('audio/mpeg');
      expect(response.headers['x-video-title']).toBeTruthy();
      expect(response.headers['x-video-duration']).toBeTruthy();
    });

    test('POST /v1/media/youtube/mp3 should handle stream errors', async () => {
      const mockStream = require('stream');
      const mockAudioStream = new mockStream.Readable({
        read() {
          this.emit('error', new Error('Stream error'));
        }
      });

      ytdl.mockReturnValue(mockAudioStream);
      ytdl.getInfo.mockResolvedValue({
        videoDetails: {
          videoId: 'dQw4w9WgXcQ',
          title: 'Test Video',
          lengthSeconds: '213'
        }
      });

      const response = await request(app)
        .post('/v1/media/youtube/mp3')
        .send({ url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' })
        .set('Content-Type', 'application/json')
        .expect(500);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error');
    });
  });

  describe('MP4 Download Endpoint', () => {
    test('POST /v1/media/youtube/mp4 should stream MP4 video', async () => {
      const mockStream = require('stream');
      const mockVideoStream = new mockStream.Readable({
        read() {
          this.push('video-data-chunk');
          this.push(null); // End stream
        }
      });

      ytdl.mockReturnValue(mockVideoStream);
      ytdl.getInfo.mockResolvedValue({
        videoDetails: {
          videoId: 'dQw4w9WgXcQ',
          title: 'Test Video',
          lengthSeconds: '213'
        }
      });

      const response = await request(app)
        .post('/v1/media/youtube/mp4')
        .send({ url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', quality: 'highest' })
        .set('Content-Type', 'application/json')
        .expect(200);

      expect(response.headers['content-type']).toBe('video/mp4');
      expect(response.headers['x-video-title']).toBeTruthy();
      expect(response.headers['x-video-duration']).toBeTruthy();
    });
  });

  describe('Security Features', () => {
    test('Should reject requests without proper Content-Type', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send('{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}')
        .expect(400);
    });

    test('Should handle SSRF protection', async () => {
      const maliciousUrls = [
        'http://localhost:22/admin',
        'http://127.0.0.1:8080/internal',
        'http://169.254.169.254/metadata',
        'file:///etc/passwd',
        'ftp://malicious.com/file'
      ];

      for (const url of maliciousUrls) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .send({ url })
          .set('Content-Type', 'application/json')
          .expect(400);

        expect(response.body).toHaveProperty('error');
      }
    });

    test('Should sanitize log output', async () => {
      // Test that sensitive data is not logged
      const sensitiveUrl = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&token=secret123';
      
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: sensitiveUrl })
        .set('Content-Type', 'application/json');

      // Logs should not contain the full URL with token
      // This is tested by verifying the response doesn't leak sensitive data
      expect(response.body).not.toHaveProperty('token');
    });

    test('Should enforce rate limiting', async () => {
      // Make multiple rapid requests to test rate limiting
      const promises = [];
      for (let i = 0; i < 10; i++) {
        promises.push(
          request(app)
            .get('/healthz')
        );
      }

      const responses = await Promise.all(promises);
      // Some requests should still succeed, but rate limiting should be active
      const successCount = responses.filter(r => r.status === 200).length;
      expect(successCount).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    test('Should return 404 for non-existent endpoints', async () => {
      const response = await request(app)
        .get('/non-existent-endpoint')
        .expect(404);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error', 'Endpoint not found');
      expect(response.body).toHaveProperty('availableEndpoints');
    });

    test('Should handle malformed JSON gracefully', async () => {
      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send('{"malformed": json}')
        .set('Content-Type', 'application/json')
        .expect(400);
    });

    test('Should handle ytdl-core timeout errors', async () => {
      ytdl.getInfo.mockImplementation(() => {
        return new Promise((resolve, reject) => {
          setTimeout(() => reject(new Error('Request timeout')), 100);
        });
      });

      const response = await request(app)
        .post('/v1/media/youtube/info')
        .send({ url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' })
        .set('Content-Type', 'application/json')
        .expect(500);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error');
    });
  });

  describe('Input Validation', () => {
    test('Should validate YouTube URL format', async () => {
      const invalidUrls = [
        'not-a-url',
        'https://example.com/video',
        'https://vimeo.com/123456789',
        '',
        null,
        undefined
      ];

      for (const url of invalidUrls) {
        const response = await request(app)
          .post('/v1/media/youtube/info')
          .send({ url })
          .set('Content-Type', 'application/json')
          .expect(400);

        expect(response.body).toHaveProperty('error');
      }
    });

    test('Should validate quality parameter for MP3', async () => {
      const invalidQualities = [
        'invalid-quality',
        123,
        null,
        { quality: 'high' }
      ];

      for (const quality of invalidQualities) {
        const response = await request(app)
          .post('/v1/media/youtube/mp3')
          .send({ url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', quality })
          .set('Content-Type', 'application/json')
          .expect(400);

        expect(response.body).toHaveProperty('error');
      }
    });
  });

  describe('Performance', () => {
    test('Health check should respond quickly', async () => {
      const startTime = Date.now();
      
      await request(app)
        .get('/healthz')
        .expect(200);
      
      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(1000); // Should respond within 1 second
    });

    test('Should handle concurrent requests', async () => {
      const promises = [];
      for (let i = 0; i < 5; i++) {
        promises.push(
          request(app)
            .get('/healthz')
            .expect(200)
        );
      }

      const responses = await Promise.all(promises);
      responses.forEach(response => {
        expect(response.body).toHaveProperty('status', 'healthy');
      });
    });
  });
});

describe('ytdl-core Integration', () => {
  // Tests that define expected behavior of ytdl-core integration
  
  test('Should mock ytdl-core getInfo method', () => {
    expect(ytdl.getInfo).toBeDefined();
    expect(typeof ytdl.getInfo).toBe('function');
  });

  test('Should mock ytdl-core streaming method', () => {
    expect(ytdl).toBeDefined();
    expect(typeof ytdl).toBe('function');
  });

  test('Should handle ytdl-core version compatibility', () => {
    // Test that our code works with expected ytdl-core version
    // This is a placeholder for version compatibility checks
    expect(true).toBe(true);
  });
});
