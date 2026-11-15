# status.md

Snapshot of what is done and what is left, taken from the code on `main` on 2026-11-11. `progress.md` is still the official tracker, and it is behind this file. See "progress.md is stale" at the end.

## What we are building

AI Content Intelligence Platform for Instagram creators (1,000+ followers). BS AI FYP, ITU Lahore.

1. **Format DNA:** break uploaded reference reels into transcript, cuts, pacing, hook type and structure.
2. **Scripts:** hooks, angles and full scripts in the creator's voice, in English and Roman Urdu.
3. **Hook scorer:** predict hook strength before publishing.
4. **Auto-edit:** captions, silence cuts, Roman Urdu transliteration and B-roll with FFmpeg.
5. **Trial Reels:** publish 3 to 5 variants and pull insights at 24 h and 72 h.
6. **Variant learner:** a Thompson sampling bandit learns what wins for each creator.
7. **Comment intelligence:** sort Roman Urdu and English comments into 6 classes, then group them into themes and next-video ideas.

Judged on measured ML results from a 4 to 6 week pilot.

## Completed

| Area | What exists | Status note |
|---|---|---|
| Planning docs | `CLAUDE.md`, `rules.md`, `roadmap.md`, `docs/srs.md`, `docs/prd.md`, `docs/backend.md`, `docs/frontend.md` | Done |
| P0-01 Monorepo + CI | uv, pnpm, ruff, mypy, pytest, GitHub Actions | Merged |
| P0-02 docker-compose | Postgres with pgvector and Redis in `infra/` | Merged, never run (no Docker on the dev machine) |
| P0-03 to P0-07 Frontend prototype | 8 screens on MSW mocks: login, onboarding, dashboard, DNA library and detail, script studio, editor, variants, comments, weekly report | On `main` without review |
| Landing page | Pilot recruitment page at `/` | On `main` |
| Web tests | Vitest and Playwright set up | Merged |
| P1-01 Auth (backend) | Supabase JWT verified with JWKS in `apps/api/app/core/security.py` | Merged |
| P1-02 Onboarding API (backend) | `GET /me`, `PUT /me/profile`, `DELETE /me`, users table, Alembic migration, tests | Merged |
| P0-08/09 Instagram spike (code) | OAuth login, reel import and Trial Reel publish with normal-reel fallback, in `spikes/instagram/` | Unit tested, **not run on a real account** |
| P0-10/11 DNA + Whisper spike (code) | `ReelSignals` and `DnaRecord` schema, scene cuts, keyframes, transcript, WER metric | Checked on 1 synthetic clip, **not run on real reels** |
| P0-12 Label guideline | 6 classes, Label Studio config, agreement metric | Merged, needs NLP owner approval |

## Left: Phase 0 (Gate 0)

- [ ] **P0-08/09** Run the Instagram spike on a real professional account. Publish one Trial Reel and fill in the results table. *This is the top priority.*
- [ ] **P0-10** Run DNA extraction on 20 real reels. Check cuts by eye on 5 of them and tune the threshold.
- [ ] **P0-11** Measure Whisper WER on 10+ clips each of Urdu, English and mixed, with `tiny` and `small`.
- [ ] Add the LLM structuring step for hook type, beats and CTA. Pick the LLM provider first.
- [ ] Run docker-compose for real, locally or on the first CI run.
- [ ] Get a teammate review of the frontend prototype (it went to `main` directly).
- [ ] Get the NLP owner's approval of the label guideline.
- [ ] **P0-13** Hold the Gate 0 review.

## Left: Phase 1 (weeks 3 to 6)

- [ ] Wire the frontend to real Supabase login and the `/me` API. Screens still run on mocks.
- [ ] Generate frontend types from OpenAPI and replace the hand-written `apps/web/src/lib/api/types.ts`.
- [ ] **P1-03** Instagram connect and reel import as Celery jobs, with tokens encrypted at rest. No Celery code exists yet.
- [ ] **P1-04** DNA extractor v1 in `ml/`, plus its worker.
- [ ] **P1-05** DNA screens on the real API.
- [ ] **P1-06** Script generation v1, grounded in DNA.
- [ ] **P1-07** Label 500 comments and 100 reels for hook type.
- [ ] **P1-08** Recruit 15 pilot creators.

## Left: Phase 2 to 4

- [ ] Comment classifier: LLM zero-shot and English-only baselines, then an XLM-R fine-tune. BERTopic themes.
- [ ] Hook scorer v1: features, embeddings, LightGBM, SHAP.
- [ ] Auto-edit: word-level captions, silence cut, Roman Urdu transliteration, Pexels B-roll, browser preview.
- [ ] Voice matching with pgvector, and DNA clustering.
- [ ] Variant generation (3 to 5) and Trial Reel publishing with fallback.
- [ ] Insights jobs at 24 h and 72 h, plus winner pick.
- [ ] Bandit with Thompson sampling, plus the offline simulator.
- [ ] Weekly report, dashboard, data deletion screen, hardening.
- [ ] Pilot: 10 to 15 creators for 5 weeks. Collect insights, time-to-publish and SUS.
- [ ] Evaluation, thesis, demo video.

## Decisions still open

1. **"Share winner"** can't be done by API. `MANUAL` trial reels graduate in the Instagram app. Either show instructions to the creator or use `SS_PERFORMANCE`.
2. **Business Discovery and our login type.** The docs plan to use it for public competitor metrics. It may need Facebook Login rather than Instagram Login. Verify before relying on it.
3. **App Review vs dev mode.** If every pilot creator gets a tester role on the app, App Review and Business Verification can move to future work.
4. **Timeline:** 16 or 20 weeks.
5. **LLM provider** under USD 30/month.
6. **Training dataset** with view counts (check MicroLens).
7. **Trial Reel daily cap and eligibility** (about 20/day and 1,000+ followers are unconfirmed). Confirm on the first real run.

## progress.md is stale

It was last updated 2026-10-21. It still shows P0-08 to P0-11 as `todo` even though their code is merged, and P1-01 and P1-02 as `doing` even though their backend parts are merged. Update it in the next PR.
