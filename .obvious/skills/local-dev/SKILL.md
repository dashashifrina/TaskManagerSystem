---
name: local-dev
version: 1.0.0
description: Bring this repo's local development environment up from scratch.
category: local-dev
triggers:
  - local dev setup
  - run repo locally
  - start dev server
  - bring up local stack
author: autobuild-setup
created: 2026-06-03
---

## Prerequisites

- Python 3.11+ (verified with Python 3.13.13 on install date)
- PostgreSQL 13+ (verified with PostgreSQL 17)
- pip (package manager)
- Git


## Install

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install PostgreSQL if not present
sudo apt-get install -y postgresql postgresql-client
sudo service postgresql start

# Create database
sudo -u postgres psql -c "CREATE DATABASE taskmanager_db;"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'password';"
```


## Environment

Create a .env file in the repo root (gitignored, never commit):

  DEBUG=True
  SECRET_KEY=local-dev-secret-key-change-this
  DB_NAME=taskmanager_db
  DB_USER=postgres
  DB_PASSWORD=password
  DB_HOST=localhost
  DB_PORT=5432

Required vars: SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
Optional vars: ALLOWED_HOSTS (default: localhost,127.0.0.1,0.0.0.0), JWT_ACCESS_TOKEN_LIFETIME (minutes, default: 15), JWT_REFRESH_TOKEN_LIFETIME (days, default: 1), ADMIN_URL (default: admin/)


## Start

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 8000
```

Server: http://127.0.0.1:8000
API base: http://127.0.0.1:8000/api/v1/
Swagger: http://127.0.0.1:8000/swagger/
ReDoc: http://127.0.0.1:8000/redoc/


## Verify Primary User Flow

Primary flow: Register -> Login -> Create task -> List tasks

1. GET /api/v1/status/ -- Expected: {"status":"ok","version":"1.0.0"}
2. POST /api/v1/account/register/ with {"email":"...","username":"...","password":"...","password2":"..."}
3. POST /api/v1/account/login/ with {"email":"...","password":"..."} -- returns {access, refresh} JWT tokens
4. POST /api/v1/tasks/ with Authorization: Bearer ACCESS_TOKEN and {"title":"...","priority":"M","due_date":"2026-12-31"}
   Note: priority values are L (Low), M (Medium), H (High)
5. GET /api/v1/tasks/ with Authorization: Bearer ACCESS_TOKEN -- returns paginated task list

All five steps verified on 2026-06-03. Evidence in .obvious-install/screenshots/primary-flow/.


## Verified Commands
- Typecheck: not_supported (no mypy/pyright configured)
- Lint: not_supported (no flake8/ruff configured)
- Test: coverage run --source=. manage.py test api.tests (74 tests pass)
- Scoped variants for changed files only — see the LOCAL-DEV § Capture proof phase.

## Sandbox Snapshot
- snapshotId: `67qrti7q9j40q4haslqj:default` — restoring this snapshot reproduces the verified-healthy state from install.

## Known Blockers / Workarounds

- Docker not available on this sandbox. Used native PostgreSQL install instead of docker-compose.
- pip install -r requirements.txt works directly without pip-sync.
- The repo .gitignore includes "*.md" -- .obvious/ markdown files are committed regardless as repo contract files, not generated artifacts.

