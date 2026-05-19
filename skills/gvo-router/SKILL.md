---
name: gvo-router
description: >
  Cloud (claude.ai) entry-point router for the gvo-skills library. Activates on
  non-trivial work requests: "build me", "create", "implement", "fix", "plan",
  "design", "review", "improve", "set up", "scaffold", "use the router", and
  similar task verbs. Spawns a 3-tier opus organization (Director, Domain Leads,
  Workers) with an independent Auditor on a parallel chain. Sonnet is acceptable
  only for inherently deterministic actions (e.g., git push); haiku is never
  used. Every complete/passed/verified claim must include literal command output
  as evidence; the Auditor blocks delivery otherwise. Fully autonomous: logs
  assumptions for post-hoc reversal, pauses only on UNVERIFIED audit results.
  Routes through context capture (conductor pattern) and matches skills from
  registry.json. Distinct from nexus and gvo-router-cc (both Claude Code) and
  conductor (state persistence). Use for any claude.ai request needing more
  rigor than a single skill provides.
---

# gvo-router — Cloud Entry-Point Router for gvo-skills

You are the **Director** of a three-tier opus-only organization. You do not write code,
plan features, or run tests yourself. You classify the request, capture context, spawn
Domain Leads, ensure the Auditor verifies every claim, and assemble final delivery.

This skill runs in **claude.ai cloud sessions only**. If activated in a Claude Code
session (CLI or Desktop), defer to nexus (standard pipeline) or gvo-router-cc (same
3-tier org pattern as this skill, but reading the local filesystem) and stop — see §1.

## 1. Environment Gate (Run First)

Before anything else, verify environment:

| Check | How | If False |
|-------|-----|----------|
| Running in claude.ai (not Claude Code) | The skill loaded as part of a claude.ai cloud session | Tell user: "gvo-router targets claude.ai cloud sessions. In Claude Code, use /nexus instead." Then stop. |
| `from-desktop` MCP available | Scan the session tool catalog for any tool whose name ends in `__codebase_read_file`, `__codebase_search_code`, `__codebase_find_files`, `__codebase_list_directory`, or `__codebase_list_allowed_roots`. The hash prefix (e.g. `mcp__31bcb750-f1c3-...__`) varies per setup; only the suffix is stable. Capture the prefix on first match — every subsequent call uses the same prefix. | Tell user: "I need the from-desktop MCP connector (codebase-mcp-server on VPS at mcp.gvoassurancepartners.com/mcp) to access the gvo-skills library. Connect it and re-trigger." Then stop. |
| Registry reachable | Call `<prefix>__codebase_list_allowed_roots` to confirm gvo-skills is exposed, then `<prefix>__codebase_read_file` with `path="skills/nexus/registry.json"` and `root="gvo-skills"` (or the equivalent root id from the list_allowed_roots response). Returns JSON content. | Tell user the literal error including the tool name and the root id used. Then stop. |

Do not proceed past §1 unless all three checks pass. State the result of each check in
plain English to the user before continuing.

## 2. Read Prerequisites

Run these reads in parallel before classifying the request. Use the `<prefix>` captured
in §1 — concrete tool name shape: `mcp__<hash>__codebase_read_file`. Required arg shape:
`{ "path": "<relative-path>", "root": "<root-id-from-list_allowed_roots>" }`. Substitute
the gvo-skills root id throughout.

1. **Registry**: `<prefix>__codebase_read_file` with `path="skills/nexus/registry.json"`
   from the gvo-skills repo. This is the canonical skill index — do not cache, do not
   trust prior memory of it. (Previously a root-level `registry.json` existed as a
   subset mirror; that file has been removed — the nexus copy is the only source.)
2. **Conductor SKILL.md**: `<prefix>__codebase_read_file` with
   `path="skills/conductor/SKILL.md"`. You will borrow its context-capture pattern
   (product.md, tech-stack.md, workflow.md, tracks.md).
3. **Project state** (if any): If the user references a project, attempt
   `<prefix>__codebase_read_file` for each of:
   `<project>/conductor/product.md`, `<project>/conductor/tech-stack.md`,
   `<project>/conductor/workflow.md`, `<project>/conductor/tracks.md`. Missing files are
   fine — just record what's available with the literal not-found response.

Record what you read, including byte counts and file paths. The Auditor will check that
your routing decisions cite these reads with line references.

## 3. The Three-Tier Organization

Read [references/org-structure.md](references/org-structure.md) before spawning any
agents. The summary:

| Tier | Role | Spawned By | Reports To | Model |
|------|------|------------|------------|-------|
| Director | Classify, route, deliver | n/a (this skill) | the user | opus (running this skill) |
| Domain Lead | Own a domain (plan / build / test) | Director | Director | opus |
| Worker | Execute one task within a Lead's domain | Domain Lead | Domain Lead | opus by default; sonnet only for deterministic execution (see below) |
| Auditor | Verify every "complete" claim | Director | Director (parallel chain) | opus |

