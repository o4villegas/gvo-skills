# Stack Conventions — Lando's Default Build Targets

Source: empirical patterns extracted from `damage-suite`, `service-planner` (kc-cogs), and `kc-cogs`. Apply unless the user specifies otherwise.

## Runtime + framework

| Layer | Default | Alternate |
|-------|---------|-----------|
| Edge runtime | Cloudflare Workers | — |
| Backend API | Hono 4.x mounted at `/api/*` | Next.js 16 via `@opennextjs/cloudflare` (when SSR or App Router is needed) |
| Frontend | React 19 + Vite + `@cloudflare/vite-plugin` (SPA) | Next.js 16 App Router (when SSR) |
| Routing (SPA) | react-router-dom v7, `BrowserRouter` | — |
| Styling | Tailwind CSS 4 via `@theme inline` block in `index.css` — **never** `tailwind.config.js` | — |
| Components | shadcn/ui primitives in `src/components/ui/` or `src/react-app/components/ui/`, themed to midnight glass tokens | Hand-crafted for DamageSuite (uses unified `radix-ui` package, not individual `@radix-ui/react-*`) |
| ORM | Drizzle ORM over D1 | — |
| Database | Cloudflare D1 (SQLite) — **single DB per app**, never multi-DB splits | — |
| Object storage | Cloudflare R2 | — |
| Cache | Cloudflare KV | — |
| Charts | Recharts, lazy-loaded with manual chunks | — |
| Testing (unit) | Vitest, dual-project config (`node` for backend, `happy-dom`/`jsdom` for frontend) | — |
| Testing (e2e) | Playwright, two projects: `desktop` (1280×800) and `mobile` (375×812 Pixel 5) | — |
| Deploy | **`git push origin main`** → CF Git integration auto-builds | `wrangler deploy` only as fallback; `npm run check` (tsc + build + `wrangler deploy --dry-run`) for pre-push validation |

## TypeScript project references

Three tsconfig files via `tsc -b`:

| Config | Targets | Globals |
|--------|---------|---------|
| `tsconfig.app.json` | `src/react-app/**`, `src/types/**` | DOM, DOM.Iterable |
| `tsconfig.worker.json` | `src/worker/**` | WebWorker, `@cloudflare/workers-types` |
| `tsconfig.node.json` | Build scripts, configs | Node |

`strict: true`, `noUnusedLocals`, `noUnusedParameters` everywhere. Path alias `@/` → `src/react-app/` (or `src/` for Next.js projects).

## Shared types

`src/types/` holds cross-boundary types (items, counts, sales, orders, etc.), barrel re-exported via `src/types/index.ts`. Both frontend and worker import from here via relative paths.

## Worker architecture

```
src/worker/
├── index.ts          # Entry: exports { fetch, scheduled }
├── app.ts            # Hono app: health → auth middleware → db middleware → route modules
├── middleware/
│   ├── auth.ts       # HMAC cookie + Basic auth (skips /api/health, /api/auth/login)
│   └── db.ts         # Per-request Drizzle DB via c.set("db")
├── lib/              # crypto, error-handler, constants
├── db/
│   ├── schema.ts     # Drizzle schema — single source of truth
│   ├── index.ts      # createDb(d1) factory
│   └── migrations/   # drizzle-kit generated
├── routes/           # Hono route modules, one per domain
└── services/         # Business logic
```

**Per-request DB:** Always `createDb(c.env.DB)` — never a shared instance. The `db` middleware sets `c.set("db", ...)` and route handlers use `c.get("db")`.

**Env bindings** (regenerate types via `npm run cf-typegen`):

| Binding | Type | Purpose |
|---------|------|---------|
| `DB` | `D1Database` | Primary database |
| `R2_BUCKET` or named | `R2Bucket` | Photos, receipts, PDFs |
| `KV_CACHE` or named | `KVNamespace` | Session cache, precomputed snapshots, feature flags |
| `AI` | `Ai` | Workers AI (llama vision for OCR, etc.) |
| Secrets | `string` | `wrangler secret put` for prod, `.dev.vars` for local |

