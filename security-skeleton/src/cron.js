// src/cron.js — run alongside app or as a separate process.

const { runBackup } = require('./backup/backup');

const BACKUP_HOUR = Number(process.env.BACKUP_HOUR || 2);
const BACKUP_MINUTE = Number(process.env.BACKUP_MINUTE || 0);
let lastRunDate = null;

setInterval(async () => {
  const now = new Date();
  const runDate = now.toISOString().slice(0, 10);
  const due = now.getHours() === BACKUP_HOUR && now.getMinutes() === BACKUP_MINUTE;

  if (due && lastRunDate !== runDate) {
    lastRunDate = runDate;
    await runBackup().catch((err) => console.error('[CRON] backup failed:', err.message));
  }
}, 60_000);
