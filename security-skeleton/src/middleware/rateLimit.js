// src/middleware/rateLimit.js
// Brute force protection — login + API limits

const rateLimit = require('express-rate-limit');
const { RedisStore } = require('rate-limit-redis');
const redis = require('redis');
const { logEvent } = require('../monitoring/logger');
const { triggerAlert } = require('../monitoring/alerting');

const redisClient = redis.createClient({ url: process.env.REDIS_URL });
redisClient.connect();

// Strict login limiter — 5 attempts per 15 min per IP
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 5,
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  skipSuccessfulRequests: false,
  handler: (req, res) => {
    logEvent('RATE_LIMIT_HIT', { route: 'login', ip: req.ip });
    triggerAlert('BRUTE_FORCE_ATTEMPT', { ip: req.ip, route: '/login' });
    res.status(429).json({ error: 'Too many login attempts. Try again in 15 minutes.' });
  },
});

// General API limiter — 100 req per 15 min
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  handler: (req, res) => {
    logEvent('RATE_LIMIT_HIT', { route: req.path, ip: req.ip });
    res.status(429).json({ error: 'Rate limit exceeded.' });
  },
});

// Strict limiter for password reset
const passwordResetLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 3,
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  handler: (req, res) => {
    logEvent('RATE_LIMIT_HIT', { route: 'password_reset', ip: req.ip });
    res.status(429).json({ error: 'Too many reset attempts.' });
  },
});

module.exports = { loginLimiter, apiLimiter, passwordResetLimiter };
