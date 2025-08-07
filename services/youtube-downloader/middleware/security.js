const rateLimit = require('express-rate-limit');
const slowDown = require('express-slow-down');
const helmet = require('helmet');
const winston = require('winston');

// Configure logger for security events
const securityLogger = winston.createLogger({
  level: 'warn',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'youtube-downloader-security' },
  transports: [
    new winston.transports.File({ filename: 'security.log', level: 'warn' }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

/**
 * Enhanced rate limiter with progressive restrictions
 */
const createRateLimiter = (options = {}) => {
  const defaultOptions = {
    windowMs: 60 * 1000, // 1 minute
    max: 10, // 10 requests per minute
    message: {
      success: false,
      error: 'Too many requests',
      message: 'Rate limit exceeded. Please try again later.',
      retryAfter: Math.ceil(options.windowMs / 1000) || 60
    },
    standardHeaders: true,
    legacyHeaders: false,
    // Trust proxy but validate to prevent bypass
    validate: {
      trustProxy: false // Disable trust proxy validation warning
    },
    keyGenerator: (req) => {
      // Use forwarded IP if available, otherwise use connection IP
      return req.ip || req.connection.remoteAddress || 'unknown';
    },
    handler: (req, res, next) => {
      securityLogger.warn('Rate limit exceeded', {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        endpoint: req.originalUrl,
        method: req.method
      });
      
      const message = options.message || defaultOptions.message;
      res.status(429).json(message);
    }
  };

  return rateLimit({ ...defaultOptions, ...options });
};

/**
 * Speed limiter that progressively slows down requests
 */
const speedLimiter = slowDown({
  windowMs: 60 * 1000, // 1 minute
  delayAfter: 5, // Allow 5 requests per windowMs without delay
  delayMs: () => 500, // Add 500ms delay per request after delayAfter
  maxDelayMs: 5000, // Maximum delay of 5 seconds
  skipSuccessfulRequests: false,
  skipFailedRequests: false,
  validate: {
    delayMs: false // Disable the deprecation warning
  }
});

/**
 * Enhanced helmet configuration for security headers
 */
const securityHeaders = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
    },
  },
  crossOriginEmbedderPolicy: false, // Allow cross-origin requests for media
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  },
  noSniff: true,
  frameguard: { action: 'deny' },
  xssFilter: true,
  referrerPolicy: {
    policy: ['same-origin']
  }
});

/**
 * Input sanitization middleware to prevent malicious input
 */
const sanitizeInput = (req, res, next) => {
  const sanitizeString = (str) => {
    if (typeof str !== 'string') return str;
    
    // Remove potential XSS vectors
    return str
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/vbscript:/gi, '')
      .replace(/data:text\/html/gi, '')
      .trim();
  };

  const sanitizeObject = (obj) => {
    if (obj === null || obj === undefined) return obj;
    if (typeof obj === 'string') return sanitizeString(obj);
    if (Array.isArray(obj)) return obj.map(sanitizeObject);
    if (typeof obj === 'object') {
      const sanitized = {};
      for (const [key, value] of Object.entries(obj)) {
        sanitized[sanitizeString(key)] = sanitizeObject(value);
      }
      return sanitized;
    }
    return obj;
  };

  // Sanitize body, query, and params
  if (req.body) req.body = sanitizeObject(req.body);
  if (req.query) req.query = sanitizeObject(req.query);
  if (req.params) req.params = sanitizeObject(req.params);

  next();
};

/**
 * SSRF protection middleware
 */
const ssrfProtection = (req, res, next) => {
  const { url } = req.body;
  
  if (!url) return next();

  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();
    const ip = urlObj.hostname;

    // Block private IP ranges and localhost
    const dangerousPatterns = [
      /^localhost$/i,
      /^127\./,
      /^0\.0\.0\.0$/,
      /^10\./,
      /^172\.(1[6-9]|2[0-9]|3[0-1])\./,
      /^192\.168\./,
      /^169\.254\./, // Link-local
      /^::1$/, // IPv6 localhost
      /^fc00:/, // IPv6 private
      /^fe80:/, // IPv6 link-local
    ];

    // Check for dangerous patterns
    if (dangerousPatterns.some(pattern => pattern.test(hostname) || pattern.test(ip))) {
      securityLogger.warn('SSRF attempt detected', {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        targetUrl: url,
        hostname: hostname
      });

      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'Access to private networks is not allowed'
      });
    }

    // Block non-standard ports (except 80, 443)
    const port = urlObj.port;
    if (port && !['80', '443', ''].includes(port)) {
      securityLogger.warn('Suspicious port access attempt', {
        ip: req.ip,
        targetUrl: url,
        port: port
      });

      return res.status(403).json({
        success: false,
        error: 'Forbidden',
        message: 'Access to non-standard ports is not allowed'
      });
    }

  } catch (error) {
    return res.status(400).json({
      success: false,
      error: 'Invalid URL',
      message: 'The provided URL is malformed'
    });
  }

  next();
};

