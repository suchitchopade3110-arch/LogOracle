// src/backup/backup.js
// Encrypted DB backup — run via cron, store offsite

const { execFile } = require('child_process');
const crypto   = require('crypto');
const fs       = require('fs');
const path     = require('path');
const { logEvent }    = require('../monitoring/logger');
const { triggerAlert } = require('../monitoring/alerting');

const BACKUP_DIR     = process.env.BACKUP_DIR || '/backups';
const BACKUP_KEY = process.env.BACKUP_ENCRYPTION_KEY;
if (!BACKUP_KEY) throw new Error('[BACKUP] BACKUP_ENCRYPTION_KEY not set');
const DB_NAME        = process.env.DB_NAME;
const DB_USER        = process.env.DB_USER;

async function runBackup() {
  const timestamp  = new Date().toISOString().replace(/[:.]/g, '-');
  const dumpFile   = path.join(BACKUP_DIR, `backup-${timestamp}.sql`);
  const encFile    = `${dumpFile}.enc`;

  try {
    // 1. Dump
    await dumpDatabase(dumpFile);

    // 2. Encrypt (AES-256-CBC via openssl for simplicity)
    const key = Buffer.from(BACKUP_KEY, 'hex');
    const iv  = crypto.randomBytes(16);
    await encryptFile(dumpFile, encFile, key, iv);

    // 3. Checksum
    const checksum = fileChecksum(encFile);
    fs.writeFileSync(`${encFile}.sha256`, checksum);

    // 4. Delete plaintext dump
    fs.unlinkSync(dumpFile);

    logEvent('BACKUP_SUCCESS', { file: encFile, checksum });
    // Extend: upload encFile to S3 / offsite storage here

  } catch (err) {
    logEvent('BACKUP_FAIL', { error: err.message });
    triggerAlert('BACKUP_FAIL', { error: err.message });
  }
}

function encryptFile(src, dest, key, iv) {
  return new Promise((res, rej) => {
    const cipher   = crypto.createCipheriv('aes-256-cbc', key, iv);
    const input    = fs.createReadStream(src);
    const output   = fs.createWriteStream(dest);
    // Prepend IV to file
    output.write(iv);
    input.pipe(cipher).pipe(output);
    output.on('finish', res);
    output.on('error', rej);
  });
}

function fileChecksum(filePath) {
  const data = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(data).digest('hex');
}

function dumpDatabase(dumpFile) {
  return new Promise((res, rej) => {
    const output = fs.createWriteStream(dumpFile, { flags: 'wx' });
    const child = execFile('pg_dump', ['-U', DB_USER, DB_NAME], { shell: false }, (err) => {
      if (err) return rej(err);
      return res();
    });
    child.stdout.pipe(output);
    child.stderr.on('data', (chunk) => logEvent('BACKUP_PGDUMP_STDERR', { message: String(chunk) }));
  });
}

module.exports = { runBackup };
