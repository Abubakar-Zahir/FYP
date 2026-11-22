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
| P0-08 | Spike: Instagram OAuth and reel import | Backend | done | Run on a real account with Unified Login on 2026-11-16: token, account, 21 reels, all metrics, comments. Creator login flow not run (spike uses a dashboard token). Awaiting review |
| P0-09 | Spike: publish one Trial Reel via API | Backend | done | `MANUAL`, `SS_PERFORMANCE` and normal reel all published at 907 followers. Ineligible-account error still unknown. Results in `spikes/instagram/README.md`. Awaiting review |
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

## Phase 2 (weeks 7 to 10)

Code written ahead of Gates 0 and 1. Nothing here is trained on real data yet. The hands-on work is in `docs/manual-work.md` section 4.

| ID | Task | Owner | Status | Notes |
|---|---|---|---|---|
| P2-01 | Comment classifier: baselines, CPU model, XLM-R notebook | ML NLP | blocked | #16. Needs 2,000 to 3,000 labelled comments, then the Colab run |
| P2-02 | Comment themes and next-video ideas | ML NLP | blocked | #17. NMF themes, LLM ideas, `comments.sync` job. Needs `COMMENT_MODEL_PATH` |
| P2-03 | Hook scorer v1 (LightGBM, SHAP reasons, creator-split Spearman) | ML NLP | blocked | #18. Needs pilot reels with views, then `HOOK_SCORER_PATH` |
| P2-04 | Auto-edit: word captions, silence cut, Roman Urdu, hook overlay | ML video | doing | #19. Needs real footage, CPU timing, Urdu speaker check |
| P2-05 | Voice matching and DNA clusters | ML NLP | doing | #20. In-memory n-gram retrieval, not pgvector yet |
| P2-06 | Gate 2 review | All | todo | |

## Phase 3 (weeks 11 to 13)

The hands-on work is in `docs/manual-work.md` section 5.

| ID | Task | Owner | Status | Notes |
|---|---|---|---|---|
| P3-01 | Variant learner (Thompson sampling) and offline simulator | ML | done | #21. Simulator: TS close to epsilon-greedy, both far below random. Awaiting review |
| P3-02 | Variant generation picked by the learner | Backend | done | #22. Awaiting review |
| P3-03 | Trial Reel publishing with fallback, insights at 24 h and 72 h, winner | Backend | blocked | #23. Needs a real account run (P0-09) |
| P3-04 | Account analytics and weekly report | Backend | done | #24. Awaiting review and a real week of data |
| P3-05 | Rate limits, request ids, Sentry | Backend | done | #25. Awaiting review |
| P3-06 | Web screens for Phases 2 and 3 on the real API | Frontend | done | #26. Not yet tried against the real API with a real video |
| P3-07 | Pilot creators onboarded, Gate 3 timed run | All | todo | |

PRs #16 to #26 are stacked on `main` in that order.

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
| 2026-11-16 | The Meta app uses the Instagram API with Unified Login (`graph.facebook.com`, business integration system user token), not Instagram Login | Meta no longer offers Instagram Login to new apps and calls Unified Login the recommended setup. The spike now uses it. `apps/api/app/services/instagram.py` still assumes Instagram Login and needs the same move (P1-03). Creators need a business portfolio |
| 2026-11-16 | Phase 2 and 3 screens show "arrives in Phase N" outside mock mode | They have no endpoints yet. Superseded the same day: #26 wires them to the real API |
| 2026-11-16 | New dependencies: scikit-learn, lightgbm, sentry-sdk; onnxruntime and tokenizers in an optional `nlp` group | Approved by the team. Everything runs on CPU, no torch on the server |
| 2026-11-16 | Main comment model: character n-gram TF-IDF with logistic regression. XLM-R trained on Colab, served with ONNX Runtime | Handles Roman Urdu spelling variety on CPU. XLM-R ships only if it beats it on the held-out split |
| 2026-11-16 | NMF for comment themes instead of BERTopic | BERTopic needs torch and embeddings, too heavy for the CPU worker |
| 2026-11-16 | Hook scorer evaluated with creator-split folds, Spearman and a bootstrap interval | A creator's reels must not be in both train and test. Correlation, not accuracy (SRS risks) |
| 2026-11-16 | Voice retrieval with hashed n-gram vectors in memory, not pgvector yet | A creator has tens of captions, not thousands. Revisit if retrieval is slow or poor |
| 2026-11-16 | Trial Reel fallback: after the first refusal, only the learner's top variant goes out as a normal reel | Followers should not see near-duplicates (FR-6.8) |
| 2026-11-16 | Winner by views at 72 h. Learner success means views at or above the creator's median | Matches the per-account outlier target used everywhere else |
| 2026-11-16 | Weekly report is rule-based, no LLM | Keeps cost at zero and the numbers traceable |
| 2026-11-16 | Rate limits fail open when Redis is down | A broken counter must not lock every creator out. The failure is logged |

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
| 2026-11-16 | T1 | Moved the Instagram spike to Unified Login and ran it on the test account: import works, both kinds of Trial Reel and a normal reel published. R2 bucket created | Backend: review the PR and plan P1-03 on Unified Login. Gate 0: share-winner and testers decisions |
| 2026-11-16 | Claude | Phase 2 and 3 code as 11 stacked PRs (#16 to #26): comment models and themes, hook scorer, auto-edit, voice and clusters, variant learner and simulator, experiments, publishing and insights, weekly report, hardening, web screens. About 390 Python, 22 web unit and 13 Playwright tests pass. `docs/manual-work.md` lists the hands-on work for Phases 0 to 3 | Review in order. Gates 0 and 1 first, then the Phase 2 data and labels |
