---
name: nexus
description: >
  Unified skill orchestrator. Routes ALL coding, building, and automation requests through a
  structured pipeline. Loads skills on demand from the nexus registry — never loads all skills
  at startup. Trigger on ANY coding request, project build, feature request, automation task,
  skill management, or: "nexus", "build me", "create", "implement", "let's build", "new project",
  "new feature", "fix this", "improve this", "what skills do I have", "skill health", "register
  skill", "evolve skill", "plan this", "design this", "review this". Entry point for everything.
---

# Nexus — Unified Skill Orchestrator

One skill to rule them all. You classify the request, load only the skills needed, and route
through the appropriate pipeline phases.

---

## 1. Classify & Route

| Classification | Start Phase | Skills to Load |
|---------------|-------------|----------------|
| **New build** (app, feature, project) | Phase 1 | Per-phase (see §3) |
| **Enhancement** (improve existing) | Phase 1 (brief) → 3 | Per-phase |
| **Bug fix** | Phase 5 | focused-fix, verification-loop |
| **Quick task** (lookup, generate, simple) | Direct | None or domain-specific |
| **KC Clearwater task** | Domain routing | from-kc-records, kc-pulse, financial-data-translator |
| **Skill management** | Direct | skill-evolution Worker API |
| **Prompt optimization** | Direct | from-prompter, autoresearch-agent |
| **Chaos testing** | Direct | from-billy |
| **UX audit** | Direct | ux-diagnostic |
| **Research / analysis** | Phases 1-2 | repo-intel, search-first |
| **Business strategy** | Direct | validate-idea, mvp, pricing, from-aristotle |

---

## 2. Load Skills On Demand

Read `~/.claude/skills/nexus/registry.json` to find available skills. Match user request
against `triggers` array. Load ONLY matched skills by reading their SKILL.md.

**Never load all skills at startup. This SKILL.md is the only auto-loaded file.**

### Core Skill Paths (known — use without registry lookup)

| Skill | Relative Path | Trigger Patterns |
|-------|--------------|-----------------|
| from-desktop | skills/from-desktop/SKILL.md | codebase access, read source, VPS |
| from-prompter | skills/from-prompter/SKILL.md | optimize prompt, improve prompt |
| from-billy | skills/from-billy/SKILL.md | chaos test, stress test, break it |
| from-kc-records | skills/from-kc-records/SKILL.md | KC data, invoices, Toast, expenses |
| kc-pulse | skills/kc-pulse/SKILL.md | financial review, P&L, monthly review |
| ux-diagnostic | skills/ux-diagnostic/SKILL.md | UX audit, design review, polish |
| council | skills/council/SKILL.md | tradeoff, decision, multiple perspectives |
| blueprint | skills/blueprint/SKILL.md | plan, roadmap, multi-session project |
| debate | skills/debate/SKILL.md | argue, stress test idea, devil's advocate |
| orchestrate-review | skills/orchestrate-review/SKILL.md | code review, multi-pass review |
| validate-delivery | skills/validate-delivery/SKILL.md | validate, check readiness, ship check |
| deslop | skills/deslop/SKILL.md | clean code, remove slop, repo hygiene |
| verification-loop | skills/verification-loop/SKILL.md | verify, quality check, pre-PR |
| focused-fix | skills/focused-fix/SKILL.md | fix bug, targeted fix |

---

## 3. The Pipeline

### Phase 1: Interview

**Goal:** 95%+ accurate task spec from 4-8 plain-language questions.

Rules:
- Max 3 questions per turn. Yes/no, this-or-that, pick-from-three.
- Translate technical decisions into user outcomes.
- Exit when you can describe the project in 2-3 sentences and the user would say "exactly."

Categories: What → Who → Where → Scale → Constraints → Existing work.

### Phase 2: Domain Check

**Goal:** Gather domain knowledge, load relevant skills.

