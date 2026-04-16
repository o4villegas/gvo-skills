# Phase 1 — Interview

**Goal:** A 2–3 sentence task spec the user would call "exactly right," extracted via 4–8 plain-language questions.

**Exit condition:** You can write: "We're building X so Y can do Z, running on Lando's default stack, scoped to [explicit constraints]" — and the user, if shown it, would say "exactly."

## Rules

- **≤ 3 questions per turn.** Yes/no, this-or-that, or pick-from-3. Multi-select only when choices are non-exclusive.
- **Translate technical decisions into user outcomes.** "Should we use Redis or KV?" → "Should data stay cached for 60s or a day?"
- **Use the integrated `AskUserQuestion` tool** — never ask technical questions in free text. Every question has a recommended option (first) marked "(Recommended)" + 2–3 alternatives with descriptions that include tradeoffs.
- **Never ask a question whose answer can be derived from the codebase.** Read first, ask second. Use `Glob`, `Grep`, or the from-desktop MCP tools (`mcp__claude_ai_from-desktop__*`, if the connector is attached) when codebase access is relevant.
- **Bug fixes and quick tasks skip Phase 1.** Route directly: bug → Phase 5 (`focused-fix`, `verification-loop`); lookup → Direct (no pipeline).

## Question categories (cover in this order)

| Order | Category | Example question |
|-------|----------|------------------|
| 1 | **What** | "Is this a new app, a feature added to an existing project, or a research task?" |
| 2 | **Who** | "Who uses it — field worker, desk operator, both, or internal dev only?" |
| 3 | **Where** | "Does this deploy to your CF Workers stack, a one-off artifact, or a local script?" |
| 4 | **Scale** | "How many users on day one — <10, 10–1000, or >1000?" |
| 5 | **Constraints** | "Any non-negotiables? Offline support, specific framework, privacy tier, budget?" |
| 6 | **Existing work** | "Is there a repo or file I should read first to ground the design?" |

Pick 1–3 categories per turn. Stop when the spec is crisp.

## Project-type templates

### New app/feature
1. Turn 1: What (app type) + Who (primary persona) + Scale
2. Turn 2: Where (deploy target) + Existing work (any prior art to read)
3. Turn 3 (if needed): Constraints (offline, auth, design direction)

### Enhancement to existing project
1. **First:** `cd` into the project, read `CLAUDE.md`. Use `repo-intel` if available.
2. Turn 1: Which specific surface are we touching? (list them if not obvious)
3. Turn 2: What's the user-facing outcome that tells us this worked?

### Bug fix (usually 1 turn only)
1. "What's broken, what should it do instead, and where does it live (file/route/URL)?"
2. Route to Phase 5 with `focused-fix` loaded.

### Research / codebase question
1. Turn 1: What specifically do you want to know — architecture map, answer a question, or produce a written summary?
2. Turn 2 (only if writing): What audience — you, a teammate, or external docs?
3. Route to Phase 2 with `codebase-onboarding` + `repo-intel`.

## Anti-patterns

| Do NOT | Do instead |
|--------|------------|
| Ask "Should we use Drizzle or Prisma?" | Ask "Do you want type-safe queries with migrations, or the lightest possible setup?" |
| Ask 6 questions in one turn | Max 3; the rest come after answers narrow the space |
| Accept "build me a webapp" and start coding | Push back: "What problem is it solving for whom?" |
| Skip Phase 1 because the request "looks clear" | Only skip for bug fixes, lookups, or explicit continuation of prior context |
| Write 2–3 sentence spec and proceed without showing it | Always read the spec back in the final question: "I've got: [spec]. Ready for Phase 3?" |

## Handoff to Phase 2

When exit condition is met, write the 2–3 sentence spec to working memory and proceed. If the user pushes back, treat the pushback as new information — refine, don't restart.
