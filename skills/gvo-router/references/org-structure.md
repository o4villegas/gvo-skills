# Org Structure — Roles, Reporting, Spawn Templates

This file defines the three-tier organization plus the parallel-chain Auditor.
Director (this skill) reads it before spawning any agent.

## Reporting Chain

```
                 ┌──────────────┐
                 │   Director   │  ← this skill (you, in claude.ai)
                 └──────┬───────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
  ┌─────────┐     ┌──────────┐     ┌──────────┐
  │Lead-Plan│     │Lead-Build│     │Lead-Test │   ← all opus
  └────┬────┘     └────┬─────┘     └────┬─────┘
       │               │                │
   Workers         Workers          Workers          ← all opus
   (Plan-1..N)    (Build-1..N)     (Test-1..N)

       Parallel chain (no Lead in between):

  ┌──────────────┐
  │   Auditor    │  ← opus, reports straight to Director
  └──────┬───────┘
         │
    Audit-Workers (opus)
```

**Why the parallel chain matters**: if the Auditor reported through a Lead, the Lead
could rewrite the audit before passing it up. The parallel chain prevents that — the
Director sees raw Auditor output, not a Lead-summarized version.

## Role Definitions

### Director (this skill)

- Classifies request, decides 2-tier vs 3-tier, picks Leads to spawn
- Constructs each spawn prompt from the §3.1 template — never free-text
- Receives Lead deliverables + Auditor matrix
- Cross-checks Lead claims against Auditor PASS/FAIL/UNVERIFIED
- Composes final user-facing delivery
- **Does not write code, plan features, run tests, or read files beyond the §2
  prerequisites**. The Director routes; Leads execute.

### Lead-Plan

- Receives: classified request + matched skill SKILL.md content + project context
- Produces: a plan deliverable (architecture, file structure, implementation sequence,
  test plan, top risks)
- May spawn 1-3 Plan-Workers for parallel exploration of design alternatives
- Uses council pattern (4 voices: Architect, Skeptic, Pragmatist, Critic) for
  contentious decisions — see `skills/nexus/skills/council/SKILL.md`
- Returns: `plan.md` (in-conversation, not file system) with sections:
  - Architecture overview (3-5 sentences)
  - File structure (tree)
  - Implementation sequence (numbered, with file ownership per step)
  - Test plan (for Lead-Test)
  - Top 3 risks + mitigations
  - Confidence % + what would raise it
  - Evidence: every architectural claim cites a read of an existing file/skill

### Lead-Build

- Receives: Lead-Plan's plan.md + project context
- Spawns Build-Workers, one per file-ownership unit defined in the plan
- Coordinates merge points (interface contracts) per agent-teams pattern
- Verifies build with at least one mechanical command (e.g., `tsc --noEmit`,
  `cargo check`, `pytest --collect-only`)
- Returns: build summary + the verification commands run + their literal output
- **Writes are allowed here** but must respect the project's CLAUDE.md (deploy method,
  package manager, etc.)

### Lead-Test

- Receives: Lead-Plan's test plan + Lead-Build's deliverable
- Spawns Test-Workers per test surface (unit, integration, e2e)
- Runs verification commands (e.g., `npm test`, `npm run check`)
- Returns: pass/fail per surface + the literal command output for each
- Coverage target: 70% per the user's CLAUDE.md (lowered from 80% common default)

### Auditor

- Receives: all Lead deliverables (read-only access to their full output)
- Independently re-runs every verification command claimed in the deliverables
- Never trusts a Lead's transcript — always re-runs
- Produces a matrix:
  ```
  | Claim                          | Lead    | Re-run command           | Output match | Verdict |
  |--------------------------------|---------|--------------------------|--------------|---------|
  | "tests pass"                   | Test    | npm test                 | yes          | PASS    |
  | "build succeeds"               | Build   | npm run build            | partial      | FAIL    |
  | "no security issues"           | Build   | (no command run by Lead) | n/a          | UNVERIFIED |
  ```
- Independence rule: Auditor must spawn its own Audit-Workers, never reuse a Worker
  spawned by a Lead.
- Reports straight to Director — never to a Lead.

### Workers (under any Lead)

