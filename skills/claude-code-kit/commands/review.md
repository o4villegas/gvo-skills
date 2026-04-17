# Code Review

Review the current changes and provide feedback.

## Pre-compute context
```bash
git diff --stat
git diff HEAD~1..HEAD --name-only 2>/dev/null || git diff --staged --name-only
git log -1 --oneline 2>/dev/null || echo "No commits yet"
```

## Instructions

Review the code changes with focus on:

### 1. Correctness
- Does the code do what it's supposed to do?
- Are there edge cases not handled?
- Are there potential bugs or race conditions?

### 2. Code Quality
- Is the code readable and maintainable?
- Are names clear and descriptive?
- Is there unnecessary complexity?

### 3. Patterns & Consistency
- Does it follow project conventions (check CLAUDE.md)?
- Are there better patterns that could be used?
- Is it consistent with the rest of the codebase?

### 4. Testing
- Are there tests for the changes?
- Do tests cover edge cases?
- Are tests maintainable?

### 5. Security
- Any potential security issues?
- Proper input validation?
- No exposed secrets?

## Output Format

```markdown
## Code Review

### Summary
[One paragraph overview]

### ✅ What's Good
- [Positive feedback]

### 🔧 Suggestions
- [File:Line] - [Suggestion]

### ⚠️ Issues to Address
- [File:Line] - [Issue and why it matters]

### 💡 Optional Improvements
- [Nice-to-have changes]

### Verdict
APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION
```

## Guidelines

- Be constructive, not critical
- Explain *why* something is an issue
- Suggest specific fixes
- Acknowledge good code
- Prioritize issues by severity
