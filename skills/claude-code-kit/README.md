# Claude Code Best Practices Kit

Based on Boris Cherny's workflow (creator of Claude Code). This kit provides templates and configurations to supercharge your Claude Code experience.

## Quick Start

```bash
# Copy to your project root
cp -r claude-code-kit/.claude your-project/
cp claude-code-kit/CLAUDE.md your-project/
cp claude-code-kit/.mcp.json your-project/  # Optional: if using MCP servers
```

## What's Included

```
.claude/
├── settings.json      # Pre-allowed commands & model config
├── hooks.json         # Auto-formatting on file changes
├── commands/          # Slash commands for common workflows
│   ├── commit-push-pr.md
│   ├── verify.md
│   └── fix-errors.md
└── agents/            # Specialized subagents
    ├── code-simplifier.md
    ├── code-architect.md
    ├── build-validator.md
    └── verify-app.md

CLAUDE.md              # Project context & coding standards
.mcp.json              # MCP server integrations
```

## Boris's Key Insights

### 1. Model Choice
**Use Opus 4.5 with thinking for everything.** It's bigger and slower than Sonnet, but you steer it less and it's better at tool use—so it's often faster overall.

### 2. Plan Mode First (shift+tab twice)
Start sessions in Plan mode. Iterate on the plan until you like it. Then switch to auto-accept edits mode for 1-shot execution. **A good plan is everything.**

### 3. Team CLAUDE.md
Your CLAUDE.md is a living document. When Claude does something wrong, add it to CLAUDE.md so it won't do it next time. Commit it to git and have the team contribute.

### 4. Verification is Critical
Give Claude a way to verify its work. If Claude has a feedback loop, it will 2-3x the quality of the final result. Use:
- Type checking
- Linting
- Test suites
- Browser testing (Claude Chrome extension)

### 5. Slash Commands for Inner Loops
Create slash commands for workflows you do many times a day. Commands live in `.claude/commands/` and can pre-compute context using inline bash.

### 6. Subagents for Common Workflows
Think of subagents as automating what you do for most PRs:
- `code-simplifier` - Clean up after Claude is done
- `verify-app` - Full end-to-end testing
- `build-validator` - Ensure production readiness

### 7. Pre-Allow Safe Commands
Use `/permissions` to pre-allow safe commands instead of `--dangerously-skip-permissions`. Share via `.claude/settings.json`.

### 8. Hooks for Automation
Use PostToolUse hooks to auto-format code after writes. Claude usually generates well-formatted code, but the hook handles the last 10%.

### 9. Parallel Sessions
Run 5+ Claudes in parallel. Use terminal tabs, claude.ai/code web sessions, and the iOS app. Hand off between them with `&` or `--teleport`.

## Customization Guide

### Updating CLAUDE.md

**When to update:**
- Claude uses wrong patterns → Add to "Common Mistakes to Avoid"
- Project conventions change → Update "Code Style & Patterns"
- New dependencies added → Add usage notes

**Pro tip:** Tag @claude on PRs to have it update CLAUDE.md as part of code review.

### Adding Slash Commands

Create a new `.md` file in `.claude/commands/`:

```markdown
# Command Name

Description of what this command does.

## Pre-compute context
\`\`\`bash
# Commands to gather context before Claude starts
git status
\`\`\`

## Instructions

What Claude should do...
```

Use with: `/command-name` in Claude Code

### Adding Subagents

Create a new `.md` file in `.claude/agents/`:

```markdown
# Agent Name

You are a [specialist role]. Your job is to [purpose].

## Process
1. Step one
2. Step two

## Guidelines
- Rule one
- Rule two
```

Use with: `@agent-name` or spawn as background task

### Configuring Permissions

Edit `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(your-safe-command:*)",
      "Read(*)",
      "Write(*)"
    ]
  }
}
```

Patterns use glob syntax. `*` matches anything.

### Setting Up Hooks

Edit `.claude/hooks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "your-command" }]
      }
    ]
  }
}
```

Available hook points:
- `PostToolUse` - After any tool is used
- `Stop` - When Claude finishes
- `PreToolUse` - Before tool execution

## Recommended Workflow

1. **Start in Plan Mode**: `shift+tab` twice
2. **Describe the goal**: Be specific about what you want
3. **Iterate on plan**: Go back and forth until plan is solid
4. **Execute**: Switch to auto-accept, let Claude work
5. **Verify**: Run `/verify` or `@verify-app`
6. **Simplify**: Run `@code-simplifier` if code is complex
7. **Ship**: Run `/commit-push-pr`

## Integration with Your Stack

### Cloudflare Workers
Add to CLAUDE.md:
```markdown
## Cloudflare Workers
- Use Hono for routing
- Workers have 128MB memory limit
- Use KV for simple storage, D1 for relational data
- Test with `wrangler dev`
```

### React Router v7
Add to CLAUDE.md:
```markdown
## React Router v7
- Use loaders for data fetching
- Use actions for mutations
- Prefer `<Form>` over `fetch` for mutations
- Use `useNavigation` for loading states
```

### Vercel Deployment
Add to CLAUDE.md:
```markdown
## Deployment
- Deploy with `vercel --prod`
- Preview deployments on PRs
- Use `vercel env pull` for local env vars
```

## Troubleshooting

**Claude ignores CLAUDE.md:**
- Ensure CLAUDE.md is in project root
- Check file isn't too long (keep < 500 lines)
- Most important rules should be near the top

**Slash commands not showing:**
- Commands must be in `.claude/commands/`
- File must have `.md` extension
- Restart Claude Code after adding

**Hooks not running:**
- Check hooks.json syntax
- Ensure matcher pattern is correct
- Command must exist and be executable

## Resources

- [Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code)
- [Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [Slash Commands](https://code.claude.com/docs/en/slash-commands)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
