const express = require('express');
const cors = require('cors');
const ytdl = require('ytdl-core');
const winston = require('winston');
const morgan = require('morgan');

// Import custom security middleware
const {
  securityHeaders,
  sanitizeInput,
  ssrfProtection,
  securityLogging,
  contentLengthLimiter,
  speedLimiter,
  rateLimiters,
  validateHeaders
} = require('./middleware/security');

// Import Joi validation schemas
const {
  validate,
  videoInfoSchema,
  mp3DownloadSchema,
  mp4DownloadSchema
} = require('./utils/joi-schemas');

// Import enhanced validation utilities
const {
  validateYouTubeURL,
  sanitizeURL,
  sanitizeFilename
} = require('./utils/validation');

const app = express();
const PORT = process.env.PORT || 3001;

// Configure Winston logger with no sensitive data exposure
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.printf(({ timestamp, level, message, service, ...meta }) => {
      // Remove sensitive data from logs
      const sanitizedMeta = { ...meta };
      if (sanitizedMeta.url && typeof sanitizedMeta.url === 'string') {
        // Only show domain for URL logging
        try {
          const urlObj = new URL(sanitizedMeta.url);
          sanitizedMeta.url = `${urlObj.protocol}//${urlObj.hostname}`;
        } catch (e) {
          sanitizedMeta.url = '[REDACTED]';
        }
      }
      if (sanitizedMeta.userAgent) {
        // Truncate user agent to first 50 chars
        sanitizedMeta.userAgent = sanitizedMeta.userAgent.substring(0, 50);
      }
      
      return JSON.stringify({
        timestamp,
        level,
        message,
        service,
        ...sanitizedMeta
      });
    })
  ),
  defaultMeta: { service: 'youtube-downloader' },
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

// Trust proxy for accurate IP addresses
app.set('trust proxy', true);

// Enhanced security middleware stack
app.use(securityHeaders);
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
  credentials: true,
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Accept', 'User-Agent']
}));

// Security middleware
app.use(contentLengthLimiter);
app.use(sanitizeInput);
app.use(speedLimiter);
app.use(securityLogging);

