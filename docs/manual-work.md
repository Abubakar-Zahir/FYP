# Manual work, Phase 0 to Phase 3

Written 2026-11-16, after the code for Phases 0 to 3 was finished (PRs #2 to #14 on `main`, #16 to #26 open and stacked).

The **code** for Phases 0 to 3 is written and tested against fakes: about 390 Python tests, 22 web unit tests and 13 Playwright tests. None of it has run against a real Instagram account, a real LLM, R2 or Supabase. No real data or labels exist, no model has been trained on real data, and no gate has been held.

This file lists everything that needs a person: accounts, data, labels, checks by eye or ear, real-account runs, reviews and decisions. Code cannot do these. `progress.md` stays the official tracker.

Order matters. Work top to bottom: section 1 unblocks everything, and each phase needs the one before it.

## 1. Accounts and settings

Variable names are in `infra/.env.example`, `infra/.env.prod.example` and `apps/web/.env.example`.

- [ ] **Supabase project.** Turn on Google and email sign-in and **asymmetric JWT signing keys**. Add `http://localhost:3000/auth/callback` and the deployed `/auth/callback` to Redirect URLs. Set `SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- [ ] **Meta app** with Instagram Login and a professional test account added as a tester. Set `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`, and `INSTAGRAM_REDIRECT_URI` (pointing at `<web>/connect/instagram`). Publishing needs the content publish permission on the app. Check the exact permission name in Meta's docs before requesting it.
- [ ] **Cloudflare R2 bucket** with an API token and a CORS rule that allows PUT from the web app (the JSON is in `apps/api/README.md`). Set `R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET_KEY` and `R2_BUCKET`.
- [ ] **LLM provider and key.** Set `LLM_PROVIDER=openai_compatible`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, and the two price settings from the provider's price page. Without prices the client refuses to run.
- [ ] **`TOKEN_ENCRYPTION_KEY`**, generated with the command in `apps/api/README.md`. Store it safely: if it changes, every creator has to reconnect Instagram.
- [ ] **Sentry project (optional).** Set `SENTRY_DSN` and `ENVIRONMENT`. Without a DSN, error reporting stays off.
- [ ] **Model paths**, once the models in section 4 exist: `COMMENT_MODEL_PATH` and `HOOK_SCORER_PATH`. While they are empty, comments stay unlabelled and hooks stay unscored. Nothing breaks.
- [ ] **Run the stack locally once with real settings:** API, a `default,ai` worker, a `video` worker (it needs FFmpeg), and `beat`. The commands are in `apps/api/README.md`.

## 2. Phase 0: left before Gate 0

| ID | What is left | Who | Done when |
|---|---|---|---|
| P0-03 to P0-07 | A teammate reviews the prototype screens. They went to `main` without review | T1 | An issue with review notes and creator feedback exists |
| P0-08 | Run Instagram login and reel import on a real account. Confirm the unverified details (paging on `graph.instagram.com`, field names, latest `API_VERSION`) | T1 | Rows 1 to 3 and the quota row of the table in `spikes/instagram/README.md` are filled |
| P0-09 | Publish one Trial Reel (`MANUAL` and `SS_PERFORMANCE`) and one normal reel. Record the exact error an ineligible account gets | T1 | Whole results table filled, and the team knows if Trial Reels work |
| P0-10 | Run extraction on 20 real reels, check cuts by eye on 5, tune the threshold, run `spikes/dna/structure.py`, check 5 DNA records | T2 | P0-10 table filled, 20 `.dna.json` files exist |
| P0-11 | Record 30+ clips with human-typed transcripts, run WER with `tiny` and `small` | T2 | WER table has 6 rows and a model recommendation. Set `WHISPER_MODEL` |
| LLM provider | Compare 2 or 3 models on 10 hand-labelled reels, then choose one | T2 | Row in the `progress.md` decision log |
| P0-12 | NLP owner approves the comment label guideline. Write the reel hook-type guide. Do the 25-comment trial in Label Studio | T2 | Both guidelines approved, trial agreement written down |
| P0-13 | Gate 0 review | All | Decisions written in the decision log, phase set to Phase 1 |

## 3. Phase 1: left before Gate 1

| ID | What is left |
|---|---|
| P1-01 | Sign in live with Google and email. Check `GET /me` returns the real user |
| P1-02 | Delete an account on the real API and confirm the rows and every R2 file are gone (reference reels, raw and edited videos, rendered variants) |
| P1-03 | Connect a real account and import 30+ reels with comments. Check the token in the database is unreadable |
| P1-04 | Time a 60 s reel on the target CPU (target: under 2 minutes). Choose OCR or a vision model for on-screen text. Freeze the DNA schema |
| P1-05 | Upload a real reel in the browser and see it appear with hook type and beats. Press Analyse on an imported reel on the dashboard |
| P1-06 | Generate 5 scripts with the chosen provider and rate them on the rubric (2 raters). Check the script comes back in under 15 s |
| P1-07 | 100 reels labelled for hook type by people only. 500 comments labelled, with a 150 human-only test split and a kappa score |
| P1-08 | 15 pilot creators with signed consent, at least 10 added as Meta app testers |
| Baseline | Run DNA structuring on the 100 labelled reels and report hook-type accuracy with a confidence interval |
| Gate 1 | Record the full demo on a real account: sign in, onboard, connect, import, upload, DNA, script, disconnect, delete |

## 4. Phase 2: left before Gate 2

Gate 2 needs: the classifier scored against both baselines on a held-out set, a first correlation number for the hook scorer, and a 60 s clip auto-edited in under 5 minutes on CPU.

### Comment classifier and themes (ML NLP)

Code: `ml/comments/`, `notebooks/comment_classifier_xlmr.ipynb`, the `comments.sync` job and the comments screen.

- [ ] **Label 2,000 to 3,000 comments** in Label Studio with the approved guideline (the 500 from P1-07 count). Use only comments the consent forms cover. Keep the export in `data/labels/`, never in git.
- [ ] **An Urdu speaker checks the spelling map** in `ml/comments/normalise.py` (`VARIANTS`). Add common spellings the pilot comments use. Wrong merges hurt every model.
- [ ] **Train the CPU model and the English-only baseline:**
  `uv run python -m ml.comments.train data/labels/comments.json --out data/models/comments`
- [ ] **Score the LLM zero-shot baseline** on the same split. It sends comments to the provider and prints the cost:
  `PYTHONPATH=apps/api:. uv run python apps/api/scripts/evaluate_zero_shot.py data/labels/comments.json`
- [ ] **Fine-tune XLM-R on Colab or Kaggle** with the notebook. Download the ONNX folder it writes. To use it, install the `nlp` group on the worker (`uv sync --group nlp`).
- [ ] **Pick the model to ship** on macro F1 with its confidence interval, from the held-out split only. Set `COMMENT_MODEL_PATH` to the `.joblib` file or the ONNX folder. Write the three scores in the decision log.
- [ ] **Read the themes and ideas** for 3 pilot creators. Themes need 30+ labelled comments from the last 90 days. Write down if they make sense. NMF is used instead of BERTopic (no torch on CPU). Keep that or change it, and log it.

### Hook scorer (ML NLP)

Code: `ml/scoring/`, `POST /hooks/score`, scores in script generation when `HOOK_SCORER_PATH` is set.

- [ ] **Get enough reels with views.** The target is each reel's views against the creator's own median (outlier score), so it needs many reels per creator from at least 2 creators, ideally all pilot creators. Import them through the app (consenting creators only). Decide on open question 3 (public dataset with view counts) before using any outside data.
- [ ] **Export and train:**
  `PYTHONPATH=apps/api:. uv run python apps/api/scripts/export_hook_dataset.py data/hooks.jsonl`
  `uv run python -m ml.scoring.train data/hooks.jsonl --out data/models/hook_scorer`
- [ ] **Report the number honestly.** The report gives Spearman correlation across held-out creators with a bootstrap interval, against two baselines. If the interval includes zero, say so. No accuracy claims.
- [ ] **Set `HOOK_SCORER_PATH`** to the folder, then check the hook reasons on 5 scripts read sensibly to a creator.

### Auto-edit (ML video)

Code: `ml/edit/`, the `videos.edit` job, the editor screen.

- [ ] **Record raw footage**: 5 or more vertical clips, 30 to 90 s, real talking in Urdu, Roman Urdu and English, from team members or consenting creators.
- [ ] **Time a 60 s clip** on the target CPU, upload to render ready. Gate 2 target: under 5 minutes.
- [ ] **Watch every render.** Check that silence cuts don't clip words, captions line up with speech, the hook overlay shows for 3 s, and the progress bar runs to the end.
- [ ] **Caption WER on the edited clips.** Compare captions with a human-typed transcript, using the P0-11 method.
- [ ] **An Urdu speaker checks Roman Urdu captions** from Urdu-script speech (`ml/edit/transliterate.py`). The rules are simple, and a native speaker will spot wrong spellings at once. Record a short list of fixes.
- [ ] **Check fonts in the Docker image.** Captions must render with no missing-glyph boxes on the VPS, not just on a laptop.

### Voice matching and DNA clusters

- [ ] **Voice check.** For 3 creators, generate scripts and ask each creator if they sound like them (1 to 5). Retrieval uses character n-gram vectors in memory, not pgvector. Keep that or move to pgvector, and log the decision.
- [ ] **Clusters check.** The niche view needs 6+ DNA records per creator. Look at the clusters for 2 creators and write down if the groups make sense.

### Gate 2

- [ ] Classifier scores (main model, English-only baseline, LLM zero-shot) on the held-out set, with intervals, in the decision log
- [ ] Hook scorer correlation with interval in the decision log
- [ ] 60 s clip edited in under 5 minutes on CPU, time recorded
- [ ] Gate 2 review held, phase set to Phase 3

## 5. Phase 3: left before Gate 3

Gate 3 needs: a pilot creator goes from idea to published variants in under 15 minutes, and the variant learner runs in the simulator and updates from real insights.

### Publishing and insights (Backend)

Code: `POST /experiments`, `POST /experiments/{id}/publish`, the insights beat task every 30 minutes, the variants screen.

- [ ] **Publish a real experiment** of 3 variants on the test account. Confirm each one appears as a Trial Reel (not shown to followers) and that the permalinks in the app open.
- [ ] **Confirm the fallback.** On an account without Trial Reels, the first refusal should switch to one normal reel (the learner's top pick) and mark the account ineligible. Compare the real error with what P0-09 recorded. If Meta answers differently than the code expects, open an issue.
- [ ] **Check the insights at 24 h and 72 h.** Compare views, reach, saves and shares in the app with Instagram's own numbers for the same reels. Note any metric the API doesn't return.
- [ ] **Choose `TRIAL_GRADUATION_STRATEGY`.** `MANUAL`: the creator shares the winner using the in-app instructions. `SS_PERFORMANCE`: Instagram decides. Test both on the test account, then log the choice.

### Variant learner (ML)

Code: `ml/bandit/`, beliefs saved per creator, updated when a winner is picked.

- [ ] **Re-run the simulator and keep the output:**
  `uv run python -m ml.bandit.report --rounds 20 60 --out data/reports/bandit_regret.json`
  Version 1 (lower regret is better): at 20 rounds, Thompson sampling 10.40, epsilon-greedy 8.89, random 19.26. At 60 rounds, 18.83, 18.40 and 57.20. **Epsilon-greedy was slightly better than Thompson sampling.** Both beat random by a wide margin. Report these as they are.
- [ ] **Check one real update.** After a pilot experiment's 72 h winner, confirm the creator's beliefs changed in the database.
- [ ] **Decide which policy ships** after the pilot, from real data, not from the simulator alone.

### Weekly report and dashboard

- [ ] **Read one real weekly report** for a pilot creator (it builds Mondays 06:00 UTC, 11:00 in Pakistan, or with "Build it now"). Check that wins and losses match their real week and the ideas make sense.
- [ ] **Check the dashboard numbers** against Instagram's own for one account.

### Hardening and deploy

- [ ] **Deploy to the VPS** with `docs/deploy.md`: API, two workers, beat, Redis, Caddy. Pilot creators need a real URL. Rate limits use Redis when it is set, so all API processes share the counts.
- [ ] **Check the limits are sensible** for real use: 60 writes a minute per user, 10 a minute on Instagram routes. Change them if a creator hits them in normal work.
- [ ] **Send one test error to Sentry** and confirm it arrives with no personal data or request bodies.
- [ ] **Watch the LLM spend** for the first pilot week. It must stay under USD 30 a month.
- [ ] **Delete a pilot test account** after publishing and confirm everything is gone, including rendered variant files in R2.

### Pilot and Gate 3

- [ ] Pilot creators onboarded and added as testers. Submit for Meta App Review only if testers are not enough (decision 3 below)
- [ ] **Time one creator** from idea to published variants, unassisted. Target: under 15 minutes. Write down where they got stuck
- [ ] Gate 3 review held, decisions logged

## 6. Reviews and process

- [ ] **PRs #2 to #14 went to `main` without a teammate's approval.** rules.md 1.1 and 1.6 require one. A teammate should review the merged code and open issues for anything found.
- [ ] **Review PRs #16 to #26 in order.** Each one's base is the one before it. #26 touches the web app, so the frontend owner reviews it. ML owners review #16, #18, #19 and #21.
- [ ] **Merge style.** Stacks were merged with merge commits, not squash (rules.md 1.6), because squashing a stack causes conflicts. Record this in the decision log or change the rule.
- [ ] **Old branches.** Delete merged branches once reviews are done.
- [ ] **Stale docs.** Update `status.md` and `README.md` files that still describe the prototype only.
- [ ] **Lockfile.** `pnpm-lock.yaml` has a Windows-only `@pnpm/exe` entry. CI accepts it, but regenerate it on Linux when convenient.

## 7. Known gaps in the code

Each needs a fix or an issue number before Gate 3 (CLAUDE.md: no TODO without an issue).

- [ ] **On-screen text (overlays) is always empty.** Keyframes are not kept until OCR or a vision model is chosen (P1-04).
- [ ] **No cap on reference reels or videos per user.** Decide if one is needed for R2 cost.
- [ ] **No Claude adapter in the LLM client.** Only OpenAI-compatible providers work. If Claude wins the comparison, add an adapter with the official `anthropic` SDK.
- [ ] **Job results are not in the OpenAPI contract.** The web app types `EditResult` by hand. Fine for now; revisit if more job results are read by the web app.
- [ ] **Rate limit counts are per process without Redis.** Fine locally. Production must set `REDIS_URL`.

## 8. Decisions still open

1. Trial Reels, or the normal-reel fallback (after P0-09).
2. `TRIAL_GRADUATION_STRATEGY`: `MANUAL` with in-app instructions, or `SS_PERFORMANCE`.
3. Pilot creators as app testers, or Meta App Review.
4. Whisper model size: `tiny` or `small` (after P0-11).
5. LLM provider (after the comparison).
6. 16 or 20 week timeline, and the start date.
7. Whether Apify may be used for consenting creators' data. It needs a decision log entry and supervisor approval, because of CLAUDE.md hard constraint 1.
8. A training dataset with view counts for the hook scorer (MicroLens or similar), and whether its licence allows it.
9. Which comment model ships: character n-gram model or XLM-R (after section 4).
10. Thompson sampling or epsilon-greedy (after the pilot).

## 9. When Phases 0 to 3 are really done

- [ ] Gates 0, 1, 2 and 3 held and logged
- [ ] Every box in sections 1 to 5 ticked
- [ ] Every gap in section 7 fixed or given an issue number
- [ ] All merged code reviewed by a teammate
- [ ] `progress.md` shows P0-01 to P3 as `done`
