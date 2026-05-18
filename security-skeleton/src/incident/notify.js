// src/incident/notify.js
// Alert security team through configured channels.

const { triggerAlert } = require('../monitoring/alerting');

async function alertTeam(incident) {
  await triggerAlert(`IR_${incident.type}`, {
    incidentId: incident.id,
    severity: incident.severity,
    timestamp: incident.timestamp,
    ...incident.meta,
  });
}

module.exports = { alertTeam };
