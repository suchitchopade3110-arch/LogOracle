// src/incident/playbook.js
// NIST 6-phase IR — Prepare → Identify → Contain → Eradicate → Recover → Learn

const { logEvent }    = require('../monitoring/logger');
const { triggerAlert } = require('../monitoring/alerting');
const containment      = require('./containment');
const notify           = require('./notify');

// Severity levels
const SEVERITY = { LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4 };

async function runPlaybook(incidentType, meta = {}) {
  const incident = {
    id:        `INC-${Date.now()}`,
    type:      incidentType,
    severity:  classifySeverity(incidentType),
    meta,
    timestamp: new Date().toISOString(),
    phases:    [],
  };

  logEvent('IR_STARTED', { incidentId: incident.id, type: incidentType });

  // Phase 1 — IDENTIFY
  incident.phases.push({ phase: 'IDENTIFY', status: 'done', at: new Date().toISOString() });

  // Phase 2 — CONTAIN
  if (incident.severity >= SEVERITY.HIGH) {
    await containment.isolate(meta);
    incident.phases.push({ phase: 'CONTAIN', status: 'done', at: new Date().toISOString() });
  }

  // Phase 3 — NOTIFY team
  await notify.alertTeam(incident);

  // Phase 4 — ERADICATE (manual, but logged)
  logEvent('IR_ERADICATE_REQUIRED', { incidentId: incident.id, action: 'Manual eradication needed' });

  // Phase 5 — RECOVER (trigger restore if data loss)
  if (incidentType === 'DATA_LOSS' || incidentType === 'RANSOMWARE') {
    logEvent('IR_RECOVER_TRIGGER', { incidentId: incident.id });
    // import { restore } from '../backup/restore'; — trigger here
  }

  // Phase 6 — LESSONS LEARNED (log for post-mortem)
  logEvent('IR_POSTMORTEM_NEEDED', { incidentId: incident.id, meta });

  return incident;
}

function classifySeverity(type) {
  const critical = ['RANSOMWARE', 'DATA_LOSS', 'HONEYTOKEN_ACCESS', 'MASS_EXFIL'];
  const high     = ['BRUTE_FORCE_SUCCESS', 'PRIVILEGE_ESCALATION', 'CREDENTIAL_DUMP'];
  const medium   = ['BRUTE_FORCE_ATTEMPT', 'INVALID_TOKEN', 'RATE_LIMIT_HIT'];

  if (critical.includes(type)) return SEVERITY.CRITICAL;
  if (high.includes(type))     return SEVERITY.HIGH;
  if (medium.includes(type))   return SEVERITY.MEDIUM;
  return SEVERITY.LOW;
}

module.exports = { runPlaybook };
