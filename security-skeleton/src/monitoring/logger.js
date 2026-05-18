// src/monitoring/logger.js
// Structured JSON logs — ELK / SIEM ready

const { createLogger, transports, format } = require('winston');
const fs = require('fs');

fs.mkdirSync('logs', { recursive: true });

const logger = createLogger({
  level: 'info',
  format: format.combine(
    format.timestamp(),
    format.errors({ stack: true }),
    format.json()  // machine-readable for ELK ingestion
  ),
  transports: [
    new transports.File({ filename: 'logs/error.log',  level: 'error' }),
    new transports.File({ filename: 'logs/audit.log' }),  // ALL events
    new transports.Console({ format: format.simple() }),   // dev only
  ],
});

// Security event log — every auth/query/access event
function logEvent(eventType, meta = {}) {
  logger.info({
    event:     eventType,
    timestamp: new Date().toISOString(),
    ...meta,
  });
}

// Query log — track who ran what
function logQuery(queryName, meta = {}) {
  logger.info({
    event:     'DB_QUERY',
    query:     queryName,
    timestamp: new Date().toISOString(),
    ...meta,
  });
}

// Auth log
function logAuth(outcome, meta = {}) {
  logger.info({
    event:     `AUTH_${outcome}`,  // AUTH_SUCCESS / AUTH_FAIL
    timestamp: new Date().toISOString(),
    ...meta,
  });
}

module.exports = { logEvent, logQuery, logAuth };
