# Interview Questions by Category

Use the relevant section during Phase 1c. Ask universal questions for all categories, then category-specific ones. Don't badger — if the user gives a short answer, move on and note gaps as `[CONFIRM]` flags.

## Universal Questions (All Categories)

1. **Objective** — What specifically should the agent accomplish? Push for concrete, verifiable descriptions — not "improve the dashboard" but "add a date range filter to the sales dashboard that filters all three chart components and persists the selection in URL params."
2. **Current state** — What exists today related to this task? What works, what doesn't? (This is about the *feature's* state, not the codebase — you already know the codebase from recon.)
3. **Constraints** — Things the agent must NOT do? Performance budgets? Compatibility requirements? Deployment targets?
4. **Definition of done** — How will the user verify this worked? Observable, testable criteria.

## New Feature Build

5. **User-facing behavior** — Walk through the feature from the end user's perspective. What do they see, click, experience?
6. **Data model** — What data does this feature need? Where does it come from? Shape? New tables/KV/D1 schemas? (Cross-reference against schemas found in recon.)
7. **Integration points** — What existing code does this touch? (Suggest based on recon: "Based on the code, it looks like this would touch [routes/files]. Match what you're thinking?")
8. **Edge cases & error states** — What happens when things go wrong? Empty states, loading states, error handling, validation?

## Bug Investigation & Fix

5. **Reproduction steps** — Exact steps to trigger the bug. Expected vs. actual behavior. Do not accept "it's broken" — get the specific sequence, the exact wrong output, and what should have happened.
6. **Error output** — Error messages, stack traces, console logs, network failures? Ask user to paste if possible. If no visible errors, note explicitly — silent failures need a different approach.
7. **Environment details** — Which browsers/devices affected vs. working? Dev, staging, or production?
8. **Recent changes** — What changed recently? New deploys, dependency updates, config changes?
9. **Previous attempts** — Has the user tried to fix it? What did they try? What happened?

## UI/UX Polish & Components

5. **Visual reference** — Design, screenshot, or reference site to match? If none: "What apps feel like what you're going for?" (This anchors the polish level — Bumble-tier vs "just make it not ugly.")
6. **Component inventory** — What components need work? New or modifications? Do they need loading/error/empty state variants?
7. **Interaction patterns** — Animations, transitions, hover states, responsive behavior, accessibility? Probe: "Do you have loading states? Skeleton screens? What happens on error?" These are the #1 gap in vibe-coded apps.
8. **Design system** — Existing tokens (colors, spacing, typography)? If none: from-prompter will inject a starter set from `references/ux-standards.md`.

## Audit & Remediation

5. **Scope** — Full app or specific pages/flows? What's the boundary?
6. **Approval gates** — Approve findings before fixes are applied? (Default: yes.)
7. **Adversarial review** — Challenger/devil's advocate phase that re-audits fixes? (Default: yes for 5+ files.)
8. **Viewports/devices** — Which viewports matter? (e.g., mobile 375px + desktop 1440px for UX audits)

## Closing Questions (All Categories)

9. **Anything else?** — Open-ended. Let the user add context, caveats, priorities.
10. **Priority ranking** — If the agent has to make tradeoffs, what matters most? (e.g., "ship fast over pixel-perfect" or "correctness over speed")
