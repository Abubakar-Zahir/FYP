# progress.md

Single source of truth for status. Update it in the same PR that finishes a task. Keep it short.

Start date: set when the team agrees (week 1 begins).
Current phase: Phase 0, Spikes and prototype.
Last updated: 2026-10-21

Status values: `todo`, `doing`, `blocked`, `done`.

## Phase 0 (weeks 1 to 2)

| ID | Task | Owner | Status | Notes |
|---|---|---|---|---|
| P0-01 | Create monorepo, CI, lint, types, test setup | Backend | todo | |
| P0-02 | docker-compose with Postgres (pgvector) and Redis | Backend | todo | |
| P0-03 | Frontend scaffold: Next.js, Tailwind, shadcn, tokens | Frontend | todo | |
| P0-04 | Prototype: login and onboarding screens (mock data) | Frontend | todo | |
| P0-05 | Prototype: dashboard and DNA library and DNA detail | Frontend | todo | |
| P0-06 | Prototype: script studio and hook scores | Frontend | todo | |
| P0-07 | Prototype: editor preview and variants and comments insights | Frontend | todo | |
| P0-08 | Spike: Instagram OAuth and reel import | Backend | todo | |
| P0-09 | Spike: publish one Trial Reel via API | Backend | todo | Confirm account type needed |
| P0-10 | Spike: DNA pipeline on 20 reels | ML video | todo | |
| P0-11 | Spike: Whisper WER on Urdu and Roman Urdu | ML video | todo | |
| P0-12 | Label guideline (6 classes) and Label Studio setup | ML NLP | todo | |
| P0-13 | Gate 0 review | All | todo | |

## Phase 1 (weeks 3 to 6)

| ID | Task | Owner | Status |
|---|---|---|---|
| P1-01 | Auth with Supabase, backend JWT verification | Backend | todo |
| P1-02 | Onboarding API and real screens | Frontend | todo |
| P1-03 | Instagram connect and reel import jobs | Backend | todo |
| P1-04 | DNA extractor v1 in `ml/` and worker | ML video | todo |
| P1-05 | DNA screens wired to real API | Frontend | todo |
| P1-06 | Script generation v1 with DNA grounding | ML NLP | todo |
| P1-07 | Label 500 comments and 100 reels (hook type) | ML NLP, ML video | todo |
| P1-08 | Recruit pilot creators (target 15) | All | todo |

Later phases are listed in `roadmap.md`. Move tasks here when the phase starts.

## Decision log

| Date | Decision | Reason |
|---|---|---|
| 2026-10-21 | FastAPI for the backend, not Django or Node | Work is API heavy (Instagram, LLM, webhooks, jobs). Python for all AI code. One backend language |
| 2026-10-21 | Supabase Auth and Postgres, R2 for video | Auth is free and fast to wire. Video files are large |
| 2026-10-21 | Celery and Redis for jobs | Heavy video and ML work must not run in request handlers |
| 2026-10-21 | `ml/` is a plain Python package | Same code runs in notebooks and workers. Framework stays swappable |
| 2026-10-21 | Reference reels are uploaded files only, no links | Avoids scraping and ToS problems |
| 2026-10-21 | Brand module moved to v2 | Scope too large for the timeline |
| 2026-10-21 | Frontend prototype first, with mock data | Gets feedback early and fixes the API contract before backend work |

## Blockers

None yet.

## Open questions

1. Final timeline: 16 or 20 weeks?
2. Which LLM provider fits the budget (OpenRouter, Gemini, Claude)?
3. Is there a public short-video dataset with view counts that we may legally use?
4. Can we recruit 10 to 15 pilot creators with 1,000+ followers?
5. Does the supervisor want the brand module in the demo or as future work?

## Session log

Add one line per working session: date, who, what was done, what is next.

| Date | Who | Done | Next |
|---|---|---|---|
| 2026-10-21 | Team | Requirements doc reviewed, stack decided, docs set created | Start Phase 0 |
