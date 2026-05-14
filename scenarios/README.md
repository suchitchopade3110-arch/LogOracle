# Demo Scenarios

Each JSON file is a one-click demo payload. Use `endpoint` and `payload` to call the backend, then compare the response with the `expected` block.

For log demos:

```bash
curl -X POST http://127.0.0.1:8001/analyze/log \
  -H "Content-Type: application/json" \
  -d @scenarios/01_ssh_bruteforce.json
```

For the UI, read `title`, `category`, `severity`, and `payload` to populate demo buttons.
