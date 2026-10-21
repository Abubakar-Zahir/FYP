# frontend.md

The frontend is built first, as a clickable prototype with mock data. The real API replaces the mocks screen by screen.

## Stack

| Need | Choice |
|---|---|
| Framework | Next.js (App Router), TypeScript strict |
| Styling | Tailwind CSS, shadcn/ui components |
| Server state | TanStack Query |
| Forms | React Hook Form and Zod |
| Charts | Recharts |
| Mocking | MSW (Mock Service Worker), so mocks behave like the real network |
| API types | Generated from the backend OpenAPI with `openapi-typescript` |
| Auth | Supabase Auth client (Google and email) |
| Tests | Vitest, Testing Library, Playwright |
| Package manager | pnpm |

Pin versions in `package.json` and commit the lockfile.

## Folder structure

```
apps/web/
  src/
    app/                    routes (App Router)
      (auth)/login
      (app)/dashboard
      (app)/onboarding
      (app)/dna
      (app)/dna/[id]
      (app)/studio
      (app)/editor
      (app)/variants
      (app)/comments
      (app)/reports
    components/
      ui/                   shadcn primitives
      <feature>/            feature components (dna, studio, variants...)
    lib/
      api/                  generated types, typed fetch client, query hooks
      mocks/                MSW handlers and fixtures
      utils/
    styles/
  tests/                    Playwright flows
```

Rules: a feature component lives in its feature folder. Shared primitives live in `components/ui`. No feature imports another feature's internals.

## Prototype scope (weeks 1 to 2)

Eight screens, all with mock data, all with loading, empty and error states:

| # | Screen | What it shows |
|---|---|---|
| 1 | Login | Google and email sign in |
| 2 | Onboarding | Role (creator or brand), niche, language mix (English, Urdu, Roman Urdu), tone, goals. Connect Instagram button (mocked) |
| 3 | Dashboard | Recent reels with views, saves, shares, watch time. Best performing formats. Quick actions |
| 4 | DNA library | Cards of analysed reels with hook type, outlier score, save as template |
| 5 | DNA detail | Timeline of beats, pacing (cuts per 10 s), overlays, CTA, transcript |
| 6 | Script studio | Pick template, enter topic, get 5 hooks with scores, 3 angles, full script, language switch |
| 7 | Editor and variants | Upload footage, caption style, preview, create 3 to 5 variants, publish as Trial Reels, winner view at 24 h and 72 h |
| 8 | Comments and weekly report | Theme clusters, comment types, ideas from themes, weekly summary |

Out of the prototype: brand module, scheduling, B-roll picker, settings pages beyond disconnect and delete data.

## Prototype done when

1. All 8 screens are reachable through real navigation.
2. A user can click through: onboarding, DNA library, script, variants, comments.
3. Every screen works at 375 px and 1280 px.
4. Every screen has loading, empty and error states.
5. Data comes only from MSW handlers that match the planned API shapes in `docs/backend.md`.
6. Teammates and one or two real creators have tried it and given feedback.

## Data and API rules

1. One typed client in `lib/api`. Components never call `fetch` directly.
2. One query hook per resource, for example `useReels()`, `useDnaRecord(id)`.
3. Long jobs: call the endpoint, get `job_id`, poll `GET /jobs/{id}` with TanStack Query `refetchInterval`, stop on `done` or `failed`. Show progress and a retry button on failure.
4. Mock handlers return the same shapes as the backend schemas. When the backend ships an endpoint, delete its mock handler.
5. Keep mock fixtures realistic: Roman Urdu comments, mixed-language captions, real-looking numbers.

## UI rules

1. Design tokens (colors, spacing, radius, type scale) live in the `@theme` block of `src/app/globals.css` (Tailwind v4 has no `tailwind.config`). No hard-coded hex values in components.
2. One accent color, neutral base, clear hierarchy. Keep it plain and fast to scan. Dashboards are for decisions, not decoration.
3. Scores always show the top 3 contributing factors next to the number (explainability requirement).
4. Show job status clearly: queued, running, done, failed. A failed job never blocks the page.
5. Core flow from idea to published variants must stay under 10 clicks.
6. Support right-to-left text in caption and comment displays where Urdu script appears. Use `dir="auto"`.
7. Accessible by default: labels, focus rings, keyboard use, AA contrast.

## Performance

1. Server Components for static and data-fetch shells. Client Components only for interactivity.
2. Lazy-load the editor and chart libraries.
3. Use `next/image` for thumbnails. Video preview uses signed R2 URLs, never proxied through the API.
4. Uploads go directly to R2 with a presigned URL from the backend. Show upload progress.

## Environment variables

```
NEXT_PUBLIC_API_BASE_URL=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_USE_MOCKS=true
```

Nothing else is exposed to the browser.

## Testing

1. Component tests for forms, score cards and job status.
2. Playwright flows: onboarding, generate script, create variants, view comment themes.
3. Playwright runs against MSW in CI. A smaller set runs against the real API once it exists.
