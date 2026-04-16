---
name: conductor
description: >-
  Context-driven development orchestrator with persistent state, track management, 
  TDD loops, and session resumability. Manages product.md, tech-stack.md, workflow.md, 
  and tracks.md as living artifacts. Use when setting up a new project, implementing 
  features with full lifecycle tracking, resuming work across sessions, or managing 
  multi-track development with semantic revert. Supports both human-assist (phase 
  checkpoints) and auto mode (continuous execution with quality gates).
version: 1.0.0
---

# Conductor — Context-Driven Development Orchestrator

Treats project context as a managed artifact alongside code. Maintains persistent state 
across sessions via `conductor/` directory with structured artifacts.

## When to Use

- Setting up new or existing projects with structured context
- Implementing features with TDD lifecycle and progress tracking
- Resuming work across sessions (reads `metadata.json` for state)
- Managing multiple work tracks with semantic revert capability
- Running `/nexus --mode=auto` — conductor provides the state persistence layer

## Commands

| Command | Purpose |
|---------|---------|
| `/conductor:setup` | Initialize context artifacts (greenfield or brownfield) |
| `/conductor:new-track` | Create a new work unit with spec + plan |
| `/conductor:implement` | Execute tasks from a track's plan (TDD loop) |
| `/conductor:status` | Show project and track progress |
| `/conductor:revert` | Semantic revert by track/phase/task |
| `/conductor:manage` | Manage tracks (archive, delete, reprioritize) |

## Core Workflow

```
Context → Spec & Plan → Implement → Verify → Complete
   ↑                                          |
   └──────── Update context ←────────────────┘
```

## State Persistence

All state lives in `conductor/` directory:
- `product.md` — what and why
- `tech-stack.md` — with what
- `workflow.md` — how to work
- `tracks.md` — what's happening
- `tracks/{id}/metadata.json` — resumable task progress

## Auto Mode Integration

When invoked via `--mode=auto`:
1. Skip Phase 4 (user approval) — auto-approve if plan scores > 80% confidence
2. Phase verification gates become self-assessed (build + test pass = continue)
3. Max 3 retries per task before escalating to user
4. State persists in metadata.json for recovery on failure

See [skills/context-driven-development/SKILL.md](skills/context-driven-development/SKILL.md) for full patterns.
See [commands/implement.md](commands/implement.md) for TDD execution loop.
