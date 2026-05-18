// tests/static-security.test.js
// Run with: node tests/static-security.test.js

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const requiredFiles = [
  '.gitignore',
  'infra/nginx.conf',
  'src/app.js',
  'src/cron.js',
  'src/middleware/inputSanitize.js',
  'src/db/audit.js',
  'src/db/honeytoken.js',
  'src/monitoring/dam.js',
  'src/crypto/keyManager.js',
  'src/crypto/encrypt.js',
  'src/backup/restore.js',
  'src/incident/containment.js',
  'src/incident/notify.js',
];

for (const file of requiredFiles) {
  assert.ok(fs.existsSync(path.join(root, file)), `${file} should exist`);
}

const queries = fs.readFileSync(path.join(root, 'src/db/queries.js'), 'utf8');
const activeQueryLines = queries
  .split('\n')
  .filter((line) => !line.trim().startsWith('//'))
  .join('\n');
assert.ok(!activeQueryLines.includes('${email}'), 'active SQL must not interpolate email');
assert.ok(queries.includes('WHERE email = $1'), 'login query must be parameterized');

const gitignore = fs.readFileSync(path.join(root, '.gitignore'), 'utf8');
for (const pattern of ['.env', 'logs/', '*.key', '*.pem']) {
  assert.ok(gitignore.includes(pattern), `.gitignore should include ${pattern}`);
}

const app = fs.readFileSync(path.join(root, 'src/app.js'), 'utf8');
assert.ok(app.indexOf('await loadFromVault()') < app.indexOf("require('./middleware/rateLimit')"), 'Vault should load before DB-touching modules');

const compose = fs.readFileSync(path.join(root, 'infra/docker-compose.yml'), 'utf8');
assert.ok(compose.includes('./certs:/etc/nginx/certs:ro'), 'nginx TLS cert directory should be mounted');

const cron = fs.readFileSync(path.join(root, 'src/cron.js'), 'utf8');
assert.ok(cron.includes('runBackup'), 'cron should schedule runBackup');

console.log('static security checks ok');
