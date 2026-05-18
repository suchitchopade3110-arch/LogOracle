// src/crypto/hash.js
// Argon2id for passwords — bcrypt fallback if argon2 unavailable

const argon2 = require('argon2');

// Argon2id — best for passwords (memory-hard)
async function hashPassword(plaintext) {
  return argon2.hash(plaintext, {
    type: argon2.argon2id,
    memoryCost: 65536,  // 64MB
    timeCost: 3,
    parallelism: 4,
  });
}

async function verifyPassword(hash, plaintext) {
  return argon2.verify(hash, plaintext);
}

module.exports = { hashPassword, verifyPassword };
