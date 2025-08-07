const validator = require('validator');
const ytdl = require('ytdl-core');

/**
 * Validates if the provided URL is a valid YouTube URL
 * @param {string} url - The URL to validate
 * @returns {boolean} - True if valid YouTube URL, false otherwise
 */
const validateYouTubeURL = (url) => {
  try {
    if (!url || typeof url !== 'string') {
      return false;
    }

    const urlObj = new URL(url);
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
      return false;
    }
    
    // Additional validation using ytdl-core
    return ytdl.validateURL(url);
  } catch (error) {
    return false;
  }
};

/**
 * Sanitizes YouTube URL by removing tracking and non-essential parameters
 * @param {string} url - The URL to sanitize
 * @returns {string} - Sanitized URL
 * @throws {Error} - If URL is invalid
 */
const sanitizeURL = (url) => {
  try {
    const urlObj = new URL(url);
    
    // Remove tracking parameters and keep only essential ones
    const allowedParams = ['v', 't', 'list', 'index', 'start'];
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

/**
 * Extracts video ID from YouTube URL
 * @param {string} url - YouTube URL
 * @returns {string|null} - Video ID or null if not found
 */
const extractVideoId = (url) => {
  try {
    return ytdl.getURLVideoID(url);
  } catch (error) {
    return null;
  }
};

/**
 * Validates quality parameter for audio downloads
 * @param {string} quality - Quality parameter
 * @returns {boolean} - True if valid quality
 */
const validateAudioQuality = (quality) => {
  const validQualities = [
    'highestaudio',
    'lowestaudio',
    'highest',
    'lowest'
  ];
  return !quality || validQualities.includes(quality);
};

/**
 * Validates quality parameter for video downloads
 * @param {string} quality - Quality parameter
 * @returns {boolean} - True if valid quality
 */
const validateVideoQuality = (quality) => {
  const validQualities = [
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
  ];
  return !quality || validQualities.includes(quality);
};

/**
 * Sanitizes filename by removing invalid characters
 * @param {string} filename - Original filename
 * @returns {string} - Sanitized filename
 */
const sanitizeFilename = (filename) => {
  if (!filename || typeof filename !== 'string') {
    return 'download';
  }
  
  return filename
    .replace(/[<>:"/\\|?*]/g, '_')
    .replace(/[\x00-\x1f\x80-\x9f]/g, '')
    .replace(/^\.+/, '')
    .substring(0, 255)
    .trim();
};

/**
 * Validates request rate limiting parameters
 * @param {Object} req - Express request object
 * @returns {Object} - Validation result with isValid and message
 */
const validateRateLimit = (req) => {
  const ip = req.ip || req.connection.remoteAddress;
  
  if (!ip) {
    return {
      isValid: false,
      message: 'Unable to identify client IP'
    };
  }
  
  return {
    isValid: true,
    ip
  };
};

module.exports = {
  validateYouTubeURL,
  sanitizeURL,
  extractVideoId,
  validateAudioQuality,
  validateVideoQuality,
  sanitizeFilename,
  validateRateLimit
};
