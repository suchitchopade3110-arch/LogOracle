# User DB Security — Full Project Structure

```
secure-db-project/
├── src/
│   ├── config/
│   │   ├── db.js                  # DB connection + TLS enforced
│   │   ├── secrets.js             # Vault / env secrets loader
│   │   └── security.js            # Global security config
│   │
│   ├── middleware/
│   │   ├── auth.js                # JWT verify + MFA check
│   │   ├── rateLimit.js           # Brute force protection
│   │   ├── inputSanitize.js       # Input validation layer
│   │   └── rbac.js                # Role-based access control
│   │
│   ├── db/
│   │   ├── queries.js             # Parameterized queries ONLY
│   │   ├── audit.js               # DB audit log writer
│   │   └── honeytoken.js          # Honeytoken trap records
│   │
│   ├── crypto/
│   │   ├── hash.js                # bcrypt/argon2 password hashing
│   │   ├── encrypt.js             # AES-256 column encryption
│   │   └── keyManager.js          # Key rotation logic
│   │
│   ├── monitoring/
│   │   ├── logger.js              # Structured log writer (ELK-ready)
│   │   ├── alerting.js            # Anomaly alert dispatcher
│   │   └── dam.js                 # DB Activity Monitor hooks
│   │
│   ├── backup/
│   │   ├── backup.js              # Encrypted backup runner
│   │   └── restore.js             # Verified restore logic
│   │
│   └── incident/
│       ├── playbook.js            # IR phase runner
│       ├── containment.js         # Isolate + revoke on breach
│       └── notify.js              # Alert team on incident
│
├── tests/
│   ├── security/
│   │   ├── injection.test.js      # SQL injection test suite
│   │   ├── auth.test.js           # Auth bypass tests
│   │   └── rbac.test.js           # Permission boundary tests
│   └── backup/
│       └── restore.test.js        # Monthly restore verification
│
├── infra/
│   ├── docker-compose.yml         # DB in isolated network
│   ├── nginx.conf                 # WAF + rate limit at edge
│   └── vault/
│       └── vault-config.hcl       # HashiCorp Vault config
│
├── logs/                          # Audit + app logs (gitignored)
├── .env.example                   # Template — no real secrets
├── .gitignore                     # Ignore .env, logs, keys
└── README.md
```
