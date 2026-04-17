# Fix All Errors

Automatically fix typecheck, lint, and test errors.

## Pre-compute context
```bash
bun run typecheck 2>&1 | head -50
bun run lint 2>&1 | head -50
```

## Instructions

1. Analyze the errors shown above
2. Group errors by file and type
3. Fix errors in order of dependency (types first, then lint, then tests)
4. After each fix, re-run the relevant check to verify
5. Continue until all checks pass

## Strategy

- **Type errors**: Fix the root cause, not symptoms. Check imports and type definitions.
- **Lint errors**: Use auto-fix where possible (`bun run lint --fix`), then fix remaining manually.
- **Test failures**: Read the test to understand intent, then fix the implementation (not the test, unless the test is wrong).

## Output

For each error fixed:
- File and line
- What was wrong
- How it was fixed

End with verification that all checks now pass.
