// src/incident/containment.js
// Isolate compromised users and suspicious IPs.

const db = require('../config/db');
const { logEvent } = require('../monitoring/logger');

async function isolate({ userId, ip } = {}) {
  if (userId) {
    await db.query(
      `UPDATE users SET locked = true, lock_reason = 'SECURITY_INCIDENT' WHERE id = $1`,
      [userId]
    );
    await db.query(`DELETE FROM sessions WHERE user_id = $1`, [userId]);
    logEvent('CONTAINMENT_USER_ISOLATED', { userId });
  }

  if (ip) {
    await db.query(
      `INSERT INTO blocked_ips (ip, reason, blocked_at)
       VALUES ($1, 'INCIDENT', NOW())
       ON CONFLICT (ip) DO NOTHING`,
      [ip]
    );
    logEvent('CONTAINMENT_IP_BLOCKED', { ip });
  }
}

module.exports = { isolate };
