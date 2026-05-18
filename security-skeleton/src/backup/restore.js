// src/backup/restore.js
// Verify checksum, decrypt, then pg_restore.

const crypto   = require('crypto');
const fs       = require('fs');
const path     = require('path');
const { execFile } = require('child_process');
const { logEvent }    = require('../monitoring/logger');
const { triggerAlert } = require('../monitoring/alerting');

function verifyChecksum(encFile) {
  const storedChecksum   = fs.readFileSync(`${encFile}.sha256`, 'utf8').trim();
  const data             = fs.readFileSync(encFile);
  const computedChecksum = crypto.createHash('sha256').update(data).digest('hex');

  if (storedChecksum !== computedChecksum) {
    logEvent('BACKUP_INTEGRITY_FAIL', { file: encFile });
    triggerAlert('BACKUP_INTEGRITY_FAIL', {
      file: encFile,
      message: 'Checksum mismatch; backup may be tampered',
    });
    throw new Error('Backup integrity check failed');
  }

  logEvent('BACKUP_INTEGRITY_OK', { file: encFile });
  return true;
}

function decryptFile(encFile, keyHex) {
  const raw    = fs.readFileSync(encFile);
  const iv     = raw.slice(0, 16);           // prepended in backup.js
  const body   = raw.slice(16);
  const key    = Buffer.from(keyHex, 'hex');
  const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
  return Buffer.concat([decipher.update(body), decipher.final()]);
}

function pgRestore(sqlBuffer, dbName, dbUser) {
  return new Promise((res, rej) => {
    const child = execFile(
      'psql',
      ['-U', dbUser, '-d', dbName, '-f', '-'],
      { shell: false },
      (err) => { if (err) return rej(err); res(); }
    );
    child.stdin.write(sqlBuffer);
    child.stdin.end();
    child.stderr.on('data', (d) => logEvent('RESTORE_PSQL_STDERR', { msg: String(d) }));
  });
}

async function restore(encFile, keyHex) {
  if (!keyHex) throw new Error('[RESTORE] key required');

  verifyChecksum(encFile);
  logEvent('RESTORE_STARTED', { file: encFile });

  const sqlBuffer = decryptFile(encFile, keyHex);
  await pgRestore(sqlBuffer, process.env.DB_NAME, process.env.DB_USER);

  logEvent('RESTORE_COMPLETE', { file: encFile });
}

module.exports = { verifyChecksum, restore };
