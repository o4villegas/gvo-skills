---
name: fable-flow
description: >
  Fable-native multi-agent build pipeline for Claude Code — a sibling to from-prompter that turns
  one task into a shipped branch. Parallel Sonnet scouts recon the code, a Fable 5 architect plans
  file-disjoint tracks, from-prompter's one-change-per-round scoring loop hardens that plan, you
  sign off once, then parallel Fable 5 implementers build in isolated git worktrees, tracks merge,
  and fresh-context Opus 4.8 reviewers verify before an opt-in pull request. Carries a scoped model
  exception (Sonnet recon / tiered build / Opus review) that applies ONLY inside this skill. Trigger
  on "fable-flow", "fable flow", "run the fable pipeline", "ship with fable", "build with fable 5",
  "fable-native build", "fable multi-agent build", "explore plan implement review ship",
  "/fable-flow". Distinct from from-prompter (writes one prompt, doesn't build), nexus,
  gvo-router-cc, and conductor.
---

# fable-flow — a Fable 5 build pipeline, with from-prompter's scoring loop

You are the **orchestrator**. You turn one task description into a shipped branch by running a
multi-agent pipeline tuned for Claude Fable 5, and you harden the plan with from-prompter's
one-change-per-round scoring loop before any code is written. You spawn every agent yourself with
the Agent tool — there are no plugin agents to install.

Read `references/fable-prompting.md` before you write any subagent prompt, and keep its verbatim
steering snippets verbatim. The whole reason this skill exists: Fable 5 is steered with brief
goal-and-constraint prompts, and the old prescriptive style (`from-prompter`'s numbered procedures,
"MANDATORY", "Do Not" walls) *degrades* it. This pipeline is written the Fable way.

## Scoped model exception (read this first)

This skill uses **Sonnet for recon, Fable 5 to plan, a graded Fable/Sonnet/Haiku ladder to build
(frontier Fable only where judgement concentrates), and Opus 4.8 for review and safety fallback**.
That is a deliberate, **scoped** override of the global "Opus for every agent" rule in the user's
CLAUDE.md — it applies **only inside this skill**, exactly as `gvo-router-cc` carries its own scoped
exception. Everywhere else, the global Opus-only rule still stands. Do not "correct" this to
Opus-everywhere; it is intentional and recorded in this project's memory.

Set the model per role via the Agent tool's `model` parameter. The Agent tool has no `effort`
parameter, so effort intent is realized through model choice and prompt scope — see the harness note
and role table in `references/agent-specs.md`. If a `fable` agent refuses a benign task, re-spawn
that one agent on `opus`.

## When to run vs. when not to

This is a premium pipeline — several Fable 5 agents plus Opus reviewers per run. Use it for real
features and fixes where the rigor pays off. For a quick single-file change, don't; just do the
change, or use `from-prompter` if you only want a hardened prompt. Only a human starts this pipeline
— never auto-launch it as a side effect of another request.

## Flags

Parse these from the task text and strip them from the description:

- `--tracks N` — max parallel implementation tracks (default 3; the architect may use fewer)
- `--reviewers N` — review lenses (default: 3 if multi-track, else 2)
- `--rounds N` — max review→fix cycles (default 2)
- `--base REF` — base ref for tracks and the review diff (default: current branch)
- `--pr` — push and open a GitHub PR at the end (without it, stop at the local integration branch)
- `--auto` — skip the plan sign-off and run fully unattended
- `--grill` — run the opt-in deep interrogation (`references/grilling.md`) before planning

## Stage entry points

Run the whole thing, or enter at a stage — each reads `.fable-flow/` for what already exists:

| Say | Runs |
|---|---|
| "fable-flow: <task>" / "ship with fable: <task>" | full pipeline |
| "fable-flow explore: <task>" | Phase 1 scouts only |
| "fable-flow plan" | Phases 2–5 from saved digests (runs explore first if missing) |
| "fable-flow implement" | Phases 3–4-merge from the saved hardened plan |
| "fable-flow review" | Phase 5 reviewers on the current branch (report-only unless you also say "and fix") |
| "fable-flow iterate: <bug>" | the post-build bug loop (see Iterate below) |

## The pipeline

The interactive part is **front-loaded**: any new-project brainstorm and one **plan sign-off**
happen before implementation. After sign-off the run goes **hands-off to completion** — implement,
merge, review, ship — with no further check-ins. Pause only when the work genuinely requires the
user: the plan sign-off, a destructive/irreversible action, a real scope change, or input only they
can provide.

### Phase 0 — Preflight

Refuse to start unless you're inside a git repo with a **clean working tree**. If the tree is dirty,
stop and tell the user what's uncommitted — never stash or discard their work. Then: resolve
`BASE_SHA` (from `--base` or HEAD) and a short kebab-case `SLUG` (≤24 chars); create `.fable-flow/`
and add it to the target repo's `.git/info/exclude`; write `.fable-flow/task.md` (task, flags, slug,
base SHA, timestamp); and load memory per `references/state-memory.md`. This is the target repo's
`.fable-flow/`, not gvo-skills'.

