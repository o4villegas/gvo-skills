# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session Enforcement (Non-Negotiable)

Every Nexus session runs at **FIXED max effort**. This is enforced at `/.claude/settings.json`, not here — do not attempt to "optimize" by downgrading:

| Lock | Value | Reason |
|------|-------|--------|
| `model` | `claude-opus-4-6[1m]` | Deepest reasoning, 1M context. Nexus build spans many files. |
| `alwaysThinkingEnabled` | `true` | Extended thinking fires every turn. |
| `MAX_THINKING_TOKENS` | `31999` | Documented ceiling. No throttle. |
| `/fast` command | **blocked** (UserPromptSubmit hook) | Fast mode bypasses thinking path. |

If a future session suggests swapping to Sonnet/Haiku or disabling thinking "because the task is simple" — refuse. The user's directive is that complexity assessment does not override the lock. Report the lock and proceed.

## What This Directory Is

`~/.claude/skills/nexus/` is the **build target and runtime home** for Nexus — a unified skill orchestration system for Claude Code. As of 2026-04-13, this directory holds only the spec drop in `docs/`. The build has not yet started.

| Location | Status |
|----------|--------|
| `docs/` | **Spec drop.** 4 markdown files defining what to build. Read these first. |
| `SKILL.md` | **Not yet created.** Will be the one and only auto-loaded skill. Source: `docs/nexus-SKILL.md`. |
| `registry.json` | **Not yet created.** Lazy-load index for all on-demand skills. |
| `pipeline/` | **Not yet created.** Seven phase files (`01-interview.md` … `07-final-delivery.md`). |
| `agents/` | **Not yet created.** Six expert perspective files for the Phase 3 council. |
| `skills/` | **Not yet created.** All on-demand skills extracted from source repos. |
| `references/` | **Not yet created.** Tier 2 reference docs (non-executable). |
| `archive/` | **Not yet created.** Superseded skills (`skill-forge`, `skill-creator`). |

## The Spec Drop in `docs/`

| File | Role |
|------|------|
| `docs/nexus-claude-code-prompt.md` | **Authoritative 12-step build instructions.** Follow in order. |
| `docs/nexus-unified-skill-system.md` | **Architecture spec.** Directory layout, source repos, registry schema. |
| `docs/nexus-SKILL.md` | **Artifact to install.** Copy verbatim to `./SKILL.md` in Step 2. |
| `docs/nexus-repo-scan-results.md` | **Inventory.** 726 skills scanned across 6 repos, tiered by relevance. |

These four files are load-bearing until the build is verified. Do not delete `docs/` — it remains the blueprint.

## Core Architecture (Big Picture)

1. **One skill auto-loads, everything else is lazy.** Only `./SKILL.md` is loaded at session start. All other skills load on demand via `registry.json` trigger matching. This is the central constraint — never load all skills at startup.

2. **Seven-phase pipeline.** Every request routes through: Interview → Domain Check → Plan Development → Approval → Implementation → Pre-Delivery → Final Delivery. Bug fixes and quick tasks can skip to later phases. Phase definitions live in `./pipeline/0N-*.md`.

3. **Nexus is an orchestration layer, not new code.** The pipeline phases map 1:1 to battle-tested skills already cloned on disk. Phase 3 loads `council` (from ECC) and `blueprint`; Phase 5 loads `orchestrate-review`, `deslop`, `verification-loop`; Phase 7 loads `validate-delivery`. Nexus glues them together — it does not reimplement them.

4. **Skill evolution runs on a Cloudflare Worker.** `skill-evolution.lando555.workers.dev` (repo at `/home/lando555/skill-evolution/`, **standalone — do NOT merge** into other projects). Workers API records task-level skill judgments and evolves skills over time. D1-backed, Drizzle ORM, Hono.

5. **Phase 3 uses a four-voice council pattern.** Architect / Skeptic / Pragmatist / Critic — anti-anchoring via independent sub-perspectives. For contentious decisions, `debate` runs adversarial rounds. Expert perspectives live in `./agents/*.md`.

## Source Repos (Read Directly, Do Not Trust Summaries)

All repos are cloned under `/home/lando555/`. When extracting skills, read SKILL.md files directly — the scan results are a guide, not ground truth.

