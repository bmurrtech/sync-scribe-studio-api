const express = require('express');
const cors = require('cors');
const ytdl = require('ytdl-core');
const winston = require('winston');

// Import custom security middleware
const {
  securityHeaders,
  sanitizeInput,
  ssrfProtection,
  securityLogging,
  contentLengthLimiter,
  speedLimiter,
  rateLimiters
} = require('./middleware/security');

// Import Joi validation schemas
const {
  validate,
  validateQuery,
  validateHeaders,
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

// Configure Winston logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
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

// Enhanced security middleware
app.use(securityHeaders);
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
  credentials: true
}));

// Security middleware stack
app.use(contentLengthLimiter);
app.use(sanitizeInput);
app.use(speedLimiter);
app.use(securityLogging);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging middleware
app.use(morgan('combined', {
  stream: { write: (message) => logger.info(message.trim()) }
}));

// Utility functions
const validateYouTubeURL = (url) => {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();
    
    // Check for valid YouTube domains
    const validDomains = [
      'www.youtube.com',
      'youtube.com',
      'youtu.be',
      'm.youtube.com'
    ];
    
    if (!validDomains.includes(hostname)) {
      return false;
    }
    
    // Additional validation using ytdl-core
    return ytdl.validateURL(url);
  } catch (error) {
    return false;
  }
};

const sanitizeURL = (url) => {
  try {
    const urlObj = new URL(url);
    // Remove tracking parameters and keep only essential ones
    const allowedParams = ['v', 't', 'list'];
    const params = new URLSearchParams();
    
    for (const [key, value] of urlObj.searchParams) {
      if (allowedParams.includes(key)) {
        params.append(key, value);
      }
    }
    
    urlObj.search = params.toString();
    return urlObj.toString();
  } catch (error) {
    throw new Error('Invalid URL format');
  }
};

// Validation middleware
const validateURLMiddleware = [
  body('url')
    .isURL()
    .withMessage('Invalid URL format')
    .custom((value) => {
      if (!validateYouTubeURL(value)) {
        throw new Error('Invalid YouTube URL');
      }
      return true;
    }),
];

const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      error: 'Validation failed',
      details: errors.array()
    });
  }
  next();
};