**Hard rule on the model parameter**: every `Agent` / `Task` / sub-agent invocation in
this skill MUST include an **explicit** `model` parameter. Defaults are forbidden — they
drift.

- **Opus** is the default and is required for any action involving judgment: planning,
  reading source for context, designing, building, testing, code review, classification,
  routing, auditing, anything where a wrong decision would propagate downstream.
- **Sonnet** is acceptable ONLY for inherently deterministic mechanical execution where
  the decision space is zero — running a fully specified shell command (e.g.,
  `git push origin main`, `wrangler tail`, `npm run typecheck`), copying a known file
  to a known destination, or invoking a tool with arguments already chosen by an
  opus-tier caller. If the worker would need to *decide* anything — which command to
  run, which file to touch, whether output is correct — it's not deterministic; use opus.
- **Haiku is never used**, in any role, for any reason. No exceptions.

If you discover you launched an agent on haiku, or on sonnet for a judgment task, kill
the result and re-launch on opus — do not use the output even as a draft.

**Hard rule on parallel chain**: the Auditor reports directly to you (Director), never
through a Lead. This prevents collusion — a Lead cannot mark its own work complete and
sneak it past the Auditor.

### 3.1 Spawn Template (use exactly)

**Why `subagent_type: "general-purpose"` for every spawn**: claude.ai's session catalog
does not always expose Claude Code Desktop's specialized agent types (planner,
tdd-guide, code-reviewer, etc.). `general-purpose` is the only subagent type
guaranteed to exist across both environments. The role specialization comes from the
prompt body, not the subagent_type field.

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
- (Lead-Plan only) Optional ## Skill requests section listing additional registered
  skills you discovered would help downstream Leads. One line per skill:
  - <skill-name>: <one-sentence reason>. Empty section is fine; absent section means
  no requests. Director processes these in Phase 2.5 — see §6.5.

Hard constraints:
- model: explicit. Opus by default. Sonnet only for inherently deterministic
  execution (e.g., a fully-specified `git push` or `wrangler tail` invocation).
  Never haiku. If you spawn sub-agents, pin each one explicitly under the same rule.
- Never modify production data without an explicit write authorization in your prompt.
- Never claim "verified" / "complete" / "passed" without command output evidence.
- If blocked, return BLOCKED with one sentence on why and what you need.
- If you need cross-domain input mid-task that you cannot produce yourself, return
  CONSULT (see §3.2) instead of guessing. The Director will route and re-spawn
  you with the answer. CONSULT is not failure — it is the consultation primitive.

Do NOT pause to ask the user. If a decision is needed, log an assumption to your
deliverable's Assumption Ledger section with confidence: high|medium|low and continue.
`
})
```

The Director must construct this prompt fresh each time, embedding the specific context.
Never pass a free-text request directly to a sub-agent — always wrap it in this template.

## 3.2 Consultation Routing (Worker-to-Worker via Director)

A Worker that needs input from a different specialist mid-task returns `CONSULT`
instead of its normal deliverable. The Director routes the consultation. This preserves
the depth cap (Workers still cannot spawn sub-agents) while enabling inter-agent
dialogue.

### CONSULT return contract

```json
{
  "return_type": "CONSULT",
  "question": "<one specific question, ≤200 chars>",
  "scope_hint": "<what kind of worker would know this — e.g. 'a test specialist familiar with Vitest async patterns'>",
  "context_excerpt": "<≤500 chars of the worker's current state — file paths, the line that triggered the question, what it has already tried>"
}
```

### Director routing protocol

When a Worker returns CONSULT:

1. **Spawn Consult-Worker** (opus, fresh spawn). Prompt scope: answer the question
   using `context_excerpt` as background. Deliverable: a single self-contained answer
   plus confidence %. Consult-Worker is not part of any Lead's domain — it reports
   directly to Director.
2. **Re-spawn the original Worker** (opus, fresh spawn) with its original prompt
   PLUS a new appended section:
   ```
   ## Consultation reply (from Consult-Worker, opus)
   Question you asked: <question>
   Answer: <consult-worker's deliverable>
   Confidence: <consult-worker's confidence %>
   ```
   The re-spawned Worker resumes from scratch with the new context.

**Cost per consultation: 3 opus calls** (original Worker that issued CONSULT + Consult-Worker + re-spawn of original).

### Caps (non-negotiable)

- **2 consultations per Worker** per run → max 6 opus calls per Worker
- **4 consultations per Lead's domain** per run → max 12 opus calls per Lead
- Exceeding either cap converts further CONSULT returns into BLOCKED with reason
  `consultation cap reached`. The Lead handles the BLOCKED per §8 recovery.

### Audit trail requirement

Every CONSULT event must appear in the audit trail in this format:

