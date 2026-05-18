// src/config/db.js
// Hardened DB connection — TLS enforced, min privileges

const { Pool } = require('pg'); // swap for mysql2/knex as needed
const secrets = require('./secrets');
const fs = require('fs');

function sslValue(key) {
  const value = secrets.getOptional(key);
  if (!value) return undefined;
  if (fs.existsSync(value)) return fs.readFileSync(value, 'utf8');
  return value;
}

const ssl = {
  rejectUnauthorized: true,
  ca: sslValue('DB_SSL_CA'),
  cert: sslValue('DB_SSL_CERT'),
  key: sslValue('DB_SSL_KEY'),
};

Object.keys(ssl).forEach((key) => {
  if (ssl[key] === undefined) delete ssl[key];
});

const pool = new Pool({
  host:     secrets.get('DB_HOST'),
  port:     secrets.get('DB_PORT'),
  database: secrets.get('DB_NAME'),
  user:     secrets.get('DB_USER'),
  password: secrets.get('DB_PASS'),

  // TLS enforced — NEVER disable in prod
  ssl,

  // Connection limits — cap blast radius
  max:              10,   // max pool size
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
  options: '-c timezone=UTC',
});

pool.on('error', (err) => {
  console.error('[DB] Unexpected pool error:', err.message);
  process.exit(1); // fail fast — do not limp along
});

module.exports = pool;