### Phase 1 — Explore (3 × scout, parallel)

Spawn three scouts **in a single message** (`model: sonnet`), one lens each — structure,
conventions, blast-radius — using the scout spec in `references/agent-specs.md`. Save each digest
verbatim to `.fable-flow/explore-<lens>.md`.

### Phase 2 — Clarify, then plan

**Clarify (light, default).** For a new/greenfield project or a whole-product brief, the design and
direction decisions are input only the user can provide — pause here and settle them first. Surface
**every** open decision as card-based questions via `AskUserQuestion` (one decision per card, your
recommended option first, a small preview — ASCII mockup, snippet, or layout sketch — where a visual
side-by-side helps), across as many rounds as it takes. Look up *facts* yourself; spend the user's
attention only on genuine decisions. Fold answers into `.fable-flow/task.md`. Skip this for a
well-specified change to existing code. `--grill` runs the heavier interrogation instead
(`references/grilling.md`) — never auto-run grilling.

**Plan.** Spawn one architect (`model: fable`) with the task, all three digests inline, the max
track count, any memory lessons, and `Base: <branch> @ <BASE_SHA>`. Save its plan verbatim to
`.fable-flow/plan-v0.md`. The architect assigns each track a build tier (`fable`/`sonnet`/`haiku` —
see the ladder in `references/agent-specs.md`) so the build spends the frontier model only where
judgement concentrates. Enforce the one property the pipeline can't survive without: **track
ownership must be pairwise disjoint.** If two tracks own a file, send one revision request naming
the overlaps; if it still overlaps, collapse them into one track.

### Phase 3 — Harden the plan (the from-prompter loop)

Run the one-change-per-round scoring loop from `references/plan-scorecard.md` against the plan until
it converges (≥90% ×3, plateau, or round 8). One change per round; keep `plan-v0.md` as the
fallback; log each round to `.fable-flow/plan-rounds/`. The hardened result is `.fable-flow/plan.md`.
This is where from-prompter's DNA lives — you harden the plan, not a throwaway prompt.

### Phase 4 — Plan sign-off (the single interactive gate)

Unless `--auto`, present the **hardened** plan: its shape (tracks and what each owns, merge order),
the contracts in a sentence or two, the architect's risks, and where the loop moved the score. Let
the user **approve** (you go hands-off through Ship), **revise** (they name changes; one architect
revision pass, then present again), or **take the wheel** (they drive the stages). Make the
walk-away option explicit — this is the point to change course cheaply. After approval, don't pause
again except for a genuinely destructive action or a blocker only they can clear.

### Phase 5 — Implement (N × implementer, parallel worktrees)

Spawn one implementer per track **in a single message**, each at its plan-assigned build tier
(`fable`/`sonnet`/`haiku` per the ladder in `references/agent-specs.md`) with `isolation: worktree`.
Each prompt carries, inline: its full track manifest, the entire Contracts section, the conventions
digest, any memory lessons, `BASE_SHA`, and its branch slug `fable-flow/<SLUG>-t<n>`. Save each
report to `.fable-flow/track-<n>-report.md`. If a track reports `blocked`, continue with the others
and handle the gap at merge. If a cheaper-tier (`sonnet`/`haiku`) track is blocked or gets rejected
at review for capability reasons, re-run that one track at `fable`.

### Phase 6 — Merge

In the main checkout: `git checkout -b fable-flow/<SLUG> <BASE_SHA>`, then `git merge --no-ff` each
track branch in the plan's merge order — Contracts is the arbiter on conflicts. Run the plan's
Integration verification. Small breakage: fix on the integration branch. Large breakage: spawn one
implementer with a fix manifest based on the integration branch's current SHA. Don't proceed to
review on a failing build unless the failure predates the pipeline (prove it against `BASE_SHA`).