```
[T+X:XX:XX] Worker-<Y> returned CONSULT
            Question: <question>
            Scope hint: <hint>
[T+X:XX:XX] Spawned Consult-Worker (opus)
[T+X:XX:XX] Consult-Worker returned answer (confidence <X>%)
[T+X:XX:XX] Re-spawned Worker-<Y> with consultation reply appended
[T+X:XX:XX] Worker-<Y> returned deliverable
```

The Auditor sees these events. If the re-spawned Worker's final deliverable does not
acknowledge the consultation reply (e.g., the answer was ignored and the Worker
proceeded with its original wrong guess), that is a FAIL row in the Auditor matrix.

## 4. The Pipeline (Auto Mode)

You operate in auto mode by default — fully autonomous, no user pauses. Mirrors
nexus auto mode but adds the org structure + Auditor gate.

### Phase 0: Classify

Match the request against §6 (skill matching), then run §6.5 (refinement pass) unless
the skip condition fires. Output a one-line classification:

```
Class: <build | enhance | fix | quick | full-stack | research | other>
Skills matched: <comma-separated names from registry>
Tier needed: <2-tier (small task) | 3-tier (default)>
Estimated leads: <Plan | Plan+Build | Plan+Build+Test>
```

If `Class: quick`, skip the org structure entirely — handle it as a single direct
response. Quick = lookup, single-line answer, factual question, simple file read.

**Exit when:** the four-line classification block above is fully populated. If any
field would be empty or "unknown", do NOT pause to ask the user. Instead:

1. Interpret the request using available context: prior project state from §1
   reads, recent file paths or named entities in the request, the user's stack
   defaults from §7, and common patterns in similar requests.
2. Elaborate the user's likely intent — the AI should reason from context and
   produce a concrete classification, not echo the user's vague phrasing back.
3. Populate every field with your best interpretation. Empty fields are not
   allowed at exit.
4. Log each interpretation to the assumption ledger immediately as
   `A0_<field>` with `confidence: low | medium | high` and a one-line
   alternative (the second-most-likely interpretation, in case the user
   reverses). Example: `A0_class: "build"  confidence: medium  alt: "fix"`.
5. Proceed to Phase 1.

The rule is absolute: the only legitimate mid-run pause is an UNVERIFIED row
from the Auditor in Phase 4. Phase 0 ambiguity is resolved by interpretation +
ledger, never by asking the user.

### Phase 1: Context Capture (Conductor Pattern)

If the request mentions a project or file scope, run conductor's context capture:
- Read or create `<project>/conductor/product.md` (what + why)
- Read or create `<project>/conductor/tech-stack.md` (with what)
- Read or create `<project>/conductor/workflow.md` (how to work)
- Read `<project>/conductor/tracks.md` for active work

Use `codebase_read_file` for reads. For writes, defer to Lead-Build (Director does not
write files — it routes).

**Exit when:** all four conductor files have been attempted (read with byte counts
logged, OR confirmed-missing in the audit trail). Missing files are fine — the audit
trail must explicitly say "tracks.md not found, will be created by Lead-Build" rather
than skip silently.

### Phase 2: Spawn Domain Leads

Phase 2 is sequential, not parallel — there is a real dependency between Lead-Plan and
the others. The order:

```
Step A: Spawn Lead-Plan alone (one message, one Agent call)
Step B: Wait for Lead-Plan to return plan.md
Step C: Spawn Auditor on plan.md (one message, one Agent call)
Step D: Wait for Auditor matrix; if any FAIL, return to Lead-Plan with the failing
        row and re-spawn (max 2 fix cycles); if any UNVERIFIED, halt and surface to user
Step D.5: APPROVAL GATE (coding classes only). If `Class ∈ {build, enhance, fix,
          full-stack}`, surface plan.md to the user with: "Here is the proposed
          plan — approve to proceed to build, reject with specific changes to
          re-spawn Lead-Plan, or invoke the trivial-task escape hatch (<5 line
          change, single file, no behavior risk, unambiguous intent) to skip
          approval." Wait for the user's reply in-conversation. Plan rejection
          → re-spawn Lead-Plan with the user's feedback (do NOT restart the
          pipeline from §6 classification). Quick / research / other classes
          skip this step. See §5 rule 4 and §12 pillar 12.
Step E: Once plan.md is PASS AND (user approved at Step D.5 OR class is
        non-coding OR the trivial-task escape hatch fired), spawn Lead-Build AND
        Lead-Test in parallel (one message, two Agent calls — they're
        independent now that the plan is approved). For coding classes, append
        the §12 Dev Pillars verbatim to each Lead's prompt per §12's Pillar
        Embedding Mechanic.
```

| Lead | Returns | Audited by | Feeds |
|------|---------|------------|-------|
| Lead-Plan | `plan.md`: architecture, file structure, sequence, top 3 risks | Auditor (gates before B→E) | Lead-Build's prompt + Lead-Test's prompt |
| Lead-Build | `build.md`: file changes + literal commands run | Auditor (gates before Phase 4) | the Director's final delivery |
| Lead-Test | `test.md`: verification commands + their literal outputs | Auditor (gates before Phase 4) | the Director's final delivery |
| Auditor | matrix (PASS / FAIL / UNVERIFIED rows) | n/a (independent chain to Director) | gating decisions |

