# SRS: AI Content Intelligence Platform

Software Requirements Specification. Version 0.1. Date: 2026-10-21.
Project: BS AI Final Year Project, ITU Lahore.

## 1. Purpose

This document defines what the system must do, how well, and under which constraints. It is the reference for design, implementation and evaluation.

## 2. Product summary

A web system that analyses why short-form videos work, tests a creator's video as Instagram Trial Reels before followers see it, and learns from every post. It also reads Roman Urdu and English comments and turns them into themes and video ideas.

Problem: creators use five or more separate tools and none of them learn from what performed for that specific account. Pakistani creators also get comments in Roman Urdu mixed with English, which global tools misread.

## 3. Users

| User | Description | Priority |
|---|---|---|
| Creator | Instagram creator, 1,000+ followers, posts 3 to 7 reels a week | Primary |
| Brand | Small business posting its own reels | Secondary (light module) |

## 4. Scope

In scope for the FYP: Instagram only, the creator loop (DNA, scripts, hook score, auto-edit, trial variants, bandit learning, comment intelligence, weekly report), and a light brand competitor analysis if time allows.

Out of scope: TikTok and YouTube Shorts, comment auto-replies, DM automation, automated brand outreach, creator matching (v2), ads management.

## 5. Assumptions and constraints

1. Instagram official APIs only. Trial Reels publishing is supported through the Content Publishing API (`trial_params`). Eligibility depends on the account. Verified in the week 1 spike.
2. No guaranteed GPU. Training on Colab or Kaggle. Inference on CPU or through APIs.
3. API spend under USD 30 per month during the pilot.
4. Team of four, 20 weeks (16 if the deadline requires it).
5. Pilot with 10 to 15 creators for 4 to 6 weeks. Pilot accounts are added as testers while the Meta app is in development mode.
6. Reference reels come from user uploads, not from links or scraping.

## 6. Functional requirements

Priority: P0 must ship for the demo, P1 should ship, P2 nice to have.

### 6.1 Accounts and onboarding

| ID | Requirement | P |
|---|---|---|
| FR-1.1 | Sign up with email or Google and choose a role: creator or brand | P0 |
| FR-1.2 | Connect an Instagram Professional account through Instagram Login (OAuth) | P0 |
| FR-1.3 | Onboarding captures niche, language mix (English, Urdu, Roman Urdu), tone and goals | P0 |
| FR-1.4 | Import the last 30 to 50 reels with captions, insights and comments | P0 |
| FR-1.5 | Add up to 10 reference reels by uploading files | P0 |

### 6.2 Format DNA engine

| ID | Requirement | P |
|---|---|---|
| FR-2.1 | Ingest a reference reel and extract transcript, scene cuts, on-screen text and audio features | P0 |
| FR-2.2 | Classify the hook type (question, bold claim, pattern interrupt, story, list, other) | P0 |
| FR-2.3 | Produce a structured DNA record: hook, pacing (cuts per 10 s), structure beats, overlays, CTA, length | P0 |
| FR-2.4 | Compute an outlier score: views relative to the account median | P0 |
| FR-2.5 | Library of DNA templates the user can save and reuse | P1 |
| FR-2.6 | Cluster DNA records to show dominant formats in a niche | P1 |

### 6.3 Ideation and scripting

| ID | Requirement | P |
|---|---|---|
| FR-3.1 | Pick a DNA template and enter a topic or rough idea | P0 |
| FR-3.2 | Generate 5 hooks, 3 angles and a full script that follows the template beats | P0 |
| FR-3.3 | Match the creator's voice using past captions and transcripts as examples | P0 |
| FR-3.4 | Output in English, Roman Urdu or a mix | P0 |
| FR-3.5 | Shot list and B-roll suggestions per beat | P1 |
| FR-3.6 | Suggest ideas from comment themes | P1 |

### 6.4 Hook scoring

| ID | Requirement | P |
|---|---|---|
| FR-4.1 | Score each generated hook from 0 to 100 for predicted performance | P0 |
| FR-4.2 | Score the first 3 seconds of an uploaded video | P1 |
| FR-4.3 | Explain each score with the top 3 contributing factors | P1 |

