# PROD_RUNBOOK.md — 3 remaining prod tasks

## Task 1: Seed Vault + enable VAULT_REQUIRED

```bash
# 1. Start stack (Vault must be up)
docker compose --env-file .env -f infra/docker-compose.yml up -d

# 2. Seed
chmod +x scripts/vault_seed.sh && ./scripts/vault_seed.sh

# 3. Verify a secret
curl -H "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/secret/data/logoracle/groq

# 4. Enable enforcement
#    In .env: set VAULT_REQUIRED=true
#    Then:
docker compose --env-file .env -f infra/docker-compose.yml restart app

# 5. Check logs — should see no "VAULT_REQUIRED" errors
docker compose --env-file .env -f infra/docker-compose.yml logs app | grep -i vault
```

---

## Task 2: Replace self-signed TLS certs

**Option A — No domain (demo/localhost):**
```bash
chmod +x scripts/tls_setup.sh
./scripts/tls_setup.sh          # generates cert with SANs
docker compose --env-file .env -f infra/docker-compose.yml restart nginx
```

**Option B — Real domain:**
```bash
DOMAIN=yourdomain.com ./scripts/tls_setup.sh
docker compose --env-file .env -f infra/docker-compose.yml restart nginx
```

Verify:
```bash
curl -v https://localhost:8443/health 2>&1 | grep "SSL certificate"
```

---

## Task 3: Backup cron as persistent process

Already wired in docker-compose.yml as `backup-cron` service.

```bash
# Start (runs immediately then every 24h)
docker compose --env-file .env -f infra/docker-compose.yml up -d backup-cron

# Check it ran
docker compose --env-file .env -f infra/docker-compose.yml logs backup-cron

# Manual backup now
docker compose --env-file .env -f infra/docker-compose.yml exec backup-cron /backup.sh

# List backups
ls -lh backups/
```

Backups saved to `./backups/logoracle_YYYYMMDD_HHMMSS.sql.gz`.
7-day retention — older files pruned automatically.

---

## Full prod bring-up order

```bash
# 1. TLS certs first (nginx needs them at start)
./scripts/tls_setup.sh

# 2. Start all services
docker compose --env-file .env -f infra/docker-compose.yml up -d

# 3. Seed Vault
./scripts/vault_seed.sh

# 4. Set VAULT_REQUIRED=true in .env
# 5. Restart app
docker compose --env-file .env -f infra/docker-compose.yml restart app

# 6. Verify all green
docker compose --env-file .env -f infra/docker-compose.yml ps
curl -k https://localhost:8443/health
```
