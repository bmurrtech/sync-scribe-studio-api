const Joi = require('joi');

/**
 * Joi schema for validating YouTube URLs
 */
const youtubeUrlSchema = Joi.object({
  url: Joi.string()
    .uri({
      scheme: ['http', 'https'],
      domain: {
        allowUnicode: false
      }
    })
    .required()
    .custom((value, helpers) => {
      try {
        const urlObj = new URL(value);
        const hostname = urlObj.hostname.toLowerCase();
        
        // Check for valid YouTube domains
        const validDomains = [
          'www.youtube.com',
          'youtube.com',
          'youtu.be',
          'm.youtube.com',
          'music.youtube.com'
        ];
        
        if (!validDomains.includes(hostname)) {
          return helpers.error('url.domain');
        }
        
        // Prevent common SSRF/RFI attack vectors
        if (hostname.includes('localhost') || 
            hostname.includes('127.0.0.1') ||
            hostname.includes('0.0.0.0') ||
            hostname.match(/192\.168\.\d+\.\d+/) ||
            hostname.match(/10\.\d+\.\d+\.\d+/) ||
            hostname.match(/172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+/)) {
          return helpers.error('url.private');
        }
        
        return value;
      } catch (error) {
        return helpers.error('url.invalid');
      }
    })
    .messages({
      'url.domain': 'URL must be from a valid YouTube domain',
      'url.private': 'Private IP addresses and localhost are not allowed',
      'url.invalid': 'URL format is invalid'
    })
});

/**
 * Joi schema for video information requests
 */
const videoInfoSchema = youtubeUrlSchema.keys({
  // Additional parameters can be added here if needed
  includeFormats: Joi.boolean().optional().default(true),
  includeThumbnails: Joi.boolean().optional().default(true)
});

/**
 * Joi schema for MP3 download requests
 */
const mp3DownloadSchema = youtubeUrlSchema.keys({
  quality: Joi.string()
    .valid(
      'highestaudio',
      'lowestaudio',
      'highest',
      'lowest'
    )
    .optional()
    .default('highestaudio')
    .messages({
      'any.only': 'Quality must be one of: highestaudio, lowestaudio, highest, lowest'
    }),
  format: Joi.string()
    .valid('mp3', 'aac', 'm4a', 'ogg', 'webm')
    .optional()
    .default('mp3')
    .messages({
      'any.only': 'Format must be one of: mp3, aac, m4a, ogg, webm'
    })
});

/**
 * Joi schema for MP4 download requests
 */
const mp4DownloadSchema = youtubeUrlSchema.keys({
  quality: Joi.string()
    .valid(
      'highest',
      'lowest',
      'highestvideo',
      'lowestvideo',
      '144p',
      '240p',
      '360p',
      '480p',
      '720p',
      '1080p',
      '1440p',
      '2160p'
    )
    .optional()
    .default('highest')
    .messages({
      'any.only': 'Quality must be one of: highest, lowest, highestvideo, lowestvideo, or specific resolution (144p-2160p)'
    }),
  includeAudio: Joi.boolean()
    .optional()
    .default(true)
});

/**
 * Joi validation middleware generator
 * @param {Joi.ObjectSchema} schema - The Joi schema to validate against
 * @returns {Function} Express middleware function
 */
const validate = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true,
      allowUnknown: false
    });

    if (error) {
      const errorDetails = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message,
        type: detail.type,
        value: detail.context?.value
      }));

      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errorDetails,
        timestamp: new Date().toISOString()
      });
    }

    // Replace req.body with validated and sanitized data
    req.body = value;
    next();
  };
};

/**
 * Query parameter validation schema
 */
const queryParamsSchema = Joi.object({
  format: Joi.string()
    .valid('json', 'xml')
    .optional()
    .default('json'),
  pretty: Joi.boolean()
    .optional()
    .default(false),
  includeMetadata: Joi.boolean()
    .optional()
    .default(false)
});

/**
 * Headers validation schema
 */
const headersSchema = Joi.object({
  'user-agent': Joi.string()
    .min(10)
    .max(500)
    .optional()
    .pattern(/^[a-zA-Z0-9\s\(\)\/\.\-;:,_]+$/)
    .messages({
      'string.pattern.base': 'User-Agent contains invalid characters'
    }),
  'accept': Joi.string()
    .optional()
    .valid(
      'application/json',
      'application/xml',
      '*/*',
      'application/json, text/plain, */*'
    ),
  'content-type': Joi.string()
    .valid('application/json', 'application/x-www-form-urlencoded')
    .when('$method', {
      is: 'POST',
      then: Joi.required(),
      otherwise: Joi.optional()
    })
});

/**
 * Validate query parameters middleware
 */
const validateQuery = (req, res, next) => {
  const { error, value } = queryParamsSchema.validate(req.query, {
    stripUnknown: true
  });

  if (error) {
    return res.status(400).json({
      success: false,
      error: 'Invalid query parameters',
      details: error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }))
    });
  }

  req.query = value;
  next();
};

/**
 * Validate headers middleware
 */
const validateHeaders = (req, res, next) => {
  const { error } = headersSchema.validate(req.headers, {
    context: { method: req.method },
    allowUnknown: true
  });

  if (error) {
    return res.status(400).json({
      success: false,
      error: 'Invalid headers',
      details: error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }))
    });
  }

  next();
};

module.exports = {
  youtubeUrlSchema,
  videoInfoSchema,
  mp3DownloadSchema,
  mp4DownloadSchema,
  queryParamsSchema,
  headersSchema,
  validate,
  validateQuery,
  validateHeaders
};
