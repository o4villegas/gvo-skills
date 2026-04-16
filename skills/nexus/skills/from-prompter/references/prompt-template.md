# Output Prompt Template

Use this structure when generating Claude Code agent prompts. Adapt section depth to task complexity.

## Template

```markdown
# [Descriptive Title of the Task]

## Objective
[Clear, specific description of what needs to be accomplished. Direct instruction to the agent.]

## Product Purpose
[What this app is, who uses it, and what success looks like for the end user. This is NOT the task objective — it's the broader product context that helps the agent make judgment calls when requirements are ambiguous. 2-3 sentences max.]

## Context
- **Project**: [name and brief description]
- **Stack**: [framework, runtime, UI library, database, key dependencies — from recon]
- **Relevant paths**: [specific directories and files the agent should examine first — from analysis]

## Current State
[What exists today. What works. What doesn't. Specific file references and patterns from codebase analysis. The agent should orient immediately, not spend time exploring.]

## Requirements

### Functional Requirements
[Numbered list of specific, verifiable requirements. Each one should be testable.]

### Non-Functional Requirements
[Performance, accessibility, security, compatibility constraints.]

## Best Practices & Recommendations
[Distilled from web research. Specific patterns, libraries, or approaches. Explain WHY each matters.]

## Implementation Approach
[High-level approach. Not prescriptive step-by-step, but enough structure to prevent wrong paths. Note architectural decisions that need user input.]

## Agent Team Configuration
[ONLY when 2+ genuinely independent parallel workstreams exist.]

- **Agent: [Role Name]** — [Specific responsibility and deliverable]

### Consensus Protocol
Before any sub-agent commits code or reports recommendations:
1. All agents share findings
2. Resolve conflicts or contradictions
3. Lead agent synthesizes unified recommendation
4. Only consensus-backed recommendations presented to user

### Subagent Discipline
- Use subagents to keep the main context window clean
- One task per subagent for focused execution
- For complex problems, throw more compute at it via subagents

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Minimal code impact.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Only touch what's necessary. Don't introduce bugs in unrelated code.
- **Demand Elegance (Balanced)**: For non-trivial changes, pause and ask "is there a more elegant way?" Skip for simple, obvious fixes.

## Do Not
[Customize per task. Always include:]
- Do not install packages not discussed in this prompt without asking first
- Do not refactor or modify files outside the scope of this task
- Do not over-abstract — build for current requirements, not hypothetical futures
- Do not silently swallow errors or skip edge cases to hit "done" faster
- Do not keep pushing when something goes sideways — STOP and re-plan immediately
- [Add task-specific anti-patterns]

## Workflow Orchestration

### Plan Mode
Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions). Present implementation plan for review before writing code. Wait for explicit approval. If plan changes during implementation, pause and re-confirm.
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity
- If something goes sideways, STOP and re-plan immediately

### Task Management
1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

### Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Review lessons at session start
- Ruthlessly iterate until mistake rate drops

### Autonomous Bug Fixing
When given a bug report: just fix it. Don't ask for hand-holding.
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Communication Protocol
- When uncertain, ask. Do not assume.
- When presenting options, include your recommendation and why.
- After each major milestone, report what was done and what's next.
- If something fails, explain what happened and recommend next steps.

## Verification & Completeness

### Pre-Implementation Checklist
Before writing any code, verify 100% confidence in ALL items:
- [ ] Plan based ONLY on empirical evidence from code analysis (zero assumptions)
- [ ] Plan necessity validated (no duplication of existing functionality)
- [ ] Plan designed for this specific project's architecture and constraints
- [ ] Plan complexity appropriate (neither over/under-engineered)
- [ ] Plan addresses full stack considerations (data layer, business logic, presentation, APIs)
- [ ] Plan maximizes code reuse through enhancement vs. new development
- [ ] Plan includes code organization, cleanup, and documentation requirements
- [ ] Plan considers system-wide impact (routing, state management, data flow)
- [ ] Plan ensures complete feature delivery without shortcuts or placeholders
- [ ] Plan contains only validated assumptions with explicit confirmation sources

### Empirical Verification Mandate
The primary coding agent MUST directly examine all relevant source code before formulating any plan or recommendation. Do not rely on file names, directory structure, or memory alone. Open and read the actual code. Verify:
- Existing patterns and conventions by reading neighboring files
- Import paths and dependency versions from package.json / wrangler.toml
- Database schemas from migration files or D1 table definitions
- API contracts from route handlers and type definitions

### Pre-Delivery Self-Audit (MANDATORY)
Before presenting any deliverable, hitting any STOP gate, or reporting a phase complete, complete this internal audit silently:
1. Re-read the objective. Does your output satisfy EVERY requirement, not just most?
2. Pick the 3 weakest parts of your work. For each: why is it weak? Can you fix it right now?
3. If a senior engineer reviewed this cold, what would they flag first? Fix that before presenting.
4. Run a "fresh eyes" pass — re-read as if you've never seen the project. Anything confusing or incomplete?
5. Check for the "last 10%" — edge cases, error states, empty states, and polish you were tempted to skip.
6. Count things you said you'd do vs. things you actually did. Close any gap.

### Explore Validation Gate (MANDATORY)
Before completing each phase or major deliverable, spawn an Explore sub-agent:

"Audit [this deliverable] against [the requirements/spec]. List every gap, missing item, inconsistency, or unstated assumption. Be adversarial — assume something was missed and find it."

If gaps found, fix before proceeding. This is not optional.

### Runtime Testing
After implementation, run the application and verify:
- All functional requirements work end-to-end (not just "it compiles")
- Error states and edge cases behave as specified
- No regressions in existing functionality
- Console is clean of warnings and errors
- If tests exist, they pass. If they don't exist for this feature, write them.

### Implementation Completeness Check
Before reporting completion, confirm:
- No TODO comments, placeholder values, or stubbed functions remain
- All imports resolve correctly
- TypeScript types are complete (no `any` without justification)
- Error handling in place for all async operations and user inputs
- Loading and empty states implemented where applicable
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
```

