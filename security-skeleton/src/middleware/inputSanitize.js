// src/middleware/inputSanitize.js
// Defensive request sanitizer for JSON bodies, params, and query strings.

const BLOCKED_KEYS = new Set(['__proto__', 'constructor', 'prototype']);
const CONTROL_CHARS = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g;
const MAX_STRING_LENGTH = 10_000;

function sanitizeValue(value) {
  if (typeof value === 'string') {
    return value
      .replace(CONTROL_CHARS, '')
      .trim()
      .slice(0, MAX_STRING_LENGTH);
  }

  if (Array.isArray(value)) return value.map(sanitizeValue);

  if (value && typeof value === 'object') {
    const clean = {};
    for (const [key, child] of Object.entries(value)) {
      if (BLOCKED_KEYS.has(key)) continue;
      clean[key] = sanitizeValue(child);
    }
    return clean;
  }

  return value;
}

function inputSanitize(req, _res, next) {
  req.body = sanitizeValue(req.body || {});
  req.query = sanitizeValue(req.query || {});
  req.params = sanitizeValue(req.params || {});
  next();
}

function requireFields(...fields) {
  return (req, res, next) => {
    const missing = fields.filter((field) => req.body?.[field] === undefined || req.body[field] === '');
    if (missing.length > 0) {
      return res.status(400).json({ error: 'Missing required fields', fields: missing });
    }
    next();
  };
}

module.exports = { inputSanitize, sanitizeValue, requireFields };
