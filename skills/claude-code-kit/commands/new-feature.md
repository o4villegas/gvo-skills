# New Feature

Plan and implement a new feature with full verification.

## Pre-compute context
```bash
# Project structure
find . -type f \( -name "*.ts" -o -name "*.tsx" \) | grep -v node_modules | head -30

# Recent patterns
git log --oneline -10
```

## Instructions

### Phase 1: Planning (Plan Mode)

Before writing any code:

1. **Understand the requirement**
   - What exactly should this feature do?
   - Who uses it and how?
   - What are the acceptance criteria?

2. **Analyze the codebase**
   - Where should this code live?
   - What existing code can be reused?
   - What patterns are already established?

3. **Design the solution**
   - What files need to be created/modified?
   - What's the data flow?
   - How will it be tested?

4. **Present the plan**
   - List all files to create/modify
   - Describe the implementation approach
   - Identify potential risks

**Wait for approval before proceeding to Phase 2.**

### Phase 2: Implementation

Once plan is approved:

1. Create/modify files according to plan
2. Follow project conventions (see CLAUDE.md)
3. Write tests alongside implementation
4. Run typecheck after each significant change

### Phase 3: Verification

1. Run full verification:
   ```bash
   bun run typecheck
   bun run lint
   bun run test
   ```

2. Test the feature manually if possible

3. Review the changes:
   - Does it match the plan?
   - Is the code clean?
   - Are tests comprehensive?

### Phase 4: Cleanup

1. Run code simplifier if needed
2. Update documentation if necessary
3. Prepare commit message

## Output

End with:
- Summary of what was built
- Files created/modified
- How to test the feature
- Any follow-up tasks
