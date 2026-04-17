# PR Feedback Handler

Address PR feedback and update CLAUDE.md if needed.

## Pre-compute context
```bash
git branch --show-current
git log -1 --format="%s"
cat CLAUDE.md | head -100
```

## Instructions

When handling PR feedback:

### 1. Understand the Feedback
- What specific changes are requested?
- Is this a style/convention issue or a bug?
- Should this become a project-wide rule?

### 2. Make the Fix
- Address the specific feedback
- Run verification to ensure fix doesn't break anything

### 3. Update CLAUDE.md (if applicable)

If the feedback represents a pattern Claude should always follow:

**Add to "Common Mistakes to Avoid":**
```markdown
## Common Mistakes to Avoid
- Don't [what Claude did wrong] - [do this instead]
```

**Or update relevant section:**
- Code style issues → Update "Code Style & Patterns"
- Architecture issues → Update "Architecture Decisions"
- Testing issues → Update "Testing Requirements"

### 4. Commit the Changes

Create a commit that:
- Fixes the specific feedback
- Includes CLAUDE.md update if made
- References the PR if possible

## Example Workflow

Feedback: "Use string literal union, not enum"

1. Fix: Change `enum Status { ... }` to `type Status = 'active' | 'inactive'`
2. Update CLAUDE.md: Add "Never use enum - use string literal unions instead"
3. Commit: "fix: use string literal union per PR feedback; update CLAUDE.md"

## Output

- What was changed
- Whether CLAUDE.md was updated and why
- Confirmation changes are ready for re-review
