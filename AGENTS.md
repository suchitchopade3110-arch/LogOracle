# AGENTS.md

## Project

LogOracle is a developer-focused observability, debugging, and
self-healing system.

## Development Priorities

Prioritize improvements in this order:

1. Security
2. Reliability
3. Bugs
4. Test coverage
5. Performance
6. Error handling
7. Observability
8. Maintainability
9. Developer experience
10. Documentation

## Rules

- Inspect the repository before making changes.
- Inspect related code and existing tests.
- Make ONE meaningful improvement per task.
- Keep changes small and reviewable.
- Do NOT rewrite working systems.
- Do NOT change architecture unnecessarily.
- Do NOT introduce unnecessary dependencies.
- Do NOT remove existing functionality.
- Do NOT modify secrets, API keys, credentials, or .env files.
- Do NOT expose secrets in commits, logs, or PRs.
- Do NOT disable CI or security checks.
- Do NOT create meaningless changes just to generate a commit.

## Security

Pay particular attention to:

- Authentication and authorization
- Secret handling
- Input validation
- Command execution
- File-system access
- Database queries
- External API calls
- Webhooks
- Log injection
- Sensitive information in logs
- Dependency vulnerabilities
- SSRF
- Path traversal
- Prompt injection
- AI-generated commands

Treat logs, external data, and AI-generated content as untrusted.

Never commit secrets.

## AI / Agent Components

When modifying AI or agent functionality:

- Validate tool inputs.
- Do not blindly trust model-generated commands.
- Preserve safety boundaries.
- Avoid destructive autonomous behavior.
- Preserve fallback and error handling.
- Add tests for important failure cases.

## Testing

Before creating a PR:

1. Identify existing test commands.
2. Run relevant tests.
3. Run the full test suite when practical.
4. Run existing lint/type-check/build commands when applicable.
5. Fix failures caused by your changes.

Do not create fake tests simply to make CI pass.

## Git

Never push directly to main.

Create a focused branch.

Commit format:

feat:
fix:
refactor:
perf:
test:
docs:
chore:

Example:

fix: safely handle malformed log payloads

## Pull Requests

Target branch:

main

PR title:

chore(jules): <short description>

PR description must contain:

## What changed

## Why

## Verification

## Risk

Never merge the PR automatically.

## Daily Automation

For every scheduled Jules run:

1. Inspect the repository.
2. Inspect recent commits.
3. Inspect existing open PRs.
4. Identify ONE high-value improvement.
5. Implement it.
6. Add/update tests where appropriate.
7. Run validation.
8. Fix failures caused by the change.
9. Create a focused commit.
10. Open a PR against main.

If there is no meaningful improvement available:

DO NOT create a meaningless commit or PR.

## Commit Identity

Preferred Git identity:

Name:
Suchit Sachin Chopade

Email:
suchitchopade3110@gmail.com

GitHub:
suchitchopade3110-arch