// Body parsing middleware with limits
app.use(express.json({ limit: '1mb', strict: true }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

// Logging middleware with sanitization
app.use(morgan('combined', {
  stream: { 
    write: (message) => {
      // Remove sensitive data from morgan logs
      const sanitizedMessage = message
        .replace(/(\?|&)(v|watch\?v)=[^&\s]+/g, '$1$2=[REDACTED]')
        .trim();
      logger.info(sanitizedMessage);
    }
  },
  skip: (req, res) => res.statusCode < 400 // Only log errors and client errors
}));

// Health check endpoint with basic rate limiting
app.get('/healthz', rateLimiters.health, (req, res) => {
  const healthCheck = {
    uptime: process.uptime(),
    message: 'OK',
    timestamp: new Date().toISOString(),
    service: 'youtube-downloader',
    version: '1.0.0',
    status: 'healthy'
  };

  try {
    res.status(200).json(healthCheck);
  } catch (error) {
    healthCheck.message = 'ERROR';
    healthCheck.status = 'unhealthy';
    res.status(503).json(healthCheck);
  }
});

// Root endpoint with service information
app.get('/', rateLimiters.health, (req, res) => {
  res.json({
    service: 'YouTube Downloader Microservice',
    version: '1.0.0',
    endpoints: {
      '/healthz': 'Health check endpoint',
      '/v1/media/youtube/info': 'Get video information (POST)',
      '/v1/media/youtube/mp3': 'Download audio as MP3 (POST)',
      '/v1/media/youtube/mp4': 'Download video as MP4 (POST)'
    },
    documentation: '/docs/media-youtube.yaml',
    rateLimit: {
      health: '100 requests/minute',
      info: '30 requests/minute',
      download: '5 requests/5 minutes'
    },
    security: {
      validation: 'Joi schema validation',
      protection: 'SSRF/RFI protection',
      sanitization: 'Input sanitization',
      headers: 'Security headers with Helmet.js'
    }
  });
});

// Get YouTube video information with enhanced validation
app.post('/v1/media/youtube/info', 
  rateLimiters.info,
  validateHeaders,
  validate(videoInfoSchema),
  ssrfProtection,
  async (req, res) => {
    const startTime = Date.now();
    
    try {
      const { url } = req.body;
      const sanitizedURL = sanitizeURL(url);
      
      logger.info('Fetching video info', {
        endpoint: '/v1/media/youtube/info',
        ip: req.ip,
        duration: 0
      });

      const info = await ytdl.getInfo(sanitizedURL);
      const videoDetails = info.videoDetails;
      
      const responseData = {
        success: true,
        data: {
          videoId: videoDetails.videoId,
          title: sanitizeFilename(videoDetails.title),
          description: videoDetails.description ? 
            videoDetails.description.substring(0, 500) : '', // Limit description length
          lengthSeconds: parseInt(videoDetails.lengthSeconds) || 0,
          viewCount: parseInt(videoDetails.viewCount) || 0,
          author: {
            name: sanitizeFilename(videoDetails.author?.name || 'Unknown'),
            channelUrl: videoDetails.author?.channel_url || '',
            subscriberCount: parseInt(videoDetails.author?.subscriber_count) || 0
          },
          publishDate: videoDetails.publishDate,
          uploadDate: videoDetails.uploadDate,
          thumbnails: videoDetails.thumbnails?.slice(0, 5) || [], // Limit thumbnails
          keywords: (videoDetails.keywords || []).slice(0, 10), // Limit keywords
          category: videoDetails.category || 'Unknown',
          isLiveContent: Boolean(videoDetails.isLiveContent),
          formats: {
            audioFormats: info.formats
              .filter(format => format.hasAudio && !format.hasVideo)
              .slice(0, 10) // Limit formats
              .map(format => ({
                itag: format.itag,
                mimeType: format.mimeType,
                bitrate: format.averageBitrate || 0,
                audioQuality: format.audioQuality,
                audioSampleRate: format.audioSampleRate
              })),
            videoFormats: info.formats
              .filter(format => format.hasVideo)
              .slice(0, 10) // Limit formats
              .map(format => ({
                itag: format.itag,
                mimeType: format.mimeType,
                qualityLabel: format.qualityLabel,
                width: format.width || 0,
                height: format.height || 0,
                fps: format.fps || 0,
                hasAudio: Boolean(format.hasAudio)
              }))
          }
        },
        timestamp: new Date().toISOString()
      };

      const duration = Date.now() - startTime;
      logger.info('Video info retrieved successfully', {
        videoId: videoDetails.videoId,
        duration: duration,
        titleLength: videoDetails.title?.length || 0
      });

      res.json(responseData);
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error('Error fetching video info', {
        error: error.message,
        duration: duration,
        type: error.name
      });

      res.status(500).json({
        success: false,
        error: 'Failed to fetch video information',
        message: 'Unable to retrieve video information',
        timestamp: new Date().toISOString()
      });
    }
  }
);

// Download YouTube video as MP3 with strict rate limiting
app.post('/v1/media/youtube/mp3',
  rateLimiters.download,
  validateHeaders,
  validate(mp3DownloadSchema),
  ssrfProtection,
  async (req, res) => {
    const startTime = Date.now();
    
    try {
      const { url, quality = 'highestaudio' } = req.body;
      const sanitizedURL = sanitizeURL(url);
      
      logger.info('Starting MP3 download', {
        endpoint: '/v1/media/youtube/mp3',
        quality,
        ip: req.ip
      });

      const info = await ytdl.getInfo(sanitizedURL);
      const videoDetails = info.videoDetails;
      
      // Set response headers for audio download
      const safeTitle = sanitizeFilename(videoDetails.title);
      res.setHeader('Content-Type', 'audio/mpeg');
      res.setHeader('Content-Disposition', `attachment; filename="${safeTitle}.mp3"`);
      res.setHeader('X-Video-Title', safeTitle);
      res.setHeader('X-Video-Duration', videoDetails.lengthSeconds);
      res.setHeader('X-Download-Time', new Date().toISOString());

      // Create audio stream with timeout
      const audioStream = ytdl(sanitizedURL, {
        quality: quality,
        filter: 'audioonly',
        requestOptions: {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }
        }
      });

      // Handle stream events
      let streamEnded = false;
      
      audioStream.on('error', (error) => {
        if (streamEnded) return;
        streamEnded = true;
        
        logger.error('Audio stream error', {
          error: error.message,
          duration: Date.now() - startTime
        });
        
        if (!res.headersSent) {
          res.status(500).json({
            success: false,
            error: 'Stream error occurred',
            message: 'Unable to process audio stream',
            timestamp: new Date().toISOString()
          });
        }
      });

      audioStream.on('end', () => {
        if (streamEnded) return;
        streamEnded = true;
        
        const duration = Date.now() - startTime;
        logger.info('MP3 download completed', {
          videoId: videoDetails.videoId,
          duration: duration,
          title: safeTitle
        });
      });

      // Set timeout for stream
      const timeout = setTimeout(() => {
        if (!streamEnded) {
          streamEnded = true;
          audioStream.destroy();
          if (!res.headersSent) {
            res.status(408).json({
              success: false,
              error: 'Download timeout',
              message: 'Download took too long to complete'
            });
          }
        }
      }, 300000); // 5 minute timeout

      audioStream.on('end', () => clearTimeout(timeout));
      audioStream.on('error', () => clearTimeout(timeout));

      // Pipe audio stream to response
      audioStream.pipe(res);

    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error('Error downloading MP3', {
        error: error.message,
        duration: duration,
        type: error.name
      });

      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          error: 'Failed to download MP3',
          message: 'Unable to process download request',
          timestamp: new Date().toISOString()
        });
      }
    }
  }
);

