# Assumption Ledger — Auto Mode Decision Logging

When running in `--mode=auto`, nexus encounters ambiguities that would normally trigger
a question to the user. Instead of stopping, it logs each decision to a structured ledger
and continues working. At delivery, the full ledger is presented for review.

## When to Log

Log an assumption whenever you:
1. Choose between 2+ valid implementation approaches
2. Interpret an ambiguous requirement one way when another reading is plausible
3. Make a UX/design decision the user didn't specify
4. Select a library, pattern, or architecture without explicit instruction
5. Skip or defer something that could reasonably be in scope
6. Handle an edge case where the correct behavior isn't obvious

**Do NOT log:**
- Obvious implementation details (variable names, formatting)
- Decisions dictated by the tech stack or CLAUDE.md
- Standard patterns established in codebase conventions

## Ledger Format

Write assumptions to `conductor/tracks/{track-id}/assumptions.jsonl` (one JSON object per line):

```jsonl
{"id":"A1","ts":"2026-04-16T20:30:00Z","phase":"plan","question":"Should the drying chart show all visits or only the last 5?","assumption":"Show all visits with horizontal scroll","confidence":"high","alternatives":["Show last 5 with 'show more' button","Paginate by 10"],"evidence":"Existing DryingProgressChart.tsx renders all visits without pagination","blast_radius":{"files":["src/components/DryingProgressChart.tsx"],"lines_changed":12},"reversible":true,"reversal_cost":"low","commit":"abc1234"}
{"id":"A2","ts":"2026-04-16T20:35:00Z","phase":"implement","question":"Should we use a modal or inline expansion for reading details?","assumption":"Inline expansion (Sheet component) matching existing ReadingFormSheet pattern","confidence":"high","alternatives":["Full-screen modal","New page route"],"evidence":"ReadingFormSheet uses shadcn Sheet (side panel) — consistent with existing UX","blast_radius":{"files":["src/components/ReadingDetail.tsx","src/components/ReadingsDataTable.tsx"],"lines_changed":45},"reversible":true,"reversal_cost":"medium","commit":"def5678"}
```

## Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Sequential ID (A1, A2, ...) for easy reference |
| `ts` | ISO 8601 | When the assumption was made |
| `phase` | string | Nexus phase: plan, implement, test, review |
| `question` | string | The question that WOULD have been asked (written as if to the user) |
| `assumption` | string | What was decided instead |
| `confidence` | high/medium/low | How confident the agent is in this choice |
| `alternatives` | string[] | Other valid options that were considered |
| `evidence` | string | Why this choice was made (cite files, patterns, standards) |
| `blast_radius` | object | Files and approximate lines affected by this decision |
| `reversible` | boolean | Can this be cleanly reverted without cascading changes? |
| `reversal_cost` | low/medium/high | Effort to reverse: low (<5 min), medium (5-30 min), high (>30 min) |
| `commit` | string | Git commit hash where this assumption was implemented (added post-commit) |

## Confidence Levels

- **high**: One option is clearly better given codebase evidence. Reversal unlikely.
- **medium**: Multiple reasonable options. The user might prefer an alternative.
- **low**: Genuine coin flip. Flag prominently at delivery. Consider pausing even in auto mode.

**Auto-mode pause rule**: If 3+ consecutive assumptions are `confidence: low`, STOP and 
switch to assist mode. Too many uncertain decisions compound error risk.

## Delivery Presentation

At Phase 6 (Pre-Delivery), present the ledger as a formatted summary:

```markdown
## Assumptions Made During Auto Mode

I made **7 assumptions** while working autonomously. Review below — 
say "reverse A3" to undo any decision, or "approve all" to accept.

### High Confidence (5) — likely correct
| ID | Question | Assumption | Evidence |
|----|----------|-----------|----------|
| A1 | Show all visits or last 5? | All visits with scroll | Matches existing chart |
| A2 | Modal or inline? | Inline Sheet | Matches ReadingFormSheet |
| ... | ... | ... | ... |

### Medium Confidence (2) — review recommended  
| ID | Question | Assumption | Alternatives | Reversal Cost |
|----|----------|-----------|-------------|---------------|
| A5 | Cache strategy? | SWR with 30s stale | [No cache, 5min stale] | medium |
| A6 | Error message tone? | Technical for now | [User-friendly, silent] | low |

### Low Confidence (0)
None — auto mode would have paused if any appeared.
```

## Reversal Protocol

When the user says "reverse A{N}":

1. Read the assumption entry from `assumptions.jsonl`
2. Check `reversible` flag — if false, warn and explain why
3. Check `reversal_cost` — inform user of effort
4. Load the `commit` hash
5. If the commit is isolated (only this assumption's changes):
   - `git revert {commit}` — clean reversal
6. If the commit is mixed (multiple changes):
   - Manually edit the specific files listed in `blast_radius`
   - Apply the user's chosen alternative from `alternatives[]`
7. Re-run verification-loop on affected files
8. Update the assumption entry: `"reversed": true, "reversed_to": "alternative chosen"`

## Batch Operations

- `"approve all"` → Mark all assumptions as accepted, clear the ledger
- `"reverse A3, A5"` → Reverse multiple assumptions in sequence
- `"reverse all medium"` → Reverse all medium-confidence assumptions
- `"explain A4"` → Show full evidence and alternatives for one assumption

## Integration with Conductor State

The assumption ledger lives alongside track state:

```
conductor/tracks/{track-id}/
├── spec.md
├── plan.md  
├── metadata.json       ← task progress
├── assumptions.jsonl    ← assumption ledger (auto mode only)
└── index.md
```

Track completion in metadata.json includes assumption summary:

```json
{
  "assumptions": {
    "total": 7,
    "high_confidence": 5,
    "medium_confidence": 2,
    "low_confidence": 0,
    "reversed": 0,
    "pending_review": 7
  }
}
```

## Anti-Patterns

### Assumption Inflation
Problem: Logging obvious decisions to appear thorough.
Solution: Only log decisions where you genuinely considered 2+ approaches.

### Confidence Inflation  
Problem: Marking everything "high" to avoid pausing.
Solution: If you debated it internally for >5 seconds, it's "medium" at best.

### Irreversible Assumptions
Problem: Making database schema changes or API contract changes that cascade.
Solution: Schema and API changes are ALWAYS "medium" confidence minimum. 
Flag destructive changes (DROP, DELETE, rename) as `reversible: false`.

### Missing Blast Radius
Problem: Not tracking which files were affected.
Solution: Every assumption MUST list files. This is what makes reversal possible.
