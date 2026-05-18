// src/db/queries.js
// ALL queries parameterized — string concat = instant fail in review

const db = require('../config/db');
const { logQuery } = require('../monitoring/logger');
const { inspectQuery } = require('../monitoring/dam');

async function getUserById(id) {
  const sql = 'SELECT id, email, role, created_at FROM users WHERE id = $1';
  const { rows } = await db.query(sql, [id]);
  logQuery('getUserById', { id });
  await inspectQuery({ sql, rowCount: rows.length }).catch(() => {});
  return rows[0] || null;
}

async function getUserByEmail(email) {
  const sql = 'SELECT id, email, password_hash, role FROM users WHERE email = $1';
  const { rows } = await db.query(sql, [email.toLowerCase().trim()]);
  await inspectQuery({ sql, rowCount: rows.length }).catch(() => {});
  return rows[0] || null;
}

async function createUser({ email, passwordHash, role = 'user' }) {
  const sql = `
    INSERT INTO users (email, password_hash, role, created_at)
    VALUES ($1, $2, $3, NOW())
    RETURNING id, email, role
  `;
  const { rows } = await db.query(sql, [email, passwordHash, role]);
  logQuery('createUser', { email });
  return rows[0];
}

async function updatePassword(userId, newHash) {
  const sql = `
    UPDATE users SET password_hash = $1, updated_at = NOW()
    WHERE id = $2
  `;
  await db.query(sql, [newHash, userId]);
  logQuery('updatePassword', { userId });
}

// ❌ NEVER DO THIS — shown for reference only
// const bad = `SELECT * FROM users WHERE email = '${email}'`; // SQL INJECTION

module.exports = { getUserById, getUserByEmail, createUser, updatePassword };
