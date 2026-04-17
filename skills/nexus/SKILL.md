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

## 0. Execution Mode

Parse `--mode` flag from arguments. Two modes:

| Mode | Flag | Behavior |
|------|------|----------|
| **assist** (default) | `--mode=assist` or no flag | Interactive — user approves at Phase 4, reviews at Phase 6 |
| **auto** | `--mode=auto` | Autonomous — zero human intervention, self-assessed quality gates |

### Auto Mode Rules

When `--mode=auto`:
1. **Skip Phase 1 (Interview)** if task description is sufficient (>20 words with clear intent)
2. **Skip Phase 4 (Approval)** — auto-proceed if council produces no CRITICAL risks
3. **Phase 5 uses conductor** for state persistence — write progress to `conductor/tracks/{id}/metadata.json`
4. **Self-assessed quality gates**: build passes + tests pass + no CRITICAL review findings = continue
5. **Bounded retries**: max 3 attempts per task, max 2 full verify→fix cycles. Escalate to user on 4th failure.
6. **Phase 6 (Pre-Delivery)** becomes a verification-loop pass instead of user demo
7. **Parallel execution**: use `agent-teams` for independent work streams when >3 files affected
8. **Commit on completion**: auto-commit with conventional commit messages per task

Trigger words for auto: "auto", "autonomous", "just do it", "ship it", "no questions", "dangerousbypass"

### Auto Mode State File

On auto-mode activation, create/update `.nexus-state.json` in project root:

```json
{
  "mode": "auto",
  "task": "description from user",
  "started": "ISO_TIMESTAMP",
  "phase": 3,
  "retries": { "current_task": 0, "total_cycles": 0 },
  "quality_gates": { "build": null, "tests": null, "review": null },
  "escalated": false
}
```

**Read this file at session start** to detect in-progress auto runs.
**Delete this file** when task completes or mode switches to assist.
**Set `escalated: true`** when retry limit hit — next session starts in assist mode for that task.

### Assumption Ledger (Critical — Auto Mode)

In auto mode, **NEVER ask the user a question**. Instead:

1. **Log the question** you would have asked to `conductor/tracks/{id}/assumptions.jsonl`
2. **Record your assumption** with confidence level, alternatives, and evidence
3. **Track the blast radius** (files and lines affected)
4. **Tag the commit** that implements the assumption
5. **Continue working**

At delivery (Phase 6), present the full ledger grouped by confidence level.
The user can reverse any assumption by ID: `"reverse A3"`.

**Pause rule**: If 3+ consecutive assumptions are `confidence: low`, STOP auto mode 
and switch to assist. Too many uncertain decisions compound error risk.

See `references/assumption-ledger.md` for full format, field definitions, reversal 
protocol, and anti-patterns.

### Auto Mode Decision Tree

```
Task arrives with --mode=auto
  │
  ├── Description >20 words? → Skip Phase 1
  ├── Description ≤20 words? → Run Phase 1 (brief: 2 questions max)
  │
  ├── Plan has CRITICAL risk? → STOP, switch to assist, ask user
  ├── Plan is clean? → Skip Phase 4, begin Phase 5
  │
  ├── Ambiguity encountered? → Log to assumption ledger (DO NOT ask user)
  │     ├── confidence: high → log and continue
  │     ├── confidence: medium → log and continue  
  │     └── confidence: low (3+ consecutive) → STOP, switch to assist
  │
  ├── Task fails? → retry (n/3)
  │     ├── n < 3 → fix and retry
  │     └── n = 3 → set escalated=true, STOP, report to user
  │
  ├── All tasks done? → verification-loop (automated)
  │     ├── Pass → deslop → commit → complete
  │     └── Fail → fix cycle (m/2)
  │           ├── m < 2 → fix and re-verify
  │           └── m = 2 → escalate to user
  │
  ├── Phase 6: Present assumption ledger to user
  │     ├── "approve all" → accept, complete
  │     ├── "reverse A{N}" → revert commit, apply alternative, re-verify
  │     └── "reverse all medium" → batch reversal
  │
  └── Complete → delete .nexus-state.json, report summary
```

---

## 1. Classify & Route

| Classification | Start Phase | Skills to Load |
|---------------|-------------|----------------|
| **New build** (app, feature, project) | Phase 1 | Per-phase (see §3) |
| **Enhancement** (improve existing) | Phase 1 (brief) → 3 | Per-phase |
| **Bug fix** | Phase 5 | focused-fix, verification-loop |
| **Quick task** (lookup, generate, simple) | Direct | None or domain-specific |
| **Full-stack feature** | Phase 1 | full-stack-orchestration |
| **KC Clearwater task** | Domain routing | from-kc-records |
| **Skill management** | Direct | skill-evolution Worker API |
| **Prompt optimization** | Direct | from-prompter, autoresearch-agent |
| **Chaos testing** | Direct | from-billy |
| **Research / analysis** | Phases 1-2 | repo-intel, search-first |
| **Business strategy** | Direct | validate-idea, mvp, pricing |

---

## 2. Load Skills On Demand

Read `~/.claude/skills/nexus/registry.json` to find available skills. Match user request
against `triggers` array. Load ONLY matched skills by reading their SKILL.md.

**Never load all skills at startup. This SKILL.md is the only auto-loaded file.**

### Core Skill Paths (known — use without registry lookup)

| Skill | Relative Path | Trigger Patterns |
|-------|--------------|-----------------|
| from-prompter | skills/from-prompter/SKILL.md | optimize prompt, improve prompt |
| from-billy | skills/from-billy/SKILL.md | chaos test, stress test, break it |
| from-kc-records | skills/from-kc-records/SKILL.md | KC data, invoices, Toast, expenses |
| council | skills/council/SKILL.md | tradeoff, decision, multiple perspectives |
| blueprint | skills/blueprint/SKILL.md | plan, roadmap, multi-session project |
| debate | skills/debate/SKILL.md | argue, stress test idea, devil's advocate |
| orchestrate-review | skills/orchestrate-review/SKILL.md | code review, multi-pass review |
| validate-delivery | skills/validate-delivery/SKILL.md | validate, check readiness, ship check |
| deslop | skills/deslop/SKILL.md | clean code, remove slop, repo hygiene |
| verification-loop | skills/verification-loop/SKILL.md | verify, quality check, pre-PR |
| focused-fix | skills/focused-fix/SKILL.md | fix bug, targeted fix |
| conductor | ../conductor/SKILL.md | project setup, track management, auto mode state |
| agent-teams | ../agent-teams/SKILL.md | parallel agents, team spawn, multi-agent |
| full-stack-orchestration | ../full-stack-orchestration/SKILL.md | full-stack feature, end-to-end build |

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
3. If building on existing code → load `codebase-onboarding` to map architecture
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
4. Execute requested refactors
5. Final `verification-loop` pass

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
