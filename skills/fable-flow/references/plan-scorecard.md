# Plan-hardening scorecard (Fable-native)

This is the `from-prompter` DNA, repointed. `from-prompter` runs a one-change-per-round scoring
loop to harden a **prompt** before an unattended run. Here the same loop hardens the **architect's
plan** before any code is written — the highest-leverage spot, because the plan is the only
coordination the parallel implementers ever get, and the cheap place to change course.

## The loop (Phase 4 of the pipeline)

```
REPEAT (the orchestrator runs this — no subagent needed):
  1. Score every item below 0–10 against the current .fable-flow/plan.md, using the rubric.
  2. Compute the weighted score: (Σ score×weight) / (Σ 10×weight) × 100.
  3. Target the lowest-weighted item. Diagnose WHY it scored low (one sentence).
  4. Propose ONE change to the plan. Apply it (edit plan.md, or send the architect ONE
     revision request naming just that item).
  5. Re-score ALL items — catch regressions.
  6. DECISION: overall improved → KEEP; flat or worse → REVERT to the prior plan.
  7. Log the round to .fable-flow/plan-rounds/round-NNN.json (item, change, before/after, decision).
  8. EXIT when any of: ≥90% for 3 consecutive rounds · last 3 kept rounds improved <2 pts total
     (plateau) · round 8 reached (max — report residual weaknesses).
```

**One change per round. No exceptions** — isolated changes produce clean signal; bundled changes
hide second-order regressions (a lesson `from-prompter` learned the hard way). Keep the pre-loop
plan untouched at `.fable-flow/plan-v0.md` so a bad loop can always fall back.

The loop runs **before** the single plan sign-off (Phase 5). You present the *hardened* plan to the
user, not the raw architect draft.

## Scoring rubric (applies to every item)

| Score | Meaning |
|---|---|
| 9–10 | No ambiguity. A cold implementer executes the track perfectly with no cross-talk. |
| 7–8 | Minor ambiguity — one reasonable reading exists; the implementer probably gets it right. |
| 5–6 | Needs clarification — the implementer must assume something that could go wrong. |
| 3–4 | Significantly unclear — high chance of a wrong track or a merge collision. |
| 1–2 | Missing or contradictory. |

## Items

| # | Item | Weight | Scores high when… |
|---|---|---|---|
| 1 | **Disjoint ownership** | 2.0 | No file appears in two tracks; the split is by genuine independence, not symmetry. The one property the pipeline cannot survive without. |
| 2 | **Contract completeness** | 1.5 | Every shared type/signature/schema/file two tracks touch is written verbatim in Contracts, with its owner named. Implementers never guess about each other. |
| 3 | **Full spec up front** | 1.5 | Each track manifest carries the complete task for that track — goal, owned files, work, tests, done-when — so the implementer needs zero clarifying questions (the core Fable strength). |
| 4 | **Requirements verifiable** | 1.5 | "Done" is stated as checkable criteria, not vibes; each requirement maps to a test or an observable result. |
| 5 | **Seam named + proven** | 1.5 | The round's riskiest seam (track↔track, or track↔live-runtime) is called out, and Integration verification proves it with ONE real end-to-end run, not just a green unit suite. |
| 6 | **De-prescribed** | 1.0 | Track "Work" states outcomes and constraints, not numbered step lists or "YOU MUST" scaffolding. Over-prescription degrades Fable output — penalize it here. |
| 7 | **Scoped to the task** | 1.0 | No features, refactors, or abstractions beyond what the task requires. No speculative generality. |
| 8 | **Right-sized track count** | 1.0 | Tracks match the number of genuinely independent workstreams. Over-splitting (symmetry for its own sake) invites merge pain; a single track is a valid, often better, plan. |
| 9 | **Design direction** (UI tasks only) | 1.0 | For user-facing work: an explicit aesthetic (type, palette, one motion moment), a track owning the shared design system first, and a headless screenshot in verification. Skip/neutralize this item for non-UI tasks. |
| 10 | **Effort-by-role realized** | 0.5 | The plan is shaped so planning-grade reasoning is spent on the plan, implementer tracks are narrow enough to run at "medium", and the reviewer has an adversarial, wide brief. |
| 11 | **Build-tier assignment** | 1.0 | Every track carries a justified build tier (`fable`/`sonnet`/`haiku`): the frontier tier is reserved for judgement-dense work, no hard track is under-tiered onto a cheaper model, and `sonnet`/`haiku` are used only for well-specified or non-code tracks. Mis-tiering wastes credits (over-tier) or costs a whole review round (under-tier). This is the promode-inspired credit lever. |

Weights are defaults — the user may reweight (0.5×–2.0×) at the plan sign-off. For a non-UI task,
drop item 9 from the denominator rather than scoring it 0 (a 0 would understate a fine plan).

## What this rubric deliberately does NOT reward

Unlike an Opus/Sonnet-era prompt checklist, this rubric does **not** reward: enumerated
step-by-step procedures, "CRITICAL/YOU MUST" pressure language, forced progress-update cadence, or
exhaustive anti-pattern "Do Not" lists. Those degrade Fable 5. If a loop change adds any of them to
raise a different score, that's a regression — revert it. See `fable-prompting.md`.