## Adapting the Template — Section Inclusion by Category

Include only the sections marked ✓ for each category. Omitting sections is how you hit the line count target.

| Section | Feature (≤280) | Bug Fix (≤140) | UI Polish (≤200) | Audit (≤350) |
|---------|:-:|:-:|:-:|:-:|
| Objective | ✓ | ✓ | ✓ | ✓ |
| Context | ✓ | ✓ | ✓ | ✓ |
| Product Purpose | ✓ | ✓ | ✓ | ✓ |
| Current State | ✓ | ✓ (focus: repro) | ✓ | ✓ |
| Functional Requirements | ✓ | ✓ | ✓ | ✓ |
| Non-Functional Requirements | ✓ | — | ✓ | ✓ |
| Best Practices | ✓ | — | ✓ (UX patterns) | ✓ |
| Implementation Approach | ✓ | slim | slim | ✓ (multi-phase) |
| Agent Team Config | ✓ (if parallel) | — | — | ✓ (if 5+ files) |
| Core Principles | — | — | — | — |
| Do Not | ✓ | ✓ | ✓ | ✓ |
| Workflow Orchestration | ✓ | — | — | ✓ (STOP gates) |
| Communication Protocol | — | — | — | — |
| Self-Improvement Loop | — | — | — | — |
| Task Management | ✓ | — | — | ✓ |
| Verification & Completeness | ✓ | ✓ (slim) | ✓ (slim) | ✓ |

**Core Principles, Communication Protocol, and Self-Improvement Loop** are generic boilerplate — they consume context window without adding task-specific value. Omit them by default. Only include if the user's interview responses revealed a specific need (e.g., the user said "the agent keeps making the same mistake" → add Self-Improvement Loop).

## `[CONFIRM]` Flag Discipline

A `[CONFIRM]` flag means the interview/recon failed to extract that info. Acceptable:
- User explicitly said "I'm not sure yet, let the agent propose options"
- Decision requires seeing implementation first
- Codebase has conflicting patterns, user must choose

Unacceptable:
- File paths (you found them)
- What the feature should do (that's the interview's job)
- Framework/library choice (you read the code)
- Schema column names (you searched for schemas)

More than 2-3 `[CONFIRM]` flags → go back and ask or query the codebase.