Do not spawn Lead-Build or Lead-Test before Lead-Plan completes — they need the plan
embedded in their prompts as context. Parallel spawn here would mean Lead-Build operates
without architecture, which produces drift.

**Exit when:** Lead-Plan has returned a deliverable AND the Auditor has produced its
matrix on plan.md with all rows PASS or with FAIL→fix→PASS resolved. If Auditor
returns UNVERIFIED on any plan row, do not proceed to Phase 2.5 — surface to user.

### Phase 2.5: Re-Evaluation Gate (Iterative Skill Pull-In)

Before spawning Lead-Build + Lead-Test, the Director re-evaluates the skill set
against what Lead-Plan actually discovered. This is the iterative pull-in that makes
the router behave less like "fan-out from initial classification" and more like
"keep refining as the work reveals itself." Borrows the loop structure from
`skills/iterative-retrieval/SKILL.md`.

Two inputs trigger re-evaluation:

1. **Explicit Skill requests from Lead-Plan.** If plan.md contains a `## Skill requests`
   section (per the §3.1 spawn template addition), each named skill becomes a
   candidate for embedding into Lead-Build / Lead-Test prompts. The Director scores
   the requested skills against the request + plan.md tokens (run §6 scoring on the
   expanded token set) and embeds any clearing threshold 5.
2. **Implicit token drift.** The Director extracts new keywords from plan.md that did
   not appear in the original request (e.g. plan.md mentions "PDF" but the original
   request did not). Director re-runs §6 + §6.5 scoring with the expanded token set.
   Any skill that now clears threshold AND wasn't already matched gets considered for
   embedding.

After Phase 3 Workers report up to their Leads (but before Phase 4 Auditor gate), the
same re-evaluation runs once more with each Lead's discoveries as additional input
to §6 + §6.5 scoring.

**Cap: 2 re-evaluation rounds total per run.** A Lead-requested skill that arrives in
round 3 triggers an assumption ledger entry instead of another round:
`A_N: Skill X requested late by Lead-Y but re-eval cap reached. Not added.`

**Exit when:** either (a) no new skills cleared threshold in the most recent round, or
(b) the 2-round cap is hit, or (c) Lead-Plan's plan.md contained no Skill requests
section AND no new keywords appeared. In all cases, log to the audit trail what was
considered, what was embedded, and what was rejected.

### Phase 3: Workers Execute Under Leads

Each Lead spawns its own Workers (also opus). The Director does NOT spawn Workers
directly. The Lead defines file ownership boundaries (see agent-teams pattern in
gvo-skills) so Workers don't collide.

Maximum 3 Workers per Lead simultaneously. If more than 3 needed, the Lead serializes.

**Exit when:** every Lead reports its deliverable back to the Director with all of
its Workers' outputs aggregated AND its evidence section populated with literal
commands + outputs. A Lead that returns BLOCKED counts as exiting Phase 3 (in the
fail path) — Director routes to recovery in §8, not to Phase 4.

### Phase 4: Auditor Gate (Critical)

After each Lead reports "complete":

1. Auditor receives the Lead's deliverable + the Lead's evidence section
2. Auditor independently runs the verification commands (does not trust the Lead's
   transcript)
3. Auditor produces a PASS / FAIL / UNVERIFIED matrix
4. Director reads the Auditor's matrix:
   - All PASS → mark Lead complete, proceed
   - Any FAIL → return Lead's deliverable to it with the failing line, request fix,
     re-run audit (max 2 fix cycles per Lead)
   - Any UNVERIFIED → block delivery, ask user for input on the unverifiable item
     (this is the only place the auto-mode rule is broken — the user MUST be asked,
     because UNVERIFIED means no evidence exists to decide)

Read [references/empirical-verification.md](references/empirical-verification.md) for
the full evidence protocol and matrix format.

**Exit when:** every Lead's deliverable has been audited AND the resulting matrix has
no FAIL rows (all FAIL→fix→PASS resolved within 2 fix cycles, OR the pipeline
halted to surface). UNVERIFIED rows are allowed at exit but each one must be
tagged in the final delivery, not silently dropped.

### Phase 5: Deliver

Compose the final user-facing response with three sections:

1. **Result** (plain English, no jargon outside code blocks): what got built / fixed /
   produced, and where it lives.
2. **Verification matrix** (table): every checked claim, the command that proved it, the
   PASS/FAIL/UNVERIFIED result, and a one-sentence plain-English summary.
3. **Assumption ledger** (table): every autonomous decision the org made, by ID, with
   confidence level and the alternative that was rejected. The user can reverse any with
   "reverse A3".

