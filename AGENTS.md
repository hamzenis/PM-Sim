# Agent guide

This file is the repository-wide operating contract for coding agents. Read it before changing
anything, then read every more-specific `AGENTS.md` between the repository root and the file being
edited. Deeper files override this guide for their directory only.

## Mission and priorities

Make the smallest complete change that satisfies the request while preserving security, data
integrity, deterministic simulation behavior, accessibility, and documented contracts. Prefer
verified repository facts over assumptions. If instructions conflict, follow them in this order:

1. system, platform, and explicit user instructions;
2. the nearest applicable `AGENTS.md`;
3. repository documentation and established local patterns.

Do not silently broaden scope, rewrite unrelated code, or weaken a check to make it pass. Never
discard uncommitted work that you did not create.

## Repository orientation

- `backend/` is the Python 3.13 FastAPI, SQLAlchemy, Alembic, and deterministic simulation
  application. **Read `backend/AGENTS.md` before touching it.**
- `frontend/` is the React 19, Chakra UI, and Vite application. **Read `frontend/AGENTS.md` before
  touching it.**
- `docs/` and the root Markdown files own cross-application and contributor guidance. Keep root
  documentation concise and link into the backend or frontend indexes for implementation details.
- `scripts/` owns repository automation. Keep scripts deterministic, non-interactive, runnable from
  the documented working directory, and based on repository-relative paths rather than a developer's
  environment.
- `.github/workflows/` owns CI. Preserve lockfile-driven setup and keep its commands aligned with the
  checks documented below; pin third-party actions to an intentional reviewed version.
- `scripts/check_docs.py` validates documentation links and documented application contracts.
- `.github/workflows/application-tests.yml` is the authoritative CI command sequence.
- `CONTRIBUTING.md` defines branch, commit, review, and documentation expectations.

Use `rg` and `rg --files` for discovery. Inspect the implementation, its tests, and the relevant
documentation before editing; names alone are not proof of behavior.

## Working method

1. Check `git status --short --branch` and identify pre-existing changes.
2. Restate the acceptance criteria internally and locate the narrowest owning modules.
3. Read neighboring code and tests, plus the applicable documentation and agent instructions.
4. Make a focused patch. Keep public contracts backward compatible unless the task explicitly
   changes them.
5. Add or update tests for observable behavior, including failure and authorization paths where
   relevant. A bug fix should normally include a regression test.
6. Update documentation in the same change when behavior, configuration, commands, routes, data,
   schema, operations, or user workflows change.
7. Run focused checks first, then the applicable full checks below. Report failures honestly; do not
   describe a check as passing if it was not run.
8. Review `git diff --check`, the complete diff, and `git status` before committing. Do not commit
   databases, environment files, credentials, generated reports, build output, or unrelated files.

## Repository checks

Run commands from the directory shown.

```bash
# Repository root: documentation and documented-contract validation
uv run --project backend python scripts/check_docs.py

# backend/
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run pytest

# frontend/
npm ci
npm ls --depth=0
npm run lint
npm test
npm run build
npm run test:visual
```

Use the smallest relevant subset while iterating, but run every affected suite before handoff. A
documentation-only change needs the documentation checker and `git diff --check`; it does not
require unrelated application suites unless the changed instructions claim those commands work and
that claim needs validation. For perceptible UI changes, test desktop and mobile behavior and
capture/review a screenshot. Do not update visual baselines without explaining every changed pixel.

Changes to repository automation or CI require direct coverage of the affected script or workflow
plus the application checks whose setup or invocation changed. Keep local documentation and CI in
sync; neither is a substitute for the other.

## Cross-cutting engineering rules

- Preserve dependency direction and package ownership; do not bypass a service boundary for
  convenience.
- Validate at trust boundaries and enforce authorization server-side. Do not log or commit secrets,
  passwords, session tokens, private scenario content, or personal student data.
- Keep operations deterministic: use fixed seeds, explicit UTC timestamps, stable ordering, and
  isolated fixtures. Do not make tests depend on wall-clock timing, network availability, execution
  order, or a developer database.
- Use lockfile-driven installs (`uv sync --locked`, `npm ci`). Do not change a lockfile unless the
  dependency change is intentional.
- Follow the existing style in touched files. Avoid drive-by formatting and blanket lint disables.
- Comments should explain invariants or non-obvious decisions, not narrate syntax.
- Treat API payloads, database migrations, scenario JSON, persisted engine state, and frontend API
  adapters as versioned contracts. Update both producers and consumers when a contract changes.
- Prefer an ADR under `backend/docs/adr/` for a durable architectural decision or new cross-package
  boundary; do not create one for a routine local implementation choice.

## Documentation and handoff

Put cross-cutting guidance in the root documentation, backend guidance in `backend/docs/`, and
frontend guidance in `frontend/docs/`. Keep examples executable, links relative, terminology
consistent, and secrets fictional. Do not commit generated OpenAPI or reports unless the repository
explicitly adopts them as reviewed artifacts.

Commits follow `CONTRIBUTING.md`: `<type>: #IssueNumber <present-tense subject>`. If no issue number
was supplied and a commit is required, do not invent one; use a concise conventional subject and
call out the missing issue association in the handoff. A pull request must summarize behavior,
tests, documentation changes (or why none were required), compatibility or migration concerns, and
the required reviewer role.
