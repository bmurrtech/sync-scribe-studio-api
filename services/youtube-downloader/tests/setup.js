/**
 * Jest Test Setup
 * Global test configuration and utilities
 */

// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.PORT = 3001;
process.env.LOG_LEVEL = 'error';
process.env.ALLOWED_ORIGINS = 'http://localhost:3000';
process.env.API_KEY = 'test-api-key';

// Global test timeout
jest.setTimeout(30000);

// Global error handling for unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Global error handling for uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

// Mock external dependencies
jest.mock('ytdl-core', () => ({
  getInfo: jest.fn(),
  chooseFormat: jest.fn(),
  downloadFromInfo: jest.fn(),
  validateURL: jest.fn()
}));

// Mock Winston logger to prevent console spam
jest.mock('winston', () => ({
  createLogger: () => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn()
  }),
  format: {
    combine: jest.fn(() => ({})),
    timestamp: jest.fn(() => ({})),
    errors: jest.fn(() => ({})),
    printf: jest.fn(() => ({})),
    colorize: jest.fn(() => ({})),
    simple: jest.fn(() => ({}))
  },
  transports: {
    File: jest.fn(() => ({})),
    Console: jest.fn(() => ({}))
  }
}));

// Global test utilities
global.testUtils = {
  // Mock YouTube URL for testing
  mockYouTubeUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  
  // Mock video info response
  mockVideoInfo: {
    videoDetails: {
      videoId: 'dQw4w9WgXcQ',
      title: 'Test Video Title',
      description: 'Test video description',
      lengthSeconds: '212',
      viewCount: '1000000',
      author: {
        name: 'Test Channel',
        channel_url: 'https://www.youtube.com/channel/test',
        subscriber_count: '100000'
      },
      publishDate: '2021-01-01',
      uploadDate: '2021-01-01',
      thumbnail: {
        thumbnails: [
          {
            url: 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
            width: 1920,
            height: 1080
          }
        ]
      }
    },
    formats: [
      {
        itag: 140,
        mimeType: 'audio/mp4; codecs="mp4a.40.2"',
        bitrate: 128,
        audioBitrate: 128,
        url: 'https://test-audio-url.com/audio.mp4',
        hasAudio: true,
        hasVideo: false,
        container: 'mp4',
        codecs: 'mp4a.40.2',
        audioCodec: 'mp4a.40.2',
        videoCodec: null
      },
      {
        itag: 18,
        mimeType: 'video/mp4; codecs="avc1.42001E, mp4a.40.2"',
        quality: 'medium',
        qualityLabel: '360p',
        url: 'https://test-video-url.com/video.mp4',
        hasAudio: true,
        hasVideo: true,
        container: 'mp4',
        codecs: 'avc1.42001E, mp4a.40.2',
        videoCodec: 'avc1.42001E',
        audioCodec: 'mp4a.40.2'
      }
    ]
  },
  
  // Helper to create mock request
  createMockRequest: (overrides = {}) => ({
    body: {},
    headers: { 'user-agent': 'test-agent' },
    ip: '127.0.0.1',
    method: 'POST',
    url: '/test',
    ...overrides
  }),
  
  // Helper to create mock response
  createMockResponse: () => {
    const res = {
      status: jest.fn(() => res),
      json: jest.fn(() => res),
      send: jest.fn(() => res),
      set: jest.fn(() => res),
      header: jest.fn(() => res)
    };
    return res;
  },
  
  // Helper to create mock next function
  createMockNext: () => jest.fn(),
  
  // Wait helper for async operations
  wait: (ms = 100) => new Promise(resolve => setTimeout(resolve, ms))
};

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
  // Reset environment variables if needed
});

// Console override for cleaner test output
const originalConsoleError = console.error;
console.error = (...args) => {
  // Filter out known test warnings/errors that are expected
  const message = args[0];
  if (
    typeof message === 'string' &&
    (message.includes('Warning:') || message.includes('deprecated'))
  ) {
    return;
  }
  originalConsoleError.apply(console, args);
};

// Suppress console logs during testing unless debugging
if (!process.env.DEBUG_TESTS) {
  global.console = {
    ...console,
    log: jest.fn(),
    info: jest.fn(),
    warn: jest.fn()
  };
}
