// src/db/audit.js
// Write security events directly to DB audit table.

const db = require('../config/db');

async function writeAuditLog({ userId = null, action, targetTable = null, ip = null, meta = {} }) {
  if (!action) throw new Error('audit action is required');
  const sql = `
    INSERT INTO audit_log (user_id, action, target_table, ip_address, meta, created_at)
    VALUES ($1, $2, $3, $4, $5, NOW())
  `;
  await db.query(sql, [userId, action, targetTable, ip, JSON.stringify(meta)]);
}

module.exports = { writeAuditLog };
