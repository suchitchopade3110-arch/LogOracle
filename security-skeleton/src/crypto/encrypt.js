// src/crypto/encrypt.js
// AES-256-GCM column encryption for PII fields.

const crypto = require('crypto');
const { getActiveKey, getKeyById } = require('./keyManager');

const ALGORITHM = 'aes-256-gcm';

function encrypt(plaintext, aad = '') {
  const active = getActiveKey();
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv(ALGORITHM, active.key, iv);
  if (aad) cipher.setAAD(Buffer.from(aad, 'utf8'));
  const encrypted = Buffer.concat([cipher.update(String(plaintext), 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();

  return [
    'v1',
    active.id,
    iv.toString('hex'),
    tag.toString('hex'),
    encrypted.toString('hex'),
  ].join(':');
}

function decrypt(stored, aad = '') {
  const [version, keyId, ivHex, tagHex, encHex] = String(stored).split(':');
  if (version !== 'v1') throw new Error('Unsupported ciphertext version');

  const key = getKeyById(keyId);
  const decipher = crypto.createDecipheriv(ALGORITHM, key, Buffer.from(ivHex, 'hex'));
  if (aad) decipher.setAAD(Buffer.from(aad, 'utf8'));
  decipher.setAuthTag(Buffer.from(tagHex, 'hex'));
  return Buffer.concat([
    decipher.update(Buffer.from(encHex, 'hex')),
    decipher.final(),
  ]).toString('utf8');
}

module.exports = { encrypt, decrypt };
