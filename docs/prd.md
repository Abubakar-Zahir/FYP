# prd.md

Product requirements and the work split for four people. Names go in the owner slots. Swap the areas around if strengths differ, but keep each area owned by exactly one person.

## Product in one paragraph

A creator uploads or connects Instagram, the system learns what formats work in their niche, writes scripts in their voice, edits their footage, publishes 3 to 5 variants as Trial Reels, and learns which variant wins for that creator. Comments in Roman Urdu and English become themes and ideas.

## Goals

1. Complete the creator loop end to end on Instagram.
2. Produce measurable ML results from a real pilot.
3. Keep the code clean enough that four people can work in parallel.

## Non-goals

TikTok, YouTube Shorts, DM automation, auto-replies, ads, creator matching, brand outreach.

## Success metrics

See SRS section 9. The main ones: comment classifier beats both baselines, hook scorer correlation is positive on held-out creators, variant learner shows uplift, idea to published variants under 15 minutes, SUS 68+.

## Team and ownership

| Owner | Area | Main modules |
|---|---|---|
| Member A | Frontend and product | All screens, prototype, UX, dashboard, weekly report UI, usability testing |
| Member B | Backend, integrations, infra | Auth, DB, jobs, Instagram OAuth and publishing, insights, bandit service, CI and deploy |
| Member C | NLP | Comment intelligence, Roman Urdu normalisation, labelling, script and caption generation, voice retrieval |
| Member D | Video and ML | Format DNA extractor, hook scorer, auto-edit pipeline, DNA clustering |

## PRD per member

### Member A: Frontend and product

Deliverables:
1. Prototype of 8 screens with mock data (weeks 1 to 2). Spec in `docs/frontend.md`.
2. Real screens wired to the API as endpoints arrive (weeks 3 to 13).
3. Editor and variants UI with upload progress, caption style picker, preview.
4. Comments and weekly report views, analytics dashboard.
5. Usability testing: time-to-publish measurement and SUS questionnaire during the pilot.
6. Pilot onboarding flow and data deletion screen.

Acceptance criteria:
1. Every screen has loading, empty and error states and works at 375 px.
2. No hand-written API types. Types come from OpenAPI.
3. Core flow from idea to published variants is under 10 clicks.
4. Playwright covers onboarding, script generation, variants, comments.

Depends on: B for the API contract and OpenAPI. C and D for response shapes of scripts, scores and DNA.

### Member B: Backend, integrations, infra

Deliverables:
1. Monorepo, CI, docker-compose, deploy to VPS (weeks 1 to 2).
2. Supabase auth verification, user and profile endpoints, data deletion.
3. Instagram OAuth, reel and comment import, token encryption and refresh.
4. Trial Reel publishing flow with eligibility check and fallback, rate limit guard.
5. Insights jobs at 24 h and 72 h, winner selection.
6. Variant learner service: Thompson sampling using `ml/bandit`, state storage, offline simulator (owns the algorithm and its evaluation).
7. Job system: queues, retries, status endpoint.
8. LLM wrapper with budget guard.

Acceptance criteria:
1. Week 2: one Trial Reel published through the API and a written note on account type and permissions.
2. Every endpoint has schema, ownership check, tests and OpenAPI docs.
3. Tokens encrypted. No secrets in git.
4. Bandit regret curve in the simulator and pilot results report.

Depends on: D and C for `ml/` interfaces. A for contract feedback.

### Member C: NLP

Deliverables:
1. Label guideline (6 classes) and Label Studio setup (week 2).
2. 2,000 to 3,000 labelled comments, with a shared subset for Cohen's kappa.
3. Roman Urdu normaliser.
4. Comment classifier: LLM zero-shot baseline, English-only baseline, fine-tuned XLM-R or mBERT. Evaluation report.
5. Theme clustering with BERTopic and idea generation from themes.
6. Script generation: 5 hooks, 3 angles, full script, English and Roman Urdu, grounded by DNA records.
7. Voice matching with pgvector retrieval of the creator's captions and transcripts.
8. Caption and hashtag generation per variant.

Acceptance criteria:
1. Classifier macro F1 beats both baselines on a held-out test set. Results table with confidence intervals.
2. Script endpoint returns in under 15 s.
3. All prompts and model versions stored with outputs.
4. Labelling progress: 500 comments by week 6, 2,000 by week 10.

Depends on: D for the DNA schema. B for job and LLM wrapper. A for response shapes.

### Member D: Video and ML

Deliverables:
1. DNA pipeline spike on 20 reels and Whisper Urdu WER (weeks 1 to 2).
2. DNA extractor: transcript, scene cuts, keyframes, on-screen text, LLM structuring into the DNA schema. Hook type classifier.
3. 100 reels labelled for hook type for evaluation.
4. Outlier score computation.
5. Hook scorer: features, embeddings, LightGBM, SHAP, ablations (text only, text plus embeddings, normalisation on or off), evaluation by creator split.
6. Auto-edit pipeline: word-level captions, silence cut, Roman Urdu transliteration hook, FFmpeg render under 5 minutes for a 60 s clip.
7. DNA clustering for niche view.

Acceptance criteria:
1. Hook type accuracy of 80% or more on 100 labelled reels, compared with LLM zero-shot.
2. Hook scorer reports Spearman correlation on held-out creators, with baseline.
3. DNA schema is versioned and documented in `ml/dna/schema.py`.
4. WER reported per language.

Depends on: B for jobs and storage. C for transliteration and LLM wrapper.

## Cross-team agreements

1. API contract first: Pydantic schemas are reviewed by the frontend owner before implementation.
2. DNA schema is owned by D and frozen by the end of week 4. Changes need a version bump.
3. Weekly 30 minute sync: progress, blockers, next week. Update `progress.md`.
4. Any person can block a PR for rule violations (`rules.md`).
5. Pilot recruitment is shared. Each member brings at least 3 creators.

## Milestones

Follow `roadmap.md`. Gates at weeks 2, 6, 10, 13 and 20.
