# Phase 5 — Implementation

**Goal:** Build the approved plan from Phase 4 to production quality. **No user intervention** — run the 8-step sequence autonomously, stalling only on genuine blockers.

## Skills to load

| Skill | Role |
|-------|------|
| `orchestrate-review` | Parallel multi-pass code review (quality, security, performance, coverage) |
| `deslop` | Clean AI artifacts: debug statements, placeholders, dead code, TODO comments |
| `verification-loop` | Quality gate: build → types → lint → tests → security → e2e |
| `continuous-agent-loop` | Autonomous iteration loop with stall detection |
| `focused-fix` | Bug-fix fast path (when invoked as bug route) |
| `karpathy-coder` | Tight change → verify → repeat cadence |
| `search-first` | Check existing patterns before creating new ones |

## The 8-step sequence

Run each step to completion. Do **not** skip. Each step ends with a verification gate.

### 1. Scaffold
- Project structure, `package.json`, `wrangler.json`, `tsconfig*.json`, `vite.config.ts`, `drizzle.config.ts`
- Initial commits: one commit per config file so diffs stay reviewable
- Gate: `npx tsc --noEmit` passes on the skeleton

### 2. Core
- Data model first → API second → UI third
- `src/worker/db/schema.ts` → `drizzle-kit generate` → migrations applied
- Route modules in `src/worker/routes/` using `c.get("db")` pattern
- UI components consume the typed API client (`src/react-app/lib/api.ts`)
- Gate: happy-path flow works end-to-end once (manual check via `curl` + browser)

### 3. Polish
- Error handling at every boundary (structured `{ error: string }`, never raw)
- Loading states (skeleton, spinner, stale-while-revalidate via `usePageData`)
- Empty states (never zero-valued cards — show onboarding prompt instead)
- Edge cases from the Phase 3 risk register
- Gate: UI handles 500/timeout/empty/large-data without crashing

### 4. Deslop
Run the `deslop` skill. Minimum checks (from `references/stack-conventions.md`):

```bash
grep -rn "TODO\|FIXME\|XXX" src/ --include="*.ts" --include="*.tsx"          # zero
grep -rn "console\.log" src/ --include="*.ts" --include="*.tsx" | grep -v test  # zero
grep -rn "any" src/ --include="*.ts" --include="*.tsx" -l                      # zero (excluding narrow guards)
grep -rn "style={{" src/components/ --include="*.tsx"                          # zero
grep -rn "bg-\[#" src/ --include="*.tsx"                                       # zero hardcoded hex
```

Remove every match or justify inline with a `// REASON: …` comment.

### 5. Test
Run `verification-loop`. The canonical gate:

```bash
npx tsc -b --noEmit && npm run lint && npm test && npm run build && echo "All gates passed"
```

Full gate: add `npm run test:e2e && npx wrangler deploy --dry-run`.

**Coverage target:** 80%+ via Vitest unit + integration. Every route has a backend test. Every interactive component has a frontend test. Every user flow has an e2e test.

### 6. Review
Run `orchestrate-review` — parallel pass of 4 lenses:
- **Code quality:** readability, nesting, duplication, naming
- **Security:** auth on every mutation, Zod on every POST/PUT/PATCH, no secret leakage, no injection vectors
- **Performance:** N+1 queries, missing indexes, bundle size, render churn
- **Test coverage:** missing paths, brittle mocks, flaky assertions

Each lens produces a list of issues tagged CRITICAL / HIGH / MEDIUM / LOW.

### 7. Harden
- Fix every CRITICAL. Fix every HIGH unless justified in the risk register.
- MEDIUM at author discretion; LOW deferred to Phase 6 polish unless trivial.
- Re-run `verification-loop` after every batch of fixes.

### 8. Iterate
Repeat 5 → 6 → 7 until:
- `verification-loop` passes cleanly
- `orchestrate-review` reports zero CRITICAL/HIGH
- `deslop` reports zero matches

**Stall detection:** if the same issue surfaces twice in a row, stop the loop and escalate to the user with the specific blocker + a proposed resolution.

## Production-quality rules (enforce throughout)

| Rule | Verification |
|------|--------------|
| No TODOs in src | `grep -rn "TODO\|FIXME" src/` = zero |
| No placeholders | `grep -rn "placeholder\|coming soon\|lorem ipsum" src/` = zero |
| No commented-out code | Manual review during Phase 6 |
| Every API route validates input | `grep -rL "z\." src/worker/routes/ --include="*.ts"` = zero (or `REASON` comment) |
| Every database query uses Drizzle | `grep -rn "db\.prepare\|db\.exec" src/` = zero |
| No Node APIs in Worker | `grep -rn "from \"node:" src/worker/ src/react-app/` = zero |
| No `localStorage` | `grep -rn "localStorage\|sessionStorage" src/react-app/` = zero |
| No `bcrypt` | `grep -rn "bcrypt" src/` = zero |
| No hardcoded hex colors | `grep -rn "#[0-9a-f]\{6\}" src/ --include="*.tsx"` outside token files = zero |

## Commit discipline

- Commit after every step ends green. Never batch unrelated fixes.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- Do NOT `git push` until Phase 6 — implementation is local-first.

## Handoff to Phase 6

When the 8-step loop exits clean, hand off with: "Phase 5 complete. N commits. All gates green. Ready for pre-delivery review."