/**
 * Request logging middleware with security focus
 */
const securityLogging = (req, res, next) => {
  const startTime = Date.now();
  
  // Log suspicious patterns
  const userAgent = req.get('User-Agent') || '';
  const suspiciousPatterns = [
    /bot|crawler|spider/i,
    /curl|wget|axios/i,
    /python|java|php/i
  ];

  if (suspiciousPatterns.some(pattern => pattern.test(userAgent))) {
    securityLogger.info('Potential automated request', {
      ip: req.ip,
      userAgent: userAgent,
      endpoint: req.originalUrl,
      method: req.method
    });
  }

  res.on('finish', () => {
    const duration = Date.now() - startTime;
    
    // Log slow requests (potential DoS)
    if (duration > 30000) { // 30 seconds
      securityLogger.warn('Slow request detected', {
        ip: req.ip,
        endpoint: req.originalUrl,
        duration: duration,
        statusCode: res.statusCode
      });
    }

    // Log failed requests
    if (res.statusCode >= 400) {
      securityLogger.warn('Failed request', {
        ip: req.ip,
        endpoint: req.originalUrl,
        statusCode: res.statusCode,
        userAgent: req.get('User-Agent')
      });
    }
  });

  next();
};

/**
 * Content length limiter to prevent large payload attacks
 */
const contentLengthLimiter = (req, res, next) => {
  const maxSize = 1024 * 1024; // 1MB
  const contentLength = parseInt(req.get('Content-Length') || '0', 10);

  if (contentLength > maxSize) {
    securityLogger.warn('Large payload rejected', {
      ip: req.ip,
      contentLength: contentLength,
      maxAllowed: maxSize
    });

    return res.status(413).json({
      success: false,
      error: 'Payload too large',
      message: `Request body must be smaller than ${maxSize} bytes`
    });
  }

  next();
};

/**
 * Create different rate limiters for different endpoints
 */
const rateLimiters = {
  // Strict rate limiting for download endpoints
  download: createRateLimiter({
    windowMs: 5 * 60 * 1000, // 5 minutes
    max: 5, // 5 downloads per 5 minutes
    message: {
      success: false,
      error: 'Download rate limit exceeded',
      message: 'Too many download requests. Please wait before trying again.',
      retryAfter: 300
    }
  }),

  // Moderate rate limiting for info endpoints
  info: createRateLimiter({
    windowMs: 60 * 1000, // 1 minute
    max: 30, // 30 requests per minute
    message: {
      success: false,
      error: 'API rate limit exceeded',
      message: 'Too many API requests. Please wait before trying again.',
      retryAfter: 60
    }
  }),

  // Lenient rate limiting for health checks
  health: createRateLimiter({
    windowMs: 60 * 1000, // 1 minute
    max: 100, // 100 requests per minute
    skipSuccessfulRequests: true
  })
};

/**
 * Headers validation middleware
 */
const validateHeaders = (req, res, next) => {
  // Basic header validation
  const userAgent = req.get('User-Agent');
  if (userAgent && userAgent.length > 1000) {
    securityLogger.warn('Oversized User-Agent header', {
      ip: req.ip,
      headerLength: userAgent.length
    });
    
    return res.status(400).json({
      success: false,
      error: 'Invalid headers',
      message: 'User-Agent header too long'
    });
  }
  
  // Check for potentially malicious headers
  const dangerousHeaderPatterns = [
    /<script/i,
    /javascript:/i,
    /vbscript:/i,
    /\x00/,
    /\r|\n/
  ];
  
  const allHeaders = JSON.stringify(req.headers);
  if (dangerousHeaderPatterns.some(pattern => pattern.test(allHeaders))) {
    securityLogger.warn('Malicious headers detected', {
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });
    
    return res.status(400).json({
      success: false,
      error: 'Invalid headers',
      message: 'Request headers contain invalid content'
    });
  }
  
  next();
};

module.exports = {
  securityHeaders,
  sanitizeInput,
  ssrfProtection,
  securityLogging,
  contentLengthLimiter,
  speedLimiter,
  rateLimiters,
  validateHeaders,
  securityLogger
};