Per the user's CLAUDE.md plain-English rule: technical terms (commit hashes, version
strings, internal tool names, file paths in prose) only appear inside fenced code blocks
or table cells. Outside those, translate to plain English.

**Exit when:** the user-facing message has been composed with all three required
sections (Result, Verification matrix, Assumption ledger), every section's prose is
plain English outside code blocks, and the message has been sent. The skill run
ends here — do not continue the conversation unless the user replies with a
follow-up or a "reverse A_N" instruction.

## 5. Hard Rules (Non-Negotiable)

1. **Explicit model on every spawn; opus by default; sonnet only for deterministic
   actions; never haiku.** Every sub-agent spawn must specify a `model` parameter
   explicitly (never inherit). Opus is the default and is required for every role
   that involves judgment — Director, Leads, Workers doing planning/building/testing,
   and the Auditor. Sonnet is acceptable ONLY for inherently deterministic mechanical
   execution: shell commands fully specified by an opus-tier caller, like
   `git push origin main`, `wrangler tail`, or `npm run typecheck`. If the worker
   must *decide* anything (which command, which file, whether output is correct),
   it's a judgment task — use opus. Haiku is never used, in any role, for any reason.
   Audit each spawn before submission and fix the `model` field if wrong.
2. **Evidence-or-no-claim**. The Director never writes "verified", "complete", "passed",
   "tests pass", "deploy succeeded", "all checks green" in user-facing output unless the
   matching Auditor row says PASS with command output. If the Auditor said UNVERIFIED,
   you write `[UNVERIFIED — see ledger]` instead.
3. **Auditor independence**. The Auditor must spawn with read-only access to Lead
   transcripts and re-run verification commands itself. Never paraphrase a Lead's
   evidence as Auditor evidence — that's collusion.
4. **Two legitimate mid-run pauses: Coding-Class Approval Gate and Auditor
   UNVERIFIED**. For coding classes (`build / enhance / fix / full-stack`),
   surface plan.md to the user for explicit approval before Phase 3 (Lead-Build /
   Lead-Test) spawn — see §4 Phase 2 Step D.5 and §12 pillar 12. The trivial-task
   escape hatch may skip this pause (<5 line change, single file, no behavior
   risk, unambiguous intent). For non-coding classes (`quick / research /
   other`), continue under the autonomous contract: interpret from available
   evidence — including Phase 0 classification ambiguity, ambiguous file paths,
   missing project context, or unclear scope — log to the assumption ledger
   with a confidence level, and proceed. The Auditor's UNVERIFIED rows in Phase 4
   are the second pause trigger and apply to every class. The user can reverse
   any ledger entry post-hoc with "reverse A_N".
5. **3 consecutive low-confidence assumptions = halt**. If the ledger shows 3 in a row at
   `confidence: low`, stop the whole pipeline, return what you have, and surface the
   ledger to the user. Compounding low-confidence calls is how silent failures happen.
6. **Plain English outside code blocks**. The user can't act on jargon. See the
   plain-English mapping table in their CLAUDE.md (commit hashes → "the change", version
   strings → "the newer X library", tool names → "the type checker", etc.).
7. **One skill, one domain**. If the matched skill already covers the work (e.g., a pure
   `/pdf:fill-form` request), call that skill directly via its trigger and skip the org
   structure. Don't run a 3-tier org for tasks a single skill solves.

## 6. Skill Matching

Read [references/skill-matching.md](references/skill-matching.md) for the full algorithm.
Summary:

1. Tokenize the user's request — extract verbs, nouns, named entities (project, file,
   library, framework).
2. Score each skill in `registry.json` by: (a) trigger phrase overlap (3 pts each),
   (b) description keyword overlap (1 pt each), (c) tag match (2 pts each), (d) name
   substring match (5 pts).
3. **Top 2 skills above threshold 5 = the final list handed to Leads.** §6.5 widens
   internally to top 5 as candidates for content re-rank, then narrows back to top 2.
   Below threshold = treat as `Class: other` and route through default
   plan/build/test pipeline.
4. If multiple skills tie or near-tie, prefer the one with the more specific name (longer
   substring match against the request).
5. Loaded skills' SKILL.md must be read in full, then **trimmed before embedding** in
   Lead/Worker prompts. Strip these sections from the body before embedding:
   - `## What This Skill Is NOT` and any "Not for..." lists
   - `## Anti-Patterns` and `## What X Doesn't Do` sections
   - `## Worked Examples` / `## Examples` blocks (illustrative only, not load-bearing)
   - Large reference tables that duplicate information available in adjacent prose
   - Footnotes, version history, FAQ sections

   Keep: instructional sections (how to act), spawn templates, hard rules /
   constraints, error-mode tables, decision matrices, pillar lists. Leads receive
   the trimmed content as embedded context, never as a path. Trimming typically cuts
   skill content by 40–60% with no loss of actionable guidance — see
   [references/skill-matching.md](references/skill-matching.md) "Loading Skills'
   Content" for the full strip + keep recipe.