## API route pattern

```ts
import { getCloudflareContext } from "@opennextjs/cloudflare"; // only for Next.js mode
import { getDB } from "@/db";
import { requireAuth } from "@/lib/auth";

export async function POST(request: Request) {
  const { env } = await getCloudflareContext({ async: true });
  const db = getDB(env.DB);
  const user = await requireAuth(request, db);
  // ... env.R2_BUCKET, env.KV_CACHE
}
```

For Hono routes: `const db = c.get("db"); const user = await requireAuth(c);`

## Database conventions

- **UUID text primary keys** via `crypto.randomUUID()` (Web API, not `crypto.createHash`)
- **ISO 8601 timestamps** via SQLite `datetime('now')`
- **Every table** has `created_at` and `updated_at`
- **Enums** as SQLite text with Drizzle constraints
- **Foreign keys**: cascade on parent-child delete, set null for optional relationships
- **Every query uses Drizzle** — `grep db.prepare\|db.exec` must be zero
- **D1 batch pattern** — chunk inserts at 15 items max (D1 SQL variable limit):
  ```ts
  const BATCH_SIZE = 15;
  for (let i = 0; i < items.length; i += BATCH_SIZE) {
    const batch = items.slice(i, i + BATCH_SIZE);
    const stmts = batch.map(item => db.insert(table).values(item));
    await (db as any).batch(stmts as any);
  }
  ```
- **All dev uses remote D1** (kc-cogs convention) — no local database. Exception: seed-local scripts for test fixtures.

## Auth

Custom token-based sessions backed by D1 (or HMAC cookie for single-operator tools). Key rules:
- Password hashing via `crypto.subtle.digest("SHA-256", ...)` — **never** bcrypt
- Cookie `secure` flag must be conditional: `secure: !c.req.url.includes("localhost")`
- Middleware skips `/api/health`, `/api/auth/login`, OAuth callbacks
- Roles: `admin | manager | tech` (damage-suite) or none (single-operator)
- Frontend auth stored **in memory**, never `localStorage`

## Offline-first capture

- IndexedDB via `idb` package (named `cogs-offline` or similar)
- Service Worker registered in `main.tsx`, script at `public/sw.js`, generated post-build with asset hashing
- Entry shape: `{ itemId, quantity, countedAt, synced: 0|1 }`
- Sync on reconnect, batch-POST all `synced: 0` entries
- Conflict resolution: last-write-wins per key, append-only for photos/annotations

## Testing

**Unit (Vitest)** — dual-project config:
- `backend` — node env, tests in `src/worker/__tests__/` or `tests/backend/`
- `frontend` — happy-dom/jsdom env, tests in `src/react-app/__tests__/` or `tests/frontend/`
- D1 mock via `tests/helpers/d1-mock.ts` (better-sqlite3) — MUST detect SELECT/WITH/RETURNING vs INSERT/UPDATE/DELETE to call `.all()` vs `.run()`
- Frontend API mocked via MSW (`tests/mocks/handlers.ts`)
- Recharts mocked in frontend tests — jsdom cannot render SVG
- Polyfills: `ResizeObserver`, pointer capture (Radix UI needs these)

**E2E (Playwright)** — `desktop` + `mobile` projects, helpers in `tests/e2e/helpers/`.

**Single test:** `npx vitest run path/to/file.test.ts`

## Verification gate

The canonical one-liner every project uses:

```bash
npx tsc -b --noEmit && npm run lint && npm test && npm run build && echo "All gates passed"
```

Full gate adds `npm run test:e2e && npx wrangler deploy --dry-run`.

All gates must pass before declaring work complete. `&&` chaining stops on first failure.

## Design system — Midnight glassmorphism

**Base palette** (apply unless the project explicitly overrides):

