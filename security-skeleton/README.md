# User DB Security Skeleton

Full implementation of OWASP + MITRE-aligned user DB protection.

## Stack
- Node.js (Express)
- PostgreSQL 16 (TLS enforced)
- Redis (rate limit store + session)
- HashiCorp Vault (secrets)
- Docker (network isolation)

---

## Quick Start

Requires Node.js 20 LTS. If the machine has an older Node, install and select Node 20 first:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
node --version  # must print v20.x
```

```bash
cp .env.example .env          # fill all values
mkdir -p infra/certs          # add server.crt + server.key; see infra/certs/README.md

# Load .env into the shell for docker compose, psql, and local npm commands.
export $(grep -v '^#' .env | xargs)

docker compose -f infra/docker-compose.yml up -d  # start isolated stack
npm install
npm run check:db              # verify DB connects
psql -U $DB_USER -h localhost -d $DB_NAME < infra/schema.sql  # init tables
npm start                     # boot app after Vault preload
```

If dependencies were previously installed with an older Node version:

```bash
rm -rf node_modules package-lock.json
npm install
```

---

## Implementation Checklist

### Prevention
- [ ] All queries use parameterized statements (`src/db/queries.js`)
- [ ] Argon2id password hashing (`src/crypto/hash.js`)
- [ ] AES-256-GCM column encryption for PII (`src/crypto/hash.js`)
- [ ] TLS enforced on DB connection (`src/config/db.js`)
- [ ] MFA middleware on sensitive routes (`src/middleware/auth.js`)
- [ ] RBAC roles enforced (`src/middleware/auth.js`)
- [ ] Rate limiting on login + password reset (`src/middleware/rateLimit.js`)
- [ ] Secrets in Vault, never in code (`src/config/secrets.js`)
- [ ] DB in private Docker network (no exposed port) (`infra/docker-compose.yml`)
- [ ] Least-privilege DB role (`infra/schema.sql`)

### Detection
- [ ] Structured JSON audit log — ELK ready (`src/monitoring/logger.js`)
- [ ] DB audit log table — append-only (`infra/schema.sql`)
- [ ] Honeytoken records planted (`src/db/honeytoken.js`)
- [ ] Slack/PagerDuty alerts wired (`src/monitoring/alerting.js`)
- [ ] Alert types: brute force, bad JWT, privilege escalation, honeytoken, bulk export

### Backup + Recovery
- [ ] Encrypted backup with checksum (`src/backup/backup.js`)
- [ ] Backup restore verification (`src/backup/restore.js`)
- [ ] Backup cron scheduled (daily minimum)
- [ ] Offsite storage wired (S3 / GCS)
- [ ] Monthly restore test documented

### Incident Response
- [ ] NIST 6-phase playbook wired (`src/incident/playbook.js`)
- [ ] Containment: user lock + session revoke + IP block (`src/incident/playbook.js`)
- [ ] Team notification on CRITICAL/HIGH severity
- [ ] Post-mortem log on every incident

---

## Threat → File Map

| Threat | File |
|--------|------|
| SQL Injection | `src/db/queries.js` |
| Brute Force | `src/middleware/rateLimit.js` |
| Broken Auth | `src/middleware/auth.js` |
| Credential Dump | `src/crypto/hash.js` (hashed creds useless) |
| Insider Threat | `src/monitoring/logger.js` + `src/db/audit.js` |
| Honeytoken | `src/db/honeytoken.js` |
| Backup Attack | `src/backup/backup.js` + `restore.js` |
| MitM | `src/config/db.js` (TLS) |
| Incident | `src/incident/playbook.js` |

---

## Extend Later
- Add WAF (Nginx + ModSecurity) in `infra/nginx.conf`
- Wire SIEM (Splunk / ELK) to consume `logs/audit.log`
- Add DAM (Imperva / Guardium) hooks in `src/monitoring/dam.js`
- Key rotation schedule in `src/crypto/keyManager.js`
- PITR (Point-in-Time Recovery) via pgBackRest
