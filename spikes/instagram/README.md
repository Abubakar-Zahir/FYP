# Instagram spike (P0-08, P0-09)

**Status: code ready and unit tested, not yet run against a real account.** These tasks are done only when the results table below is filled in.

Questions: can we log in, import reels, and publish one Trial Reel through the official API? Which account type does it need?

## What the docs say (read 2026-11-03)

| Question | Answer | Source |
|---|---|---|
| Account type | Instagram professional account, business or creator. No linked Facebook Page needed | [Overview](https://developers.facebook.com/docs/instagram-platform/overview) |
| Host | `graph.instagram.com` for Instagram Login | Overview |
| Scopes | `instagram_business_basic`, `_content_publish`, `_manage_insights`, `_manage_comments` | [Business Login](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login), [Insights](https://developers.facebook.com/docs/instagram-platform/reference/instagram-media/insights) |
| Publishing | `POST /<IG_ID>/media`, poll `status_code`, `POST /<IG_ID>/media_publish` | [Content publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing) |
| Trial Reels | `trial_params.graduation_strategy` is `MANUAL` or `SS_PERFORMANCE`. `media_type` must be `REELS` | [IG User media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media) |
| Video source | `video_url` must be a public URL. Instagram Login cannot use resumable upload | Content publishing |
| Quota | 100 published posts per 24 h on one part of the page, 50 on another. Read the real number with `limit` | Content publishing |

## Decisions the team needs to make

1. **"Share winner to followers" cannot be a simple API call.** Meta's docs say `MANUAL` trial reels graduate "in the native app". [Ayrshare's docs](https://www.ayrshare.com/docs/de/apis/post/social-networks/instagram.md) also say the API does not expose graduation. `POST /experiments/{id}/share-winner` (FR-6.6) probably has to become "open Instagram and share it" instructions, or we use `SS_PERFORMANCE`, where Instagram decides. The prototype button and the landing page's "one tap" line would need to change too.
2. **Serving outside creators needs App Review.** Standard Access covers people with roles on the app. Accounts we don't own or manage need Advanced Access, which requires Meta App Review. Submit early, because the pilot depends on it.
3. **The 24 h insights window may be incomplete.** Data can lag by up to 48 hours, and unavailable data comes back empty, not zero. Winner selection at 72 h is safer, and the 24 h number should be labelled preliminary.
4. **R2 video must be reachable by Instagram.** Use a signed URL that lasts through processing, and check that Instagram accepts it.

## Not confirmed by the docs

Verify these on the first real run. `CLAUDE.md` asks us to say so when unsure.

- `GET /me/media` on `graph.instagram.com`, and its cursor paging. The page we could read shows the Facebook host and time-based paging.
- Field names for `GET /me` and the `config` field on `content_publishing_limit`.
- Trial Reel eligibility rules. The SRS says public account with 1,000+ followers, and Meta's pages we read do not state them. We also don't know what error an ineligible account gets, which the FR-6.8 fallback must detect.
- The Trial Reels publishing cap, if it differs from the normal quota.
- `API_VERSION` in `ig_client.py` comes from a doc sample. Use the latest when you run this.

## Run it

You need a Meta app with Instagram Login, an HTTPS redirect URI registered on it, and a professional Instagram account with a role on the app.

```
export IG_APP_ID=... IG_APP_SECRET=... IG_REDIRECT_URI=https://your-domain/callback
cd spikes/instagram
uv run cli.py login                     # open the URL, approve, copy `code` from the redirect
uv run cli.py exchange "<code>"         # saves the token to .env.instagram, which git ignores
uv run cli.py account
uv run cli.py import
uv run cli.py limit
uv run cli.py publish "https://public-url/video.mp4" "Test caption"            # Trial Reel
uv run cli.py publish "https://public-url/video.mp4" "Test caption" --normal   # fallback
```

The video must meet [Reels specs](https://developers.facebook.com/docs/instagram-platform/content-publishing). Use a throwaway test clip, because publishing is real and public.

Tests are mocked and never call Instagram: `uv run pytest spikes/instagram`

## Results (fill in after running)

| Check | Result | Notes |
|---|---|---|
| Login and long-lived token | | |
| Account type used | | |
| Reels, insights and comments imported | | |
| Trial Reel published (`MANUAL`) | | |
| Trial Reel published (`SS_PERFORMANCE`) | | |
| Ineligible account: what error? | | |
| Normal reel fallback | | |
| Real quota from `limit` | | |
| Time from container to `FINISHED` | | |
