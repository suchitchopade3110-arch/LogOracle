// src/middleware/auth.js
// JWT verify + MFA enforced for sensitive routes

const jwt = require('jsonwebtoken');
const secrets = require('../config/secrets');
const { logEvent } = require('../monitoring/logger');
const { triggerAlert } = require('../monitoring/alerting');

function verifyToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    logEvent('AUTH_FAIL', { reason: 'missing_token', ip: req.ip });
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, secrets.get('JWT_SECRET'), {
      algorithms: ['HS256'],
      issuer: 'your-app',
      audience: 'your-app-users',
    });
    req.user = decoded;
    next();
  } catch (err) {
    logEvent('AUTH_FAIL', { reason: err.message, ip: req.ip });
    triggerAlert('INVALID_TOKEN', { ip: req.ip });
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

// MFA check — apply to sensitive routes (password change, data export)
function requireMFA(req, res, next) {
  if (!req.user?.mfa_verified) {
    logEvent('MFA_FAIL', { userId: req.user?.id, ip: req.ip });
    return res.status(403).json({ error: 'MFA required for this action' });
  }
  next();
}

// Role gate — usage: requireRole('admin')
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!allowedRoles.includes(req.user?.role)) {
      logEvent('AUTHZ_FAIL', { userId: req.user?.id, role: req.user?.role, required: allowedRoles });
      triggerAlert('PRIVILEGE_ESCALATION_ATTEMPT', { userId: req.user?.id });
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}

module.exports = { verifyToken, requireMFA, requireRole };
