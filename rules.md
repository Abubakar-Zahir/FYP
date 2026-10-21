# rules.md

These rules are binding for everyone, including AI assistants. If a rule blocks you, raise it in the PR instead of working around it.

## 1. Git and PRs

1. `main` is protected. No direct pushes. Every change goes through a PR with at least one approval from a teammate.
2. Branch names: `feat/<area>-<short-name>`, `fix/<area>-<short-name>`, `chore/...`, `docs/...`, `ml/...`. Example: `feat/web-onboarding-form`.
3. Commit messages follow Conventional Commits: `feat(web): add onboarding form`. One logical change per commit.
4. A PR does one thing. Aim for under 400 changed lines. Split larger work.
5. PR description must have: what changed, why, how to test, screenshots for UI changes, and linked task from `progress.md`.
6. The author does not merge their own PR. Squash merge to keep history linear.
7. Rebase on `main` before asking for review. Resolve conflicts yourself.
8. CI must be green before merge: lint, typecheck, tests.

## 2. General code rules

1. Names say what a thing is. No abbreviations except common ones (`id`, `url`, `db`).
2. Functions do one thing and stay short. If a function needs a comment to explain its sections, split it.
3. No dead code, no commented-out code, no `console.log` or `print` left in merged code.
4. Comments explain why, not what. Do not write comments that narrate a change.
5. No magic numbers or strings. Use named constants or config.
6. Handle errors at the right layer. Never swallow an exception silently. Never return `None` to hide a failure.
7. Prefer small pure functions. Keep I/O at the edges.
8. Do not duplicate logic. Three copies means extract.
9. Every TODO has an issue number: `TODO(#42): ...`.

## 3. Python (api and ml)

1. Python version pinned in `pyproject.toml`. Dependencies managed with `uv`. Lockfile committed.
2. Formatting and linting: `ruff` (format and check). Types: `mypy --strict` on `apps/api` and `ml`.
3. Full type hints on every function signature. No bare `Any` without a comment.
4. Pydantic v2 models for every request, response, job payload and DNA record. No raw dicts crossing a boundary.
5. Async all the way in request handlers. Never call blocking code (FFmpeg, Whisper, `requests`) inside `async def`. Use `httpx.AsyncClient` for HTTP.
6. Use dependency injection (`Depends`) for the DB session, current user and settings. No globals.
7. Config comes from environment through one `Settings` class (`pydantic-settings`). No `os.environ` calls elsewhere.
8. Database changes only through Alembic migrations. Never edit a merged migration. Write a new one.
9. `ml/` is plain Python. It must not import `fastapi`, `celery`, `sqlalchemy` or anything from `apps/`. Workers call into `ml/`.
10. ML code takes explicit inputs and returns typed outputs. Fix random seeds. Log model name and version with every prediction.
11. Logging with the standard `logging` module, structured, no PII, no tokens, no full comments in logs.

## 3b. API design

1. Base path `/api/v1`. Nouns for resources, plural: `/reels`, `/scripts`.
2. Long work returns `202` with a `job_id`. The client polls `GET /api/v1/jobs/{id}`.
3. One error shape: `{ "error": { "code": "string", "message": "string", "details": {} } }`. Codes are stable strings.
4. Every list endpoint paginates (`limit`, `cursor`).
5. Every endpoint checks that the resource belongs to the current user.
6. Never change a response shape without updating the frontend in the same PR or versioning it.

## 4. TypeScript and React (web)

1. `strict: true`. No `any`. No `// @ts-ignore` without an explanation and issue number.
2. ESLint and Prettier run in CI. Import order is automatic.
3. Server Components by default. Add `"use client"` only where state, effects or browser APIs are needed.
4. Server state lives in TanStack Query. Local UI state in `useState`. Add a global store only with team agreement.
5. API types are generated from the backend OpenAPI schema. Do not hand-write them.
6. Validate forms with React Hook Form and Zod. Validate data at the boundary.
7. Components are small, typed and have one job. Props are explicit. No prop drilling over 2 levels, use composition.
8. Every data screen has a loading state, an empty state and an error state. No exceptions.
9. Accessibility: semantic HTML, labels on inputs, keyboard navigation, visible focus, contrast AA. Mobile first, test at 375 px width.
10. No inline styles. Use Tailwind classes and design tokens defined in `tailwind.config`.
11. No secrets in client code. Only `NEXT_PUBLIC_` variables are exposed, and only if safe to expose.

## 5. Testing

1. New logic ships with tests. Bug fixes ship with a test that fails before the fix.
2. Backend: `pytest` unit tests for services, API tests with `httpx` against a test DB. External APIs (Instagram, LLM, Pexels) are mocked.
3. Frontend: Vitest and Testing Library for components and hooks. Playwright for the main flows.
4. ML: tests for data loaders, feature functions and metrics. Model quality is tracked in an evaluation report, not in unit tests.
5. Tests must not call the real Instagram API or a paid LLM API in CI.

## 6. Security and privacy

1. No secrets in git. `.env.example` lists variable names only. Rotate any secret that leaks.
2. Instagram tokens are encrypted before they reach the database. The key is an environment variable.
3. Validate and limit uploads: file type, size and duration (max 90 s).
4. Rate limit auth and job endpoints.
5. Store the minimum personal data. Support full deletion of a user's data (DB rows and R2 objects).
6. Do not log tokens, emails, comment text or video URLs.
7. Only official Instagram APIs. No scraping, no unofficial libraries that log in with passwords.

## 7. ML and data practice

1. Keep train, validation and test splits separate. The test set is touched once per experiment round.
2. Split by creator, not by random row, when evaluating the hook scorer, so the model is not scored on accounts it trained on.
3. Every reported metric states the dataset, the split and the baseline.
4. Label data with a written guideline. Measure agreement (Cohen's kappa) on a shared subset.
5. Save every experiment: config, seed, data version, metrics. Notebooks that matter get cleaned into `ml/`.
6. No claim without a baseline. Compare against a simple model and the LLM zero-shot option.
7. Do not commit datasets with real user comments or videos. Store them in R2 or a private drive and commit the loader.

## 8. Documentation

1. Update `progress.md` when a task finishes. Update `docs/*.md` when behaviour or structure changes.
2. Each module has a short README: what it does, inputs, outputs, how to run its tests.
3. Decisions that change the stack or scope are written in the decision log in `progress.md`.

## 9. Review checklist

Reviewers check: does it do what the task says, is it the smallest reasonable change, are errors handled, are tests meaningful, any secret or PII risk, does it follow this file, and does the UI have loading, empty and error states.