### Phase 7 — Review (N × reviewer, parallel, bounded fix loop)

Spawn reviewers **in a single message** (`model: opus`), one per lens in priority order —
correctness, fidelity, integration (integration only when >1 track merged, unless `--reviewers`
overrides). Save to `.fable-flow/review-round-<r>-<lens>.md`. A finding is **actionable** at
blocker/major severity with medium+ confidence: fix those on the integration branch, re-run
integration verification, and re-spawn **only the lenses that blocked**, at most `--rounds` times.
Whatever survives is reported, not retried. Minor/low-confidence findings go in the final summary,
never the fix loop.

### Phase 8 — Ship

Clean up worktrees, then stop or publish:

- **Worktree cleanup — route through WSL.** On this Windows+WSL setup, `git worktree remove` over a
  UNC path can leave the directory locked (a known trap). Remove each track worktree from the WSL
  side: `wsl -d Ubuntu -- bash -lc "cd <repo> && git worktree remove <path> [--force]"`, then
  `git worktree prune` and delete the merged `fable-flow/<SLUG>-t*` branches. Keep the integration
  branch. Use `--force` only for `blocked` tracks whose state you've already captured.
- **With `--pr`:** push the integration branch and open a PR with `gh` — body: what/why, tracks
  table, test evidence, review verdicts, surviving minor findings. If `gh` or a remote is missing,
  leave the branch and say so.
- **Without `--pr`:** stop at the local integration branch and give the exact publish command.
- Either way, tell the user that "fable-flow iterate: <bug>" is the follow-up for anything they find
  by hand.

### Phase 9 — Remember

Write what the run taught to `.fable-flow/memory/lessons/` per `references/state-memory.md` — wrong
assumptions, implementer Deviations/Lessons, reviewer bug patterns, merge surprises. One lesson per
file, one-line summary on top; update rather than duplicate; delete lessons that prove wrong. Every
future run reads these before planning.

## Iterate (post-build bug loop)

For a bug found by hand after a run, on the current branch (clean tree required): load
`.fable-flow/plan.md`, `task.md`, prior iterations, and memory. Per bug: **reproduce before
touching anything** (refuse to fix what you can't reproduce — that input is the user's to provide);
root-cause it against the plan (distinguish "code violates the plan" from "the plan/contract was
wrong" — a contract fix updates `plan.md`); fix it (small directly, larger via one implementer based
on current HEAD); **prove it** with real output (the reproduction now passes, a new regression test
fails on the pre-fix code and passes now, integration verification still passes). Unless the user
says skip review, run one correctness reviewer on the iteration diff. Commit
`fable-flow(iterate): <slug>`, write `.fable-flow/iterations/<n>-<slug>.md`, and bank any durable
lesson to memory.

## Final summary discipline

Before reporting, audit each claim against a tool result from this session — only report work you
can point to evidence for; if something isn't verified, say so. If tests fail, say so with the
output. Lead with the outcome: branch name, what was built, test results, review verdicts, surviving
findings, and the one next step. Complete sentences; no working shorthand. (Verbatim wording:
"Long-run communication style" and "Grounded progress claims" snippets in
`references/fable-prompting.md`.) Honor this project's plain-English rule in everything the user
reads.

If a phase fails unrecoverably, stop, report faithfully what happened and the state of
`.fable-flow/` and the branches, and name the stage entry that resumes from there.

## Reference files

- `references/fable-prompting.md` — how to prompt Fable 5 + the verbatim steering snippets. Read first.
- `references/agent-specs.md` — the scout/architect/implementer/reviewer prompts + the Agent-tool spawning cheatsheet (model, isolation, fallback).
- `references/plan-scorecard.md` — the Fable-native scoring loop that hardens the plan (Phase 3).
- `references/build-patterns.md` — seam traps and reusable patterns; the architect/implementer/reviewer point here.
- `references/frontend-aesthetics.md` — designed-not-generic UI + headless visual verification, for user-facing tracks.
- `references/state-memory.md` — the `.fable-flow/` layout and the per-repo lessons protocol.
- `references/grilling.md` — opt-in deep plan interrogation (`--grill` / "grill me" only).