- Receive: one specific task within the Lead's domain
- Have file ownership boundaries — never write files outside their assigned scope
- Return: deliverable + evidence section (commands run + output) + confidence %
- May not spawn sub-agents (depth cap at Workers — no further nesting)

## Tier-2 vs Tier-3 Decision Rules

Use 2-tier (Director → Workers, no Leads) when:
- Task affects ≤2 files
- Single domain (only Plan, only Build, or only Test)
- No coordination needed across domains

Use 3-tier (Director → Leads → Workers + Auditor) when:
- Task affects 3+ files OR spans multiple domains
- Plan must precede Build (most non-trivial work)
- Auditor independence matters (any time a "complete" claim will be made)

Default: 3-tier. The overhead of one extra agent layer is small compared to the cost
of unverified claims.

## Spawn Order (Critical)

Always spawn in this sequence within a single message when possible:

1. **Lead-Plan first, alone** — its output feeds Lead-Build
2. **After Plan completes**: Lead-Build + Lead-Test in parallel (they're independent at
   spawn time; Lead-Test will wait on Lead-Build to finish before running tests, but its
   prompt can be constructed now)
3. **Auditor**: spawn after each Lead reports complete, NOT in parallel with the Lead.
   Auditor must wait for the Lead's full deliverable so it has something to audit.

Do not spawn all Leads simultaneously when Lead-Build depends on Lead-Plan's plan.md —
the dependency is real and parallel spawn would mean Lead-Build operates without a plan.

## File Ownership (for Build-Workers)

Lead-Build assigns ownership using one of three strategies (mirrors agent-teams):

| Strategy | When | Example |
|----------|------|---------|
| By directory | Module-shaped repos | Worker-1 owns `src/api/`, Worker-2 owns `src/ui/` |
| By module | Logical splits that cross dirs | Worker-1 owns "auth flow" wherever it lives |
| By layer | Monoliths with clear layers | Worker-1 owns DB, Worker-2 owns API, Worker-3 owns UI |

**Cardinal rule**: one owner per file. Two Workers must never write the same file
within one Lead-Build pass. If they need to, the Lead serializes them.

## Spawn Template (Reference Copy)

```
Agent({
  description: "<3-5 word task summary>",
  subagent_type: "general-purpose",
  model: "opus",
  prompt: `You are <Role> in the gvo-router organization.

Your role: <Lead-Plan | Lead-Build | Lead-Test | Worker-X | Auditor>
You report to: <Director | Lead-Y>

Context (read-only — do not re-fetch):
<embed file paths + line counts the Director already gathered>

Your task: <one specific deliverable>

Deliverable format:
- Plain English summary (max 4 lines)
- Evidence section: every claim must be backed by a literal command + its output
  inside a fenced code block. No claim may stand alone in prose.
- Confidence %: state your confidence the deliverable is correct, with one sentence
  explaining what would raise it.

Hard constraints:
- model: opus only — if you spawn sub-agents, also pin opus.
- Never modify production data without an explicit write authorization in your prompt.
- Never claim "verified" / "complete" / "passed" without command output evidence.
- If blocked, return BLOCKED with one sentence on why and what you need.

Do NOT pause to ask the user. If a decision is needed, log an assumption to your
deliverable's Assumption Ledger section with confidence: high|medium|low and continue.
`
})
```

The Director constructs this prompt fresh for each spawn. Variables to fill in: role,
reports-to, context block, task, role-specific deliverable shape (the body sections vary
between Plan, Build, Test, Audit — Lead-Plan returns plan.md sections, Lead-Build returns
build summary, etc.).

## Audit Trail

The Director maintains an in-conversation audit trail of every spawn:

```
[T+0:00:05] Spawned Lead-Plan (opus) — task: "Plan auth refactor"
[T+0:01:32] Lead-Plan returned plan.md (8 sections, confidence 87%)
[T+0:01:35] Spawned Auditor (opus) — task: "Audit plan.md"
[T+0:02:10] Auditor returned matrix (3 PASS, 0 FAIL, 1 UNVERIFIED)
[T+0:02:12] Spawned Lead-Build (opus) + Lead-Test (opus) parallel
...
```

This trail goes into the final delivery's Assumption Ledger if the user asks "show me
how this got decided." It is not surfaced by default — adds noise.
