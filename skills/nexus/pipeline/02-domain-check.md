# Phase 2 — Domain Check

**Goal:** Load the specific skills and context needed for this task — no more, no less — and verify the sources you're relying on are current and relevant.

## Skill loading protocol

1. **Read `~/.claude/skills/nexus/registry.json`.**
2. Extract trigger phrases from the Phase 1 spec (nouns, verbs, domain words).
3. Match triggers against `registry.json[].triggers` arrays.
4. **Load matched skills by reading their `SKILL.md`** (one `Read` call each). Never load more than 6 skills for a single task — if more match, drop the least relevant.
5. Report what you loaded: `"Loaded: council, blueprint, verification-loop, codebase-onboarding"`

**Core skills you load without registry lookup** (always-available table in master `SKILL.md`):
- `council`, `blueprint`, `debate` — planning
- `orchestrate-review`, `deslop`, `verification-loop`, `continuous-agent-loop` — implementation
- `validate-delivery` — delivery
- `repo-intel`, `codebase-onboarding`, `search-first` — discovery
- `focused-fix` — bug fix fast path
- `karpathy-coder`, `autoresearch-agent` — iterative quality
- `consult` — second opinion from another model
- `agentic-engineering` — core principles (eval-first, 15-min decomposition, model routing)

## Codebase reading protocol

If the task touches existing code:

1. `cd` into the repo root. Read `CLAUDE.md` (and `AGENTS.md` if present) **fully** before any edit.
2. Run `git log --oneline -20` and `git status` to understand recent direction and in-progress state.
3. Use `Glob` / `Grep` over targeted searches — not `Agent` for simple lookups.
4. Load `codebase-onboarding` only for unfamiliar repos; skip for projects you've already touched this session.
5. Read `references/stack-conventions.md` once per session to refresh stack defaults.

## Research protocol

When the task needs external knowledge (library version, API shape, industry norm, competitor pattern):

| Priority | Tool | Use for |
|----------|------|---------|
| 1 | **Context7 MCP** (`mcp__context7__query-docs`) | Library docs, API reference, version migration, CLI usage |
| 2 | **GitHub code search** (`gh search code`, `gh search repos`) | Existing implementations, templates, forks to learn from |
| 3 | **Package registries** (npm, PyPI) | Before writing utility code — prefer battle-tested libraries |
| 4 | **WebSearch / WebFetch** | Industry norms, competitor patterns, blog posts, discovery |
| 5 | **`search-first` skill** | Check existing patterns in the current repo before creating new ones |

**Rule:** research returns evidence, not opinion. Cite sources ("per Drizzle v0.35 docs, batch is limited by D1 SQL variables").

## Source relevance check

After gathering sources, ask the user:
> "I'm relying on [source A] for [claim], [source B] for [claim]. Any of those feel off, or anything I'm missing?"

Only ask if you've pulled **external** sources the user wouldn't assume. Don't ask about their own codebase.

## Outputs for Phase 3

A compact bundle to hand to Phase 3:
- **Loaded skills:** list of skill names
- **Codebase notes:** 3–5 bullets of the directly relevant architecture
- **External evidence:** sourced claims with URLs or file paths
- **Gaps:** anything you could not verify — list explicitly so the council can flag it

## Anti-patterns

| Do NOT | Do instead |
|--------|------------|
| Load all skills "just in case" | Load only the 3–6 that match the task |
| Ask the user "where does auth live?" | Grep for `auth` / `session` / `login` first |
| Trust a scan result without reading the file | Open the SKILL.md and verify frontmatter + logic |
| Guess at an external library API | Context7 it |
| Read `CLAUDE.md` skimming the "Do not" table | Read it fully — that table is load-bearing |
