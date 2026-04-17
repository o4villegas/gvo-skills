# Verify All Changes

Run full verification suite before committing or creating a PR.

## Pre-compute context
```bash
git status --short
git diff --name-only
```

## Instructions

Run the following verification steps in order. Stop and fix issues if any step fails.

### Step 1: TypeScript Check
```bash
bun run typecheck
```

### Step 2: Lint
```bash
bun run lint
```

### Step 3: Run Tests
```bash
bun run test
```

### Step 4: Build Check (if applicable)
```bash
bun run build
```

## Output

Provide a verification report:
- ✅ or ❌ for each step
- Summary of any issues found
- Suggested fixes for failures

If all steps pass, confirm the code is ready for commit.
