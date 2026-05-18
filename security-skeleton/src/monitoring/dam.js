// src/monitoring/dam.js
// Lightweight database activity monitoring hooks.

const { logEvent } = require('./logger');
const { triggerAlert } = require('./alerting');
const { writeAuditLog } = require('../db/audit');

const BULK_ROW_THRESHOLD = Number(process.env.DAM_BULK_ROW_THRESHOLD || 500);
const SENSITIVE_TABLES = new Set(['users', 'sessions', 'audit_log']);

function classifyQuery(sql = '') {
  const normalized = sql.replace(/\s+/g, ' ').trim().toLowerCase();
  const type = normalized.split(' ')[0] || 'unknown';
  const tableMatch = normalized.match(/\bfrom\s+([a-z0-9_."-]+)/i)
    || normalized.match(/\binto\s+([a-z0-9_."-]+)/i)
    || normalized.match(/\bupdate\s+([a-z0-9_."-]+)/i);
  const table = tableMatch ? tableMatch[1].replace(/"/g, '') : null;
  return { type, table, normalized };
}

async function inspectQuery({ sql, params = [], rowCount = 0, userId = null, ip = null }) {
  const info = classifyQuery(sql);
  const meta = { table: info.table, rowCount, paramsCount: params.length, ip };

  if (info.type === 'select' && rowCount >= BULK_ROW_THRESHOLD) {
    logEvent('BULK_EXPORT', meta);
    await writeAuditLog({ userId, action: 'BULK_EXPORT', targetTable: info.table, ip, meta }).catch(() => {});
    await triggerAlert('BULK_EXPORT', meta);
  }

  if (info.table && SENSITIVE_TABLES.has(info.table)) {
    logEvent('SENSITIVE_TABLE_ACCESS', meta);
  }

  return info;
}

module.exports = { BULK_ROW_THRESHOLD, classifyQuery, inspectQuery };