### 6.5 Auto-editing

| ID | Requirement | P |
|---|---|---|
| FR-5.1 | Upload raw vertical footage up to 90 s | P0 |
| FR-5.2 | Add word-level captions in a chosen style | P0 |
| FR-5.3 | Cut silences and filler words (silences P0, fillers P1) | P0 |
| FR-5.4 | Insert B-roll from a stock API matched to the transcript | P1 |
| FR-5.5 | Add frame, progress bar and text hook overlay | P1 |
| FR-5.6 | Preview and adjust before export | P1 |

### 6.6 Publishing and trial variants

| ID | Requirement | P |
|---|---|---|
| FR-6.1 | Generate 3 to 5 variants of one video: different hook line, opening frame, caption | P0 |
| FR-6.2 | Publish variants as Instagram Trial Reels through the Content Publishing API | P0 |
| FR-6.3 | Generate captions and hashtags per variant | P0 |
| FR-6.4 | Schedule posts for a chosen time | P1 |
| FR-6.5 | Pull insights for each variant at 24 h and 72 h | P0 |
| FR-6.6 | Pick the winning variant and recommend sharing it to followers | P0 |
| FR-6.7 | Update the creator's bandit model with the result | P0 |
| FR-6.8 | Fall back to a normal reel when the account is not eligible for Trial Reels | P0 |

### 6.7 Comment intelligence

| ID | Requirement | P |
|---|---|---|
| FR-7.1 | Fetch comments on the user's reels | P0 |
| FR-7.2 | Classify each comment: question, request, praise, objection, complaint, spam | P0 |
| FR-7.3 | Handle English, Urdu script and Roman Urdu code-mixed text | P0 |
| FR-7.4 | Cluster comments into themes and rank by frequency | P0 |
| FR-7.5 | Turn top themes into video ideas | P1 |
| FR-7.6 | Suggest replies to questions, user approves before sending | P2 |

### 6.8 Analytics and weekly report

| ID | Requirement | P |
|---|---|---|
| FR-8.1 | Dashboard: views, reach, saves, shares, watch time per reel | P0 |
| FR-8.2 | Show which DNA formats perform best for this account | P1 |
| FR-8.3 | Weekly report: wins, losses, comment themes, 5 ideas for next week | P1 |

### 6.9 Brand module (light)

| ID | Requirement | P |
|---|---|---|
| FR-9.1 | Brand adds up to 5 competitor accounts | P1 |
| FR-9.2 | Show competitors' top formats and DNA breakdown | P1 |
| FR-9.3 | Generate content ideas and scripts from those formats | P1 |
| FR-9.4 | Recommend creators whose content DNA fits the brand | P2 (v2) |

Note: competitor reels reach the system through user uploads and public metrics only. If this makes FR-9.x impractical, the module moves to v2.

## 7. Non-functional requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Performance | Script and hooks return in under 15 s. DNA analysis of a 60 s reel in under 2 min |
| NFR-2 | Performance | Auto-edit of a 60 s clip finishes in under 5 min on CPU |
| NFR-3 | Reliability | Video jobs run in a queue with retries. A failed job never blocks the UI |
| NFR-4 | Security | OAuth tokens encrypted at rest. No Instagram passwords stored |
| NFR-5 | Privacy | Users can disconnect accounts and delete all their data |
| NFR-6 | Compliance | Official APIs only for publishing and insights. No scraping |
| NFR-7 | Rate limits | Respect Instagram quotas, including the Trial Reels publishing cap |
| NFR-8 | Usability | Mobile-responsive web app. Idea to published variants in under 10 clicks |
| NFR-9 | Cost | Free tiers plus under USD 30 per month API spend during the pilot |
| NFR-10 | Explainability | Every score shows its top contributing factors |
| NFR-11 | Maintainability | Lint, type checks and tests in CI. ML code isolated in `ml/` |
| NFR-12 | Observability | Structured logs, error tracking, job status visible to the user |

