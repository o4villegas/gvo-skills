# Commit, Push, and Create PR

Commit current changes, push to remote, and create a pull request.

## Pre-compute context
```bash
git status --short
git diff --stat
git branch --show-current
```

## Instructions

1. Review the staged and unstaged changes shown above
2. Generate a concise, descriptive commit message following conventional commits:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `refactor:` for code changes that neither fix bugs nor add features
   - `docs:` for documentation changes
   - `test:` for adding or updating tests
   - `chore:` for maintenance tasks

3. Stage all changes: `git add -A`

4. Commit with the generated message

5. Push to the current branch: `git push -u origin HEAD`

6. Create a PR using GitHub CLI:
   ```bash
   gh pr create --fill --web
   ```
   
   If `gh` is not available, provide the GitHub URL for creating a PR manually.

## Output

Provide a summary of:
- What was committed
- The commit message used
- PR URL or instructions
