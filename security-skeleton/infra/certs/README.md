# PostgreSQL TLS Certs

Place deployment certificates here before starting the stack:

- `server.crt`
- `server.key`

Keep private keys out of Git. The repository `.gitignore` excludes `*.key`, `*.pem`, and `*.crt`.

For local-only testing, generate a self-signed pair and set strict permissions:

```bash
openssl req -new -x509 -days 365 -nodes \
  -out infra/certs/server.crt \
  -keyout infra/certs/server.key \
  -subj "/CN=db"
chmod 600 infra/certs/server.key
```
