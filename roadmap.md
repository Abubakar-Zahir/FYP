# roadmap.md

Plan: 20 weeks. The core AI ships first so the pilot gets 5 real weeks of data. Set the real start date in `progress.md`. If the deadline is 16 weeks, use the cut plan at the bottom.

Order of work: frontend prototype first (clickable, mock data), then the real backend behind the same screens.

## Phase 0: Spikes and prototype (weeks 1 to 2)

Goal: kill the biggest risks early and have something clickable.

| Track | Work | Owner area |
|---|---|---|
| Frontend | Repo setup, design tokens, prototype of 8 screens with mock data (see `docs/frontend.md`) | Frontend |
| Instagram spike | OAuth with Instagram Login, import reels, publish one Trial Reel in dev mode. Confirm which account type is needed for publishing | Backend |
| DNA spike | Run Whisper, PySceneDetect and keyframes on 20 reels. Produce one JSON DNA record | ML video |
| Urdu spike | Whisper on Urdu and Roman Urdu speech. Measure word error rate | ML video |
| Labelling prep | Write the label guideline (6 classes), set up Label Studio | ML NLP |
| Infra | Monorepo, CI (lint, types, tests), docker-compose with Postgres and Redis | Backend |

**Gate 0 (end of week 2):** a Trial Reel was published through the API, a DNA record exists for 20 reels, Urdu WER is known, prototype is clickable. If publishing fails, decide: fall back to normal reels or change scope.

## Phase 1: Vertical slice (weeks 3 to 6)

Goal: one user goes from signup to a script grounded in real data.

1. Auth, onboarding (role, niche, language mix, tone), Instagram connect.
2. Import last 30 to 50 reels with captions, insights and comments.
3. Format DNA v1: transcript, cuts, hook type, pacing, structure, outlier score.
4. Script generation v1: 5 hooks, 3 angles, full script, English and Roman Urdu.
5. Comment labelling starts in week 3 and runs in parallel.
6. Start recruiting pilot creators (1,000+ followers, public account).

**Gate 1 (end of week 6):** a real account runs end to end from connect to script. 100 reels labelled for hook type. 500 comments labelled.

## Phase 2: Core ML and editing (weeks 7 to 10)

1. Comment classifier: baselines first (LLM zero-shot, English-only model), then XLM-R fine-tune. BERTopic for themes.
2. Hook scorer v1: text features, embeddings, LightGBM, SHAP. Per-account outlier target.
3. Auto-edit: word-level captions, silence cut, Roman Urdu caption transliteration, preview in the browser.
4. Voice matching with pgvector retrieval.
5. DNA clustering for niche view.

**Gate 2 (end of week 10):** classifier evaluated against both baselines on a held-out set. Hook scorer has a first correlation number. A 60 s clip is auto-edited in under 5 minutes on CPU.

## Phase 3: Publish, variants, learning (weeks 11 to 13)

1. Variant generation (3 to 5, different hook line, opener, caption).
2. Trial Reel publishing with fallback to a normal reel.
3. Insights pull at 24 h and 72 h, winner pick.
4. Bandit with Thompson sampling, plus offline simulator.
5. Weekly report, dashboard, data deletion, hardening.
6. Pilot creators onboarded and added as testers. Meta app review submitted if needed.

**Gate 3 (end of week 13):** a pilot creator completes idea to published variants in under 15 minutes. The bandit runs in the simulator and updates from real insights.

## Pilot (weeks 14 to 18)

1. 10 to 15 creators use the product for 5 weeks.
2. Collect: variant insights, comment data, time-to-publish, SUS questionnaire.
3. Bug fixes only. No new features.
4. Weekly check: are creators posting, are variants publishing, is data clean.

## Phase 4: Evaluation and thesis (weeks 19 to 20)

1. Final metrics: DNA hook accuracy, hook scorer Spearman, comment macro F1, bandit uplift, median views before vs during pilot, WER per language, SUS.
2. Report honestly, including results that did not improve.
3. Thesis writing, demo video, final presentation.

**Gate 4 (end of week 20):** thesis, evaluation report and demo ready.

## Risks to watch

| Risk | When we know | Fallback |
|---|---|---|
| Trial Reel API not usable for our accounts | Gate 0 | Publish normal reels, keep variant testing across posts |
| Not enough pilot creators | Week 6 | Use team and friends' accounts, shorten claims about uplift |
| Hook scorer data too small | Gate 2 | Report correlation with confidence interval, no accuracy claims |
| Meta review delay | Week 13 | Stay in dev mode with testers |
| Labelling falls behind | Week 6 | Pre-label with LLM, human corrects |

## Cut plan for 16 weeks

1. Drop the brand module completely.
2. Phase 2 and 3 become 3 weeks each. Drop DNA clustering and voice retrieval tuning.
3. Pilot shortens to 4 weeks.
4. Keep: comment classifier, hook scorer, bandit, DNA extractor, basic edit, publish.