// Health check endpoint
app.get('/healthz', (req, res) => {
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
app.get('/', (req, res) => {
  res.json({
    service: 'YouTube Downloader Microservice',
    version: '1.0.0',
    endpoints: {
      '/healthz': 'Health check endpoint',
      '/v1/media/youtube/info': 'Get video information (POST)',
      '/v1/media/youtube/mp3': 'Download audio as MP3 (POST)',
      '/v1/media/youtube/mp4': 'Download video as MP4 (POST)'
    },
    documentation: 'https://github.com/sync-scribe-studio/api'
  });
});

// Get YouTube video information
app.post('/v1/media/youtube/info', validateURLMiddleware, handleValidationErrors, async (req, res) => {
  try {
    const { url } = req.body;
    const sanitizedURL = sanitizeURL(url);
    
    logger.info(`Fetching video info for URL: ${sanitizedURL}`, {
      endpoint: '/v1/media/youtube/info',
      userAgent: req.get('User-Agent'),
      ip: req.ip
    });

    const info = await ytdl.getInfo(sanitizedURL);
    const videoDetails = info.videoDetails;
    
    const responseData = {
      success: true,
      data: {
        videoId: videoDetails.videoId,
        title: videoDetails.title,
        description: videoDetails.description,
        lengthSeconds: parseInt(videoDetails.lengthSeconds),
        viewCount: parseInt(videoDetails.viewCount),
        author: {
          name: videoDetails.author.name,
          channelUrl: videoDetails.author.channel_url,
          subscriberCount: videoDetails.author.subscriber_count
        },
        publishDate: videoDetails.publishDate,
        uploadDate: videoDetails.uploadDate,
        thumbnails: videoDetails.thumbnails,
        keywords: videoDetails.keywords || [],
        category: videoDetails.category,
        isLiveContent: videoDetails.isLiveContent,
        formats: {
          audioFormats: info.formats
            .filter(format => format.hasAudio && !format.hasVideo)
            .map(format => ({
              itag: format.itag,
              mimeType: format.mimeType,
              bitrate: format.averageBitrate,
              audioQuality: format.audioQuality,
              audioSampleRate: format.audioSampleRate
            })),
          videoFormats: info.formats
            .filter(format => format.hasVideo)
            .map(format => ({
              itag: format.itag,
              mimeType: format.mimeType,
              qualityLabel: format.qualityLabel,
              width: format.width,
              height: format.height,
              fps: format.fps,
              hasAudio: format.hasAudio
            }))
        }
      },
      timestamp: new Date().toISOString()
    };

    logger.info(`Video info retrieved successfully for: ${videoDetails.title}`, {
      videoId: videoDetails.videoId,
      duration: videoDetails.lengthSeconds
    });

    res.json(responseData);
  } catch (error) {
    logger.error('Error fetching video info:', {
      error: error.message,
      stack: error.stack,
      url: req.body.url
    });

    res.status(500).json({
      success: false,
      error: 'Failed to fetch video information',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Download YouTube video as MP3
app.post('/v1/media/youtube/mp3', validateURLMiddleware, handleValidationErrors, async (req, res) => {
  try {
    const { url, quality = 'highestaudio' } = req.body;
    const sanitizedURL = sanitizeURL(url);
    
    logger.info(`Starting MP3 download for URL: ${sanitizedURL}`, {
      endpoint: '/v1/media/youtube/mp3',
      quality,
      userAgent: req.get('User-Agent'),
      ip: req.ip
    });

    const info = await ytdl.getInfo(sanitizedURL);
    const videoDetails = info.videoDetails;
    
    // Set response headers for audio download
    res.setHeader('Content-Type', 'audio/mpeg');
    res.setHeader('Content-Disposition', `attachment; filename="${videoDetails.title.replace(/[^a-zA-Z0-9]/g, '_')}.mp3"`);
    res.setHeader('X-Video-Title', videoDetails.title);
    res.setHeader('X-Video-Duration', videoDetails.lengthSeconds);

    // Create audio stream
    const audioStream = ytdl(sanitizedURL, {
      quality: quality,
      filter: 'audioonly',
      requestOptions: {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
      }
    });

    // Handle stream events
    audioStream.on('error', (error) => {
      logger.error('Audio stream error:', {
        error: error.message,
        url: sanitizedURL
      });
      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          error: 'Stream error occurred',
          message: error.message
        });
      }
    });

    audioStream.on('end', () => {
      logger.info(`MP3 download completed for: ${videoDetails.title}`, {
        videoId: videoDetails.videoId
      });
    });

    // Pipe audio stream to response
    audioStream.pipe(res);

  } catch (error) {
    logger.error('Error downloading MP3:', {
      error: error.message,
      stack: error.stack,
      url: req.body.url
    });

    if (!res.headersSent) {
      res.status(500).json({
        success: false,
        error: 'Failed to download MP3',
        message: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
});

// Download YouTube video as MP4
app.post('/v1/media/youtube/mp4', validateURLMiddleware, handleValidationErrors, async (req, res) => {
  try {
    const { url, quality = 'highest' } = req.body;
    const sanitizedURL = sanitizeURL(url);
    
    logger.info(`Starting MP4 download for URL: ${sanitizedURL}`, {
      endpoint: '/v1/media/youtube/mp4',
      quality,
      userAgent: req.get('User-Agent'),
      ip: req.ip
    });

    const info = await ytdl.getInfo(sanitizedURL);
    const videoDetails = info.videoDetails;
    
    // Set response headers for video download
    res.setHeader('Content-Type', 'video/mp4');
    res.setHeader('Content-Disposition', `attachment; filename="${videoDetails.title.replace(/[^a-zA-Z0-9]/g, '_')}.mp4"`);
    res.setHeader('X-Video-Title', videoDetails.title);
    res.setHeader('X-Video-Duration', videoDetails.lengthSeconds);

    // Create video stream
    const videoStream = ytdl(sanitizedURL, {
      quality: quality,
      filter: format => format.container === 'mp4',
      requestOptions: {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
      }
    });

    // Handle stream events
    videoStream.on('error', (error) => {
      logger.error('Video stream error:', {
        error: error.message,
        url: sanitizedURL
      });
      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          error: 'Stream error occurred',
          message: error.message
        });
      }
    });

    videoStream.on('end', () => {
      logger.info(`MP4 download completed for: ${videoDetails.title}`, {
        videoId: videoDetails.videoId
      });
    });

    // Pipe video stream to response
    videoStream.pipe(res);

  } catch (error) {
    logger.error('Error downloading MP4:', {
      error: error.message,
      stack: error.stack,
      url: req.body.url
    });

    if (!res.headersSent) {
      res.status(500).json({
        success: false,
        error: 'Failed to download MP4',
        message: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
});

// Global error handler
app.use((error, req, res, next) => {
  logger.error('Unhandled error:', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method
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
    }
  });
});

// Start server
app.listen(PORT, () => {
  logger.info(`YouTube Downloader microservice started on port ${PORT}`, {
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    nodeVersion: process.version
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

module.exports = app;
