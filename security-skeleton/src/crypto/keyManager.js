// src/crypto/keyManager.js
// Versioned encryption-key loading and rotation helpers.

const crypto = require('crypto');

function parseKeyring() {
  if (process.env.ENCRYPTION_KEYS_JSON) {
    const parsed = JSON.parse(process.env.ENCRYPTION_KEYS_JSON);
    return parsed.map(({ id, key, active }) => ({ id, key: keyFromHex(key), active: Boolean(active) }));
  }

  if (!process.env.ENCRYPTION_KEY) {
    throw new Error('Missing ENCRYPTION_KEY or ENCRYPTION_KEYS_JSON');
  }
  return [{ id: process.env.ENCRYPTION_KEY_ID || 'k1', key: keyFromHex(process.env.ENCRYPTION_KEY), active: true }];
}

function keyFromHex(hex) {
  const key = Buffer.from(hex, 'hex');
  if (key.length !== 32) throw new Error('Encryption keys must be 32 bytes hex encoded');
  return key;
}

function getActiveKey() {
  const active = parseKeyring().find((entry) => entry.active);
  if (!active) throw new Error('No active encryption key configured');
  return active;
}

function getKeyById(id) {
  const entry = parseKeyring().find((candidate) => candidate.id === id);
  if (!entry) throw new Error(`Unknown encryption key id: ${id}`);
  return entry.key;
}

function generateKey() {
  return crypto.randomBytes(32).toString('hex');
}

function rotationPlan(nextKeyId = `k${Date.now()}`) {
  return {
    nextKeyId,
    nextKeyHex: generateKey(),
    steps: [
      'Add next key to ENCRYPTION_KEYS_JSON with active=true',
      'Keep previous keys with active=false for decrypt-only compatibility',
      'Run field re-encryption job by table and column',
      'Remove retired keys only after backup and restore verification',
    ],
  };
}

module.exports = { getActiveKey, getKeyById, generateKey, rotationPlan };
