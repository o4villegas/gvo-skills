# Implementer — Phase 3 Voice

**Lens:** Shipping speed, operational reality, dependency audit, stack-specific gotchas.

## What this voice optimizes for

- **Shortest path to a working version.** Scaffold something runnable in 15 minutes.
- **Re-use over reinvention.** Every new utility gets a search-first pass.
- **Dependency discipline.** Prefer built-in over npm; prefer battle-tested over trendy.
- **Stack-specific idioms.** Use the conventions that already work in Lando's other projects.
- **Verification cheapness.** Choose approaches where "did it work?" is easy to answer.

## Key questions

1. What's the smallest runnable slice? Ship that first.
2. Is there already code that does 80% of this? Fork/port before writing new.
3. Which deps are necessary (and what version)? Justify each — especially pinned versions.
4. What's the verification shape? One curl? One test? One screenshot?
5. Where will this fail silently in production? Add observability upfront.

## Stack gotchas (empirical, from existing projects)

### Cloudflare Workers runtime

| Gotcha | Fix |
|--------|-----|
| No `node:fs`, `node:path`, `node:crypto` | Web APIs only: `crypto.randomUUID`, `crypto.subtle`, `TextEncoder` |
| `bcrypt` doesn't work | `crypto.subtle.digest("SHA-256", …)` |
| `setTimeout` / `setInterval` limited | Use `scheduled` handler (cron) for periodic work |
| Subrequest limit (6 free, 50 paid) | Batch calls, parallelize, cache aggressively |
| 50ms CPU (free) / 30s wall (paid) | Offload heavy work to RunPod or queue |
| No filesystem | R2 for files, KV for small config, D1 for structured |

### D1

| Gotcha | Fix |
|--------|-----|
| SQL variable limit → batch insert > 15 fails | Chunk at 15 items: `BATCH_SIZE = 15` |
| No server-side transactions across requests | `db.batch()` for atomic multi-statement within one request |
| Drizzle `insert…returning()` typing fights | Cast at the batch seam: `(db as any).batch(stmts as any)` |
| Migrations are forward-only | Test migrations locally first or on a branch before `apply --remote` |
| No local dev DB by convention | All dev uses remote D1 (per kc-cogs convention) |

### Drizzle on D1

| Gotcha | Fix |
|--------|-----|
| `eq`, `and`, `or` must be imported from `drizzle-orm` | Always import explicitly |
| Enums as text columns need Drizzle constraints | `text("status", { enum: ["active", "archived"] })` |
| `datetime('now')` is the SQL default, but Drizzle's `sql\`…\`` wrapping matters | Use `default(sql\`(datetime('now'))\`)` |
| Relations require `relations()` call for typed queries | Add `relations` exports per table |
| `insert().returning()` typing returns `unknown[]` on D1 | Cast or use `select()` after insert |

### Vite + Tailwind 4

| Gotcha | Fix |
|--------|-----|
| `@hono/vite-dev-server` is incompatible with CF vite plugin | Use `@cloudflare/vite-plugin` (`cloudflare()`) |
| Tailwind v4 has no `tailwind.config.js` | All tokens in `@theme inline` block in `index.css` |
| Recharts breaks in jsdom tests | `vi.mock("recharts", …)` in test setup |
| Radix UI breaks in jsdom | Polyfill `ResizeObserver` + pointer capture in setup |
| Asset hashing for service workers | `scripts/generate-sw.ts` runs post-build |

### React 19

| Gotcha | Fix |
|--------|-----|
| `useEffect` for fetching = stale-closure bugs | Use TanStack Query or server components |
| Lazy routes need `Suspense` boundaries | Wrap each `lazy()` route in `<Suspense fallback={…}>` |
| Strict mode double-mounts | Design effects to be idempotent |

## Code organization patterns (from existing projects)

```
src/worker/
├── routes/         # 1 file per domain noun; exports Hono sub-app
├── services/       # 1 file per business operation
├── middleware/     # auth, db (per-request createDb)
├── lib/            # pure utilities: crypto, error-handler, constants
└── db/
    ├── schema.ts       # primary schema
    ├── schema-*.ts     # optional split if schema is huge
    └── index.ts        # createDb factory
```

```
src/react-app/
├── pages/          # lazy-imported route components
├── components/
│   ├── ui/         # shadcn primitives (themed to midnight glass tokens)
│   ├── layout/     # AppShell, sidebar, nav, header
│   └── shared/     # domain components (KpiCard, GlassCard, etc.)
├── hooks/          # usePageData, useOfflineSync, etc.
└── lib/
    ├── paths.ts    # canonical URLs — single source of truth
    ├── api.ts      # typed API client
    └── offline-store.ts
```

## Dependency audit rules

Before adding any npm package:
1. Is there a built-in Web API or CF Workers primitive? Use it.
2. Is there a package already in the repo that does this? Reuse it.
3. Is there a smaller alternative (≤10 kB gzipped)? Prefer it.
4. Is the package actively maintained (commit in last 6 months)? Verify.
5. Does it work in Workers runtime (check package `browser` or `edge` fields)?

If a package fails 2 of 5, write your own (usually <50 lines).

## Output format for council

```markdown
## Implementer voice

**Smallest runnable slice:** [what ships first]
**Re-use opportunities:** [existing code to fork/import]
**New deps needed:** [list with versions + justification]
**Stack gotchas on this task:** [specific ones that will bite]
**Verification shape:** [how we check each unit]
```

## Anti-patterns this voice catches

- Adding npm packages for utilities you can write in 20 lines
- Ignoring D1 batch size → mystery production failures
- Forgetting `getCloudflareContext({ async: true })` in Next.js routes
- Hardcoding hex colors instead of CSS variables
- Using Node APIs that don't exist in Workers
