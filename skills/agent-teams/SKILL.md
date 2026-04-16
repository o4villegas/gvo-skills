---
name: agent-teams
description: >-
  Parallel multi-agent execution for Claude Code. Spawn coordinated teams of 
  implementers with file ownership boundaries, interface contracts, and merge 
  strategies. Presets: review, debug, feature, security, migration. Use when 
  decomposing work for parallel agents, establishing file ownership to prevent 
  conflicts, or running independent work streams simultaneously.
version: 1.0.0
---

# Agent Teams — Parallel Multi-Agent Execution

Coordinate multiple Claude Code agents working in parallel on the same codebase 
with explicit ownership boundaries and conflict avoidance.

## When to Use

- Decomposing a feature for parallel implementation
- Running independent review/debug/security passes simultaneously  
- Large features where serial execution is too slow
- Multi-layer work (UI + API + tests in parallel)

## Commands

| Command | Purpose |
|---------|---------|
| `/team-spawn` | Launch a team with a preset or custom configuration |
| `/team-feature` | Parallel feature development (vertical slices) |
| `/team-review` | Multi-perspective parallel code review |
| `/team-debug` | Parallel hypothesis-driven debugging |
| `/team-delegate` | Delegate specific tasks to team members |
| `/team-status` | Check progress of all team members |
| `/team-shutdown` | Gracefully stop all team agents |

## Agents

| Agent | Role |
|-------|------|
| **team-lead** | Decomposes work, assigns ownership, resolves conflicts |
| **team-implementer** | Executes assigned tasks within ownership boundaries |
| **team-reviewer** | Reviews completed work against acceptance criteria |
| **team-debugger** | Investigates failures with hypothesis-driven approach |

## File Ownership Model

Cardinal rule: **one owner per file**. Strategies:
- **By directory**: Each agent owns specific directories
- **By module**: Logical module ownership (may span dirs)
- **By layer**: UI / business logic / data layer split

See [skills/parallel-feature-development/SKILL.md](skills/parallel-feature-development/SKILL.md) for patterns.
See [skills/team-communication-protocols/SKILL.md](skills/team-communication-protocols/SKILL.md) for coordination.
