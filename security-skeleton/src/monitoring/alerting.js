// src/monitoring/alerting.js
// Dispatch alerts on anomalies — Slack / PagerDuty / email

const axios = require('axios');

const SLACK_WEBHOOK = process.env.SLACK_SECURITY_WEBHOOK;

async function triggerAlert(type, meta = {}) {
  const msg = {
    text: `🚨 *SECURITY ALERT: ${type}*`,
    attachments: [{
      color: 'danger',
      fields: Object.entries(meta).map(([k, v]) => ({ title: k, value: String(v), short: true })),
      footer: `Triggered at ${new Date().toISOString()}`,
    }],
  };

  // Slack
  if (SLACK_WEBHOOK) {
    await axios.post(SLACK_WEBHOOK, msg).catch(err =>
      console.error('[ALERT] Slack failed:', err.message)
    );
  }

  // Extend: PagerDuty, OpsGenie, email etc.
  console.error(`[SECURITY ALERT] ${type}`, meta);
}

// Alert types reference:
// BRUTE_FORCE_ATTEMPT    — rate limit hit on login
// INVALID_TOKEN          — bad JWT
// PRIVILEGE_ESCALATION   — role mismatch
// HONEYTOKEN_ACCESS      — trap record accessed (critical)
// BULK_EXPORT            — large SELECT detected
// OFF_HOURS_ACCESS       — DB access outside business hours
// BACKUP_INTEGRITY_FAIL  — restore checksum mismatch

module.exports = { triggerAlert };
