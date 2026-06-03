# Codebase Map

| Directory | Purpose |
|---|---|
| `TaskManagerSystem` | Django project config — settings, URLs, WSGI/ASGI, middleware |
| `api` | API entry point — shared URLs, views, mixins, validators, tests |
| `api/tests` | Full test suite — covers tasks, projects, users, security, permissions |
| `users` | User model, registration/login/logout views, JWT auth service |
| `tasks` | Task model, CRUD views, category model, filtering |
| `projects` | Project model, role-based membership, share link invitation system |
| `static` | Static assets directory |
| `.github/workflows` | CI — Django test suite, Docker build, coverage reporting |