| Token | Value | Role |
|-------|-------|------|
| `--color-bg-base` | `#0A0D12` | Page background |
| `--color-bg-glass` | `rgba(255,255,255, 0.035)` | Card fill |
| `--color-bg-glass-elevated` | `rgba(255,255,255, 0.05)` | Elevated cards, modals |
| `--color-border-glass` | `rgba(255,255,255, 0.055)` | Default borders |
| `--color-text-primary` | `rgba(255,255,255, 0.92)` | Headings |
| `--color-text-body` | `rgba(255,255,255, 0.65)` | Body (WCAG AA floor) |
| `--color-text-muted` | `rgba(255,255,255, 0.50)` | Labels |
| `--color-brand` | `#FF9F43` | Primary actions, focus rings |
| `--color-cyan` | `#22D3A8` | Positive delta, financials accent |
| `--color-violet` | `#9B7AFF` | Inventory/secondary accent |
| `--color-blue` | `#3B9EFF` | Data/tertiary accent |
| `--color-warning` | `#FFC55A` | Caution |
| `--color-red` | `#FF6B6B` | Danger only — never decorative |

Typography: `Outfit Variable` headings, `IBM Plex Mono` data, `Plus Jakarta Sans Variable` body.

**Glass cards:** `background: var(--color-bg-glass); backdrop-filter: blur(22px); border: 0.5px solid var(--color-border-glass); border-radius: 14px;`

**Color rule:** color = signal + section ownership. Orange = brand + Dashboard. Teal = positive + Financials. Violet = Inventory. Blue = Data. Warning = caution. Red = danger only.

**Accessibility floor:** labels ≥ 0.50 opacity, body ≥ 0.65, interactive ≥ 0.80.

Map shadcn CSS vars (`--background`, `--foreground`, `--card`, `--primary`, `--destructive`) to these tokens. Do not use shadcn default themes.

## Do-not list (stack-level)

| Prohibition | Use instead | Why |
|-------------|-------------|-----|
| Node APIs (`fs`, `path`, `crypto.createHash`, `Buffer.from`) | Web APIs (`crypto.randomUUID`, `crypto.subtle`, `TextEncoder`) | Workers runtime has no Node |
| `bcrypt` | `crypto.subtle.digest("SHA-256", …)` | No Node crypto |
| `localStorage` / `sessionStorage` | IndexedDB via `idb` or `offline-store.ts` | 5MB max, sync, unavailable in Workers |
| `@hono/vite-dev-server` | `@cloudflare/vite-plugin` (`cloudflare()`) | CF plugin handles Workers runtime |
| `tailwind.config.js` | `@theme inline` block in `index.css` | Tailwind v4 |
| `db.batch()` with >15 statements | Chunks of 15 | D1 SQL variable limit |
| Hardcoded hex colors | `var(--color-*)` or Tailwind tokens (`bg-ds-*`, `text-color-*`) | Design system enforcement |
| `useEffect` for data fetching | TanStack Query or server components | Stale-closure bugs |
| Raw errors to client | `{ error: string }` structured responses | No stack-trace leaks |
| `console.log` in src | Structured logger (`src/lib/utils/logger.ts`) | Log hygiene |
| `wrangler deploy` as primary | `git push origin main` (auto-deploy) | Reproducible CI build |
| Multiple D1 databases per app | Single DB, multi-schema files if needed | Consolidation, easier queries |

## Directory shape

```
src/
├── react-app/ (or app/)
│   ├── components/ui/       # shadcn primitives
│   ├── components/shared/   # Domain components
│   ├── components/layout/   # Shell, nav, header
│   ├── pages/               # Route components (lazy-imported)
│   ├── hooks/               # usePageData, useOfflineSync, etc.
│   ├── lib/                 # paths, api, auth, format, offline-store
│   └── index.css            # @theme inline tokens
├── worker/
│   ├── index.ts, app.ts
│   ├── middleware/, lib/, db/, routes/, services/
│   └── __tests__/
└── types/
    └── index.ts             # Barrel exports

tests/
├── backend/  frontend/  e2e/
├── helpers/  (d1-mock, test-app)
├── mocks/    (MSW handlers)
└── setup/    (backend.ts, frontend.ts)
```

`.claude/skills/` holds project-specific skill files. Agent prompts in `prompts/` if used.