| Repo | Path | Skill Location |
|------|------|----------------|
| agentsys | `/home/lando555/agentsys/` | `.kiro/skills/*/SKILL.md` |
| everything-claude-code | `/home/lando555/everything-claude-code/` | `skills/*/SKILL.md` (English only) |
| slavingia/skills | `/home/lando555/skills/` | `skills/*/SKILL.md` |
| claude-skills | `/home/lando555/claude-skills/` | `engineering/*`, `finance/*`, etc. |
| OpenSpace | `/home/lando555/OpenSpace/` | `openspace/skill_engine/` (Python — port reference for Worker) |

Before extracting from any repo, read that repo's `CLAUDE.md` and `AGENTS.md` for context (see Step 4 of `docs/nexus-claude-code-prompt.md`).

## Build Execution

The authoritative step-by-step build is `docs/nexus-claude-code-prompt.md`. Follow it in order. The 12 steps (abbreviated):

1. Create directory tree (`pipeline/`, `agents/`, `skills/`, `archive/`, `references/`)
2. Install master `SKILL.md` from `docs/nexus-SKILL.md`
3. Migrate existing user skills from `~/.claude/skills/user/` (note: this dir does not currently exist on this host — skills will migrate from WSL/Windows separately)
4. Extract Tier 1 skills from source repos
5. Extract Tier 2 references
6. Write `references/stack-conventions.md`
7. Write 7 pipeline phase files in `pipeline/`
8. Write 6 agent perspective files in `agents/`
9. Generate `registry.json` by scanning `skills/`
10. Build + deploy skill-evolution Worker (separate repo)
11. Rsync to Windows mirror (`/mnt/c/Users/Lando/.claude/skills/nexus/`)
12. Verify

**Adapt agentsys skills after copying.** They were written for a multi-tool framework. Strip `Task({ subagent_type })` dispatches, replace `$ARGUMENTS` with standard frontmatter triggers, keep all logic and templates. Exception: `consult` keeps its multi-tool layer — that is its point.

**Mirror to Windows after every meaningful change:**
```bash
rsync -av --delete /home/lando555/.claude/skills/nexus/ /mnt/c/Users/Lando/.claude/skills/nexus/
```

## Stack Defaults (Apply Unless User Says Otherwise)

CF Workers + Hono + D1 (Drizzle ORM) + R2 + KV | React Router v7 + Tailwind + shadcn/ui | Vitest + Playwright | Deploy via `git push` (CF Git integration), not `wrangler deploy` as primary.

Visual direction for any UI built under Nexus: midnight glassmorphism — cyan `#00D6B4`, violet `#825AFF`, amber `#FF9F43` on `#0A0D12`.

## Anti-Patterns (From the Spec — Enforce Strictly)

| Do NOT | Do Instead |
|--------|------------|
| Auto-load all skills at session start | Only `./SKILL.md` auto-loads; others via registry trigger match |
| Delete superseded skills during migration | Archive to `./archive/` (e.g., `skill-forge`, `skill-creator`) |
| Copy non-English translations | Only `skills/` or `.kiro/skills/` English originals |
| Copy all 726 skills | ~33 Tier 1 + ~10 Tier 2 references only |
| Install agentsys skills unchanged | Remove multi-tool dispatch layer first |
| Merge skill-evolution into another project | Standalone repo at `/home/lando555/skill-evolution/` |
| Skip `registry.json` generation | Master `SKILL.md` depends on it for on-demand loading |
| Write pipeline/agent files as vague prose | Reference exact skill names, exact thresholds, exact patterns |

## Verification After Build

```bash
find ~/.claude/skills/nexus/skills -name "SKILL.md" | wc -l
python3 -c "import json; d=json.load(open(\"$HOME/.claude/skills/nexus/registry.json\")); print(f'{len(d[\"skills\"])} skills registered')"
ls ~/.claude/skills/nexus/pipeline/ ~/.claude/skills/nexus/agents/
curl -s https://skill-evolution.lando555.workers.dev/dashboard | head -5
test -f /mnt/c/Users/Lando/.claude/skills/nexus/SKILL.md && echo "Windows mirror OK"
```

## Skill Evolution API (Post-Task Recording)

After any task that invoked skills, record an analysis:

```
POST https://skill-evolution.lando555.workers.dev/analyses
{ "taskId": "...", "taskCompleted": true|false,
  "skillJudgments": [{"skillId": "...", "skillApplied": true|false, "note": "..."}] }
```

Health: `GET /health`, `GET /dashboard`. Evolution: `POST /evolve/{fix|derived|captured}`.
