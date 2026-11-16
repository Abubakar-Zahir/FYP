# Instagram spike (P0-08, P0-09)

**Status: run on a real account on 2026-11-16. Trial Reels publish through the API.** Results are in the table at the bottom.

Questions: can we read an account, import reels, and publish one Trial Reel through the official API? Which account type does it need?

## Which login this uses

Our Meta app uses the **Instagram API with Unified Login** (a Facebook Login for Business configuration). Meta no longer offers Instagram Login to new apps, and Meta calls Unified Login "the recommended setup for new integrations". The first version of this spike was written for Instagram Login, which uses a different host, token and scope names.

The spike skips the login flow. It uses a business integration system user token generated in the App Dashboard, which you put in `.env.instagram` by hand. The real "Connect Instagram" flow for creators is in the docs table below and is not tested here.

## What the docs say (read 2026-11-16)

| Question | Answer | Source |
|---|---|---|
| Host | `graph.facebook.com`. Samples use `v27.0` | [Unified Login](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-unified-login.md) |
| Token | Business integration system user access token. It belongs to the client's business portfolio, not to the person who logged in. Expiry is set in the configuration | [Authentication](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-unified-login/authentication.md) |
| Account id | `/me` is the system user, not the Instagram account. `GET /me/assigned_instagram_accounts?fields=id,username` lists the accounts the token may use | Authentication, [Get started](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-unified-login/get-started.md) |
| Account type | Instagram professional account (business or creator). A business portfolio is required. No Facebook Page needed | Unified Login |
| Permissions | `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`, `instagram_manage_comments`. The default configuration also requires `instagram_manage_messages` | Get started, [Insights](https://developers.facebook.com/documentation/instagram-platform/reference/instagram-media/insights.md) |
| Creator login (product, not this spike) | Link to `https://www.facebook.com/dialog/oauth` with `client_id`, `config_id`, `redirect_uri`, `response_type=code`. Exchange the code once with `GET graph.facebook.com/v27.0/oauth/access_token` (app id, app secret, code) | Get started |
| Publishing | `POST /<IG_ID>/media`, poll `status_code`, `POST /<IG_ID>/media_publish` | [Content publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing) |
| Trial Reels | `trial_params.graduation_strategy` is `MANUAL` or `SS_PERFORMANCE`. `media_type` must be `REELS`. Trial reels are shown only to non-followers | [IG User media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media) |
| Video | `video_url` must be public when Instagram fetches it. MP4 or MOV, H.264 or HEVC, 23 to 60 fps, 3 s to 15 min, 300 MB max. Containers expire after 24 h | IG User media |
| Quota | 100 API-published posts per 24 h on one part of the page, 50 in another, and 50 in the `content_publishing_limit` sample. Read the real number with `limit` | Content publishing, [Publishing limit](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user/content_publishing_limit.md) |
| Access | Standard Access covers only people with a role on the app. Other accounts need Advanced Access through App Review, and the app in Live mode | Get started |

## Decisions the team needs to make

1. **"Share winner to followers" cannot be a simple API call.** Meta's docs say `MANUAL` trial reels graduate "in the native app", and the run confirmed it: the app shows "Manage trial" with **Share to everyone** and **Turn on automatic sharing** ("Trial reels that get a lot of views within the first 72 hours will be shared to everyone"). `POST /experiments/{id}/share-winner` (FR-6.6) has to become in-app instructions (reel, ⋯, Manage trial, Share to everyone), or we use `SS_PERFORMANCE`, where Instagram decides within 72 hours. The prototype button and the landing page's "one tap" line need to change too.
2. **Serving outside creators needs App Review.** See the Access row above. Submit early, because the pilot depends on it.
3. **Every creator needs a business portfolio.** Unified Login lists it as required. Check how much work that is for a creator before recruiting.
4. **The API code still assumes Instagram Login.** `apps/api/app/services/instagram.py` and its connect flow need the same move to Unified Login (P1-03).
5. **The 24 h insights window may be incomplete.** Data can lag by up to 48 hours, and unavailable data comes back empty, not zero. Winner selection at 72 h is safer, and the 24 h number should be labelled preliminary.
6. **R2 video must be reachable by Instagram.** Use a signed URL that lasts through processing, and check that Instagram accepts it.

## Not confirmed by the docs

Verify these on the first real run. `CLAUDE.md` asks us to say so when unsure.

- Trial Reel eligibility rules. Meta's pages do not state them. The SRS says public account with 1,000+ followers, but a public account with 907 followers published both kinds (run below), so that rule is at least not enforced at 907. We still don't know what error an ineligible account gets, which the FR-6.8 fallback must detect.
- Whether the API returns the "Trial insights" the app shows for trial reels.
- Paging on `GET /<IG_ID>/media`. Meta documents time-based paging (`since`, `until`). The client follows cursors if they come back and otherwise reads one page.
- The `comments` fields on this host.
- Whether resumable upload works for us. Meta says it is "only for apps that have implemented Facebook Login for Business", which Unified Login is built on. If it works, Instagram would not need a public video URL.
- The "Instagram Login Compatible" tag shown on the configuration screen. No doc we found explains it.
- The Trial Reels publishing cap, if it differs from the normal quota.

## Run it

You need the Meta app, a professional Instagram account added as an Instagram Tester, and a token generated for it in the App Dashboard.

1. Check that git ignores the credentials file. This must print a `.gitignore` rule:

   ```
   git check-ignore -v spikes/instagram/.env.instagram
   ```

2. Create `spikes/instagram/.env.instagram` in your editor (never paste the token into a chat or a terminal command). Two lines:

   ```
   IG_ACCESS_TOKEN=<token from the App Dashboard>
   IG_USER_ID=<Instagram account id>
   ```

3. Run, from `spikes/instagram`:

   ```
   uv run cli.py accounts    # the token's Instagram accounts. IG_USER_ID must be one of these ids
   uv run cli.py account     # username, followers, media count
   uv run cli.py import      # counts only: reels, metric names, comments
   uv run cli.py limit       # publishing quota
   uv run cli.py publish "https://public-url/video.mp4" "Test caption"                            # Trial Reel, MANUAL
   uv run cli.py publish "https://public-url/video.mp4" "Test caption" --graduation SS_PERFORMANCE
   uv run cli.py publish "https://public-url/video.mp4" "Test caption" --normal                   # fallback, visible to followers
   ```

`publish` is real and public. Use a throwaway clip, and only with the account owner's agreement.

Tests are mocked and never call Instagram: `uv run pytest spikes/instagram`

## Results (run 2026-11-16)

Account: the team's test account, with its owner's agreement. Clip: 20 s, 1080 × 1920, H.264, 30 fps, AAC, 4.9 MB, served from a private R2 bucket through a 2-hour presigned GET URL.

| Check | Result | Notes |
|---|---|---|
| Token (Unified Login system user) | Pass | Generated in the App Dashboard, never expires. `accounts` lists the test account |
| Host and API version used | `graph.facebook.com`, `v27.0` | |
| Account type used | Public professional account, 907 followers, 67 posts | |
| Reels, insights and comments imported | Pass | 21 reels. All 6 metrics returned (views, reach, saved, shares, total_interactions, ig_reels_avg_watch_time). Comments readable. About 6.5 s |
| Trial Reel published (`MANUAL`) | Pass | Shown only in a "Trial reels" folder on the profile's Reels tab, labelled "This reel is a trial reel". Graduation is in the app: Manage trial, Share to everyone |
| Trial Reel published (`SS_PERFORMANCE`) | Pass | Same folder. The app describes automatic sharing as "a lot of views within the first 72 hours" |
| Ineligible account: what error? | Not seen | 907 followers was eligible. No under-threshold account found yet |
| Normal reel fallback | Pass | Posted to the profile like a normal reel, then deleted in the app |
| Real quota from `limit` | 100 per 24 h | Usage went 0, 1, 1, 2, then 3 a few minutes later: the counter lags. Deleting a reel did not lower it. Trial reels did not change `media_count` |
| Time from container to `FINISHED` | About 1 to 2 min | Whole publish command: 138 s, 76 s and 77 s, with checks once a minute |
| Resumable upload tried? | No | Not needed: the presigned R2 URL worked |
