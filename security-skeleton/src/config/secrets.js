// src/config/secrets.js
// Secrets from HashiCorp Vault or .env — NEVER hardcoded

const vault = require('node-vault'); // optional: only if using Vault

let secretsCache = {};

async function loadFromVault() {
  const client = vault({ endpoint: process.env.VAULT_ADDR, token: process.env.VAULT_TOKEN });
  const paths = {
    'secret/data/logoracle/db': {
      user: 'DB_USER',
      pass: 'DB_PASS',
      name: 'DB_NAME',
      host: 'DB_HOST',
      port: 'DB_PORT',
    },
    'secret/data/logoracle/redis': {
      pass: 'REDIS_PASS',
      url: 'REDIS_URL',
    },
    'secret/data/logoracle/app': {
      api_key: 'API_KEY',
      jwt_secret: 'JWT_SECRET',
      encryption_key: 'ENCRYPTION_KEY',
      backup_encryption_key: 'BACKUP_ENCRYPTION_KEY',
      slack_security_webhook: 'SLACK_SECURITY_WEBHOOK',
    },
  };

  const loaded = {};
  for (const [path, mapping] of Object.entries(paths)) {
    try {
      const result = await client.read(path);
      const data = result.data.data || {};
      Object.entries(mapping).forEach(([vaultKey, envKey]) => {
        if (data[vaultKey]) loaded[envKey] = data[vaultKey];
      });
    } catch (err) {
      if (process.env.VAULT_REQUIRED === 'true') {
        throw new Error(`[VAULT] Missing or unreadable path ${path}: ${err.message}`);
      }
    }
  }

  if (loaded.REDIS_PASS && !loaded.REDIS_URL) {
    loaded.REDIS_URL = `redis://:${loaded.REDIS_PASS}@redis:6379`;
  }
  secretsCache = loaded;
  return secretsCache;
}

function get(key) {
  // Vault takes priority, fallback to env
  const val = secretsCache[key] || process.env[key];
  if (!val) throw new Error(`[SECRETS] Missing required secret: ${key}`);
  return val;
}

function getOptional(key) {
  return secretsCache[key] || process.env[key] || '';
}

module.exports = { loadFromVault, get, getOptional };