1. Identify domains the task touches
2. Load matching skills from registry
3. If building on existing code → load `from-desktop`, read codebase via MCP
4. Load `repo-intel` for git history / codebase intelligence
5. Load `search-first` to check existing patterns before creating new ones
6. Web search for industry norms, competitor patterns, best practices
7. If sources seem off, ask user: "Is [X] relevant?"

### Phase 3: Plan Development (No User Intervention)

**Goal:** Multi-perspective expert planning producing a world-class implementation plan.

Load `council` skill and run the four-voice pattern:

| Voice | Lens |
|-------|------|
| Architect | Correctness, maintainability, long-term implications, system design |
| Skeptic | Challenge framing, question assumptions, propose simplest alternative |
| Pragmatist | Shipping speed, user impact, operational reality |
| Critic | Edge cases, downside risk, failure modes |

For complex multi-session projects, also load `blueprint` to generate step-by-step plans
with cold-start context briefs per step.

For contentious technical decisions, load `debate` for structured adversarial rounds.

Load `agentic-engineering` principles: eval-first, 15-minute task decomposition, model routing.

**Output:** Architecture overview, file structure, implementation sequence, test plan, top risks.

### Phase 4: Approval

Present clean summary to user:
- 2-3 sentence description
- Key features list
- Stack + architecture
- Top risks + mitigations
- "Proceed? (yes / no / change something)"

Rejected → return to Phase 3 with feedback. Do NOT restart from Phase 1.

### Phase 5: Implementation (No User Intervention)

**Goal:** Build, test, debug, harden.

Load: `orchestrate-review`, `deslop`, `verification-loop`, `continuous-agent-loop`

Sequence:
1. **Scaffold** — project structure, deps, configs
2. **Core** — data model → API → UI
3. **Polish** — error handling, loading states, edge cases
4. **Deslop** — run `deslop` to clean AI artifacts (debug stmts, placeholders, dead code)
5. **Test** — run `verification-loop` (build → types → lint → tests → security)
6. **Review** — run `orchestrate-review` (parallel: code quality, security, performance, test coverage)
7. **Harden** — address review findings, re-run verification
8. **Iterate** — repeat 5-7 until clean or stall detected

No TODOs, no placeholders, no commented-out code. Production quality throughout.

### Phase 6: Pre-Delivery

1. Present working implementation to user (demo, artifact, or screenshot)
2. Ask: "Does this match what you expected?"
3. Present enhancement options
4. If UI exists → load `ux-diagnostic` and run audit
5. Execute requested refactors
6. Final `verification-loop` pass

### Phase 7: Final Delivery

Load `validate-delivery` and run autonomous validation:
- Tests pass, build passes, requirements met, no regressions

Checklist: features working, tests passing, no console errors, error handling complete,
responsive (if UI), accessible, performance acceptable, deployed (if applicable), docs updated.

Delivery format:
- Claude Code: committed + pushed + deployed
- Claude.ai: files in /mnt/user-data/outputs/

---

## 4. Skill Evolution

After tasks involving skills, record analysis:

```
POST https://skill-evolution.lando555.workers.dev/analyses
{ "taskId": "...", "taskCompleted": true/false,
  "skillJudgments": [{"skillId": "...", "skillApplied": true/false, "note": "..."}] }
```

Periodic health: `GET /health`, `GET /dashboard`
Evolution: `POST /evolve/fix`, `/evolve/derived`, `/evolve/captured`

---

## 5. Stack Defaults

Unless user specifies otherwise: CF Workers + Hono + D1 (Drizzle) + R2 + KV |
React Router v7 + Tailwind + shadcn/ui | Vitest + Playwright | `wrangler deploy`

## 6. Prompt Rules (Always Apply)

1. Mechanical verification (grep, not trust)
2. One skill = one domain
3. Prerequisites before execution
4. Anti-patterns name alternatives
5. Code examples show failure path
6. Tables beat prose for structured data
7. Threshold everything (no vague "often")
8. Chain verify commands with `&&`
