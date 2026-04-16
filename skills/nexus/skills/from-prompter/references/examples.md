# Example V0 Prompts

These show target quality for each category. Use as calibration, not templates.

---

## Example 1: Bug Fix (Simple — ~110 lines)

```markdown
# Fix Toast Daily Email Parser Skipping Weekend Summaries

## Objective
The `from-kc-records` Gmail scanner correctly parses Toast daily sales emails Mon–Fri but silently skips Saturday and Sunday summary emails. Fix the parser to handle weekend email format differences and ingest all 7 days.

## Context
- **Project**: service-planner (kava bar operations PWA)
- **Stack**: Hono + React 19 + Cloudflare Workers (D1/R2/KV), Drizzle ORM
- **Relevant paths**:
  - `src/workers/gmail-scanner/toast-parser.ts` — main parser
  - `src/workers/gmail-scanner/email-patterns.ts` — regex patterns for subject matching
  - `src/db/schema/revenue.ts` — D1 revenue table schema
  - `test/gmail-scanner/toast-parser.test.ts` — existing tests (weekday only)

## Current State
- Weekday emails: subject line "Daily Sales Summary – [Weekday], [Date]" → parsed correctly
- Weekend emails: subject line "Weekend Sales Summary – [Sat/Sun], [Date]" → not matched by `DAILY_SUBJECT_REGEX` in email-patterns.ts
- No error thrown — the email is silently filtered out at the subject-match step
- D1 `revenue` table has gaps every Saturday and Sunday since October 2025

## Requirements
1. Update `DAILY_SUBJECT_REGEX` to match both "Daily Sales Summary" and "Weekend Sales Summary" prefixes
2. Weekend email body uses a two-column layout (Sat | Sun) instead of single-day — parser must extract both days as separate revenue records
3. Add test cases for Saturday-only, Sunday-only, and combined weekend emails
4. Backfill: scan Gmail for all weekend emails since Oct 5, 2025 and ingest missing records

## Do Not
- Do not modify the revenue table schema — weekend records use the same columns
- Do not change how weekday emails are parsed — only extend to handle weekend format
- Do not delete or modify existing test cases

## Verification
- Run `pnpm test toast-parser` — all existing + new tests pass
- Query D1: `SELECT date, total FROM revenue WHERE day_of_week IN ('Saturday','Sunday') ORDER BY date DESC LIMIT 14` — returns 14 rows with no gaps in last 7 weeks
- Console clean of warnings during a full Gmail scan dry-run
```

---

## Example 2: New Feature Build (Standard — ~220 lines, abbreviated here)

```markdown
# Add Share/Export Flow to Shellpass Passport

## Objective
Build a share/export feature that lets users share their botanical bar passport progress as a shareable image (Instagram Stories format, 1080×1920) or a deep link that opens the app to their public profile.

## Context
- **Project**: Shellpass (botanical bar passport PWA)
- **Stack**: React 19 + Vite + Tailwind 4 + Hono + Cloudflare Workers (D1/R2/KV)
- **Relevant paths**:
  - `src/components/passport/` — existing passport card components
  - `src/routes/profile.tsx` — user profile page (share source)
  - `src/workers/api/routes/user.ts` — user API endpoints
  - `src/lib/canvas-utils.ts` — existing canvas helpers for stamp rendering

## Current State
- Users can view their passport with stamps but cannot share it
- Profile page exists but is not publicly accessible (requires auth)
- Canvas utilities already render individual stamps to canvas elements
- No public profile route exists; no Open Graph meta tags

## Requirements

### Functional
1. "Share" button on profile page opens a bottom sheet with two options: "Share Image" and "Share Link"
2. Share Image: generates a 1080×1920 canvas with passport summary (name, stamp count, recent 6 stamps, QR code linking to public profile) → triggers native Web Share API with the image, falls back to download
3. Share Link: copies `https://shellpass.app/u/{username}` to clipboard with toast confirmation
4. Public profile route `/u/{username}` displays read-only passport (no auth required)
5. Open Graph meta tags on public profile for rich link previews (title, description, stamp count, preview image)

### Non-Functional
- Image generation completes in <2s on mid-range mobile
- Public profile loads in <1.5s (static generation preferred)
- Share sheet respects system dark/light mode

## Best Practices
- Use `html2canvas` or `@napi-rs/canvas` — avoid heavy server-side rendering for a PWA
- Web Share API Level 2 supports file sharing; check `navigator.canShare({files: [...]})` before offering image share
- OG image: pre-generate on stamp save, store in R2, serve via `/og/{username}.png`

## Implementation Approach
1. Create public profile route + API endpoint (no auth middleware)
2. Build canvas-to-image generation utility extending existing canvas-utils
3. Add share bottom sheet component
4. Wire Web Share API with fallback
5. Add OG meta tag generation + R2 image storage on stamp save

## Agent Team Configuration
Not needed — this is a single linear workflow.

[... Do Not, Verification, Core Principles sections per template ...]
```

---

## Quality Signals

A good V0 prompt has these properties:
- **Grep-testable file paths** — every path can be verified with `ls` or `find`
- **Zero hand-waving requirements** — "improve performance" is bad; "reduce LCP from 3.2s to <1.5s" is good
- **Task-specific Do Nots** — generic "don't break things" doesn't count
- **Concrete current state** — not "it's partially working" but "weekday parsing works, weekend silently dropped"
- **Verification that proves completion** — not "check it works" but a specific query, test command, or observable behavior
