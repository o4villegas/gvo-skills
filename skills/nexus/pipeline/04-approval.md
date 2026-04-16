# Phase 4 — Approval

**Goal:** Present the Phase 3 plan clearly, get a decision (proceed / change / reject), and either advance to Phase 5 or loop back to Phase 3 with new constraints.

## Summary template

Present in this exact order — user can say "yes" after reading the first three lines if the plan is obviously right:

```markdown
**What it is:** [2-sentence description — outcome-first, not feature-first]

**Stack:** [one line — e.g. "CF Workers + Hono + D1 (Drizzle) + React 19 + Tailwind v4 + shadcn/ui"]

**Key features:**
- [3–6 bullets of user-visible capabilities]

**Architecture (one diagram):**
[ASCII or mermaid-in-text for CLI; visualize tool output for claude.ai context]

**Top risks:**
1. [Risk] → [mitigation]
2. [Risk] → [mitigation]

**Plan length:** [N] 15-min units across [M] phases. Estimated session count: [S].

**Proceed?** Yes / No / Change [specify what]
```

## Presentation channel

| Environment | How to present |
|-------------|----------------|
| Claude Code CLI | Markdown message with ASCII diagram. Use code fences for structured blocks. |
| claude.ai with Canvas/Artifacts | Write plan to `/mnt/user-data/outputs/plan.md`, reference file, show summary inline. |
| claude.ai without tools | Inline markdown; use Mermaid syntax in fenced blocks where supported. |

## Decision handling

| User response | Action |
|---------------|--------|
| **"Yes" / "proceed" / thumbs up** | Advance to Phase 5. Do not revisit the plan unless Phase 5 hits a blocker. |
| **"Change X"** | Return to Phase 3 with X as a new constraint. Run the council *only on the affected section* — do not re-plan the untouched 80%. |
| **"No"** | Ask: what about this is wrong — scope, stack, direction, risk, or all of it? Return to Phase 1 (scope/direction) or Phase 3 (stack/risk) based on answer. |
| **Silence / ambiguous** | Use `AskUserQuestion` with a single yes/no: "Ready to start building, or change something?" |

## Rejection handling

Rejection is not failure — it's missing information. When the user rejects:

1. Thank them briefly (not effusively)
2. Ask the one question that will most narrow the new space (`AskUserQuestion`, single question)
3. Return to the phase that best addresses the feedback:
   - Wrong problem → Phase 1
   - Wrong approach → Phase 3
   - Wrong stack/tool → Phase 3 with the stack constraint locked
4. **Do not restart from scratch.** Preserve what was validated.

## Risk communication

Risks must be actionable, not scary. Each risk gets:
- **Likelihood** (low / medium / high) based on empirical evidence
- **Impact** (contained / blocking / data-loss) if it fires
- **Mitigation** (specific action, not "we'll watch for it")

Rule: if you cannot write a specific mitigation, the risk is actually a *requirement* — move it to the plan, not the risk register.

## Anti-patterns

| Do NOT | Do instead |
|--------|------------|
| Dump the full Phase 3 plan into chat | Show the summary template; full plan lives in a file |
| Ask "does this look good?" | Ask "Proceed? Yes / No / Change X." — give the user something to click |
| Treat approval as irrevocable | If Phase 5 discovers the plan was wrong, return here transparently |
| Hide risks to get approval | Surface top 3 risks with mitigations — the user trusts the plan more when you name the downside |
| Restart from Phase 1 on "change X" | Only re-run the affected part of Phase 3 |

## Handoff to Phase 5

On approval, write a single line to working state: `"Phase 4 approved [timestamp]. Plan: [link/path]."` Then proceed to scaffold — no user intervention until Phase 6.
