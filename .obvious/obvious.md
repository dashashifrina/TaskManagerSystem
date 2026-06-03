# Repo guidance

## Codebase Map

See `.obvious/codebase-map.md`.

## Rules

<!-- synthesized from: README.md, CONTRIBUTING.md (agent-relevant rules only) -->

- **Style:** Follow PEP 8, use type hints, and write tests for all new code.
- **Commits:** Use conventional commits — `feat:`, `fix:`, `test:` prefixes.
- **PRs:** Fork → feature branch → PR against `master`. Branch pattern: `feature/xyz`.
- **Testing:** All PRs must include tests. GitHub Actions enforces 90%+ coverage.
- **Security:** Custom regex validators enforce input formats; middleware blocks oversized requests (25 MB limit).
- **Roles:** Task/project write operations are gated by role (Admin > Moderator > Member > Viewer). Always check permissions before mutating project resources.
- **JWT tokens:** Use `Bearer <access_token>` header. Refresh via `/api/v1/account/token/refresh/`. Logout blacklists the refresh token.

## Local Verification

> **Warning:** Running full-repo tests exercises the database. Ensure PostgreSQL is running and `.env` is configured before running tests.

### Verified Commands

- **Test:** `coverage run --source='.' manage.py test api.tests` — verified, 74 tests pass
- **Test (scoped):** `python manage.py test api.tests.test_tasks` — verified
- **Coverage report:** `coverage report -m` — verified

### Scoped Workflow

Run these commands to verify changed files without triggering a full-repo scan:

1. **Typecheck changed files:** not_supported (no mypy/pyright configured)
2. **Lint changed files:** not_supported (no flake8/ruff configured in repo)
3. **Test changed files:** `python manage.py test api.tests.<module>` — e.g. `api.tests.test_tasks`

## Sandbox Snapshot

- **Snapshot ID:** `67qrti7q9j40q4haslqj:default`
- **Captured:** `2026-06-03T17:02:52.708Z`
- **Dev stack healthy:** yes

## Bibliography

5 nodes upserted (0 reused):
- `taskmanagersystem-api` (system) — root node
- `taskmanagersystem-postgres` (infrastructure) — child of api
- `taskmanagersystem-tasks` (feature) — child of api
- `taskmanagersystem-projects` (feature) — child of api
- `taskmanagersystem-jwt-auth` (feature) — child of api

## Security Scan

> **Note:** security_scan_not_triggered — repository `dashashifrina/TaskManagerSystem` not registered in Autobuild workspace. Trigger manually using the trigger_security_onboarding tool with commit SHA `259ba11a6dfb71ac4017057ddf95e4ac8e65c272` after connecting the repo in Settings → Repositories.

## Runbooks

[Populated by autobuild-runbooks skill when requested. See `.obvious/runbooks/` after that skill runs.]
