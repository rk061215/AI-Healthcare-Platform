# Contributing to AI Healthcare Follow-up Assistant

Thank you for considering contributing to this project. Please read this document thoroughly before submitting any work.

## Table of Contents

- [Development Workflow](#development-workflow)
- [Branch Strategy](#branch-strategy)
- [Commit Conventions](#commit-conventions)
- [Pull Request Checklist](#pull-request-checklist)
- [Code Review Process](#code-review-process)
- [Documentation Update Requirements](#documentation-update-requirements)
- [Getting Help](#getting-help)

---

## Development Workflow

This project follows a **feature-branch workflow** with regular rebasing onto `main`.

### Step-by-step

1. **Pick a task** from the issue tracker or TASKS.md.
2. **Create a branch** from the latest `main`.
3. **Implement** your changes with incremental commits (see [Commit Conventions](#commit-conventions)).
4. **Run tests and quality checks** locally before pushing.
5. **Push and open a Pull Request** against `main`.
6. **Address review feedback** and keep the branch updated with `main`.
7. **Merge** after approval and all checks pass.

### Prerequisites

```bash
# Install pre-commit hooks (required)
cd backend
pre-commit install

# Verify setup
pre-commit run --all-files
```

---

## Branch Strategy

### Naming Convention

```
<type>/<short-description>
```

| Type      | When to Use                     | Example                          |
|-----------|---------------------------------|----------------------------------|
| `feat/`   | New feature or endpoint         | `feat/patient-report-upload`     |
| `fix/`    | Bug fix                         | `fix/appointment-idor-bypass`    |
| `refactor/` | Code restructuring           | `refactor/auth-service`          |
| `chore/`  | Dependencies, config, CI        | `chore/update-bcrypt-version`    |
| `docs/`   | Documentation only              | `docs/api-auth-flow`             |
| `test/`   | Adding or fixing tests          | `test/rate-limit-coverage`       |
| `perf/`   | Performance improvement         | `perf/db-query-optimization`     |

### Branch Rules

- Always branch from `main`.
- Keep branches short-lived (ideally < 3 days).
- Rebase (not merge) `main` into your branch to avoid merge commits.
- Delete the branch after merging.

```bash
# Keep your branch up to date
git fetch origin
git rebase origin/main
# If conflicts arise:
git rebase --abort   # to bail out
git rebase --continue  # after resolving conflicts
```

---

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/) with the following format:

```
<type>(<scope>): <imperative description>

[optional body]

[optional footer]
```

### Types

| Type       | Usage                                   |
|------------|-----------------------------------------|
| `feat`     | A new feature                           |
| `fix`      | A bug fix                               |
| `refactor` | Code change that is neither feat nor fix|
| `test`     | Adding or modifying tests               |
| `docs`     | Documentation changes                   |
| `chore`    | Build, deps, config, CI                 |
| `perf`     | Performance improvement                 |
| `style`    | Formatting, linting only                |

### Scopes

| Scope          | Area                                        |
|----------------|---------------------------------------------|
| `api`          | Route handlers                              |
| `service`      | Business logic layer                        |
| `repository`   | Data access layer                           |
| `model`        | SQLAlchemy models                           |
| `schema`       | Pydantic schemas                            |
| `auth`         | Authentication / authorization              |
| `agent`        | LangGraph agents                            |
| `middleware`   | Middleware (rate limit, CSRF, CORS)         |
| `db`           | Migrations, seed data                       |
| `ui`           | Frontend components                         |
| `store`        | Zustand stores                              |
| `infra`        | Docker, CI/CD, deployment                   |
| `docs`         | Documentation                               |
| `deps`         | Dependency updates                          |

### Examples

```
feat(auth): add refresh token rotation
fix(db): resolve SQLAlchemy metadata reserved name conflict
test(api): add IDOR tests for appointment endpoints
docs(api): document rate limit response format
chore(deps): pin bcrypt to 4.1.3 for passlib compat
refactor(service): extract password validation into utility
```

### Commit Body

Use the body to explain the **what** and **why** (not the how):

```
fix(middleware): skip CSRF check for OPTIONS requests

OPTIONS requests are preflight CORS requests and should not
trigger CSRF validation. Browsers never include custom headers
on preflight requests, so the Origin check is redundant and
may cause false negatives during CORS negotiation.
```

---

## Pull Request Checklist

Before opening a PR, verify the following:

### Required

- [ ] Code compiles and runs without errors
- [ ] All existing tests pass (`pytest -v --cov=app`)
- [ ] New tests cover the change (target >= 80% coverage on new code)
- [ ] Linting passes (`black . && isort . && flake8`)
- [ ] Type checking passes (`mypy app/`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] No secrets, credentials, or tokens in the code
- [ ] No debug code, print statements, or commented-out code
- [ ] `.env.example` updated if new environment variables were added

### Documentation

- [ ] CHANGELOG.md updated under the `[Unreleased]` section
- [ ] TASKS.md updated if the PR completes a tracked task
- [ ] API changes reflected in docstrings and OpenAPI schema
- [ ] Architecture decisions documented in ARCHITECTURE_DECISIONS.md if applicable
- [ ] README.md updated if setup, config, or workflow changed

### Security

- [ ] No new vulnerabilities introduced (verified with `pip-audit` or `npm audit`)
- [ ] Rate limiting considered for new endpoints
- [ ] Input validation in place for new API routes
- [ ] Ownership checks for multi-tenant data access
- [ ] Sensitive data not exposed in response schemas

### Frontend

- [ ] TypeScript strict mode passes (`tsc --noEmit`)
- [ ] No unused imports or variables
- [ ] Responsive design tested on mobile breakpoint
- [ ] Loading, error, and empty states handled
- [ ] Form validation matches server-side rules

---

## Code Review Process

### Review Timeline

| PR Size      | Expected Response |
|-------------|-------------------|
| < 100 lines  | Within 4 hours    |
| 100-300 lines| Within 24 hours   |
| 300-1000 lines| Within 48 hours  |
| > 1000 lines | Consider splitting |

### Reviewer Responsibilities

1. **Read the full diff** — not just the summary.
2. **Verify correctness** — does the code do what it claims?
3. **Check test coverage** — are edge cases covered?
4. **Look for security issues** — injection, IDOR, rate limiting, exposed secrets.
5. **Consider maintainability** — is the code easy to understand and modify?
6. **Test the change** — pull the branch and run it if the change is complex.

### Review Comments Format

Use the following prefixes for clarity:

| Prefix    | Meaning                                  |
|-----------|------------------------------------------|
| `nit:`    | Minor style preference, non-blocking     |
| `blocker:`| Must be fixed before merge               |
| `question:` | Need clarification                     |
| `suggestion:` | Optional improvement                |
| `praise:` | Positive feedback                        |

Example:

```
nit: consider using `Optional[str]` instead of `str | None` for consistency with the rest of the codebase.
```

### Author Responsibilities

- Respond to all comments within 24 hours.
- Mark resolved conversations after pushing changes.
- Keep the PR description up to date as the code evolves.
- Do not self-approve or merge without at least one reviewer.

---

## Documentation Update Requirements

Documentation must be updated in the same PR as the code change. The following files must be kept in sync with the codebase:

### Required Updates

| Change Type                    | Files to Update                                                    |
|--------------------------------|--------------------------------------------------------------------|
| New feature                    | CHANGELOG.md, TASKS.md, README.md (if user-facing)                 |
| API change                     | Docstrings on route handlers, OpenAPI schema (auto), README.md     |
| Database change                | Alembic migration, ARCHITECTURE.md (ERD), models/__init__.py       |
| Config change                  | `.env.example` (backend + root), config.py, ARCHITECTURE.md        |
| Dependency change              | requirements.txt or package.json, CHANGELOG.md                     |
| Architecture decision          | ARCHITECTURE_DECISIONS.md (under project_memory/)                  |
| Security policy change         | SECURITY.md                                                       |
| Workflow/tooling change        | CONTRIBUTING.md, README.md                                         |

### Documentation Standards

- Use Markdown with a table of contents for files longer than 100 lines.
- Keep line length to 100 characters maximum.
- Use fenced code blocks with language identifiers.
- Update the "Last Updated" date in the file header.
- When modifying architecture, update the relevant ASCII diagram.

---

## Getting Help

- **Issues**: Open a GitHub issue with the appropriate label.
- **Discussions**: Use GitHub Discussions for questions and proposals.
- **Security vulnerabilities**: Email the maintainers or open a draft security advisory (see SECURITY.md).

---

*Last updated: 2026-07-11*
