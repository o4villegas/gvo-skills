# Phase 6 — Pre-Delivery

**Goal:** Present the working implementation, collect feedback, run targeted refinements, and verify readiness before final delivery.

## Skills to load

| Skill | Role |
|-------|------|
| `verification-loop` | Final pre-delivery gate |
| `deslop` | Final slop check before delivery |

For UI work, the UX audit runs inline (step 4) against the checklist below. Deep-rubric scoring references live at `references/ux-diagnostic-2026-benchmark.md` and `references/ux-diagnostic-recon-checklist.md` — load when rigor matters.

## The 6-step sequence

### 1. Present working implementation
- **Claude Code:** run `npm run dev`, capture the dev server URL, open the primary flow in browser, take a screenshot (or describe it), paste to chat.
- **claude.ai:** write artifacts to `/mnt/user-data/outputs/`, reference path, describe the flow the user should click through.
- **API-only:** run 2–3 `curl` examples covering the happy path and 1 error path.

Never just say "it's done." Show, don't tell.

### 2. Confirmation question
Ask: "Does this match what you expected?"

Follow-up options (use `AskUserQuestion` with 2–4 options):
- "Yes, ship it" → advance to Phase 7
- "Yes, and I want to tweak X" → step 3
- "No, [specific issue]" → step 5 (refactor)
- "No, fundamentally wrong" → back to Phase 4 with full explanation

### 3. Enhancement presentation
If user wants more, offer 3–6 specific enhancement options as a menu. Each option has:
- **Label** (≤5 words)
- **Effort** (S/M/L — 15min / 1hr / >1hr)
- **Impact** (what the user gains)
- **Risk** (what could regress)

Use `AskUserQuestion` with `multiSelect: true` for the enhancement menu. Do not propose open-ended "anything else?" — forces decision.

### 4. UX audit (if any UI)
Run the inline audit against 2026 standards (deep rubric: `references/ux-diagnostic-2026-benchmark.md`):
- Visual hierarchy, spacing rhythm, typography pairing
- Interaction states (hover/focus/active/disabled)
- Reduced-motion support (prefers-reduced-motion media query)
- Color contrast (WCAG 2.2 AA minimum — labels ≥ 0.50 opacity, body ≥ 0.65)
- Mobile-first responsive (320/375/768/1024/1440)
- Touch targets ≥44px (48px for capture workflows)
- Anti-template check: does it look like a generic shadcn/Tailwind template? If yes, add intentional hierarchy, depth, or editorial layout.

Record the audit findings. Apply top 3 visual improvements inline — defer the rest to the enhancement menu.

### 5. Execute requested refactors
For each approved enhancement or refactor:
1. Run `search-first` to confirm you're not duplicating existing code
2. Make the change
3. Run `verification-loop` (quick gate)
4. Commit with a specific message

### 6. Final verification pass
Run the **full** verification gate one last time:

```bash
npx tsc -b --noEmit && npm run lint && npm test && npm run test:e2e && npm run build && npx wrangler deploy --dry-run && echo "Ready for delivery"
```

All 6 gates must pass. If any fails, return to Phase 5 step 7 (harden) — do not ship with a red gate.

## Enhancement suggestion format

When proposing enhancements, use this exact structure:

```markdown
**Found working.** [1 sentence describing what's shipping.]

**Suggestions to consider** (pick any):

1. **[Short label]** (S/M/L effort)
   What: [1 sentence]
   Why: [user impact in their terms]
   Risk: [what regresses if we get it wrong]

2. [...]
```

Cap at 6 items. More becomes noise.

## Anti-patterns

| Do NOT | Do instead |
|--------|------------|
| Describe the build without showing it | Screenshot / curl / demo link — always |
| Ask "anything else?" | Present a concrete menu of options |
| Run a full rebuild to apply a 1-line tweak | Make the targeted edit, then quick-gate |
| Ship with a yellow test | Red is red. Fix first, ship second. |
| Skip the UX audit on "small" UI changes | Run the audit — "small" changes are where template-looking defaults creep in |
| Accept vague "it feels off" feedback | Ask one specific clarifying question, then fix concretely |

## Handoff to Phase 7

When pre-delivery passes: "Phase 6 complete. [N] enhancements applied. Full gate green. Starting final delivery."