// Download YouTube video as MP4 with strict rate limiting
app.post('/v1/media/youtube/mp4',
  rateLimiters.download,
  validateHeaders,
  validate(mp4DownloadSchema),
  ssrfProtection,
  async (req, res) => {
    const startTime = Date.now();
    
    try {
      const { url, quality = 'highest' } = req.body;
      const sanitizedURL = sanitizeURL(url);
      
      logger.info('Starting MP4 download', {
        endpoint: '/v1/media/youtube/mp4',
        quality,
        ip: req.ip
      });

      const info = await ytdl.getInfo(sanitizedURL);
      const videoDetails = info.videoDetails;
      
      // Set response headers for video download
      const safeTitle = sanitizeFilename(videoDetails.title);
      res.setHeader('Content-Type', 'video/mp4');
      res.setHeader('Content-Disposition', `attachment; filename="${safeTitle}.mp4"`);
      res.setHeader('X-Video-Title', safeTitle);
      res.setHeader('X-Video-Duration', videoDetails.lengthSeconds);
      res.setHeader('X-Download-Time', new Date().toISOString());

      // Create video stream with timeout
      const videoStream = ytdl(sanitizedURL, {
        quality: quality,
        filter: format => format.container === 'mp4',
        requestOptions: {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }
        }
      });

      // Handle stream events
      let streamEnded = false;
      
      videoStream.on('error', (error) => {
        if (streamEnded) return;
        streamEnded = true;
        
        logger.error('Video stream error', {
          error: error.message,
          duration: Date.now() - startTime
        });
        
        if (!res.headersSent) {
          res.status(500).json({
            success: false,
            error: 'Stream error occurred',
            message: 'Unable to process video stream',
            timestamp: new Date().toISOString()
          });
        }
      });

      videoStream.on('end', () => {
        if (streamEnded) return;
        streamEnded = true;
        
        const duration = Date.now() - startTime;
        logger.info('MP4 download completed', {
          videoId: videoDetails.videoId,
          duration: duration,
          title: safeTitle
        });
      });

      // Set timeout for stream
      const timeout = setTimeout(() => {
        if (!streamEnded) {
          streamEnded = true;
          videoStream.destroy();
          if (!res.headersSent) {
            res.status(408).json({
              success: false,
              error: 'Download timeout',
              message: 'Download took too long to complete'
            });
          }
        }
      }, 600000); // 10 minute timeout for video

      videoStream.on('end', () => clearTimeout(timeout));
      videoStream.on('error', () => clearTimeout(timeout));

      // Pipe video stream to response
      videoStream.pipe(res);

    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error('Error downloading MP4', {
        error: error.message,
        duration: duration,
        type: error.name
      });

      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          error: 'Failed to download MP4',
          message: 'Unable to process download request',
          timestamp: new Date().toISOString()
        });
      }
    }
  }
);

// Global error handler
app.use((error, req, res, next) => {
  logger.error('Unhandled error', {
    error: error.message,
    stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    url: req.url,
    method: req.method,
    ip: req.ip
  });

  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    message: `${req.method} ${req.url} is not a valid endpoint`,
    availableEndpoints: {
      '/healthz': 'GET - Health check',
      '/v1/media/youtube/info': 'POST - Get video information',
      '/v1/media/youtube/mp3': 'POST - Download audio as MP3',
      '/v1/media/youtube/mp4': 'POST - Download video as MP4'
    },
    timestamp: new Date().toISOString()
  });
});

// Start server
const server = app.listen(PORT, () => {
  logger.info(`YouTube Downloader microservice started on port ${PORT}`, {
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    nodeVersion: process.version,
    features: {
      validation: 'Joi schemas',
      security: 'SSRF protection, input sanitization',
      rateLimit: 'Progressive rate limiting',
      logging: 'No sensitive data exposure'
    }
  });
});

// Graceful shutdown
const gracefulShutdown = (signal) => {
  logger.info(`${signal} received, shutting down gracefully`);
  server.close((err) => {
    if (err) {
      logger.error('Error during shutdown', { error: err.message });
      process.exit(1);
    }
    logger.info('Server closed successfully');
    process.exit(0);
  });
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught exception', {
    error: error.message,
    stack: error.stack
  });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled promise rejection', {
    reason: reason?.toString(),
    promise: promise?.toString()
  });
  process.exit(1);
});

module.exports = app;
