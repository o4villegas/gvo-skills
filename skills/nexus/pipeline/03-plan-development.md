# Phase 3 — Plan Development

**Goal:** Produce a world-class implementation plan using multi-perspective expert planning. **No user intervention** during this phase — the user sees the output in Phase 4.

## Skills to load

| Skill | Role |
|-------|------|
| `council` | Four-voice planning pattern (primary) |
| `blueprint` | Multi-session step-by-step plan with cold-start context briefs per step |
| `debate` | Adversarial rounds for contentious decisions |
| `agentic-engineering` | Core principles: eval-first, 15-minute task decomposition, model routing |
| `repo-intel` (if existing code) | Git history + codebase intelligence |

Read `~/.claude/skills/nexus/agents/*.md` — these are the expert lenses the council uses.

## The four-voice council pattern

Run each voice independently — **do not let one voice anchor the next**. Each produces a short written take (5–10 bullet points), then synthesize.

| Voice | Agent file | Lens |
|-------|-----------|------|
| **Architect** | `agents/architect.md` | Correctness, maintainability, long-term implications, system design, data model, API surface |
| **Skeptic** | `agents/architect.md` + `agents/qa-engineer.md` | Challenge the framing. Question assumptions. Propose the simplest alternative that could work. |
| **Pragmatist** | `agents/implementer.md` | Shipping speed, operational reality, dependency audit (prefer built-in over npm), stack gotchas |
| **Critic** | `agents/qa-engineer.md` | Edge cases, downside risk, failure modes, security, performance |

Optional additional voices (load agent file, run independently):

| Voice | Agent file | When to add |
|-------|-----------|-------------|
| **UX specialist** | `agents/ux-specialist.md` | Any UI surface |
| **Domain researcher** | `agents/domain-researcher.md` | Industry norms, competitor analysis, regulation |
| **Lead** | `agents/lead.md` | Always — synthesis and user communication format |

## Decomposition (from `agentic-engineering`)

Break the work into **15-minute units**. Each unit must:
- Produce a reviewable diff or artifact
- Have a clear pass/fail verification
- Be independently re-runnable if it fails

If a unit is >15 min, split it. If a unit cannot be verified, it's not a unit — it's an assumption.

## Contentious decisions → `debate`

When two voices disagree on a material choice (framework, data model, scope boundary), load `debate` and run structured adversarial rounds:

1. Each side states position + strongest evidence
2. Each side attacks the other's strongest argument
3. Each side concedes the weakest point in their own position
4. Synthesis: what does the combined evidence actually show?

Do not skip this for technical decisions that shape the product — a wrong call in Phase 3 costs 10× to fix in Phase 5.

## Plan output format

The Lead voice produces the final plan in this exact structure:

```markdown
# Plan — [task name]

## Architecture
- Runtime/framework
- Data model (tables + key relationships)
- API surface (endpoints + contracts)
- Key libraries (with versions where relevant)

## File structure
- List directories to create
- List files to create/modify with one-line purpose

## Implementation sequence
1. [15-min unit 1] — verifies via X
2. [15-min unit 2] — verifies via Y
…

## Test plan
- Unit: what to cover, framework, expected count
- Integration: which boundaries
- E2E: which user flows

## Risk register
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|

## Open questions
- Things the council could not resolve without user input
```

## Handoff to Phase 4

Package the plan for user review. Do NOT start implementing yet — Phase 4 is the approval gate. The plan must be terse enough to read in 60 seconds but specific enough that nothing in Phase 5 needs a new decision.
