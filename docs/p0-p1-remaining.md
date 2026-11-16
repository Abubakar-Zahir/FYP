# What is left in Phase 0 and Phase 1

Written 2026-11-16, after PRs #2 to #14 were merged into `main`.

All the **code** for Phase 0 and Phase 1 is on `main`, and CI passes (249 Python tests, 22 web unit tests, 12 Playwright tests). The phases themselves are **not finished**. Nothing has run against a real Instagram account, a real LLM, R2 or Supabase yet. No real data or labels exist, and Gate 0 and Gate 1 have not been held.

Do not start Phase 2 until every box below is ticked. `progress.md` stays the official tracker. This file lists what is left in one place.

## 1. Accounts and settings to create

Nothing below can be tested until these exist. Variable names are in `infra/.env.example`, `infra/.env.prod.example` and `apps/web/.env.example`.

- [ ] **Supabase project.** Turn on Google and email sign-in and **asymmetric JWT signing keys**. Add `http://localhost:3000/auth/callback` and the deployed `/auth/callback` to Redirect URLs. Set `SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- [ ] **Meta app** with Instagram Login and a professional test account added as a tester. Set `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`, and `INSTAGRAM_REDIRECT_URI` (pointing at `<web>/connect/instagram`).
- [ ] **Cloudflare R2 bucket** with an API token and a CORS rule that allows PUT from the web app (the JSON is in `apps/api/README.md`). Set `R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET_KEY` and `R2_BUCKET`.
- [ ] **LLM provider and key.** Set `LLM_PROVIDER=openai_compatible`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, and the two price settings from the provider's price page. Without prices the client refuses to run.
- [ ] **`TOKEN_ENCRYPTION_KEY`**, generated with the command in `apps/api/README.md`. Store it safely: if it changes, every creator has to reconnect Instagram.
- [ ] **Run the stack locally once with real settings:** API, a `default,ai` worker, a `video` worker, and `beat`. The commands are in `apps/api/README.md`.

## 2. Phase 0: left before Gate 0

| ID | What is left | Who | Done when |
|---|---|---|---|
| P0-03 to P0-07 | A teammate reviews the prototype screens. They went to `main` without review | T1 | An issue with review notes and creator feedback exists |
| P0-08 | Run Instagram login and reel import on a real account. Confirm the unverified details (paging on `graph.instagram.com`, field names, latest `API_VERSION`) | T1 | Rows 1 to 3 and the quota row of the table in `spikes/instagram/README.md` are filled |
| P0-09 | Publish one Trial Reel (`MANUAL` and `SS_PERFORMANCE`) and one normal reel. Record the error an ineligible account gets | T1 | Whole results table filled, and the team knows if Trial Reels work |
| P0-10 | Run extraction on 20 real reels, check cuts by eye on 5, tune the threshold, run `spikes/dna/structure.py`, check 5 DNA records | T2 | P0-10 table filled, 20 `.dna.json` files exist |
| P0-11 | Record 30+ clips with human-typed transcripts, run WER with `tiny` and `small` | T2 | WER table has 6 rows and a model recommendation |
| LLM provider | Compare 2 or 3 models on 10 hand-labelled reels, then choose one | T2 | Row in the `progress.md` decision log |
| P0-12 | NLP owner approves the comment label guideline. Write the reel hook-type guide. Do the 25-comment trial in Label Studio | T2 | Both guidelines approved, trial agreement written down |
| P0-13 | Gate 0 review | All | Decisions written in the decision log, phase set to Phase 1 |

## 3. Phase 1: left before Gate 1

| ID | Code on `main` | What is left |
|---|---|---|
| P1-01 | Supabase sign-in, JWT check on the API | Sign in live with Google and email. Check `GET /me` returns the real user |
| P1-02 | Onboarding, profile, disconnect, delete account | Manual check against the real API. Delete an account and confirm the rows and R2 files are gone |
| P1-03 | Connect, encrypted tokens, import job, token refresh | Connect a real account and import 30+ reels with comments. Check the token in the database is unreadable |
| P1-04 | Extractor, DNA job and endpoints | Time a 60 s reel on the target CPU (target: under 2 minutes). Choose OCR or a vision model for on-screen text. Freeze the DNA schema |
| P1-05 | DNA library on the real API | Upload a real reel in the browser and see it appear with hook type and beats |
| P1-06 | Script generation and endpoints | Generate 5 scripts with the chosen provider and rate them on the rubric (2 raters). Check the script comes back in under 15 s |
| P1-07 | Nothing (hands-on work) | 100 reels labelled for hook type by people only. 500 comments labelled, with a 150 human-only test split and a kappa score |
| P1-08 | Nothing (hands-on work) | 15 pilot creators with signed consent, at least 10 added as Meta app testers |
| Baseline | Nothing | Run DNA structuring on the 100 labelled reels and report hook-type accuracy with a confidence interval |
| Gate 1 | Nothing | Record the full demo on a real account: sign in, onboard, connect, import, upload, DNA, script, disconnect, delete |

## 4. Gaps in the merged code

Found while building. None of them blocks testing, but each should be fixed or given an issue number before Gate 1.

- [ ] **No rate limiting** on sign-in and job endpoints. rules.md 6.4 requires it.
- [ ] **No error reporting.** `SENTRY_DSN` is listed in the env files, but Sentry is not wired up.
- [ ] **No button to analyse the creator's own imported reels.** `POST /dna/analyse` supports them, but the web app only analyses uploaded reference reels.
- [ ] **On-screen text (overlays) is always empty.** Keyframes are not kept until OCR or a vision model is chosen.
- [ ] **Hooks are not scored.** `score` is `null` until the Phase 2 hook scorer.
- [ ] **Voice matching is basic.** Scripts use the creator's 8 latest captions. pgvector retrieval is Phase 2.
- [ ] **No cap on reference reels per user.** The old prototype limit of 10 was dropped. Decide whether a cap is needed.
- [ ] **No Claude adapter in the LLM client.** Only OpenAI-compatible providers work. If Claude is chosen, add an adapter with the official `anthropic` SDK.
- [ ] **Production deploy not done.** `docs/deploy.md` and the prod compose (API, two workers, beat, Caddy) are ready, but nothing runs on a VPS yet. Pilot creators need a real URL.
- [ ] **Lockfile.** `pnpm-lock.yaml` has a Windows-only `@pnpm/exe` entry. CI accepts it, but regenerate it on Linux when convenient.

## 5. Process items

- [ ] **PRs #2 to #14 went to `main` without a teammate's approval.** rules.md 1.1 and 1.6 require one. A teammate should review the merged code now and open issues for anything found.
- [ ] **Merge style.** They were merged with merge commits, not squash (rules.md 1.6), because squashing a stack causes conflicts. Record this in the decision log or change the rule.
- [ ] **Old branches.** The merged branches for #3 to #14 are still on GitHub. Delete them once the review is done.
- [ ] **Stale docs.** Update `status.md` and `README.md` files that still describe the prototype only, or mark them superseded.

## 6. Decisions still open

These go to the Gate 0 review.

1. Trial Reels, or the normal-reel fallback (after P0-09).
2. "Share winner to followers": the API can't graduate a `MANUAL` Trial Reel. Show in-app instructions, or use `SS_PERFORMANCE`.
3. Pilot creators as app testers, or Meta App Review.
4. Whisper model size: `tiny` or `small` (after P0-11).
5. LLM provider (after the comparison).
6. 16 or 20 week timeline, and the start date.
7. Whether Apify may be used for consenting creators' data. It needs a decision log entry and supervisor approval, because of CLAUDE.md hard constraint 1.
8. Training dataset with view counts for the hook scorer (MicroLens or similar).

## 7. When Phase 0 and 1 are really done

- [ ] Gate 0 checklist ticked and decisions logged
- [ ] Every item in sections 1 to 3 ticked
- [ ] Every gap in section 4 fixed or given an issue number (CLAUDE.md: no TODO without an issue)
- [ ] Merged code reviewed by a teammate
- [ ] Gate 1 demo recorded on a real account
- [ ] `progress.md` shows P0-01 to P1-08 as `done`