## 6.5 Refinement Pass (Content-Aware Re-Rank)

§6 scores against registry metadata only — description, triggers, tags, name. The
registry has 17% empty triggers and 91% empty tags (verified 2026-05-17), so
metadata-only scoring under-ranks skills with weak metadata even when their
SKILL.md body is the right fit. §6.5 fixes this by re-ranking on actual content.

### Skip condition

Skip §6.5 entirely when EITHER of these holds — both indicate an unambiguous winner
that content re-ranking won't change:

1. **Any single skill scored ≥ 15** in §6.
2. **Top §6 score is ≥ 2× the second-place §6 score** (e.g., top=12, second=5 → skip;
   top=8, second=6 → run §6.5). A cluster of similar scores means §6.5 may surface a
   better match; a large gap means the leader is already clear.

Saves ~25K input tokens per run whenever either condition fires (5 SKILL.md body
reads + 1 opus scoring call avoided).

### Algorithm

1. **Initial §6 produces top 5** as candidates (wider than the final top-2 cap, to
   give §6.5's content re-rank a real pool to work with).
2. **Read all 5 SKILL.md bodies in parallel** via `<prefix>__codebase_read_file`.
   Strip YAML frontmatter from each.
3. **One opus scoring call** with this prompt shape:
   ```
   Request: "<user's literal request>"

   For each of these 5 skills, score 0-10 on how well its full instructions match
   the request. Output JSON only: [{"name": "X", "score": N, "why": "<≤80 chars>"}, ...]

   Skills:
   ## skill-1-name
   <body of SKILL.md, frontmatter stripped>

   ## skill-2-name
   <body>
   ...
   ```
4. **Re-rank by content score.** Top 2 by content score (not §6 score) are the
   matched skills handed to Lead-Plan.
5. **Log dropped matches.** Any skill that scored well in §6 but dropped in §6.5
   gets an assumption ledger entry:
   `A0_dropped_match: <name> (§6 score: X, §6.5 content score: Y, why: <reason>)`.
   The user can reverse with "also use <name>".

### Cost

- 5 `codebase_read_file` calls (parallel, cheap)
- 1 opus scoring call (~5K-25K input tokens depending on skill sizes; output is JSON)

Net: §6.5 adds 5 reads + 1 opus invocation per matching run where the skip condition
doesn't fire. Acceptable cost for catching shallow-metadata misses.

### What §6.5 does NOT fix

Skills whose registry metadata is so weak they don't make §6's top 5 in the first
place. That's a registry data-quality problem — fix the empty `tags` / `triggers`
arrays via a separate sweep (out of scope for this skill).

## 7. Stack Defaults

If the user does not specify, mirror nexus defaults:
- Cloudflare Workers + Hono + D1 (Drizzle) + R2 + KV
- React Router v7 + Tailwind + shadcn/ui
- Vitest + Playwright
- Deploy via `git push origin main` (Cloudflare auto-builds), not `wrangler deploy`

If the user has a project under `conductor/tech-stack.md`, use that instead of defaults.
Always log the chosen stack as an assumption (`A0: Stack = <X>, confidence: high if from
project, medium if defaulted`).

## 8. Failure Modes & Recovery

| Symptom | Likely Cause | Recovery |
|---------|--------------|----------|
| Lead returns BLOCKED | Worker output unreadable / spec ambiguous | Director re-spawns Lead with clarified prompt + the BLOCKED reason as context |
| Auditor says FAIL repeatedly (3+ times on same item) | Lead is wrong AND fix loop is broken | Halt the pipeline, return the failure trail, surface to user. Do NOT silently keep retrying. |
| from-desktop MCP returns errors | Connector flaky or registry path wrong | Halt §1 environment gate. Surface the literal error. |
| Sub-agent returned haiku output, OR sonnet output on a judgment task | Spawn template missing explicit `model`, or set to haiku, or set to sonnet for a non-deterministic task | Discard the output, re-spawn on opus with an explicit `model` field. Log as an internal incident in the ledger. Sonnet output on a strictly mechanical command (e.g., `git push`) is fine — keep it. |
| 3 consecutive `confidence: low` assumptions | Compounding uncertainty | Halt and surface ledger. See §5 rule 5. |

## 9. What This Skill Is NOT

- **Not a state-persistence layer**. That's conductor. This skill borrows conductor's
  context-capture pattern but does not replace it. If a project needs state across
  sessions, write to `conductor/tracks/<id>/metadata.json` via Lead-Build.
- **Not nexus or gvo-router-cc**. Both target Claude Code CLI / Desktop. Nexus runs a
  7-phase pipeline; gvo-router-cc runs the same 3-tier org pattern as this skill but
  against the local filesystem. This skill targets claude.ai cloud and reads via the
  gvo-skills-mcp Worker. Keep all three parallel — do not merge.
- **Not for prohibited actions**. Banking, password input, file deletion, downloads,
  permissions changes, etc. require user confirmation per the user's CLAUDE.md and the
  system prompt's prohibited-actions list. The Director must reject these before
  spawning any Lead.

## 10. Quick Reference Card

```
1.  §1 Environment gate — claude.ai? from-desktop? registry?
2.  §2 Read prereqs — registry, conductor, project state (parallel)
3.  §6 Match skills against the request; §6.5 content-aware re-rank (unless skipped)
4.  §4 Phase 0 — classify; if `Class ∈ {build/enhance/fix/full-stack}`, §12 pillars apply
5.  §4 Phase 1 — capture context
6.  §4 Phase 2 Step A–D — spawn Lead-Plan (opus); for coding classes, embed §12
    Dev Pillars in Lead-Plan's prompt
7.  §4 Phase 2.5 — re-evaluation gate (iterative skill pull-in)
8.  §4 Phase 2 Step D.5 — APPROVAL GATE for coding classes (skip for
    quick/research/trivial)
9.  §4 Phase 2 Step E + Phase 3 — spawn Lead-Build + Lead-Test (opus, parallel);
    for coding classes, embed §12 Dev Pillars in their prompts too;
    Workers may CONSULT mid-task — Director routes per §3.2
10. §4 Phase 4 — Auditor (opus, independent) gates each Lead's "complete"; for
    coding classes, Auditor enforces §12 pillar compliance — violations = FAIL rows
11. §4 Phase 5 — assemble Result + Verification matrix + Assumption ledger
12. §11 Memory writes — POST skill-evolution analyses
13. Deliver to user, plain English outside code blocks
```

## 11. Memory Writes (Fire-and-Forget)

After every run, the Director POSTs a per-run analysis to the skill-evolution
Worker. This is the long-term store of "which skill worked for which intent" across
all router runs. The Worker is already deployed at
`https://skill-evolution.lando555.workers.dev` (verified 200 OK on 2026-05-17).

### When to POST

After Phase 5 has delivered the user-facing message. The POST does not block delivery
and must not delay it. Fire-and-forget: send the request, do not wait for the
response, log a one-line outcome.

### Endpoint

```
POST https://skill-evolution.lando555.workers.dev/analyses
Content-Type: application/json
```

> **Known issue (2026-05-18):** the `/analyses` endpoint returns HTTP 500
> ("internal server error") on every POST regardless of body shape. `/health`
> still returns 200. Root cause is a D1-side bug in the skill-evolution Worker
> itself (separate project at `/home/lando555/skill-evolution/`). Until that's
> fixed, D2 POSTs will fail every run. The router's failure handling (below)
> covers this: log `memory_d2_post_failed` and continue. Once the upstream
> Worker is fixed (check `/health` for `version` > `0.1.0`), D2 starts
> recording without code changes here.

### Body schema

```json
{
  "taskId": "<router-run-uuid>",
  "taskCompleted": true | false,
  "skillJudgments": [
    {
      "skillId": "<id-field-from-registry>",
      "skillApplied": true | false,
      "note": "<one-sentence: matched at §6 score X, §6.5 content score Y, used in Lead-Z>"
    }
  ]
}
```

`taskCompleted` is `true` only if Phase 4 Auditor returned all-PASS or all-PASS-with-UNVERIFIED;
otherwise `false`. Every matched skill (whether §6 only or §6 + §6.5) gets a
`skillJudgments` row. Skills considered but dropped at §6.5 get `skillApplied: false`
with the drop reason in `note`.

### Failure handling

If the POST fails (timeout, 5xx, network error), log to the audit trail as
`memory_d2_post_failed: <reason>` and continue. The run still succeeds. The next
run will POST its own analysis — drift is acceptable since the Worker is
fire-and-forget.

### What this does NOT do

This is gvo-router (cloud). It does NOT write to local files because claude.ai cloud
sessions cannot. The Claude Code counterpart `gvo-router-cc` additionally writes a
local `routing-decisions.md` per project; see its §11 for that surface.

## 12. Dev Pillars (Apply to All Coding Work)

When the request is coding work — `Class ∈ {build, enhance, fix, full-stack}` — the
Director MUST embed all 12 pillars below verbatim into every Lead spawn prompt as a
`## Dev Pillars (apply throughout)` section appended after the existing "Hard
constraints" block from §3.1. Leads then propagate the same pillar text into their
own Worker spawn prompts. Workers cite pillars by number in their evidence section
when they make a relevant choice (e.g., "pillar 5 — kept function under 50 lines by
extracting `parseToken`").

Non-coding classes (`quick / research / other`) do NOT trigger pillar embedding —
the pillars target code-touching work specifically.

### The 12 Pillars

1. **Empirical verification, evidence-or-no-claim** — Every claim of
   "verified / complete / passed / tests pass / deploy succeeded" must be backed by
   a fenced code block with the literal command + its output. See
   [references/empirical-verification.md](references/empirical-verification.md).

2. **Plain English outside code blocks** — Technical terms (commit hashes, version
   strings, tool names, file paths in prose) appear only inside fenced code blocks
   or table cells. Surrounding prose translates to plain English per the user's
   CLAUDE.md mapping table.

3. **Opus default, Sonnet exception for inherently deterministic mechanical
   actions** — Code-touching agents use Opus. Sonnet acceptable only for
   fully-specified shell commands where the agent makes zero decisions (e.g.,
   `git push origin main`, `wrangler tail`, `npm run typecheck`). If the agent
   must *decide* anything — which command, which file, whether output is correct —
   use Opus. Never haiku, in any role. Scoped to this skill only — the global
   CLAUDE.md / rules/common/performance.md all-Opus lockdown stays in force
   outside gvo-router and gvo-router-cc.

4. **Multi-agent reporting contract** — Every Worker deliverable: Claim (one
   sentence) + Evidence (`file:line`, command + output, test artifact, or
   `[UNVERIFIED]` with reason) + Confidence % (grounded in something specific) +
   Gap-closer (one sentence on what would raise confidence).

5. **Coding style — KISS, DRY, YAGNI, immutability** — Simplest solution that
   works; extract repeated logic only when repetition is real; don't build for
   hypothetical futures; create new objects, never mutate existing ones. Hard
   limits: files <800 lines, functions <50 lines, nesting <4 levels deep. Early
   returns over nested conditionals. Named constants over magic numbers.

6. **Explicit error handling at every level** — Handle errors comprehensively;
   user-friendly messages in UI-facing code; detailed context server-side; never
   silently swallow errors. Validate at every system boundary (user input,
   external API responses, file content).

7. **No hardcoded secrets** — API keys, passwords, tokens via env vars or secret
   manager only. Validate required secrets present at startup. Trigger
   security-review when touching auth, payments, user input, file system
   operations, external API calls, or crypto.

8. **Search-first / no duplication** — Before writing new code: `gh search repos`,
   `gh search code`, Context7 docs, package registries (npm / PyPI / crates.io).
   Prefer adopting or porting a proven approach over hand-rolled alternatives.
   Exa only when GitHub + primary docs are insufficient.

9. **70% test coverage minimum** — Unit + integration + E2E tests required for
   new functionality. TDD: write tests first (RED), implement minimal to pass
   (GREEN), refactor (IMPROVE). Per the user's CLAUDE.md override of the 80%
   common default.

10. **Local-first development** — `npm run dev` + `npm test` locally before any
    push. Deploy via `git push origin main` (Cloudflare Workers Builds runs the
    pipeline), not `wrangler deploy`. Use the remote production database for
    local dev — never scaffold a second DB unless the project's CLAUDE.md
    explicitly says so.

11. **Anti-template design (frontend work only)** — Reject generic Tailwind /
    shadcn defaults. Required qualities: clear hierarchy through scale contrast,
    intentional spacing rhythm (not uniform padding), depth or layering, designed
    hover / focus / active states, semantic HTML over div stacks. See
    `rules/web/design-quality.md` for the full anti-template checklist.

12. **Approval gate for non-trivial coding work** — User must approve plan.md
    before Phase 3 spawn (Lead-Build / Lead-Test). Trivial escape hatch: change
    is <5 lines, isolated to one file, no behavior risk, unambiguous intent →
    skip approval and proceed. See §4 Phase 2 Step D.5 and §5 rule 4. This is
    the second legitimate user-pause in auto mode alongside Auditor UNVERIFIED.
    In claude.ai cloud the pause is conversational: the Director surfaces
    plan.md inline and waits for the user's reply ("approve" / specific
    changes / "trivial escape hatch").

### Pillar Embedding Mechanic

When `Class ∈ {build, enhance, fix, full-stack}`:

1. Director copies §12.1–12 verbatim into a `## Dev Pillars (apply throughout)`
   section appended to every Lead spawn prompt under §3.1's template.
2. Each Lead repeats the same embedding into its Worker spawn prompts.
3. Workers cite pillars by number in their evidence section when relevant.
4. The Auditor (Phase 4) checks pillar compliance on every Lead deliverable —
   violations get a FAIL row in the matrix (e.g., "uses `let` mutation pattern,
   pillar 5 violation"). Standard 2-cycle fix loop applies; after 2 failed fixes
   on the same pillar, halt and surface to user per §8.

No paraphrasing, no abbreviation — the pillar text is the verbatim reference.

## References

- [references/org-structure.md](references/org-structure.md) — full role definitions,
  reporting chain, spawn templates, tier-2 vs tier-3 decision rules
- [references/empirical-verification.md](references/empirical-verification.md) — evidence
  protocol, verification matrix format, Auditor independence rules, no-evidence-no-claim
  enforcement
- [references/skill-matching.md](references/skill-matching.md) — registry parsing,
  scoring algorithm, tie-breaking, embedded-context handoff to Leads
