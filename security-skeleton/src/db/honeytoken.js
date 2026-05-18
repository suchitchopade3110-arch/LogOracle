// src/db/honeytoken.js
// Plant fake records; any access is an alert.

const db = require('../config/db');
const { triggerAlert } = require('../monitoring/alerting');
const { logEvent } = require('../monitoring/logger');
const { writeAuditLog } = require('./audit');

const HONEYTOKENS = [
  { email: 'admin-backup@internal.local', role: 'honeytoken' },
  { email: 'sysadmin-test@internal.local', role: 'honeytoken' },
];

async function plantHoneytokens() {
  for (const token of HONEYTOKENS) {
    await db.query(
      `INSERT INTO users (email, password_hash, role)
       VALUES ($1, $2, $3)
       ON CONFLICT (email) DO NOTHING`,
      [token.email, 'HONEYTOKEN_HASH_NEVER_VALID', token.role]
    );
  }
}

async function checkHoneytoken(email, meta = {}) {
  const normalized = String(email || '').toLowerCase().trim();
  const { rows } = await db.query(
    `SELECT id FROM users WHERE email = $1 AND role = 'honeytoken'`,
    [normalized]
  );

  if (rows.length === 0) return false;

  const payload = { email: normalized, severity: 'CRITICAL', ...meta };
  logEvent('HONEYTOKEN_ACCESS', payload);
  await writeAuditLog({
    userId: rows[0].id,
    action: 'HONEYTOKEN_ACCESS',
    targetTable: 'users',
    ip: meta.ip,
    meta: payload,
  }).catch(() => {});
  await triggerAlert('HONEYTOKEN_ACCESS', {
    email: normalized,
    message: 'Attacker probing honeytoken accounts',
    ...meta,
  });
  return true;
}

module.exports = { HONEYTOKENS, plantHoneytokens, checkHoneytoken };
