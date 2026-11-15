# progress.md

Single source of truth for status. Update it in the same PR that finishes a task. Keep it short.

Start date: set when the team agrees (week 1 begins).
Current phase: Phase 0, Spikes and prototype.
Last updated: 2026-11-16

Status values: `todo`, `doing`, `blocked`, `done`.

## Phase 0 (weeks 1 to 2)

| ID | Task | Owner | Status | Notes |
|---|---|---|---|---|
| P0-01 | Create monorepo, CI, lint, types, test setup | Backend | done | Awaiting review. CI first runs when pushed |
| P0-02 | docker-compose with Postgres (pgvector) and Redis | Backend | done | Run locally on 2026-11-16: pgvector 0.8.7 and Redis healthy, Alembic migrations applied. Awaiting review |
| P0-03 | Frontend scaffold: Next.js, Tailwind, shadcn, tokens | Frontend | doing | On `main` (pushed directly, not reviewed). Needs teammate review |
| P0-04 | Prototype: login and onboarding screens (mock data) | Frontend | doing | On `main` (pushed directly, not reviewed). Needs teammate review |
| P0-05 | Prototype: dashboard and DNA library and DNA detail | Frontend | doing | On `main` (pushed directly, not reviewed). Needs teammate review |
| P0-06 | Prototype: script studio and hook scores | Frontend | doing | On `main` (pushed directly, not reviewed). Needs teammate review |
| P0-07 | Prototype: editor preview and variants and comments insights | Frontend | doing | On `main` (pushed directly, not reviewed). Needs teammate review |
| P0-08 | Spike: Instagram OAuth and reel import | Backend | blocked | Code merged and unit tested. Needs a professional test account and the Meta app to run (see the hands-on plan) |
| P0-09 | Spike: publish one Trial Reel via API | Backend | blocked | Code merged. Same account, plus a public clip URL. Fill the results table in `spikes/instagram/README.md` |
| P0-10 | Spike: DNA pipeline on 20 reels | ML video | blocked | Extraction (#5) and LLM structuring (#4) done in code. Needs the 20 reels and an LLM provider |
| P0-11 | Spike: Whisper WER on Urdu and Roman Urdu | ML video | blocked | Script ready. Needs 30+ clips with human-typed transcripts |
| P0-12 | Label guideline (6 classes) and Label Studio setup | ML NLP | done | Awaiting review. NLP owner to approve the guideline |
| P0-13 | Gate 0 review | All | todo | |

## Phase 1 (weeks 3 to 6)

| ID | Task | Owner | Status | Notes |
|---|---|---|---|---|
| P1-01 | Auth with Supabase, backend JWT verification | Backend | doing | Backend JWKS check merged. Web sign-in in #12. Needs a Supabase project with asymmetric keys to try live |
| P1-02 | Onboarding API and real screens | Frontend | doing | `/me` endpoints merged. Real screens, disconnect and delete account in #13 |
| P1-03 | Instagram connect and reel import jobs | Backend | doing | Celery (#2), connect with encrypted tokens (#6), import job, `GET /reels`, token refresh (#7). Needs a real account run |
| P1-04 | DNA extractor v1 in `ml/` and worker | ML video | doing | Extractor and outlier score (#5), R2 upload (#8), `dna.analyse` worker and endpoints (#9). OCR for overlays not wired |
| P1-05 | DNA screens wired to real API | Frontend | doing | Generated types (#11), upload and library on the real API (#13) |
| P1-06 | Script generation v1 with DNA grounding | ML NLP | doing | `ml/scripts` and `/scripts` endpoints (#10). Needs a provider, then the 5-script rubric check |
| P1-07 | Label 500 comments and 100 reels (hook type) | ML NLP, ML video | todo | Hands-on work, see the plan |
| P1-08 | Recruit pilot creators (target 15) | All | todo | Hands-on work, see the plan |

PRs #2 to #14 are stacked: each one's base is the one before it. Review and merge them in order.

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
| 2026-11-03 | Verify Supabase tokens with public keys (JWKS), not the shared secret | Supabase strongly recommends against local verification with the secret. Needs asymmetric signing keys on the project |
| 2026-10-21 | Glassmorphism visual style, dark base, one violet accent | Team choice for the prototype |
| 2026-11-11 | Replaced by a light theme: white base, hot pink accent `#ff0087`, Inter headings and Geist body | Team choice, modelled on a reference landing page. Tokens still live in `globals.css` `@theme` |
| 2026-10-21 | Tailwind v4: tokens in `globals.css` `@theme`, not `tailwind.config` | v4 is CSS-first; no config file |
| 2026-11-16 | LLM wrapper speaks the OpenAI-compatible API over httpx (OpenRouter, Gemini). No SDK yet | Provider not chosen. A Claude adapter with the official SDK gets added if Claude wins the comparison |
| 2026-11-16 | LLM prices are settings, and the client refuses to run without them | The USD 30 budget guard needs a cost per call |
| 2026-11-16 | Instagram OAuth state is a Fernet token holding the user id, valid 10 minutes | Can't be forged or reused, and needs no state table |
| 2026-11-16 | `reels` keeps the latest metrics only. Null means unavailable, not zero | Per-variant history comes with Phase 3 insights |
| 2026-11-16 | Video libraries in an optional `video` dependency group, one worker for the `video` queue | Keeps the API image small and protects the CPU |
| 2026-11-16 | Web sign-in is client-side only (`@supabase/supabase-js`), no `@supabase/ssr` | Every API call is made from the browser, and the API checks the token |
| 2026-11-16 | Phase 2 and 3 screens show "arrives in Phase N" outside mock mode | They have no endpoints yet |

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
| 2026-10-21 | Frontend | Prototype: 8 screens on MSW mocks, glass UI, works at 375 px and 1280 px | Review, add Vitest + Playwright, get creator feedback |
| 2026-10-21 | Frontend | Landing page at `/` for pilot recruitment (editorial glass style, no fake stats or testimonials) | Feedback from creators, link pilot form |
| 2026-11-16 | Claude | Phase 0 and 1 code as 13 stacked PRs (#2 to #14): jobs, LLM wrapper, DNA structuring and extractor, Instagram connect and import, R2 upload, DNA and script endpoints, generated web types, Supabase sign-in, real screens. 249 Python, 22 web unit and 12 Playwright tests pass | Review and merge in order. Then the hands-on work: accounts, data, labels, Gate 0 |
| 2026-11-16 | Backend | Ran the full stack locally: web and API checks, 110 pytest, 10 Playwright, docker-compose and migrations all pass | Run Instagram spike on a real account, LLM structuring step, Gate 0 |