## 8. AI and ML requirements

| Component | Approach | Data | Output |
|---|---|---|---|
| Format DNA extractor | Whisper, PySceneDetect, frame embeddings (CLIP or SigLIP), OCR or vision LLM, LLM structuring into a fixed schema | Uploaded reels, public short-video datasets for testing | JSON DNA record |
| Hook scorer | Regression on per-account outlier score, sentence embeddings plus LightGBM, SHAP for explanation. Small fine-tuned transformer as stretch | Pilot creators' reels with insights, public datasets if licensed | Score 0 to 100 and top factors |
| Variant learner | Contextual multi-armed bandit, Thompson sampling over variant features, shared prior across creators | Trial Reel insights at 24 h and 72 h, plus simulator | Next variant policy and winner |
| Comment intelligence | Roman Urdu normalisation, fine-tuned XLM-R or mBERT classifier, BERTopic for themes | Hand-labelled 2,000 to 3,000 comments | Labels, themes, idea seeds |
| Script generation (supporting) | LLM API, grounded by DNA and retrieved examples of the creator's writing | Creator captions and transcripts | Hooks, angles, scripts |

## 9. Evaluation plan

| What we test | Metric | Target |
|---|---|---|
| DNA extractor | Agreement with human labels on hook type (100 reels) | 80%+ hook type accuracy |
| Hook scorer | Spearman correlation, predicted vs real outlier score, held-out creators | Positive and significant |
| Comment classifier | Macro F1 on labelled test set vs LLM zero-shot and English-only baseline | Beats both baselines |
| Variant learner | Winning variant views vs average variant views. Regret in simulator | Clear uplift |
| Overall product | Pilot creators' median views per reel, before vs during pilot | Report honestly |
| Usability | Time from idea to published variants, SUS score | Under 15 min, SUS 68+ |
| Editing | Caption word error rate per language | Report WER for Urdu and English |
| Labelling quality | Cohen's kappa on a shared subset | Report value |

## 10. External interfaces

| Interface | Use |
|---|---|
| Instagram API with Instagram Login | OAuth, media import, insights, comments, Content Publishing |
| LLM API (OpenRouter, Gemini or Claude, to be chosen) | Structuring, scripts, captions |
| Pexels API | Stock B-roll |
| Supabase | Auth and Postgres |
| Cloudflare R2 | Video and file storage |

## 11. Platform risks

| Risk | Impact | Mitigation |
|---|---|---|
| No official API to download other accounts' reels | DNA engine has no input | Users upload reference reels. Business Discovery for public metrics. Public datasets for training |
| Trial Reels need a public account with 1,000+ followers and are not on every account | Some pilot creators ineligible | Recruit above 1,000 followers. Fallback to normal reels (FR-6.8) |
| Publishing cap for Trial Reels | Cannot push unlimited variants | 3 to 5 variants per video. Bandit picks informative ones |
| Meta app review for permissions | Delay beyond testers | Dev mode with testers. Submit review early |
| Near-duplicate variants treated as unoriginal | Reach penalty | Variants differ in hook, opener and caption, not only a re-upload |
| Small dataset for hook scorer | Weak model | Per-account normalised target. Report correlation, not accuracy |
| Roman Urdu has no standard spelling | Classifier errors | Normalisation step, hand-labelled set, LLM baseline |
| No guaranteed GPU | Slow processing | API inference, small models, Colab or Kaggle for training |

## 12. Architecture summary

Next.js web app, one FastAPI API, Celery workers with Redis for video and AI jobs, Postgres with pgvector, Cloudflare R2 for files, FFmpeg for video. Details in `docs/backend.md` and `docs/frontend.md`.

## 13. Open questions

1. Final timeline: 16 or 20 weeks.
2. LLM provider choice under the budget.
3. Legal public short-video dataset with view counts.
4. Pilot recruitment: 10 to 15 creators with 1,000+ followers.
5. Supervisor decision on brand module in the demo.
